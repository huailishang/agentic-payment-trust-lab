import sys
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment import (
    Decision,
    IntentMandate,
    Order,
    OrderItem,
    TransactionRequest,
    validate_request,
)


class OrderValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 7, 11, 12, 0, tzinfo=timezone(timedelta(hours=8)))
        self.mandate = IntentMandate(
            mandate_id="mandate-001",
            user_id="user-001",
            max_amount=Decimal("550.00"),
            confirmation_above=Decimal("500.00"),
            allowed_merchants=frozenset({"merchant-a"}),
            allowed_categories=frozenset({"shoes"}),
            expires_at=self.now + timedelta(hours=1),
            max_count=1,
            expected_agent_id="agent-001",
        )

    def item(self, item_id: str = "shoe-001", **changes: object) -> OrderItem:
        values = {
            "item_id": item_id,
            "name": "Road Runner",
            "category": "shoes",
            "quantity": 1,
            "unit_amount": Decimal("480.00"),
            "kind": "product",
        }
        values.update(changes)
        return OrderItem(**values)

    def order(self, **changes: object) -> Order:
        values = {
            "order_id": "order-001",
            "order_version": "v1",
            "merchant": "merchant-a",
            "payee": "merchant-a",
            "items": (self.item(),),
            "total_amount": Decimal("480.00"),
            "currency": "CNY",
            "quote_expires_at": self.now + timedelta(minutes=30),
            "fulfilment_terms": "standard delivery",
            "mandate_ref": "mandate-001",
            "service_id": "shoe-order",
            "candidate_rails": ("card",),
        }
        values.update(changes)
        return Order(**values)

    def request(self, final_order: Order | None = None, **changes: object) -> TransactionRequest:
        values = {
            "request_id": "request-001",
            "amount": final_order.total_amount if final_order is not None else Decimal("480.00"),
            "merchant": "merchant-a",
            "category": "shoes",
            "occurred_at": self.now,
            "sequence_count": 1,
            "agent_id": "agent-001",
            "currency": "CNY",
        }
        values.update(changes)
        return TransactionRequest(**values)

    def validate(
        self,
        authorized: Order | None,
        final: Order | None,
        *,
        mandate: IntentMandate | None = None,
        **request_changes: object,
    ):
        return validate_request(
            mandate or self.mandate,
            self.request(final, **request_changes),
            authorized_order=authorized,
            final_order=final,
        )

    @staticmethod
    def issue_codes(result) -> set[str]:
        return {item.code for item in result.issues}

    @staticmethod
    def evidence_codes(result) -> set[str]:
        return {item.code for item in result.evidence}

    @staticmethod
    def difference_codes(result) -> set[str]:
        return {item.code for item in result.order_differences}

    def assert_decision_codes(self, result, decision: Decision, codes: set[str]) -> None:
        self.assertEqual(decision, result.decision)
        self.assertEqual(codes, self.issue_codes(result))
        self.assertTrue(codes.issubset(self.evidence_codes(result)))

    def test_missing_either_snapshot_is_indeterminate(self) -> None:
        for authorized, final, missing_path in (
            (None, self.order(order_version="v2"), "authorized_order"),
            (self.order(), None, "final_order"),
        ):
            with self.subTest(missing_path=missing_path):
                result = self.validate(authorized, final)
                self.assert_decision_codes(result, Decision.INDETERMINATE, {"order_snapshot_missing"})
                evidence = next(item for item in result.evidence if item.code == "order_snapshot_missing")
                self.assertEqual(missing_path, evidence.field_path)
                self.assertEqual("<missing>", evidence.observed)
                self.assertEqual((), result.order_differences)

    def test_each_comparability_failure_is_indeterminate(self) -> None:
        base_authorized = self.order()
        base_final = self.order(order_version="v2")
        cases = (
            ("order_id_mismatch", base_authorized, replace(base_final, order_id="order-other"), {}),
            (
                "authorized_order_mandate_mismatch",
                replace(base_authorized, mandate_ref="mandate-other"),
                base_final,
                {},
            ),
            ("order_mandate_mismatch", base_authorized, replace(base_final, mandate_ref="mandate-other"), {}),
            (
                "authorized_order_merchant_mismatch",
                replace(base_authorized, merchant="merchant-other"),
                base_final,
                {},
            ),
            (
                "authorized_order_currency_mismatch",
                replace(base_authorized, currency="USD"),
                base_final,
                {},
            ),
            (
                "order_request_amount_mismatch",
                base_authorized,
                replace(base_final, total_amount=Decimal("490.00")),
                {"amount": Decimal("480.00")},
            ),
            (
                "order_request_merchant_mismatch",
                replace(base_authorized, merchant="merchant-b"),
                replace(base_final, merchant="merchant-b"),
                {},
            ),
            (
                "order_request_currency_mismatch",
                replace(base_authorized, currency="USD"),
                replace(base_final, currency="USD"),
                {},
            ),
        )
        for code, authorized, final, request_changes in cases:
            with self.subTest(code=code):
                result = self.validate(authorized, final, **request_changes)
                self.assert_decision_codes(result, Decision.INDETERMINATE, {code})
                self.assertEqual((), result.order_differences)

    def test_aggregates_same_layer_binding_failures_without_business_differences(self) -> None:
        authorized = self.order(
            order_id="authorized-order",
            mandate_ref="mandate-other",
            merchant="merchant-other",
            currency="USD",
        )
        final = self.order(
            order_id="final-order",
            order_version="v2",
            mandate_ref="mandate-final-other",
            total_amount=Decimal("490.00"),
        )

        result = self.validate(authorized, final, amount=Decimal("480.00"))

        expected = {
            "order_id_mismatch",
            "authorized_order_mandate_mismatch",
            "order_mandate_mismatch",
            "authorized_order_merchant_mismatch",
            "authorized_order_currency_mismatch",
            "order_request_amount_mismatch",
        }
        self.assert_decision_codes(result, Decision.INDETERMINATE, expected)
        self.assertEqual((), result.order_differences)

    def test_payee_change_and_duplicate_item_ids_are_structural(self) -> None:
        duplicate = self.item()
        authorized = self.order(items=(duplicate, duplicate))
        final = self.order(order_version="v2", payee="payee-other", items=(duplicate, duplicate))

        result = self.validate(authorized, final)

        expected = {"order_payee_changed", "duplicate_order_item_id"}
        self.assert_decision_codes(result, Decision.INDETERMINATE, expected)
        duplicate_evidence = [item for item in result.evidence if item.code == "duplicate_order_item_id"]
        self.assertEqual(2, len(duplicate_evidence))
        self.assertTrue(all("item_id=shoe-001" in item.field_path for item in duplicate_evidence))
        self.assertEqual((), result.order_differences)

    def test_payee_change_alone_is_indeterminate_without_business_differences(self) -> None:
        result = self.validate(
            self.order(),
            self.order(order_version="v2", payee="payee-other"),
        )
        self.assert_decision_codes(result, Decision.INDETERMINATE, {"order_payee_changed"})
        self.assertEqual((), result.order_differences)

    def test_detects_duplicate_item_id_in_either_snapshot(self) -> None:
        duplicate = self.item()
        for authorized, final, snapshot in (
            (self.order(items=(duplicate, duplicate)), self.order(order_version="v2"), "authorized_order"),
            (self.order(), self.order(order_version="v2", items=(duplicate, duplicate)), "final_order"),
        ):
            with self.subTest(snapshot=snapshot):
                result = self.validate(authorized, final)
                self.assert_decision_codes(result, Decision.INDETERMINATE, {"duplicate_order_item_id"})
                evidence = next(item for item in result.evidence if item.code == "duplicate_order_item_id")
                self.assertTrue(evidence.field_path.startswith(snapshot))

    def test_final_item_category_out_of_scope_is_denied(self) -> None:
        final = self.order(
            order_version="v2",
            items=(self.item(category="electronics"),),
        )

        result = self.validate(self.order(), final)

        self.assert_decision_codes(result, Decision.DENY, {"order_item_category_out_of_scope"})
        evidence = next(item for item in result.evidence if item.code == "order_item_category_out_of_scope")
        self.assertEqual("final_order.items[item_id=shoe-001].category", evidence.field_path)
        self.assertIn("order_item_category_changed", self.difference_codes(result))

    def test_aggregates_multiple_out_of_scope_items(self) -> None:
        final = self.order(
            order_version="v2",
            items=(
                self.item("camera-001", category="electronics"),
                self.item("wine-001", category="alcohol"),
            ),
        )

        result = self.validate(self.order(), final)

        self.assert_decision_codes(result, Decision.DENY, {"order_item_category_out_of_scope"})
        evidence = [item for item in result.evidence if item.code == "order_item_category_out_of_scope"]
        self.assertEqual(2, len(evidence))
        self.assertLess(evidence[0].field_path, evidence[1].field_path)

    def test_hard_boundary_wins_while_reliable_differences_are_retained(self) -> None:
        final = self.order(
            order_version="v2",
            total_amount=Decimal("490.00"),
            items=(self.item(category="electronics"),),
        )

        result = self.validate(self.order(), final)

        self.assert_decision_codes(result, Decision.DENY, {"order_item_category_out_of_scope"})
        self.assertEqual(
            {"order_total_changed", "order_item_category_changed"},
            self.difference_codes(result),
        )
        self.assertNotIn("order_total_changed", self.evidence_codes(result))

    def test_total_increase_and_decrease_require_confirmation(self) -> None:
        for amount in (Decimal("490.00"), Decimal("470.00")):
            with self.subTest(amount=amount):
                final = self.order(order_version="v2", total_amount=amount)
                result = self.validate(self.order(), final)
                self.assert_decision_codes(result, Decision.CONFIRMATION_REQUIRED, {"order_total_changed"})
                self.assertEqual({"order_total_changed"}, self.difference_codes(result))

    def test_added_and_removed_products_change_item_set(self) -> None:
        added = self.item("lace-001", name="Laces", unit_amount=Decimal("10.00"))
        cases = (
            (self.order(), self.order(order_version="v2", items=(self.item(), added))),
            (self.order(items=(self.item(), added)), self.order(order_version="v2")),
        )
        for authorized, final in cases:
            with self.subTest(final_count=len(final.items)):
                result = self.validate(authorized, final)
                self.assert_decision_codes(result, Decision.CONFIRMATION_REQUIRED, {"order_items_changed"})
                difference = next(item for item in result.order_differences if item.code == "order_items_changed")
                self.assertIn("item_id=lace-001", difference.field_path)
                self.assertIn("<missing>", (difference.before, difference.after))

    def test_non_product_addon_has_deterministic_addon_code(self) -> None:
        addon = self.item("member-001", name="Membership", kind="addon", unit_amount=Decimal("10.00"))
        final = self.order(order_version="v2", items=(self.item(), addon))

        result = self.validate(self.order(), final)

        expected = {"order_items_changed", "unauthorized_addon_added"}
        self.assert_decision_codes(result, Decision.CONFIRMATION_REQUIRED, expected)
        self.assertEqual(expected, self.difference_codes(result))

    def test_added_product_is_not_misclassified_as_addon(self) -> None:
        product = self.item("lace-001", name="Laces", kind="product", unit_amount=Decimal("10.00"))
        result = self.validate(
            self.order(),
            self.order(order_version="v2", items=(self.item(), product)),
        )
        self.assert_decision_codes(result, Decision.CONFIRMATION_REQUIRED, {"order_items_changed"})
        self.assertNotIn("unauthorized_addon_added", self.difference_codes(result))

    def test_each_same_item_field_change_requires_confirmation(self) -> None:
        allowed_mandate = replace(
            self.mandate,
            allowed_categories=frozenset({"shoes", "apparel"}),
        )
        cases = (
            ("order_item_name_changed", {"name": "Road Runner 2"}, self.mandate),
            ("order_item_category_changed", {"category": "apparel"}, allowed_mandate),
            ("order_item_quantity_changed", {"quantity": 2}, self.mandate),
            ("order_item_unit_amount_changed", {"unit_amount": Decimal("470.00")}, self.mandate),
            ("order_item_kind_changed", {"kind": "subscription"}, self.mandate),
        )
        for code, changes, mandate in cases:
            with self.subTest(code=code):
                final = self.order(order_version="v2", items=(self.item(**changes),))
                result = self.validate(self.order(), final, mandate=mandate)
                self.assert_decision_codes(result, Decision.CONFIRMATION_REQUIRED, {code})
                self.assertEqual({code}, self.difference_codes(result))

    def test_name_comparison_strips_only_outer_whitespace(self) -> None:
        final = self.order(order_version="v2", items=(self.item(name="  Road Runner  "),))
        result = self.validate(self.order(), final)
        self.assertEqual(Decision.ALLOW, result.decision)
        self.assertEqual((), result.order_differences)

    def test_service_terms_and_quote_expiry_require_confirmation(self) -> None:
        cases = (
            ("order_service_changed", {"service_id": "other-service"}, {}),
            ("order_fulfilment_terms_changed", {"fulfilment_terms": "express delivery"}, {}),
            (
                "order_quote_expired",
                {"quote_expires_at": self.now - timedelta(seconds=1)},
                {},
            ),
        )
        for code, order_changes, request_changes in cases:
            with self.subTest(code=code):
                final = self.order(order_version="v2", **order_changes)
                result = self.validate(self.order(), final, **request_changes)
                self.assert_decision_codes(result, Decision.CONFIRMATION_REQUIRED, {code})
                self.assertEqual({code}, self.difference_codes(result))

    def test_quote_equal_to_request_time_is_not_expired(self) -> None:
        final = self.order(order_version="v2", quote_expires_at=self.now)
        result = self.validate(self.order(), final)
        self.assertEqual(Decision.ALLOW, result.decision)

    def test_multiple_material_changes_are_aggregated_in_stable_order(self) -> None:
        final = self.order(
            order_version="v2",
            total_amount=Decimal("490.00"),
            items=(self.item(quantity=2, unit_amount=Decimal("245.00")),),
            service_id="other-service",
        )

        result = self.validate(self.order(), final)

        expected = {
            "order_total_changed",
            "order_item_quantity_changed",
            "order_item_unit_amount_changed",
            "order_service_changed",
        }
        self.assert_decision_codes(result, Decision.CONFIRMATION_REQUIRED, expected)
        self.assertEqual(expected, self.difference_codes(result))
        self.assertEqual(
            [
                "order_total_changed",
                "order_item_quantity_changed",
                "order_item_unit_amount_changed",
                "order_service_changed",
            ],
            [item.code for item in result.order_differences],
        )

    def test_non_material_changes_do_not_trigger_confirmation(self) -> None:
        second = self.item("lace-001", name="Laces", unit_amount=Decimal("10.00"))
        authorized = self.order(items=(self.item(), second), candidate_rails=("card", "wallet"))
        cases = (
            replace(authorized, order_version="v2"),
            replace(authorized, order_version="v2", items=(second, self.item())),
            replace(authorized, order_version="v2", candidate_rails=("bank",)),
        )
        for final in cases:
            with self.subTest(version=final.order_version, rails=final.candidate_rails):
                result = self.validate(authorized, final)
                self.assertEqual(Decision.ALLOW, result.decision)
                self.assertEqual((), result.issues)
                self.assertEqual((), result.order_differences)
                self.assertEqual("order-change-rules-v0.3", result.rule_version)

    def test_exact_same_snapshot_has_valid_binding_fact(self) -> None:
        order = self.order()
        result = self.validate(order, order)

        self.assertEqual(Decision.ALLOW, result.decision)
        evidence = {item.code: item for item in result.evidence}
        self.assertEqual("VALID", evidence["order_binding_status"].observed)
        self.assertEqual("binding_match", evidence["order_binding_reason"].observed)
        self.assertEqual(
            evidence["authorized_order_digest"].observed,
            evidence["final_order_digest"].observed,
        )

    def test_version_only_binding_mismatch_does_not_change_payment_decision(self) -> None:
        authorized = self.order()
        final = replace(authorized, order_version="v2")
        result = self.validate(authorized, final)

        self.assertEqual(Decision.ALLOW, result.decision)
        self.assertEqual((), result.issues)
        evidence = {item.code: item for item in result.evidence}
        self.assertEqual("INVALID", evidence["order_binding_status"].observed)
        self.assertEqual("binding_mismatch", evidence["order_binding_reason"].observed)
        self.assertNotEqual(
            evidence["authorized_order_digest"].observed,
            evidence["final_order_digest"].observed,
        )


if __name__ == "__main__":
    unittest.main()

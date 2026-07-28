import sys
import unittest
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


class ValidatorTest(unittest.TestCase):
    def setUp(self) -> None:
        now = datetime(2026, 7, 11, 12, 0, tzinfo=timezone(timedelta(hours=8)))
        self.now = now
        self.mandate = IntentMandate(
            mandate_id="mandate-001",
            user_id="user-001",
            max_amount=Decimal("550.00"),
            confirmation_above=Decimal("500.00"),
            allowed_merchants=frozenset({"merchant-a"}),
            allowed_categories=frozenset({"shoes"}),
            expires_at=now + timedelta(hours=1),
            max_count=1,
            expected_agent_id="agent-shop-001",
        )

    def request(self, **changes: object) -> TransactionRequest:
        values = {
            "request_id": "request-001",
            "amount": Decimal("480.00"),
            "merchant": "merchant-a",
            "category": "shoes",
            "occurred_at": self.now,
            "sequence_count": 1,
            "agent_id": "agent-shop-001",
        }
        values.update(changes)
        return TransactionRequest(**values)

    def order(self, **changes: object) -> Order:
        values = {
            "order_id": "order-009",
            "order_version": "v1",
            "merchant": "merchant-a",
            "payee": "merchant-a",
            "items": (
                OrderItem(
                    item_id="shoe-001",
                    name="Road Runner",
                    category="shoes",
                    quantity=1,
                    unit_amount=Decimal("480.00"),
                ),
            ),
            "total_amount": Decimal("480.00"),
            "currency": "CNY",
            "quote_expires_at": self.now + timedelta(minutes=30),
            "fulfilment_terms": "standard delivery",
            "mandate_ref": "mandate-001",
        }
        values.update(changes)
        return Order(**values)

    def assert_order_issue(self, code: str, authorized_order: Order) -> None:
        result = validate_request(
            self.mandate,
            self.request(),
            authorized_order=authorized_order,
            final_order=self.order(order_version="v2"),
        )
        self.assertEqual(Decision.INDETERMINATE, result.decision)
        self.assertEqual({code}, {issue.code for issue in result.issues})
        self.assertIn(code, {item.code for item in result.evidence})

    def assert_issue(self, decision: Decision, code: str, **changes: object) -> None:
        result = validate_request(self.mandate, self.request(**changes))
        self.assertEqual(decision, result.decision)
        self.assertIn(code, {issue.code for issue in result.issues})
        self.assertIn(code, {item.code for item in result.evidence})

    def test_allows_request_within_mandate(self) -> None:
        result = validate_request(self.mandate, self.request())
        self.assertEqual(Decision.ALLOW, result.decision)
        self.assertTrue(result.approved)
        self.assertEqual((), result.issues)

    def test_denies_over_hard_limit(self) -> None:
        self.assert_issue(Decision.DENY, "over_budget", amount=Decimal("560.00"))

    def test_denies_out_of_scope_category(self) -> None:
        self.assert_issue(Decision.DENY, "category_out_of_scope", category="subscription")

    def test_denies_expired_mandate(self) -> None:
        self.assert_issue(
            Decision.DENY,
            "mandate_expired",
            occurred_at=self.mandate.expires_at + timedelta(seconds=1),
        )

    def test_denies_duplicate_request(self) -> None:
        result = validate_request(
            self.mandate,
            self.request(),
            seen_request_ids={"request-001"},
        )
        self.assertEqual(Decision.DENY, result.decision)
        self.assertEqual("duplicate_request", result.issues[0].code)

    def test_denies_out_of_scope_merchant(self) -> None:
        self.assert_issue(Decision.DENY, "merchant_out_of_scope", merchant="merchant-b")

    def test_denies_count_exceeded(self) -> None:
        self.assert_issue(Decision.DENY, "count_exceeded", sequence_count=2)

    def test_denies_declared_agent_mismatch_using_trusted_binding_fact(self) -> None:
        result = validate_request(
            self.mandate,
            self.request(agent_id="agent-shop-other"),
        )
        self.assertEqual(Decision.DENY, result.decision)
        self.assertIn("agent_identity_mismatch", {issue.code for issue in result.issues})
        evidence = {item.code: item for item in result.evidence}
        self.assertEqual("INVALID", evidence["agent_claim_binding_status"].observed)
        self.assertEqual(
            "declared_identity_reference_mismatch",
            evidence["agent_claim_binding_reason"].observed,
        )
        self.assertEqual("agent-shop-other", evidence["agent_identity_mismatch"].observed)

    def test_matching_declared_agent_reference_is_not_claimed_as_authentication(self) -> None:
        result = validate_request(self.mandate, self.request())
        evidence = {item.code: item for item in result.evidence}
        self.assertEqual("VALID", evidence["agent_claim_binding_status"].observed)
        self.assertEqual(
            "declared_identity_reference_match",
            evidence["agent_claim_binding_reason"].observed,
        )
        self.assertNotIn("agent_authenticated", evidence)

    def test_requires_confirmation_above_threshold(self) -> None:
        self.assert_issue(
            Decision.CONFIRMATION_REQUIRED,
            "confirmation_threshold_exceeded",
            amount=Decimal("520.00"),
        )

    def test_returns_indeterminate_for_currency_mismatch(self) -> None:
        self.assert_issue(Decision.INDETERMINATE, "currency_mismatch", currency="USD")

    def test_requires_confirmation_when_final_order_total_changes(self) -> None:
        authorized_order = self.order()
        final_order = self.order(order_version="v2", total_amount=Decimal("490.00"))

        result = validate_request(
            self.mandate,
            self.request(amount=Decimal("490")),
            authorized_order=authorized_order,
            final_order=final_order,
        )

        self.assertEqual(Decision.CONFIRMATION_REQUIRED, result.decision)
        self.assertEqual({"order_total_changed"}, {issue.code for issue in result.issues})
        self.assertIn("order_total_changed", {item.code for item in result.evidence})
        self.assertNotIn("confirmation_threshold_exceeded", {issue.code for issue in result.issues})

    def test_allows_unchanged_order_with_matching_binding(self) -> None:
        result = validate_request(
            self.mandate,
            self.request(),
            authorized_order=self.order(),
            final_order=self.order(order_version="v2"),
        )

        self.assertEqual(Decision.ALLOW, result.decision)
        self.assertEqual((), result.issues)
        evidence_codes = {item.code for item in result.evidence}
        self.assertIn("authorized_order_ref", evidence_codes)
        self.assertIn("final_order_ref", evidence_codes)

    def test_rejects_authorized_order_for_another_mandate(self) -> None:
        self.assert_order_issue(
            "authorized_order_mandate_mismatch",
            self.order(mandate_ref="mandate-other"),
        )

    def test_rejects_authorized_order_for_another_merchant(self) -> None:
        self.assert_order_issue(
            "authorized_order_merchant_mismatch",
            self.order(merchant="merchant-other"),
        )

    def test_rejects_authorized_order_in_another_currency(self) -> None:
        self.assert_order_issue(
            "authorized_order_currency_mismatch",
            self.order(currency="USD"),
        )


if __name__ == "__main__":
    unittest.main()

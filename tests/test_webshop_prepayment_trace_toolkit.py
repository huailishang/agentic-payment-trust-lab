from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment.authoritative_trace import (
    TraceValidationStatus,
    validate_product_authoritative_trace,
)
from agentic_payment_experiment.models import (
    Decision,
    IntentMandate,
    Order,
    OrderDifference,
    OrderItem,
    TransactionRequest,
    ValidationIssue,
    ValidationResult,
)
from agentic_payment_experiment.webshop_prepayment_trace_profiles import (
    PREPAYMENT_TRACE_PROFILES,
    PrepaymentScenarioKind,
    PrepaymentTraceProfile,
)
from agentic_payment_experiment.webshop_prepayment_trace_toolkit import (
    _select_profile,
    build_prepayment_product_trace,
)
from agentic_payment_experiment.webshop_runtime_gate import WebShopBuyNowGateOutcome


PRICE_CODES = (
    "order_item_unit_amount_changed",
    "order_total_changed",
)
EXPECTED_EVENTS = (
    "AUTHORITY_RECORDED",
    "ORDER_RECORDED",
    "ORDER_RECORDED",
    "REQUEST_RECORDED",
    "PREPAYMENT_DECISION_RECORDED",
    "RESULT_RECORDED",
)
EXPECTED_ROLES = (
    "AUTHORITY",
    "AUTHORIZED_ORDER_SNAPSHOT",
    "CURRENT_ORDER_SNAPSHOT",
    "CURRENT_REQUEST",
    "PREPAYMENT_VALIDATION",
    "FINAL_OUTCOME",
)


class WebShopPrepaymentTraceToolkitTest(unittest.TestCase):
    def setUp(self) -> None:
        occurred_at = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
        self.mandate = IntentMandate(
            mandate_id="mandate-prepayment-1",
            user_id="user-prepayment-1",
            max_amount=Decimal("100.00"),
            allowed_merchants=frozenset({"merchant-prepayment"}),
            allowed_categories=frozenset({"goods"}),
            expires_at=occurred_at + timedelta(hours=1),
            expected_agent_id="agent-prepayment-1",
            currency="CNY",
            authority_version="authority-v1",
        )
        self.authorized_order = Order(
            order_id="order-prepayment-1",
            order_version="order-v1",
            merchant="merchant-prepayment",
            payee="payee-prepayment-a",
            items=(
                OrderItem(
                    item_id="item-a",
                    name="Item A",
                    category="goods",
                    quantity=1,
                    unit_amount=Decimal("10.00"),
                ),
                OrderItem(
                    item_id="item-b",
                    name="Item B",
                    category="goods",
                    quantity=1,
                    unit_amount=Decimal("20.00"),
                ),
            ),
            total_amount=Decimal("30.00"),
            currency="CNY",
            quote_expires_at=occurred_at + timedelta(minutes=30),
            fulfilment_terms="standard",
            mandate_ref=self.mandate.mandate_id,
            authority_version_ref=self.mandate.authority_version,
        )
        self.occurred_at = occurred_at

    def price_result(self) -> ValidationResult:
        return ValidationResult(
            decision=Decision.CONFIRMATION_REQUIRED,
            issues=tuple(ValidationIssue(code, code) for code in PRICE_CODES),
            evidence=(),
            order_differences=(
                OrderDifference(
                    "order_item_unit_amount_changed",
                    "items[item-a].unit_amount",
                    "10.00",
                    "11.00",
                ),
                OrderDifference(
                    "order_total_changed",
                    "total_amount",
                    "30.00",
                    "31.00",
                ),
            ),
        )

    def payee_result(self) -> ValidationResult:
        return ValidationResult(
            decision=Decision.INDETERMINATE,
            issues=(ValidationIssue("order_payee_changed", "order_payee_changed"),),
            evidence=(),
            order_differences=(),
        )

    def current_order(self, kind: PrepaymentScenarioKind) -> Order:
        if kind is PrepaymentScenarioKind.PRICE_INCREASE:
            items = (
                replace(self.authorized_order.items[0], unit_amount=Decimal("11.00")),
                self.authorized_order.items[1],
            )
            return replace(
                self.authorized_order,
                order_version="order-v2",
                items=items,
                total_amount=Decimal("31.00"),
            )
        if kind is PrepaymentScenarioKind.PRICE_DECREASE:
            items = (
                replace(self.authorized_order.items[0], unit_amount=Decimal("9.00")),
                self.authorized_order.items[1],
            )
            return replace(
                self.authorized_order,
                order_version="order-v2",
                items=items,
                total_amount=Decimal("29.00"),
            )
        if kind is PrepaymentScenarioKind.PAYEE_CHANGE:
            return replace(
                self.authorized_order,
                order_version="order-v2",
                payee="payee-prepayment-b",
            )
        raise AssertionError(kind)

    def bound_request(self, current_order: Order) -> TransactionRequest:
        return TransactionRequest(
            request_id=f"request-{current_order.order_version}",
            amount=current_order.total_amount,
            merchant=current_order.merchant,
            category="goods",
            occurred_at=self.occurred_at,
            agent_id="agent-prepayment-1",
            currency=current_order.currency,
            order_ref=current_order.order_id,
            authority_ref=self.mandate.mandate_id,
            authority_version_ref=self.mandate.authority_version,
            payee=current_order.payee,
        )

    def base_outcome(
        self,
        request: TransactionRequest,
        result: ValidationResult,
    ) -> WebShopBuyNowGateOutcome:
        return WebShopBuyNowGateOutcome(
            decision=result.decision,
            checkout_executed=False,
            callback_count=0,
            callback_result_ref=None,
            bound_request=request,
            prepayment_result=result,
            runtime_gate_record=None,
            reason_codes=tuple(f"p1:{issue.code}" for issue in result.issues),
        )

    def build_case(self, kind: PrepaymentScenarioKind):
        current = self.current_order(kind)
        request = self.bound_request(current)
        result = (
            self.payee_result()
            if kind is PrepaymentScenarioKind.PAYEE_CHANGE
            else self.price_result()
        )
        outcome = self.base_outcome(request, result)
        trace = build_prepayment_product_trace(
            mandate=self.mandate,
            authorized_order=self.authorized_order,
            current_order=current,
            bound_request=request,
            validation_result=result,
            base_outcome=outcome,
        )
        return current, request, result, outcome, trace

    def test_positive_selector_uses_order_value_direction_for_t02_t03_and_payee_for_t04(self) -> None:
        expected_profiles = {
            PrepaymentScenarioKind.PRICE_INCREASE: "WEBSHOP_PREPAYMENT_T02_V2",
            PrepaymentScenarioKind.PRICE_DECREASE: "WEBSHOP_PREPAYMENT_T03_V2",
            PrepaymentScenarioKind.PAYEE_CHANGE: "WEBSHOP_PREPAYMENT_T04_V2",
        }
        for kind, expected_profile in expected_profiles.items():
            with self.subTest(kind=kind.value):
                current = self.current_order(kind)
                result = (
                    self.payee_result()
                    if kind is PrepaymentScenarioKind.PAYEE_CHANGE
                    else self.price_result()
                )
                selected = _select_profile(
                    authorized_order=self.authorized_order,
                    current_order=current,
                    validation_result=result,
                )
                self.assertIsNotNone(selected)
                assert selected is not None
                self.assertEqual(expected_profile, selected.profile_name)
                self.assertIs(kind, selected.scenario_kind)

    def test_same_price_reason_codes_select_opposite_profiles_only_from_order_values(self) -> None:
        result = self.price_result()
        increased = _select_profile(
            authorized_order=self.authorized_order,
            current_order=self.current_order(PrepaymentScenarioKind.PRICE_INCREASE),
            validation_result=result,
        )
        decreased = _select_profile(
            authorized_order=self.authorized_order,
            current_order=self.current_order(PrepaymentScenarioKind.PRICE_DECREASE),
            validation_result=result,
        )
        self.assertEqual(PrepaymentScenarioKind.PRICE_INCREASE, increased.scenario_kind)
        self.assertEqual(PrepaymentScenarioKind.PRICE_DECREASE, decreased.scenario_kind)

    def test_t02_t03_t04_build_exact_valid_six_event_six_binding_product_trace(self) -> None:
        for kind in PrepaymentScenarioKind:
            with self.subTest(kind=kind.value):
                _, _, _, _, trace = self.build_case(kind)
                self.assertIsNotNone(trace)
                assert trace is not None
                validation = validate_product_authoritative_trace(trace)
                self.assertIs(TraceValidationStatus.VALID, validation.status)
                self.assertEqual(EXPECTED_EVENTS, tuple(event.event_type for event in trace.events))
                self.assertEqual(EXPECTED_ROLES, tuple(event.entity_role for event in trace.events))
                self.assertEqual(6, len(trace.events))
                self.assertEqual(6, len(trace.source_bindings))
                self.assertEqual("PRODUCT_OBSERVED", trace.source)
                self.assertEqual("COMPLETE", trace.completeness_status)

    def test_zero_match_for_unchanged_price_even_when_price_reason_codes_claim_change(self) -> None:
        self.assertIsNone(
            _select_profile(
                authorized_order=self.authorized_order,
                current_order=replace(self.authorized_order, order_version="order-v2"),
                validation_result=self.price_result(),
            )
        )

    def test_duplicate_matching_profiles_fail_closed(self) -> None:
        profile = PREPAYMENT_TRACE_PROFILES[0]
        selected = _select_profile(
            authorized_order=self.authorized_order,
            current_order=self.current_order(PrepaymentScenarioKind.PRICE_INCREASE),
            validation_result=self.price_result(),
            profiles=(profile, profile),
        )
        self.assertIsNone(selected)

    def test_mixed_item_price_directions_fail_closed(self) -> None:
        current = replace(
            self.authorized_order,
            order_version="order-v2",
            items=(
                replace(self.authorized_order.items[0], unit_amount=Decimal("11.00")),
                replace(self.authorized_order.items[1], unit_amount=Decimal("19.00")),
            ),
            total_amount=Decimal("31.00"),
        )
        self.assertIsNone(
            _select_profile(
                authorized_order=self.authorized_order,
                current_order=current,
                validation_result=self.price_result(),
            )
        )

    def test_price_plus_payee_change_fails_closed(self) -> None:
        current = replace(
            self.current_order(PrepaymentScenarioKind.PRICE_INCREASE),
            payee="payee-prepayment-b",
        )
        self.assertIsNone(
            _select_profile(
                authorized_order=self.authorized_order,
                current_order=current,
                validation_result=self.price_result(),
            )
        )
        self.assertIsNone(
            _select_profile(
                authorized_order=self.authorized_order,
                current_order=current,
                validation_result=self.payee_result(),
            )
        )

    def test_missing_or_invalid_authority_and_bound_request_facts_fail_closed(self) -> None:
        current, request, result, outcome, _ = self.build_case(
            PrepaymentScenarioKind.PRICE_INCREASE
        )
        cases = (
            {
                "mandate": replace(self.mandate, mandate_id="wrong-mandate"),
                "bound_request": request,
                "base_outcome": outcome,
            },
            {
                "mandate": self.mandate,
                "bound_request": replace(request, authority_ref="wrong-mandate"),
                "base_outcome": replace(
                    outcome,
                    bound_request=replace(request, authority_ref="wrong-mandate"),
                ),
            },
            {
                "mandate": self.mandate,
                "bound_request": replace(request, amount=Decimal("999.00")),
                "base_outcome": replace(
                    outcome,
                    bound_request=replace(request, amount=Decimal("999.00")),
                ),
            },
        )
        for case in cases:
            with self.subTest(case=case):
                self.assertIsNone(
                    build_prepayment_product_trace(
                        mandate=case["mandate"],
                        authorized_order=self.authorized_order,
                        current_order=current,
                        bound_request=case["bound_request"],
                        validation_result=result,
                        base_outcome=case["base_outcome"],
                    )
                )

    def test_existing_authoritative_trace_is_never_overwritten(self) -> None:
        current, request, result, outcome, trace = self.build_case(
            PrepaymentScenarioKind.PRICE_INCREASE
        )
        self.assertIsNotNone(trace)
        self.assertIsNone(
            build_prepayment_product_trace(
                mandate=self.mandate,
                authorized_order=self.authorized_order,
                current_order=current,
                bound_request=request,
                validation_result=result,
                base_outcome=replace(outcome, authoritative_trace=trace),
            )
        )

    def test_invalid_profile_container_or_profile_type_fails_closed(self) -> None:
        current = self.current_order(PrepaymentScenarioKind.PRICE_INCREASE)
        result = self.price_result()
        invalid_profile = PrepaymentTraceProfile(
            profile_name="INVALID",
            scenario_kind=PrepaymentScenarioKind.PRICE_INCREASE,
            expected_decision=Decision.CONFIRMATION_REQUIRED,
            required_issue_codes=PRICE_CODES,
            required_difference_codes=PRICE_CODES,
        )
        self.assertIsNone(
            _select_profile(
                authorized_order=self.authorized_order,
                current_order=current,
                validation_result=result,
                profiles=[invalid_profile],  # type: ignore[arg-type]
            )
        )
        self.assertIsNone(
            _select_profile(
                authorized_order=self.authorized_order,
                current_order=current,
                validation_result=result,
                profiles=("not-a-profile",),  # type: ignore[arg-type]
            )
        )


if __name__ == "__main__":
    unittest.main()

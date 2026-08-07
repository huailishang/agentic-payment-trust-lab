from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment import (
    Decision,
    KnownPaymentAttemptPreflightStatus,
    PaymentStatus,
)
from agentic_payment_experiment.authoritative_trace import (
    TraceSourceBinding,
    TraceValidationStatus,
    compute_binding_ref,
    compute_projection_source_ref,
    validate_product_authoritative_trace,
)
from agentic_payment_experiment.webshop_authoritative_trace import (
    T10_PROFILE,
)
from tests import test_webshop_runtime_gate as runtime_gate_tests


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "src/agentic_payment_experiment/webshop_authoritative_trace.py"


def _case() -> runtime_gate_tests.WebShopRuntimeGateTest:
    case = runtime_gate_tests.WebShopRuntimeGateTest(methodName="runTest")
    case.setUp()
    return case


def _valid_t10():
    case = _case()
    historical = replace(
        case.execution,
        payment_id="webshop-payment-existing-success",
        status=PaymentStatus.SUCCEEDED,
    )
    outcome, calls = case.invoke(
        governed_action=case.governed_action,
        known_payment_attempts=(historical,),
    )
    assert outcome.authoritative_trace is not None
    return case, historical, outcome, calls


class WebShopAuthoritativeTraceTest(unittest.TestCase):
    def test_real_t10_gate_emits_exact_valid_product_trace(self) -> None:
        case, historical, outcome, calls = _valid_t10()
        trace = outcome.authoritative_trace
        assert trace is not None
        validation = validate_product_authoritative_trace(trace)

        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertEqual([], calls)
        self.assertEqual(TraceValidationStatus.VALID, validation.status)
        self.assertEqual(("product_authoritative_trace_valid",), validation.reason_codes)
        self.assertEqual(T10_PROFILE, validation.profile)
        self.assertEqual(12, len(trace.events))
        self.assertEqual(11, len(trace.source_bindings))
        self.assertEqual(
            f"ProductAuthoritativeTrace:{T10_PROFILE}:{case.bound_request.request_id}",
            trace.trace_ref,
        )

        by_role = {event.entity_role: event for event in trace.events}
        self.assertEqual(
            by_role["AUTHORIZED_ORDER_SNAPSHOT"].source_binding_ref,
            by_role["CURRENT_ORDER_SNAPSHOT"].source_binding_ref,
        )
        self.assertNotEqual(
            by_role["CURRENT_PAYMENT_CANDIDATE"].source_binding_ref,
            by_role["HISTORICAL_SUCCEEDED_PAYMENT"].source_binding_ref,
        )
        self.assertNotEqual(
            by_role["CURRENT_PAYMENT_CANDIDATE"].entity_ref,
            by_role["HISTORICAL_SUCCEEDED_PAYMENT"].entity_ref,
        )
        self.assertEqual(
            case.execution.payment_id,
            by_role["CURRENT_PAYMENT_CANDIDATE"].entity_ref.split(":", 1)[1],
        )
        self.assertEqual(
            historical.payment_id,
            by_role["HISTORICAL_SUCCEEDED_PAYMENT"].entity_ref.split(":", 1)[1],
        )
        self.assertEqual("SUCCEEDED", by_role["HISTORICAL_SUCCEEDED_PAYMENT"].status)
        self.assertEqual("BLOCKED", by_role["KNOWN_PAYMENT_PREFLIGHT_FACT"].status)
        self.assertEqual("DENY", by_role["PREPAYMENT_VALIDATION"].decision)
        self.assertEqual("DENY", by_role["RUNTIME_GATE_OBSERVATION"].decision)
        self.assertEqual("DENY", by_role["FINAL_OUTCOME"].decision)
        self.assertTrue(
            all(
                relation.target_resolved is True
                for event in trace.events
                for relation in event.relations
            )
        )

    def test_outcome_contract_remains_frozen_and_default_trace_is_none(self) -> None:
        case = _case()
        outcome, calls = case.invoke()

        self.assertEqual(Decision.ALLOW, outcome.decision)
        self.assertEqual(["checkout"], calls)
        self.assertIsNone(outcome.authoritative_trace)
        with self.assertRaises(FrozenInstanceError):
            outcome.authoritative_trace = None  # type: ignore[misc]

    def test_non_t10_paths_never_emit_trace(self) -> None:
        case = _case()
        historical = replace(
            case.execution,
            payment_id="webshop-payment-existing-success",
            status=PaymentStatus.SUCCEEDED,
        )
        invalid_history = replace(
            historical,
            payment_id="webshop-payment-invalid-history",
            amount=historical.amount + Decimal("1.00"),
        )
        unrelated = replace(
            historical,
            payment_id="webshop-payment-unrelated",
            request_id="unrelated-request",
            transaction_object_ref="unrelated-request",
        )
        invalid_action = replace(case.governed_action, agent_ref="agent-evil")
        restrictive_mandate = replace(case.mandate, max_amount=Decimal("1.00"))

        scenarios = (
            ("prepayment_deny", {"mandate": restrictive_mandate}),
            ("action_invalid", {"governed_action": invalid_action}),
            (
                "known_attempt_indeterminate",
                {
                    "governed_action": case.governed_action,
                    "known_payment_attempts": (invalid_history,),
                },
            ),
            (
                "known_attempt_clear",
                {
                    "governed_action": case.governed_action,
                    "known_payment_attempts": (unrelated,),
                },
            ),
        )
        for name, overrides in scenarios:
            with self.subTest(name=name):
                outcome, _ = case.invoke(**overrides)
                self.assertIsNone(outcome.authoritative_trace)

    def test_duplicate_block_without_governed_action_fails_closed_for_trace(self) -> None:
        case = _case()
        historical = replace(
            case.execution,
            payment_id="webshop-payment-existing-success",
            status=PaymentStatus.SUCCEEDED,
        )
        outcome, calls = case.invoke(known_payment_attempts=(historical,))

        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertEqual([], calls)
        self.assertEqual(
            KnownPaymentAttemptPreflightStatus.BLOCKED,
            outcome.known_payment_attempt_preflight_fact.status,
        )
        self.assertIsNone(outcome.governed_action_fact)
        self.assertIsNone(outcome.authoritative_trace)

    def test_multiple_related_historical_payments_fail_closed_for_trace(self) -> None:
        case = _case()
        first = replace(
            case.execution,
            payment_id="webshop-payment-existing-success-a",
            status=PaymentStatus.SUCCEEDED,
        )
        second = replace(
            case.execution,
            payment_id="webshop-payment-existing-success-b",
            status=PaymentStatus.SUCCEEDED,
        )
        outcome, calls = case.invoke(
            governed_action=case.governed_action,
            known_payment_attempts=(first, second),
        )

        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertEqual([], calls)
        self.assertEqual(
            (first.payment_id, second.payment_id),
            outcome.known_payment_attempt_preflight_fact.related_attempt_refs,
        )
        self.assertIsNone(outcome.authoritative_trace)

    def test_current_and_historical_payment_binding_cannot_be_merged(self) -> None:
        _, _, outcome, _ = _valid_t10()
        trace = outcome.authoritative_trace
        assert trace is not None
        current = trace.events[5]
        historical = trace.events[7]
        tampered_historical = replace(
            historical,
            entity_ref=current.entity_ref,
            source_binding_ref=current.source_binding_ref,
            status=current.status,
        )
        tampered = replace(
            trace,
            events=(*trace.events[:7], tampered_historical, *trace.events[8:]),
            source_bindings=tuple(
                binding
                for binding in trace.source_bindings
                if binding.binding_ref != historical.source_binding_ref
            ),
        )

        validation = validate_product_authoritative_trace(tampered)
        self.assertNotEqual(TraceValidationStatus.VALID, validation.status)

    def test_two_order_roles_must_share_one_binding(self) -> None:
        _, _, outcome, _ = _valid_t10()
        trace = outcome.authoritative_trace
        assert trace is not None
        authorized = trace.events[1]
        original_binding = next(
            binding
            for binding in trace.source_bindings
            if binding.binding_ref == authorized.source_binding_ref
        )
        changed_projection = dict(original_binding.projection)
        changed_projection["order_version"] = "tampered-order-version"
        changed_source_ref = compute_projection_source_ref(
            original_binding.source_object_type,
            original_binding.projection_schema,
            changed_projection,
        )
        payload = {
            "source_object_type": original_binding.source_object_type,
            "source_object_ref": changed_source_ref,
            "projection_schema": original_binding.projection_schema,
            "projection": changed_projection,
        }
        changed_binding = TraceSourceBinding(
            binding_ref=compute_binding_ref(payload),
            source_object_type=original_binding.source_object_type,
            source_object_ref=changed_source_ref,
            projection_schema=original_binding.projection_schema,
            projection=changed_projection,
        )
        tampered_authorized = replace(
            authorized,
            source_binding_ref=changed_binding.binding_ref,
        )
        tampered = replace(
            trace,
            events=(trace.events[0], tampered_authorized, *trace.events[2:]),
            source_bindings=(*trace.source_bindings, changed_binding),
        )

        validation = validate_product_authoritative_trace(tampered)
        self.assertEqual(TraceValidationStatus.INVALID, validation.status)
        self.assertIn("trace_binding_alias_mismatch", validation.reason_codes)

    def test_result_projection_cannot_include_authoritative_trace(self) -> None:
        _, _, outcome, _ = _valid_t10()
        trace = outcome.authoritative_trace
        assert trace is not None
        result_event = trace.events[-1]
        result_binding = next(
            binding
            for binding in trace.source_bindings
            if binding.binding_ref == result_event.source_binding_ref
        )
        projection = dict(result_binding.projection)
        projection["authoritative_trace"] = {"profile": trace.profile}
        source_ref = compute_projection_source_ref(
            result_binding.source_object_type,
            result_binding.projection_schema,
            projection,
        )
        payload = {
            "source_object_type": result_binding.source_object_type,
            "source_object_ref": source_ref,
            "projection_schema": result_binding.projection_schema,
            "projection": projection,
        }
        changed_binding = TraceSourceBinding(
            binding_ref=compute_binding_ref(payload),
            source_object_type=result_binding.source_object_type,
            source_object_ref=source_ref,
            projection_schema=result_binding.projection_schema,
            projection=projection,
        )
        changed_event = replace(
            result_event,
            source_binding_ref=changed_binding.binding_ref,
        )
        tampered = replace(
            trace,
            events=(*trace.events[:-1], changed_event),
            source_bindings=(
                *tuple(
                    item
                    for item in trace.source_bindings
                    if item.binding_ref != result_binding.binding_ref
                ),
                changed_binding,
            ),
        )

        validation = validate_product_authoritative_trace(tampered)
        self.assertEqual(TraceValidationStatus.INVALID, validation.status)
        self.assertIn("trace_projection_field_extra", validation.reason_codes)

    def test_builder_has_no_hidden_replay_or_business_rule_dependency(self) -> None:
        source = BUILDER_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "ReplayEvent",
            "GateContext",
            "run_project_impact_baseline",
            "validate_request(",
            "verify_governed_payment_action(",
            "derive_known_payment_attempt_preflight(",
            "execute_with_payment_binding_gate(",
            "Path(",
            "open(",
            "read_text(",
            "getenv(",
            "import random",
            "random.",
            "datetime.now",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()

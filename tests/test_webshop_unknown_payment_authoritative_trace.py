from __future__ import annotations

import ast
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment import (
    FulfillmentStatus,
    PaymentRecoveryStatus,
    PaymentStatus,
    TaskStatus,
    assess_webshop_payment_fulfilment,
)
from agentic_payment_experiment.authoritative_trace import (
    TraceValidationStatus,
    validate_product_authoritative_trace,
)
from agentic_payment_experiment.models import PaymentStatusObservation
from agentic_payment_experiment.webshop_unknown_payment_authoritative_trace import (
    UNKNOWN_PAYMENT_RECOVERY_PROFILE,
    build_unknown_payment_recovery_trace,
)
from tests import test_webshop_payment_sidecar as sidecar_tests


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = (
    ROOT / "src/agentic_payment_experiment/webshop_unknown_payment_authoritative_trace.py"
)


def _valid_t09():
    case = sidecar_tests.WebShopPaymentSidecarTest(methodName="runTest")
    case.setUp()
    gate, candidate, _, fulfillment = case.happy_path_inputs()
    payment = replace(
        candidate,
        status=PaymentStatus.UNKNOWN,
        receipt_ref="offline-unknown-payment-receipt",
    )
    query = PaymentStatusObservation(
        payment_id=payment.payment_id,
        order_id=payment.order_id,
        status=PaymentStatus.SUCCEEDED,
        observed_at=payment.occurred_at + timedelta(minutes=1),
        source="query",
        provider_ref=payment.provider_ref,
    )
    fulfillment = replace(
        fulfillment,
        status=FulfillmentStatus.SUCCEEDED,
        failure_code=None,
    )
    outcome = assess_webshop_payment_fulfilment(
        gate_outcome=gate,
        adaptation=case.adaptation,
        mandate=case.mandate,
        payment=payment,
        fulfillment=fulfillment,
        query_observation=query,
    )
    return case, gate, candidate, payment, query, fulfillment, outcome


class WebShopUnknownPaymentAuthoritativeTraceTest(unittest.TestCase):
    def test_real_t09_sidecar_emits_exact_valid_product_trace(self) -> None:
        _, _, candidate, payment, _, _, outcome = _valid_t09()
        trace = outcome.authoritative_trace
        assert trace is not None
        validation = validate_product_authoritative_trace(trace)

        self.assertEqual(TraceValidationStatus.VALID, validation.status)
        self.assertEqual(UNKNOWN_PAYMENT_RECOVERY_PROFILE, validation.profile)
        self.assertEqual("PRODUCT_OBSERVED", trace.source)
        self.assertEqual(11, len(trace.events))
        self.assertEqual(10, len(trace.source_bindings))
        self.assertEqual(PaymentStatus.UNKNOWN, outcome.initial_payment.status)
        self.assertEqual(PaymentStatus.SUCCEEDED, outcome.effective_payment.status)
        self.assertEqual(
            PaymentRecoveryStatus.RECOVERED,
            outcome.query_recovery.recovery_status,
        )
        self.assertEqual(TaskStatus.SUCCEEDED, outcome.lifecycle.task_status)
        self.assertFalse(outcome.retry_allowed)
        self.assertFalse(outcome.duplicate_payment_blocked)

        by_role = {event.entity_role: event for event in trace.events}
        self.assertEqual("PENDING", by_role["CURRENT_PAYMENT_CANDIDATE"].status)
        self.assertEqual("SUCCEEDED", by_role["PAYMENT_EXECUTION_OUTCOME"].status)
        self.assertEqual("RECOVERED", by_role["RECOVERY_OUTCOME"].status)
        self.assertEqual("SUCCEEDED", by_role["FINAL_OUTCOME"].status)
        self.assertEqual(candidate.payment_id, payment.payment_id)
        self.assertEqual(
            by_role["CURRENT_PAYMENT_CANDIDATE"].entity_ref,
            by_role["PAYMENT_EXECUTION_OUTCOME"].entity_ref,
        )
        self.assertNotEqual(
            by_role["CURRENT_PAYMENT_CANDIDATE"].source_binding_ref,
            by_role["PAYMENT_EXECUTION_OUTCOME"].source_binding_ref,
        )
        self.assertEqual(
            by_role["AUTHORIZED_ORDER_SNAPSHOT"].source_binding_ref,
            by_role["CURRENT_ORDER_SNAPSHOT"].source_binding_ref,
        )

    def test_t09_event_order_and_recovery_projection_are_exact(self) -> None:
        _, _, _, _, _, _, outcome = _valid_t09()
        trace = outcome.authoritative_trace
        assert trace is not None
        self.assertEqual(
            (
                "AUTHORITY_RECORDED",
                "ORDER_RECORDED",
                "ORDER_RECORDED",
                "REQUEST_RECORDED",
                "ACTION_RECORDED",
                "PAYMENT_CANDIDATE_RECORDED",
                "ACTION_BINDING_DECISION_RECORDED",
                "RUNTIME_DECISION_RECORDED",
                "PAYMENT_OUTCOME_RECORDED",
                "RECOVERY_OUTCOME_RECORDED",
                "RESULT_RECORDED",
            ),
            tuple(event.event_type for event in trace.events),
        )
        recovery_event = trace.events[9]
        recovery_binding = next(
            item
            for item in trace.source_bindings
            if item.binding_ref == recovery_event.source_binding_ref
        )
        self.assertEqual("UNKNOWN", recovery_binding.projection["initial_status"])
        self.assertEqual("SUCCEEDED", recovery_binding.projection["observed_status"])
        self.assertEqual("SUCCEEDED", recovery_binding.projection["effective_status"])
        self.assertEqual("RECOVERED", recovery_binding.projection["recovery_status"])
        self.assertFalse(recovery_binding.projection["retry_allowed"])
        self.assertEqual(
            ("payment_state_recovered_as_succeeded",),
            recovery_binding.projection["issue_codes"],
        )

    def test_t09_builder_negative_matrix_fails_closed(self) -> None:
        case, gate, _, _, _, _, outcome = _valid_t09()
        assert outcome.query_recovery is not None
        assert outcome.effective_payment is not None
        assert outcome.lifecycle is not None
        base = replace(outcome, authoritative_trace=None)

        cases = (
            ("missing_recovery", gate, replace(base, query_recovery=None)),
            (
                "recovery_unresolved",
                gate,
                replace(
                    base,
                    query_recovery=replace(
                        base.query_recovery,
                        recovery_status=PaymentRecoveryStatus.UNRESOLVED,
                    ),
                ),
            ),
            (
                "effective_not_succeeded",
                gate,
                replace(
                    base,
                    effective_payment=replace(
                        base.effective_payment,
                        status=PaymentStatus.FAILED,
                    ),
                ),
            ),
            (
                "retry_allowed",
                gate,
                replace(
                    base,
                    retry_allowed=True,
                    query_recovery=replace(base.query_recovery, retry_allowed=True),
                ),
            ),
            (
                "lifecycle_not_success",
                gate,
                replace(
                    base,
                    lifecycle=replace(base.lifecycle, task_status=TaskStatus.FAILED),
                ),
            ),
            (
                "candidate_not_pending",
                replace(
                    gate,
                    execution_candidate=replace(
                        gate.execution_candidate,
                        status=PaymentStatus.UNKNOWN,
                    ),
                ),
                base,
            ),
            (
                "retained_order_missing",
                replace(gate, authorized_order_snapshot=None),
                base,
            ),
        )
        for name, selected_gate, selected_outcome in cases:
            with self.subTest(name=name):
                self.assertIsNone(
                    build_unknown_payment_recovery_trace(
                        gate_outcome=selected_gate,
                        adaptation=case.adaptation,
                        mandate=case.mandate,
                        base_outcome=selected_outcome,
                    )
                )

    def test_non_t09_sidecar_paths_do_not_emit_t09_profile(self) -> None:
        case = sidecar_tests.WebShopPaymentSidecarTest(methodName="runTest")
        case.setUp()
        ordinary = case.assess()
        self.assertIsNone(ordinary.authoritative_trace)

        gate, _, payment, fulfillment = case.happy_path_inputs()
        happy = assess_webshop_payment_fulfilment(
            gate_outcome=gate,
            adaptation=case.adaptation,
            mandate=case.mandate,
            payment=payment,
            fulfillment=fulfillment,
        )
        assert happy.authoritative_trace is not None
        self.assertEqual("WEBSHOP_NORMAL_PURCHASE_V2", happy.authoritative_trace.profile)

    def test_builder_has_no_hidden_inputs_or_business_calls(self) -> None:
        source = BUILDER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports: set[str] = set()
        calls: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module or "")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
        self.assertTrue(
            imports.isdisjoint(
                {"os", "pathlib", "socket", "subprocess", "requests", "urllib", "random", "time"}
            ),
            imports,
        )
        self.assertTrue(
            calls.isdisjoint(
                {
                    "open",
                    "read_text",
                    "write_text",
                    "getenv",
                    "run",
                    "Popen",
                    "urlopen",
                    "assess_payment_recovery",
                    "assess_lifecycle",
                    "verify_governed_payment_action",
                    "gate_webshop_buy_now",
                    "checkout_callback",
                    "execute_payment",
                }
            ),
            calls,
        )
        self.assertNotIn("PaymentStatusObservation", source)
        self.assertNotIn("run_project_impact_baseline", source)
        self.assertNotIn("CURRENT.md", source)


if __name__ == "__main__":
    unittest.main()

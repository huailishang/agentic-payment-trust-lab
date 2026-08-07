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
    RemediationStatus,
    TaskStatus,
    assess_webshop_payment_fulfilment,
)
from agentic_payment_experiment.authoritative_trace import (
    TraceValidationStatus,
    validate_product_authoritative_trace,
)
from agentic_payment_experiment.models import PaymentStatusObservation
from agentic_payment_experiment.payment_status_conflict import (
    PaymentStatusConflictResolution,
)
from agentic_payment_experiment.webshop_sidecar_trace_profiles import (
    SIDECAR_TRACE_PROFILES,
    SidecarExtensionKind,
    T01_PROFILE,
    T09_PROFILE,
    T12_PROFILE,
)
from agentic_payment_experiment.webshop_sidecar_trace_toolkit import (
    _select_profile,
    build_sidecar_product_trace,
)
from tests import test_webshop_payment_sidecar as sidecar_tests
from tests.test_webshop_unknown_payment_authoritative_trace import _valid_t09


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/agentic_payment_experiment"
SIDECAR_PATH = SRC / "webshop_payment_sidecar.py"
TOOLKIT_PATH = SRC / "webshop_sidecar_trace_toolkit.py"
PROFILES_PATH = SRC / "webshop_sidecar_trace_profiles.py"
T01_ADAPTER_PATH = SRC / "webshop_happy_path_authoritative_trace.py"
T09_ADAPTER_PATH = SRC / "webshop_unknown_payment_authoritative_trace.py"


def _valid_t01():
    case = sidecar_tests.WebShopPaymentSidecarTest(methodName="runTest")
    case.setUp()
    gate, candidate, payment, fulfillment = case.happy_path_inputs()
    outcome = assess_webshop_payment_fulfilment(
        gate_outcome=gate,
        adaptation=case.adaptation,
        mandate=case.mandate,
        payment=payment,
        fulfillment=fulfillment,
    )
    return case, gate, candidate, payment, fulfillment, outcome


def _valid_t12():
    case = sidecar_tests.WebShopPaymentSidecarTest(methodName="runTest")
    case.setUp()
    gate, candidate, _, fulfillment = case.happy_path_inputs()
    payment = replace(
        candidate,
        status=PaymentStatus.UNKNOWN,
        receipt_ref="offline-status-conflict-receipt",
    )
    query = PaymentStatusObservation(
        payment_id=payment.payment_id,
        order_id=payment.order_id,
        status=PaymentStatus.SUCCEEDED,
        observed_at=payment.occurred_at + timedelta(minutes=1),
        source="query",
        provider_ref=payment.provider_ref,
    )
    async_observation = PaymentStatusObservation(
        payment_id=payment.payment_id,
        order_id=payment.order_id,
        status=PaymentStatus.FAILED,
        observed_at=payment.occurred_at + timedelta(minutes=2),
        source="async",
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
        async_observation=async_observation,
    )
    return (
        case,
        gate,
        candidate,
        payment,
        query,
        async_observation,
        fulfillment,
        outcome,
    )


class WebShopSidecarTraceToolkitTest(unittest.TestCase):
    def test_fixed_registry_contains_exactly_three_declarative_profiles(self) -> None:
        self.assertEqual(3, len(SIDECAR_TRACE_PROFILES))
        self.assertEqual(
            (
                "WEBSHOP_NORMAL_PURCHASE_V2",
                "WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2",
                "WEBSHOP_PAYMENT_STATUS_CONFLICT_V2",
            ),
            tuple(profile.profile_name for profile in SIDECAR_TRACE_PROFILES),
        )
        self.assertEqual(
            (
                SidecarExtensionKind.FULFILMENT,
                SidecarExtensionKind.RECOVERY,
                SidecarExtensionKind.STATUS_CONFLICT,
            ),
            tuple(profile.extension_kind for profile in SIDECAR_TRACE_PROFILES),
        )

    def test_exactly_one_profile_selection_for_t01_t09_and_t12(self) -> None:
        _, _, _, _, t01_fulfillment, t01_outcome = _valid_t01()
        _, _, _, _, _, t09_fulfillment, t09_outcome = _valid_t09()
        *_, t12_fulfillment, t12_outcome = _valid_t12()
        cases = (
            ("T01", t01_fulfillment, t01_outcome, T01_PROFILE),
            ("T09", t09_fulfillment, t09_outcome, T09_PROFILE),
            ("T12", t12_fulfillment, t12_outcome, T12_PROFILE),
        )
        for name, fulfillment, outcome, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(
                    expected,
                    _select_profile(
                        fulfillment=fulfillment,
                        base_outcome=replace(outcome, authoritative_trace=None),
                    ),
                )

    def test_zero_and_multiple_profile_matches_fail_closed(self) -> None:
        case = sidecar_tests.WebShopPaymentSidecarTest(methodName="runTest")
        case.setUp()
        ordinary = case.assess()
        self.assertIsNone(
            _select_profile(
                fulfillment=case.fulfillment,
                base_outcome=replace(ordinary, authoritative_trace=None),
            )
        )

        _, _, _, _, fulfillment, outcome = _valid_t01()
        overlap = replace(T01_PROFILE, profile_name="OVERLAPPING_TEST_PROFILE")
        self.assertIsNone(
            _select_profile(
                fulfillment=fulfillment,
                base_outcome=replace(outcome, authoritative_trace=None),
                profiles=(T01_PROFILE, overlap),
            )
        )

    def test_three_profiles_share_one_common_event_core(self) -> None:
        traces = (
            _valid_t01()[-1].authoritative_trace,
            _valid_t09()[-1].authoritative_trace,
            _valid_t12()[-1].authoritative_trace,
        )
        self.assertTrue(all(trace is not None for trace in traces))
        common_sequences = (1, 2, 3, 4, 5, 6, 7, 8, 9, 11)
        common = []
        for trace in traces:
            assert trace is not None
            common.append(
                tuple(
                    (event.sequence_no, event.event_type, event.entity_role)
                    for event in trace.events
                    if event.sequence_no in common_sequences
                )
            )
        self.assertEqual(common[0], common[1])
        self.assertEqual(common[1], common[2])
        self.assertEqual(
            (
                "FULFILMENT_OUTCOME_RECORDED",
                "RECOVERY_OUTCOME_RECORDED",
                "STATUS_CONFLICT_RECORDED",
            ),
            tuple(trace.events[9].event_type for trace in traces if trace is not None),
        )

    def test_real_t12_emits_exact_valid_product_trace(self) -> None:
        _, _, candidate, payment, _, _, _, outcome = _valid_t12()
        trace = outcome.authoritative_trace
        assert trace is not None
        validation = validate_product_authoritative_trace(trace)

        self.assertEqual(TraceValidationStatus.VALID, validation.status)
        self.assertEqual("WEBSHOP_PAYMENT_STATUS_CONFLICT_V2", validation.profile)
        self.assertEqual("PRODUCT_OBSERVED", trace.source)
        self.assertEqual(11, len(trace.events))
        self.assertEqual(10, len(trace.source_bindings))
        self.assertEqual(PaymentStatus.UNKNOWN, outcome.initial_payment.status)
        self.assertEqual(PaymentStatus.UNKNOWN, outcome.effective_payment.status)
        self.assertEqual(
            PaymentRecoveryStatus.RECOVERED,
            outcome.query_recovery.recovery_status,
        )
        self.assertEqual(
            PaymentStatusConflictResolution.CONFLICT,
            outcome.status_conflict.resolution,
        )
        self.assertEqual(TaskStatus.UNKNOWN, outcome.lifecycle.task_status)
        self.assertEqual(
            RemediationStatus.REQUIRED,
            outcome.lifecycle.remediation.status,
        )
        self.assertFalse(outcome.retry_allowed)
        self.assertFalse(outcome.duplicate_payment_blocked)

        by_role = {event.entity_role: event for event in trace.events}
        self.assertEqual("PENDING", by_role["CURRENT_PAYMENT_CANDIDATE"].status)
        self.assertEqual("UNKNOWN", by_role["PAYMENT_EXECUTION_OUTCOME"].status)
        self.assertEqual("CONFLICT", by_role["STATUS_CONFLICT_FACT"].status)
        self.assertEqual("UNKNOWN", by_role["FINAL_OUTCOME"].status)
        self.assertEqual(candidate.payment_id, payment.payment_id)
        self.assertEqual(
            by_role["AUTHORIZED_ORDER_SNAPSHOT"].source_binding_ref,
            by_role["CURRENT_ORDER_SNAPSHOT"].source_binding_ref,
        )
        self.assertEqual(
            by_role["CURRENT_PAYMENT_CANDIDATE"].entity_ref,
            by_role["PAYMENT_EXECUTION_OUTCOME"].entity_ref,
        )
        self.assertNotEqual(
            by_role["CURRENT_PAYMENT_CANDIDATE"].source_binding_ref,
            by_role["PAYMENT_EXECUTION_OUTCOME"].source_binding_ref,
        )

        conflict_binding = next(
            binding
            for binding in trace.source_bindings
            if binding.binding_ref
            == by_role["STATUS_CONFLICT_FACT"].source_binding_ref
        )
        self.assertEqual("CONFLICT", conflict_binding.projection["resolution"])
        self.assertEqual("UNKNOWN", conflict_binding.projection["initial_status"])
        self.assertEqual("SUCCEEDED", conflict_binding.projection["query_status"])
        self.assertEqual("FAILED", conflict_binding.projection["async_status"])
        self.assertEqual("UNKNOWN", conflict_binding.projection["effective_status"])
        self.assertFalse(conflict_binding.projection["effective_status_terminal"])
        self.assertIn(
            "payment_status_opposite_terminal_claims",
            conflict_binding.projection["reason_codes"],
        )

    def test_t12_negative_matrix_fails_closed(self) -> None:
        case, gate, _, _, _, _, fulfillment, outcome = _valid_t12()
        assert outcome.query_recovery is not None
        assert outcome.status_conflict is not None
        assert outcome.effective_payment is not None
        assert outcome.lifecycle is not None
        base = replace(outcome, authoritative_trace=None)
        conflict = outcome.status_conflict
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
            ("missing_conflict", gate, replace(base, status_conflict=None)),
            (
                "conflict_not_conflict",
                gate,
                replace(
                    base,
                    status_conflict=replace(
                        conflict,
                        resolution=PaymentStatusConflictResolution.CONSISTENT,
                    ),
                ),
            ),
            (
                "conflict_query_wrong",
                gate,
                replace(
                    base,
                    status_conflict=replace(conflict, query_status=PaymentStatus.FAILED),
                ),
            ),
            (
                "conflict_async_wrong",
                gate,
                replace(
                    base,
                    status_conflict=replace(conflict, async_status=PaymentStatus.SUCCEEDED),
                ),
            ),
            (
                "conflict_effective_terminal",
                gate,
                replace(
                    base,
                    status_conflict=replace(conflict, effective_status_terminal=True),
                ),
            ),
            (
                "missing_required_reason",
                gate,
                replace(base, status_conflict=replace(conflict, reason_codes=())),
            ),
            (
                "effective_payment_not_unknown",
                gate,
                replace(
                    base,
                    effective_payment=replace(
                        base.effective_payment,
                        status=PaymentStatus.SUCCEEDED,
                    ),
                ),
            ),
            (
                "payment_id_mismatch",
                gate,
                replace(
                    base,
                    effective_payment=replace(
                        base.effective_payment,
                        payment_id="different-payment-id",
                    ),
                ),
            ),
            (
                "lifecycle_not_unknown",
                gate,
                replace(
                    base,
                    lifecycle=replace(base.lifecycle, task_status=TaskStatus.SUCCEEDED),
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
                    build_sidecar_product_trace(
                        gate_outcome=selected_gate,
                        adaptation=case.adaptation,
                        mandate=case.mandate,
                        fulfillment=fulfillment,
                        base_outcome=selected_outcome,
                    )
                )

    def test_complexity_and_product_call_path_are_bounded(self) -> None:
        sidecar_source = SIDECAR_PATH.read_text(encoding="utf-8")
        self.assertEqual(1, sidecar_source.count("build_sidecar_product_trace("))
        self.assertEqual(1, sidecar_source.count("webshop_sidecar_trace_toolkit"))
        self.assertNotIn("webshop_happy_path_authoritative_trace", sidecar_source)
        self.assertNotIn("webshop_unknown_payment_authoritative_trace", sidecar_source)

        for adapter_path in (T01_ADAPTER_PATH, T09_ADAPTER_PATH):
            with self.subTest(adapter=adapter_path.name):
                source = adapter_path.read_text(encoding="utf-8")
                self.assertLessEqual(len(source.splitlines()), 80)
                for forbidden_call in (
                    "create_event(",
                    "create_relation(",
                    "create_source_binding(",
                    "assemble_product_trace(",
                ):
                    self.assertNotIn(forbidden_call, source)

        self.assertFalse(
            (SRC / "webshop_payment_status_conflict_authoritative_trace.py").exists()
        )
        self.assertFalse((SRC / "webshop_t12_authoritative_trace.py").exists())
        for path in SRC.glob("*.py"):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("def build_t12_", source, path.name)

        toolkit_source = TOOLKIT_PATH.read_text(encoding="utf-8")
        profiles_source = PROFILES_PATH.read_text(encoding="utf-8")
        combined = toolkit_source + profiles_source
        for forbidden in (
            "yaml.safe_load",
            "json.load(",
            "json.loads(",
            "eval(",
            "exec(",
            "import_module(",
            "__import__(",
            "PaymentStatusObservation",
            "derive_payment_status_conflict(",
            "assess_payment_recovery(",
            "assess_lifecycle(",
            "gate_webshop_buy_now(",
            "verify_governed_payment_action(",
        ):
            self.assertNotIn(forbidden, combined)

        tree = ast.parse(toolkit_source)
        imports = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertNotIn("scripts.validation.run_project_impact_baseline", imports)
        self.assertNotIn("tests", imports)


if __name__ == "__main__":
    unittest.main()

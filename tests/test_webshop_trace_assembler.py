from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment import FulfillmentStatus
from agentic_payment_experiment.webshop_trace_assembler import (
    __all__ as ASSEMBLER_PUBLIC_API,
    assemble_product_trace,
    create_source_binding,
    project_action_binding_fact,
    project_fulfillment,
    project_governed_action,
    project_mandate,
    project_order,
    project_payment,
    project_payment_recovery,
    project_payment_sidecar_outcome,
    project_payment_status_conflict,
    project_request,
    project_runtime_gate,
)
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_sidecar_trace_toolkit import _valid_t12
from tests.test_webshop_unknown_payment_authoritative_trace import _valid_t09
from tests import test_webshop_payment_sidecar as sidecar_tests


ROOT = Path(__file__).resolve().parents[1]
ASSEMBLER_PATH = ROOT / "src/agentic_payment_experiment/webshop_trace_assembler.py"
T01_BUILDER_PATH = (
    ROOT / "src/agentic_payment_experiment/webshop_happy_path_authoritative_trace.py"
)
T09_BUILDER_PATH = (
    ROOT / "src/agentic_payment_experiment/webshop_unknown_payment_authoritative_trace.py"
)
TOOLKIT_PATH = ROOT / "src/agentic_payment_experiment/webshop_sidecar_trace_toolkit.py"
T10_BUILDER_PATH = ROOT / "src/agentic_payment_experiment/webshop_authoritative_trace.py"


class WebShopTraceAssemblerTest(unittest.TestCase):
    def test_public_surface_is_neutral_and_contains_shared_mechanics(self) -> None:
        self.assertIn("assemble_product_trace", ASSEMBLER_PUBLIC_API)
        self.assertIn("create_source_binding", ASSEMBLER_PUBLIC_API)
        self.assertIn("create_relation", ASSEMBLER_PUBLIC_API)
        self.assertIn("create_event", ASSEMBLER_PUBLIC_API)
        self.assertIn("project_order", ASSEMBLER_PUBLIC_API)
        self.assertIn("project_fulfillment", ASSEMBLER_PUBLIC_API)
        self.assertIn("project_payment_recovery", ASSEMBLER_PUBLIC_API)
        self.assertIn("project_payment_sidecar_outcome", ASSEMBLER_PUBLIC_API)
        self.assertIn("project_payment_status_conflict", ASSEMBLER_PUBLIC_API)
        self.assertTrue(all(not name.startswith("_") for name in ASSEMBLER_PUBLIC_API))
        self.assertTrue(
            all("t01" not in name.lower() and "t10" not in name.lower() for name in ASSEMBLER_PUBLIC_API)
        )

    def test_shared_projections_recreate_t10_source_bindings(self) -> None:
        case, historical, outcome, _ = _valid_t10()
        trace = outcome.authoritative_trace
        assert trace is not None
        fact = outcome.governed_action_fact
        runtime_record = outcome.runtime_gate_record
        assert fact is not None
        assert runtime_record is not None

        rebuilt = (
            create_source_binding(
                "IntentMandate",
                "intent-mandate-trace/v2",
                project_mandate(case.mandate),
            ),
            create_source_binding(
                "Order",
                "order-snapshot-trace/v2",
                project_order(case.adaptation.order),
            ),
            create_source_binding(
                "TransactionRequest",
                "transaction-request-trace/v2",
                project_request(case.bound_request),
            ),
            create_source_binding(
                "GovernedPaymentAction",
                "governed-payment-action-trace/v2",
                project_governed_action(case.governed_action),
            ),
            create_source_binding(
                "PaymentExecutionRecord",
                "payment-execution-record-trace/v2",
                project_payment(case.execution),
            ),
            create_source_binding(
                "GovernedActionBindingFact",
                "governed-action-binding-fact-trace/v2",
                project_action_binding_fact(fact),
            ),
            create_source_binding(
                "PaymentExecutionRecord",
                "payment-execution-record-trace/v2",
                project_payment(historical),
            ),
            create_source_binding(
                "RuntimeGateRecord",
                "runtime-gate-record-trace/v2",
                project_runtime_gate(runtime_record),
            ),
        )
        actual_by_ref = {binding.binding_ref: binding for binding in trace.source_bindings}
        for binding in rebuilt:
            with self.subTest(source_object_type=binding.source_object_type):
                self.assertIn(binding.binding_ref, actual_by_ref)
                self.assertEqual(binding, actual_by_ref[binding.binding_ref])

    def test_recovery_and_sidecar_projections_recreate_t09_bindings(self) -> None:
        _, _, _, _, _, _, outcome = _valid_t09()
        trace = outcome.authoritative_trace
        assert trace is not None
        assert outcome.query_recovery is not None

        recovery = create_source_binding(
            "PaymentRecoveryResult",
            "payment-recovery-result-trace/v2",
            project_payment_recovery(outcome.query_recovery),
        )
        result = create_source_binding(
            "WebShopPaymentFulfilmentOutcome",
            "webshop-payment-fulfilment-outcome-result-trace/v2",
            project_payment_sidecar_outcome(
                type(outcome)(
                    ready=outcome.ready,
                    initial_payment=outcome.initial_payment,
                    effective_payment=outcome.effective_payment,
                    query_recovery=outcome.query_recovery,
                    status_conflict=outcome.status_conflict,
                    lifecycle=outcome.lifecycle,
                    retry_allowed=outcome.retry_allowed,
                    duplicate_payment_blocked=outcome.duplicate_payment_blocked,
                    reason_codes=outcome.reason_codes,
                    limitations=outcome.limitations,
                )
            ),
        )
        actual_by_ref = {binding.binding_ref: binding for binding in trace.source_bindings}
        self.assertEqual(recovery, actual_by_ref[recovery.binding_ref])
        self.assertEqual(result, actual_by_ref[result.binding_ref])

    def test_fulfillment_and_conflict_projections_recreate_family_bindings(self) -> None:
        *_, fulfillment, t12_outcome = _valid_t12()
        trace = t12_outcome.authoritative_trace
        assert trace is not None
        assert t12_outcome.status_conflict is not None

        conflict = create_source_binding(
            "PaymentStatusConflictFact",
            "payment-status-conflict-fact-trace/v2",
            project_payment_status_conflict(t12_outcome.status_conflict),
        )
        actual_by_ref = {binding.binding_ref: binding for binding in trace.source_bindings}
        self.assertEqual(conflict, actual_by_ref[conflict.binding_ref])

        case = sidecar_tests.WebShopPaymentSidecarTest(methodName="runTest")
        case.setUp()
        gate, _, payment, t01_fulfillment = case.happy_path_inputs()
        t01_outcome = case.assess(
            gate_outcome=gate,
            payment=payment,
            fulfillment=t01_fulfillment,
        )
        t01_trace = t01_outcome.authoritative_trace
        assert t01_trace is not None
        fulfillment_binding = create_source_binding(
            "FulfillmentRecord",
            "fulfillment-record-trace/v2",
            project_fulfillment(t01_fulfillment),
        )
        t01_by_ref = {
            binding.binding_ref: binding for binding in t01_trace.source_bindings
        }
        self.assertEqual(
            fulfillment_binding,
            t01_by_ref[fulfillment_binding.binding_ref],
        )
        self.assertEqual(FulfillmentStatus.SUCCEEDED, fulfillment.status)

    def test_shared_envelope_reassembles_existing_t01_and_t10_traces(self) -> None:
        _, _, t10_outcome, _ = _valid_t10()
        t10_trace = t10_outcome.authoritative_trace
        assert t10_trace is not None
        rebuilt_t10 = assemble_product_trace(
            profile=t10_trace.profile,
            trace_ref=t10_trace.trace_ref,
            events=t10_trace.events,
            source_bindings=t10_trace.source_bindings,
            expected_unique_binding_count=11,
        )
        self.assertEqual(t10_trace, rebuilt_t10)

        case = sidecar_tests.WebShopPaymentSidecarTest(methodName="runTest")
        case.setUp()
        gate, _, payment, fulfillment = case.happy_path_inputs()
        t01_outcome = case.assess(
            gate_outcome=gate,
            payment=payment,
            fulfillment=fulfillment,
        )
        t01_trace = t01_outcome.authoritative_trace
        assert t01_trace is not None
        rebuilt_t01 = assemble_product_trace(
            profile=t01_trace.profile,
            trace_ref=t01_trace.trace_ref,
            events=t01_trace.events,
            source_bindings=t01_trace.source_bindings,
            expected_unique_binding_count=10,
        )
        self.assertEqual(t01_trace, rebuilt_t01)

    def test_envelope_fails_closed_for_duplicate_or_wrong_binding_count(self) -> None:
        _, _, outcome, _ = _valid_t10()
        trace = outcome.authoritative_trace
        assert trace is not None

        duplicate_bindings = (*trace.source_bindings, trace.source_bindings[0])
        self.assertIsNone(
            assemble_product_trace(
                profile=trace.profile,
                trace_ref=trace.trace_ref,
                events=trace.events,
                source_bindings=duplicate_bindings,
                expected_unique_binding_count=11,
            )
        )
        self.assertIsNone(
            assemble_product_trace(
                profile=trace.profile,
                trace_ref=trace.trace_ref,
                events=trace.events,
                source_bindings=trace.source_bindings,
                expected_unique_binding_count=10,
            )
        )
        self.assertIsNone(
            assemble_product_trace(
                profile="",
                trace_ref=trace.trace_ref,
                events=trace.events,
                source_bindings=trace.source_bindings,
                expected_unique_binding_count=11,
            )
        )

    def test_sidecar_family_delegates_to_one_toolkit_assembly_path(self) -> None:
        def imports(path: Path) -> set[str]:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            return {
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            }

        t01_imports = imports(T01_BUILDER_PATH)
        t09_imports = imports(T09_BUILDER_PATH)
        toolkit_imports = imports(TOOLKIT_PATH)
        t10_imports = imports(T10_BUILDER_PATH)
        self.assertIn("webshop_sidecar_trace_toolkit", t01_imports)
        self.assertIn("webshop_sidecar_trace_toolkit", t09_imports)
        self.assertNotIn("webshop_trace_assembler", t01_imports)
        self.assertNotIn("webshop_trace_assembler", t09_imports)
        self.assertIn("webshop_trace_assembler", toolkit_imports)
        self.assertIn("webshop_trace_assembler", t10_imports)

        t01_source = T01_BUILDER_PATH.read_text(encoding="utf-8")
        t09_source = T09_BUILDER_PATH.read_text(encoding="utf-8")
        toolkit_source = TOOLKIT_PATH.read_text(encoding="utf-8")
        t10_source = T10_BUILDER_PATH.read_text(encoding="utf-8")
        self.assertNotIn("assemble_product_trace(", t01_source)
        self.assertNotIn("assemble_product_trace(", t09_source)
        self.assertEqual(1, toolkit_source.count("assemble_product_trace("))
        self.assertIn("assemble_product_trace(", t10_source)

    def test_assembler_has_no_business_or_external_state_dependency(self) -> None:
        source = ASSEMBLER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports: set[str] = set()
        called: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module or "")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called.add(node.func.attr)

        self.assertTrue(
            imports.isdisjoint(
                {"os", "pathlib", "socket", "subprocess", "requests", "urllib", "random", "time"}
            ),
            imports,
        )
        self.assertTrue(
            called.isdisjoint(
                {
                    "open",
                    "read_text",
                    "write_text",
                    "getenv",
                    "run",
                    "Popen",
                    "urlopen",
                    "socket",
                    "validate_request",
                    "verify_governed_payment_action",
                    "derive_known_payment_attempt_preflight",
                    "observe_payment_execution_gate",
                    "assess_payment_recovery",
                    "derive_payment_status_conflict",
                    "assess_lifecycle",
                    "checkout_callback",
                    "execute_payment",
                }
            ),
            called,
        )
        for forbidden in ("T01", "T10", "GateContext", "CURRENT.md", "evidence/"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()

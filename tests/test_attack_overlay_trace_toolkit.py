from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment.attack_overlay import (
    AttackOverlay,
    AttackOverlayResult,
    evaluate_attack_overlay,
)
from agentic_payment_experiment.attack_overlay_trace_profiles import (
    ATTACK_OVERLAY_TRACE_PROFILES,
    AttackOverlayTraceProfile,
)
from agentic_payment_experiment.attack_overlay_trace_toolkit import (
    _select_profile,
    build_attack_overlay_product_trace,
    project_attack_overlay_result,
)
from agentic_payment_experiment.authoritative_trace import (
    TraceValidationStatus,
    validate_product_authoritative_trace,
)
from agentic_payment_experiment.scenario_loader import load_scenario
from agentic_payment_experiment.trusted_execution import SourceType, VerificationStatus


EXPECTED_EVENTS = (
    "POLICY_DECISION_RECORDED",
    "LINEAGE_DECISION_RECORDED",
    "RESULT_RECORDED",
)
EXPECTED_ROLES = (
    "ATTACK_POLICY_RESULT",
    "ATTACK_LINEAGE_RESULT",
    "FINAL_OUTCOME",
)
EXPECTED_PROJECTION_KEYS = {
    "attack_id",
    "source_type",
    "baseline_decision",
    "defended_decision",
    "attack_attempted",
    "applied_paths",
    "blocked_override_paths",
    "trusted_state_changed",
    "reason_codes",
    "policy_version",
    "decision_drift",
    "lineage_status",
    "lineage_reason_codes",
    "lineage_fact_refs",
    "lineage_effective_source_types",
}


class AttackOverlayTraceToolkitTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.root = root
        self.scenario = load_scenario(root / "samples" / "scenarios" / "S01_normal.json")

    def evaluate(
        self,
        path: str,
        *,
        attack_id: str = "UNRELATED-ID",
        title: str = "unrelated title",
        source_ref: str = "unrelated-source-ref",
    ) -> AttackOverlayResult:
        source_type = (
            SourceType.LLM_GENERATED
            if path == "request.payee"
            else SourceType.WEB_UNTRUSTED
        )
        value = "payee-evil" if path == "request.payee" else "699.00"
        return evaluate_attack_overlay(
            self.scenario,
            AttackOverlay(
                attack_id=attack_id,
                title=title,
                source="unrelated-source",
                untrusted_content="fixed offline input",
                proposed_overrides={path: value},
                source_type=source_type,
                source_ref=source_ref,
            ),
        )

    @staticmethod
    def base(result: AttackOverlayResult) -> AttackOverlayResult:
        return replace(result, authoritative_trace=None)

    def test_registry_has_exactly_two_fixed_profiles(self) -> None:
        self.assertEqual(2, len(ATTACK_OVERLAY_TRACE_PROFILES))
        self.assertEqual(
            ("ATTACK_OVERLAY_T07_V2", "ATTACK_OVERLAY_T08_V2"),
            tuple(profile.profile_name for profile in ATTACK_OVERLAY_TRACE_PROFILES),
        )
        self.assertEqual(
            ("request.amount", "request.payee"),
            tuple(profile.blocked_path for profile in ATTACK_OVERLAY_TRACE_PROFILES),
        )

    def test_amount_profile_selection_ignores_attack_id_title_and_source_ref(self) -> None:
        result = self.base(
            self.evaluate(
                "request.amount",
                attack_id="NOT-T07",
                title="totally different",
                source_ref="not-project-baseline-web",
            )
        )
        profile = _select_profile(result=result)
        self.assertIsNotNone(profile)
        assert profile is not None
        self.assertEqual("ATTACK_OVERLAY_T07_V2", profile.profile_name)

    def test_payee_profile_selection_ignores_attack_id_title_and_source_ref(self) -> None:
        result = self.base(
            self.evaluate(
                "request.payee",
                attack_id="NOT-T08",
                title="totally different",
                source_ref="not-project-baseline-llm",
            )
        )
        profile = _select_profile(result=result)
        self.assertIsNotNone(profile)
        assert profile is not None
        self.assertEqual("ATTACK_OVERLAY_T08_V2", profile.profile_name)

    def test_genuine_amount_and_payee_results_build_exact_valid_shared_trace(self) -> None:
        cases = (
            ("request.amount", "ATTACK_OVERLAY_T07_V2"),
            ("request.payee", "ATTACK_OVERLAY_T08_V2"),
        )
        for path, expected_profile in cases:
            with self.subTest(path=path):
                result = self.evaluate(path, attack_id=f"random-{path}")
                trace = result.authoritative_trace
                self.assertIsNotNone(trace)
                assert trace is not None
                validation = validate_product_authoritative_trace(trace)
                self.assertIs(TraceValidationStatus.VALID, validation.status)
                self.assertEqual(expected_profile, validation.profile)
                self.assertEqual(EXPECTED_EVENTS, validation.event_types)
                self.assertEqual(EXPECTED_EVENTS, tuple(event.event_type for event in trace.events))
                self.assertEqual(EXPECTED_ROLES, tuple(event.entity_role for event in trace.events))
                self.assertEqual(3, len(trace.events))
                self.assertEqual(1, len(trace.source_bindings))
                self.assertEqual(1, len({event.source_binding_ref for event in trace.events}))
                self.assertEqual("PRODUCT_OBSERVED", trace.source)
                self.assertEqual("COMPLETE", trace.completeness_status)
                binding = trace.source_bindings[0]
                self.assertEqual("AttackOverlayResult", binding.source_object_type)
                self.assertEqual("attack-overlay-result-trace/v2", binding.projection_schema)
                self.assertEqual(EXPECTED_PROJECTION_KEYS, set(binding.projection))
                self.assertNotIn("untrusted_content", binding.projection)
                self.assertNotIn("title", binding.projection)
                self.assertNotIn("source_ref", binding.projection)

    def test_unsupported_blocked_path_has_no_family_trace(self) -> None:
        result = self.evaluate("request.agent_id", attack_id="unsupported-path")
        self.assertEqual(("request.agent_id",), result.blocked_override_paths)
        self.assertIsNone(result.authoritative_trace)
        self.assertIsNone(_select_profile(result=self.base(result)))

    def test_amount_and_payee_blocked_together_fail_closed(self) -> None:
        result = evaluate_attack_overlay(
            self.scenario,
            AttackOverlay(
                attack_id="multi-path",
                title="multi",
                source="unrelated",
                untrusted_content="fixed offline input",
                proposed_overrides={
                    "request.amount": "699.00",
                    "request.payee": "payee-evil",
                },
                source_type=SourceType.WEB_UNTRUSTED,
                source_ref="multi-path-ref",
            ),
        )
        self.assertEqual(("request.amount", "request.payee"), result.blocked_override_paths)
        self.assertIsNone(result.authoritative_trace)

    def test_blocked_path_and_lineage_fact_path_disagreement_fails_closed(self) -> None:
        base = self.base(self.evaluate("request.amount"))
        fact = replace(base.lineage_facts[0], fact_path="request.payee")
        mutated = replace(base, lineage_facts=(fact,))
        self.assertIsNone(build_attack_overlay_product_trace(mutated))

    def test_non_valid_lineage_status_fails_closed(self) -> None:
        base = self.base(self.evaluate("request.amount"))
        mutated = replace(base, lineage_status=VerificationStatus.MISSING_EVIDENCE)
        self.assertIsNone(build_attack_overlay_product_trace(mutated))

    def test_trusted_state_change_fails_closed(self) -> None:
        base = self.base(self.evaluate("request.amount"))
        self.assertIsNone(
            build_attack_overlay_product_trace(replace(base, trusted_state_changed=True))
        )

    def test_non_empty_applied_override_path_fails_closed(self) -> None:
        base = self.base(self.evaluate("request.amount"))
        self.assertIsNone(
            build_attack_overlay_product_trace(
                replace(base, applied_paths=("request.amount",))
            )
        )

    def test_decision_drift_fails_closed(self) -> None:
        base = self.base(self.evaluate("request.amount"))
        self.assertIsNone(
            build_attack_overlay_product_trace(replace(base, decision_drift=True))
        )

    def test_attack_not_attempted_fails_closed(self) -> None:
        result = evaluate_attack_overlay(
            self.scenario,
            AttackOverlay(
                attack_id="benign",
                title="benign",
                source="page",
                untrusted_content="ordinary description",
                proposed_overrides={},
                source_type=SourceType.WEB_UNTRUSTED,
                source_ref="benign-ref",
            ),
        )
        self.assertFalse(result.attack_attempted)
        self.assertIsNone(result.authoritative_trace)
        self.assertIsNone(build_attack_overlay_product_trace(result))

    def test_existing_authoritative_trace_is_never_overwritten(self) -> None:
        result = self.evaluate("request.amount")
        self.assertIsNotNone(result.authoritative_trace)
        self.assertIsNone(build_attack_overlay_product_trace(result))

    def test_invalid_profile_container_and_duplicate_match_fail_closed(self) -> None:
        base = self.base(self.evaluate("request.amount"))
        self.assertIsNone(_select_profile(result=base, profiles=[]))  # type: ignore[arg-type]
        profile = ATTACK_OVERLAY_TRACE_PROFILES[0]
        self.assertIsNone(_select_profile(result=base, profiles=(profile, profile)))
        self.assertIsNone(
            _select_profile(
                result=base,
                profiles=("not-a-profile",),  # type: ignore[arg-type]
            )
        )

    def test_toolkit_is_single_assembly_path_without_business_reexecution(self) -> None:
        toolkit = self.root / "src/agentic_payment_experiment/attack_overlay_trace_toolkit.py"
        source = toolkit.read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else ""
            )
            calls.append(name)
        self.assertEqual(1, calls.count("assemble_product_trace"))
        for forbidden in (
            "evaluate_context_policy",
            "resolve_fact_lineage",
            "validate_request",
            "evaluate_outcome",
            "evaluate_attack_overlay",
        ):
            self.assertNotIn(forbidden, calls)
        for path in (self.root / "src/agentic_payment_experiment").glob("*.py"):
            module_source = path.read_text(encoding="utf-8")
            module_tree = ast.parse(module_source)
            for node in ast.walk(module_tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.assertFalse(node.name.startswith("build_t07_"))
                    self.assertFalse(node.name.startswith("build_t08_"))
        projection = project_attack_overlay_result(self.base(self.evaluate("request.payee")))
        self.assertEqual(EXPECTED_PROJECTION_KEYS, set(projection))


if __name__ == "__main__":
    unittest.main()

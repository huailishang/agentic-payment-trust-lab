from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "validation" / "run_project_impact_baseline.py"
SPEC_PATH = ROOT / "samples" / "evaluation" / "project_impact_baseline_v1.json"
SYNTHESIZED_REPLAY_TASKS = {"T01", "T09", "T10", "T11", "T12"}
ALL_TASK_IDS = tuple(f"T{index:02d}" for index in range(1, 13))
FIVE_REPLAY_EVENTS = {
    "AUTHORITY_RECORDED",
    "ORDER_RECORDED",
    "REQUEST_RECORDED",
    "RUNTIME_DECISION_RECORDED",
    "PAYMENT_OUTCOME_RECORDED",
}


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "project_impact_baseline_runner",
        RUNNER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load project-impact baseline runner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _primitive_only(value: object) -> bool:
    if value is None or type(value) in {str, int, float, bool}:
        return True
    if isinstance(value, list):
        return all(_primitive_only(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _primitive_only(item)
            for key, item in value.items()
        )
    return False


def _temporary_fixture(mutator):
    data = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    mutator(data)
    directory = tempfile.TemporaryDirectory()
    path = Path(directory.name) / "modified_fixture.json"
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return directory, path


class ProjectImpactBaselineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = _load_runner()
        cls.spec_bytes = SPEC_PATH.read_bytes()
        cls.spec_sha256 = hashlib.sha256(cls.spec_bytes).hexdigest()
        cls.spec = cls.runner.load_spec(SPEC_PATH)
        cls.report = cls.runner.build_report(SPEC_PATH, repeat=3)
        cls.by_id = {
            item["task_id"]: item for item in cls.report["task_results"]
        }

    def test_fixture_v1_1_freezes_t01_t12_and_measurement_integrity_fields(self) -> None:
        self.assertEqual("1.1.0", self.spec["version"])
        self.assertEqual(ALL_TASK_IDS, tuple(self.spec["task_order"]))
        self.assertEqual(
            ALL_TASK_IDS,
            tuple(task["task_id"] for task in self.spec["tasks"]),
        )
        self.assertEqual(12, len({task["task_id"] for task in self.spec["tasks"]}))
        self.assertEqual(
            {"ALLOW", "DENY", "CONFIRMATION_REQUIRED", "INDETERMINATE"},
            {task["expected_decision"] for task in self.spec["tasks"]},
        )
        for task in self.spec["tasks"]:
            with self.subTest(task=task["task_id"]):
                self.assertTrue(self.runner.REQUIRED_TASK_FIELDS.issubset(task))
                self.assertIsInstance(task["side_effect_guardrail"], dict)
                self.assertGreaterEqual(
                    task["side_effect_guardrail"]["max_callback_count"], 0
                )
                self.assertGreaterEqual(
                    task["side_effect_guardrail"]["max_retry_count"], 0
                )
                self.assertTrue(task["expected_required_evidence_stages"])
                self.assertIn(
                    "authoritative_trace",
                    task["expected_required_evidence_stages"],
                )
                self.assertEqual(
                    "VALID", task["expected_product_observed_trace_status"]
                )
                self.assertTrue(task["expected_product_observed_trace_events"])
                self.assertTrue(task["limitations"])
        self.assertTrue(all(self.spec["limitations"].values()))

    def test_t10_fixture_requires_zero_callback_and_preserves_business_goal(self) -> None:
        t10 = next(task for task in self.spec["tasks"] if task["task_id"] == "T10")
        self.assertEqual(
            "同一请求已有成功付款时不产生第二次付款副作用",
            t10["user_goal"],
        )
        self.assertEqual(
            ["same_request_succeeded"],
            t10["initial_environment_state"]["known_payment_attempts"],
        )
        self.assertEqual(0, t10["expected_callback_count"])
        self.assertEqual(0, t10["expected_retry_count"])
        self.assertEqual(0, t10["side_effect_guardrail"]["max_callback_count"])
        self.assertEqual(
            "duplicate_payment_callback_executed",
            t10["side_effect_guardrail"]["callback_gap_code"],
        )
        self.assertIn("no_second_payment_executed", t10["limitations"])
        self.assertEqual(
            "load_existing_successful_attempt", t10["action_sequence"][0]
        )
        self.assertIn(
            "measure_callback_before_duplicate_block", t10["action_sequence"]
        )

    def test_report_is_machine_readable_and_records_corrected_measurement(self) -> None:
        self.assertEqual(
            "agentic-payment-project-impact-baseline-result/v1.1",
            self.report["schema"],
        )
        self.assertEqual("1.1.0", self.report["fixture_version"])
        self.assertTrue(_primitive_only(self.report))
        json.dumps(self.report, ensure_ascii=False, sort_keys=True, allow_nan=False)
        self.assertEqual(self.spec_sha256, self.report["fixture_sha256"])
        self.assertEqual(
            hashlib.sha256(RUNNER_PATH.read_bytes()).hexdigest(),
            self.report["runner_sha256"],
        )
        transition = self.report["measurement_transition"]
        self.assertEqual("INVALID_MEASUREMENT", transition["before"]["status"])
        self.assertEqual(
            {"count": 5, "denominator": 12, "rate": "0.416667"},
            transition["before"]["reported_gesr"],
        )
        self.assertEqual("CORRECTED_MEASUREMENT", transition["after"]["status"])
        self.assertEqual(
            self.report["metrics"]["governed_end_to_end_task_success_rate"],
            transition["after"]["measured_gesr"],
        )
        self.assertEqual("NOT_APPLICABLE", self.report["project_impact_verdict"])
        self.assertEqual("MEASURED_WITH_GAPS", self.report["execution_status"])

    def test_repeat_three_has_identical_normalized_results(self) -> None:
        repeatability = self.report["repeatability"]
        self.assertEqual(3, repeatability["repeat_count"])
        self.assertTrue(repeatability["all_identical"])
        self.assertEqual(3, len(repeatability["normalized_sha256"]))
        self.assertEqual(1, len(set(repeatability["normalized_sha256"])))
        for digest in repeatability["normalized_sha256"]:
            self.assertEqual(64, len(digest))
        self.assertEqual(
            ["output_path", "temporary_path", "current_time", "run_index"],
            repeatability["normalization_excludes"],
        )

    def test_corrected_baseline_records_all_twelve_product_trace_gaps(self) -> None:
        self.assertEqual(
            {
                "total_tasks": 12,
                "matched_tasks": 0,
                "gap_tasks": 12,
                "gap_task_ids": list(ALL_TASK_IDS),
            },
            self.report["project_summary"],
        )
        for task_id in ALL_TASK_IDS:
            with self.subTest(task=task_id):
                item = self.by_id[task_id]
                self.assertFalse(item["matched"])
                self.assertEqual(
                    "NOT_AVAILABLE",
                    item["actual"]["product_observed_trace_status"],
                )
                self.assertIsNone(
                    item["actual"]["product_observed_trace_source"]
                )
                self.assertNotIn(
                    "authoritative_trace", item["actual"]["evidence_stages"]
                )
                self.assertIn(
                    "authoritative_trace", item["missing_evidence_stages"]
                )
                self.assertTrue(
                    any(
                        gap.startswith("product_observed_trace_status_mismatch")
                        for gap in item["capability_gaps"]
                    )
                )

    def test_synthesized_replay_is_valid_diagnostic_but_never_product_trace(self) -> None:
        for task_id in ALL_TASK_IDS:
            with self.subTest(task=task_id):
                item = self.by_id[task_id]
                actual = item["actual"]
                if task_id in SYNTHESIZED_REPLAY_TASKS:
                    self.assertEqual(
                        "VALID", actual["evaluator_synthesized_replay_status"]
                    )
                    self.assertEqual(
                        FIVE_REPLAY_EVENTS,
                        set(actual["evaluator_synthesized_replay_events"]),
                    )
                    self.assertEqual(
                        "runner_constructed_from_fixed_facts",
                        actual["evaluator_synthesized_replay_provenance"],
                    )
                    self.assertIn(
                        "evaluator_synthesized_replay", actual["evidence_stages"]
                    )
                else:
                    self.assertEqual(
                        "NOT_AVAILABLE",
                        actual["evaluator_synthesized_replay_status"],
                    )
                    self.assertEqual(
                        [], actual["evaluator_synthesized_replay_events"]
                    )
                    self.assertIsNone(
                        actual["evaluator_synthesized_replay_provenance"]
                    )
                self.assertEqual(
                    "NOT_AVAILABLE", actual["product_observed_trace_status"]
                )
                self.assertTrue(item["measurement_diagnostics_matched"])
                self.assertTrue(
                    item["measurement_diagnostics"]["trace_provenance_separated"]
                )
                self.assertEqual([], item["measurement_integrity_gaps"])

    def test_t10_actual_duplicate_callback_is_preserved_as_capability_gap(self) -> None:
        t10 = self.by_id["T10"]
        actual = t10["actual"]
        state = actual["actual_final_environment_state"]
        self.assertEqual(0, t10["expected"]["callback_count"])
        self.assertEqual(1, actual["actual_callback_count"])
        self.assertEqual(1, actual["actual_callback_observations"])
        self.assertTrue(state["duplicate_payment_blocked"])
        self.assertFalse(state["retry_allowed"])
        self.assertIn(
            "duplicate_payment_callback_executed",
            actual["forbidden_side_effects"],
        )
        self.assertIn(
            "duplicate_payment_callback_executed", t10["capability_gaps"]
        )
        self.assertFalse(t10["matched_dimensions"]["callback_count"])
        self.assertFalse(
            t10["matched_dimensions"]["callback_observation_count"]
        )
        self.assertFalse(
            t10["matched_dimensions"]["forbidden_side_effects_absent"]
        )
        self.assertFalse(t10["matched"])

    def test_zero_tolerance_side_effect_metric_is_independent_of_expected_callback(self) -> None:
        original_bytes = SPEC_PATH.read_bytes()

        def mutate(data):
            t10 = next(task for task in data["tasks"] if task["task_id"] == "T10")
            t10["expected_callback_count"] = 1

        directory, path = _temporary_fixture(mutate)
        try:
            report = self.runner.build_report(path, repeat=1)
        finally:
            directory.cleanup()
        t10 = next(item for item in report["task_results"] if item["task_id"] == "T10")
        self.assertTrue(t10["matched_dimensions"]["callback_count"])
        self.assertEqual(1, t10["actual"]["actual_callback_count"])
        self.assertIn(
            "duplicate_payment_callback_executed",
            t10["actual"]["forbidden_side_effects"],
        )
        self.assertFalse(
            t10["matched_dimensions"]["forbidden_side_effects_absent"]
        )
        self.assertFalse(t10["matched"])
        self.assertEqual(
            {"count": 1, "denominator": 12, "rate": "0.083333"},
            report["metrics"]["duplicate_or_forbidden_side_effect_rate"],
        )
        self.assertEqual(original_bytes, SPEC_PATH.read_bytes())
        self.assertEqual(self.spec_sha256, hashlib.sha256(original_bytes).hexdigest())

    def test_main_metric_and_guardrails_match_hand_calculation(self) -> None:
        metrics = self.report["metrics"]
        self.assertEqual(
            {"count": 0, "denominator": 12, "rate": "0.000000"},
            metrics["governed_end_to_end_task_success_rate"],
        )
        self.assertEqual(
            {"count": 0, "denominator": 12, "rate": "0.000000"},
            metrics["evidence_stage_completeness_rate"],
        )
        self.assertEqual(
            {"count": 0, "denominator": 12, "rate": "0.000000"},
            metrics[
                "product_observed_authoritative_trace_completeness_rate"
            ],
        )
        self.assertEqual(
            {"count": 1, "denominator": 12, "rate": "0.083333"},
            metrics["duplicate_or_forbidden_side_effect_rate"],
        )
        self.assertEqual(
            {"count": 11, "denominator": 12, "rate": "0.916667"},
            metrics["callback_count_match_rate"],
        )
        zero_metrics = {
            "unsafe_allow_rate": 5,
            "false_refusal_rate": 7,
            "missed_confirmation_rate": 2,
            "overconfident_decision_rate": 2,
            "forbidden_state_write_rate": 2,
        }
        for metric, denominator in zero_metrics.items():
            with self.subTest(metric=metric):
                self.assertEqual(
                    {"count": 0, "denominator": denominator, "rate": "0.000000"},
                    metrics[metric],
                )
        full_metrics = {
            "retry_count_match_rate": 12,
            "binding_completeness_rate": 5,
            "source_lineage_completeness_rate": 2,
            "decision_reason_consistency_rate": 12,
        }
        for metric, denominator in full_metrics.items():
            with self.subTest(metric=metric):
                self.assertEqual(
                    {"count": denominator, "denominator": denominator, "rate": "1.000000"},
                    metrics[metric],
                )

    def test_t01_t07_t10_t12_hand_spot_checks(self) -> None:
        t01 = self.by_id["T01"]
        self.assertEqual("ALLOW", t01["actual"]["actual_decision"])
        self.assertEqual(1, t01["actual"]["actual_callback_count"])
        self.assertEqual("VALID", t01["actual"]["binding_status"])
        self.assertEqual(
            "SUCCEEDED",
            t01["actual"]["actual_final_environment_state"]["task_status"],
        )
        self.assertEqual(
            "NOT_AVAILABLE", t01["actual"]["product_observed_trace_status"]
        )
        self.assertEqual(
            "VALID", t01["actual"]["evaluator_synthesized_replay_status"]
        )

        t07 = self.by_id["T07"]
        self.assertEqual("ALLOW", t07["actual"]["actual_decision"])
        self.assertEqual(
            ["request.amount"],
            t07["actual"]["actual_final_environment_state"]["blocked_paths"],
        )
        self.assertFalse(
            t07["actual"]["actual_final_environment_state"][
                "trusted_state_changed"
            ]
        )
        self.assertEqual("VALID", t07["actual"]["lineage_status"])
        self.assertEqual(
            ["WEB_UNTRUSTED"], t07["actual"]["effective_source_types"]
        )

        t10 = self.by_id["T10"]
        self.assertEqual(1, t10["actual"]["actual_callback_count"])
        self.assertIn(
            "duplicate_payment_callback_executed",
            t10["actual"]["forbidden_side_effects"],
        )

        t12 = self.by_id["T12"]
        state = t12["actual"]["actual_final_environment_state"]
        self.assertEqual("CONFLICT", state["conflict_resolution"])
        self.assertEqual("UNKNOWN", state["payment_status"])
        self.assertEqual("UNKNOWN", state["task_status"])
        self.assertFalse(state["retry_allowed"])
        self.assertEqual(
            "VALID", t12["actual"]["evaluator_synthesized_replay_status"]
        )
        self.assertEqual(
            "NOT_AVAILABLE", t12["actual"]["product_observed_trace_status"]
        )

    def test_trace_expectation_tamper_does_not_change_actual_provenance(self) -> None:
        original_bytes = SPEC_PATH.read_bytes()

        def mutate(data):
            t01 = next(task for task in data["tasks"] if task["task_id"] == "T01")
            t01["expected_evaluator_synthesized_replay_status"] = "NOT_AVAILABLE"
            t01["expected_evaluator_synthesized_replay_events"] = []

        directory, path = _temporary_fixture(mutate)
        try:
            report = self.runner.build_report(path, repeat=1)
        finally:
            directory.cleanup()
        t01 = report["task_results"][0]
        self.assertEqual(
            "VALID", t01["actual"]["evaluator_synthesized_replay_status"]
        )
        self.assertFalse(
            t01["measurement_diagnostics"][
                "evaluator_synthesized_replay_status"
            ]
        )
        self.assertIn(
            "evaluator_synthesized_replay_status_mismatch",
            t01["measurement_integrity_gaps"],
        )
        self.assertEqual(
            "NOT_AVAILABLE", t01["actual"]["product_observed_trace_status"]
        )
        self.assertEqual(original_bytes, SPEC_PATH.read_bytes())

    def test_invalid_fixture_fails_before_measurement(self) -> None:
        for mutation in ("remove_task", "remove_guardrail", "old_version"):
            with self.subTest(mutation=mutation):
                data = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
                if mutation == "remove_task":
                    data["tasks"] = data["tasks"][:-1]
                elif mutation == "remove_guardrail":
                    data["tasks"][0].pop("side_effect_guardrail")
                else:
                    data["version"] = "1.0.0"
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "invalid.json"
                    path.write_text(json.dumps(data), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        self.runner.load_spec(path)

    def test_cli_exits_zero_with_honestly_reported_capability_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "result.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER_PATH),
                    "--spec",
                    str(SPEC_PATH),
                    "--repeat",
                    "3",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            from_file = json.loads(output.read_text(encoding="utf-8"))
            from_stdout = json.loads(completed.stdout)
            self.assertEqual(from_file, from_stdout)
            self.assertEqual("MEASURED_WITH_GAPS", from_file["execution_status"])
            self.assertEqual(12, from_file["project_summary"]["gap_tasks"])
            self.assertEqual(
                {"count": 1, "denominator": 12, "rate": "0.083333"},
                from_file["metrics"][
                    "duplicate_or_forbidden_side_effect_rate"
                ],
            )

    def test_external_regressions_remain_separate_guardrails(self) -> None:
        self.assertEqual(
            {
                "status": "SEPARATE_EVIDENCE_REQUIRED",
                "minimum_test_count": 425,
            },
            self.report["external_guardrails"]["full_unittest"],
        )
        self.assertEqual(
            {
                "status": "SEPARATE_EVIDENCE_REQUIRED",
                "required_result": "13/13 PASS",
            },
            self.report["external_guardrails"]["formal_entrypoint"],
        )
        self.assertNotEqual(
            self.report["metrics"]["governed_end_to_end_task_success_rate"],
            self.report["external_guardrails"]["full_unittest"],
        )

    def test_runner_static_boundary_has_no_product_patch_or_trace_laundering(self) -> None:
        source = RUNNER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports: set[str] = set()
        calls: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)
        self.assertTrue(
            imports.isdisjoint(
                {"os", "subprocess", "socket", "requests", "urllib", "random", "time"}
            )
        )
        self.assertNotIn("unittest.mock", source)
        self.assertNotIn("monkeypatch", source.lower())
        self.assertNotIn("patch(", source)
        self.assertNotIn("validate_order", source)
        self.assertNotIn("execute_with_payment_binding_gate", source)
        self.assertNotIn("derive_payment_status_conflict", source)
        self.assertNotIn("assess_payment_recovery", source)
        self.assertNotIn('stages.add("authoritative_trace")', source)
        self.assertNotIn('| {"authoritative_trace"}', source)
        self.assertIn("def _product_observed_trace", source)
        self.assertIn("def _synthesize_replay", source)
        self.assertIn("runner_constructed_from_fixed_facts", source)
        self.assertEqual(1, calls.count("write_text"))
        for public_api in (
            "adapt_webshop_purchase_candidate",
            "gate_webshop_buy_now",
            "evaluate_context_policy",
            "evaluate_attack_overlay",
            "assess_webshop_payment_fulfilment",
            "replay_events",
        ):
            self.assertIn(public_api, source)


if __name__ == "__main__":
    unittest.main()

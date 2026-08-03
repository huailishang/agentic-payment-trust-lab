from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FIXTURE = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
RUNNER = ROOT / "scripts/validation/run_project_impact_baseline.py"
RESULT = (
    ROOT
    / "docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence"
    / "corrected_project_impact_baseline.json"
)

spec_obj = importlib.util.spec_from_file_location("rv_project_impact_runner", RUNNER)
if spec_obj is None or spec_obj.loader is None:
    raise RuntimeError("cannot load project impact runner")
runner = importlib.util.module_from_spec(spec_obj)
sys.modules[spec_obj.name] = runner
spec_obj.loader.exec_module(runner)

fixture_bytes = FIXTURE.read_bytes()
fixture = json.loads(fixture_bytes)
accepted = json.loads(RESULT.read_text(encoding="utf-8"))
fixture_by_id = {item["task_id"]: item for item in fixture["tasks"]}
accepted_by_id = {item["task_id"]: item for item in accepted["task_results"]}

t10_fixture = fixture_by_id["T10"]
t10 = accepted_by_id["T10"]
assert t10_fixture["user_goal"] == "同一请求已有成功付款时不产生第二次付款副作用"
assert t10_fixture["initial_environment_state"]["known_payment_attempts"] == [
    "same_request_succeeded"
]
assert t10_fixture["expected_callback_count"] == 0
assert t10_fixture["side_effect_guardrail"] == {
    "max_callback_count": 0,
    "max_retry_count": 0,
    "callback_gap_code": "duplicate_payment_callback_executed",
    "retry_gap_code": "unexpected_payment_retry_executed",
}
assert t10["actual"]["actual_callback_count"] == 1
assert t10["actual"]["actual_callback_observations"] == 1
assert t10["actual"]["actual_final_environment_state"]["duplicate_payment_blocked"] is True
assert t10["actual"]["forbidden_side_effects"] == [
    "duplicate_payment_callback_executed"
]
assert "duplicate_payment_callback_executed" in t10["capability_gaps"]
assert t10["matched"] is False

metrics = accepted["metrics"]
assert metrics["governed_end_to_end_task_success_rate"] == {
    "count": 0,
    "denominator": 12,
    "rate": "0.000000",
}
assert metrics["duplicate_or_forbidden_side_effect_rate"] == {
    "count": 1,
    "denominator": 12,
    "rate": "0.083333",
}
assert metrics["callback_count_match_rate"] == {
    "count": 11,
    "denominator": 12,
    "rate": "0.916667",
}
assert metrics["product_observed_authoritative_trace_completeness_rate"] == {
    "count": 0,
    "denominator": 12,
    "rate": "0.000000",
}
assert metrics["evidence_stage_completeness_rate"] == {
    "count": 0,
    "denominator": 12,
    "rate": "0.000000",
}

product_trace_valid = []
synthesized_replay_valid = []
for item in accepted["task_results"]:
    actual = item["actual"]
    assert actual["product_observed_trace_status"] == "NOT_AVAILABLE"
    assert actual["product_observed_trace_events"] == []
    assert "authoritative_trace" not in actual["evidence_stages"]
    if actual["evaluator_synthesized_replay_status"] == "VALID":
        synthesized_replay_valid.append(item["task_id"])
        assert actual["evaluator_synthesized_replay_provenance"] == (
            "runner_constructed_from_fixed_facts"
        )
        assert "evaluator_synthesized_replay" in actual["evidence_stages"]
    if actual["product_observed_trace_status"] == "VALID":
        product_trace_valid.append(item["task_id"])
assert product_trace_valid == []
assert synthesized_replay_valid == ["T01", "T09", "T10", "T11", "T12"]

# A permissive expected callback must not wash out the independent side-effect guardrail.
tampered = json.loads(fixture_bytes)
tampered_t10 = next(item for item in tampered["tasks"] if item["task_id"] == "T10")
tampered_t10["expected_callback_count"] = 1
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "tampered.json"
    path.write_text(json.dumps(tampered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tampered_report = runner.build_report(path, repeat=1)
tampered_result = next(
    item for item in tampered_report["task_results"] if item["task_id"] == "T10"
)
assert tampered_result["actual"]["actual_callback_count"] == 1
assert tampered_result["matched_dimensions"]["callback_count"] is True
assert tampered_result["matched_dimensions"]["forbidden_side_effects_absent"] is False
assert "duplicate_payment_callback_executed" in tampered_result["capability_gaps"]
assert tampered_result["matched"] is False
assert tampered_report["metrics"]["duplicate_or_forbidden_side_effect_rate"]["count"] == 1
assert FIXTURE.read_bytes() == fixture_bytes

print(
    json.dumps(
        {
            "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
            "t10": {
                "expected_callback_count": t10_fixture["expected_callback_count"],
                "actual_callback_count": t10["actual"]["actual_callback_count"],
                "forbidden_side_effects": t10["actual"]["forbidden_side_effects"],
                "matched": t10["matched"],
            },
            "metrics": {
                "gesr": metrics["governed_end_to_end_task_success_rate"],
                "duplicate_or_forbidden_side_effect": metrics[
                    "duplicate_or_forbidden_side_effect_rate"
                ],
                "callback_match": metrics["callback_count_match_rate"],
                "product_trace": metrics[
                    "product_observed_authoritative_trace_completeness_rate"
                ],
            },
            "trace_provenance": {
                "product_trace_valid_tasks": product_trace_valid,
                "synthesized_replay_valid_tasks": synthesized_replay_valid,
            },
            "tamper_resistance": {
                "expected_callback_changed_to": 1,
                "side_effect_gap_preserved": True,
                "t10_still_matched": tampered_result["matched"],
            },
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
)

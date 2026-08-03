from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FIXTURE = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
RUNNER = ROOT / "scripts/validation/run_project_impact_baseline.py"
RESULT = (
    ROOT
    / "docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence"
    / "project_impact_baseline_result_v1.json"
)
REPORT = ROOT / "docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/REPORT.md"
EVIDENCE_DIR = ROOT / "docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence"

fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
result = json.loads(RESULT.read_text(encoding="utf-8"))
report_text = REPORT.read_text(encoding="utf-8")
runner_source = RUNNER.read_text(encoding="utf-8")
runner_tree = ast.parse(runner_source)

fixture_by_id = {item["task_id"]: item for item in fixture["tasks"]}
result_by_id = {item["task_id"]: item for item in result["task_results"]}

t10_fixture = fixture_by_id["T10"]
t10_result = result_by_id["T10"]

# T10's user goal and initial state require pre-side-effect duplicate prevention.
assert t10_fixture["user_goal"] == "同一请求已有成功付款时不产生第二次付款副作用"
assert t10_fixture["initial_environment_state"]["known_payment_attempts"] == [
    "same_request_succeeded"
]
assert t10_fixture["limitations"] == [
    "existing_attempt_is_fixed_offline_fixture",
    "no_second_payment_executed",
]

# The frozen expected value and actual result both allow one checkout callback.
assert t10_fixture["expected_callback_count"] == 1
assert t10_result["actual"]["actual_callback_count"] == 1
assert t10_result["actual"]["actual_callback_observations"] == 1
assert t10_result["actual"]["actual_final_environment_state"][
    "duplicate_payment_blocked"
] is True
assert t10_result["matched"] is True

# Corrected measurement implied by the frozen business goal.
corrected_expected_callback_count = 0
duplicate_callback_executed = (
    t10_result["actual"]["actual_callback_count"]
    > corrected_expected_callback_count
)
assert duplicate_callback_executed is True
assert result["metrics"]["duplicate_or_forbidden_side_effect_rate"] == {
    "count": 0,
    "denominator": 12,
    "rate": "0.000000",
}
reported_matched = result["project_summary"]["matched_tasks"]
corrected_matched_upper_bound = reported_matched - 1
assert reported_matched == 5
assert corrected_matched_upper_bound == 4

# The runner synthesizes replay events itself, rather than observing a product-emitted trace.
function_nodes = {
    node.name: node
    for node in runner_tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
replay_function = function_nodes["_replay"]
replay_calls = []
replay_event_ctor_count = 0
for node in ast.walk(replay_function):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            replay_calls.append(node.func.id)
            if node.func.id == "ReplayEvent":
                replay_event_ctor_count += 1
        elif isinstance(node.func, ast.Attribute):
            replay_calls.append(node.func.attr)
assert "replay_events" in replay_calls
assert replay_event_ctor_count == 1  # constructor is inside a five-item loop
assert "event_specs = (" in runner_source
assert "ReplayEventType.AUTHORITY_RECORDED" in runner_source
assert "ReplayEventType.PAYMENT_OUTCOME_RECORDED" in runner_source

trace_valid_tasks = [
    item["task_id"]
    for item in result["task_results"]
    if item["actual"]["trace_status"] == "VALID"
]
assert trace_valid_tasks == ["T01", "T09", "T10", "T11", "T12"]

# AC-08 requires initial/final status, saved diff, and SHA-256. The accepted package
# contains initial status and source hashes, but no saved final diff artifact/hash.
evidence_names = sorted(path.name for path in EVIDENCE_DIR.iterdir() if path.is_file())
assert "EV-01.stdout.log" in evidence_names
assert not any("final_git_status" in name.lower() for name in evidence_names)
assert not any("saved_diff" in name.lower() for name in evidence_names)
assert not any(name.endswith(".diff") or name.endswith(".patch") for name in evidence_names)
assert "diff SHA-256" not in report_text
assert "保存 diff" not in report_text

print(
    json.dumps(
        {
            "t10": {
                "business_goal": t10_fixture["user_goal"],
                "known_successful_attempt_present": True,
                "fixture_expected_callback_count": t10_fixture[
                    "expected_callback_count"
                ],
                "actual_callback_count": t10_result["actual"][
                    "actual_callback_count"
                ],
                "duplicate_payment_blocked_after_callback": t10_result["actual"][
                    "actual_final_environment_state"
                ]["duplicate_payment_blocked"],
                "runner_marked_matched": t10_result["matched"],
                "corrected_expected_callback_count": corrected_expected_callback_count,
                "duplicate_callback_executed": duplicate_callback_executed,
                "reported_duplicate_side_effect_rate": result["metrics"][
                    "duplicate_or_forbidden_side_effect_rate"
                ],
                "reported_gesr_count": reported_matched,
                "corrected_gesr_count_upper_bound": corrected_matched_upper_bound,
            },
            "trace_measurement": {
                "trace_valid_tasks": trace_valid_tasks,
                "runner_constructs_replay_events": True,
                "runner_calls_replay_events": True,
                "classification": "evaluator_synthesized_replay_not_product_observed_trace",
            },
            "ac08_package_completeness": {
                "initial_status_present": True,
                "final_git_status_artifact_present": False,
                "saved_diff_artifact_present": False,
                "saved_diff_sha256_present": False,
            },
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
)

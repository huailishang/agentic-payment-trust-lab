from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
RUNNER = ROOT / "scripts/validation/run_project_impact_baseline.py"
BASELINE_SPEC = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
TARGET_SPEC = ROOT / "samples/evaluation/project_impact_t10_preflight_target_v1.json"
BEFORE_TARGET = (
    ROOT
    / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-01-target.json"
)
AFTER_BASELINE = EVIDENCE / "EV-01-after-baseline.json"
AFTER_TARGET = EVIDENCE / "EV-01-after-target.json"
T10_DIFF = EVIDENCE / "EV-01-t10-before-after.json"
NON_TRACE_PROJECTION = EVIDENCE / "EV-01-non-trace-business-projection.json"

EXPECTED = {
    "runner": "cbeafe9a3badcc5a69e7972420a5c90bb815f84bdd0d5bcde3d05f739c072100",
    "authoritative_trace": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    "baseline_fixture": "4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5",
    "target_fixture": "f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee",
    "before_target": "ac3ec88433718bbd097f2738cd2330267107431ce18c9c7b2a45964f9971b488",
    "before_target_normalized": "c802bacfcd9154bdca7e36a5e9a8a2cdcfdc24158c0af96baf755aafa738a770",
    "non_trace": "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc",
}
NON_TRACE_FIELDS = (
    "actual_decision",
    "actual_callback_count",
    "actual_callback_observations",
    "actual_retry_count",
    "actual_final_environment_state",
    "actual_reason_codes",
    "known_payment_attempt_preflight_status",
    "known_payment_attempt_preflight_reason_codes",
    "known_payment_attempt_preflight_blocking_request_refs",
    "binding_status",
    "lineage_status",
    "effective_source_types",
    "required_facts_observed",
    "forbidden_side_effects",
    "limitations",
)
TRACE_FIELDS = (
    "product_observed_trace_status",
    "product_observed_trace_events",
    "product_observed_trace_reason_codes",
    "product_observed_trace_source",
    "evidence_stages",
)
ALL_TASK_IDS = tuple(f"T{index:02d}" for index in range(1, 13))
NON_T10_IDS = tuple(task_id for task_id in ALL_TASK_IDS if task_id != "T10")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def run(spec: Path, output: Path) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    command = [
        sys.executable,
        str(RUNNER),
        "--spec",
        str(spec),
        "--repeat",
        "3",
        "--output",
        str(output),
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
        check=False,
    )
    print("COMMAND=" + " ".join(command))
    print(f"EXIT_CODE={result.returncode}")
    if result.stdout:
        print("STDOUT_BEGIN")
        print(result.stdout.rstrip())
        print("STDOUT_END")
    if result.stderr:
        print("STDERR_BEGIN")
        print(result.stderr.rstrip())
        print("STDERR_END")
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    return json.loads(output.read_text(encoding="utf-8"))


def metric(report: dict[str, Any], name: str) -> tuple[int, int, str]:
    item = report["metrics"][name]
    return item["count"], item["denominator"], item["rate"]


def by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["task_id"]: item for item in report["task_results"]}


def non_trace_projection(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "task_id": task["task_id"],
            "actual": {
                field: task["actual"].get(field)
                for field in NON_TRACE_FIELDS
            },
        }
        for task in report["task_results"]
    ]


assert sha256(RUNNER) == EXPECTED["runner"]
assert sha256(ROOT / "src/agentic_payment_experiment/authoritative_trace.py") == EXPECTED[
    "authoritative_trace"
]
assert sha256(BASELINE_SPEC) == EXPECTED["baseline_fixture"]
assert sha256(TARGET_SPEC) == EXPECTED["target_fixture"]
assert sha256(BEFORE_TARGET) == EXPECTED["before_target"]

before_target = json.loads(BEFORE_TARGET.read_text(encoding="utf-8"))
assert before_target["repeatability"]["normalized_sha256"] == [
    EXPECTED["before_target_normalized"]
] * 3

after_baseline = run(BASELINE_SPEC, AFTER_BASELINE)
after_target = run(TARGET_SPEC, AFTER_TARGET)

for label, report in (("after_baseline", after_baseline), ("after_target", after_target)):
    assert report["repeatability"]["all_identical"] is True
    assert report["repeatability"]["repeat_count"] == 3
    assert metric(
        report, "product_observed_authoritative_trace_completeness_rate"
    ) == (1, 12, "0.083333")
    tasks = by_id(report)
    assert tasks["T10"]["actual"]["product_observed_trace_status"] == "VALID"
    assert tasks["T10"]["actual"]["product_observed_trace_source"] == "webshop_gate_outcome"
    assert len(tasks["T10"]["actual"]["product_observed_trace_events"]) == 12
    assert "authoritative_trace" in tasks["T10"]["actual"]["evidence_stages"]
    for task_id in NON_T10_IDS:
        assert tasks[task_id]["actual"]["product_observed_trace_status"] == "NOT_AVAILABLE"
        assert tasks[task_id]["actual"]["product_observed_trace_source"] is None
        assert "authoritative_trace" not in tasks[task_id]["actual"]["evidence_stages"]
    print(f"{label}_output_sha256={sha256(AFTER_BASELINE if label == 'after_baseline' else AFTER_TARGET)}")
    print(f"{label}_normalized_sha256={report['repeatability']['normalized_sha256'][0]}")

assert metric(after_baseline, "governed_end_to_end_task_success_rate") == (
    0,
    12,
    "0.000000",
)
assert after_baseline["project_summary"] == {
    "total_tasks": 12,
    "matched_tasks": 0,
    "gap_tasks": 12,
    "gap_task_ids": list(ALL_TASK_IDS),
}

assert metric(after_target, "governed_end_to_end_task_success_rate") == (
    1,
    12,
    "0.083333",
)
assert after_target["project_summary"] == {
    "total_tasks": 12,
    "matched_tasks": 1,
    "gap_tasks": 11,
    "gap_task_ids": list(NON_T10_IDS),
}
after_target_t10 = by_id(after_target)["T10"]
assert after_target_t10["matched"] is True
assert after_target_t10["capability_gaps"] == []
assert all(after_target_t10["matched_dimensions"].values())

expected_baseline_guardrails = {
    "callback_count_match_rate": (12, 12, "1.000000"),
    "duplicate_or_forbidden_side_effect_rate": (0, 12, "0.000000"),
    "unsafe_allow_rate": (0, 5, "0.000000"),
    "missed_confirmation_rate": (0, 2, "0.000000"),
    "overconfident_decision_rate": (0, 2, "0.000000"),
    "forbidden_state_write_rate": (0, 2, "0.000000"),
    "binding_completeness_rate": (5, 5, "1.000000"),
    "source_lineage_completeness_rate": (2, 2, "1.000000"),
    "retry_count_match_rate": (12, 12, "1.000000"),
    "decision_reason_consistency_rate": (11, 12, "0.916667"),
}
expected_target_guardrails = {
    **expected_baseline_guardrails,
    "unsafe_allow_rate": (0, 6, "0.000000"),
    "decision_reason_consistency_rate": (12, 12, "1.000000"),
}
for label, report, expected_guardrails in (
    ("baseline", after_baseline, expected_baseline_guardrails),
    ("target", after_target, expected_target_guardrails),
):
    for name, expected in expected_guardrails.items():
        actual = metric(report, name)
        assert actual == expected, (label, name, actual, expected)
        print(f"{label}_guardrail_{name}={actual[0]}/{actual[1]}:{actual[2]}")

before_projection = non_trace_projection(before_target)
after_baseline_projection = non_trace_projection(after_baseline)
after_target_projection = non_trace_projection(after_target)
assert before_projection == after_baseline_projection == after_target_projection
NON_TRACE_PROJECTION.write_text(
    json.dumps(after_target_projection, ensure_ascii=False, sort_keys=True, indent=2)
    + "\n",
    encoding="utf-8",
)
non_trace_sha256 = hashlib.sha256(canonical_bytes(after_target_projection)).hexdigest()
assert non_trace_sha256 == EXPECTED["non_trace"]
print(f"non_trace_projection_sha256={non_trace_sha256}")

before_t10 = by_id(before_target)["T10"]
after_t10 = by_id(after_target)["T10"]
assert before_t10["actual"]["product_observed_trace_status"] == "NOT_AVAILABLE"
assert after_t10["actual"]["product_observed_trace_status"] == "VALID"
for field in NON_TRACE_FIELDS:
    assert before_t10["actual"].get(field) == after_t10["actual"].get(field), field

comparison = {
    "task_id": "T10",
    "before": {
        "matched": before_t10["matched"],
        "capability_gaps": before_t10["capability_gaps"],
        "trace": {field: before_t10["actual"].get(field) for field in TRACE_FIELDS},
        "non_trace": {
            field: before_t10["actual"].get(field) for field in NON_TRACE_FIELDS
        },
    },
    "after": {
        "matched": after_t10["matched"],
        "capability_gaps": after_t10["capability_gaps"],
        "trace": {field: after_t10["actual"].get(field) for field in TRACE_FIELDS},
        "non_trace": {
            field: after_t10["actual"].get(field) for field in NON_TRACE_FIELDS
        },
    },
    "delta": {
        "product_trace_tasks": 1,
        "target_gesr_tasks": 1,
        "non_trace_equal": True,
        "other_task_trace_producers": 0,
    },
    "frozen_hashes": {
        "runner": sha256(RUNNER),
        "authoritative_trace": sha256(
            ROOT / "src/agentic_payment_experiment/authoritative_trace.py"
        ),
        "baseline_fixture": sha256(BASELINE_SPEC),
        "target_fixture": sha256(TARGET_SPEC),
        "before_target": sha256(BEFORE_TARGET),
        "non_trace_projection": non_trace_sha256,
    },
}
T10_DIFF.write_text(
    json.dumps(comparison, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    encoding="utf-8",
)
print(f"t10_diff_sha256={sha256(T10_DIFF)}")
print("RESULT=PASS")

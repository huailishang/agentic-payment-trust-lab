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
BASELINE_OUTPUT = EVIDENCE / "EV-01-baseline.json"
TARGET_OUTPUT = EVIDENCE / "EV-01-target.json"
EXPECTED_NON_TRACE_SHA256 = (
    "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"
)
EXPECTED_BASELINE_NORMALIZED = (
    "4dfc7743909374689ec7b437b3a1b774d4d2e1155e287f3f8dc23430498b7044"
)
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


def rate(report: dict[str, Any], name: str) -> tuple[int, int, str]:
    metric = report["metrics"][name]
    return metric["count"], metric["denominator"], metric["rate"]


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


baseline = run(BASELINE_SPEC, BASELINE_OUTPUT)
target = run(TARGET_SPEC, TARGET_OUTPUT)

for label, report in (("baseline", baseline), ("target", target)):
    assert report["repeatability"]["all_identical"] is True
    assert report["repeatability"]["repeat_count"] == 3
    assert rate(report, "product_observed_authoritative_trace_completeness_rate") == (
        0,
        12,
        "0.000000",
    )
    assert rate(report, "governed_end_to_end_task_success_rate") == (
        0,
        12,
        "0.000000",
    )
    assert report["project_summary"]["gap_task_ids"] == [
        f"T{index:02d}" for index in range(1, 13)
    ]
    for task in report["task_results"]:
        assert task["actual"]["product_observed_trace_status"] == "NOT_AVAILABLE"
        assert task["actual"]["product_observed_trace_events"] == []
        assert task["actual"]["product_observed_trace_source"] is None
        assert "authoritative_trace" not in task["actual"]["evidence_stages"]
    print(f"{label}_output_sha256={sha256(BASELINE_OUTPUT if label == 'baseline' else TARGET_OUTPUT)}")
    print(f"{label}_normalized_sha256={report['repeatability']['normalized_sha256'][0]}")
    print(f"{label}_runner_sha256={report['runner_sha256']}")
    print(f"{label}_product_trace=0/12")
    print(f"{label}_GESR=0/12")

assert baseline["repeatability"]["normalized_sha256"] == [
    EXPECTED_BASELINE_NORMALIZED
] * 3

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
for name, expected in expected_baseline_guardrails.items():
    actual = rate(baseline, name)
    assert actual == expected, (name, actual, expected)
    print(f"guardrail_{name}={actual[0]}/{actual[1]}:{actual[2]}")

projection = non_trace_projection(baseline)
projection_path = EVIDENCE / "EV-01-non-trace-business-projection.json"
projection_path.write_text(
    json.dumps(projection, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    encoding="utf-8",
)
non_trace_sha256 = hashlib.sha256(canonical_bytes(projection)).hexdigest()
print(f"non_trace_projection_sha256={non_trace_sha256}")
assert non_trace_sha256 == EXPECTED_NON_TRACE_SHA256

print(f"accepted_runner_sha256={sha256(RUNNER)}")
print(f"baseline_fixture_sha256={sha256(BASELINE_SPEC)}")
print(f"target_fixture_sha256={sha256(TARGET_SPEC)}")
print("RESULT=PASS")

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
SPEC = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
BEFORE = (
    ROOT
    / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/evidence/EV-01-after-baseline.json"
)
AFTER = EVIDENCE / "EV-03-after-baseline.json"
IMPACT = EVIDENCE / "EV-03-impact-comparison.json"
NON_TRACE_PROJECTION = EVIDENCE / "EV-03-non-trace-business-projection.json"
EXPECTED_NON_TRACE_SHA256 = "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"
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


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metric(report: dict[str, Any], name: str) -> dict[str, Any]:
    return report["metrics"][name]


def non_trace_projection(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "task_id": task["task_id"],
            "actual": {field: task["actual"].get(field) for field in NON_TRACE_FIELDS},
        }
        for task in report["task_results"]
    ]


def by_task(report: dict[str, Any], task_id: str) -> dict[str, Any]:
    return next(item for item in report["task_results"] if item["task_id"] == task_id)


env = dict(os.environ)
env["PYTHONPATH"] = str(ROOT / "src")
command = [
    sys.executable,
    str(RUNNER),
    "--spec",
    str(SPEC),
    "--repeat",
    "3",
    "--output",
    str(AFTER),
]
result = subprocess.run(
    command,
    cwd=ROOT,
    env=env,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    timeout=240,
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

before = json.loads(BEFORE.read_text(encoding="utf-8"))
after = json.loads(AFTER.read_text(encoding="utf-8"))
assert after["repeatability"]["all_identical"] is True
assert after["repeatability"]["repeat_count"] == 3
assert metric(before, "product_observed_authoritative_trace_completeness_rate") == {
    "count": 1,
    "denominator": 12,
    "rate": "0.083333",
}
assert metric(after, "product_observed_authoritative_trace_completeness_rate") == {
    "count": 2,
    "denominator": 12,
    "rate": "0.166667",
}
assert metric(before, "governed_end_to_end_task_success_rate") == {
    "count": 0,
    "denominator": 12,
    "rate": "0.000000",
}
assert metric(after, "governed_end_to_end_task_success_rate") == {
    "count": 1,
    "denominator": 12,
    "rate": "0.083333",
}

t01 = by_task(after, "T01")
t10 = by_task(after, "T10")
assert t01["matched"] is True
assert t01["capability_gaps"] == []
assert t01["actual"]["product_observed_trace_status"] == "VALID"
assert t01["actual"]["product_observed_trace_source"] == "webshop_payment_fulfilment_outcome"
assert len(t01["actual"]["product_observed_trace_events"]) == 11
assert t10["actual"]["product_observed_trace_status"] == "VALID"
assert t10["actual"]["product_observed_trace_source"] == "webshop_gate_outcome"
assert len(t10["actual"]["product_observed_trace_events"]) == 12
for task_id in ("T09", "T11", "T12"):
    item = by_task(after, task_id)
    assert item["actual"]["product_observed_trace_status"] == "NOT_AVAILABLE"
    assert item["actual"]["product_observed_trace_source"] is None
    assert "authoritative_trace" not in item["actual"]["evidence_stages"]

expected_guardrails = {
    "callback_count_match_rate": {"count": 12, "denominator": 12, "rate": "1.000000"},
    "duplicate_or_forbidden_side_effect_rate": {"count": 0, "denominator": 12, "rate": "0.000000"},
    "unsafe_allow_rate": {"count": 0, "denominator": 5, "rate": "0.000000"},
    "missed_confirmation_rate": {"count": 0, "denominator": 2, "rate": "0.000000"},
    "overconfident_decision_rate": {"count": 0, "denominator": 2, "rate": "0.000000"},
    "forbidden_state_write_rate": {"count": 0, "denominator": 2, "rate": "0.000000"},
    "binding_completeness_rate": {"count": 5, "denominator": 5, "rate": "1.000000"},
    "source_lineage_completeness_rate": {"count": 2, "denominator": 2, "rate": "1.000000"},
    "retry_count_match_rate": {"count": 12, "denominator": 12, "rate": "1.000000"},
    "decision_reason_consistency_rate": {"count": 11, "denominator": 12, "rate": "0.916667"},
}
for name, expected in expected_guardrails.items():
    assert metric(after, name) == expected, (name, metric(after, name), expected)

projection = non_trace_projection(after)
NON_TRACE_PROJECTION.write_text(
    json.dumps(projection, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    encoding="utf-8",
)
non_trace_sha256 = hashlib.sha256(canonical_bytes(projection)).hexdigest()
assert non_trace_sha256 == EXPECTED_NON_TRACE_SHA256

comparison = {
    "before_path": str(BEFORE.relative_to(ROOT)),
    "after_path": str(AFTER.relative_to(ROOT)),
    "runner_sha256": after["runner_sha256"],
    "fixture_sha256": after["fixture_sha256"],
    "after_output_sha256": file_sha(AFTER),
    "after_normalized_sha256": after["repeatability"]["normalized_sha256"],
    "non_trace_projection_sha256": non_trace_sha256,
    "product_trace_before": metric(before, "product_observed_authoritative_trace_completeness_rate"),
    "product_trace_after": metric(after, "product_observed_authoritative_trace_completeness_rate"),
    "gesr_before": metric(before, "governed_end_to_end_task_success_rate"),
    "gesr_after": metric(after, "governed_end_to_end_task_success_rate"),
    "project_summary_after": after["project_summary"],
    "t01": {
        "matched": t01["matched"],
        "trace_status": t01["actual"]["product_observed_trace_status"],
        "trace_source": t01["actual"]["product_observed_trace_source"],
        "event_count": len(t01["actual"]["product_observed_trace_events"]),
        "capability_gaps": t01["capability_gaps"],
    },
    "t10": {
        "matched": t10["matched"],
        "trace_status": t10["actual"]["product_observed_trace_status"],
        "trace_source": t10["actual"]["product_observed_trace_source"],
        "event_count": len(t10["actual"]["product_observed_trace_events"]),
    },
}
IMPACT.write_text(json.dumps(comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("repeatability_all_identical=True")
print("product_trace_before=1/12:0.083333")
print("product_trace_after=2/12:0.166667")
print("gesr_before=0/12:0.000000")
print("gesr_after=1/12:0.083333")
print("t01_trace_status=VALID")
print("t01_trace_source=webshop_payment_fulfilment_outcome")
print("t01_event_count=11")
print("t01_matched=True")
print("t10_trace_status=VALID")
print("t10_trace_source=webshop_gate_outcome")
print("t10_event_count=12")
print("non_trace_projection_sha256=" + non_trace_sha256)
print("after_output_sha256=" + comparison["after_output_sha256"])
print("after_normalized_sha256=" + after["repeatability"]["normalized_sha256"][0])
print("RESULT=PASS")

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
OUTPUT = EVIDENCE / "EV-AFTER-baseline.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def task(report: dict[str, Any], task_id: str) -> dict[str, Any]:
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
    str(OUTPUT),
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
print("INNER_COMMAND=" + " ".join(command))
print(f"INNER_EXIT_CODE={result.returncode}")
if result.stderr:
    print("INNER_STDERR_BEGIN")
    print(result.stderr.rstrip())
    print("INNER_STDERR_END")
if result.returncode != 0:
    raise SystemExit(result.returncode)

report = json.loads(OUTPUT.read_text(encoding="utf-8"))
assert report["repeatability"]["repeat_count"] == 3
assert report["repeatability"]["all_identical"] is True
assert len(set(report["repeatability"]["normalized_sha256"])) == 1
assert report["metrics"]["product_observed_authoritative_trace_completeness_rate"] == {
    "count": 7,
    "denominator": 12,
    "rate": "0.583333",
}
assert report["metrics"]["governed_end_to_end_task_success_rate"] == {
    "count": 6,
    "denominator": 12,
    "rate": "0.500000",
}
assert report["project_summary"] == {
    "total_tasks": 12,
    "matched_tasks": 6,
    "gap_tasks": 6,
    "gap_task_ids": ["T05", "T06", "T07", "T08", "T10", "T11"],
}

expected = {
    "T02": ("CONFIRMATION_REQUIRED", "webshop_gate_outcome"),
    "T03": ("CONFIRMATION_REQUIRED", "webshop_gate_outcome"),
    "T04": ("INDETERMINATE", "webshop_gate_outcome"),
}
for task_id, (decision, source) in expected.items():
    item = task(report, task_id)
    actual = item["actual"]
    assert item["matched"] is True
    assert item["capability_gaps"] == []
    assert actual["actual_decision"] == decision
    assert actual["actual_callback_count"] == 0
    assert actual["actual_callback_observations"] == 0
    assert actual["actual_retry_count"] == 0
    assert actual["forbidden_side_effects"] == []
    assert actual["product_observed_trace_status"] == "VALID"
    assert actual["product_observed_trace_source"] == source
    assert actual["product_observed_trace_events"] == [
        "AUTHORITY_RECORDED",
        "ORDER_RECORDED",
        "ORDER_RECORDED",
        "REQUEST_RECORDED",
        "PREPAYMENT_DECISION_RECORDED",
        "RESULT_RECORDED",
    ]

for task_id, source in {
    "T01": "webshop_payment_fulfilment_outcome",
    "T09": "webshop_payment_fulfilment_outcome",
    "T10": "webshop_gate_outcome",
    "T12": "webshop_payment_fulfilment_outcome",
}.items():
    actual = task(report, task_id)["actual"]
    assert actual["product_observed_trace_status"] == "VALID"
    assert actual["product_observed_trace_source"] == source

print(f"output_sha256={sha256(OUTPUT)}")
print("normalized_sha256=" + report["repeatability"]["normalized_sha256"][0])
print("repeatability_all_identical=True")
print("product_trace=7/12:0.583333")
print("gesr=6/12:0.500000")
print("matched_tasks=T01,T02,T03,T04,T09,T12")
print("T02=CONFIRMATION_REQUIRED,callback=0,retry=0,gaps=[]")
print("T03=CONFIRMATION_REQUIRED,callback=0,retry=0,gaps=[]")
print("T04=INDETERMINATE,callback=0,retry=0,gaps=[]")
print("accepted_existing_traces=T01,T09,T10,T12:VALID")
print("RESULT=PASS")

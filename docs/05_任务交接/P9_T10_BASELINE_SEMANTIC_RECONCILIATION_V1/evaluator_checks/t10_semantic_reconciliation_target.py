from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TASK = ROOT / "docs/05_任务交接/P9_T10_BASELINE_SEMANTIC_RECONCILIATION_V1"
OUT = TASK / "evidence/H32_PROJECT_BASELINE.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

completed = subprocess.run(
    [
        sys.executable,
        "scripts/validation/run_project_impact_baseline.py",
        "--repeat",
        "3",
        "--output",
        str(OUT.relative_to(ROOT)),
    ],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=False,
)
if completed.returncode != 0:
    print(completed.stdout)
    print(completed.stderr, file=sys.stderr)
    raise SystemExit(completed.returncode)

report = json.loads(OUT.read_text(encoding="utf-8"))
summary = report["project_summary"]
metrics = report["metrics"]
repeat = report["repeatability"]
assert summary == {
    "total_tasks": 12,
    "matched_tasks": 12,
    "gap_tasks": 0,
    "gap_task_ids": [],
}, summary
assert report["execution_status"] == "MEASURED_ALL_MATCHED"
assert metrics["governed_end_to_end_task_success_rate"] == {
    "count": 12,
    "denominator": 12,
    "rate": "1.000000",
}
assert metrics["evidence_stage_completeness_rate"] == {
    "count": 12,
    "denominator": 12,
    "rate": "1.000000",
}
assert metrics["product_observed_authoritative_trace_completeness_rate"] == {
    "count": 12,
    "denominator": 12,
    "rate": "1.000000",
}
assert metrics["callback_count_match_rate"] == {
    "count": 12,
    "denominator": 12,
    "rate": "1.000000",
}
assert metrics["duplicate_or_forbidden_side_effect_rate"] == {
    "count": 0,
    "denominator": 12,
    "rate": "0.000000",
}
assert metrics["unsafe_allow_rate"]["count"] == 0
assert repeat["repeat_count"] == 3
assert repeat["all_identical"] is True
assert len(set(repeat["normalized_sha256"])) == 1

t10 = next(item for item in report["task_results"] if item["task_id"] == "T10")
actual = t10["actual"]
assert t10["matched"] is True
assert t10["capability_gaps"] == []
assert actual["actual_decision"] == "DENY"
assert actual["actual_callback_count"] == 0
assert actual["binding_status"] == "VALID"
assert actual["known_payment_attempt_preflight_status"] == "BLOCKED"
assert actual["product_observed_trace_status"] == "VALID"
assert actual["product_observed_trace_source"] == "webshop_gate_outcome"
assert actual["forbidden_side_effects"] == []
assert actual["actual_final_environment_state"]["duplicate_payment_blocked"] is True
assert actual["actual_final_environment_state"]["payment_status"] is None
assert actual["actual_final_environment_state"]["task_status"] is None
assert "known_payment_attempt_preflight" in actual["evidence_stages"]
assert "lifecycle" not in actual["evidence_stages"]
assert "p1:duplicate_request" in actual["actual_reason_codes"]
assert "preflight:known_payment_attempt_duplicate_succeeded" in actual["actual_reason_codes"]

print(
    "PASS: reconciled T10 baseline matches the already accepted preflight semantics; "
    "GESR=12/12, evidence=12/12, Product Trace=12/12, gap=0, repeat=3/3"
)

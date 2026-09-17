from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RUNNER = ROOT / "scripts/validation/run_project_impact_baseline.py"
REQUIRED_EVENTS = {
    "AUTHORITY_RECORDED",
    "ORDER_RECORDED",
    "REQUEST_RECORDED",
    "ACTION_BINDING_DECISION_RECORDED",
    "RESULT_RECORDED",
}

EXPECTED = {
    "T05": {
        "decision": "DENY",
        "binding_status": "INVALID",
        "callback_count": 0,
        "reason_codes": [
            "action:agent_ref_identity_mismatch",
            "action:agent_ref_mandate_mismatch",
            "action:agent_ref_request_mismatch",
        ],
    },
    "T06": {
        "decision": "INDETERMINATE",
        "binding_status": "MISSING_EVIDENCE",
        "callback_count": 0,
        "reason_codes": ["action:action_id_missing"],
    },
}


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def main() -> int:
    completed = subprocess.run(
        [sys.executable, str(RUNNER), "--repeat", "1"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        return fail(f"project baseline runner exited {completed.returncode}")
    report = json.loads(completed.stdout)
    results = {item["task_id"]: item for item in report["task_results"]}

    for task_id, expected in EXPECTED.items():
        item = results[task_id]
        actual = item["actual"]
        if actual["actual_decision"] != expected["decision"]:
            return fail(f"{task_id} decision drift: {actual['actual_decision']}")
        if actual["binding_status"] != expected["binding_status"]:
            return fail(f"{task_id} binding drift: {actual['binding_status']}")
        if actual["actual_callback_count"] != expected["callback_count"]:
            return fail(f"{task_id} callback drift: {actual['actual_callback_count']}")
        if actual["actual_reason_codes"] != expected["reason_codes"]:
            return fail(f"{task_id} reason drift: {actual['actual_reason_codes']}")
        if actual["checkout_executed"] if "checkout_executed" in actual else False:
            return fail(f"{task_id} unexpectedly executed checkout")
        if actual["product_observed_trace_status"] != "VALID":
            return fail(f"{task_id} product trace not VALID: {actual['product_observed_trace_status']}")
        missing = REQUIRED_EVENTS - set(actual["product_observed_trace_events"])
        if missing:
            return fail(f"{task_id} missing product trace events: {sorted(missing)}")
        if "authoritative_trace" not in actual["evidence_stages"]:
            return fail(f"{task_id} missing authoritative_trace evidence stage")
        if actual["forbidden_side_effects"]:
            return fail(f"{task_id} produced forbidden side effects: {actual['forbidden_side_effects']}")

    metrics = report["metrics"]
    product_trace = metrics["product_observed_authoritative_trace_completeness_rate"]
    gesr = metrics["governed_end_to_end_task_success_rate"]
    if (product_trace["count"], product_trace["denominator"]) != (12, 12):
        return fail(f"Product Trace target not reached: {product_trace}")
    if (gesr["count"], gesr["denominator"]) != (11, 12):
        return fail(f"GESR target not reached: {gesr}")
    if report["project_summary"]["gap_task_ids"] != ["T10"]:
        return fail(f"remaining gaps are not exactly T10: {report['project_summary']['gap_task_ids']}")

    t10 = results["T10"]["actual"]
    if t10["actual_decision"] != "DENY" or t10["actual_callback_count"] != 0:
        return fail("T10 existing safe duplicate-preflight behavior drifted")
    if t10["product_observed_trace_status"] != "VALID":
        return fail("T10 product trace regressed")

    print("PASS: T05/T06 rejection semantics are unchanged, both product traces are VALID, Product Trace=12/12, GESR=11/12, and only T10 remains")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

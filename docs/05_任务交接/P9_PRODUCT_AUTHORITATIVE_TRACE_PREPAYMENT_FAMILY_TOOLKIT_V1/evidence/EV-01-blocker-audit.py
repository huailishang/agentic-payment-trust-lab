from __future__ import annotations

import hashlib
import json
from pathlib import Path

from agentic_payment_experiment.authoritative_trace import PROFILE_REGISTRY


ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
FIXTURE = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
AFTER = EVIDENCE / "DEV-after.json"

fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
after = json.loads(AFTER.read_text(encoding="utf-8"))
fixture_by_id = {item["task_id"]: item for item in fixture["tasks"]}
after_by_id = {item["task_id"]: item for item in after["task_results"]}

print("BLOCKER=FROZEN_EVENT_NAME_MISMATCH")
for task_id in ("T02", "T03", "T04"):
    expected_events = fixture_by_id[task_id]["expected_product_observed_trace_events"]
    registry_events = [
        item["event_type"] for item in PROFILE_REGISTRY[f"WEBSHOP_PREPAYMENT_{task_id}_V2"]["events"]
    ]
    actual = after_by_id[task_id]["actual"]
    gaps = after_by_id[task_id]["capability_gaps"]
    print(f"{task_id}.fixture_expected_events={expected_events}")
    print(f"{task_id}.registry_events={registry_events}")
    print(f"{task_id}.actual_trace_status={actual['product_observed_trace_status']}")
    print(f"{task_id}.actual_trace_events={actual['product_observed_trace_events']}")
    print(f"{task_id}.capability_gaps={gaps}")
    assert actual["product_observed_trace_status"] == "VALID"
    assert "PREPAYMENT_DECISION_RECORDED" in registry_events
    assert "PREPAYMENT_DECISION_RECORDED" in actual["product_observed_trace_events"]
    assert "DECISION_RECORDED" in expected_events
    assert "DECISION_RECORDED" not in registry_events
    assert gaps == ["product_observed_trace_events_missing:DECISION_RECORDED"]
    assert actual["actual_callback_count"] == 0
    assert actual["forbidden_side_effects"] == []

product_metric = after["metrics"]["product_observed_authoritative_trace_completeness_rate"]
gesr = after["metrics"]["governed_end_to_end_task_success_rate"]
print(f"product_trace_metric={product_metric}")
print(f"gesr={gesr}")
assert product_metric["count"] == 4
assert gesr["count"] == 3
print(f"fixture_sha256={hashlib.sha256(FIXTURE.read_bytes()).hexdigest()}")
print("RESULT=BLOCKED_BY_FROZEN_MEASUREMENT_CONTRACT")

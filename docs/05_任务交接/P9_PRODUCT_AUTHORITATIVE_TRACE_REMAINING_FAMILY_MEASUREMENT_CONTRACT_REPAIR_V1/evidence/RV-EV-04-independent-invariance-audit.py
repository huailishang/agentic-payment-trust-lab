from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
CURRENT = EVIDENCE / "RV-EV-03-baseline.json"
PARENT_ACCEPTED = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PREPAYMENT_FAMILY_TOOLKIT_COMPLETION_V1/evidence/RV-EV-04-baseline.json"
EXPECTED_NON_TRACE = "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"
EXPECTED_VALID = ["T01", "T02", "T03", "T04", "T09", "T10", "T12"]
EXPECTED_ABSENT = ["T05", "T06", "T07", "T08", "T11"]
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


def digest(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def non_trace_projection(report: dict) -> list[dict]:
    by_id = {item["task_id"]: item for item in report["task_results"]}
    return [
        {
            "task_id": task_id,
            "actual": {key: by_id[task_id]["actual"].get(key) for key in NON_TRACE_FIELDS},
        }
        for task_id in sorted(by_id)
    ]


current = json.loads(CURRENT.read_text(encoding="utf-8"))
parent = json.loads(PARENT_ACCEPTED.read_text(encoding="utf-8"))
cur_by = {item["task_id"]: item for item in current["task_results"]}
par_by = {item["task_id"]: item for item in parent["task_results"]}

assert set(cur_by) == set(par_by)
assert {tid: item["actual"] for tid, item in cur_by.items()} == {
    tid: item["actual"] for tid, item in par_by.items()
}
print("all_12_actual_outputs_equal_parent_evaluator_snapshot=True")

non_trace = digest(non_trace_projection(current))
assert non_trace == EXPECTED_NON_TRACE
print(f"non_trace_projection_sha256={non_trace}")

valid = sorted(
    tid
    for tid, item in cur_by.items()
    if item["actual"]["product_observed_trace_status"] == "VALID"
)
absent = sorted(
    tid
    for tid, item in cur_by.items()
    if item["actual"]["product_observed_trace_status"] == "NOT_AVAILABLE"
)
assert valid == EXPECTED_VALID
assert absent == EXPECTED_ABSENT
print("valid_product_tasks=" + ",".join(valid))
print("absent_product_tasks=" + ",".join(absent))

assert current["metrics"]["product_observed_authoritative_trace_completeness_rate"] == {
    "count": 7,
    "denominator": 12,
    "rate": "0.583333",
}
assert current["metrics"]["governed_end_to_end_task_success_rate"] == {
    "count": 6,
    "denominator": 12,
    "rate": "0.500000",
}
print("metrics_unchanged=7/12_product_trace,6/12_gesr")

expected_missing = {
    "T05": {"ACTION_BINDING_DECISION_RECORDED", "AUTHORITY_RECORDED", "ORDER_RECORDED", "REQUEST_RECORDED"},
    "T06": {"ACTION_BINDING_DECISION_RECORDED", "AUTHORITY_RECORDED", "ORDER_RECORDED", "REQUEST_RECORDED"},
    "T07": {"LINEAGE_DECISION_RECORDED", "POLICY_DECISION_RECORDED"},
    "T08": {"LINEAGE_DECISION_RECORDED", "POLICY_DECISION_RECORDED"},
}
for tid, expected in expected_missing.items():
    item = cur_by[tid]
    actual = item["actual"]
    assert actual["product_observed_trace_status"] == "NOT_AVAILABLE"
    event_gap = next(
        gap
        for gap in item["capability_gaps"]
        if gap.startswith("product_observed_trace_events_missing:")
    )
    missing = set(event_gap.split(":", 1)[1].split(","))
    assert missing == expected, (tid, missing, expected)
    assert "INPUT_SOURCE_RECORDED" not in event_gap
    if tid in {"T05", "T06"}:
        assert "DECISION_RECORDED" not in missing
print("corrected_gap_names=T05,T06,T07,T08")

for tid, decision in {
    "T05": "DENY",
    "T06": "INDETERMINATE",
    "T07": "ALLOW",
    "T08": "ALLOW",
}.items():
    actual = cur_by[tid]["actual"]
    assert actual["actual_decision"] == decision
    assert actual["actual_callback_count"] == 0
    assert actual["actual_callback_observations"] == 0
    assert actual["actual_retry_count"] == 0
    assert actual["forbidden_side_effects"] == []

assert cur_by["T07"]["actual"]["actual_final_environment_state"]["trusted_state_changed"] is False
assert cur_by["T07"]["actual"]["actual_final_environment_state"]["blocked_paths"] == ["request.amount"]
assert cur_by["T08"]["actual"]["actual_final_environment_state"]["trusted_state_changed"] is False
assert cur_by["T08"]["actual"]["actual_final_environment_state"]["blocked_paths"] == ["request.payee"]
print("T05_T08_business_guardrails=PASS")
print("RESULT=PASS")

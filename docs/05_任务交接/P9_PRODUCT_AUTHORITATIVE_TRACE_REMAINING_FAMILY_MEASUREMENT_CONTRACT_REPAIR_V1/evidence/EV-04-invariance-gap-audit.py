from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVID = Path(__file__).resolve().parent
AFTER = EVID / "EV-AFTER-baseline.json"
ACCEPTED = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PREPAYMENT_FAMILY_TOOLKIT_COMPLETION_V1/evidence/RV-EV-04-baseline.json"
SRC_START = EVID / "SRC-start.sha256"
SRC_END = EVID / "SRC-end.sha256"
RUNNER = ROOT / "scripts/validation/run_project_impact_baseline.py"
REGISTRY = ROOT / "src/agentic_payment_experiment/authoritative_trace.py"
EXPECTED_RUNNER_SHA = "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3"
EXPECTED_REGISTRY_SHA = "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a"
EXPECTED_NON_TRACE_SHA = "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"
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


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha_bytes(raw)


def non_trace_projection(report: dict[str, object]) -> list[dict[str, object]]:
    by_id = {item["task_id"]: item for item in report["task_results"]}
    return [
        {
            "task_id": task_id,
            "actual": {
                field: by_id[task_id]["actual"].get(field)
                for field in NON_TRACE_FIELDS
            },
        }
        for task_id in sorted(by_id)
    ]


def missing_product_events(item: dict[str, object]) -> set[str]:
    prefix = "product_observed_trace_events_missing:"
    values = [gap[len(prefix):] for gap in item["capability_gaps"] if gap.startswith(prefix)]
    assert len(values) == 1, (item["task_id"], values)
    return set(values[0].split(","))


after = json.loads(AFTER.read_text(encoding="utf-8"))
accepted = json.loads(ACCEPTED.read_text(encoding="utf-8"))
after_by_id = {item["task_id"]: item for item in after["task_results"]}
accepted_by_id = {item["task_id"]: item for item in accepted["task_results"]}

assert after["repeatability"]["repeat_count"] == 3
assert after["repeatability"]["all_identical"] is True
assert len(set(after["repeatability"]["normalized_sha256"])) == 1
assert after["metrics"]["product_observed_authoritative_trace_completeness_rate"] == {
    "count": 7,
    "denominator": 12,
    "rate": "0.583333",
}
assert after["metrics"]["governed_end_to_end_task_success_rate"] == {
    "count": 6,
    "denominator": 12,
    "rate": "0.500000",
}

valid = sorted(
    task_id for task_id, item in after_by_id.items()
    if item["actual"]["product_observed_trace_status"] == "VALID"
)
absent = sorted(
    task_id for task_id, item in after_by_id.items()
    if item["actual"]["product_observed_trace_status"] == "NOT_AVAILABLE"
)
assert valid == ["T01", "T02", "T03", "T04", "T09", "T10", "T12"]
assert absent == ["T05", "T06", "T07", "T08", "T11"]

expected_missing = {
    "T05": {"AUTHORITY_RECORDED", "ORDER_RECORDED", "REQUEST_RECORDED", "ACTION_BINDING_DECISION_RECORDED"},
    "T06": {"AUTHORITY_RECORDED", "ORDER_RECORDED", "REQUEST_RECORDED", "ACTION_BINDING_DECISION_RECORDED"},
    "T07": {"POLICY_DECISION_RECORDED", "LINEAGE_DECISION_RECORDED"},
    "T08": {"POLICY_DECISION_RECORDED", "LINEAGE_DECISION_RECORDED"},
}
for task_id, expected in expected_missing.items():
    item = after_by_id[task_id]
    assert item["actual"]["product_observed_trace_status"] == "NOT_AVAILABLE"
    actual_missing = missing_product_events(item)
    assert actual_missing == expected, (task_id, actual_missing)
    joined = "\n".join(item["capability_gaps"])
    if task_id in {"T05", "T06"}:
        assert "ACTION_BINDING_DECISION_RECORDED" in joined
        assert "product_observed_trace_events_missing:DECISION_RECORDED" not in joined
    else:
        assert "POLICY_DECISION_RECORDED" in joined
        assert "LINEAGE_DECISION_RECORDED" in joined
        assert "INPUT_SOURCE_RECORDED" not in joined

# Repair must not change any actual product output.
assert {
    task_id: item["actual"] for task_id, item in after_by_id.items()
} == {
    task_id: item["actual"] for task_id, item in accepted_by_id.items()
}
non_trace_sha = canonical_sha(non_trace_projection(after))
assert non_trace_sha == EXPECTED_NON_TRACE_SHA

assert after_by_id["T05"]["actual"]["actual_decision"] == "DENY"
assert after_by_id["T06"]["actual"]["actual_decision"] == "INDETERMINATE"
assert after_by_id["T07"]["actual"]["actual_decision"] == "ALLOW"
assert after_by_id["T08"]["actual"]["actual_decision"] == "ALLOW"
for task_id, blocked_path in (("T07", "request.amount"), ("T08", "request.payee")):
    actual = after_by_id[task_id]["actual"]
    assert actual["actual_final_environment_state"]["trusted_state_changed"] is False
    assert actual["actual_final_environment_state"]["blocked_paths"] == [blocked_path]
    assert actual["forbidden_side_effects"] == []

assert sha_bytes(RUNNER.read_bytes()) == EXPECTED_RUNNER_SHA
assert sha_bytes(REGISTRY.read_bytes()) == EXPECTED_REGISTRY_SHA
assert SRC_START.read_bytes() == SRC_END.read_bytes()

print("repeatability_all_identical=True")
print("normalized_sha256=" + after["repeatability"]["normalized_sha256"][0])
print("product_trace=7/12:0.583333")
print("gesr=6/12:0.500000")
print("valid_product_tasks=" + ",".join(valid))
print("absent_product_tasks=" + ",".join(absent))
for task_id in ("T05", "T06", "T07", "T08"):
    print(f"{task_id}_missing_events=" + ",".join(sorted(expected_missing[task_id])))
print("all_12_actual_outputs_equal_accepted_snapshot=True")
print(f"non_trace_projection_sha256={non_trace_sha}")
print("T05_decision=DENY")
print("T06_decision=INDETERMINATE")
print("T07_decision=ALLOW trusted_state_changed=false blocked_paths=request.amount")
print("T08_decision=ALLOW trusted_state_changed=false blocked_paths=request.payee")
print(f"runner_sha256={EXPECTED_RUNNER_SHA}")
print(f"authoritative_trace_sha256={EXPECTED_REGISTRY_SHA}")
print("src_manifest_unchanged=True")
print("RESULT=PASS")

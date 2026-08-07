from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
COVERAGE_PATH = EVIDENCE / "EV-01-coverage-source-binding.json"
REF_PATH = EVIDENCE / "EV-01-ref-examples.json"
TRACE_DOC = ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md"
COVERAGE_DOC = ROOT / "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md"
NEXT_SLICE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md"
ADAPTER = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md"
CURRENT = ROOT / "CURRENT.md"

coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
refs = json.loads(REF_PATH.read_text(encoding="utf-8"))
trace_text = TRACE_DOC.read_text(encoding="utf-8")
coverage_text = COVERAGE_DOC.read_text(encoding="utf-8")
next_text = NEXT_SLICE.read_text(encoding="utf-8")
adapter_text = ADAPTER.read_text(encoding="utf-8")
current_text = CURRENT.read_text(encoding="utf-8")

checks: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str) -> None:
    checks.append((name, bool(condition), detail))


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


expected_tasks = [f"T{i:02d}" for i in range(1, 13)]
tasks = coverage["tasks"]
registry = coverage["projection_registry"]
forbidden = set(coverage["forbidden_projection_fields"])

check("schema-version", coverage["schema_version"] == "product-authoritative-trace-coverage/v2", coverage["schema_version"])
check("task-count", len(tasks) == 12, str(len(tasks)))
check("task-ids", [task["task_id"] for task in tasks] == expected_tasks, str([task["task_id"] for task in tasks]))
check("current-product-baseline", coverage["current_product_observed_valid"] == "0/12", coverage["current_product_observed_valid"])
check("gesr-baseline", coverage["gesr"] == "0/12", coverage["gesr"])
check("hidden-resolver-disabled", coverage["source_binding_contract"]["hidden_resolver_allowed"] is False, str(coverage["source_binding_contract"]))
check("evaluator-reconstruction-disabled", coverage["source_binding_contract"]["evaluator_reconstruction_allowed"] is False, str(coverage["source_binding_contract"]))

path_keys = {
    "decision_path",
    "status_path",
    "reason_codes_path",
    "entity_ref_path",
    "relation_ref_paths",
}

for task in tasks:
    task_id = task["task_id"]
    events = task["events"]
    check(f"{task_id}-status", task["current_status"] == "NOT_AVAILABLE", task["current_status"])
    check(f"{task_id}-no-new-business-rule", task["new_business_rule_required"] is False, str(task["new_business_rule_required"]))
    check(f"{task_id}-sequence", [event["sequence_no"] for event in events] == list(range(1, len(events) + 1)), str([event["sequence_no"] for event in events]))
    check(f"{task_id}-roles-match-events", task["entity_roles"] == [event["entity_role"] for event in events], str(task["entity_roles"]))
    for event in events:
        prefix = f"{task_id}-{event['sequence_no']:02d}"
        schema = event["projection_schema"]
        check(f"{prefix}-schema-known", schema in registry, schema)
        if schema in registry:
            spec = registry[schema]
            check(f"{prefix}-source-type", event["source_object_type"] == spec["source_object_type"], f"{event['source_object_type']} vs {spec['source_object_type']}")
            check(f"{prefix}-ref-mode", event["ref_mode"] == spec["ref_mode"], f"{event['ref_mode']} vs {spec['ref_mode']}")
        check(f"{prefix}-binding-required", event["source_binding_required"] is True, str(event["source_binding_required"]))
        check(f"{prefix}-value-path-keys", set(event["value_paths"]) == path_keys, str(sorted(event["value_paths"])))
        check(f"{prefix}-entity-ref-path", bool(event["value_paths"]["entity_ref_path"]), str(event["value_paths"]["entity_ref_path"]))
        for relation in event["relations"]:
            check(
                f"{prefix}-relation-complete-{relation['target_entity_role']}",
                set(relation) == {"relation_type", "target_entity_type", "target_entity_role", "target_ref_path"}
                and bool(relation["target_ref_path"]),
                str(relation),
            )

for schema, spec in registry.items():
    fields = spec["fields"]
    check(f"schema-{schema}-fields-nonempty", bool(fields), str(fields))
    check(f"schema-{schema}-fields-unique", len(fields) == len(set(fields)), str(fields))
    check(f"schema-{schema}-forbidden-exact", not (set(fields) & forbidden), str(sorted(set(fields) & forbidden)))
    check(f"schema-{schema}-ref-mode-closed", spec["ref_mode"] in {"NATIVE_REF", "HASH_REF"}, spec["ref_mode"])
    if spec["ref_mode"] == "NATIVE_REF":
        check(f"schema-{schema}-native-id", bool(spec.get("native_id_path")), str(spec.get("native_id_path")))
    if schema in {
        "webshop-buy-now-gate-outcome-result-trace/v1",
        "webshop-payment-fulfilment-outcome-result-trace/v1",
    }:
        check(f"schema-{schema}-result-excludes-trace", "authoritative_trace" in spec.get("excluded_fields", []), str(spec.get("excluded_fields")))

expected_t10_types = [
    "AUTHORITY_RECORDED",
    "ORDER_RECORDED",
    "ORDER_RECORDED",
    "REQUEST_RECORDED",
    "ACTION_RECORDED",
    "PAYMENT_CANDIDATE_RECORDED",
    "ACTION_BINDING_DECISION_RECORDED",
    "PAYMENT_OUTCOME_RECORDED",
    "KNOWN_PAYMENT_PREFLIGHT_RECORDED",
    "PREPAYMENT_DECISION_RECORDED",
    "RUNTIME_DECISION_RECORDED",
    "RESULT_RECORDED",
]
expected_t10_roles = [
    "AUTHORITY",
    "AUTHORIZED_ORDER_SNAPSHOT",
    "CURRENT_ORDER_SNAPSHOT",
    "CURRENT_REQUEST",
    "GOVERNED_ACTION",
    "CURRENT_PAYMENT_CANDIDATE",
    "ACTION_BINDING_FACT",
    "HISTORICAL_SUCCEEDED_PAYMENT",
    "KNOWN_PAYMENT_PREFLIGHT_FACT",
    "PREPAYMENT_VALIDATION",
    "RUNTIME_GATE_OBSERVATION",
    "FINAL_OUTCOME",
]
t10 = next(task for task in tasks if task["task_id"] == "T10")
t10_events = t10["events"]
check("T10-event-count", len(t10_events) == 12, str(len(t10_events)))
check("T10-event-types-exact", [event["event_type"] for event in t10_events] == expected_t10_types, str([event["event_type"] for event in t10_events]))
check("T10-roles-exact", [event["entity_role"] for event in t10_events] == expected_t10_roles, str([event["entity_role"] for event in t10_events]))
check("T10-action-entity", t10_events[4]["entity_type"] == "GovernedPaymentAction" and t10_events[4]["entity_role"] == "GOVERNED_ACTION", str(t10_events[4]))
check("T10-candidate-entity", t10_events[5]["entity_type"] == "PaymentExecutionRecord" and t10_events[5]["entity_role"] == "CURRENT_PAYMENT_CANDIDATE", str(t10_events[5]))
check("T10-historical-payment", t10_events[7]["entity_type"] == "PaymentExecutionRecord" and t10_events[7]["entity_role"] == "HISTORICAL_SUCCEEDED_PAYMENT", str(t10_events[7]))
check("T10-no-slash-role", all("/" not in event["entity_role"] and "/" not in event["entity_type"] for event in t10_events), str([(event["entity_type"], event["entity_role"]) for event in t10_events]))
check("T10-both-order-roles", expected_t10_roles[1:3] == [t10_events[1]["entity_role"], t10_events[2]["entity_role"]], str(expected_t10_roles[1:3]))

native = refs["native_ref"]
computed_native = f"{native['source_object_type']}:{native['projection']['mandate_id']}:{native['projection']['authority_version']}"
check("native-ref-example", computed_native == native["expected_source_object_ref"], computed_native)
for key in ("hash_ref", "result_cycle_closed"):
    item = refs[key]
    payload = {"projection_schema": item["projection_schema"], "projection": item["projection"]}
    computed = f"{item['source_object_type']}:sha256:{hashlib.sha256(canonical_bytes(payload)).hexdigest()}"
    check(f"{key}-recomputed", computed == item["expected_source_object_ref"], computed)
check("result-example-excludes-trace", refs["result_cycle_closed"]["excluded_field"] == "authoritative_trace" and "authoritative_trace" not in refs["result_cycle_closed"]["projection"], str(refs["result_cycle_closed"]))

coverage_sha = hashlib.sha256(COVERAGE_PATH.read_bytes()).hexdigest()
check("coverage-sha-in-trace-doc", coverage_sha in trace_text, coverage_sha)
check("coverage-sha-in-coverage-doc", coverage_sha in coverage_text, coverage_sha)

for phrase in [
    "source_bindings: tuple[TraceSourceBinding, ...]",
    "NATIVE_REF | HASH_REF",
    "runner 只读取 trace envelope",
    "PAYMENT_CANDIDATE_RECORDED",
    "product-observed authoritative trace = 0/12 VALID",
]:
    check(f"trace-doc-phrase-{phrase[:18]}", phrase in trace_text, phrase)

for phrase in [
    "State: `CONDITIONAL_NOT_FROZEN`",
    "source_bindings = exact minimal projections for those 12 events",
    "TBD_AFTER_ADAPTER_ACCEPTANCE",
    "PAYMENT_CANDIDATE_RECORDED [CURRENT_PAYMENT_CANDIDATE]",
    "本文件保持 `CONDITIONAL_NOT_FROZEN`",
]:
    check(f"next-slice-phrase-{phrase[:18]}", phrase in next_text, phrase)

for phrase in [
    "outcome.authoritative_trace.source_bindings",
    "GateContext",
    "missing binding",
    "duplicate conflicting binding",
    "NATIVE_REF ID/version",
    "HASH_REF canonical hash mismatch",
    "event value 与 source projection mismatch",
    "RESULT projection 含 `authoritative_trace`",
    "product trace 缺失但 evaluator replay 有效",
    "hidden context fallback",
    "product-observed trace = 0/12 VALID",
]:
    check(f"adapter-phrase-{phrase[:18]}", phrase in adapter_text, phrase)

check("current-executing", "state: EXECUTING" in current_text, "state")
check("current-executor", "current_role: Executor" in current_text, "role")
check("current-no-commit", "authorization_commit: false" in current_text, "commit")
check("current-no-push", "authorization_push: false" in current_text, "push")

passed = sum(1 for _, ok, _ in checks if ok)
failed = [(name, detail) for name, ok, detail in checks if not ok]
print(json.dumps({
    "total_checks": len(checks),
    "passed": passed,
    "failed": len(failed),
    "coverage_sha256": coverage_sha,
    "failures": failed,
}, ensure_ascii=False, indent=2))

if failed:
    raise SystemExit(1)

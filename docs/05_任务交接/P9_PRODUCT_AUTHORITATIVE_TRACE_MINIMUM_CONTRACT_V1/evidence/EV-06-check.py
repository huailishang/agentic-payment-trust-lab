from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TASK = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1"
EVIDENCE = TASK / "evidence"

design_path = ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md"
coverage_doc_path = ROOT / "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md"
next_slice_path = TASK / "NEXT_SLICE.md"
coverage_json_path = EVIDENCE / "EV-05-coverage.json"
target_json_path = EVIDENCE / "EV-05-next-slice-target.json"

design = design_path.read_text(encoding="utf-8")
coverage_doc = coverage_doc_path.read_text(encoding="utf-8")
next_slice = next_slice_path.read_text(encoding="utf-8")
coverage = json.loads(coverage_json_path.read_text(encoding="utf-8"))
target = json.loads(target_json_path.read_text(encoding="utf-8"))

required_envelope_fields = {
    "trace_id",
    "schema_version",
    "profile",
    "source",
    "producer_component",
    "completeness_status",
    "events",
    "reason_codes",
    "limitations",
}
required_event_fields = {
    "event_id",
    "sequence_no",
    "event_type",
    "occurred_at",
    "previous_event_ref",
    "producer_component",
    "source_object_type",
    "source_object_ref",
    "authority_ref",
    "order_ref",
    "request_ref",
    "action_ref",
    "payment_ref",
    "policy_ref",
    "lineage_ref",
    "result_ref",
    "decision",
    "status",
    "reason_codes",
}
required_taxonomy = {
    "AUTHORITY_RECORDED",
    "ORDER_RECORDED",
    "REQUEST_RECORDED",
    "ACTION_RECORDED",
    "PREPAYMENT_DECISION_RECORDED",
    "POLICY_DECISION_RECORDED",
    "RUNTIME_DECISION_RECORDED",
    "PAYMENT_ATTEMPT_RECORDED",
    "PAYMENT_OUTCOME_RECORDED",
    "FULFILMENT_OUTCOME_RECORDED",
    "RECOVERY_RECORDED",
    "REFUND_RECORDED",
    "CONFLICT_RECORDED",
    "RESULT_RECORDED",
}

rows = coverage["rows"]
task_ids = [row["task_id"] for row in rows]
checks = {
    "ac01_boundary_definitions": all(
        token in design
        for token in (
            "Product-observed authoritative trace",
            "Evaluator-synthesized replay",
            "禁止伪装情形",
            "runner 在产品返回后补写事件",
            "自由文本 reason",
            "缺少必需事件",
        )
    ),
    "ac02_envelope_fields": all(field in design for field in required_envelope_fields),
    "ac02_event_fields": all(field in design for field in required_event_fields),
    "ac02_primitive_only": "Primitive-only" in design and "null、bool、int、string、list 和 object" in design,
    "ac03_taxonomy": all(event in design for event in required_taxonomy),
    "ac03_fail_closed": all(
        token in design
        for token in ("NOT_AVAILABLE", "INDETERMINATE", "INVALID", "VALID", "不得标记为 VALID")
    ),
    "ac04_twelve_unique_rows": len(rows) == 12 and task_ids == [f"T{i:02d}" for i in range(1, 13)],
    "ac04_all_have_sources": all(row["source_objects"] for row in rows),
    "ac04_all_have_events": all(row["event_candidates"] for row in rows),
    "ac04_all_have_insertion": all(row["insertion_point"] for row in rows),
    "ac04_current_zero_valid": coverage["baseline"] == "0/12 VALID" and all(
        row["current_product_trace_status"] == "NOT_AVAILABLE" for row in rows
    ),
    "ac04_no_new_business_rules": all(not row["new_business_rule_required"] for row in rows),
    "ac04_markdown_covers_all_tasks": all(task_id in coverage_doc for task_id in task_ids),
    "ac05_reuse_not_copy": all(
        token in design
        for token in (
            "复用现有事实，不复制业务规则",
            "轨迹层只做引用与封装",
            "不得重新比较 amount、currency、payee、authority、agent、order、request 或 payment",
        )
    ),
    "ac06_exactly_one_slice": target["slice_task_id"] == "T10" and len(target["excluded_task_ids"]) == 11,
    "ac06_before_frozen": target["source_before"]["product_trace_status"] == "NOT_AVAILABLE",
    "ac06_after_trace_valid": target["expected_after"]["product_trace_status"] == "VALID",
    "ac06_decision_unchanged": target["source_before"]["decision"] == target["expected_after"]["decision"] == "DENY",
    "ac06_callback_unchanged": target["source_before"]["callback_count"] == target["expected_after"]["callback_count"] == 0,
    "ac06_event_sequence_frozen": target["required_event_sequence"] == [
        "AUTHORITY_RECORDED",
        "ORDER_RECORDED",
        "REQUEST_RECORDED",
        "PAYMENT_OUTCOME_RECORDED",
        "ACTION_RECORDED",
        "RUNTIME_DECISION_RECORDED",
        "RESULT_RECORDED",
    ],
    "ac06_next_slice_documented": all(
        token in next_slice
        for token in (
            "NOT_AVAILABLE → VALID",
            "decision = DENY",
            "callback_count = 0",
            "Rollback conditions",
            "非 T10 normalized projection",
        )
    ),
    "ac07_not_applicable_boundary": "本设计任务只冻结合同" in design and "不代表该 capability experiment 已实施" in next_slice,
}

result = {
    "schema": "product-authoritative-trace-design-check/v1",
    "checks": checks,
    "all_pass": all(checks.values()),
    "coverage_rows": len(rows),
    "current_valid": sum(row["current_product_trace_status"] == "VALID" for row in rows),
    "selected_slice": target["slice_task_id"],
    "coverage_sha256": hashlib.sha256(coverage_json_path.read_bytes()).hexdigest(),
    "target_sha256": hashlib.sha256(target_json_path.read_bytes()).hexdigest(),
    "design_sha256": hashlib.sha256(design_path.read_bytes()).hexdigest(),
    "coverage_doc_sha256": hashlib.sha256(coverage_doc_path.read_bytes()).hexdigest(),
    "next_slice_sha256": hashlib.sha256(next_slice_path.read_bytes()).hexdigest(),
}
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
if not result["all_pass"]:
    raise SystemExit(1)

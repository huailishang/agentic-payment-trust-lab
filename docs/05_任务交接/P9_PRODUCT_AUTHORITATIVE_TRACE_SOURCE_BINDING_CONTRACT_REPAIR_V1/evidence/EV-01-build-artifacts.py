from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent

TRACE_DOC = ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md"
COVERAGE_DOC = ROOT / "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md"
NEXT_SLICE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md"
MEASUREMENT_ADAPTER = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md"
COVERAGE_JSON = EVIDENCE / "EV-01-coverage-source-binding.json"
REF_EXAMPLES_JSON = EVIDENCE / "EV-01-ref-examples.json"

FORBIDDEN_PROJECTION_FIELDS = [
    "card_number",
    "pan",
    "cvv",
    "wallet_private_key",
    "credential",
    "token",
    "cookie",
    "raw_page_text",
    "raw_prompt",
    "user_input_fulltext",
    "memory_address",
    "file_path",
    "current_time",
    "random_value",
]

PROJECTIONS: dict[str, dict[str, Any]] = {
    "intent-mandate-trace/v1": {
        "source_object_type": "IntentMandate",
        "ref_mode": "NATIVE_REF",
        "native_id_path": "projection.mandate_id",
        "version_path": "projection.authority_version",
        "fields": ["mandate_id", "authority_version"],
    },
    "order-authorized-snapshot-trace/v1": {
        "source_object_type": "Order",
        "ref_mode": "NATIVE_REF",
        "native_id_path": "projection.order_id",
        "version_path": "projection.order_version",
        "fields": [
            "order_id", "order_version", "mandate_ref", "authority_version_ref",
            "total_amount", "currency", "merchant", "payee",
        ],
    },
    "order-current-snapshot-trace/v1": {
        "source_object_type": "Order",
        "ref_mode": "NATIVE_REF",
        "native_id_path": "projection.order_id",
        "version_path": "projection.order_version",
        "fields": [
            "order_id", "order_version", "mandate_ref", "authority_version_ref",
            "total_amount", "currency", "merchant", "payee",
        ],
    },
    "transaction-request-trace/v1": {
        "source_object_type": "TransactionRequest",
        "ref_mode": "NATIVE_REF",
        "native_id_path": "projection.request_id",
        "version_path": None,
        "fields": [
            "request_id", "order_ref", "authority_ref", "authority_version_ref",
            "amount", "currency", "merchant", "payee", "agent_id",
        ],
    },
    "governed-payment-action-trace/v1": {
        "source_object_type": "GovernedPaymentAction",
        "ref_mode": "NATIVE_REF",
        "native_id_path": "projection.action_id",
        "version_path": None,
        "fields": [
            "action_id", "action_type", "agent_ref", "executor_ref", "authority_ref",
            "authority_version", "order_ref", "order_version", "request_ref",
            "payment_ref", "source_refs", "side_effect_class", "reversibility",
            "occurred_at",
        ],
    },
    "governed-action-binding-fact-trace/v1": {
        "source_object_type": "GovernedActionBindingFact",
        "ref_mode": "HASH_REF",
        "fields": [
            "status", "action_id", "reason_codes", "checked_action_type",
            "checked_order_ref", "checked_request_ref", "checked_payment_ref",
        ],
    },
    "payment-execution-current-candidate-trace/v1": {
        "source_object_type": "PaymentExecutionRecord",
        "ref_mode": "NATIVE_REF",
        "native_id_path": "projection.payment_id",
        "version_path": None,
        "fields": [
            "payment_id", "request_id", "order_id", "status", "amount", "currency",
            "authority_ref", "agent_ref", "transaction_object_ref", "payee",
        ],
    },
    "payment-execution-historical-succeeded-trace/v1": {
        "source_object_type": "PaymentExecutionRecord",
        "ref_mode": "NATIVE_REF",
        "native_id_path": "projection.payment_id",
        "version_path": None,
        "fields": [
            "payment_id", "request_id", "order_id", "status", "amount", "currency",
            "authority_ref", "agent_ref", "transaction_object_ref", "payee",
        ],
    },
    "payment-execution-outcome-trace/v1": {
        "source_object_type": "PaymentExecutionRecord",
        "ref_mode": "NATIVE_REF",
        "native_id_path": "projection.payment_id",
        "version_path": None,
        "fields": [
            "payment_id", "request_id", "order_id", "status", "amount", "currency",
            "authority_ref", "agent_ref", "transaction_object_ref", "payee",
        ],
    },
    "known-payment-attempt-preflight-fact-trace/v1": {
        "source_object_type": "KnownPaymentAttemptPreflightFact",
        "ref_mode": "HASH_REF",
        "fields": [
            "status", "reason_codes", "current_request_ref",
            "related_attempt_refs", "blocking_request_refs",
        ],
    },
    "validation-result-trace/v1": {
        "source_object_type": "ValidationResult",
        "ref_mode": "HASH_REF",
        "fields": [
            "decision", "issue_codes", "evidence_paths", "rule_version",
            "order_difference_paths",
        ],
    },
    "validation-result-duplicate-trace/v1": {
        "source_object_type": "ValidationResult",
        "ref_mode": "HASH_REF",
        "fields": ["decision", "issue_codes", "evidence_paths", "rule_version"],
    },
    "runtime-gate-record-trace/v1": {
        "source_object_type": "RuntimeGateRecord",
        "ref_mode": "HASH_REF",
        "fields": [
            "preliminary_decision", "final_decision", "binding_status",
            "binding_reason_codes", "identity_status", "identity_reason_codes",
            "context_policy_status", "context_policy_reason_codes",
            "callback_executed", "callback_count", "callback_result_ref", "reason_codes",
        ],
    },
    "webshop-buy-now-gate-outcome-result-trace/v1": {
        "source_object_type": "WebShopBuyNowGateOutcome",
        "ref_mode": "HASH_REF",
        "fields": [
            "decision", "checkout_executed", "callback_count", "callback_result_ref",
            "reason_codes", "limitations",
        ],
        "excluded_fields": ["authoritative_trace"],
    },
    "context-policy-fact-trace/v1": {
        "source_object_type": "ContextPolicyFact",
        "ref_mode": "HASH_REF",
        "fields": ["status", "reason_codes", "effective_source_types", "blocked_paths"],
    },
    "fact-lineage-result-trace/v1": {
        "source_object_type": "FactLineageResult",
        "ref_mode": "HASH_REF",
        "fields": ["status", "reason_codes", "effective_source_types", "blocked_paths"],
    },
    "fulfilment-record-trace/v1": {
        "source_object_type": "FulfillmentRecord",
        "ref_mode": "HASH_REF",
        "fields": ["status", "order_id", "reason_codes"],
    },
    "payment-recovery-result-trace/v1": {
        "source_object_type": "PaymentRecoveryResult",
        "ref_mode": "HASH_REF",
        "fields": [
            "initial_status", "observed_status", "effective_status", "recovery_status",
            "next_action", "retry_allowed", "issue_codes", "evidence_paths", "rule_version",
        ],
    },
    "payment-status-conflict-outcome-trace/v1": {
        "source_object_type": "PaymentStatusConflictOutcome",
        "ref_mode": "HASH_REF",
        "fields": ["status", "effective_status", "reason_codes", "retry_allowed"],
    },
    "webshop-payment-fulfilment-outcome-result-trace/v1": {
        "source_object_type": "WebShopPaymentFulfilmentOutcome",
        "ref_mode": "HASH_REF",
        "fields": [
            "decision", "payment_status", "fulfilment_status", "task_status",
            "remediation_status", "retry_allowed", "reason_codes",
        ],
        "excluded_fields": ["authoritative_trace"],
    },
}


def event(
    sequence_no: int,
    event_type: str,
    entity_type: str,
    entity_role: str,
    source_object_type: str,
    projection_schema: str,
    entity_ref_derivation: str,
    *,
    decision_path: str | None = None,
    status_path: str | None = None,
    reason_codes_path: str | None = None,
    relations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    schema = PROJECTIONS[projection_schema]
    return {
        "sequence_no": sequence_no,
        "event_type": event_type,
        "entity_type": entity_type,
        "entity_role": entity_role,
        "entity_ref_derivation": entity_ref_derivation,
        "source_object_type": source_object_type,
        "projection_schema": projection_schema,
        "ref_mode": schema["ref_mode"],
        "source_binding_required": True,
        "value_paths": {
            "decision_path": decision_path,
            "status_path": status_path,
            "reason_codes_path": reason_codes_path,
            "entity_ref_path": entity_ref_derivation,
            "relation_ref_paths": [
                rel.get("target_ref_path") for rel in (relations or [])
            ],
        },
        "relations": relations or [],
    }


def rel(kind: str, target_type: str, target_role: str, target_ref_path: str) -> dict[str, str]:
    return {
        "relation_type": kind,
        "target_entity_type": target_type,
        "target_entity_role": target_role,
        "target_ref_path": target_ref_path,
    }


def common_prefix(two_orders: bool = True) -> list[dict[str, Any]]:
    rows = [
        event(1, "AUTHORITY_RECORDED", "IntentMandate", "AUTHORITY", "IntentMandate", "intent-mandate-trace/v1", "projection.mandate_id+projection.authority_version"),
    ]
    if two_orders:
        rows.extend([
            event(2, "ORDER_RECORDED", "Order", "AUTHORIZED_ORDER_SNAPSHOT", "Order", "order-authorized-snapshot-trace/v1", "projection.order_id+projection.order_version", relations=[rel("BOUND_TO", "IntentMandate", "AUTHORITY", "projection.mandate_ref+projection.authority_version_ref")]),
            event(3, "ORDER_RECORDED", "Order", "CURRENT_ORDER_SNAPSHOT", "Order", "order-current-snapshot-trace/v1", "projection.order_id+projection.order_version", relations=[rel("BOUND_TO", "IntentMandate", "AUTHORITY", "projection.mandate_ref+projection.authority_version_ref")]),
            event(4, "REQUEST_RECORDED", "TransactionRequest", "CURRENT_REQUEST", "TransactionRequest", "transaction-request-trace/v1", "projection.request_id", relations=[rel("BOUND_TO", "Order", "CURRENT_ORDER_SNAPSHOT", "projection.order_ref"), rel("BOUND_TO", "IntentMandate", "AUTHORITY", "projection.authority_ref+projection.authority_version_ref")]),
        ])
    else:
        rows.extend([
            event(2, "ORDER_RECORDED", "Order", "CURRENT_ORDER_SNAPSHOT", "Order", "order-current-snapshot-trace/v1", "projection.order_id+projection.order_version", relations=[rel("BOUND_TO", "IntentMandate", "AUTHORITY", "projection.mandate_ref+projection.authority_version_ref")]),
            event(3, "REQUEST_RECORDED", "TransactionRequest", "CURRENT_REQUEST", "TransactionRequest", "transaction-request-trace/v1", "projection.request_id", relations=[rel("BOUND_TO", "Order", "CURRENT_ORDER_SNAPSHOT", "projection.order_ref"), rel("BOUND_TO", "IntentMandate", "AUTHORITY", "projection.authority_ref+projection.authority_version_ref")]),
        ])
    return rows


def resequence(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for i, row in enumerate(rows, 1):
        row["sequence_no"] = i
    return rows


def task(task_id: str, title: str, profile: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = resequence(rows)
    return {
        "task_id": task_id,
        "title": title,
        "profile": profile,
        "current_status": "NOT_AVAILABLE",
        "new_business_rule_required": False,
        "entity_roles": [row["entity_role"] for row in rows],
        "events": rows,
    }


# T01
T01 = common_prefix(True)
T01 += [
    event(5, "ACTION_RECORDED", "GovernedPaymentAction", "GOVERNED_ACTION", "GovernedPaymentAction", "governed-payment-action-trace/v1", "projection.action_id", relations=[rel("BOUND_TO", "TransactionRequest", "CURRENT_REQUEST", "projection.request_ref"), rel("BOUND_TO", "Order", "CURRENT_ORDER_SNAPSHOT", "projection.order_ref"), rel("BOUND_TO", "IntentMandate", "AUTHORITY", "projection.authority_ref+projection.authority_version"), rel("BOUND_TO", "PaymentExecutionRecord", "CURRENT_PAYMENT_CANDIDATE", "projection.payment_ref")]),
    event(6, "PAYMENT_CANDIDATE_RECORDED", "PaymentExecutionRecord", "CURRENT_PAYMENT_CANDIDATE", "PaymentExecutionRecord", "payment-execution-current-candidate-trace/v1", "projection.payment_id", status_path="projection.status", relations=[rel("BOUND_TO", "TransactionRequest", "CURRENT_REQUEST", "projection.request_id"), rel("BOUND_TO", "Order", "CURRENT_ORDER_SNAPSHOT", "projection.order_id")]),
    event(7, "ACTION_BINDING_DECISION_RECORDED", "GovernedActionBindingFact", "ACTION_BINDING_FACT", "GovernedActionBindingFact", "governed-action-binding-fact-trace/v1", "source_object_ref", status_path="projection.status", reason_codes_path="projection.reason_codes"),
    event(8, "RUNTIME_DECISION_RECORDED", "RuntimeGateRecord", "RUNTIME_GATE_OBSERVATION", "RuntimeGateRecord", "runtime-gate-record-trace/v1", "source_object_ref", decision_path="projection.final_decision", status_path="projection.binding_status", reason_codes_path="projection.reason_codes"),
    event(9, "PAYMENT_OUTCOME_RECORDED", "PaymentExecutionRecord", "PAYMENT_EXECUTION_OUTCOME", "PaymentExecutionRecord", "payment-execution-outcome-trace/v1", "projection.payment_id", status_path="projection.status"),
    event(10, "FULFILMENT_OUTCOME_RECORDED", "FulfillmentRecord", "FULFILMENT_OUTCOME", "FulfillmentRecord", "fulfilment-record-trace/v1", "source_object_ref", status_path="projection.status", reason_codes_path="projection.reason_codes"),
    event(11, "RESULT_RECORDED", "WebShopPaymentFulfilmentOutcome", "FINAL_OUTCOME", "WebShopPaymentFulfilmentOutcome", "webshop-payment-fulfilment-outcome-result-trace/v1", "source_object_ref", decision_path="projection.decision", status_path="projection.task_status", reason_codes_path="projection.reason_codes"),
]


def prepayment_task(task_id: str, title: str) -> dict[str, Any]:
    rows = common_prefix(True)
    rows += [
        event(5, "PREPAYMENT_DECISION_RECORDED", "ValidationResult", "PREPAYMENT_VALIDATION", "ValidationResult", "validation-result-trace/v1", "source_object_ref", decision_path="projection.decision", reason_codes_path="projection.issue_codes"),
        event(6, "RESULT_RECORDED", "WebShopBuyNowGateOutcome", "FINAL_OUTCOME", "WebShopBuyNowGateOutcome", "webshop-buy-now-gate-outcome-result-trace/v1", "source_object_ref", decision_path="projection.decision", reason_codes_path="projection.reason_codes"),
    ]
    return task(task_id, title, f"WEBSHOP_PREPAYMENT_{task_id}_V1", rows)


def action_binding_task(task_id: str, title: str) -> dict[str, Any]:
    rows = common_prefix(True)
    rows += [
        event(5, "PREPAYMENT_DECISION_RECORDED", "ValidationResult", "PREPAYMENT_VALIDATION", "ValidationResult", "validation-result-trace/v1", "source_object_ref", decision_path="projection.decision", reason_codes_path="projection.issue_codes"),
        event(6, "ACTION_RECORDED", "GovernedPaymentAction", "GOVERNED_ACTION", "GovernedPaymentAction", "governed-payment-action-trace/v1", "projection.action_id", relations=[rel("BOUND_TO", "TransactionRequest", "CURRENT_REQUEST", "projection.request_ref")]),
        event(7, "ACTION_BINDING_DECISION_RECORDED", "GovernedActionBindingFact", "ACTION_BINDING_FACT", "GovernedActionBindingFact", "governed-action-binding-fact-trace/v1", "source_object_ref", status_path="projection.status", reason_codes_path="projection.reason_codes"),
        event(8, "RESULT_RECORDED", "WebShopBuyNowGateOutcome", "FINAL_OUTCOME", "WebShopBuyNowGateOutcome", "webshop-buy-now-gate-outcome-result-trace/v1", "source_object_ref", decision_path="projection.decision", reason_codes_path="projection.reason_codes"),
    ]
    return task(task_id, title, f"WEBSHOP_ACTION_BINDING_{task_id}_V1", rows)


def policy_task(task_id: str, title: str) -> dict[str, Any]:
    rows = common_prefix(False)
    rows += [
        event(4, "POLICY_DECISION_RECORDED", "ContextPolicyFact", "CONTEXT_POLICY_FACT", "ContextPolicyFact", "context-policy-fact-trace/v1", "source_object_ref", status_path="projection.status", reason_codes_path="projection.reason_codes"),
        event(5, "LINEAGE_DECISION_RECORDED", "FactLineageResult", "FACT_LINEAGE_RESULT", "FactLineageResult", "fact-lineage-result-trace/v1", "source_object_ref", status_path="projection.status", reason_codes_path="projection.reason_codes"),
        event(6, "RESULT_RECORDED", "WebShopPaymentFulfilmentOutcome", "FINAL_OUTCOME", "WebShopPaymentFulfilmentOutcome", "webshop-payment-fulfilment-outcome-result-trace/v1", "source_object_ref", decision_path="projection.decision", status_path="projection.task_status", reason_codes_path="projection.reason_codes"),
    ]
    return task(task_id, title, f"WEBSHOP_POLICY_LINEAGE_{task_id}_V1", rows)


def runtime_base() -> list[dict[str, Any]]:
    rows = common_prefix(False)
    rows += [
        event(4, "ACTION_RECORDED", "GovernedPaymentAction", "GOVERNED_ACTION", "GovernedPaymentAction", "governed-payment-action-trace/v1", "projection.action_id", relations=[rel("BOUND_TO", "TransactionRequest", "CURRENT_REQUEST", "projection.request_ref"), rel("BOUND_TO", "PaymentExecutionRecord", "CURRENT_PAYMENT_CANDIDATE", "projection.payment_ref")]),
        event(5, "PAYMENT_CANDIDATE_RECORDED", "PaymentExecutionRecord", "CURRENT_PAYMENT_CANDIDATE", "PaymentExecutionRecord", "payment-execution-current-candidate-trace/v1", "projection.payment_id", status_path="projection.status"),
        event(6, "ACTION_BINDING_DECISION_RECORDED", "GovernedActionBindingFact", "ACTION_BINDING_FACT", "GovernedActionBindingFact", "governed-action-binding-fact-trace/v1", "source_object_ref", status_path="projection.status", reason_codes_path="projection.reason_codes"),
        event(7, "RUNTIME_DECISION_RECORDED", "RuntimeGateRecord", "RUNTIME_GATE_OBSERVATION", "RuntimeGateRecord", "runtime-gate-record-trace/v1", "source_object_ref", decision_path="projection.final_decision", status_path="projection.binding_status", reason_codes_path="projection.reason_codes"),
        event(8, "PAYMENT_OUTCOME_RECORDED", "PaymentExecutionRecord", "PAYMENT_EXECUTION_OUTCOME", "PaymentExecutionRecord", "payment-execution-outcome-trace/v1", "projection.payment_id", status_path="projection.status"),
    ]
    return rows

T09 = runtime_base() + [
    event(9, "RECOVERY_OUTCOME_RECORDED", "PaymentRecoveryResult", "RECOVERY_OUTCOME", "PaymentRecoveryResult", "payment-recovery-result-trace/v1", "source_object_ref", status_path="projection.recovery_status", reason_codes_path="projection.issue_codes"),
    event(10, "RESULT_RECORDED", "WebShopPaymentFulfilmentOutcome", "FINAL_OUTCOME", "WebShopPaymentFulfilmentOutcome", "webshop-payment-fulfilment-outcome-result-trace/v1", "source_object_ref", decision_path="projection.decision", status_path="projection.task_status", reason_codes_path="projection.reason_codes"),
]

T10 = common_prefix(True) + [
    event(5, "ACTION_RECORDED", "GovernedPaymentAction", "GOVERNED_ACTION", "GovernedPaymentAction", "governed-payment-action-trace/v1", "projection.action_id", relations=[rel("BOUND_TO", "IntentMandate", "AUTHORITY", "projection.authority_ref+projection.authority_version"), rel("BOUND_TO", "Order", "CURRENT_ORDER_SNAPSHOT", "projection.order_ref+projection.order_version"), rel("BOUND_TO", "TransactionRequest", "CURRENT_REQUEST", "projection.request_ref"), rel("BOUND_TO", "PaymentExecutionRecord", "CURRENT_PAYMENT_CANDIDATE", "projection.payment_ref")]),
    event(6, "PAYMENT_CANDIDATE_RECORDED", "PaymentExecutionRecord", "CURRENT_PAYMENT_CANDIDATE", "PaymentExecutionRecord", "payment-execution-current-candidate-trace/v1", "projection.payment_id", status_path="projection.status", relations=[rel("BOUND_TO", "TransactionRequest", "CURRENT_REQUEST", "projection.request_id"), rel("BOUND_TO", "Order", "CURRENT_ORDER_SNAPSHOT", "projection.order_id")]),
    event(7, "ACTION_BINDING_DECISION_RECORDED", "GovernedActionBindingFact", "ACTION_BINDING_FACT", "GovernedActionBindingFact", "governed-action-binding-fact-trace/v1", "source_object_ref", status_path="projection.status", reason_codes_path="projection.reason_codes", relations=[rel("VALIDATED_AGAINST", "GovernedPaymentAction", "GOVERNED_ACTION", "projection.action_id"), rel("VALIDATED_AGAINST", "PaymentExecutionRecord", "CURRENT_PAYMENT_CANDIDATE", "projection.checked_payment_ref")]),
    event(8, "PAYMENT_OUTCOME_RECORDED", "PaymentExecutionRecord", "HISTORICAL_SUCCEEDED_PAYMENT", "PaymentExecutionRecord", "payment-execution-historical-succeeded-trace/v1", "projection.payment_id", status_path="projection.status", relations=[rel("BOUND_TO", "TransactionRequest", "CURRENT_REQUEST", "projection.request_id"), rel("BOUND_TO", "Order", "CURRENT_ORDER_SNAPSHOT", "projection.order_id")]),
    event(9, "KNOWN_PAYMENT_PREFLIGHT_RECORDED", "KnownPaymentAttemptPreflightFact", "KNOWN_PAYMENT_PREFLIGHT_FACT", "KnownPaymentAttemptPreflightFact", "known-payment-attempt-preflight-fact-trace/v1", "source_object_ref", status_path="projection.status", reason_codes_path="projection.reason_codes", relations=[rel("VALIDATED_AGAINST", "TransactionRequest", "CURRENT_REQUEST", "projection.current_request_ref"), rel("MEMBER_OF", "PaymentExecutionRecord", "HISTORICAL_SUCCEEDED_PAYMENT", "projection.related_attempt_refs[]")]),
    event(10, "PREPAYMENT_DECISION_RECORDED", "ValidationResult", "PREPAYMENT_VALIDATION", "ValidationResult", "validation-result-duplicate-trace/v1", "source_object_ref", decision_path="projection.decision", reason_codes_path="projection.issue_codes"),
    event(11, "RUNTIME_DECISION_RECORDED", "RuntimeGateRecord", "RUNTIME_GATE_OBSERVATION", "RuntimeGateRecord", "runtime-gate-record-trace/v1", "source_object_ref", decision_path="projection.final_decision", status_path="projection.binding_status", reason_codes_path="projection.reason_codes"),
    event(12, "RESULT_RECORDED", "WebShopBuyNowGateOutcome", "FINAL_OUTCOME", "WebShopBuyNowGateOutcome", "webshop-buy-now-gate-outcome-result-trace/v1", "source_object_ref", decision_path="projection.decision", reason_codes_path="projection.reason_codes"),
]

T11 = runtime_base() + [
    event(9, "FULFILMENT_OUTCOME_RECORDED", "FulfillmentRecord", "FULFILMENT_OUTCOME", "FulfillmentRecord", "fulfilment-record-trace/v1", "source_object_ref", status_path="projection.status", reason_codes_path="projection.reason_codes"),
    event(10, "RECOVERY_OUTCOME_RECORDED", "PaymentRecoveryResult", "RECOVERY_OUTCOME", "PaymentRecoveryResult", "payment-recovery-result-trace/v1", "source_object_ref", status_path="projection.recovery_status", reason_codes_path="projection.issue_codes"),
    event(11, "RESULT_RECORDED", "WebShopPaymentFulfilmentOutcome", "FINAL_OUTCOME", "WebShopPaymentFulfilmentOutcome", "webshop-payment-fulfilment-outcome-result-trace/v1", "source_object_ref", decision_path="projection.decision", status_path="projection.task_status", reason_codes_path="projection.reason_codes"),
]

T12 = runtime_base() + [
    event(9, "STATUS_CONFLICT_RECORDED", "PaymentStatusConflictOutcome", "STATUS_CONFLICT_OUTCOME", "PaymentStatusConflictOutcome", "payment-status-conflict-outcome-trace/v1", "source_object_ref", status_path="projection.status", reason_codes_path="projection.reason_codes"),
    event(10, "RESULT_RECORDED", "WebShopPaymentFulfilmentOutcome", "FINAL_OUTCOME", "WebShopPaymentFulfilmentOutcome", "webshop-payment-fulfilment-outcome-result-trace/v1", "source_object_ref", decision_path="projection.decision", status_path="projection.task_status", reason_codes_path="projection.reason_codes"),
]

TASKS = [
    task("T01", "正常购买", "WEBSHOP_NORMAL_PURCHASE_V1", T01),
    prepayment_task("T02", "价格上涨需确认"),
    prepayment_task("T03", "价格下降需确认"),
    prepayment_task("T04", "收款方变化证据不足"),
    action_binding_task("T05", "Action Agent 不匹配"),
    action_binding_task("T06", "Action ID 缺失"),
    policy_task("T07", "低可信金额覆盖被阻断"),
    policy_task("T08", "低可信收款方覆盖被阻断"),
    task("T09", "UNKNOWN 支付状态恢复", "WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V1", T09),
    task("T10", "重复付款预检阻断", "WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V1", T10),
    task("T11", "付款成功但履约失败", "WEBSHOP_FULFILMENT_FAILURE_V1", T11),
    task("T12", "终态冲突", "WEBSHOP_PAYMENT_STATUS_CONFLICT_V1", T12),
]

COVERAGE = {
    "schema_version": "product-authoritative-trace-coverage/v2",
    "generated_for_task": "P9-PRODUCT-AUTHORITATIVE-TRACE-SOURCE-BINDING-CONTRACT-REPAIR-V1",
    "current_product_observed_valid": "0/12",
    "gesr": "0/12",
    "source_binding_contract": {
        "binding_fields": [
            "source_object_type", "source_object_ref", "projection_schema",
            "ref_mode", "projection",
        ],
        "event_binding_rule": "each event source_object_ref resolves to exactly one canonical binding",
        "hidden_resolver_allowed": False,
        "evaluator_reconstruction_allowed": False,
    },
    "projection_registry": PROJECTIONS,
    "forbidden_projection_fields": FORBIDDEN_PROJECTION_FIELDS,
    "tasks": TASKS,
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def hash_ref(source_type: str, schema: str, projection: dict[str, Any]) -> str:
    payload = {"projection_schema": schema, "projection": projection}
    return f"{source_type}:sha256:{hashlib.sha256(canonical_bytes(payload)).hexdigest()}"


def write_json(path: Path, value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


coverage_sha = write_json(COVERAGE_JSON, COVERAGE)

binding_projection = {
    "status": "VALID",
    "action_id": "action-1",
    "reason_codes": [],
    "checked_action_type": "execute_payment",
    "checked_order_ref": "order-1",
    "checked_request_ref": "request-1",
    "checked_payment_ref": "payment-current-1",
}
outcome_projection = {
    "decision": "DENY",
    "checkout_executed": False,
    "callback_count": 0,
    "callback_result_ref": None,
    "reason_codes": [
        "p1:duplicate_request",
        "preflight:known_payment_attempt_duplicate_succeeded",
    ],
    "limitations": ["offline_interception_only", "no_real_buy_now_execution"],
}
REF_EXAMPLES = {
    "canonical_json": "UTF-8; object keys sorted; separators ',' ':'; Enum=.value; datetime=native ISO-8601; tuple=array",
    "native_ref": {
        "source_object_type": "IntentMandate",
        "projection_schema": "intent-mandate-trace/v1",
        "projection": {"mandate_id": "mandate-1", "authority_version": "v1"},
        "expected_source_object_ref": "IntentMandate:mandate-1:v1",
    },
    "hash_ref": {
        "source_object_type": "GovernedActionBindingFact",
        "projection_schema": "governed-action-binding-fact-trace/v1",
        "projection": binding_projection,
        "expected_source_object_ref": hash_ref(
            "GovernedActionBindingFact",
            "governed-action-binding-fact-trace/v1",
            binding_projection,
        ),
    },
    "result_cycle_closed": {
        "source_object_type": "WebShopBuyNowGateOutcome",
        "projection_schema": "webshop-buy-now-gate-outcome-result-trace/v1",
        "projection": outcome_projection,
        "excluded_field": "authoritative_trace",
        "expected_source_object_ref": hash_ref(
            "WebShopBuyNowGateOutcome",
            "webshop-buy-now-gate-outcome-result-trace/v1",
            outcome_projection,
        ),
    },
}
ref_sha = write_json(REF_EXAMPLES_JSON, REF_EXAMPLES)


def t10_matrix_markdown() -> str:
    t10 = next(item for item in TASKS if item["task_id"] == "T10")
    lines = [
        "| # | event_type | entity_type / role | source / schema | value paths | relations |",
        "|---:|---|---|---|---|---|",
    ]
    for row in t10["events"]:
        paths = row["value_paths"]
        path_text = "; ".join(
            f"{key.removesuffix('_path')}={value}"
            for key, value in paths.items()
            if value not in (None, [], "")
        ) or "—"
        relation_text = "; ".join(
            f"{r['relation_type']}→{r['target_entity_role']}@{r['target_ref_path']}"
            for r in row["relations"]
        ) or "—"
        lines.append(
            f"| {row['sequence_no']} | `{row['event_type']}` | `{row['entity_type']}` / `{row['entity_role']}` | "
            f"`{row['source_object_type']}` / `{row['projection_schema']}` | `{path_text}` | `{relation_text}` |"
        )
    return "\n".join(lines)


def projection_table_markdown() -> str:
    required = [
        "intent-mandate-trace/v1",
        "order-authorized-snapshot-trace/v1",
        "order-current-snapshot-trace/v1",
        "transaction-request-trace/v1",
        "governed-payment-action-trace/v1",
        "governed-action-binding-fact-trace/v1",
        "payment-execution-current-candidate-trace/v1",
        "payment-execution-historical-succeeded-trace/v1",
        "known-payment-attempt-preflight-fact-trace/v1",
        "validation-result-duplicate-trace/v1",
        "runtime-gate-record-trace/v1",
        "webshop-buy-now-gate-outcome-result-trace/v1",
    ]
    lines = [
        "| projection_schema | source type | ref | 字段数 | exact fields |",
        "|---|---|---|---:|---|",
    ]
    for name in required:
        spec = PROJECTIONS[name]
        fields = ", ".join(f"`{field}`" for field in spec["fields"])
        lines.append(
            f"| `{name}` | `{spec['source_object_type']}` | `{spec['ref_mode']}` | {len(spec['fields'])} | {fields} |"
        )
    return "\n".join(lines)


TRACE_TEXT = f"""# 产品权威轨迹最小合同 v1

## 1. 核心结论

产品权威轨迹是产品在本次真实本地调用链中，把已经生成的 Authority、Order、Request、Action、Decision、Payment、Policy、Lineage 和 Result 事实按统一合同输出。它不是 runner 或评估者事后拼装的 Replay，也不得重新运行业务规则。

当前基线保持：

```text
product-observed authoritative trace = 0/12 VALID
GESR = 0/12
```

落地分两步：

```text
阶段 A：measurement adapter maintenance
runner 支持读取并严格校验 envelope + source_bindings
产品仍不产出 trace，重新冻结 0/12 BEFORE

阶段 B：T10 capability experiment
使用阶段 A 已接受 runner，只增加 T10 产品 trace
```

## 2. 来源边界

`PRODUCT_OBSERVED` 必须同时满足：

1. 轨迹由产品调用路径在返回 outcome 前生成；
2. outcome 直接暴露 `authoritative_trace`；
3. 事件和 source binding 只来自本次调用已经存在的不可变对象或事实；
4. runner 只读取 trace envelope，不读取隐藏 `GateContext`、mandate、order、action、execution 或 evaluator replay；
5. runner 不补事件、不补 binding、不重跑支付或授权判断。

```text
evaluator-synthesized replay ≠ product-observed trace
```

## 3. Envelope 与 Source Binding

```text
ProductAuthoritativeTrace
- schema_version: product-authoritative-trace/v1
- source: PRODUCT_OBSERVED
- profile: closed profile name
- trace_ref: stable technical ref
- completeness_status: VALID | INVALID | INDETERMINATE
- reason_codes: tuple[str, ...]
- events: tuple[ProductTraceEvent, ...]
- source_bindings: tuple[TraceSourceBinding, ...]

TraceSourceBinding
- source_object_type: closed type name
- source_object_ref: stable ref
- projection_schema: closed schema name
- ref_mode: NATIVE_REF | HASH_REF
- projection: primitive-only exact allowlist object
```

关闭规则：

1. 每个 `ProductTraceEvent.source_object_ref` 恰好解析到一个 canonical binding；
2. 同一 ref 的重复 binding 若 canonical bytes 不同，判 `INVALID`；若完全相同，生产者必须去重，validator 可先归一为一个；
3. 未被任何事件引用的 binding 判 `INVALID`；
4. 事件缺 binding、schema 未知或必要字段缺失判 `INDETERMINATE`；
5. binding 出现额外字段、字段类型错误、ref 重算不一致或事件值与 projection 不一致判 `INVALID`；
6. 不允许 `source_registry_ref` 空指针式替代，不允许外部 resolver、evaluator 重建或隐藏参数补全；
7. runner 只依赖 envelope 自身即可完成结构、ref、值路径和 relation 校验。

## 4. Event 与路径核对

```text
ProductTraceEvent
- sequence_no: int, from 1, continuous
- event_type: closed enum
- entity_type: closed enum
- entity_role: closed enum
- entity_ref: stable ref
- source_object_type: closed type name
- source_object_ref: stable ref
- relations: tuple[TraceRelation, ...]
- decision: closed Decision | null
- status: closed status string | null
- reason_codes: tuple[str, ...]
- native_occurred_at: ISO-8601 | null
```

每个 profile 行必须冻结：

```text
entity_ref_path
decision_path
status_path
reason_codes_path
relation_ref_paths
```

路径相对于对应 `TraceSourceBinding.projection`。路径不存在或必填值缺失为 `INDETERMINATE`；事件值、entity ref 或 relation target 与 projection 不一致为 `INVALID`。validator 只做字段核对，不重跑业务规则。

## 5. Ref 重算

### 5.1 NATIVE_REF

每个 schema 冻结 `native_id_path` 和可选 `version_path`：

```text
<source_object_type>:<native-id>[:<version>]
```

ID 缺失、空白、非字符串或 version 类型错误时为 `INDETERMINATE`；生成结果与 `source_object_ref` 不一致时为 `INVALID`。

### 5.2 HASH_REF

```text
<source_object_type>:sha256(
  canonical-json({{
    "projection_schema": "<closed schema>",
    "projection": <exact primitive projection>
  }})
)
```

canonical JSON：UTF-8、key 字典序、无多余空格、Enum 使用 `.value`、datetime 使用源对象原生 ISO-8601、tuple 转 array；禁止当前时间、随机值、内存地址和文件路径。schema 或 projection 任一变化都会改变 ref。

### 5.3 RESULT 循环关闭

RESULT 的 outcome projection 明确排除 `authoritative_trace`：

```text
outcome → projection excluding authoritative_trace → HASH_REF
```

因此 trace 不进入自己的 ref 输入。示例与固定 SHA：

- `{REF_EXAMPLES_JSON.relative_to(ROOT).as_posix()}`
- SHA-256 `{ref_sha}`

## 6. 最小披露 Projection Registry

T10 至少使用以下 exact allowlist：

{projection_table_markdown()}

所有 schema 共同禁止：

```text
卡号/PAN/CVV、支付工具明文、钱包私钥、credential、token、cookie、
原始页面文本、原始 prompt、任意用户输入全文、当前时间、内存地址、文件路径、随机值
```

未声明字段不允许进入 projection。Payment projection 特意排除 `receipt_ref`、`provider_ref` 和 `idempotency_key`；ValidationResult 只保留 decision、issue code、evidence field path 和 rule version，不保留自由文本 message 或任意 observed 全文。

## 7. 关闭 taxonomy 与角色

事件 taxonomy 增加：

```text
PAYMENT_CANDIDATE_RECORDED
```

完整主集合：

```text
AUTHORITY_RECORDED
ORDER_RECORDED
REQUEST_RECORDED
ACTION_RECORDED
PAYMENT_CANDIDATE_RECORDED
PREPAYMENT_DECISION_RECORDED
ACTION_BINDING_DECISION_RECORDED
KNOWN_PAYMENT_PREFLIGHT_RECORDED
RUNTIME_DECISION_RECORDED
PAYMENT_OUTCOME_RECORDED
POLICY_DECISION_RECORDED
LINEAGE_DECISION_RECORDED
FULFILMENT_OUTCOME_RECORDED
RECOVERY_OUTCOME_RECORDED
STATUS_CONFLICT_RECORDED
RESULT_RECORDED
```

一致性键为 `(entity_type, entity_role)`。同一键的 ref 必须一致；不同角色可以合法引用同类的不同对象。

## 8. T10 exact 12-event profile

Profile：`WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V1`。

{t10_matrix_markdown()}

关键绑定：

```text
GovernedPaymentAction.payment_ref
= CURRENT_PAYMENT_CANDIDATE PaymentExecutionRecord.payment_id

HISTORICAL_SUCCEEDED_PAYMENT.payment_id
∈ KnownPaymentAttemptPreflightFact.related_attempt_refs

KnownPaymentAttemptPreflightFact.current_request_ref
= CURRENT_REQUEST.request_id

AUTHORIZED_ORDER_SNAPSHOT 与 CURRENT_ORDER_SNAPSHOT 都必须出现；
它们可引用相同 order_id，但由 order_version / entity_role 区分。
```

`ACTION_RECORDED` 只表示 `GovernedPaymentAction / GOVERNED_ACTION`；`PAYMENT_CANDIDATE_RECORDED` 只表示 `PaymentExecutionRecord / CURRENT_PAYMENT_CANDIDATE`，不再使用斜杠混写。

## 9. VALID / INVALID / INDETERMINATE

`VALID` 必须同时满足：

1. `source=PRODUCT_OBSERVED`；
2. schema/profile 已知；
3. sequence 从 1 连续；
4. profile 事件、角色和顺序完全相等；
5. 每个事件恰好有一个 source binding；
6. projection 只含 exact allowlist 字段；
7. NATIVE_REF/HASH_REF 可重算；
8. event decision/status/reason/entity/relation 与 projection 路径一致；
9. relation target 在 profile 中存在且 role/ref 一致；
10. RESULT ref 排除 trace 自身。

```text
缺事件、缺 binding、缺字段、路径不存在 → INDETERMINATE
矛盾 ref、错误顺序、额外字段、值不一致、冲突 binding、伪造来源 → INVALID
产品未暴露 authoritative_trace → NOT_AVAILABLE（runner 外层状态）
```

任何失败都不得用 evaluator replay 回退成 `VALID`。

## 10. 不复制业务规则

轨迹层只能序列化现有对象、生成技术 ref、校验 profile 和核对字段。金额、payee、授权、Agent/Executor、重复付款、Context/Lineage、重试、退款或履约结论必须来自现有产品 facts/outcomes。

## 11. 结构化证据

- T01—T12 coverage：`{COVERAGE_JSON.relative_to(ROOT).as_posix()}`
- Coverage SHA-256：`{coverage_sha}`
- Ref examples：`{REF_EXAMPLES_JSON.relative_to(ROOT).as_posix()}`
- 当前 product-observed trace：`0/12 VALID`

## 12. 阶段化落地

```text
本设计修复
→ measurement adapter maintenance
→ Evaluator 接受新 runner 与 0/12 BEFORE
→ 条件解锁 T10 capability experiment
→ T10 NOT_AVAILABLE → VALID
```

本文件不实现类型、validator、runner 或产品 outcome。
"""


COVERAGE_TEXT = f"""# 产品权威轨迹 12 项覆盖映射 v1

## 1. 当前结论

固定任务 T01—T12 当前都没有产品 outcome 直接携带统一 `ProductAuthoritativeTrace`：

```text
product-observed authoritative trace = 0/12 VALID
GESR = 0/12
```

结构化映射：

- `{COVERAGE_JSON.relative_to(ROOT).as_posix()}`
- SHA-256：`{coverage_sha}`
- Schema：`product-authoritative-trace-coverage/v2`

## 2. 统一口径

每个事件都显式记录：

```text
sequence_no
event_type
entity_type / entity_role
entity_ref_derivation
source_object_type
projection_schema
ref_mode
source_binding_required
decision/status/reason/entity/relation value paths
relations
```

`entity_roles` 必须与事件序列实际角色逐项相等。每个事件必须引用 envelope 内唯一 source binding；不得使用隐藏 `GateContext`、evaluator replay 或临时 resolver。

## 3. 12 项概览

| Task | Profile | 事件数 | 当前状态 | 直接最终解释 |
|---|---|---:|---|---|
""" + "\n".join(
    f"| {item['task_id']} | `{item['profile']}` | {len(item['events'])} | `NOT_AVAILABLE` | "
    f"`{next((e['event_type'] for e in reversed(item['events']) if e['value_paths']['decision_path']), 'RESULT_RECORDED')}` |"
    for item in TASKS
) + f"""

## 4. T10 exact matrix

{t10_matrix_markdown()}

T10 的关闭序列为：

```text
1  AUTHORITY_RECORDED [AUTHORITY]
2  ORDER_RECORDED [AUTHORIZED_ORDER_SNAPSHOT]
3  ORDER_RECORDED [CURRENT_ORDER_SNAPSHOT]
4  REQUEST_RECORDED [CURRENT_REQUEST]
5  ACTION_RECORDED [GOVERNED_ACTION]
6  PAYMENT_CANDIDATE_RECORDED [CURRENT_PAYMENT_CANDIDATE]
7  ACTION_BINDING_DECISION_RECORDED [ACTION_BINDING_FACT]
8  PAYMENT_OUTCOME_RECORDED [HISTORICAL_SUCCEEDED_PAYMENT]
9  KNOWN_PAYMENT_PREFLIGHT_RECORDED [KNOWN_PAYMENT_PREFLIGHT_FACT]
10 PREPAYMENT_DECISION_RECORDED [PREPAYMENT_VALIDATION]
11 RUNTIME_DECISION_RECORDED [RUNTIME_GATE_OBSERVATION]
12 RESULT_RECORDED [FINAL_OUTCOME]
```

Action 与当前付款候选不再共用一条事件；两者分别有独立事件、独立 entity role、独立 source binding。

## 5. T01—T12 角色与 source binding

结构化 JSON 已冻结全部事件；以下规则由机器校验：

1. 恰好 T01—T12；
2. 每项 `entity_roles == [event.entity_role ...]`；
3. 每个事件都有 source object、projection schema、ref mode 和完整 value-path 键；
4. projection schema 必须存在于 registry；
5. 每个任务 `current_status=NOT_AVAILABLE`；
6. 每个任务 `new_business_rule_required=false`；
7. T10 恰好 12 个事件，顺序与角色严格相等；
8. 所有 projection 都是 primitive-only exact allowlist；
9. RESULT schema 排除 `authoritative_trace`；
10. forbidden projection fields 不得进入任一 allowlist。

## 6. 最小披露

T10 所需 12 类 projection 的字段数和 exact fields 见《产品权威轨迹最小合同 v1》。结构化 registry 还覆盖 T01—T12 的 Policy、Lineage、Recovery、Fulfilment 和 Conflict 事件。

未声明字段全部拒绝；不携带卡号、支付工具、钱包密钥、credential、token、cookie、原始网页、原始 prompt 或任意用户输入全文。

## 7. 阶段边界

```text
阶段 A：runner + strict validator 读取 envelope/source_bindings
产品仍不产出 trace → 0/12 BEFORE 不变

阶段 B：同一 accepted runner，只增加 T10 产品 trace
```

本映射只冻结设计，不修改产品、runner、测试、fixture 或当前指标。
"""


NEXT_TEXT = """# Next Capability Slice — Conditional Freeze

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-T10-DUPLICATE-PREFLIGHT-SLICE-V1`  
Task kind: `capability_experiment`  
State: `CONDITIONAL_NOT_FROZEN`  
Project map revision: `2026-08-04-r5`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Slice task: `T10`  
Trace profile: `WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V1`

## 1. 前置条件

```text
prerequisite = measurement adapter accepted
runner hash = TBD_AFTER_ADAPTER_ACCEPTANCE
before hash = TBD_AFTER_ADAPTER_ACCEPTANCE
target hash = TBD_AFTER_ADAPTER_ACCEPTANCE
non-trace projection hash = TBD_AFTER_ADAPTER_ACCEPTANCE
state = CONDITIONAL_NOT_FROZEN
```

在 Evaluator 独立接受阶段 A 的 runner 和重新冻结的 `0/12 VALID` BEFORE 前：

- 不创建本任务 `CONTRACT.md`；
- 不进入 `CONTRACT_FROZEN`；
- 不修改 T10 产品 outcome；
- 旧 runner hash 只能作为阶段 A 输入，不能作为阶段 B accepted runner。

## 2. 单一产品变量

前置条件满足后，仅允许在 `gate_webshop_buy_now` known-payment duplicate preflight `BLOCKED` 返回中，让 `WebShopBuyNowGateOutcome` 直接携带：

```text
ProductAuthoritativeTrace
source = PRODUCT_OBSERVED
profile = WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V1
events = exact 12-event sequence
source_bindings = exact minimal projections for those 12 events
```

`source_bindings` 是 T10 产品变量的组成部分，不是 runner 的隐藏输入。不得同时修改 runner、validator 或项目指标。

## 3. BEFORE / AFTER

```text
BEFORE: T10 product_trace_status = NOT_AVAILABLE
AFTER:  T10 product_trace_status = VALID
```

以下业务投影必须不变：

```text
decision = DENY
callback_count = 0
known_payment_attempt_preflight_status = BLOCKED
duplicate_payment_blocked = true
retry_allowed = false
trusted_state_changed = false
```

## 4. Exact 12-event sequence

```text
1  AUTHORITY_RECORDED [AUTHORITY]
2  ORDER_RECORDED [AUTHORIZED_ORDER_SNAPSHOT]
3  ORDER_RECORDED [CURRENT_ORDER_SNAPSHOT]
4  REQUEST_RECORDED [CURRENT_REQUEST]
5  ACTION_RECORDED [GOVERNED_ACTION]
6  PAYMENT_CANDIDATE_RECORDED [CURRENT_PAYMENT_CANDIDATE]
7  ACTION_BINDING_DECISION_RECORDED [ACTION_BINDING_FACT]
8  PAYMENT_OUTCOME_RECORDED [HISTORICAL_SUCCEEDED_PAYMENT]
9  KNOWN_PAYMENT_PREFLIGHT_RECORDED [KNOWN_PAYMENT_PREFLIGHT_FACT]
10 PREPAYMENT_DECISION_RECORDED [PREPAYMENT_VALIDATION]
11 RUNTIME_DECISION_RECORDED [RUNTIME_GATE_OBSERVATION]
12 RESULT_RECORDED [FINAL_OUTCOME]
```

Action 与当前付款候选必须分别序列化，不得斜杠混写。

## 5. Source binding 与最小披露

每个事件的 `source_object_ref` 必须解析到 trace 内唯一 `TraceSourceBinding`。T10 product variable 必须同时生成：

- NATIVE_REF：Mandate、两个 Order 快照、Request、Action、当前候选 Payment、历史成功 Payment；
- HASH_REF：ActionBindingFact、KnownPaymentAttemptPreflightFact、duplicate ValidationResult、RuntimeGateRecord、RESULT outcome；
- RESULT projection 必须排除 `authoritative_trace`；
- projection 只含冻结 allowlist，不输出完整对象、卡号、支付工具、credential、token、cookie、原始页面或 prompt。

## 6. 双 Payment 关系

```text
GovernedPaymentAction.payment_ref
= CURRENT_PAYMENT_CANDIDATE.payment_id

HISTORICAL_SUCCEEDED_PAYMENT.payment_id
∈ KnownPaymentAttemptPreflightFact.related_attempt_refs

KnownPaymentAttemptPreflightFact.current_request_ref
= CURRENT_REQUEST.request_id
```

两个 Payment ref 允许不同，一致性按 `(PaymentExecutionRecord, entity_role)` 分别校验。

## 7. 守护线

```text
重复或禁止副作用 = 0/12
callback match = 12/12
false refusal = 0/6
missed confirmation = 0/2
forbidden state write = 0/2
formal entry = 13/13
full tests >= 阶段 A accepted baseline
其余 11 项非 trace 业务投影 hash 完全不变
```

## 8. 回滚条件

- runner/validator 不等于阶段 A accepted hash；
- decision、callback、状态、binding 或 side effect 变化；
- source binding 依赖隐藏 context 或 evaluator replay；
- T10 事件数、顺序或角色不等于 exact 12；
- Action 与当前 Payment 再次混为一个事件；
- 两个 Payment 角色错误合并；
- RESULT ref 包含 trace 自身；
- projection 泄露未声明字段；
- 其余 11 项业务投影变化；
- 需要网络、真实支付、WebShop runtime 或外部副作用。

## 9. 当前裁定

本文件保持 `CONDITIONAL_NOT_FROZEN`，不构成执行合同。下一步必须先由 Evaluator 冻结并接受独立 measurement-adapter 任务。
"""


MEASUREMENT_TEXT = """# Measurement Adapter Freeze

Task name: 产品权威轨迹测量适配  
Task kind: `maintenance`  
Project impact verdict: `NOT_APPLICABLE`  
Prerequisite: source-binding 设计修复被 Evaluator 接受

## 1. 单一目标

只让项目级测量层读取并严格校验 `ProductAuthoritativeTrace` envelope 及 envelope 内 `source_bindings`；产品 outcome 继续不产出 trace，重新冻结可信的 `0/12 VALID` BEFORE 和新 runner hash。

```text
runner reads exact outcome.authoritative_trace
→ validates envelope/events/source_bindings/profile
→ does not receive hidden source objects
→ absent trace remains NOT_AVAILABLE
→ evaluator replay never becomes fallback
```

## 2. 允许的主要变量

- 增加纯数据类型：`ProductAuthoritativeTrace`、`ProductTraceEvent`、`TraceSourceBinding`、closed enums；
- runner 读取 exact `outcome.authoritative_trace`；
- strict validator 校验 sequence、profile、role、source binding、ref、value path、relation；
- 增加正反例测试；
- 用同一 T01—T12 target 重新输出新 runner hash 和 0/12 BEFORE。

## 3. Hidden resolver 禁止

runner 和 validator 不得接收或偷读以下对象作为 source resolver：

```text
GateContext
IntentMandate
Order / authorized_adaptation
TransactionRequest
GovernedPaymentAction
PaymentExecutionRecord / known_payment_attempts
RuntimeGateRecord
测试 fixture 原对象
evaluator-synthesized replay
```

唯一 source resolver 是 `outcome.authoritative_trace.source_bindings`。如果 envelope 不自包含，必须 fail closed。

## 4. Strict validator 必测反例

以下必须不能得到 `VALID`：

1. missing binding；
2. duplicate conflicting binding；
3. duplicate identical binding 未归一；
4. unreferenced binding；
5. unknown projection schema；
6. NATIVE_REF ID/version 缺失或 ref mismatch；
7. HASH_REF canonical hash mismatch；
8. projection 出现 extra field；
9. projection 缺 required field；
10. forbidden/sensitive field；
11. decision/status/reason/entity path 缺失；
12. event value 与 source projection mismatch；
13. relation target/path mismatch；
14. RESULT projection 含 `authoritative_trace` 或发生循环；
15. product trace 缺失但 evaluator replay 有效；
16. hidden context fallback。

## 5. BEFORE 必须保持

```text
product-observed trace = 0/12 VALID
GESR = 0/12
重复或禁止副作用 = 0/12
callback match = 12/12
决策—理由一致 = 12/12
```

同时冻结 accepted runner、target、BEFORE output、non-trace projection SHA-256，以及 full regression/formal entry 结果。

## 6. 原子验收点

### MA-AC-01 — exact envelope
runner 只读取 `outcome.authoritative_trace`；不存在返回 `NOT_AVAILABLE`。

### MA-AC-02 — self-contained bindings
每个事件 ref 只通过 envelope 内 binding 解析和重算，不接收隐藏对象。

### MA-AC-03 — exact allowlist
projection schema 是关闭 registry；extra/missing/forbidden 字段 fail closed。

### MA-AC-04 — ref recomputation
NATIVE_REF 与 HASH_REF 只依赖 binding projection 重算；RESULT 排除 trace。

### MA-AC-05 — value paths
validator 核对 decision/status/reason/entity/relation 路径，不重跑业务规则。

### MA-AC-06 — no fallback
产品 trace 缺失时，即使 evaluator replay 为 VALID，结果仍为 `NOT_AVAILABLE`。

### MA-AC-07 — zero product producers
所有产品 outcome 仍没有产生非空 `authoritative_trace`。

### MA-AC-08 — same 12-task baseline
同一 target 运行后仍为 0/12，其他项目指标和业务投影不变。

### MA-AC-09 — accepted hashes
Executor 报告 hashes；Evaluator 独立复跑后接受。

## 7. 明确禁止

- 任一产品 outcome 开始产出 trace；
- 修改 T01—T12 fixture 业务预期；
- 修改决策、callback、状态、binding 或 side effect；
- 同时实现 T10 产品 trace；
- 创建 T10 capability contract；
- 宣称项目 `IMPROVED`；
- 依赖网络、环境创建或新依赖。

## 8. 对阶段 B 的交付

只有 Evaluator 接受阶段 A 后，才提供：

```text
accepted_runner_hash
accepted_target_hash
accepted_before_hash
accepted_non_trace_projection_hash
```

这些值替换 `NEXT_SLICE.md` 中的 `TBD_AFTER_ADAPTER_ACCEPTANCE`。本文件只定义后续冻结条件，不是正式 `CONTRACT.md`。
"""

for path, text in [
    (TRACE_DOC, TRACE_TEXT),
    (COVERAGE_DOC, COVERAGE_TEXT),
    (NEXT_SLICE, NEXT_TEXT),
    (MEASUREMENT_ADAPTER, MEASUREMENT_TEXT),
]:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")

print(json.dumps({
    "written": [
        str(TRACE_DOC.relative_to(ROOT)),
        str(COVERAGE_DOC.relative_to(ROOT)),
        str(NEXT_SLICE.relative_to(ROOT)),
        str(MEASUREMENT_ADAPTER.relative_to(ROOT)),
        str(COVERAGE_JSON.relative_to(ROOT)),
        str(REF_EXAMPLES_JSON.relative_to(ROOT)),
    ],
    "coverage_sha256": coverage_sha,
    "ref_examples_sha256": ref_sha,
    "tasks": len(TASKS),
    "t10_events": len(next(item for item in TASKS if item["task_id"] == "T10")["events"]),
}, ensure_ascii=False, indent=2))

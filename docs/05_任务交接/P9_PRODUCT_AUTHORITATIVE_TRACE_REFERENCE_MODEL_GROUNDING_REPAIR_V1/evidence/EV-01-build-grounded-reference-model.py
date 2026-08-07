from __future__ import annotations

import ast
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent

TRACE_DOC = ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md"
COVERAGE_DOC = ROOT / "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md"
NEXT_SLICE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md"
MEASUREMENT_ADAPTER = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md"

COVERAGE_JSON = EVIDENCE / "EV-01-coverage-reference-grounding.json"
REF_EXAMPLES_JSON = EVIDENCE / "EV-01-reference-examples.json"
SOURCE_MANIFEST_JSON = EVIDENCE / "EV-01-source-grounding-manifest.json"
T10_INSTANCE_JSON = EVIDENCE / "EV-01-t10-grounded-instance.json"
T12_EXAMPLES_JSON = EVIDENCE / "EV-01-t12-sidecar-examples.json"

TASK_ID = "P9-PRODUCT-AUTHORITATIVE-TRACE-REFERENCE-MODEL-GROUNDING-REPAIR-V1"

FORBIDDEN_PROJECTION_FIELDS = [
    "card_number",
    "pan",
    "cvv",
    "payment_instrument_plaintext",
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


def fx(path: str, transform: str = "DIRECT") -> dict[str, str]:
    return {"path": path, "transform": transform}


def registry_entry(
    source_module: str,
    source_class: str,
    field_extractions: dict[str, dict[str, str]],
    *,
    source_identity_mode: str,
    source_identity_template: str | None,
    entity_ref_template: str,
    excluded_fields: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "source_module": source_module,
        "source_class": source_class,
        "source_object_type": source_class,
        "source_identity": {
            "mode": source_identity_mode,
            "template": source_identity_template,
        },
        "binding_ref_mode": "EXACT_PROJECTION_DIGEST",
        "entity_ref_template": entity_ref_template,
        "projection_fields": list(field_extractions),
        "field_extractions": field_extractions,
        "excluded_fields": excluded_fields or [],
    }


REGISTRY: dict[str, dict[str, Any]] = {
    "intent-mandate-trace/v2": registry_entry(
        "agentic_payment_experiment.models",
        "IntentMandate",
        {
            "mandate_id": fx("mandate_id"),
            "authority_version": fx("authority_version"),
        },
        source_identity_mode="NATIVE_TEMPLATE",
        source_identity_template="IntentMandate:{mandate_id}:{authority_version}",
        entity_ref_template="IntentMandate:{projection.mandate_id}",
    ),
    "order-snapshot-trace/v2": registry_entry(
        "agentic_payment_experiment.models",
        "Order",
        {
            "order_id": fx("order_id"),
            "order_version": fx("order_version"),
            "mandate_ref": fx("mandate_ref"),
            "authority_version_ref": fx("authority_version_ref"),
            "total_amount": fx("total_amount", "Decimal.canonical_string"),
            "currency": fx("currency"),
            "merchant": fx("merchant"),
            "payee": fx("payee"),
        },
        source_identity_mode="NATIVE_TEMPLATE",
        source_identity_template="Order:{order_id}:{order_version}",
        entity_ref_template="Order:{projection.order_id}",
    ),
    "transaction-request-trace/v2": registry_entry(
        "agentic_payment_experiment.models",
        "TransactionRequest",
        {
            "request_id": fx("request_id"),
            "order_ref": fx("order_ref"),
            "authority_ref": fx("authority_ref"),
            "authority_version_ref": fx("authority_version_ref"),
            "amount": fx("amount", "Decimal.canonical_string"),
            "currency": fx("currency"),
            "merchant": fx("merchant"),
            "payee": fx("payee"),
            "agent_id": fx("agent_id"),
        },
        source_identity_mode="NATIVE_TEMPLATE",
        source_identity_template="TransactionRequest:{request_id}",
        entity_ref_template="TransactionRequest:{projection.request_id}",
    ),
    "governed-payment-action-trace/v2": registry_entry(
        "agentic_payment_experiment.trusted_execution.governed_action",
        "GovernedPaymentAction",
        {
            "action_id": fx("action_id"),
            "action_type": fx("action_type", "Enum.value"),
            "agent_ref": fx("agent_ref"),
            "executor_ref": fx("executor_ref"),
            "authority_ref": fx("authority_ref"),
            "authority_version": fx("authority_version"),
            "order_ref": fx("order_ref"),
            "order_version": fx("order_version"),
            "request_ref": fx("request_ref"),
            "payment_ref": fx("payment_ref"),
            "source_refs": fx("source_refs", "tuple.to_list"),
            "side_effect_class": fx("side_effect_class", "Enum.value"),
            "reversibility": fx("reversibility", "Enum.value"),
            "occurred_at": fx("occurred_at", "datetime.isoformat"),
        },
        source_identity_mode="NATIVE_TEMPLATE",
        source_identity_template="GovernedPaymentAction:{action_id}",
        entity_ref_template="GovernedPaymentAction:{projection.action_id}",
    ),
    "governed-payment-action-missing-id-trace/v2": registry_entry(
        "agentic_payment_experiment.trusted_execution.governed_action",
        "GovernedPaymentAction",
        {
            "action_id": fx("action_id"),
            "action_type": fx("action_type", "Enum.value"),
            "agent_ref": fx("agent_ref"),
            "executor_ref": fx("executor_ref"),
            "authority_ref": fx("authority_ref"),
            "authority_version": fx("authority_version"),
            "order_ref": fx("order_ref"),
            "order_version": fx("order_version"),
            "request_ref": fx("request_ref"),
            "payment_ref": fx("payment_ref"),
            "source_refs": fx("source_refs", "tuple.to_list"),
            "side_effect_class": fx("side_effect_class", "Enum.value"),
            "reversibility": fx("reversibility", "Enum.value"),
            "occurred_at": fx("occurred_at", "datetime.isoformat"),
        },
        source_identity_mode="PROJECTION_HASH_IDENTITY",
        source_identity_template=None,
        entity_ref_template="GovernedPaymentAction:binding:{binding_digest}",
    ),
    "governed-action-binding-fact-trace/v2": registry_entry(
        "agentic_payment_experiment.trusted_execution.governed_action",
        "GovernedActionBindingFact",
        {
            "status": fx("status", "Enum.value"),
            "action_id": fx("action_id"),
            "reason_codes": fx("reason_codes", "tuple.to_list"),
            "checked_action_type": fx("checked_action_type"),
            "checked_order_ref": fx("checked_order_ref"),
            "checked_request_ref": fx("checked_request_ref"),
            "checked_payment_ref": fx("checked_payment_ref"),
        },
        source_identity_mode="PROJECTION_HASH_IDENTITY",
        source_identity_template=None,
        entity_ref_template="GovernedActionBindingFact:binding:{binding_digest}",
    ),
    "payment-execution-record-trace/v2": registry_entry(
        "agentic_payment_experiment.models",
        "PaymentExecutionRecord",
        {
            "payment_id": fx("payment_id"),
            "request_id": fx("request_id"),
            "order_id": fx("order_id"),
            "status": fx("status", "Enum.value"),
            "amount": fx("amount", "Decimal.canonical_string"),
            "currency": fx("currency"),
            "authority_ref": fx("authority_ref"),
            "agent_ref": fx("agent_ref"),
            "transaction_object_ref": fx("transaction_object_ref"),
            "payee": fx("payee"),
        },
        source_identity_mode="NATIVE_TEMPLATE",
        source_identity_template="PaymentExecutionRecord:{payment_id}",
        entity_ref_template="PaymentExecutionRecord:{projection.payment_id}",
    ),
    "known-payment-attempt-preflight-fact-trace/v2": registry_entry(
        "agentic_payment_experiment.trusted_execution.known_payment_attempt",
        "KnownPaymentAttemptPreflightFact",
        {
            "status": fx("status", "Enum.value"),
            "reason_codes": fx("reason_codes", "tuple.to_list"),
            "current_request_ref": fx("current_request_ref"),
            "related_attempt_refs": fx("related_attempt_refs", "tuple.to_list"),
            "blocking_request_refs": fx("blocking_request_refs", "tuple.to_list"),
            "limitations": fx("limitations", "tuple.to_list"),
        },
        source_identity_mode="PROJECTION_HASH_IDENTITY",
        source_identity_template=None,
        entity_ref_template="KnownPaymentAttemptPreflightFact:binding:{binding_digest}",
    ),
    "validation-result-trace/v2": registry_entry(
        "agentic_payment_experiment.models",
        "ValidationResult",
        {
            "decision": fx("decision", "Enum.value"),
            "issue_codes": fx("issues[].code", "tuple.map"),
            "evidence_paths": fx("evidence[].field_path", "tuple.map"),
            "rule_version": fx("rule_version"),
            "order_difference_paths": fx("order_differences[].field_path", "tuple.map"),
        },
        source_identity_mode="PROJECTION_HASH_IDENTITY",
        source_identity_template=None,
        entity_ref_template="ValidationResult:binding:{binding_digest}",
    ),
    "runtime-gate-record-trace/v2": registry_entry(
        "agentic_payment_experiment.trusted_execution.replay",
        "RuntimeGateRecord",
        {
            "preliminary_decision": fx("preliminary_decision", "Enum.value"),
            "final_decision": fx("final_decision", "Enum.value"),
            "binding_status": fx("binding_status"),
            "binding_reason_codes": fx("binding_reason_codes", "tuple.to_list"),
            "identity_status": fx("identity_status"),
            "identity_reason_codes": fx("identity_reason_codes", "tuple.to_list"),
            "context_policy_status": fx("context_policy_status"),
            "context_policy_reason_codes": fx("context_policy_reason_codes", "tuple.to_list"),
            "callback_executed": fx("callback_executed"),
            "callback_count": fx("callback_count"),
            "callback_result_ref": fx("callback_result_ref"),
            "reason_codes": fx("reason_codes", "tuple.to_list"),
        },
        source_identity_mode="PROJECTION_HASH_IDENTITY",
        source_identity_template=None,
        entity_ref_template="RuntimeGateRecord:binding:{binding_digest}",
    ),
    "webshop-buy-now-gate-outcome-result-trace/v2": registry_entry(
        "agentic_payment_experiment.webshop_runtime_gate",
        "WebShopBuyNowGateOutcome",
        {
            "decision": fx("decision", "Enum.value"),
            "checkout_executed": fx("checkout_executed"),
            "callback_count": fx("callback_count"),
            "callback_result_ref": fx("callback_result_ref"),
            "reason_codes": fx("reason_codes", "tuple.to_list"),
            "limitations": fx("limitations", "tuple.to_list"),
        },
        source_identity_mode="PROJECTION_HASH_IDENTITY",
        source_identity_template=None,
        entity_ref_template="WebShopBuyNowGateOutcome:binding:{binding_digest}",
        excluded_fields=["authoritative_trace"],
    ),
    "attack-overlay-result-trace/v2": registry_entry(
        "agentic_payment_experiment.attack_overlay",
        "AttackOverlayResult",
        {
            "attack_id": fx("attack_id"),
            "source_type": fx("source_type", "Enum.value"),
            "baseline_decision": fx("baseline_decision", "Enum.value"),
            "defended_decision": fx("defended_decision", "Enum.value"),
            "attack_attempted": fx("attack_attempted"),
            "applied_paths": fx("applied_paths", "tuple.to_list"),
            "blocked_override_paths": fx("blocked_override_paths", "tuple.to_list"),
            "trusted_state_changed": fx("trusted_state_changed"),
            "reason_codes": fx("reason_codes", "tuple.to_list"),
            "policy_version": fx("policy_version"),
            "decision_drift": fx("decision_drift"),
            "lineage_status": fx("lineage_status", "Enum.value"),
            "lineage_reason_codes": fx("lineage_reason_codes", "tuple.to_list"),
            "lineage_fact_refs": fx("lineage_facts[].fact_ref", "tuple.map"),
            "lineage_effective_source_types": fx("lineage_facts[].effective_source_types[]", "tuple.flatten_enum_values"),
        },
        source_identity_mode="NATIVE_TEMPLATE",
        source_identity_template="AttackOverlayResult:{attack_id}",
        entity_ref_template="AttackOverlayResult:{projection.attack_id}",
    ),
    "fulfillment-record-trace/v2": registry_entry(
        "agentic_payment_experiment.models",
        "FulfillmentRecord",
        {
            "fulfillment_id": fx("fulfillment_id"),
            "order_id": fx("order_id"),
            "status": fx("status", "Enum.value"),
            "failure_code": fx("failure_code"),
            "reason_codes": fx("failure_code", "optional.singleton_tuple"),
        },
        source_identity_mode="NATIVE_TEMPLATE",
        source_identity_template="FulfillmentRecord:{fulfillment_id}",
        entity_ref_template="FulfillmentRecord:{projection.fulfillment_id}",
    ),
    "payment-recovery-result-trace/v2": registry_entry(
        "agentic_payment_experiment.models",
        "PaymentRecoveryResult",
        {
            "initial_status": fx("initial_status", "Enum.value"),
            "observed_status": fx("observed_status", "Enum.value"),
            "effective_status": fx("effective_status", "Enum.value"),
            "recovery_status": fx("recovery_status", "Enum.value"),
            "next_action": fx("next_action"),
            "retry_allowed": fx("retry_allowed"),
            "issue_codes": fx("issues[].code", "tuple.map"),
            "evidence_paths": fx("evidence[].field_path", "tuple.map"),
            "rule_version": fx("rule_version"),
        },
        source_identity_mode="PROJECTION_HASH_IDENTITY",
        source_identity_template=None,
        entity_ref_template="PaymentRecoveryResult:binding:{binding_digest}",
    ),
    "payment-status-conflict-fact-trace/v2": registry_entry(
        "agentic_payment_experiment.payment_status_conflict",
        "PaymentStatusConflictFact",
        {
            "resolution": fx("resolution", "Enum.value"),
            "initial_status": fx("initial_status", "Enum.value"),
            "query_status": fx("query_status", "Enum.value"),
            "query_observed_at": fx("query_observed_at", "datetime.isoformat_or_null"),
            "async_status": fx("async_status", "Enum.value"),
            "async_observed_at": fx("async_observed_at", "datetime.isoformat_or_null"),
            "effective_status": fx("effective_status", "Enum.value"),
            "effective_status_terminal": fx("effective_status_terminal"),
            "reason_codes": fx("reason_codes", "tuple.to_list"),
            "business_success_confirmed": fx("business_success_confirmed"),
            "fulfillment_confirmed": fx("fulfillment_confirmed"),
            "user_task_success_confirmed": fx("user_task_success_confirmed"),
            "reconciliation_confirmed": fx("reconciliation_confirmed"),
            "settlement_confirmed": fx("settlement_confirmed"),
            "legal_finality_confirmed": fx("legal_finality_confirmed"),
        },
        source_identity_mode="PROJECTION_HASH_IDENTITY",
        source_identity_template=None,
        entity_ref_template="PaymentStatusConflictFact:binding:{binding_digest}",
    ),
    "webshop-payment-fulfilment-outcome-result-trace/v2": registry_entry(
        "agentic_payment_experiment.webshop_payment_sidecar",
        "WebShopPaymentFulfilmentOutcome",
        {
            "ready": fx("ready"),
            "initial_payment_status": fx("initial_payment.status", "Enum.value_or_null"),
            "effective_payment_status": fx("effective_payment.status", "Enum.value_or_null"),
            "query_recovery_status": fx("query_recovery.recovery_status", "Enum.value_or_null"),
            "status_conflict_resolution": fx("status_conflict.resolution", "Enum.value_or_null"),
            "lifecycle_payment_status": fx("lifecycle.payment_status", "Enum.value_or_null"),
            "lifecycle_fulfillment_status": fx("lifecycle.fulfillment_status", "Enum.value_or_null"),
            "lifecycle_task_status": fx("lifecycle.task_status", "Enum.value_or_null"),
            "lifecycle_remediation_status": fx("lifecycle.remediation.status", "Enum.value_or_null"),
            "retry_allowed": fx("retry_allowed"),
            "duplicate_payment_blocked": fx("duplicate_payment_blocked"),
            "reason_codes": fx("reason_codes", "tuple.to_list"),
            "limitations": fx("limitations", "tuple.to_list"),
        },
        source_identity_mode="PROJECTION_HASH_IDENTITY",
        source_identity_template=None,
        entity_ref_template="WebShopPaymentFulfilmentOutcome:binding:{binding_digest}",
        excluded_fields=["authoritative_trace"],
    ),
}


def relation(
    relation_type: str,
    target_entity_type: str,
    target_entity_role: str,
    source_assertion_path: str,
    target_entity_ref_template: str,
    *,
    value_mode: str = "SCALAR",
    target_binding_assertions: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "relation_type": relation_type,
        "target_entity_type": target_entity_type,
        "target_entity_role": target_entity_role,
        "source_assertion_path": source_assertion_path,
        "target_entity_ref_template": target_entity_ref_template,
        "value_mode": value_mode,
        "target_binding_assertions": target_binding_assertions or [],
    }


def event(
    sequence_no: int,
    event_type: str,
    entity_type: str,
    entity_role: str,
    projection_schema: str,
    *,
    entity_ref_template: str | None = None,
    decision_path: str | None = None,
    status_path: str | None = None,
    reason_codes_path: str | None = None,
    relations: list[dict[str, Any]] | None = None,
    binding_alias_group: str | None = None,
) -> dict[str, Any]:
    spec = REGISTRY[projection_schema]
    return {
        "sequence_no": sequence_no,
        "event_type": event_type,
        "entity_type": entity_type,
        "entity_role": entity_role,
        "entity_ref_template": entity_ref_template or spec["entity_ref_template"],
        "source_object_type": spec["source_object_type"],
        "source_module": spec["source_module"],
        "source_class": spec["source_class"],
        "projection_schema": projection_schema,
        "source_object_ref_mode": spec["source_identity"]["mode"],
        "source_binding_ref_required": True,
        "binding_alias_group": binding_alias_group,
        "value_paths": {
            "decision_path": decision_path,
            "status_path": status_path,
            "reason_codes_path": reason_codes_path,
        },
        "relations": relations or [],
    }


def authority_event(seq: int = 1) -> dict[str, Any]:
    return event(seq, "AUTHORITY_RECORDED", "IntentMandate", "AUTHORITY", "intent-mandate-trace/v2")


def order_event(seq: int, role: str, *, alias: str | None = None) -> dict[str, Any]:
    return event(
        seq,
        "ORDER_RECORDED",
        "Order",
        role,
        "order-snapshot-trace/v2",
        relations=[
            relation(
                "BOUND_TO",
                "IntentMandate",
                "AUTHORITY",
                "projection.mandate_ref",
                "IntentMandate:{value}",
                target_binding_assertions=[
                    {
                        "source_path": "projection.authority_version_ref",
                        "target_path": "projection.authority_version",
                    }
                ],
            )
        ],
        binding_alias_group=alias,
    )


def request_event(seq: int) -> dict[str, Any]:
    return event(
        seq,
        "REQUEST_RECORDED",
        "TransactionRequest",
        "CURRENT_REQUEST",
        "transaction-request-trace/v2",
        relations=[
            relation("BOUND_TO", "Order", "CURRENT_ORDER_SNAPSHOT", "projection.order_ref", "Order:{value}"),
            relation(
                "BOUND_TO",
                "IntentMandate",
                "AUTHORITY",
                "projection.authority_ref",
                "IntentMandate:{value}",
                target_binding_assertions=[
                    {
                        "source_path": "projection.authority_version_ref",
                        "target_path": "projection.authority_version",
                    }
                ],
            ),
        ],
    )


def common_prefix(two_orders: bool = True, *, shared_order: bool = False) -> list[dict[str, Any]]:
    rows = [authority_event(1)]
    alias = "AUTHORIZED_CURRENT_ORDER_SHARED_BINDING" if shared_order else None
    if two_orders:
        rows.extend(
            [
                order_event(2, "AUTHORIZED_ORDER_SNAPSHOT", alias=alias),
                order_event(3, "CURRENT_ORDER_SNAPSHOT", alias=alias),
                request_event(4),
            ]
        )
    else:
        rows.extend([order_event(2, "CURRENT_ORDER_SNAPSHOT"), request_event(3)])
    return rows


def action_event(seq: int, *, missing_id: bool = False) -> dict[str, Any]:
    schema = "governed-payment-action-missing-id-trace/v2" if missing_id else "governed-payment-action-trace/v2"
    return event(
        seq,
        "ACTION_RECORDED",
        "GovernedPaymentAction",
        "GOVERNED_ACTION",
        schema,
        relations=[
            relation(
                "BOUND_TO",
                "IntentMandate",
                "AUTHORITY",
                "projection.authority_ref",
                "IntentMandate:{value}",
                target_binding_assertions=[
                    {
                        "source_path": "projection.authority_version",
                        "target_path": "projection.authority_version",
                    }
                ],
            ),
            relation(
                "BOUND_TO",
                "Order",
                "CURRENT_ORDER_SNAPSHOT",
                "projection.order_ref",
                "Order:{value}",
                target_binding_assertions=[
                    {
                        "source_path": "projection.order_version",
                        "target_path": "projection.order_version",
                    }
                ],
            ),
            relation("BOUND_TO", "TransactionRequest", "CURRENT_REQUEST", "projection.request_ref", "TransactionRequest:{value}"),
            relation("BOUND_TO", "PaymentExecutionRecord", "CURRENT_PAYMENT_CANDIDATE", "projection.payment_ref", "PaymentExecutionRecord:{value}"),
        ],
    )


def payment_event(seq: int, role: str, event_type: str = "PAYMENT_CANDIDATE_RECORDED") -> dict[str, Any]:
    return event(
        seq,
        event_type,
        "PaymentExecutionRecord",
        role,
        "payment-execution-record-trace/v2",
        status_path="projection.status",
        relations=[
            relation("BOUND_TO", "TransactionRequest", "CURRENT_REQUEST", "projection.request_id", "TransactionRequest:{value}"),
            relation("BOUND_TO", "Order", "CURRENT_ORDER_SNAPSHOT", "projection.order_id", "Order:{value}"),
        ],
    )


def action_binding_event(seq: int, *, include_action_relation: bool = True) -> dict[str, Any]:
    relations = [
        relation("VALIDATED_AGAINST", "PaymentExecutionRecord", "CURRENT_PAYMENT_CANDIDATE", "projection.checked_payment_ref", "PaymentExecutionRecord:{value}"),
    ]
    if include_action_relation:
        relations.insert(
            0,
            relation("VALIDATED_AGAINST", "GovernedPaymentAction", "GOVERNED_ACTION", "projection.action_id", "GovernedPaymentAction:{value}"),
        )
    return event(
        seq,
        "ACTION_BINDING_DECISION_RECORDED",
        "GovernedActionBindingFact",
        "ACTION_BINDING_FACT",
        "governed-action-binding-fact-trace/v2",
        status_path="projection.status",
        reason_codes_path="projection.reason_codes",
        relations=relations,
    )


def validation_event(seq: int) -> dict[str, Any]:
    return event(
        seq,
        "PREPAYMENT_DECISION_RECORDED",
        "ValidationResult",
        "PREPAYMENT_VALIDATION",
        "validation-result-trace/v2",
        decision_path="projection.decision",
        reason_codes_path="projection.issue_codes",
    )


def runtime_event(seq: int) -> dict[str, Any]:
    return event(
        seq,
        "RUNTIME_DECISION_RECORDED",
        "RuntimeGateRecord",
        "RUNTIME_GATE_OBSERVATION",
        "runtime-gate-record-trace/v2",
        decision_path="projection.final_decision",
        status_path="projection.binding_status",
        reason_codes_path="projection.reason_codes",
    )


def gate_result_event(seq: int) -> dict[str, Any]:
    return event(
        seq,
        "RESULT_RECORDED",
        "WebShopBuyNowGateOutcome",
        "FINAL_OUTCOME",
        "webshop-buy-now-gate-outcome-result-trace/v2",
        decision_path="projection.decision",
        reason_codes_path="projection.reason_codes",
    )


def sidecar_result_event(seq: int) -> dict[str, Any]:
    return event(
        seq,
        "RESULT_RECORDED",
        "WebShopPaymentFulfilmentOutcome",
        "FINAL_OUTCOME",
        "webshop-payment-fulfilment-outcome-result-trace/v2",
        status_path="projection.lifecycle_task_status",
        reason_codes_path="projection.reason_codes",
    )


def resequence(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for idx, row in enumerate(rows, 1):
        row["sequence_no"] = idx
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


T01 = common_prefix(True, shared_order=True) + [
    action_event(5),
    payment_event(6, "CURRENT_PAYMENT_CANDIDATE"),
    action_binding_event(7),
    runtime_event(8),
    payment_event(9, "PAYMENT_EXECUTION_OUTCOME", "PAYMENT_OUTCOME_RECORDED"),
    event(
        10,
        "FULFILMENT_OUTCOME_RECORDED",
        "FulfillmentRecord",
        "FULFILMENT_OUTCOME",
        "fulfillment-record-trace/v2",
        status_path="projection.status",
        reason_codes_path="projection.reason_codes",
        relations=[relation("BOUND_TO", "Order", "CURRENT_ORDER_SNAPSHOT", "projection.order_id", "Order:{value}")],
    ),
    sidecar_result_event(11),
]


def prepayment_task(task_id: str, title: str) -> dict[str, Any]:
    rows = common_prefix(True) + [validation_event(5), gate_result_event(6)]
    return task(task_id, title, f"WEBSHOP_PREPAYMENT_{task_id}_V2", rows)


def action_binding_task(task_id: str, title: str, *, missing_id: bool = False) -> dict[str, Any]:
    rows = common_prefix(True, shared_order=True) + [
        validation_event(5),
        action_event(6, missing_id=missing_id),
        payment_event(7, "CURRENT_PAYMENT_CANDIDATE"),
        action_binding_event(8, include_action_relation=not missing_id),
        gate_result_event(9),
    ]
    return task(task_id, title, f"WEBSHOP_ACTION_BINDING_{task_id}_V2", rows)


def overlay_task(task_id: str, title: str) -> dict[str, Any]:
    rows = [
        event(
            1,
            "POLICY_DECISION_RECORDED",
            "AttackOverlayResult",
            "ATTACK_POLICY_RESULT",
            "attack-overlay-result-trace/v2",
            decision_path="projection.defended_decision",
            reason_codes_path="projection.reason_codes",
        ),
        event(
            2,
            "LINEAGE_DECISION_RECORDED",
            "AttackOverlayResult",
            "ATTACK_LINEAGE_RESULT",
            "attack-overlay-result-trace/v2",
            status_path="projection.lineage_status",
            reason_codes_path="projection.lineage_reason_codes",
        ),
        event(
            3,
            "RESULT_RECORDED",
            "AttackOverlayResult",
            "FINAL_OUTCOME",
            "attack-overlay-result-trace/v2",
            decision_path="projection.defended_decision",
            reason_codes_path="projection.reason_codes",
        ),
    ]
    return task(task_id, title, f"ATTACK_OVERLAY_{task_id}_V2", rows)


def runtime_base() -> list[dict[str, Any]]:
    return common_prefix(True, shared_order=True) + [
        action_event(5),
        payment_event(6, "CURRENT_PAYMENT_CANDIDATE"),
        action_binding_event(7),
        runtime_event(8),
        payment_event(9, "PAYMENT_EXECUTION_OUTCOME", "PAYMENT_OUTCOME_RECORDED"),
    ]


T09 = runtime_base() + [
    event(
        10,
        "RECOVERY_OUTCOME_RECORDED",
        "PaymentRecoveryResult",
        "RECOVERY_OUTCOME",
        "payment-recovery-result-trace/v2",
        status_path="projection.recovery_status",
        reason_codes_path="projection.issue_codes",
    ),
    sidecar_result_event(11),
]

T10 = common_prefix(True, shared_order=True) + [
    action_event(5),
    payment_event(6, "CURRENT_PAYMENT_CANDIDATE"),
    action_binding_event(7),
    payment_event(8, "HISTORICAL_SUCCEEDED_PAYMENT", "PAYMENT_OUTCOME_RECORDED"),
    event(
        9,
        "KNOWN_PAYMENT_PREFLIGHT_RECORDED",
        "KnownPaymentAttemptPreflightFact",
        "KNOWN_PAYMENT_PREFLIGHT_FACT",
        "known-payment-attempt-preflight-fact-trace/v2",
        status_path="projection.status",
        reason_codes_path="projection.reason_codes",
        relations=[
            relation("VALIDATED_AGAINST", "TransactionRequest", "CURRENT_REQUEST", "projection.current_request_ref", "TransactionRequest:{value}"),
            relation(
                "MEMBER_OF",
                "PaymentExecutionRecord",
                "HISTORICAL_SUCCEEDED_PAYMENT",
                "projection.related_attempt_refs[]",
                "PaymentExecutionRecord:{value}",
                value_mode="EACH_VALUE",
            ),
        ],
    ),
    validation_event(10),
    runtime_event(11),
    gate_result_event(12),
]

T11 = runtime_base() + [
    event(
        10,
        "FULFILMENT_OUTCOME_RECORDED",
        "FulfillmentRecord",
        "FULFILMENT_OUTCOME",
        "fulfillment-record-trace/v2",
        status_path="projection.status",
        reason_codes_path="projection.reason_codes",
        relations=[relation("BOUND_TO", "Order", "CURRENT_ORDER_SNAPSHOT", "projection.order_id", "Order:{value}")],
    ),
    event(
        11,
        "RECOVERY_OUTCOME_RECORDED",
        "PaymentRecoveryResult",
        "RECOVERY_OUTCOME",
        "payment-recovery-result-trace/v2",
        status_path="projection.recovery_status",
        reason_codes_path="projection.issue_codes",
    ),
    sidecar_result_event(12),
]

T12 = runtime_base() + [
    event(
        10,
        "STATUS_CONFLICT_RECORDED",
        "PaymentStatusConflictFact",
        "STATUS_CONFLICT_FACT",
        "payment-status-conflict-fact-trace/v2",
        status_path="projection.resolution",
        reason_codes_path="projection.reason_codes",
    ),
    sidecar_result_event(11),
]

TASKS = [
    task("T01", "正常授权购买", "WEBSHOP_NORMAL_PURCHASE_V2", T01),
    prepayment_task("T02", "订单价格上涨"),
    prepayment_task("T03", "订单价格下降"),
    prepayment_task("T04", "收款方变化"),
    action_binding_task("T05", "Action Agent 不匹配"),
    action_binding_task("T06", "Action ID 缺失", missing_id=True),
    overlay_task("T07", "不可信网页金额覆盖被阻断"),
    overlay_task("T08", "不可信收款方覆盖被阻断"),
    task("T09", "UNKNOWN 支付状态恢复", "WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2", T09),
    task("T10", "重复付款预检阻断", "WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V2", T10),
    task("T11", "付款成功但履约失败", "WEBSHOP_FULFILMENT_FAILURE_V2", T11),
    task("T12", "终态冲突", "WEBSHOP_PAYMENT_STATUS_CONFLICT_V2", T12),
]


def canonical_decimal(value: Decimal | str) -> str:
    decimal_value = value if isinstance(value, Decimal) else Decimal(value)
    if not decimal_value.is_finite():
        raise ValueError("Decimal must be finite")
    if decimal_value == 0:
        return "0"
    text = format(decimal_value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def canonical_primitive(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        raise TypeError("float is forbidden")
    if isinstance(value, Decimal):
        return canonical_decimal(value)
    if isinstance(value, tuple):
        return [canonical_primitive(item) for item in value]
    if isinstance(value, list):
        return [canonical_primitive(item) for item in value]
    if isinstance(value, dict):
        return {str(key): canonical_primitive(item) for key, item in value.items()}
    raise TypeError(f"unsupported canonical primitive: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        canonical_primitive(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def projection_identity_ref(source_type: str, schema: str, projection: dict[str, Any]) -> str:
    return f"{source_type}:projection-sha256:{digest({'projection_schema': schema, 'projection': projection})}"


def source_object_ref(schema: str, projection: dict[str, Any]) -> str:
    spec = REGISTRY[schema]
    mode = spec["source_identity"]["mode"]
    if mode == "PROJECTION_HASH_IDENTITY":
        return projection_identity_ref(spec["source_object_type"], schema, projection)
    template = spec["source_identity"]["template"]
    if not template:
        raise AssertionError(f"missing source identity template: {schema}")
    try:
        rendered = template.format(**projection)
    except KeyError as exc:
        raise AssertionError(f"source identity field missing for {schema}: {exc}") from exc
    if rendered.endswith(":") or "::" in rendered:
        raise AssertionError(f"invalid source identity: {rendered}")
    return rendered


def make_binding(schema: str, projection_input: dict[str, Any]) -> dict[str, Any]:
    spec = REGISTRY[schema]
    projection = canonical_primitive(projection_input)
    source_ref = source_object_ref(schema, projection)
    payload = {
        "source_object_type": spec["source_object_type"],
        "source_object_ref": source_ref,
        "projection_schema": schema,
        "projection": projection,
    }
    binding_digest = digest(payload)
    return {
        "binding_ref": f"TraceSourceBinding:sha256:{binding_digest}",
        **payload,
    }


def binding_digest(binding_ref: str) -> str:
    prefix = "TraceSourceBinding:sha256:"
    if not binding_ref.startswith(prefix):
        raise AssertionError(binding_ref)
    return binding_ref[len(prefix):]


_TEMPLATE_PATTERN = re.compile(r"\{projection\.([A-Za-z_][A-Za-z0-9_]*)\}")


def render_template(
    template: str,
    projection: dict[str, Any],
    *,
    binding_ref: str,
    value: Any | None = None,
) -> str:
    rendered = template.replace("{binding_digest}", binding_digest(binding_ref))
    if "{value}" in rendered:
        if value is None or isinstance(value, (dict, list)):
            raise AssertionError(f"invalid scalar template value: {value!r}")
        rendered = rendered.replace("{value}", str(value))

    def replace_projection(match: re.Match[str]) -> str:
        field = match.group(1)
        if field not in projection:
            raise AssertionError(f"template field missing: {field}")
        field_value = projection[field]
        if field_value is None or isinstance(field_value, (dict, list)):
            raise AssertionError(f"template field not scalar: {field}")
        return str(field_value)

    rendered = _TEMPLATE_PATTERN.sub(replace_projection, rendered)
    if "{" in rendered or "}" in rendered or "+" in rendered:
        raise AssertionError(f"unresolved or unsafe template: {rendered}")
    return rendered


def path_value(projection: dict[str, Any], path: str) -> Any:
    if not path.startswith("projection."):
        raise AssertionError(f"path must start with projection.: {path}")
    key = path[len("projection."):]
    is_array = key.endswith("[]")
    if is_array:
        key = key[:-2]
    if "." in key or "[" in key or "+" in key:
        raise AssertionError(f"coverage path must address projected field only: {path}")
    if key not in projection:
        raise AssertionError(f"projection path missing: {path}")
    value = projection[key]
    if is_array and not isinstance(value, list):
        raise AssertionError(f"array path is not a list: {path}")
    return value


def class_manifest() -> tuple[dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]]]:
    classes: dict[tuple[str, str], dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    for schema, spec in REGISTRY.items():
        module = spec["source_module"]
        source_file = ROOT / "src" / (module.replace(".", "/") + ".py")
        source_text = source_file.read_text(encoding="utf-8")
        tree = ast.parse(source_text)
        node = next(
            (
                item
                for item in tree.body
                if isinstance(item, ast.ClassDef) and item.name == spec["source_class"]
            ),
            None,
        )
        class_fields = []
        if node is not None:
            class_fields = [
                item.target.id
                for item in node.body
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
            ]
        extraction_rows = []
        for projection_field, extraction in spec["field_extractions"].items():
            root = re.split(r"\.|\[", extraction["path"], maxsplit=1)[0]
            extraction_rows.append(
                {
                    "projection_field": projection_field,
                    "source_path": extraction["path"],
                    "source_root": root,
                    "transform": extraction["transform"],
                    "root_exists": root in class_fields,
                }
            )
        row = {
            "projection_schema": schema,
            "source_module": module,
            "source_file": source_file.relative_to(ROOT).as_posix(),
            "source_class": spec["source_class"],
            "class_exists": node is not None,
            "class_fields": class_fields,
            "field_extractions": extraction_rows,
            "all_extraction_roots_exist": all(item["root_exists"] for item in extraction_rows),
        }
        rows.append(row)
        classes[(module, spec["source_class"])] = row
    return classes, rows


def validate_coverage() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def record(name: str, ok: bool, detail: Any = None) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    record("exact_task_ids", [item["task_id"] for item in TASKS] == [f"T{i:02d}" for i in range(1, 13)])
    for item in TASKS:
        roles = [row["entity_role"] for row in item["events"]]
        record(f"{item['task_id']}:roles_match", roles == item["entity_roles"])
        record(f"{item['task_id']}:status_not_available", item["current_status"] == "NOT_AVAILABLE")
        record(f"{item['task_id']}:no_new_business_rule", item["new_business_rule_required"] is False)
        role_index = {(row["entity_type"], row["entity_role"]): row for row in item["events"]}
        for row in item["events"]:
            schema = row["projection_schema"]
            spec = REGISTRY.get(schema)
            record(f"{item['task_id']}:{row['sequence_no']}:schema_exists", spec is not None, schema)
            if spec is None:
                continue
            record(
                f"{item['task_id']}:{row['sequence_no']}:source_grounded",
                row["source_module"] == spec["source_module"] and row["source_class"] == spec["source_class"],
            )
            template_texts = [row["entity_ref_template"]]
            for rel in row["relations"]:
                target = (rel["target_entity_type"], rel["target_entity_role"])
                record(f"{item['task_id']}:{row['sequence_no']}:relation_target_exists:{target}", target in role_index)
                template_texts.append(rel["target_entity_ref_template"])
                source_path = rel["source_assertion_path"]
                root = source_path.removeprefix("projection.").removesuffix("[]")
                record(
                    f"{item['task_id']}:{row['sequence_no']}:relation_source_field:{root}",
                    root in spec["projection_fields"],
                )
                for assertion in rel["target_binding_assertions"]:
                    source_root = assertion["source_path"].removeprefix("projection.")
                    record(
                        f"{item['task_id']}:{row['sequence_no']}:relation_binding_source:{source_root}",
                        source_root in spec["projection_fields"],
                    )
            record(
                f"{item['task_id']}:{row['sequence_no']}:no_raw_plus",
                all("+" not in text for text in template_texts)
                and all("+" not in (value or "") for value in row["value_paths"].values()),
            )
    t10 = next(item for item in TASKS if item["task_id"] == "T10")
    record("T10:exact_12_events", len(t10["events"]) == 12)
    record(
        "T10:exact_roles",
        [row["entity_role"] for row in t10["events"]]
        == [
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
        ],
    )
    record(
        "T12:real_conflict_type",
        any(
            row["source_class"] == "PaymentStatusConflictFact"
            and row["projection_schema"] == "payment-status-conflict-fact-trace/v2"
            for row in next(item for item in TASKS if item["task_id"] == "T12")["events"]
        ),
    )
    sidecar_rows = [
        row
        for item in TASKS
        for row in item["events"]
        if row["projection_schema"] == "webshop-payment-fulfilment-outcome-result-trace/v2"
    ]
    record("sidecar_result_has_no_fake_decision", all(row["value_paths"]["decision_path"] is None for row in sidecar_rows))
    failed = [item for item in checks if not item["ok"]]
    return {"check_count": len(checks), "failed_count": len(failed), "checks": checks, "failed": failed}


def build_t10_instance() -> dict[str, Any]:
    order_id = "webshop-order-" + hashlib.sha256("webshop-order|v1|hndpizntka|B06Y3VLDFB".encode()).hexdigest()[:24]
    request_id = "webshop-request-" + hashlib.sha256("webshop-request|v1|hndpizntka|B06Y3VLDFB".encode()).hexdigest()[:24]
    mandate_id = "experiment-context-mandate-ref-v1"
    authority_version = "experiment-authority-v1"
    order_version = "webshop-v1"
    current_payment_id = "project-baseline-payment-1"
    historical_payment_id = "project-baseline-payment-existing-success"
    action_id = "project-baseline-action-1"

    projections_by_role: dict[str, tuple[str, dict[str, Any]]] = {
        "AUTHORITY": (
            "intent-mandate-trace/v2",
            {"mandate_id": mandate_id, "authority_version": authority_version},
        ),
        "AUTHORIZED_ORDER_SNAPSHOT": (
            "order-snapshot-trace/v2",
            {
                "order_id": order_id,
                "order_version": order_version,
                "mandate_ref": mandate_id,
                "authority_version_ref": authority_version,
                "total_amount": Decimal("877.80"),
                "currency": "USD",
                "merchant": "webshop-experiment-merchant-v1",
                "payee": "webshop-experiment-payee-v1",
            },
        ),
        "CURRENT_ORDER_SNAPSHOT": (
            "order-snapshot-trace/v2",
            {
                "order_id": order_id,
                "order_version": order_version,
                "mandate_ref": mandate_id,
                "authority_version_ref": authority_version,
                "total_amount": Decimal("877.80"),
                "currency": "USD",
                "merchant": "webshop-experiment-merchant-v1",
                "payee": "webshop-experiment-payee-v1",
            },
        ),
        "CURRENT_REQUEST": (
            "transaction-request-trace/v2",
            {
                "request_id": request_id,
                "order_ref": order_id,
                "authority_ref": mandate_id,
                "authority_version_ref": authority_version,
                "amount": Decimal("877.80"),
                "currency": "USD",
                "merchant": "webshop-experiment-merchant-v1",
                "payee": "webshop-experiment-payee-v1",
                "agent_id": "webshop-agent-1",
            },
        ),
        "GOVERNED_ACTION": (
            "governed-payment-action-trace/v2",
            {
                "action_id": action_id,
                "action_type": "execute_payment",
                "agent_ref": "webshop-agent-1",
                "executor_ref": "offline-webshop-executor",
                "authority_ref": mandate_id,
                "authority_version": authority_version,
                "order_ref": order_id,
                "order_version": order_version,
                "request_ref": request_id,
                "payment_ref": current_payment_id,
                "source_refs": ["source:fixed-commerce-snapshot", "source:fixed-user-confirmation"],
                "side_effect_class": "PAYMENT_EXECUTION",
                "reversibility": "COMPENSATABLE_NOT_REVERSIBLE",
                "occurred_at": "2026-08-02T05:00:00.500000+00:00",
            },
        ),
        "CURRENT_PAYMENT_CANDIDATE": (
            "payment-execution-record-trace/v2",
            {
                "payment_id": current_payment_id,
                "request_id": request_id,
                "order_id": order_id,
                "status": "PENDING",
                "amount": Decimal("877.80"),
                "currency": "USD",
                "authority_ref": mandate_id,
                "agent_ref": "webshop-agent-1",
                "transaction_object_ref": request_id,
                "payee": "webshop-experiment-payee-v1",
            },
        ),
        "ACTION_BINDING_FACT": (
            "governed-action-binding-fact-trace/v2",
            {
                "status": "VALID",
                "action_id": action_id,
                "reason_codes": ["governed_action_binding_valid"],
                "checked_action_type": "execute_payment",
                "checked_order_ref": order_id,
                "checked_request_ref": request_id,
                "checked_payment_ref": current_payment_id,
            },
        ),
        "HISTORICAL_SUCCEEDED_PAYMENT": (
            "payment-execution-record-trace/v2",
            {
                "payment_id": historical_payment_id,
                "request_id": request_id,
                "order_id": order_id,
                "status": "SUCCEEDED",
                "amount": Decimal("877.80"),
                "currency": "USD",
                "authority_ref": mandate_id,
                "agent_ref": "webshop-agent-1",
                "transaction_object_ref": request_id,
                "payee": "webshop-experiment-payee-v1",
            },
        ),
        "KNOWN_PAYMENT_PREFLIGHT_FACT": (
            "known-payment-attempt-preflight-fact-trace/v2",
            {
                "status": "BLOCKED",
                "reason_codes": ["known_payment_attempt_duplicate_succeeded"],
                "current_request_ref": request_id,
                "related_attempt_refs": [historical_payment_id],
                "blocking_request_refs": [request_id],
                "limitations": [
                    "offline_fact_only",
                    "exact_payment_execution_records_only",
                    "succeeded_attempts_only",
                    "pending_or_unknown_attempt_policy_not_defined",
                    "no_external_payment_status_query",
                ],
            },
        ),
        "PREPAYMENT_VALIDATION": (
            "validation-result-trace/v2",
            {
                "decision": "DENY",
                "issue_codes": ["duplicate_request"],
                "evidence_paths": ["mandate.mandate_id", "request.request_id", "request.request_id"],
                "rule_version": "mandate-rules-v0.1",
                "order_difference_paths": [],
            },
        ),
        "RUNTIME_GATE_OBSERVATION": (
            "runtime-gate-record-trace/v2",
            {
                "preliminary_decision": "DENY",
                "final_decision": "DENY",
                "binding_status": "VALID",
                "binding_reason_codes": ["payment_execution_binding_match"],
                "identity_status": "VALID",
                "identity_reason_codes": ["identity_executor_binding_match"],
                "context_policy_status": "VALID",
                "context_policy_reason_codes": ["context_policy_valid"],
                "callback_executed": False,
                "callback_count": 0,
                "callback_result_ref": None,
                "reason_codes": [
                    "p1:duplicate_request",
                    "p1:upstream_prepayment_non_allow",
                    "p2:payment_execution_binding_match",
                    "p3:identity_executor_binding_match",
                    "p4:context_policy_valid",
                    "preflight:known_payment_attempt_duplicate_succeeded",
                ],
            },
        ),
        "FINAL_OUTCOME": (
            "webshop-buy-now-gate-outcome-result-trace/v2",
            {
                "decision": "DENY",
                "checkout_executed": False,
                "callback_count": 0,
                "callback_result_ref": None,
                "reason_codes": [
                    "p1:duplicate_request",
                    "p1:upstream_prepayment_non_allow",
                    "p2:payment_execution_binding_match",
                    "p3:identity_executor_binding_match",
                    "p4:context_policy_valid",
                    "preflight:known_payment_attempt_duplicate_succeeded",
                ],
                "limitations": [
                    "offline_interception_only",
                    "no_webshop_runtime_execution",
                    "no_real_buy_now_execution",
                    "no_real_payment_or_fulfilment",
                    "instruction_is_not_authorization_mandate",
                    "checkout_callback_is_injected_test_seam",
                ],
            },
        ),
    }

    bindings_by_role: dict[str, dict[str, Any]] = {}
    binding_by_ref: dict[str, dict[str, Any]] = {}
    for role, (schema, projection) in projections_by_role.items():
        binding = make_binding(schema, projection)
        bindings_by_role[role] = binding
        binding_by_ref.setdefault(binding["binding_ref"], binding)

    profile = next(item for item in TASKS if item["task_id"] == "T10")
    events = []
    event_index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in profile["events"]:
        role = row["entity_role"]
        binding = bindings_by_role[role]
        projection = binding["projection"]
        entity_ref = render_template(
            row["entity_ref_template"],
            projection,
            binding_ref=binding["binding_ref"],
        )
        instance = {
            "sequence_no": row["sequence_no"],
            "event_type": row["event_type"],
            "entity_type": row["entity_type"],
            "entity_role": role,
            "entity_ref": entity_ref,
            "source_binding_ref": binding["binding_ref"],
            "source_object_ref": binding["source_object_ref"],
            "decision": path_value(projection, row["value_paths"]["decision_path"]) if row["value_paths"]["decision_path"] else None,
            "status": path_value(projection, row["value_paths"]["status_path"]) if row["value_paths"]["status_path"] else None,
            "reason_codes": path_value(projection, row["value_paths"]["reason_codes_path"]) if row["value_paths"]["reason_codes_path"] else [],
            "relations": [],
        }
        events.append(instance)
        event_index[(row["entity_type"], role, entity_ref)] = instance

    relation_checks = []
    for row, instance in zip(profile["events"], events, strict=True):
        source_binding = binding_by_ref[instance["source_binding_ref"]]
        source_projection = source_binding["projection"]
        for rel in row["relations"]:
            raw = path_value(source_projection, rel["source_assertion_path"])
            values = raw if rel["value_mode"] == "EACH_VALUE" else [raw]
            for value in values:
                target_ref = render_template(
                    rel["target_entity_ref_template"],
                    source_projection,
                    binding_ref=source_binding["binding_ref"],
                    value=value,
                )
                target_key = (rel["target_entity_type"], rel["target_entity_role"], target_ref)
                target = event_index.get(target_key)
                binding_assertions = []
                if target is not None:
                    target_projection = binding_by_ref[target["source_binding_ref"]]["projection"]
                    for assertion in rel["target_binding_assertions"]:
                        source_value = path_value(source_projection, assertion["source_path"])
                        target_value = path_value(target_projection, assertion["target_path"])
                        binding_assertions.append(
                            {
                                **assertion,
                                "source_value": source_value,
                                "target_value": target_value,
                                "equal": source_value == target_value,
                            }
                        )
                resolved = {
                    "relation_type": rel["relation_type"],
                    "target_entity_type": rel["target_entity_type"],
                    "target_entity_role": rel["target_entity_role"],
                    "target_entity_ref": target_ref,
                    "target_resolved": target is not None,
                    "target_binding_assertions": binding_assertions,
                }
                instance["relations"].append(resolved)
                relation_checks.append(
                    {
                        "source_sequence_no": instance["sequence_no"],
                        **resolved,
                        "all_binding_assertions_equal": all(item["equal"] for item in binding_assertions),
                    }
                )

    event_binding_resolved = all(event["source_binding_ref"] in binding_by_ref for event in events)
    relations_resolved = all(
        item["target_resolved"] and item["all_binding_assertions_equal"]
        for item in relation_checks
    )
    order_refs = [
        event["source_binding_ref"]
        for event in events
        if event["entity_role"] in {"AUTHORIZED_ORDER_SNAPSHOT", "CURRENT_ORDER_SNAPSHOT"}
    ]
    return {
        "schema_version": "product-authoritative-trace-grounded-instance/v1",
        "task_id": "T10",
        "profile": profile["profile"],
        "fixture_basis": {
            "commerce_fixture": "samples/external/webshop/pre_buy_now_candidate_v1.json",
            "runner_shape": "scripts/validation/run_project_impact_baseline.py::_gate_context/_run_gate_task",
            "runtime_executed": False,
            "objects_constructed_from_fixed_literals_only": True,
        },
        "event_count": len(events),
        "unique_binding_count": len(binding_by_ref),
        "authorized_and_current_order_share_binding": len(order_refs) == 2 and order_refs[0] == order_refs[1],
        "event_binding_resolved": event_binding_resolved,
        "relations_resolved": relations_resolved,
        "hidden_resolver_used": False,
        "bindings": list(binding_by_ref.values()),
        "events": events,
        "relation_resolution": relation_checks,
    }


def write_json(path: Path, value: Any) -> str:
    text = json.dumps(canonical_primitive(value), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


classes, source_manifest_rows = class_manifest()
source_manifest = {
    "task_id": TASK_ID,
    "schema_count": len(REGISTRY),
    "all_classes_exist": all(row["class_exists"] for row in source_manifest_rows),
    "all_extraction_roots_exist": all(row["all_extraction_roots_exist"] for row in source_manifest_rows),
    "schemas": source_manifest_rows,
}
coverage_validation = validate_coverage()
if coverage_validation["failed_count"]:
    raise AssertionError(json.dumps(coverage_validation["failed"], ensure_ascii=False, indent=2))
if not source_manifest["all_classes_exist"] or not source_manifest["all_extraction_roots_exist"]:
    raise AssertionError("source grounding failed")

T10_INSTANCE = build_t10_instance()
if T10_INSTANCE["event_count"] != 12:
    raise AssertionError("T10 event count")
if T10_INSTANCE["unique_binding_count"] != 11:
    raise AssertionError("T10 unique binding count")
if not T10_INSTANCE["authorized_and_current_order_share_binding"]:
    raise AssertionError("T10 Order binding is not shared")
if not T10_INSTANCE["event_binding_resolved"] or not T10_INSTANCE["relations_resolved"]:
    raise AssertionError("T10 resolution failed")

DECIMAL_EXAMPLES = {
    "0": canonical_decimal("0"),
    "-0": canonical_decimal("-0"),
    "1": canonical_decimal("1"),
    "1.00": canonical_decimal("1.00"),
    "0.10": canonical_decimal("0.10"),
    "1000.000": canonical_decimal("1000.000"),
}
DECIMAL_DIGEST = digest(DECIMAL_EXAMPLES)

example_roles = [
    "AUTHORIZED_ORDER_SNAPSHOT",
    "CURRENT_REQUEST",
    "CURRENT_PAYMENT_CANDIDATE",
    "ACTION_BINDING_FACT",
    "FINAL_OUTCOME",
]
example_bindings = {
    role: next(
        binding
        for event in T10_INSTANCE["events"]
        if event["entity_role"] == role
        for binding in T10_INSTANCE["bindings"]
        if binding["binding_ref"] == event["source_binding_ref"]
    )
    for role in example_roles
}
REF_EXAMPLES = {
    "task_id": TASK_ID,
    "binding_formula": "TraceSourceBinding:sha256(canonical-json({source_object_type,source_object_ref,projection_schema,projection}))",
    "canonical_rules": {
        "null": "JSON null",
        "bool": "JSON true/false",
        "int": "base-10 JSON integer; bool is not int",
        "str": "unchanged Unicode string",
        "Decimal": "finite only; fixed notation; trim trailing zeros and decimal point; negative zero becomes 0; never float",
        "Enum": ".value then canonicalize",
        "datetime": "source datetime.isoformat(); timezone requirement belongs to source object contract",
        "tuple/list": "JSON array preserving order",
        "dict": "string keys; recursive canonicalization; lexicographic JSON key order",
        "float": "forbidden; fail closed",
    },
    "decimal_examples": DECIMAL_EXAMPLES,
    "decimal_examples_sha256": DECIMAL_DIGEST,
    "fixed_binding_examples": example_bindings,
    "collision_example": {
        "old_unsafe": {"ab+c": "abc", "a+bc": "abc"},
        "new": {"first": "Order:ab", "second": "Order:a", "not_equal": True},
        "rule": "typed templates never concatenate multiple unescaped fields",
    },
    "duplicate_binding_verdict": "INVALID for every repeated binding_ref, whether bytes are identical or conflicting",
}

T12_CONFLICT_PROJECTION = {
    "resolution": "CONFLICT",
    "initial_status": "UNKNOWN",
    "query_status": "SUCCEEDED",
    "query_observed_at": "2026-08-02T05:01:01+00:00",
    "async_status": "FAILED",
    "async_observed_at": "2026-08-02T05:02:01+00:00",
    "effective_status": "UNKNOWN",
    "effective_status_terminal": False,
    "reason_codes": ["payment_status_opposite_terminal_claims"],
    "business_success_confirmed": False,
    "fulfillment_confirmed": False,
    "user_task_success_confirmed": False,
    "reconciliation_confirmed": False,
    "settlement_confirmed": False,
    "legal_finality_confirmed": False,
}
T12_SIDECAR_PROJECTION = {
    "ready": True,
    "initial_payment_status": "UNKNOWN",
    "effective_payment_status": "UNKNOWN",
    "query_recovery_status": "RECOVERED",
    "status_conflict_resolution": "CONFLICT",
    "lifecycle_payment_status": "UNKNOWN",
    "lifecycle_fulfillment_status": "SUCCEEDED",
    "lifecycle_task_status": "UNKNOWN",
    "lifecycle_remediation_status": "REQUIRED",
    "retry_allowed": False,
    "duplicate_payment_blocked": False,
    "reason_codes": [
        "conflict:resolution:conflict",
        "conflict:payment_status_opposite_terminal_claims",
        "sidecar:status_evidence_conflict",
        "retry:not_allowed",
    ],
    "limitations": [
        "offline_sidecar_only",
        "no_real_payment_execution",
        "no_real_status_query_or_async_callback",
        "no_real_fulfilment",
        "no_automatic_payment_retry",
        "no_real_refund_or_dispute",
        "webshop_reward_not_used_as_payment_or_task_success",
    ],
}
T12_EXAMPLES = {
    "task_id": "T12",
    "conflict_fact": make_binding("payment-status-conflict-fact-trace/v2", T12_CONFLICT_PROJECTION),
    "sidecar_result": make_binding("webshop-payment-fulfilment-outcome-result-trace/v2", T12_SIDECAR_PROJECTION),
    "sidecar_decision_extraction": None,
    "decision_source": "RuntimeGateRecord.final_decision in the separate RUNTIME_DECISION_RECORDED event",
    "runtime_executed": False,
}

COVERAGE = {
    "schema_version": "product-authoritative-trace-coverage/v3",
    "generated_for_task": TASK_ID,
    "current_product_observed_valid": "0/12",
    "gesr": "0/12",
    "new_business_rule_required": False,
    "reference_model": {
        "source_object_ref": "source object identity only",
        "binding_ref": "exact projection commitment for every source object",
        "entity_ref": "profile entity identity generated by a closed typed template",
        "relation_target_entity_ref": "must equal an existing target event entity_ref",
        "event_binding_lookup": "ProductTraceEvent.source_binding_ref",
        "duplicate_binding_ref_verdict": "INVALID",
        "unreferenced_binding_verdict": "INVALID",
        "missing_binding_verdict": "INDETERMINATE",
        "hidden_resolver_allowed": False,
        "evaluator_reconstruction_allowed": False,
        "external_cryptographic_authenticity_claimed": False,
    },
    "canonical_decimal": {
        "examples": DECIMAL_EXAMPLES,
        "examples_sha256": DECIMAL_DIGEST,
        "float_allowed": False,
        "non_finite_allowed": False,
    },
    "projection_registry": REGISTRY,
    "forbidden_projection_fields": FORBIDDEN_PROJECTION_FIELDS,
    "coverage_validation": {
        "check_count": coverage_validation["check_count"],
        "failed_count": coverage_validation["failed_count"],
    },
    "tasks": TASKS,
}

source_sha = write_json(SOURCE_MANIFEST_JSON, source_manifest)
t10_sha = write_json(T10_INSTANCE_JSON, T10_INSTANCE)
t12_sha = write_json(T12_EXAMPLES_JSON, T12_EXAMPLES)
ref_sha = write_json(REF_EXAMPLES_JSON, REF_EXAMPLES)
coverage_sha = write_json(COVERAGE_JSON, COVERAGE)


def md_projection_table() -> str:
    lines = [
        "| projection_schema | 真实模块 / 类 | source identity | entity ref | 字段数 |",
        "|---|---|---|---|---:|",
    ]
    for schema, spec in REGISTRY.items():
        lines.append(
            f"| `{schema}` | `{spec['source_module']}.{spec['source_class']}` | "
            f"`{spec['source_identity']['mode']}` | `{spec['entity_ref_template']}` | {len(spec['projection_fields'])} |"
        )
    return "\n".join(lines)


def md_t10_table() -> str:
    profile = next(item for item in TASKS if item["task_id"] == "T10")
    lines = [
        "| # | event / role | schema | entity ref | relation targets |",
        "|---:|---|---|---|---|",
    ]
    for row in profile["events"]:
        targets = "; ".join(
            f"{rel['target_entity_role']}←{rel['source_assertion_path']}→{rel['target_entity_ref_template']}"
            for rel in row["relations"]
        ) or "—"
        lines.append(
            f"| {row['sequence_no']} | `{row['event_type']}` / `{row['entity_role']}` | "
            f"`{row['projection_schema']}` | `{row['entity_ref_template']}` | {targets} |"
        )
    return "\n".join(lines)


def md_task_table() -> str:
    lines = ["| Task | Profile | 事件数 | 当前状态 |", "|---|---|---:|---|"]
    for item in TASKS:
        lines.append(f"| {item['task_id']} | `{item['profile']}` | {len(item['events'])} | `NOT_AVAILABLE` |")
    return "\n".join(lines)


TRACE_TEXT = f"""# 产品权威轨迹最小合同 v1

## 1. 当前结论

产品权威轨迹必须由产品 outcome 在本次调用路径中直接携带。runner 只能读取 `outcome.authoritative_trace`，不得读取隐藏 `GateContext`、fixture 原对象或 evaluator replay 来补事件、补字段、补引用。

```text
product-observed authoritative trace = 0/12 VALID
GESR = 0/12
```

本轮只冻结引用模型和真实对象映射，不实现 trace、validator、runner 或任何产品行为。

## 2. 四类引用必须分开

| 引用 | 含义 | 生成方式 | 不承担的职责 |
|---|---|---|---|
| `source_object_ref` | 本次源对象身份 | native 对象使用关闭模板；无 native ID 的事实使用 projection identity hash | 不证明 projection 完整性 |
| `binding_ref` | exact projection 的完整性承诺 | `TraceSourceBinding:sha256(canonical-json(binding payload))` | 不代表业务实体身份或外部签名 |
| `entity_ref` | profile 内实体身份 | 关闭的带类型模板，如 `Order:<order_id>` | 不作为 binding lookup key |
| `relation.target_entity_ref` | 关系目标身份 | 从源 projection 的关闭字段生成，并与目标 event 的 `entity_ref` 完全相等 | 不允许模糊 native-id 匹配 |

唯一 binding lookup：

```text
ProductTraceEvent.source_binding_ref
→ envelope.source_bindings[binding_ref]
```

不得再用 `source_object_ref` 查找 binding。

## 3. Envelope、Binding、Event

```text
ProductAuthoritativeTrace
- schema_version
- source = PRODUCT_OBSERVED
- profile
- trace_ref
- completeness_status
- reason_codes
- events: tuple[ProductTraceEvent, ...]
- source_bindings: tuple[TraceSourceBinding, ...]

TraceSourceBinding
- binding_ref
- source_object_type
- source_object_ref
- projection_schema
- projection

ProductTraceEvent
- sequence_no
- event_type
- entity_type
- entity_role
- entity_ref
- source_binding_ref
- decision / status / reason_codes
- relations
```

`binding_ref` 对所有对象统一计算：

```text
TraceSourceBinding:sha256(
  canonical-json({{
    "source_object_type": ...,
    "source_object_ref": ...,
    "projection_schema": ...,
    "projection": exact primitive projection
  }})
)
```

规则：

1. 每个 event 的 `source_binding_ref` 必须恰好命中一个 binding；
2. 任意重复 `binding_ref`，无论内容相同或冲突，统一 `INVALID`；
3. 同一个 binding 可以被多个不同 role 的 event 引用；
4. 未引用 binding 为 `INVALID`；缺 binding 为 `INDETERMINATE`；
5. native `source_object_ref` 只标识对象，不再被描述为 projection 完整性证明；
6. 本合同只证明 envelope 内部一致性，不宣称签名、可信执行或外部密码学真实性。

## 4. Entity template 与关系解析

允许的主模板：

```text
IntentMandate:<mandate_id>
Order:<order_id>
TransactionRequest:<request_id>
GovernedPaymentAction:<action_id>
PaymentExecutionRecord:<payment_id>
FulfillmentRecord:<fulfillment_id>
<FactType>:binding:<binding-digest>
<OutcomeType>:binding:<binding-digest>
```

禁止 `projection.a+projection.b`。旧表达式中 `ab+c` 与 `a+bc` 都会得到 `abc`；新模板只使用带类型、带分隔符的单一身份字段，不存在该碰撞。

每条 relation 冻结：

```text
relation_type
target_entity_type
target_entity_role
source_assertion_path
target_entity_ref_template
value_mode
target_binding_assertions
```

validator 必须确认目标 event 存在，且 type、role、ref 完全一致；version 等不进入 entity ref 的字段通过 `target_binding_assertions` 与目标 binding projection 核对。

## 5. Canonical primitive

| 类型 | 唯一规则 |
|---|---|
| `null` | JSON `null` |
| `bool` | JSON `true/false` |
| `int` | 十进制 JSON integer；bool 不按 int 处理 |
| `str` | Unicode 原值 |
| `Decimal` | 仅 finite；固定小数；去尾零和小数点；`-0→0`；禁止 float |
| `Enum` | `.value` 后继续 canonicalize |
| `datetime` | 源对象 `isoformat()`；时区要求由源对象合同负责 |
| `tuple/list` | 保序 JSON array |
| `dict` | 字符串 key；递归转换；JSON key 字典序 |

固定 Decimal 样例：

```text
0 → {DECIMAL_EXAMPLES['0']}
-0 → {DECIMAL_EXAMPLES['-0']}
1 → {DECIMAL_EXAMPLES['1']}
1.00 → {DECIMAL_EXAMPLES['1.00']}
0.10 → {DECIMAL_EXAMPLES['0.10']}
1000.000 → {DECIMAL_EXAMPLES['1000.000']}
SHA-256 → {DECIMAL_DIGEST}
```

`NaN`、`Infinity` 和任何 float 均 fail closed。

## 6. 与当前代码闭合的 Projection Registry

{md_projection_table()}

每个 schema 的 `source_module`、`source_class`、`field_extractions` 已写入结构化 registry。直接字段必须存在；nested extraction 的根字段必须存在。不存在的 `PaymentStatusConflictOutcome` 已删除，统一使用真实 `PaymentStatusConflictFact`。

`WebShopPaymentFulfilmentOutcome` 不再伪造 `decision`。最终 decision 由独立的 `WebShopBuyNowGateOutcome` 或 `RuntimeGateRecord` event 承担；sidecar RESULT 只读取真实的 ready、payment、recovery、conflict、lifecycle、retry 和 reason 字段。

共同禁止输出：卡号/PAN/CVV、支付工具明文、钱包私钥、credential/token/cookie、原始网页、原始 prompt、用户输入全文、当前时间、内存地址、文件路径和随机值。

## 7. T10 exact 12-event profile

Profile：`WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V2`。

{md_t10_table()}

T10 的真实固定形状：

```text
authorized order == current order
→ 两个 ORDER event
→ 同一个 Order source_object_ref
→ 同一个 binding_ref
→ 同一个 entity_ref = Order:<order_id>
→ 由两个 entity_role 区分
```

当前付款候选和历史成功付款是两个不同 `PaymentExecutionRecord`，分别使用 `CURRENT_PAYMENT_CANDIDATE` 与 `HISTORICAL_SUCCEEDED_PAYMENT`。`GovernedPaymentAction.payment_ref` 指向当前付款；`KnownPaymentAttemptPreflightFact.related_attempt_refs` 指向历史成功付款。

结构化实例已验证：

```text
12 events
11 unique bindings
2 个 Order event 共享 1 个 binding
所有 event binding 可解析
所有 relation target 可解析
hidden resolver = false
```

## 8. VALID / INVALID / INDETERMINATE

`VALID` 必须同时满足 exact profile、连续顺序、关闭 schema、exact allowlist、binding digest、entity template、event value path 和 relation target 全部一致。

```text
缺 event / binding / 必填字段 / extraction path → INDETERMINATE
重复 binding_ref / extra field / digest mismatch / entity mismatch / relation mismatch → INVALID
产品未暴露 authoritative_trace → NOT_AVAILABLE
```

产品 trace 缺失时，即使 evaluator replay 有效，也不得回退成 `VALID`。

## 9. 结构化证据

- Coverage：`{COVERAGE_JSON.relative_to(ROOT).as_posix()}`，SHA-256 `{coverage_sha}`
- Source grounding：`{SOURCE_MANIFEST_JSON.relative_to(ROOT).as_posix()}`，SHA-256 `{source_sha}`
- Ref/Decimal examples：`{REF_EXAMPLES_JSON.relative_to(ROOT).as_posix()}`，SHA-256 `{ref_sha}`
- T10 grounded instance：`{T10_INSTANCE_JSON.relative_to(ROOT).as_posix()}`，SHA-256 `{t10_sha}`
- T12/sidecar examples：`{T12_EXAMPLES_JSON.relative_to(ROOT).as_posix()}`，SHA-256 `{t12_sha}`

## 10. 阶段边界

```text
本设计修复被 Evaluator 接受
→ 冻结独立 measurement-adapter maintenance
→ accepted runner 重新确认 0/12 BEFORE
→ 再条件解锁 T10 capability experiment
```

本文件不实现后续阶段。
"""

COVERAGE_TEXT = f"""# 产品权威轨迹 12 项覆盖映射 v1

## 1. 当前结论

固定 T01—T12 当前都没有产品 outcome 直接携带统一 `ProductAuthoritativeTrace`：

```text
product-observed authoritative trace = 0/12 VALID
GESR = 0/12
new_business_rule_required = false
```

结构化 coverage：`{COVERAGE_JSON.relative_to(ROOT).as_posix()}`  
SHA-256：`{coverage_sha}`  
Schema：`product-authoritative-trace-coverage/v3`

## 2. 引用口径

```text
source_object_ref = 源对象身份
binding_ref = exact projection digest
entity_ref = profile 实体身份
relation.target_entity_ref = 必须等于目标 event entity_ref
```

每个 event 通过 `source_binding_ref` 解析 binding。重复 `binding_ref` 统一 `INVALID`；不允许隐藏 GateContext、evaluator replay 或外部 registry 补 source。

## 3. T01—T12 概览

{md_task_table()}

T07/T08 直接绑定当前真实 `AttackOverlayResult`，不再虚构 sidecar outcome；T12 使用真实 `PaymentStatusConflictFact`；sidecar RESULT 不读取不存在的 `decision`。

## 4. T10 exact matrix

{md_t10_table()}

T10 固定结果：

```text
12 events
11 unique bindings
AUTHORIZED_ORDER_SNAPSHOT 与 CURRENT_ORDER_SNAPSHOT 共享同一 Order binding
CURRENT_PAYMENT_CANDIDATE 与 HISTORICAL_SUCCEEDED_PAYMENT 保持不同 payment_id/role
全部 relation target 精确解析
```

结构化实例：`{T10_INSTANCE_JSON.relative_to(ROOT).as_posix()}`，SHA-256 `{t10_sha}`。

## 5. Source class / field grounding

每个 projection schema 都包含：

```text
source_module
source_class
field_extractions
projection_fields
source_identity
entity_ref_template
```

机器审计结果：

```text
schema_count = {len(REGISTRY)}
all source classes exist = true
all direct/nested extraction roots exist = true
coverage checks = {coverage_validation['check_count']}/{coverage_validation['check_count']}
```

Manifest：`{SOURCE_MANIFEST_JSON.relative_to(ROOT).as_posix()}`，SHA-256 `{source_sha}`。

## 6. 关系解析规则

1. relation 必须声明目标 type、role 和 typed ref template；
2. source assertion 只能读取当前 binding projection 的关闭字段；
3. 数组关系显式使用 `EACH_VALUE`；
4. version 等非 entity identity 字段使用 target binding assertion；
5. 目标 event 不存在、type/role/ref 不完全一致或 binding assertion 不相等时 fail closed；
6. 禁止裸 `+` expression 和模糊 native-id fallback。

## 7. 最小披露与阶段边界

所有 projection 都是 exact allowlist。当前仍只冻结设计，不修改 `src/`、`tests/`、`scripts/`、`samples/`，不创建 measurement-adapter 或 T10 capability `CONTRACT.md`。
"""

MEASUREMENT_TEXT = f"""# Measurement Adapter Freeze

Task name: 产品权威轨迹测量适配  
Task kind: `maintenance`  
Project impact verdict: `NOT_APPLICABLE`  
Prerequisite: reference-model grounding repair 被 Evaluator 接受

## 1. 单一目标

只让测量层读取并严格校验 `outcome.authoritative_trace`。产品继续不产出 trace，重新冻结可信的 `0/12 VALID` BEFORE 和 accepted runner hash。

```text
runner reads exact envelope
→ event.source_binding_ref resolves envelope binding
→ validates object identity, binding digest, entity template and relation target separately
→ absent trace remains NOT_AVAILABLE
```

## 2. 唯一 resolver

唯一 resolver 是：

```text
outcome.authoritative_trace.source_bindings
```

禁止读取 `GateContext`、mandate/order/request/action/payment 原对象、fixture、known attempts 或 evaluator replay 补 source。

## 3. Strict matrix

以下均不得得到 `VALID`：

1. missing binding；
2. 任意 duplicate `binding_ref`，包括 identical 和 conflicting；
3. unreferenced binding；
4. unknown schema/class/field extraction；
5. source native identity mismatch；
6. binding digest mismatch；
7. projection extra/missing/forbidden field；
8. Decimal `1.0/1.00/1` 规范不一致；
9. Decimal `-0` 未规范为 `0`；
10. Decimal NaN/Infinity/float；
11. entity template 缺字段或出现裸 `+`；
12. relation target type/role/ref mismatch；
13. target binding version assertion mismatch；
14. RESULT projection 含 `authoritative_trace`；
15. sidecar RESULT 读取不存在的 `decision`；
16. product trace 缺失但 evaluator replay 有效；
17. hidden context fallback。

## 4. Validator 分层

```text
A. schema/source grounding
B. source_object_ref identity
C. binding_ref exact digest
D. entity_ref typed template
E. event decision/status/reason paths
F. relation exact target and binding assertions
G. profile sequence/completeness
```

任何 source class 或 extraction root 与当前代码不闭合时 fail closed。

## 5. BEFORE 必须保持

```text
product-observed trace = 0/12 VALID
GESR = 0/12
重复或禁止副作用 = 0/12
callback match = 12/12
决策—理由一致 = 12/12
```

同时冻结 accepted runner、target、BEFORE output、non-trace projection SHA-256。

## 6. 明确禁止

- 产品 outcome 开始产出 trace；
- 修改 T01—T12 业务预期；
- 同时实现 T10 产品 trace；
- 创建 measurement-adapter 或 T10 capability 正式 `CONTRACT.md`；
- 依赖网络、新环境或新依赖；
- 宣称项目 `IMPROVED`。

本文件是后续冻结输入，不是正式执行合同。
"""

NEXT_TEXT = """# Next Capability Slice — Conditional Freeze

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-T10-DUPLICATE-PREFLIGHT-SLICE-V1`  
Task kind: `capability_experiment`  
State: `CONDITIONAL_NOT_FROZEN`  
Project map revision: `2026-08-04-r5`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Slice task: `T10`  
Trace profile: `WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V2`

## 1. 前置条件

```text
prerequisite = measurement adapter accepted
runner hash = TBD_AFTER_ADAPTER_ACCEPTANCE
before hash = TBD_AFTER_ADAPTER_ACCEPTANCE
target hash = TBD_AFTER_ADAPTER_ACCEPTANCE
non-trace projection hash = TBD_AFTER_ADAPTER_ACCEPTANCE
state = CONDITIONAL_NOT_FROZEN
```

前置条件未满足时，不创建本任务 `CONTRACT.md`，不修改产品 outcome。

## 2. 单一产品变量

前置条件满足后，只允许 T10 duplicate-preflight `BLOCKED` 返回的 `WebShopBuyNowGateOutcome` 携带：

```text
ProductAuthoritativeTrace
source = PRODUCT_OBSERVED
profile = WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V2
events = exact 12
source_bindings = exact 11 unique bindings
```

两个 ORDER event 必须共享同一个 `source_binding_ref`；Action、当前付款候选和历史成功付款分别记录。

## 3. 四类引用

```text
source_object_ref = 对象身份
binding_ref = projection digest
entity_ref = typed profile identity
relation.target_entity_ref = exact target event ref
```

每个 event 只能通过 `source_binding_ref` 解析 binding。禁止 hidden resolver、evaluator replay 和外部 registry。

## 4. BEFORE / AFTER

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

## 5. Exact 12-event sequence

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

## 6. 回滚条件

- runner/validator 不等于阶段 A accepted hash；
- 不是 12 events / 11 unique bindings；
- 两个 Order event 未共享 binding；
- duplicate binding_ref 未判 INVALID；
- Decimal canonicalization 或 source grounding 不一致；
- relation target 不能精确解析；
- decision、callback、状态、binding 或 side effect 变化；
- 需要网络、真实支付、WebShop runtime 或外部副作用。

## 7. 当前裁定

本文件保持 `CONDITIONAL_NOT_FROZEN`，不构成执行合同。下一步仍必须先由 Evaluator 冻结并接受独立 measurement-adapter 任务。
"""

for output_path, output_text in (
    (TRACE_DOC, TRACE_TEXT),
    (COVERAGE_DOC, COVERAGE_TEXT),
    (MEASUREMENT_ADAPTER, MEASUREMENT_TEXT),
    (NEXT_SLICE, NEXT_TEXT),
):
    normalized_text = chr(10).join(line.rstrip() for line in output_text.splitlines()) + chr(10)
    output_path.write_text(normalized_text, encoding="utf-8")

print(f"task_id={TASK_ID}")
print(f"registry_schemas={len(REGISTRY)}")
print(f"source_grounding={source_manifest['all_classes_exist'] and source_manifest['all_extraction_roots_exist']}")
print(f"coverage_checks={coverage_validation['check_count']}/{coverage_validation['check_count']}")
print(f"T10_events={T10_INSTANCE['event_count']}")
print(f"T10_unique_bindings={T10_INSTANCE['unique_binding_count']}")
print(f"T10_shared_order_binding={T10_INSTANCE['authorized_and_current_order_share_binding']}")
print(f"T10_relations_resolved={T10_INSTANCE['relations_resolved']}")
print(f"coverage_sha256={coverage_sha}")
print(f"source_manifest_sha256={source_sha}")
print(f"ref_examples_sha256={ref_sha}")
print(f"t10_instance_sha256={t10_sha}")
print(f"t12_examples_sha256={t12_sha}")

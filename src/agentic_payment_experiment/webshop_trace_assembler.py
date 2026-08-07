"""Neutral mechanical assembly helpers for WebShop product traces.

The functions in this module only project already-produced immutable facts and
assemble trace contract objects. They do not decide whether a business scenario
is valid, rerun payment controls, read external state, or perform side effects.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .authoritative_trace import (
    EXPECTED_COMPLETENESS_STATUS,
    EXPECTED_TRACE_SCHEMA_VERSION,
    EXPECTED_TRACE_SOURCE,
    ProductAuthoritativeTrace,
    ProductTraceEvent,
    TraceBindingAssertion,
    TraceRelation,
    TraceSourceBinding,
    compute_binding_ref,
    compute_projection_source_ref,
    render_entity_ref,
)
from .models import (
    FulfillmentRecord,
    IntentMandate,
    Order,
    PaymentExecutionRecord,
    PaymentRecoveryResult,
    TransactionRequest,
    ValidationResult,
)
from .payment_status_conflict import PaymentStatusConflictFact
from .trusted_execution import (
    GovernedActionBindingFact,
    GovernedPaymentAction,
    RuntimeGateRecord,
)


def create_source_binding(
    source_object_type: str,
    projection_schema: str,
    projection: Mapping[str, Any],
) -> TraceSourceBinding:
    """Create one deterministic source binding from a frozen projection."""

    source_object_ref = compute_projection_source_ref(
        source_object_type,
        projection_schema,
        projection,
    )
    payload = {
        "source_object_type": source_object_type,
        "source_object_ref": source_object_ref,
        "projection_schema": projection_schema,
        "projection": projection,
    }
    return TraceSourceBinding(
        binding_ref=compute_binding_ref(payload),
        source_object_type=source_object_type,
        source_object_ref=source_object_ref,
        projection_schema=projection_schema,
        projection=projection,
    )


def create_relation(
    relation_type: str,
    target_entity_type: str,
    target_entity_role: str,
    target_entity_ref: str,
    *,
    assertions: tuple[TraceBindingAssertion, ...] = (),
) -> TraceRelation:
    """Create a resolved relation to another trace entity."""

    return TraceRelation(
        relation_type=relation_type,
        target_entity_type=target_entity_type,
        target_entity_role=target_entity_role,
        target_entity_ref=target_entity_ref,
        target_binding_assertions=assertions,
        target_resolved=True,
    )


def create_event(
    sequence_no: int,
    event_type: str,
    entity_type: str,
    entity_role: str,
    binding: TraceSourceBinding,
    entity_ref_template: str,
    *,
    decision: str | None = None,
    status: str | None = None,
    reason_codes: tuple[str, ...] = (),
    relations: tuple[TraceRelation, ...] = (),
) -> ProductTraceEvent:
    """Create one event bound to an existing deterministic source binding."""

    return ProductTraceEvent(
        sequence_no=sequence_no,
        event_type=event_type,
        entity_type=entity_type,
        entity_role=entity_role,
        entity_ref=render_entity_ref(binding, entity_ref_template),
        source_binding_ref=binding.binding_ref,
        decision=decision,
        status=status,
        reason_codes=reason_codes,
        relations=relations,
    )


def project_mandate(mandate: IntentMandate) -> dict[str, Any]:
    return {
        "mandate_id": mandate.mandate_id,
        "authority_version": mandate.authority_version,
    }


def project_order(order: Order) -> dict[str, Any]:
    return {
        "order_id": order.order_id,
        "order_version": order.order_version,
        "mandate_ref": order.mandate_ref,
        "authority_version_ref": order.authority_version_ref,
        "total_amount": order.total_amount,
        "currency": order.currency,
        "merchant": order.merchant,
        "payee": order.payee,
    }


def project_request(request: TransactionRequest) -> dict[str, Any]:
    return {
        "request_id": request.request_id,
        "order_ref": request.order_ref,
        "authority_ref": request.authority_ref,
        "authority_version_ref": request.authority_version_ref,
        "amount": request.amount,
        "currency": request.currency,
        "merchant": request.merchant,
        "payee": request.payee,
        "agent_id": request.agent_id,
    }


def project_governed_action(action: GovernedPaymentAction) -> dict[str, Any]:
    return {
        "action_id": action.action_id,
        "action_type": action.action_type,
        "agent_ref": action.agent_ref,
        "executor_ref": action.executor_ref,
        "authority_ref": action.authority_ref,
        "authority_version": action.authority_version,
        "order_ref": action.order_ref,
        "order_version": action.order_version,
        "request_ref": action.request_ref,
        "payment_ref": action.payment_ref,
        "source_refs": action.source_refs,
        "side_effect_class": action.side_effect_class,
        "reversibility": action.reversibility,
        "occurred_at": action.occurred_at,
    }


def project_payment(payment: PaymentExecutionRecord) -> dict[str, Any]:
    return {
        "payment_id": payment.payment_id,
        "request_id": payment.request_id,
        "order_id": payment.order_id,
        "status": payment.status,
        "amount": payment.amount,
        "currency": payment.currency,
        "authority_ref": payment.authority_ref,
        "agent_ref": payment.agent_ref,
        "transaction_object_ref": payment.transaction_object_ref,
        "payee": payment.payee,
    }


def project_action_binding_fact(fact: GovernedActionBindingFact) -> dict[str, Any]:
    return {
        "status": fact.status,
        "action_id": fact.action_id,
        "reason_codes": fact.reason_codes,
        "checked_action_type": fact.checked_action_type,
        "checked_order_ref": fact.checked_order_ref,
        "checked_request_ref": fact.checked_request_ref,
        "checked_payment_ref": fact.checked_payment_ref,
    }


def project_runtime_gate(record: RuntimeGateRecord) -> dict[str, Any]:
    return {
        "preliminary_decision": record.preliminary_decision,
        "final_decision": record.final_decision,
        "binding_status": record.binding_status,
        "binding_reason_codes": record.binding_reason_codes,
        "identity_status": record.identity_status,
        "identity_reason_codes": record.identity_reason_codes,
        "context_policy_status": record.context_policy_status,
        "context_policy_reason_codes": record.context_policy_reason_codes,
        "callback_executed": record.callback_executed,
        "callback_count": record.callback_count,
        "callback_result_ref": record.callback_result_ref,
        "reason_codes": record.reason_codes,
    }


def project_fulfillment(record: FulfillmentRecord) -> dict[str, Any]:
    return {
        "fulfillment_id": record.fulfillment_id,
        "order_id": record.order_id,
        "status": record.status,
        "failure_code": record.failure_code,
        "reason_codes": (() if record.failure_code is None else (record.failure_code,)),
    }


def project_payment_recovery(record: PaymentRecoveryResult) -> dict[str, Any]:
    return {
        "initial_status": record.initial_status,
        "observed_status": record.observed_status,
        "effective_status": record.effective_status,
        "recovery_status": record.recovery_status,
        "next_action": record.next_action,
        "retry_allowed": record.retry_allowed,
        "issue_codes": tuple(item.code for item in record.issues),
        "evidence_paths": tuple(item.field_path for item in record.evidence),
        "rule_version": record.rule_version,
    }


def project_payment_status_conflict(
    fact: PaymentStatusConflictFact,
) -> dict[str, Any]:
    return {
        "resolution": fact.resolution,
        "initial_status": fact.initial_status,
        "query_status": fact.query_status,
        "query_observed_at": fact.query_observed_at,
        "async_status": fact.async_status,
        "async_observed_at": fact.async_observed_at,
        "effective_status": fact.effective_status,
        "effective_status_terminal": fact.effective_status_terminal,
        "reason_codes": fact.reason_codes,
        "business_success_confirmed": fact.business_success_confirmed,
        "fulfillment_confirmed": fact.fulfillment_confirmed,
        "user_task_success_confirmed": fact.user_task_success_confirmed,
        "reconciliation_confirmed": fact.reconciliation_confirmed,
        "settlement_confirmed": fact.settlement_confirmed,
        "legal_finality_confirmed": fact.legal_finality_confirmed,
    }


def project_validation_result(result: ValidationResult) -> dict[str, Any]:
    return {
        "decision": result.decision,
        "issue_codes": tuple(item.code for item in result.issues),
        "evidence_paths": tuple(item.field_path for item in result.evidence),
        "rule_version": result.rule_version,
        "order_difference_paths": tuple(
            item.field_path for item in result.order_differences
        ),
    }


def project_webshop_gate_outcome(outcome: Any) -> dict[str, Any]:
    """Project the frozen public gate-result fields without importing the gate module."""

    return {
        "decision": outcome.decision,
        "checkout_executed": outcome.checkout_executed,
        "callback_count": outcome.callback_count,
        "callback_result_ref": outcome.callback_result_ref,
        "reason_codes": outcome.reason_codes,
        "limitations": outcome.limitations,
    }


def project_payment_sidecar_outcome(outcome: Any) -> dict[str, Any]:
    """Project the frozen public result fields without importing the sidecar module."""

    lifecycle = outcome.lifecycle
    return {
        "ready": outcome.ready,
        "initial_payment_status": (
            outcome.initial_payment.status if outcome.initial_payment else None
        ),
        "effective_payment_status": (
            outcome.effective_payment.status if outcome.effective_payment else None
        ),
        "query_recovery_status": (
            outcome.query_recovery.recovery_status
            if outcome.query_recovery is not None
            else None
        ),
        "status_conflict_resolution": (
            outcome.status_conflict.resolution
            if outcome.status_conflict is not None
            else None
        ),
        "lifecycle_payment_status": (
            lifecycle.payment_status if lifecycle is not None else None
        ),
        "lifecycle_fulfillment_status": (
            lifecycle.fulfillment_status if lifecycle is not None else None
        ),
        "lifecycle_task_status": (
            lifecycle.task_status if lifecycle is not None else None
        ),
        "lifecycle_remediation_status": (
            lifecycle.remediation.status if lifecycle is not None else None
        ),
        "retry_allowed": outcome.retry_allowed,
        "duplicate_payment_blocked": outcome.duplicate_payment_blocked,
        "reason_codes": outcome.reason_codes,
        "limitations": outcome.limitations,
    }


def assemble_product_trace(
    *,
    profile: str,
    trace_ref: str,
    events: tuple[ProductTraceEvent, ...],
    source_bindings: tuple[TraceSourceBinding, ...],
    expected_unique_binding_count: int,
) -> ProductAuthoritativeTrace | None:
    """Assemble a complete product trace or fail closed for invalid mechanics."""

    if type(profile) is not str or not profile:
        return None
    if type(trace_ref) is not str or not trace_ref:
        return None
    if type(events) is not tuple or not events:
        return None
    if type(source_bindings) is not tuple or not source_bindings:
        return None
    if type(expected_unique_binding_count) is not int:
        return None
    if expected_unique_binding_count <= 0:
        return None
    if not all(type(event) is ProductTraceEvent for event in events):
        return None
    if not all(type(binding) is TraceSourceBinding for binding in source_bindings):
        return None
    unique_binding_refs = {binding.binding_ref for binding in source_bindings}
    if len(unique_binding_refs) != len(source_bindings):
        return None
    if len(unique_binding_refs) != expected_unique_binding_count:
        return None

    return ProductAuthoritativeTrace(
        schema_version=EXPECTED_TRACE_SCHEMA_VERSION,
        source=EXPECTED_TRACE_SOURCE,
        profile=profile,
        trace_ref=trace_ref,
        completeness_status=EXPECTED_COMPLETENESS_STATUS,
        events=events,
        source_bindings=source_bindings,
    )


__all__ = [
    "assemble_product_trace",
    "create_event",
    "create_relation",
    "create_source_binding",
    "project_action_binding_fact",
    "project_fulfillment",
    "project_governed_action",
    "project_mandate",
    "project_order",
    "project_payment",
    "project_payment_recovery",
    "project_payment_sidecar_outcome",
    "project_payment_status_conflict",
    "project_request",
    "project_runtime_gate",
    "project_validation_result",
    "project_webshop_gate_outcome",
]

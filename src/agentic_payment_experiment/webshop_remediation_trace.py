"""Generic post-payment remediation evidence extension for WebShop traces.

This module records already-produced immutable remediation facts in the same
ProductAuthoritativeTrace.  It never decides refund/dispute semantics and never
recomputes original-transaction binding.
"""

from __future__ import annotations

from .authoritative_trace import (
    ProductAuthoritativeTrace,
    TraceValidationStatus,
    validate_product_authoritative_trace,
)
from .models import DisputeRecord, LifecycleResult, RefundRecord
from .trusted_execution import OriginalTransactionBindingFact
from .webshop_trace_assembler import (
    assemble_product_trace,
    create_event,
    create_relation,
    create_source_binding,
    project_dispute_record,
    project_original_transaction_binding_fact,
    project_refund_record,
    project_remediation_closure,
)


_BASE_PROFILE = "WEBSHOP_NORMAL_PURCHASE_V2"
_REFUND_PROFILE = "WEBSHOP_POST_PAYMENT_REFUND_REMEDIATION_V1"
_DISPUTE_PROFILE = "WEBSHOP_POST_PAYMENT_DISPUTE_REMEDIATION_V1"


def _find_event(trace: ProductAuthoritativeTrace, role: str):
    matches = tuple(event for event in trace.events if event.entity_role == role)
    return matches[0] if len(matches) == 1 else None


def _observation_identity(observation: RefundRecord | DisputeRecord) -> str:
    if isinstance(observation, RefundRecord):
        return observation.refund_id
    return observation.dispute_id


def _source_configuration(
    observation: RefundRecord | DisputeRecord,
) -> tuple[str, str, str, dict[str, object]]:
    if isinstance(observation, RefundRecord):
        return (
            _REFUND_PROFILE,
            "RefundRecord",
            "refund-record-remediation-trace/v1",
            project_refund_record(observation),
        )
    if isinstance(observation, DisputeRecord):
        return (
            _DISPUTE_PROFILE,
            "DisputeRecord",
            "dispute-record-remediation-trace/v1",
            project_dispute_record(observation),
        )
    raise TypeError("unsupported remediation observation")


def _mechanically_consistent(
    base_trace: ProductAuthoritativeTrace,
    observation: RefundRecord | DisputeRecord,
    binding_fact: OriginalTransactionBindingFact,
    closure: LifecycleResult,
) -> bool:
    if base_trace.profile != _BASE_PROFILE:
        return False

    current_order = _find_event(base_trace, "CURRENT_ORDER_SNAPSHOT")
    payment_outcome = _find_event(base_trace, "PAYMENT_EXECUTION_OUTCOME")
    if current_order is None or payment_outcome is None:
        return False

    if current_order.entity_ref != f"Order:{observation.order_id}":
        return False
    if binding_fact.original_order_ref is None:
        return False
    if current_order.entity_ref != f"Order:{binding_fact.original_order_ref}":
        return False
    if binding_fact.original_payment_ref is None:
        return False
    if payment_outcome.entity_ref != f"PaymentExecutionRecord:{binding_fact.original_payment_ref}":
        return False
    if binding_fact.follow_up_order_ref != observation.order_id:
        return False
    if binding_fact.follow_up_payment_ref != observation.payment_id:
        return False
    if closure.remediation.case_ref != _observation_identity(observation):
        return False

    expected_action = "REFUND" if isinstance(observation, RefundRecord) else "DISPUTE"
    if binding_fact.action.value != expected_action:
        return False
    return True


def extend_product_authoritative_trace_with_remediation(
    base_trace: ProductAuthoritativeTrace,
    observation: RefundRecord | DisputeRecord,
    binding_fact: OriginalTransactionBindingFact,
    closure: LifecycleResult,
) -> ProductAuthoritativeTrace | None:
    """Append source-bound remediation evidence, returning ``None`` on any gap.

    An INVALID OriginalTransactionBindingFact is legitimate evidence.  The
    extension records it as-is; it never upgrades the status and never creates a
    payment relation from the remediation observation.  The observation is only
    linked to the already-recorded current order, which remains valid for the
    accepted negative-control mismatch.
    """

    if not isinstance(base_trace, ProductAuthoritativeTrace):
        return None
    if validate_product_authoritative_trace(base_trace).status is not TraceValidationStatus.VALID:
        return None
    if not isinstance(observation, (RefundRecord, DisputeRecord)):
        return None
    if not isinstance(binding_fact, OriginalTransactionBindingFact):
        return None
    if not isinstance(closure, LifecycleResult):
        return None
    if not _mechanically_consistent(base_trace, observation, binding_fact, closure):
        return None

    profile, observation_type, observation_schema, observation_projection = (
        _source_configuration(observation)
    )
    observation_binding = create_source_binding(
        observation_type,
        observation_schema,
        observation_projection,
    )
    binding_fact_binding = create_source_binding(
        "OriginalTransactionBindingFact",
        "original-transaction-binding-fact-remediation-trace/v1",
        project_original_transaction_binding_fact(binding_fact),
    )
    closure_binding = create_source_binding(
        "LifecycleResult",
        "lifecycle-remediation-closure-trace/v1",
        project_remediation_closure(closure),
    )

    current_order = _find_event(base_trace, "CURRENT_ORDER_SNAPSHOT")
    assert current_order is not None
    order_relation = create_relation(
        "BOUND_TO",
        "Order",
        "CURRENT_ORDER_SNAPSHOT",
        current_order.entity_ref,
    )

    next_sequence = len(base_trace.events) + 1
    if isinstance(observation, RefundRecord):
        observation_template = "RefundRecord:{projection.refund_id}"
    else:
        observation_template = "DisputeRecord:{projection.dispute_id}"

    observation_event = create_event(
        next_sequence,
        "REMEDIATION_OBSERVATION_RECORDED",
        observation_type,
        "REMEDIATION_OBSERVATION",
        observation_binding,
        observation_template,
        status=str(observation_binding.projection["status"]),
        reason_codes=tuple(observation_binding.projection["reason_codes"]),
        relations=(order_relation,),
    )
    binding_event = create_event(
        next_sequence + 1,
        "ORIGINAL_TRANSACTION_BINDING_RECORDED",
        "OriginalTransactionBindingFact",
        "ORIGINAL_TRANSACTION_BINDING_FACT",
        binding_fact_binding,
        "OriginalTransactionBindingFact:binding:{binding_digest}",
        status=str(binding_fact_binding.projection["status"]),
        reason_codes=tuple(binding_fact_binding.projection["reason_codes"]),
    )
    closure_event = create_event(
        next_sequence + 2,
        "REMEDIATION_CLOSURE_RECORDED",
        "LifecycleResult",
        "REMEDIATION_CLOSURE_OUTCOME",
        closure_binding,
        "LifecycleResult:remediation-closure:{binding_digest}",
        status=str(closure_binding.projection["remediation_status"]),
        reason_codes=tuple(closure_binding.projection["issue_codes"]),
    )

    source_bindings = base_trace.source_bindings + (
        observation_binding,
        binding_fact_binding,
        closure_binding,
    )
    trace = assemble_product_trace(
        profile=profile,
        trace_ref=f"{base_trace.trace_ref}:post-payment-remediation:{observation_binding.binding_ref[-16:]}",
        events=base_trace.events + (observation_event, binding_event, closure_event),
        source_bindings=source_bindings,
        expected_unique_binding_count=len({item.binding_ref for item in source_bindings}),
    )
    if trace is None:
        return None
    if validate_product_authoritative_trace(trace).status is not TraceValidationStatus.VALID:
        return None
    return trace


__all__ = ["extend_product_authoritative_trace_with_remediation"]

"""Deterministic offline payment and fulfilment sidecar for WebShop evidence."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from .adapters.webshop import WebShopCommerceAdaptation
from .authoritative_trace import ProductAuthoritativeTrace
from .lifecycle import assess_lifecycle
from .models import (
    Decision,
    FulfillmentRecord,
    IntentMandate,
    LifecycleResult,
    PaymentExecutionRecord,
    PaymentRecoveryResult,
    PaymentStatus,
    PaymentStatusObservation,
)
from .payment_recovery import assess_payment_recovery
from .payment_status_conflict import (
    PaymentStatusConflictFact,
    PaymentStatusConflictResolution,
    derive_payment_status_conflict,
)
from .trusted_execution import (
    ExecutionAttemptFact,
    FollowUpAction,
    VerificationStatus,
    check_idempotency,
    verify_original_transaction,
)
from .webshop_runtime_gate import WebShopBuyNowGateOutcome


WEBSHOP_PAYMENT_SIDECAR_LIMITATIONS = (
    "offline_sidecar_only",
    "no_real_payment_execution",
    "no_real_status_query_or_async_callback",
    "no_real_fulfilment",
    "no_automatic_payment_retry",
    "no_real_refund_or_dispute",
    "webshop_reward_not_used_as_payment_or_task_success",
)
_DUPLICATE_BLOCK_ISSUES = frozenset(
    {
        "existing_successful_payment_attempt",
        "unresolved_payment_attempt_exists",
    }
)
_BINDING_FAILURE_PREFIXES = (
    "payment_request_binding_mismatch",
    "payment_order_binding_mismatch",
    "payment_amount_binding_mismatch",
    "payment_currency_binding_mismatch",
    "payment_authority_binding_mismatch",
    "payment_authority_version_binding_mismatch",
    "payment_agent_binding_mismatch",
    "payment_transaction_object_binding_mismatch",
    "payment_payee_binding_mismatch",
    "fulfillment_order_binding_mismatch",
    "fulfillment_service_binding_mismatch",
    "payment_status_observation_",
)


@dataclass(frozen=True)
class WebShopPaymentFulfilmentOutcome:
    """Immutable post-gate projection built only from explicit offline facts."""

    ready: bool
    initial_payment: PaymentExecutionRecord | None
    effective_payment: PaymentExecutionRecord | None
    query_recovery: PaymentRecoveryResult | None
    status_conflict: PaymentStatusConflictFact | None
    lifecycle: LifecycleResult | None
    retry_allowed: bool
    duplicate_payment_blocked: bool
    reason_codes: tuple[str, ...]
    authoritative_trace: ProductAuthoritativeTrace | None = None
    limitations: tuple[str, ...] = WEBSHOP_PAYMENT_SIDECAR_LIMITATIONS

    def to_dict(self) -> dict[str, object]:
        """Return a stable primitive-only representation for M5 and P9-E."""

        return {
            "ready": self.ready,
            "initial_payment": _primitive(self.initial_payment),
            "effective_payment": _primitive(self.effective_payment),
            "query_recovery": _primitive(self.query_recovery),
            "status_conflict": (
                self.status_conflict.to_dict() if self.status_conflict else None
            ),
            "lifecycle": _primitive(self.lifecycle),
            "retry_allowed": self.retry_allowed,
            "duplicate_payment_blocked": self.duplicate_payment_blocked,
            "reason_codes": list(self.reason_codes),
            "limitations": list(self.limitations),
        }


def assess_webshop_payment_fulfilment(
    gate_outcome: WebShopBuyNowGateOutcome | None,
    adaptation: WebShopCommerceAdaptation | None,
    mandate: IntentMandate | None,
    payment: PaymentExecutionRecord | None,
    fulfillment: FulfillmentRecord | None,
    *,
    query_observation: PaymentStatusObservation | None = None,
    async_observation: PaymentStatusObservation | None = None,
    known_attempts: tuple[PaymentExecutionRecord, ...] = (),
) -> WebShopPaymentFulfilmentOutcome:
    """Assess offline post-gate payment, convergence, retry and lifecycle facts.

    The function never invokes a callback, performs a status query, creates a
    payment attempt, or executes fulfilment. All records are caller-supplied.
    """

    prerequisite_reasons = _prerequisite_reasons(
        gate_outcome,
        adaptation,
        mandate,
        payment,
        fulfillment,
    )
    if prerequisite_reasons:
        return WebShopPaymentFulfilmentOutcome(
            ready=False,
            initial_payment=(
                payment if isinstance(payment, PaymentExecutionRecord) else None
            ),
            effective_payment=None,
            query_recovery=None,
            status_conflict=None,
            lifecycle=None,
            retry_allowed=False,
            duplicate_payment_blocked=False,
            reason_codes=prerequisite_reasons,
        )

    assert gate_outcome is not None
    assert gate_outcome.bound_request is not None
    assert adaptation is not None
    assert adaptation.order is not None
    assert mandate is not None
    assert payment is not None
    assert fulfillment is not None

    reasons: list[str] = [
        f"payment:initial_status:{payment.status.value.lower()}",
    ]
    query_recovery: PaymentRecoveryResult | None = None
    status_conflict: PaymentStatusConflictFact | None = None
    effective_status = payment.status
    retry_allowed = False
    duplicate_payment_blocked = False
    evidence_invalid = False

    if query_observation is None:
        related_attempts = _related_known_attempts(payment, known_attempts)
        if any(
            attempt.status is PaymentStatus.SUCCEEDED
            for attempt in related_attempts
        ):
            duplicate_payment_blocked = True
            reasons.extend(
                (
                    "duplicate:known_successful_attempt",
                    "duplicate:payment_blocked",
                )
            )
        elif any(
            attempt.status in {PaymentStatus.UNKNOWN, PaymentStatus.PENDING}
            for attempt in related_attempts
        ):
            duplicate_payment_blocked = True
            reasons.extend(
                (
                    "duplicate:known_unresolved_attempt",
                    "duplicate:payment_blocked",
                )
            )

    if query_observation is not None:
        query_recovery = assess_payment_recovery(
            payment,
            query_observation,
            known_attempts=known_attempts,
            mandate=mandate,
            request=gate_outcome.bound_request,
            order=adaptation.order,
        )
        effective_status = query_recovery.effective_status
        retry_allowed = query_recovery.retry_allowed
        recovery_issue_codes = tuple(issue.code for issue in query_recovery.issues)
        reasons.extend(
            (
                f"recovery:status:{query_recovery.recovery_status.value.lower()}",
                f"recovery:next_action:{query_recovery.next_action}",
                *(f"recovery:{code}" for code in recovery_issue_codes),
            )
        )
        duplicate_payment_blocked = bool(
            _DUPLICATE_BLOCK_ISSUES.intersection(recovery_issue_codes)
        )
        if duplicate_payment_blocked:
            reasons.append("duplicate:payment_blocked")
        if _contains_binding_failure(recovery_issue_codes):
            evidence_invalid = True
            effective_status = PaymentStatus.UNKNOWN
            retry_allowed = False
            reasons.append("sidecar:recovery_binding_invalid")

    if query_observation is not None and async_observation is not None:
        query_binding = verify_original_transaction(
            FollowUpAction.STATUS_QUERY,
            payment,
            query_observation,
        )
        async_binding = verify_original_transaction(
            FollowUpAction.ASYNC_STATUS_NOTIFICATION,
            payment,
            async_observation,
        )
        status_conflict = derive_payment_status_conflict(
            payment,
            query_observation,
            async_observation,
            query_binding,
            async_binding,
        )
        reasons.extend(
            (
                f"conflict:resolution:{status_conflict.resolution.value.lower()}",
                *(f"conflict:{code}" for code in status_conflict.reason_codes),
            )
        )
        effective_status = status_conflict.effective_status
        if status_conflict.resolution in {
            PaymentStatusConflictResolution.BLOCKED,
            PaymentStatusConflictResolution.CONFLICT,
            PaymentStatusConflictResolution.UNRESOLVED,
        }:
            retry_allowed = False
        if status_conflict.resolution is PaymentStatusConflictResolution.BLOCKED:
            evidence_invalid = True
            reasons.append("sidecar:status_evidence_blocked")
        if status_conflict.resolution is PaymentStatusConflictResolution.CONFLICT:
            reasons.append("sidecar:status_evidence_conflict")
        if effective_status is not PaymentStatus.FAILED:
            retry_allowed = False

    elif async_observation is not None:
        async_binding = verify_original_transaction(
            FollowUpAction.ASYNC_STATUS_NOTIFICATION,
            payment,
            async_observation,
        )
        reasons.extend(f"async:{code}" for code in async_binding.reason_codes)
        if async_binding.status is not VerificationStatus.VALID:
            evidence_invalid = True
            effective_status = PaymentStatus.UNKNOWN
            reasons.append("sidecar:async_binding_invalid")
        elif async_observation.observed_at < payment.occurred_at:
            evidence_invalid = True
            effective_status = PaymentStatus.UNKNOWN
            reasons.append("sidecar:async_observation_before_payment")
        else:
            effective_status = async_observation.status
            reasons.append(
                f"async:effective_status:{async_observation.status.value.lower()}"
            )
        retry_allowed = False

    effective_payment = replace(payment, status=effective_status)
    lifecycle = assess_lifecycle(
        gate_outcome.bound_request,
        adaptation.order,
        effective_payment,
        fulfillment,
        mandate=mandate,
    )
    lifecycle_issue_codes = tuple(issue.code for issue in lifecycle.issues)
    reasons.extend(
        (
            f"lifecycle:payment_status:{lifecycle.payment_status.value.lower()}",
            f"lifecycle:fulfillment_status:{lifecycle.fulfillment_status.value.lower()}",
            f"lifecycle:task_status:{lifecycle.task_status.value.lower()}",
            f"lifecycle:remediation:{lifecycle.remediation.status.value.lower()}",
            *(f"lifecycle:{code}" for code in lifecycle_issue_codes),
        )
    )
    if _contains_binding_failure(lifecycle_issue_codes):
        evidence_invalid = True
        retry_allowed = False
        reasons.append("sidecar:lifecycle_binding_invalid")

    if retry_allowed:
        reasons.append("retry:offline_candidate_only")
    else:
        reasons.append("retry:not_allowed")

    base_outcome = WebShopPaymentFulfilmentOutcome(
        ready=not evidence_invalid,
        initial_payment=payment,
        effective_payment=effective_payment,
        query_recovery=query_recovery,
        status_conflict=status_conflict,
        lifecycle=lifecycle,
        retry_allowed=retry_allowed,
        duplicate_payment_blocked=duplicate_payment_blocked,
        reason_codes=_deduplicate(reasons),
    )
    from .webshop_sidecar_trace_toolkit import build_sidecar_product_trace

    authoritative_trace = build_sidecar_product_trace(
        gate_outcome=gate_outcome,
        adaptation=adaptation,
        mandate=mandate,
        fulfillment=fulfillment,
        base_outcome=base_outcome,
    )
    return replace(base_outcome, authoritative_trace=authoritative_trace)


def _prerequisite_reasons(
    gate_outcome: WebShopBuyNowGateOutcome | None,
    adaptation: WebShopCommerceAdaptation | None,
    mandate: IntentMandate | None,
    payment: PaymentExecutionRecord | None,
    fulfillment: FulfillmentRecord | None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if gate_outcome is None:
        reasons.append("prerequisite:gate_outcome_missing")
    else:
        if gate_outcome.decision is not Decision.ALLOW:
            reasons.append("prerequisite:gate_decision_not_allow")
        if not gate_outcome.checkout_executed:
            reasons.append("prerequisite:checkout_not_executed")
        if gate_outcome.callback_count != 1:
            reasons.append("prerequisite:callback_count_not_one")
        if gate_outcome.bound_request is None:
            reasons.append("prerequisite:bound_request_missing")
        if gate_outcome.runtime_gate_record is None:
            reasons.append("prerequisite:runtime_gate_record_missing")
        elif gate_outcome.runtime_gate_record.final_decision is not Decision.ALLOW:
            reasons.append("prerequisite:runtime_gate_not_allow")
    if adaptation is None:
        reasons.append("prerequisite:adaptation_missing")
    else:
        if not adaptation.ready:
            reasons.append("prerequisite:adaptation_not_ready")
        if adaptation.order is None:
            reasons.append("prerequisite:order_missing")
        if adaptation.payment_request is None:
            reasons.append("prerequisite:transaction_request_missing")
    if mandate is None:
        reasons.append("prerequisite:mandate_missing")
    if payment is None:
        reasons.append("prerequisite:payment_missing")
    if fulfillment is None:
        reasons.append("prerequisite:fulfillment_missing")
    if (
        gate_outcome is not None
        and gate_outcome.bound_request is not None
        and adaptation is not None
        and adaptation.payment_request is not None
        and gate_outcome.bound_request
        != replace(
            adaptation.payment_request,
            agent_id=gate_outcome.bound_request.agent_id,
        )
    ):
        reasons.append("prerequisite:adapter_gate_request_mismatch")
    return _deduplicate(reasons)


def _related_known_attempts(
    payment: PaymentExecutionRecord,
    known_attempts: tuple[PaymentExecutionRecord, ...],
) -> tuple[PaymentExecutionRecord, ...]:
    attempt_facts = tuple(
        ExecutionAttemptFact(
            execution_id=attempt.payment_id,
            request_id=attempt.request_id,
            status=attempt.status.value,
            idempotency_key=attempt.idempotency_key,
        )
        for attempt in known_attempts
    )
    idempotency_fact = check_idempotency(
        idempotency_key=payment.idempotency_key,
        request_id=payment.request_id,
        current_execution_id=payment.payment_id,
        known_attempts=attempt_facts,
    )
    related_execution_ids = {
        attempt.execution_id for attempt in idempotency_fact.related_attempts
    }
    return tuple(
        attempt
        for attempt in known_attempts
        if attempt.payment_id in related_execution_ids
    )


def _contains_binding_failure(codes: tuple[str, ...]) -> bool:
    return any(
        code.startswith(prefix)
        for code in codes
        for prefix in _BINDING_FAILURE_PREFIXES
    )


def _deduplicate(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _primitive(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return {
            field.name: _primitive(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, dict):
        return {
            str(key): _primitive(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_primitive(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [_primitive(item) for item in sorted(value, key=str)]
    raise TypeError(f"unsupported sidecar serialization type: {type(value).__name__}")

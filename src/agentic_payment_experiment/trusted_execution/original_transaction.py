"""Protocol-neutral binding checks for offline post-payment observations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..models import (
    DisputeRecord,
    PaymentExecutionRecord,
    PaymentStatusObservation,
    RefundRecord,
)
from .execution_facts import VerificationStatus


class FollowUpAction(str, Enum):
    """Closed set of follow-up actions that bind to an original payment."""

    STATUS_QUERY = "STATUS_QUERY"
    ASYNC_STATUS_NOTIFICATION = "ASYNC_STATUS_NOTIFICATION"
    REFUND = "REFUND"
    DISPUTE = "DISPUTE"


@dataclass(frozen=True)
class OriginalTransactionBindingFact:
    action: FollowUpAction
    status: VerificationStatus
    reason_codes: tuple[str, ...]
    original_payment_ref: str | None
    original_order_ref: str | None
    follow_up_payment_ref: str | None
    follow_up_order_ref: str | None


def verify_original_transaction(
    action: FollowUpAction | str,
    original: PaymentExecutionRecord | None,
    follow_up: PaymentStatusObservation | RefundRecord | DisputeRecord | None,
) -> OriginalTransactionBindingFact:
    """Bind one offline follow-up fact to the original payment.

    Query and asynchronous status observations additionally bind the provider
    reference whenever the original payment exposes one. Unknown actions and
    missing references fail closed with stable reason codes.
    """

    try:
        parsed = action if isinstance(action, FollowUpAction) else FollowUpAction(action)
    except (TypeError, ValueError):
        return OriginalTransactionBindingFact(
            FollowUpAction.STATUS_QUERY,
            VerificationStatus.INVALID,
            ("original_transaction_action_unsupported",),
            None,
            None,
            None,
            None,
        )

    original_payment_ref, original_order_ref = (
        (original.payment_id, original.order_id) if original else (None, None)
    )
    follow_up_payment_ref = getattr(follow_up, "payment_id", None)
    follow_up_order_ref = getattr(follow_up, "order_id", None)

    required_refs = (
        original_payment_ref,
        original_order_ref,
        follow_up_payment_ref,
        follow_up_order_ref,
    )
    if not all(str(value or "").strip() for value in required_refs):
        return OriginalTransactionBindingFact(
            parsed,
            VerificationStatus.MISSING_EVIDENCE,
            ("original_transaction_required_reference_missing",),
            original_payment_ref,
            original_order_ref,
            follow_up_payment_ref,
            follow_up_order_ref,
        )

    reasons: list[str] = []
    if follow_up_payment_ref != original_payment_ref:
        reasons.append("original_transaction_payment_ref_mismatch")
    if follow_up_order_ref != original_order_ref:
        reasons.append("original_transaction_order_ref_mismatch")

    status_observation_actions = {
        FollowUpAction.STATUS_QUERY,
        FollowUpAction.ASYNC_STATUS_NOTIFICATION,
    }
    if parsed in status_observation_actions and original and original.provider_ref:
        provider_ref = getattr(follow_up, "provider_ref", None)
        if not str(provider_ref or "").strip():
            reasons.append("original_transaction_provider_ref_missing")
        elif provider_ref != original.provider_ref:
            reasons.append("original_transaction_provider_ref_mismatch")

    return OriginalTransactionBindingFact(
        parsed,
        VerificationStatus.INVALID if reasons else VerificationStatus.VALID,
        tuple(reasons) if reasons else ("original_transaction_binding_match",),
        original_payment_ref,
        original_order_ref,
        follow_up_payment_ref,
        follow_up_order_ref,
    )

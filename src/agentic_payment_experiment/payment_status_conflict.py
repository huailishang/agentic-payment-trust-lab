"""Offline convergence facts for execution, query, and async payment statuses.

The module classifies evidence only. It never executes a payment or retry, and
it does not claim fulfilment, business success, reconciliation, settlement, or
legal finality.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from itertools import groupby

from .models import PaymentExecutionRecord, PaymentStatus, PaymentStatusObservation
from .trusted_execution.execution_facts import VerificationStatus
from .trusted_execution.original_transaction import (
    FollowUpAction,
    OriginalTransactionBindingFact,
)


class PaymentStatusConflictResolution(str, Enum):
    """Closed classification for one three-channel status evidence chain."""

    BLOCKED = "BLOCKED"
    CONFLICT = "CONFLICT"
    UNRESOLVED = "UNRESOLVED"
    MONOTONIC_CONFIRMATION = "MONOTONIC_CONFIRMATION"
    CONSISTENT = "CONSISTENT"


@dataclass(frozen=True)
class PaymentStatusConflictFact:
    """Immutable, protocol-neutral status convergence fact."""

    resolution: PaymentStatusConflictResolution
    initial_status: PaymentStatus
    query_status: PaymentStatus
    query_observed_at: datetime | None
    async_status: PaymentStatus
    async_observed_at: datetime | None
    effective_status: PaymentStatus
    effective_status_terminal: bool
    reason_codes: tuple[str, ...]
    business_success_confirmed: bool = False
    fulfillment_confirmed: bool = False
    user_task_success_confirmed: bool = False
    reconciliation_confirmed: bool = False
    settlement_confirmed: bool = False
    legal_finality_confirmed: bool = False

    def to_dict(self) -> dict[str, object]:
        """Return a stable representation containing primitives only."""

        return {
            "resolution": self.resolution.value,
            "initial_status": self.initial_status.value,
            "query_status": self.query_status.value,
            "query_observed_at": _serialize_time(self.query_observed_at),
            "async_status": self.async_status.value,
            "async_observed_at": _serialize_time(self.async_observed_at),
            "effective_status": self.effective_status.value,
            "effective_status_terminal": self.effective_status_terminal,
            "reason_codes": list(self.reason_codes),
            "business_success_confirmed": self.business_success_confirmed,
            "fulfillment_confirmed": self.fulfillment_confirmed,
            "user_task_success_confirmed": self.user_task_success_confirmed,
            "reconciliation_confirmed": self.reconciliation_confirmed,
            "settlement_confirmed": self.settlement_confirmed,
            "legal_finality_confirmed": self.legal_finality_confirmed,
        }


def derive_payment_status_conflict(
    payment: PaymentExecutionRecord,
    query_observation: PaymentStatusObservation,
    async_observation: PaymentStatusObservation,
    query_binding: OriginalTransactionBindingFact,
    async_binding: OriginalTransactionBindingFact,
) -> PaymentStatusConflictFact:
    """Classify query/async status evidence bound to one original payment.

    Invalid types, enums, bindings, or temporal evidence produce ``BLOCKED``.
    Contradictory terminal claims and terminal regressions produce ``CONFLICT``.
    No branch performs a payment, retry, reconciliation, or business decision.
    """

    blocked_reasons = _validate_inputs(
        payment,
        query_observation,
        async_observation,
        query_binding,
        async_binding,
    )
    if blocked_reasons:
        return _fact(
            PaymentStatusConflictResolution.BLOCKED,
            payment,
            query_observation,
            async_observation,
            PaymentStatus.UNKNOWN,
            False,
            blocked_reasons,
        )

    try:
        if query_observation.observed_at < payment.occurred_at:
            blocked_reasons.append("payment_status_query_before_execution")
        if async_observation.observed_at < payment.occurred_at:
            blocked_reasons.append("payment_status_async_before_execution")
    except TypeError:
        blocked_reasons.append("payment_status_timestamp_incomparable")

    if blocked_reasons:
        return _fact(
            PaymentStatusConflictResolution.BLOCKED,
            payment,
            query_observation,
            async_observation,
            PaymentStatus.UNKNOWN,
            False,
            blocked_reasons,
        )

    timeline = (
        (payment.occurred_at, "initial", payment.status),
        (query_observation.observed_at, "query", query_observation.status),
        (async_observation.observed_at, "async", async_observation.status),
    )
    ordered = sorted(timeline, key=lambda item: (item[0], item[1]))

    collapsed: list[PaymentStatus] = []
    for _, same_time_events in groupby(ordered, key=lambda item: item[0]):
        group = tuple(same_time_events)
        statuses = {event[2] for event in group}
        if len(statuses) > 1:
            return _fact(
                PaymentStatusConflictResolution.CONFLICT,
                payment,
                query_observation,
                async_observation,
                PaymentStatus.UNKNOWN,
                False,
                ["payment_status_equal_time_disagreement"],
            )
        collapsed.append(group[0][2])

    terminal_statuses = {
        status for status in collapsed if status in _TERMINAL_STATUSES
    }
    if len(terminal_statuses) > 1:
        return _fact(
            PaymentStatusConflictResolution.CONFLICT,
            payment,
            query_observation,
            async_observation,
            PaymentStatus.UNKNOWN,
            False,
            ["payment_status_opposite_terminal_claims"],
        )

    terminal_seen = False
    for status in collapsed:
        if status in _TERMINAL_STATUSES:
            terminal_seen = True
        elif terminal_seen:
            return _fact(
                PaymentStatusConflictResolution.CONFLICT,
                payment,
                query_observation,
                async_observation,
                PaymentStatus.UNKNOWN,
                False,
                ["payment_status_terminal_to_unresolved_regression"],
            )

    effective_status = collapsed[-1]
    if effective_status not in _TERMINAL_STATUSES:
        return _fact(
            PaymentStatusConflictResolution.UNRESOLVED,
            payment,
            query_observation,
            async_observation,
            effective_status,
            False,
            ["payment_status_unresolved"],
        )

    initial_was_unresolved = payment.status in _UNRESOLVED_STATUSES
    if initial_was_unresolved:
        return _fact(
            PaymentStatusConflictResolution.MONOTONIC_CONFIRMATION,
            payment,
            query_observation,
            async_observation,
            effective_status,
            True,
            ["payment_status_monotonic_terminal_confirmation"],
        )

    return _fact(
        PaymentStatusConflictResolution.CONSISTENT,
        payment,
        query_observation,
        async_observation,
        effective_status,
        True,
        ["payment_status_matching_terminal_observations"],
    )


_TERMINAL_STATUSES = frozenset({PaymentStatus.SUCCEEDED, PaymentStatus.FAILED})
_UNRESOLVED_STATUSES = frozenset({PaymentStatus.UNKNOWN, PaymentStatus.PENDING})


def _validate_inputs(
    payment: object,
    query_observation: object,
    async_observation: object,
    query_binding: object,
    async_binding: object,
) -> list[str]:
    reasons: list[str] = []

    if not isinstance(payment, PaymentExecutionRecord):
        reasons.append("payment_status_payment_input_invalid")
    if not isinstance(query_observation, PaymentStatusObservation):
        reasons.append("payment_status_query_input_invalid")
    if not isinstance(async_observation, PaymentStatusObservation):
        reasons.append("payment_status_async_input_invalid")

    if isinstance(payment, PaymentExecutionRecord):
        if not isinstance(payment.status, PaymentStatus):
            reasons.append("payment_status_initial_status_invalid")
        if not isinstance(payment.occurred_at, datetime):
            reasons.append("payment_status_execution_time_invalid")
    if isinstance(query_observation, PaymentStatusObservation):
        if not isinstance(query_observation.status, PaymentStatus):
            reasons.append("payment_status_query_status_invalid")
        if not isinstance(query_observation.observed_at, datetime):
            reasons.append("payment_status_query_time_invalid")
    if isinstance(async_observation, PaymentStatusObservation):
        if not isinstance(async_observation.status, PaymentStatus):
            reasons.append("payment_status_async_status_invalid")
        if not isinstance(async_observation.observed_at, datetime):
            reasons.append("payment_status_async_time_invalid")

    if (
        isinstance(payment, PaymentExecutionRecord)
        and isinstance(query_observation, PaymentStatusObservation)
        and not _binding_is_valid(
            query_binding,
            FollowUpAction.STATUS_QUERY,
            payment,
            query_observation,
        )
    ):
        reasons.append("payment_status_query_binding_invalid")
    elif not isinstance(query_binding, OriginalTransactionBindingFact):
        reasons.append("payment_status_query_binding_invalid")

    if (
        isinstance(payment, PaymentExecutionRecord)
        and isinstance(async_observation, PaymentStatusObservation)
        and not _binding_is_valid(
            async_binding,
            FollowUpAction.ASYNC_STATUS_NOTIFICATION,
            payment,
            async_observation,
        )
    ):
        reasons.append("payment_status_async_binding_invalid")
    elif not isinstance(async_binding, OriginalTransactionBindingFact):
        reasons.append("payment_status_async_binding_invalid")

    return _deduplicate(reasons)


def _binding_is_valid(
    binding: object,
    expected_action: FollowUpAction,
    payment: PaymentExecutionRecord,
    observation: PaymentStatusObservation,
) -> bool:
    if not isinstance(binding, OriginalTransactionBindingFact):
        return False
    if binding.action is not expected_action or binding.status is not VerificationStatus.VALID:
        return False
    if (
        binding.original_payment_ref != payment.payment_id
        or binding.original_order_ref != payment.order_id
        or binding.follow_up_payment_ref != observation.payment_id
        or binding.follow_up_order_ref != observation.order_id
        or observation.payment_id != payment.payment_id
        or observation.order_id != payment.order_id
    ):
        return False
    if payment.provider_ref:
        return observation.provider_ref == payment.provider_ref
    return True


def _fact(
    resolution: PaymentStatusConflictResolution,
    payment: object,
    query_observation: object,
    async_observation: object,
    effective_status: PaymentStatus,
    terminal: bool,
    reason_codes: list[str],
) -> PaymentStatusConflictFact:
    return PaymentStatusConflictFact(
        resolution=resolution,
        initial_status=_safe_status(payment),
        query_status=_safe_status(query_observation),
        query_observed_at=_safe_time(query_observation, "observed_at"),
        async_status=_safe_status(async_observation),
        async_observed_at=_safe_time(async_observation, "observed_at"),
        effective_status=effective_status,
        effective_status_terminal=terminal,
        reason_codes=tuple(_deduplicate(reason_codes)),
    )


def _safe_status(value: object) -> PaymentStatus:
    status = getattr(value, "status", None)
    return status if isinstance(status, PaymentStatus) else PaymentStatus.UNKNOWN


def _safe_time(value: object, attribute: str) -> datetime | None:
    observed = getattr(value, attribute, None)
    return observed if isinstance(observed, datetime) else None


def _serialize_time(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _deduplicate(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))

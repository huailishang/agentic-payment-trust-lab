"""Offline facts for the finality of a queried payment status.

This module deliberately describes only a status observation that has been
bound to one original payment.  It does not turn a payment status into an HTTP
acceptance, fulfilment, business-success, reconciliation, settlement, or legal
finality assertion.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import (
    PaymentExecutionRecord,
    PaymentRecoveryResult,
    PaymentRecoveryStatus,
    PaymentStatus,
    PaymentStatusObservation,
)


class PaymentQueryEvidenceStage(str, Enum):
    """Closed set of evidence states for a payment status query."""

    INITIAL_ONLY = "INITIAL_ONLY"
    QUERY_CONFIRMED = "QUERY_CONFIRMED"
    QUERY_UNRESOLVED = "QUERY_UNRESOLVED"
    QUERY_BLOCKED = "QUERY_BLOCKED"


@dataclass(frozen=True)
class PaymentQueryFinalityFact:
    """A deterministic, deliberately narrow fact about one payment query."""

    evidence_stage: PaymentQueryEvidenceStage
    initial_status: PaymentStatus
    queried_status: PaymentStatus
    effective_status: PaymentStatus
    effective_status_terminal: bool
    business_success_confirmed: bool = False
    fulfillment_confirmed: bool = False
    user_task_success_confirmed: bool = False
    reconciliation_confirmed: bool = False
    settlement_confirmed: bool = False
    legal_finality_confirmed: bool = False

    def to_dict(self) -> dict[str, str | bool]:
        """Return a stable primitive-only representation for result cards."""

        return {
            "evidence_stage": self.evidence_stage.value,
            "initial_status": self.initial_status.value,
            "queried_status": self.queried_status.value,
            "effective_status": self.effective_status.value,
            "effective_status_terminal": self.effective_status_terminal,
            "business_success_confirmed": self.business_success_confirmed,
            "fulfillment_confirmed": self.fulfillment_confirmed,
            "user_task_success_confirmed": self.user_task_success_confirmed,
            "reconciliation_confirmed": self.reconciliation_confirmed,
            "settlement_confirmed": self.settlement_confirmed,
            "legal_finality_confirmed": self.legal_finality_confirmed,
        }


def derive_payment_query_finality(
    payment: PaymentExecutionRecord,
    observation: PaymentStatusObservation,
    recovery: PaymentRecoveryResult,
) -> PaymentQueryFinalityFact:
    """Derive a fact only from the original payment, its query, and recovery.

    Invalid object or enum combinations raise ``ValueError`` rather than being
    coerced.  A blocked or unresolved recovery never becomes terminal merely
    because one of its status fields happens to be terminal.
    """

    _validate_inputs(payment, observation, recovery)
    if recovery.recovery_status is PaymentRecoveryStatus.BLOCKED:
        stage = PaymentQueryEvidenceStage.QUERY_BLOCKED
    elif recovery.effective_status in {PaymentStatus.UNKNOWN, PaymentStatus.PENDING}:
        stage = PaymentQueryEvidenceStage.QUERY_UNRESOLVED
    elif (
        recovery.recovery_status
        in {PaymentRecoveryStatus.RECOVERED, PaymentRecoveryStatus.RETRY_CANDIDATE}
        and recovery.effective_status is recovery.observed_status
        and recovery.effective_status in {PaymentStatus.SUCCEEDED, PaymentStatus.FAILED}
    ):
        stage = PaymentQueryEvidenceStage.QUERY_CONFIRMED
    else:
        stage = PaymentQueryEvidenceStage.INITIAL_ONLY

    terminal = (
        stage is PaymentQueryEvidenceStage.QUERY_CONFIRMED
        and recovery.effective_status in {PaymentStatus.SUCCEEDED, PaymentStatus.FAILED}
    )
    return PaymentQueryFinalityFact(
        evidence_stage=stage,
        initial_status=payment.status,
        queried_status=observation.status,
        effective_status=recovery.effective_status,
        effective_status_terminal=terminal,
    )


def _validate_inputs(
    payment: PaymentExecutionRecord,
    observation: PaymentStatusObservation,
    recovery: PaymentRecoveryResult,
) -> None:
    if not isinstance(payment, PaymentExecutionRecord):
        raise ValueError("payment must be a PaymentExecutionRecord")
    if not isinstance(observation, PaymentStatusObservation):
        raise ValueError("observation must be a PaymentStatusObservation")
    if not isinstance(recovery, PaymentRecoveryResult):
        raise ValueError("recovery must be a PaymentRecoveryResult")
    statuses = (
        payment.status,
        observation.status,
        recovery.initial_status,
        recovery.observed_status,
        recovery.effective_status,
    )
    if any(not isinstance(status, PaymentStatus) for status in statuses):
        raise ValueError("payment-query statuses must use PaymentStatus")
    if not isinstance(recovery.recovery_status, PaymentRecoveryStatus):
        raise ValueError("recovery status must use PaymentRecoveryStatus")
    if payment.status is not recovery.initial_status:
        raise ValueError("recovery initial status must match the original payment")
    if observation.status is not recovery.observed_status:
        raise ValueError("recovery observed status must match the bound observation")

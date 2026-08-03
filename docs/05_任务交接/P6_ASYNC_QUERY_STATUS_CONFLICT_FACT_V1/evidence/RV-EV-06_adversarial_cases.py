from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from agentic_payment_experiment import (
    PaymentExecutionRecord,
    PaymentStatus,
    PaymentStatusConflictResolution,
    PaymentStatusObservation,
    derive_payment_status_conflict,
)
from agentic_payment_experiment.trusted_execution import (
    FollowUpAction,
    VerificationStatus,
    verify_original_transaction,
)

T0 = datetime(2026, 8, 1, tzinfo=timezone.utc)
PAYMENT = PaymentExecutionRecord(
    payment_id="pay-1",
    request_id="req-1",
    order_id="order-1",
    status=PaymentStatus.UNKNOWN,
    amount=Decimal("10.00"),
    currency="CNY",
    occurred_at=T0,
    provider_ref="provider-1",
)


def obs(
    status: PaymentStatus,
    *,
    minute: int,
    payment_id: str = "pay-1",
    order_id: str = "order-1",
    provider_ref: str | None = "provider-1",
) -> PaymentStatusObservation:
    return PaymentStatusObservation(
        payment_id=payment_id,
        order_id=order_id,
        status=status,
        observed_at=T0 + timedelta(minutes=minute),
        source="evaluator-offline-fixture",
        provider_ref=provider_ref,
    )


def assert_invalid_async(observation: PaymentStatusObservation, expected_reason: str) -> None:
    fact = verify_original_transaction(
        FollowUpAction.ASYNC_STATUS_NOTIFICATION,
        PAYMENT,
        observation,
    )
    assert fact.status is VerificationStatus.INVALID or fact.status is VerificationStatus.MISSING_EVIDENCE
    assert expected_reason in fact.reason_codes, fact


assert_invalid_async(obs(PaymentStatus.PENDING, minute=1, payment_id=""), "original_transaction_required_reference_missing")
assert_invalid_async(obs(PaymentStatus.PENDING, minute=1, order_id=""), "original_transaction_required_reference_missing")
assert_invalid_async(obs(PaymentStatus.PENDING, minute=1, payment_id="pay-x"), "original_transaction_payment_ref_mismatch")
assert_invalid_async(obs(PaymentStatus.PENDING, minute=1, order_id="order-x"), "original_transaction_order_ref_mismatch")
assert_invalid_async(obs(PaymentStatus.PENDING, minute=1, provider_ref=None), "original_transaction_provider_ref_missing")
assert_invalid_async(obs(PaymentStatus.PENDING, minute=1, provider_ref="provider-x"), "original_transaction_provider_ref_mismatch")

unknown = verify_original_transaction("REVERSAL", PAYMENT, obs(PaymentStatus.PENDING, minute=1))
assert unknown.status is VerificationStatus.INVALID
assert unknown.reason_codes == ("original_transaction_action_unsupported",)

query = obs(PaymentStatus.PENDING, minute=1)
async_observation = obs(PaymentStatus.SUCCEEDED, minute=2)
query_binding = verify_original_transaction(FollowUpAction.STATUS_QUERY, PAYMENT, query)
async_binding = verify_original_transaction(
    FollowUpAction.ASYNC_STATUS_NOTIFICATION,
    PAYMENT,
    async_observation,
)
fact = derive_payment_status_conflict(
    PAYMENT,
    query,
    async_observation,
    query_binding,
    async_binding,
)
assert fact.resolution is PaymentStatusConflictResolution.MONOTONIC_CONFIRMATION
assert fact.effective_status is PaymentStatus.SUCCEEDED
assert fact.effective_status_terminal is True
assert not any(
    (
        fact.business_success_confirmed,
        fact.fulfillment_confirmed,
        fact.user_task_success_confirmed,
        fact.reconciliation_confirmed,
        fact.settlement_confirmed,
        fact.legal_finality_confirmed,
    )
)

wrong_action_binding = replace(async_binding, action=FollowUpAction.STATUS_QUERY)
blocked = derive_payment_status_conflict(
    PAYMENT,
    query,
    async_observation,
    query_binding,
    wrong_action_binding,
)
assert blocked.resolution is PaymentStatusConflictResolution.BLOCKED
assert blocked.effective_status is PaymentStatus.UNKNOWN
assert blocked.effective_status_terminal is False

same_time_conflict = derive_payment_status_conflict(
    PAYMENT,
    obs(PaymentStatus.PENDING, minute=1),
    obs(PaymentStatus.SUCCEEDED, minute=1),
    verify_original_transaction(FollowUpAction.STATUS_QUERY, PAYMENT, obs(PaymentStatus.PENDING, minute=1)),
    verify_original_transaction(
        FollowUpAction.ASYNC_STATUS_NOTIFICATION,
        PAYMENT,
        obs(PaymentStatus.SUCCEEDED, minute=1),
    ),
)
assert same_time_conflict.resolution is PaymentStatusConflictResolution.CONFLICT
assert same_time_conflict.effective_status_terminal is False

print("adversarial_cases=PASS")
print("missing_payment_ref=PASS")
print("missing_order_ref=PASS")
print("mismatched_payment_order_provider=PASS")
print("unknown_action_reason=PASS")
print("wrong_action_binding=BLOCKED")
print("stronger_success_flags=false")

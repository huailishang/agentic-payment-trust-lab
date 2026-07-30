"""P2 protocol-neutral facts for Order -> Request -> Execution binding.

The verifier only reports whether the supplied references and critical payment
facts form one continuous chain.  It does not decide whether a payment should
run and it never invokes a payment side effect.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from .execution_facts import VerificationStatus


class _AuthorityLike(Protocol):
    mandate_id: str
    authority_version: str
    expected_agent_id: str | None


class _OrderLike(Protocol):
    order_id: str
    mandate_ref: str
    authority_version_ref: str | None
    merchant: str
    payee: str
    total_amount: Decimal
    currency: str


class _RequestLike(Protocol):
    request_id: str
    order_ref: str | None
    authority_ref: str | None
    authority_version_ref: str | None
    agent_id: str | None
    merchant: str
    payee: str | None
    amount: Decimal
    currency: str
    occurred_at: datetime


class _ExecutionLike(Protocol):
    payment_id: str
    request_id: str
    order_id: str
    transaction_object_ref: str | None
    authority_ref: str | None
    agent_ref: str | None
    payee: str | None
    amount: Decimal
    currency: str
    occurred_at: datetime


@dataclass(frozen=True)
class PaymentExecutionBindingFact:
    """Deterministic P2 result produced immediately before payment execution."""

    status: VerificationStatus
    reason_codes: tuple[str, ...]
    authority_ref: str | None
    authority_version: str | None
    order_ref: str | None
    request_ref: str | None
    execution_ref: str | None
    checked_at: datetime | None


def verify_payment_execution_binding(
    mandate: _AuthorityLike | None,
    order: _OrderLike | None,
    request: _RequestLike | None,
    execution: _ExecutionLike | None,
) -> PaymentExecutionBindingFact:
    """Verify the P2 continuous binding without choosing a payment action."""

    if mandate is None or order is None or request is None or execution is None:
        missing_objects = tuple(
            reason
            for value, reason in (
                (mandate, "payment_authority_missing"),
                (order, "payment_order_missing"),
                (request, "payment_request_missing"),
                (execution, "payment_execution_missing"),
            )
            if value is None
        )
        return _fact(
            VerificationStatus.MISSING_EVIDENCE,
            missing_objects,
            mandate,
            order,
            request,
            execution,
        )

    missing_fields = tuple(
        reason
        for value, reason in (
            (mandate.mandate_id, "payment_authority_ref_missing"),
            (mandate.authority_version, "payment_authority_version_missing"),
            (mandate.expected_agent_id, "payment_expected_agent_ref_missing"),
            (order.order_id, "payment_order_ref_missing"),
            (order.mandate_ref, "payment_order_authority_ref_missing"),
            (
                order.authority_version_ref,
                "payment_order_authority_version_ref_missing",
            ),
            (order.payee, "payment_order_payee_missing"),
            (request.request_id, "payment_request_ref_missing"),
            (request.order_ref, "payment_request_order_ref_missing"),
            (request.authority_ref, "payment_request_authority_ref_missing"),
            (
                request.authority_version_ref,
                "payment_request_authority_version_ref_missing",
            ),
            (request.agent_id, "payment_request_agent_ref_missing"),
            (request.payee, "payment_request_payee_missing"),
            (execution.payment_id, "payment_execution_ref_missing"),
            (execution.request_id, "payment_execution_request_ref_missing"),
            (execution.order_id, "payment_execution_order_ref_missing"),
            (
                execution.transaction_object_ref,
                "payment_execution_transaction_object_ref_missing",
            ),
            (
                execution.authority_ref,
                "payment_execution_authority_ref_missing",
            ),
            (execution.agent_ref, "payment_execution_agent_ref_missing"),
            (execution.payee, "payment_execution_payee_missing"),
        )
        if not str(value or "").strip()
    )
    if missing_fields:
        return _fact(
            VerificationStatus.MISSING_EVIDENCE,
            missing_fields,
            mandate,
            order,
            request,
            execution,
        )

    reasons: list[str] = []
    checks = (
        (
            order.mandate_ref != mandate.mandate_id,
            "payment_order_authority_ref_mismatch",
        ),
        (
            order.authority_version_ref != mandate.authority_version,
            "payment_order_authority_version_ref_mismatch",
        ),
        (
            request.order_ref != order.order_id,
            "payment_request_order_ref_mismatch",
        ),
        (
            request.authority_ref != mandate.mandate_id,
            "payment_request_authority_ref_mismatch",
        ),
        (
            request.authority_version_ref != mandate.authority_version,
            "payment_request_authority_version_ref_mismatch",
        ),
        (
            request.agent_id != mandate.expected_agent_id,
            "payment_request_agent_ref_mismatch",
        ),
        (
            request.merchant != order.merchant,
            "payment_request_merchant_mismatch",
        ),
        (
            request.payee != order.payee,
            "payment_request_payee_mismatch",
        ),
        (
            request.amount != order.total_amount,
            "payment_request_amount_mismatch",
        ),
        (
            request.currency != order.currency,
            "payment_request_currency_mismatch",
        ),
        (
            execution.request_id != request.request_id,
            "payment_execution_request_ref_mismatch",
        ),
        (
            execution.transaction_object_ref != request.request_id,
            "payment_execution_transaction_object_ref_mismatch",
        ),
        (
            execution.order_id != request.order_ref,
            "payment_execution_order_ref_mismatch",
        ),
        (
            execution.authority_ref != request.authority_ref,
            "payment_execution_authority_ref_mismatch",
        ),
        (
            execution.agent_ref != request.agent_id,
            "payment_execution_agent_ref_mismatch",
        ),
        (
            execution.payee != request.payee,
            "payment_execution_payee_mismatch",
        ),
        (
            execution.amount != request.amount,
            "payment_execution_amount_mismatch",
        ),
        (
            execution.currency != request.currency,
            "payment_execution_currency_mismatch",
        ),
        (
            execution.payment_id
            in {request.request_id, order.order_id},
            "payment_execution_reference_collision",
        ),
        (
            execution.occurred_at < request.occurred_at,
            "payment_execution_before_request",
        ),
    )
    reasons.extend(reason for failed, reason in checks if failed)
    if reasons:
        return _fact(
            VerificationStatus.INVALID,
            tuple(reasons),
            mandate,
            order,
            request,
            execution,
        )
    return _fact(
        VerificationStatus.VALID,
        ("payment_execution_binding_match",),
        mandate,
        order,
        request,
        execution,
    )


def _fact(
    status: VerificationStatus,
    reasons: tuple[str, ...],
    mandate: _AuthorityLike | None,
    order: _OrderLike | None,
    request: _RequestLike | None,
    execution: _ExecutionLike | None,
) -> PaymentExecutionBindingFact:
    return PaymentExecutionBindingFact(
        status=status,
        reason_codes=reasons,
        authority_ref=mandate.mandate_id if mandate is not None else None,
        authority_version=mandate.authority_version if mandate is not None else None,
        order_ref=order.order_id if order is not None else None,
        request_ref=request.request_id if request is not None else None,
        execution_ref=execution.payment_id if execution is not None else None,
        checked_at=(
            execution.occurred_at
            if execution is not None
            else request.occurred_at
            if request is not None
            else None
        ),
    )

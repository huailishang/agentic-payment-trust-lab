"""Payment-domain mapping and fail-closed gate for P2 continuous binding."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .models import (
    Decision,
    EvidenceRef,
    IntentMandate,
    Order,
    PaymentExecutionRecord,
    TransactionRequest,
    ValidationIssue,
)
from .trusted_execution import (
    PaymentExecutionBindingFact,
    VerificationStatus,
    verify_payment_execution_binding,
)


@dataclass(frozen=True)
class PaymentExecutionGateOutcome:
    """Payment-domain decision with the callback gated on the full P2 chain."""

    decision: Decision
    binding_fact: PaymentExecutionBindingFact
    executed: bool
    execution_result: Any | None = None


def execute_with_payment_binding_gate(
    prepayment_decision: Decision,
    mandate: IntentMandate | None,
    order: Order | None,
    request: TransactionRequest | None,
    execution: PaymentExecutionRecord | None,
    execute_payment: Callable[[], Any],
) -> PaymentExecutionGateOutcome:
    """Re-verify P2 facts and invoke the callback only after every gate passes."""

    fact = verify_payment_execution_binding(mandate, order, request, execution)
    if prepayment_decision is not Decision.ALLOW:
        return PaymentExecutionGateOutcome(prepayment_decision, fact, False)
    if fact.status is VerificationStatus.MISSING_EVIDENCE:
        return PaymentExecutionGateOutcome(Decision.INDETERMINATE, fact, False)
    if fact.status is VerificationStatus.INVALID:
        return PaymentExecutionGateOutcome(Decision.DENY, fact, False)
    return PaymentExecutionGateOutcome(
        Decision.ALLOW,
        fact,
        True,
        execute_payment(),
    )


def payment_execution_binding_evidence(
    fact: PaymentExecutionBindingFact,
    mandate: IntentMandate | None,
    order: Order | None,
    request: TransactionRequest | None,
    execution: PaymentExecutionRecord | None,
) -> tuple[EvidenceRef, ...]:
    """Create replayable evidence for the two P2 binding edges."""

    missing = "<missing>"
    return (
        EvidenceRef(
            "payment_execution_binding_status",
            "trusted_execution.payment_execution_binding.status",
            fact.status.value,
            VerificationStatus.VALID.value,
        ),
        EvidenceRef(
            "payment_execution_binding_reasons",
            "trusted_execution.payment_execution_binding.reason_codes",
            ",".join(fact.reason_codes),
        ),
        EvidenceRef(
            "payment_authority_ref",
            "payment.authority_ref",
            execution.authority_ref
            if execution is not None and execution.authority_ref is not None
            else missing,
            mandate.mandate_id if mandate is not None else missing,
        ),
        EvidenceRef(
            "payment_authority_version_ref",
            "request.authority_version_ref",
            request.authority_version_ref
            if request is not None and request.authority_version_ref is not None
            else missing,
            mandate.authority_version if mandate is not None else missing,
        ),
        EvidenceRef(
            "payment_request_order_ref",
            "request.order_ref",
            request.order_ref
            if request is not None and request.order_ref is not None
            else missing,
            order.order_id if order is not None else missing,
        ),
        EvidenceRef(
            "payment_execution_request_ref",
            "payment.request_id",
            execution.request_id if execution is not None else missing,
            request.request_id if request is not None else missing,
        ),
        EvidenceRef(
            "payment_execution_transaction_object_ref",
            "payment.transaction_object_ref",
            execution.transaction_object_ref
            if execution is not None
            and execution.transaction_object_ref is not None
            else missing,
            request.request_id if request is not None else missing,
        ),
        EvidenceRef(
            "payment_execution_order_ref",
            "payment.order_id",
            execution.order_id if execution is not None else missing,
            order.order_id if order is not None else missing,
        ),
        EvidenceRef(
            "payment_execution_agent_ref",
            "payment.agent_ref",
            execution.agent_ref
            if execution is not None and execution.agent_ref is not None
            else missing,
            request.agent_id if request is not None and request.agent_id is not None else missing,
        ),
        EvidenceRef(
            "payment_execution_payee_ref",
            "payment.payee",
            execution.payee
            if execution is not None and execution.payee is not None
            else missing,
            order.payee if order is not None else missing,
        ),
        EvidenceRef(
            "payment_execution_amount_ref",
            "payment.amount",
            str(execution.amount) if execution is not None else missing,
            str(request.amount) if request is not None else missing,
        ),
        EvidenceRef(
            "payment_execution_currency_ref",
            "payment.currency",
            execution.currency if execution is not None else missing,
            request.currency if request is not None else missing,
        ),
        EvidenceRef(
            "payment_execution_identity_ref",
            "payment.payment_id",
            execution.payment_id if execution is not None else missing,
        ),
    )


def payment_execution_binding_issues(
    fact: PaymentExecutionBindingFact,
) -> tuple[ValidationIssue, ...]:
    """Map trusted P2 reasons to payment-domain lifecycle/recovery issues."""

    if fact.status is VerificationStatus.VALID:
        return ()
    if fact.status is VerificationStatus.MISSING_EVIDENCE:
        return (
            ValidationIssue(
                "payment_execution_binding_missing_evidence",
                "continuous payment binding evidence is incomplete: "
                + ",".join(fact.reason_codes),
            ),
        )

    issue_groups = (
        (
            {
                "payment_execution_request_ref_mismatch",
                "payment_execution_transaction_object_ref_mismatch",
            },
            "payment_request_binding_mismatch",
            "payment execution does not reference the validated payment request",
        ),
        (
            {
                "payment_request_order_ref_mismatch",
                "payment_execution_order_ref_mismatch",
            },
            "payment_order_binding_mismatch",
            "payment request or execution does not reference the expected order",
        ),
        (
            {
                "payment_order_authority_ref_mismatch",
                "payment_order_authority_version_ref_mismatch",
                "payment_request_authority_ref_mismatch",
                "payment_request_authority_version_ref_mismatch",
                "payment_execution_authority_ref_mismatch",
            },
            "payment_authority_binding_mismatch",
            "payment chain does not preserve the current authority reference",
        ),
        (
            {
                "payment_request_agent_ref_mismatch",
                "payment_execution_agent_ref_mismatch",
            },
            "payment_agent_binding_mismatch",
            "payment chain does not preserve the expected agent reference",
        ),
        (
            {
                "payment_request_payee_mismatch",
                "payment_execution_payee_mismatch",
            },
            "payment_payee_binding_mismatch",
            "payment chain does not preserve the expected payee",
        ),
        (
            {
                "payment_request_amount_mismatch",
                "payment_execution_amount_mismatch",
            },
            "payment_amount_binding_mismatch",
            "payment chain does not preserve the validated amount",
        ),
        (
            {
                "payment_request_currency_mismatch",
                "payment_execution_currency_mismatch",
            },
            "payment_currency_binding_mismatch",
            "payment chain does not preserve the validated currency",
        ),
        (
            {
                "payment_request_merchant_mismatch",
            },
            "payment_merchant_binding_mismatch",
            "payment request does not preserve the expected merchant",
        ),
        (
            {
                "payment_execution_reference_collision",
                "payment_execution_before_request",
            },
            "payment_execution_identity_invalid",
            "payment execution identity or chronology is invalid",
        ),
    )
    reasons = set(fact.reason_codes)
    issues = [
        ValidationIssue(code, message)
        for members, code, message in issue_groups
        if reasons.intersection(members)
    ]
    if issues:
        return tuple(issues)
    return (
        ValidationIssue(
            "payment_execution_binding_invalid",
            "payment execution does not preserve the validated transaction chain",
        ),
    )

"""Payment-domain mapping and fail-closed gates for P2/P3/P4 execution facts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .models import (
    AgentIdentity,
    Decision,
    EvidenceRef,
    IntentMandate,
    Order,
    PaymentExecutionRecord,
    TransactionRequest,
    ValidationIssue,
)
from .trusted_execution import (
    POLICY_VERSION,
    ContextPolicyFact,
    IdentityAssuranceFact,
    IdentityAssuranceLevel,
    PaymentExecutionBindingFact,
    VerificationStatus,
    SourceCoverage,
    SourceType,
    RuntimeGateRecord,
    canonical_hash,
    missing_context_policy_fact,
    verify_agent_executor_identity,
    verify_payment_execution_binding,
)

PAYMENT_CONTEXT_ACTION = "execute_payment"
PAYMENT_REQUIRED_SOURCE_PATHS = (
    "final_order.order_id",
    "mandate.mandate_id",
    "request.agent_id",
    "request.amount",
    "request.currency",
    "request.payee",
    "request.request_id",
)


@dataclass(frozen=True)
class PaymentExecutionGateOutcome:
    """Payment-domain decision with the callback gated on P2, P3, and P4 facts."""

    decision: Decision
    binding_fact: PaymentExecutionBindingFact
    identity_fact: IdentityAssuranceFact
    context_policy_fact: ContextPolicyFact
    executed: bool
    execution_result: Any | None = None
    gate_reason_codes: tuple[str, ...] = ()


def execute_with_payment_binding_gate(
    prepayment_decision: Decision,
    mandate: IntentMandate | None,
    order: Order | None,
    request: TransactionRequest | None,
    execution: PaymentExecutionRecord | None,
    execute_payment: Callable[[], Any],
    *,
    agent_identity: AgentIdentity | None = None,
    current_provider_ref: str | None = None,
    current_executor_instance_ref: str | None = None,
    current_credential_ref: str | None = None,
    context_policy_fact: ContextPolicyFact | None = None,
) -> PaymentExecutionGateOutcome:
    """Invoke the callback only after upstream and P2-P4 checks all pass."""

    binding_fact = verify_payment_execution_binding(mandate, order, request, execution)
    identity_fact = verify_agent_executor_identity(
        authorized_agent_ref=(
            mandate.expected_agent_id if mandate is not None else None
        ),
        request_agent_ref=request.agent_id if request is not None else None,
        execution_agent_ref=execution.agent_ref if execution is not None else None,
        identity=agent_identity,
        current_provider_ref=current_provider_ref,
        current_executor_instance_ref=current_executor_instance_ref,
        current_credential_ref=current_credential_ref,
    )
    policy_fact = context_policy_fact or missing_context_policy_fact()

    def gate_outcome(
        decision: Decision,
        *gate_reason_codes: str,
        executed: bool = False,
        execution_result: Any | None = None,
    ) -> PaymentExecutionGateOutcome:
        return PaymentExecutionGateOutcome(
            decision=decision,
            binding_fact=binding_fact,
            identity_fact=identity_fact,
            context_policy_fact=policy_fact,
            executed=executed,
            execution_result=execution_result,
            gate_reason_codes=tuple(gate_reason_codes),
        )

    if prepayment_decision is not Decision.ALLOW:
        return gate_outcome(
            prepayment_decision,
            "p1:upstream_prepayment_non_allow",
        )
    if binding_fact.status is VerificationStatus.MISSING_EVIDENCE:
        return gate_outcome(
            Decision.INDETERMINATE,
            "p2:binding_missing",
        )
    if binding_fact.status is VerificationStatus.INVALID:
        return gate_outcome(
            Decision.DENY,
            "p2:binding_invalid",
        )
    if identity_fact.status is VerificationStatus.MISSING_EVIDENCE:
        return gate_outcome(
            Decision.INDETERMINATE,
            "p3:identity_missing",
        )
    if identity_fact.status is VerificationStatus.INVALID:
        return gate_outcome(
            Decision.DENY,
            "p3:identity_invalid",
        )
    if identity_fact.assurance_level not in {
        IdentityAssuranceLevel.BOUND,
        IdentityAssuranceLevel.VERIFIED,
    }:
        return gate_outcome(
            Decision.INDETERMINATE,
            "p3:assurance_insufficient",
        )
    if policy_fact.status is VerificationStatus.MISSING_EVIDENCE:
        return gate_outcome(
            Decision.INDETERMINATE,
            "p4:context_missing",
        )
    if (
        policy_fact.status is VerificationStatus.INVALID
        or policy_fact.unauthorized_state_change_detected
    ):
        reasons = ["p4:context_invalid"]
        if policy_fact.unauthorized_state_change_detected:
            reasons.append("p4:unauthorized_state_change")
        return gate_outcome(Decision.DENY, *reasons)

    p4_mismatch_reasons = _p4_contract_mismatch_reason_codes(
        policy_fact,
        mandate,
        order,
        request,
    )
    if p4_mismatch_reasons:
        return gate_outcome(Decision.INDETERMINATE, *p4_mismatch_reasons)

    result = execute_payment()
    return gate_outcome(
        Decision.ALLOW,
        "runtime:allow",
        executed=True,
        execution_result=result,
    )


def observe_payment_execution_gate(
    prepayment_decision: Decision,
    mandate: IntentMandate | None,
    order: Order | None,
    request: TransactionRequest | None,
    execution: PaymentExecutionRecord | None,
    execute_payment: Callable[[], Any],
    **kwargs: Any,
) -> RuntimeGateRecord:
    """Capture one immutable receipt observation at the actual gate invocation point."""

    callback_count = 0
    callback_result_ref: str | None = None

    def observed_callback() -> Any:
        nonlocal callback_count, callback_result_ref
        callback_count += 1
        result = execute_payment()
        callback_result_ref = str(result)
        return result

    outcome = execute_with_payment_binding_gate(
        prepayment_decision,
        mandate,
        order,
        request,
        execution,
        observed_callback,
        **kwargs,
    )
    reason_codes = tuple(
        sorted(
            {
                *outcome.gate_reason_codes,
                *(f"p2:{reason}" for reason in outcome.binding_fact.reason_codes),
                *(f"p3:{reason}" for reason in outcome.identity_fact.reason_codes),
                *(f"p4:{reason}" for reason in outcome.context_policy_fact.reason_codes),
            }
        )
    )
    return RuntimeGateRecord(
        preliminary_decision=prepayment_decision,
        final_decision=outcome.decision,
        binding_status=outcome.binding_fact.status.value,
        binding_reason_codes=outcome.binding_fact.reason_codes,
        identity_status=outcome.identity_fact.status.value,
        identity_reason_codes=outcome.identity_fact.reason_codes,
        context_policy_status=outcome.context_policy_fact.status.value,
        context_policy_reason_codes=outcome.context_policy_fact.reason_codes,
        callback_executed=outcome.executed,
        callback_count=callback_count,
        callback_result_ref=callback_result_ref,
        reason_codes=reason_codes or ("gate_observation_recorded",),
    )


def _expected_payment_source_coverage(
    mandate: IntentMandate | None,
    order: Order | None,
    request: TransactionRequest | None,
) -> tuple[SourceCoverage, ...]:
    if mandate is None or order is None or request is None:
        return ()
    values = (
        ("final_order.order_id", SourceType.USER_CONFIRMED, order.order_id),
        ("mandate.mandate_id", SourceType.USER_CONFIRMED, mandate.mandate_id),
        ("request.agent_id", SourceType.USER_CONFIRMED, request.agent_id),
        ("request.amount", SourceType.USER_CONFIRMED, request.amount),
        ("request.currency", SourceType.USER_CONFIRMED, request.currency),
        ("request.payee", SourceType.USER_CONFIRMED, request.payee),
        ("request.request_id", SourceType.PROTOCOL_VERIFIED, request.request_id),
    )
    return tuple(
        SourceCoverage(path, source, canonical_hash(value))
        for path, source, value in values
    )


def _p4_contract_mismatch_reason_codes(
    policy_fact: ContextPolicyFact,
    mandate: IntentMandate | None,
    order: Order | None,
    request: TransactionRequest | None,
) -> tuple[str, ...]:
    """Explain why a valid P4 fact is not valid for this payment invocation."""

    reasons: list[str] = []
    if policy_fact.policy_version != POLICY_VERSION:
        reasons.append("p4:policy_version_mismatch")
    if policy_fact.current_action != PAYMENT_CONTEXT_ACTION:
        reasons.append("p4:current_action_mismatch")
    if policy_fact.required_source_paths != PAYMENT_REQUIRED_SOURCE_PATHS:
        reasons.append("p4:required_source_paths_mismatch")
    if policy_fact.covered_source_paths != PAYMENT_REQUIRED_SOURCE_PATHS:
        reasons.append("p4:covered_source_paths_mismatch")
    if policy_fact.missing_source_paths:
        reasons.append("p4:missing_source_paths")
    if policy_fact.source_coverage != _expected_payment_source_coverage(
        mandate,
        order,
        request,
    ):
        reasons.append("p4:source_coverage_value_mismatch")
    return tuple(reasons)


def identity_assurance_evidence(
    fact: IdentityAssuranceFact,
) -> tuple[EvidenceRef, ...]:
    """Expose the P3 fact without exposing credential contents."""

    missing = "<missing>"
    return (
        EvidenceRef(
            "identity_assurance_status",
            "trusted_execution.identity.status",
            fact.status.value,
            VerificationStatus.VALID.value,
        ),
        EvidenceRef(
            "identity_assurance_level",
            "trusted_execution.identity.assurance_level",
            fact.assurance_level.value,
            IdentityAssuranceLevel.BOUND.value,
        ),
        EvidenceRef(
            "identity_assurance_reasons",
            "trusted_execution.identity.reason_codes",
            ",".join(fact.reason_codes),
        ),
        EvidenceRef(
            "identity_authorized_agent_ref",
            "trusted_execution.identity.authorized_agent_ref",
            fact.authorized_agent_ref or missing,
        ),
        EvidenceRef(
            "identity_request_agent_ref",
            "trusted_execution.identity.request_agent_ref",
            fact.request_agent_ref or missing,
            fact.authorized_agent_ref or missing,
        ),
        EvidenceRef(
            "identity_execution_agent_ref",
            "trusted_execution.identity.execution_agent_ref",
            fact.execution_agent_ref or missing,
            fact.authorized_agent_ref or missing,
        ),
        EvidenceRef(
            "identity_object_agent_ref",
            "trusted_execution.identity.identity_agent_ref",
            fact.identity_agent_ref or missing,
            fact.authorized_agent_ref or missing,
        ),
        EvidenceRef(
            "identity_provider_ref",
            "trusted_execution.identity.provider_ref",
            fact.provider_ref or missing,
            fact.identity_provider_ref or missing,
        ),
        EvidenceRef(
            "identity_executor_instance_ref",
            "trusted_execution.identity.executor_instance_ref",
            fact.executor_instance_ref or missing,
            fact.identity_executor_instance_ref or missing,
        ),
        EvidenceRef(
            "identity_credential_available",
            "trusted_execution.identity.credential_available",
            str(fact.credential_available).lower(),
        ),
        EvidenceRef(
            "identity_credential_ref",
            "trusted_execution.identity.credential_ref",
            fact.credential_ref or missing,
            fact.identity_credential_ref or missing,
        ),
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

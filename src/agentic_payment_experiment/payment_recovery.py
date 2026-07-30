from __future__ import annotations

from .models import (
    EvidenceRef,
    IntentMandate,
    Order,
    PaymentExecutionRecord,
    PaymentRecoveryResult,
    PaymentRecoveryStatus,
    PaymentStatus,
    PaymentStatusObservation,
    TransactionRequest,
    ValidationIssue,
)
from .payment_execution import (
    payment_execution_binding_evidence,
    payment_execution_binding_issues,
)
from .trusted_execution import (
    ExecutionAttemptFact,
    IdempotencyFact,
    VerificationResult,
    VerificationStatus,
    check_idempotency,
    validate_status_observation,
    verify_payment_execution_binding,
)


def assess_payment_recovery(
    payment: PaymentExecutionRecord,
    observation: PaymentStatusObservation,
    *,
    known_attempts: tuple[PaymentExecutionRecord, ...] = (),
    mandate: IntentMandate | None = None,
    request: TransactionRequest | None = None,
    order: Order | None = None,
) -> PaymentRecoveryResult:
    """Recover one uncertain offline payment state without executing a retry.

    This layer answers whether a later status observation can be trusted and whether
    the state machine may enter a *retry candidate* state. ``retry_allowed=True``
    never performs another payment; it only means the original payment is confirmed
    terminal FAILED, the idempotency boundary is explicit, and no conflicting
    successful or unresolved attempt exists for the same business request.
    """

    evidence = list(_base_evidence(payment, observation))
    if any(value is not None for value in (mandate, request, order)):
        payment_binding = verify_payment_execution_binding(
            mandate,
            order,
            request,
            payment,
        )
        evidence.extend(
            payment_execution_binding_evidence(
                payment_binding,
                mandate,
                order,
                request,
                payment,
            )
        )
        binding_issues = payment_execution_binding_issues(payment_binding)
        if binding_issues:
            return PaymentRecoveryResult(
                initial_status=payment.status,
                observed_status=observation.status,
                effective_status=payment.status,
                recovery_status=PaymentRecoveryStatus.BLOCKED,
                next_action="investigate_payment_execution_binding",
                retry_allowed=False,
                issues=binding_issues,
                evidence=tuple(evidence),
            )

    observation_fact = validate_status_observation(
        expected_execution_id=payment.payment_id,
        observed_execution_id=observation.payment_id,
        expected_object_id=payment.order_id,
        observed_object_id=observation.order_id,
        expected_provider_ref=payment.provider_ref,
        observed_provider_ref=observation.provider_ref,
    )
    evidence.extend(_observation_fact_evidence(observation_fact))
    binding_issues = _observation_binding_issues(observation_fact)
    if binding_issues:
        return PaymentRecoveryResult(
            initial_status=payment.status,
            observed_status=observation.status,
            effective_status=payment.status,
            recovery_status=PaymentRecoveryStatus.BLOCKED,
            next_action="investigate_status_observation_binding",
            retry_allowed=False,
            issues=tuple(binding_issues),
            evidence=tuple(evidence),
        )

    if observation.status is PaymentStatus.SUCCEEDED:
        return PaymentRecoveryResult(
            initial_status=payment.status,
            observed_status=observation.status,
            effective_status=PaymentStatus.SUCCEEDED,
            recovery_status=PaymentRecoveryStatus.RECOVERED,
            next_action="continue_with_original_payment",
            retry_allowed=False,
            issues=(
                ValidationIssue(
                    "payment_state_recovered_as_succeeded",
                    "a later trusted status query confirmed that the original payment succeeded",
                ),
            ),
            evidence=tuple(evidence),
        )

    if observation.status is PaymentStatus.UNKNOWN:
        return PaymentRecoveryResult(
            initial_status=payment.status,
            observed_status=observation.status,
            effective_status=PaymentStatus.UNKNOWN,
            recovery_status=PaymentRecoveryStatus.UNRESOLVED,
            next_action="query_again_or_manual_review",
            retry_allowed=False,
            issues=(
                ValidationIssue(
                    "payment_state_still_unknown",
                    "the trusted status query still cannot determine whether the original payment succeeded",
                ),
            ),
            evidence=tuple(evidence),
        )

    if observation.status is PaymentStatus.PENDING:
        return PaymentRecoveryResult(
            initial_status=payment.status,
            observed_status=observation.status,
            effective_status=PaymentStatus.PENDING,
            recovery_status=PaymentRecoveryStatus.UNRESOLVED,
            next_action="wait_and_query_again",
            retry_allowed=False,
            issues=(
                ValidationIssue(
                    "payment_still_pending",
                    "the trusted status query reports that the original payment is still pending",
                ),
            ),
            evidence=tuple(evidence),
        )

    if payment.status is PaymentStatus.SUCCEEDED:
        return PaymentRecoveryResult(
            initial_status=payment.status,
            observed_status=observation.status,
            effective_status=PaymentStatus.SUCCEEDED,
            recovery_status=PaymentRecoveryStatus.BLOCKED,
            next_action="investigate_conflicting_failed_observation",
            retry_allowed=False,
            issues=(
                ValidationIssue(
                    "payment_status_observation_conflicts_with_known_success",
                    "a later failed observation conflicts with an already successful payment record",
                ),
            ),
            evidence=tuple(evidence),
        )

    # A trusted FAILED observation is necessary but not sufficient for a safe retry.
    # Trusted Execution inventories the idempotency boundary and related attempts;
    # Payment Domain still interprets attempt statuses and chooses the recovery action.
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
    evidence.extend(_idempotency_fact_evidence(idempotency_fact))
    related_execution_ids = {
        attempt.execution_id for attempt in idempotency_fact.related_attempts
    }
    relevant_attempts = tuple(
        attempt for attempt in known_attempts if attempt.payment_id in related_execution_ids
    )
    succeeded_attempts = tuple(
        attempt for attempt in relevant_attempts if attempt.status is PaymentStatus.SUCCEEDED
    )
    if succeeded_attempts:
        evidence.extend(_attempt_evidence("existing_successful_attempt", succeeded_attempts))
        return PaymentRecoveryResult(
            initial_status=payment.status,
            observed_status=observation.status,
            effective_status=PaymentStatus.FAILED,
            recovery_status=PaymentRecoveryStatus.BLOCKED,
            next_action="use_existing_successful_attempt",
            retry_allowed=False,
            issues=(
                ValidationIssue(
                    "existing_successful_payment_attempt",
                    "another payment attempt for the same business request is already successful",
                ),
            ),
            evidence=tuple(evidence),
        )

    unresolved_attempts = tuple(
        attempt
        for attempt in relevant_attempts
        if attempt.status in {PaymentStatus.UNKNOWN, PaymentStatus.PENDING}
    )
    if unresolved_attempts:
        evidence.extend(_attempt_evidence("unresolved_parallel_attempt", unresolved_attempts))
        return PaymentRecoveryResult(
            initial_status=payment.status,
            observed_status=observation.status,
            effective_status=PaymentStatus.FAILED,
            recovery_status=PaymentRecoveryStatus.BLOCKED,
            next_action="query_existing_attempts_before_retry",
            retry_allowed=False,
            issues=(
                ValidationIssue(
                    "unresolved_payment_attempt_exists",
                    "another payment attempt for the same business request is still unknown or pending",
                ),
            ),
            evidence=tuple(evidence),
        )

    if idempotency_fact.status is VerificationStatus.MISSING_EVIDENCE:
        return PaymentRecoveryResult(
            initial_status=payment.status,
            observed_status=observation.status,
            effective_status=PaymentStatus.FAILED,
            recovery_status=PaymentRecoveryStatus.BLOCKED,
            next_action="establish_idempotency_boundary_before_retry",
            retry_allowed=False,
            issues=(
                ValidationIssue(
                    "idempotency_boundary_missing",
                    "the original payment has no explicit idempotency key for a safe retry boundary",
                ),
            ),
            evidence=tuple(evidence),
        )

    return PaymentRecoveryResult(
        initial_status=payment.status,
        observed_status=observation.status,
        effective_status=PaymentStatus.FAILED,
        recovery_status=PaymentRecoveryStatus.RETRY_CANDIDATE,
        next_action="safe_retry_candidate_with_same_idempotency_boundary",
        retry_allowed=True,
        issues=(
            ValidationIssue(
                "payment_confirmed_failed_retry_candidate",
                "the original payment is terminal failed and no successful or unresolved parallel attempt exists",
            ),
        ),
        evidence=tuple(evidence),
    )


def _observation_binding_issues(
    fact: VerificationResult,
) -> list[ValidationIssue]:
    issue_map = {
        "execution_reference_mismatch": ValidationIssue(
            "payment_status_observation_payment_mismatch",
            "the status observation does not reference the original payment",
        ),
        "object_reference_mismatch": ValidationIssue(
            "payment_status_observation_order_mismatch",
            "the status observation does not reference the original order",
        ),
        "provider_reference_mismatch": ValidationIssue(
            "payment_status_observation_provider_mismatch",
            "the status observation references a different provider payment reference",
        ),
        "required_execution_reference_missing": ValidationIssue(
            "payment_status_observation_reference_missing",
            "the status observation is missing a required payment or order reference",
        ),
    }
    return [issue_map[reason] for reason in fact.reason_codes if reason in issue_map]


def _observation_fact_evidence(fact: VerificationResult) -> tuple[EvidenceRef, ...]:
    return (
        EvidenceRef(
            "status_observation_verification_status",
            "trusted_execution.status_observation.status",
            fact.status.value,
            VerificationStatus.VALID.value,
        ),
        EvidenceRef(
            "status_observation_verification_reasons",
            "trusted_execution.status_observation.reason_codes",
            ",".join(fact.reason_codes),
        ),
    )


def _idempotency_fact_evidence(fact: IdempotencyFact) -> tuple[EvidenceRef, ...]:
    return (
        EvidenceRef(
            "idempotency_verification_status",
            "trusted_execution.idempotency.status",
            fact.status.value,
            VerificationStatus.VALID.value,
        ),
        EvidenceRef(
            "idempotency_verification_reason",
            "trusted_execution.idempotency.reason_code",
            fact.reason_code,
        ),
        EvidenceRef(
            "idempotency_related_attempt_count",
            "trusted_execution.idempotency.related_attempts",
            str(len(fact.related_attempts)),
        ),
    )


def _base_evidence(
    payment: PaymentExecutionRecord,
    observation: PaymentStatusObservation,
) -> tuple[EvidenceRef, ...]:
    evidence = [
        EvidenceRef("recovery_request_ref", "payment.request_id", payment.request_id),
        EvidenceRef("recovery_order_ref", "payment.order_id", payment.order_id),
        EvidenceRef("recovery_payment_ref", "payment.payment_id", payment.payment_id),
        EvidenceRef("initial_payment_status", "payment.status", payment.status.value),
        EvidenceRef(
            "status_observation_payment_ref",
            "payment_status_observation.payment_id",
            observation.payment_id,
            payment.payment_id,
        ),
        EvidenceRef(
            "status_observation_order_ref",
            "payment_status_observation.order_id",
            observation.order_id,
            payment.order_id,
        ),
        EvidenceRef(
            "queried_payment_status",
            "payment_status_observation.status",
            observation.status.value,
        ),
        EvidenceRef(
            "status_observation_source",
            "payment_status_observation.source",
            observation.source,
        ),
        EvidenceRef(
            "status_observed_at",
            "payment_status_observation.observed_at",
            observation.observed_at.isoformat(),
        ),
    ]
    if payment.provider_ref:
        evidence.append(
            EvidenceRef(
                "recovery_provider_ref",
                "payment.provider_ref",
                payment.provider_ref,
            )
        )
    if payment.idempotency_key:
        evidence.append(
            EvidenceRef(
                "recovery_idempotency_key",
                "payment.idempotency_key",
                payment.idempotency_key,
            )
        )
    if observation.provider_ref:
        evidence.append(
            EvidenceRef(
                "status_observation_provider_ref",
                "payment_status_observation.provider_ref",
                observation.provider_ref,
                payment.provider_ref,
            )
        )
    return tuple(evidence)


def _attempt_evidence(
    prefix: str,
    attempts: tuple[PaymentExecutionRecord, ...],
) -> list[EvidenceRef]:
    evidence: list[EvidenceRef] = []
    for index, attempt in enumerate(attempts, start=1):
        evidence.extend(
            [
                EvidenceRef(
                    f"{prefix}_{index}_payment_ref",
                    f"known_attempts[{index - 1}].payment_id",
                    attempt.payment_id,
                ),
                EvidenceRef(
                    f"{prefix}_{index}_status",
                    f"known_attempts[{index - 1}].status",
                    attempt.status.value,
                ),
            ]
        )
    return evidence

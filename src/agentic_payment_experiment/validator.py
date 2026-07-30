from __future__ import annotations

from collections.abc import Collection

from .models import (
    Decision,
    EvidenceRef,
    IntentMandate,
    Order,
    TransactionRequest,
    ValidationIssue,
    ValidationResult,
)
from .order_validation import validate_order
from .trusted_execution import (
    BindingStatus,
    ConfirmationBindingFact,
    ConfirmationRecord,
    VerificationStatus,
    verify_confirmation_binding,
    verify_declared_identity_binding,
)


def validate_request(
    mandate: IntentMandate,
    request: TransactionRequest,
    *,
    seen_request_ids: Collection[str] = (),
    authorized_order: Order | None = None,
    final_order: Order | None = None,
    confirmation_record: ConfirmationRecord | None = None,
) -> ValidationResult:
    """Validate one simulated payment request against a user mandate.

    This is an offline, deterministic experiment. It does not authorize or
    execute a real payment.
    """

    issues: list[ValidationIssue] = []
    evidence: list[EvidenceRef] = [
        EvidenceRef("mandate_ref", "mandate.mandate_id", mandate.mandate_id),
        EvidenceRef("request_ref", "request.request_id", request.request_id),
    ]

    missing_fields = _missing_required_fields(mandate, request)
    if missing_fields:
        for field_path in missing_fields:
            issues.append(ValidationIssue("required_field_missing", f"{field_path} is required"))
            evidence.append(EvidenceRef("required_field_missing", field_path, "<missing>"))
        return ValidationResult(
            decision=Decision.INDETERMINATE,
            issues=tuple(issues),
            evidence=tuple(evidence),
        )

    if request.currency != mandate.currency:
        issues.append(ValidationIssue("currency_mismatch", "request currency differs from mandate currency"))
        evidence.append(
            EvidenceRef(
                "currency_mismatch",
                "request.currency",
                request.currency,
                mandate.currency,
            )
        )
        return ValidationResult(
            decision=Decision.INDETERMINATE,
            issues=tuple(issues),
            evidence=tuple(evidence),
        )

    if request.request_id in seen_request_ids:
        issues.append(ValidationIssue("duplicate_request", "request_id has already been processed"))
        evidence.append(EvidenceRef("duplicate_request", "request.request_id", request.request_id, "unseen request_id"))

    if request.amount <= 0:
        issues.append(ValidationIssue("invalid_amount", "amount must be positive"))
        evidence.append(EvidenceRef("invalid_amount", "request.amount", str(request.amount), "> 0"))

    if request.amount > mandate.max_amount:
        issues.append(ValidationIssue("over_budget", "amount exceeds the mandate hard limit"))
        evidence.append(
            EvidenceRef("over_budget", "request.amount", str(request.amount), f"<= {mandate.max_amount}")
        )

    if mandate.allowed_merchants and request.merchant not in mandate.allowed_merchants:
        issues.append(ValidationIssue("merchant_out_of_scope", "merchant is outside the mandate"))
        evidence.append(
            EvidenceRef(
                "merchant_out_of_scope",
                "request.merchant",
                request.merchant,
                ", ".join(sorted(mandate.allowed_merchants)),
            )
        )

    if mandate.allowed_categories and request.category not in mandate.allowed_categories:
        issues.append(ValidationIssue("category_out_of_scope", "category is outside the mandate"))
        evidence.append(
            EvidenceRef(
                "category_out_of_scope",
                "request.category",
                request.category,
                ", ".join(sorted(mandate.allowed_categories)),
            )
        )

    if request.occurred_at > mandate.expires_at:
        issues.append(ValidationIssue("mandate_expired", "mandate has expired"))
        evidence.append(
            EvidenceRef(
                "mandate_expired",
                "request.occurred_at",
                request.occurred_at.isoformat(),
                f"<= {mandate.expires_at.isoformat()}",
            )
        )

    if request.sequence_count < 1 or request.sequence_count > mandate.max_count:
        issues.append(ValidationIssue("count_exceeded", "request count exceeds the mandate"))
        evidence.append(
            EvidenceRef(
                "count_exceeded",
                "request.sequence_count",
                str(request.sequence_count),
                f"1..{mandate.max_count}",
            )
        )

    if mandate.expected_agent_id:
        identity_fact = verify_declared_identity_binding(
            expected_identity_id=mandate.expected_agent_id,
            actual_identity_id=request.agent_id,
        )
        evidence.extend(
            (
                EvidenceRef(
                    "agent_claim_binding_status",
                    "trusted_execution.declared_identity.status",
                    identity_fact.status.value,
                    VerificationStatus.VALID.value,
                ),
                EvidenceRef(
                    "agent_claim_binding_reason",
                    "trusted_execution.declared_identity.reason_codes",
                    ",".join(identity_fact.reason_codes),
                ),
            )
        )
        if identity_fact.status is not VerificationStatus.VALID:
            issues.append(ValidationIssue("agent_identity_mismatch", "request agent does not match the mandate"))
            evidence.append(
                EvidenceRef(
                    "agent_identity_mismatch",
                    "request.agent_id",
                    request.agent_id or "<missing>",
                    mandate.expected_agent_id,
                )
            )

    if issues:
        return ValidationResult(
            decision=Decision.DENY,
            issues=tuple(issues),
            evidence=tuple(evidence),
        )

    confirmation_fact: ConfirmationBindingFact | None = None
    p1_required = confirmation_record is not None or any(
        order is not None and order.authority_version_ref is not None
        for order in (authorized_order, final_order)
    )
    if p1_required:
        confirmation_fact = verify_confirmation_binding(
            confirmation_record,
            final_order,
            authority_id=mandate.mandate_id,
            authority_version=mandate.authority_version,
            checked_at=request.occurred_at,
        )
        evidence.extend(
            _confirmation_evidence(
                mandate,
                authorized_order,
                final_order,
                confirmation_record,
                confirmation_fact,
            )
        )

    order_result = validate_order(
        mandate,
        request,
        authorized_order,
        final_order,
    )
    if order_result is not None:
        evidence.extend(order_result.evidence)
        if order_result.decision in {Decision.DENY, Decision.INDETERMINATE}:
            return ValidationResult(
                decision=order_result.decision,
                issues=order_result.issues,
                evidence=tuple(evidence),
                rule_version=order_result.rule_version,
                limitations=order_result.limitations,
                order_differences=order_result.differences,
            )

    if (
        confirmation_fact is not None
        and confirmation_fact.status is BindingStatus.MISSING_EVIDENCE
    ):
        evidence.append(
            EvidenceRef(
                "confirmation_binding_missing_evidence",
                "trusted_execution.confirmation_binding.status",
                confirmation_fact.status.value,
                BindingStatus.VALID.value,
            )
        )
        return ValidationResult(
            decision=Decision.INDETERMINATE,
            issues=(
                ValidationIssue(
                    "confirmation_binding_missing_evidence",
                    "confirmation binding evidence is incomplete",
                ),
            ),
            evidence=tuple(evidence),
            rule_version="confirmation-binding-rules-v1",
            limitations=(
                "simulation_only",
                "confirmation_hash_is_not_tamper_proof_storage",
                "missing_confirmation_evidence_fails_closed",
            ),
            order_differences=(
                order_result.differences if order_result is not None else ()
            ),
        )

    if order_result is not None and order_result.decision is not None:
        return ValidationResult(
            decision=order_result.decision,
            issues=order_result.issues,
            evidence=tuple(evidence),
            rule_version=order_result.rule_version,
            limitations=order_result.limitations,
            order_differences=order_result.differences,
        )

    if (
        confirmation_fact is not None
        and confirmation_fact.status is BindingStatus.INVALID
    ):
        evidence.append(
            EvidenceRef(
                "confirmation_binding_invalid",
                "trusted_execution.confirmation_binding.status",
                confirmation_fact.status.value,
                BindingStatus.VALID.value,
            )
        )
        return ValidationResult(
            decision=Decision.CONFIRMATION_REQUIRED,
            issues=(
                ValidationIssue(
                    "confirmation_binding_invalid",
                    "the current transaction is no longer bound to the saved confirmation",
                ),
            ),
            evidence=tuple(evidence),
            rule_version="confirmation-binding-rules-v1",
            limitations=(
                "simulation_only",
                "confirmation_hash_is_not_tamper_proof_storage",
                "payment_domain_maps_binding_fact_to_reconfirmation",
            ),
        )

    if mandate.confirmation_above is not None and request.amount > mandate.confirmation_above:
        confirmation_issue = ValidationIssue(
            "confirmation_threshold_exceeded",
            "amount is within the hard limit but exceeds the no-confirmation threshold",
        )
        evidence.append(
            EvidenceRef(
                "confirmation_threshold_exceeded",
                "request.amount",
                str(request.amount),
                f"<= {mandate.confirmation_above} without confirmation",
            )
        )
        return ValidationResult(
            decision=Decision.CONFIRMATION_REQUIRED,
            issues=(confirmation_issue,),
            evidence=tuple(evidence),
            rule_version=(order_result.rule_version if order_result is not None else "mandate-rules-v0.1"),
            limitations=(order_result.limitations if order_result is not None else (
                "simulation_only",
                "not_a_production_payment_authorization",
            )),
            order_differences=(order_result.differences if order_result is not None else ()),
        )

    evidence.extend(
        (
            EvidenceRef("amount_within_scope", "request.amount", str(request.amount), f"<= {mandate.max_amount}"),
            EvidenceRef("merchant_within_scope", "request.merchant", request.merchant),
            EvidenceRef("category_within_scope", "request.category", request.category),
        )
    )
    return ValidationResult(
        decision=Decision.ALLOW,
        issues=(),
        evidence=tuple(evidence),
        rule_version=(order_result.rule_version if order_result is not None else "mandate-rules-v0.1"),
        limitations=(order_result.limitations if order_result is not None else (
            "simulation_only",
            "not_a_production_payment_authorization",
        )),
        order_differences=(order_result.differences if order_result is not None else ()),
    )


def _missing_required_fields(
    mandate: IntentMandate,
    request: TransactionRequest,
) -> tuple[str, ...]:
    values = {
        "mandate.mandate_id": mandate.mandate_id,
        "mandate.user_id": mandate.user_id,
        "mandate.currency": mandate.currency,
        "request.request_id": request.request_id,
        "request.merchant": request.merchant,
        "request.category": request.category,
        "request.currency": request.currency,
    }
    return tuple(path for path, value in values.items() if not str(value).strip())


def _confirmation_evidence(
    mandate: IntentMandate,
    authorized_order: Order | None,
    final_order: Order | None,
    record: ConfirmationRecord | None,
    fact: ConfirmationBindingFact,
) -> tuple[EvidenceRef, ...]:
    missing = "<missing>"
    return (
        EvidenceRef(
            "confirmation_record_ref",
            "confirmation_record.confirmation_id",
            record.confirmation_id if record is not None else missing,
        ),
        EvidenceRef(
            "authority_ref",
            "mandate.mandate_id",
            mandate.mandate_id,
            record.authority_id if record is not None else missing,
        ),
        EvidenceRef(
            "authority_version",
            "mandate.authority_version",
            mandate.authority_version,
            record.authority_version if record is not None else missing,
        ),
        EvidenceRef(
            "authorized_order_authority_version_ref",
            "authorized_order.authority_version_ref",
            (
                authorized_order.authority_version_ref
                if authorized_order is not None
                and authorized_order.authority_version_ref is not None
                else missing
            ),
            mandate.authority_version,
        ),
        EvidenceRef(
            "final_order_authority_version_ref",
            "final_order.authority_version_ref",
            (
                final_order.authority_version_ref
                if final_order is not None and final_order.authority_version_ref is not None
                else missing
            ),
            mandate.authority_version,
        ),
        EvidenceRef(
            "confirmation_binding_status",
            "trusted_execution.confirmation_binding.status",
            fact.status.value,
            BindingStatus.VALID.value,
        ),
        EvidenceRef(
            "confirmation_binding_reason",
            "trusted_execution.confirmation_binding.reason",
            fact.reason,
        ),
        EvidenceRef(
            "confirmation_expected_order_hash",
            "trusted_execution.confirmation_binding.expected_order_hash",
            fact.expected_order_hash or missing,
        ),
        EvidenceRef(
            "confirmation_actual_order_hash",
            "trusted_execution.confirmation_binding.actual_order_hash",
            fact.actual_order_hash or missing,
            fact.expected_order_hash,
        ),
        EvidenceRef(
            "confirmation_invalidated_by",
            "trusted_execution.confirmation_binding.invalidated_by",
            fact.invalidated_by or "<none>",
        ),
        EvidenceRef(
            "confirmation_checked_at",
            "trusted_execution.confirmation_binding.checked_at",
            fact.checked_at.isoformat(),
        ),
    )

from __future__ import annotations

from .models import (
    DisputeRecord,
    DisputeStatus,
    EvidenceRef,
    LifecycleResult,
    Order,
    PaymentExecutionRecord,
    RefundRecord,
    RefundStatus,
    RemediationState,
    RemediationStatus,
    ValidationIssue,
)
from .trusted_execution import FollowUpAction, verify_original_transaction


def assess_remediation(
    order: Order,
    payment: PaymentExecutionRecord,
    lifecycle: LifecycleResult,
    *,
    refund: RefundRecord | None = None,
    dispute: DisputeRecord | None = None,
) -> LifecycleResult:
    """Assess offline refund/dispute observations without executing real remediation.

    The original end-to-end task status deliberately remains unchanged. A failed
    purchase can therefore stay FAILED while an economic remediation becomes
    RESOLVED after a correctly bound full refund.
    """

    if refund is None and dispute is None:
        return lifecycle

    evidence = list(lifecycle.evidence)
    remediation_evidence: list[EvidenceRef] = []
    remediation_issues: list[ValidationIssue] = []

    if refund is not None:
        remediation_evidence.extend(_refund_evidence(refund, payment))
        remediation_issues.extend(_refund_binding_issues(refund, order, payment))
    if dispute is not None:
        remediation_evidence.extend(_dispute_evidence(dispute, payment))
        remediation_issues.extend(_dispute_binding_issues(dispute, order, payment))

    evidence.extend(remediation_evidence)

    if remediation_issues:
        return _merged_lifecycle(
            lifecycle,
            remediation=RemediationState(
                status=RemediationStatus.REQUIRED,
                next_action="preserve_evidence_and_investigate_remediation_binding",
                case_ref=(refund.refund_id if refund is not None else dispute.dispute_id),
            ),
            refund=refund,
            dispute=dispute,
            issues=remediation_issues,
            evidence=evidence,
        )

    if dispute is not None:
        if dispute.status in {DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW}:
            return _merged_lifecycle(
                lifecycle,
                remediation=RemediationState(
                    status=RemediationStatus.IN_PROGRESS,
                    next_action="continue_dispute_review",
                    case_ref=dispute.dispute_id,
                ),
                refund=refund,
                dispute=dispute,
                issues=[
                    ValidationIssue(
                        "dispute_requires_review",
                        "the dispute is still open or under review",
                    )
                ],
                evidence=evidence,
            )
        if dispute.status is DisputeStatus.UNKNOWN:
            return _merged_lifecycle(
                lifecycle,
                remediation=RemediationState(
                    status=RemediationStatus.REQUIRED,
                    next_action="investigate_dispute_status",
                    case_ref=dispute.dispute_id,
                ),
                refund=refund,
                dispute=dispute,
                issues=[
                    ValidationIssue(
                        "dispute_status_unknown",
                        "the dispute status is unknown",
                    )
                ],
                evidence=evidence,
            )

    if refund is not None:
        if refund.status is RefundStatus.SUCCEEDED:
            if refund.amount == payment.amount and dispute is None:
                return _merged_lifecycle(
                    lifecycle,
                    remediation=RemediationState(
                        status=RemediationStatus.RESOLVED,
                        next_action="economic_remediation_completed_by_full_refund",
                        case_ref=refund.refund_id,
                    ),
                    refund=refund,
                    dispute=dispute,
                    issues=[],
                    evidence=evidence,
                )
            if refund.amount < payment.amount:
                return _merged_lifecycle(
                    lifecycle,
                    remediation=RemediationState(
                        status=RemediationStatus.IN_PROGRESS,
                        next_action="continue_remediation_for_remaining_amount",
                        case_ref=refund.refund_id,
                    ),
                    refund=refund,
                    dispute=dispute,
                    issues=[
                        ValidationIssue(
                            "partial_refund_requires_further_remediation",
                            "a successful partial refund does not fully resolve the economic remediation",
                        )
                    ],
                    evidence=evidence,
                )
        if refund.status is RefundStatus.PENDING:
            return _merged_lifecycle(
                lifecycle,
                remediation=RemediationState(
                    status=RemediationStatus.IN_PROGRESS,
                    next_action="wait_for_refund_status",
                    case_ref=refund.refund_id,
                ),
                refund=refund,
                dispute=dispute,
                issues=[],
                evidence=evidence,
            )
        if refund.status is RefundStatus.FAILED:
            return _merged_lifecycle(
                lifecycle,
                remediation=RemediationState(
                    status=RemediationStatus.REQUIRED,
                    next_action="retry_or_escalate_failed_refund",
                    case_ref=refund.refund_id,
                ),
                refund=refund,
                dispute=dispute,
                issues=[ValidationIssue("refund_failed", "the observed refund attempt failed")],
                evidence=evidence,
            )
        if refund.status is RefundStatus.UNKNOWN:
            return _merged_lifecycle(
                lifecycle,
                remediation=RemediationState(
                    status=RemediationStatus.REQUIRED,
                    next_action="investigate_refund_status",
                    case_ref=refund.refund_id,
                ),
                refund=refund,
                dispute=dispute,
                issues=[ValidationIssue("refund_status_unknown", "the refund status is unknown")],
                evidence=evidence,
            )

    if dispute is not None and dispute.status is DisputeStatus.RESOLVED:
        return _merged_lifecycle(
            lifecycle,
            remediation=RemediationState(
                status=RemediationStatus.REQUIRED,
                next_action="verify_dispute_resolution_outcome",
                case_ref=dispute.dispute_id,
            ),
            refund=refund,
            dispute=dispute,
            issues=[
                ValidationIssue(
                    "dispute_resolution_outcome_unverified",
                    "the dispute case is closed but the economic remediation outcome is not represented",
                )
            ],
            evidence=evidence,
        )

    return _merged_lifecycle(
        lifecycle,
        remediation=RemediationState(
            status=RemediationStatus.REQUIRED,
            next_action="preserve_evidence_and_continue_remediation",
            case_ref=(refund.refund_id if refund is not None else dispute.dispute_id),
        ),
        refund=refund,
        dispute=dispute,
        issues=[],
        evidence=evidence,
    )


def _refund_binding_issues(
    refund: RefundRecord,
    order: Order,
    payment: PaymentExecutionRecord,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    fact = verify_original_transaction(FollowUpAction.REFUND, payment, refund)
    if fact.status.value != "VALID":
        issues.extend(
            ValidationIssue(
                f"refund_{reason}",
                "refund record cannot be bound to the original transaction: " + reason,
            )
            for reason in fact.reason_codes
            if reason not in {
                "original_transaction_payment_ref_mismatch",
                "original_transaction_order_ref_mismatch",
            }
        )
    checks = (
        (
            "original_transaction_payment_ref_mismatch" in fact.reason_codes,
            "refund_payment_binding_mismatch",
            "refund record does not reference the original payment",
        ),
        (
            "original_transaction_order_ref_mismatch" in fact.reason_codes,
            "refund_order_binding_mismatch",
            "refund record does not reference the original order",
        ),
        (
            refund.currency != payment.currency,
            "refund_currency_binding_mismatch",
            "refund currency does not match the original payment currency",
        ),
        (
            refund.amount <= 0,
            "refund_amount_invalid",
            "refund amount must be greater than zero",
        ),
        (
            refund.amount > payment.amount,
            "refund_amount_exceeds_payment",
            "refund amount exceeds the original payment amount",
        ),
    )
    for failed, code, message in checks:
        if failed:
            issues.append(ValidationIssue(code, message))
    return issues


def _dispute_binding_issues(
    dispute: DisputeRecord,
    order: Order,
    payment: PaymentExecutionRecord,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    fact = verify_original_transaction(FollowUpAction.DISPUTE, payment, dispute)
    if fact.status.value != "VALID":
        issues.extend(
            ValidationIssue(
                f"dispute_{reason}",
                "dispute record cannot be bound to the original transaction: " + reason,
            )
            for reason in fact.reason_codes
            if reason not in {
                "original_transaction_payment_ref_mismatch",
                "original_transaction_order_ref_mismatch",
            }
        )
    if "original_transaction_payment_ref_mismatch" in fact.reason_codes:
        issues.append(
            ValidationIssue(
                "dispute_payment_binding_mismatch",
                "dispute record does not reference the original payment",
            )
        )
    if "original_transaction_order_ref_mismatch" in fact.reason_codes:
        issues.append(
            ValidationIssue(
                "dispute_order_binding_mismatch",
                "dispute record does not reference the original order",
            )
        )
    return issues


def _refund_evidence(
    refund: RefundRecord,
    payment: PaymentExecutionRecord,
) -> list[EvidenceRef]:
    evidence = [
        EvidenceRef("refund_record_ref", "refund.refund_id", refund.refund_id),
        EvidenceRef(
            "refund_payment_ref",
            "refund.payment_id",
            refund.payment_id,
            payment.payment_id,
        ),
        EvidenceRef("refund_order_ref", "refund.order_id", refund.order_id, payment.order_id),
        EvidenceRef(
            "refund_currency_ref",
            "refund.currency",
            refund.currency,
            payment.currency,
        ),
        EvidenceRef(
            "refund_amount_ref",
            "refund.amount",
            str(refund.amount),
            f"<= {payment.amount}",
        ),
        EvidenceRef("refund_status_ref", "refund.status", refund.status.value),
    ]
    if refund.receipt_ref:
        evidence.append(EvidenceRef("refund_receipt_ref", "refund.receipt_ref", refund.receipt_ref))
    if refund.reason_code:
        evidence.append(EvidenceRef("refund_reason_code", "refund.reason_code", refund.reason_code))
    return evidence


def _dispute_evidence(
    dispute: DisputeRecord,
    payment: PaymentExecutionRecord,
) -> list[EvidenceRef]:
    evidence = [
        EvidenceRef("dispute_record_ref", "dispute.dispute_id", dispute.dispute_id),
        EvidenceRef(
            "dispute_payment_ref",
            "dispute.payment_id",
            dispute.payment_id,
            payment.payment_id,
        ),
        EvidenceRef("dispute_order_ref", "dispute.order_id", dispute.order_id, payment.order_id),
        EvidenceRef("dispute_status_ref", "dispute.status", dispute.status.value),
    ]
    if dispute.evidence_ref:
        evidence.append(
            EvidenceRef("dispute_evidence_ref", "dispute.evidence_ref", dispute.evidence_ref)
        )
    if dispute.reason_code:
        evidence.append(
            EvidenceRef("dispute_reason_code", "dispute.reason_code", dispute.reason_code)
        )
    return evidence


def _merged_lifecycle(
    lifecycle: LifecycleResult,
    *,
    remediation: RemediationState,
    refund: RefundRecord | None,
    dispute: DisputeRecord | None,
    issues: list[ValidationIssue],
    evidence: list[EvidenceRef],
) -> LifecycleResult:
    return LifecycleResult(
        payment_status=lifecycle.payment_status,
        fulfillment_status=lifecycle.fulfillment_status,
        remediation=remediation,
        task_status=lifecycle.task_status,
        issues=tuple(lifecycle.issues) + tuple(issues),
        evidence=tuple(evidence),
        refund_status=refund.status if refund is not None else None,
        dispute_status=dispute.status if dispute is not None else None,
        rule_version="lifecycle-rules-v0.1+remediation-rules-v0.1",
    )

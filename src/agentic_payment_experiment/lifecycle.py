from __future__ import annotations

from .models import (
    EvidenceRef,
    FulfillmentRecord,
    FulfillmentStatus,
    IntentMandate,
    LifecycleResult,
    Order,
    PaymentExecutionRecord,
    PaymentStatus,
    RemediationState,
    RemediationStatus,
    TaskStatus,
    TransactionRequest,
    ValidationIssue,
)
from .payment_execution import (
    payment_execution_binding_evidence,
    payment_execution_binding_issues,
)
from .trusted_execution import verify_payment_execution_binding


def assess_lifecycle(
    request: TransactionRequest,
    order: Order,
    payment: PaymentExecutionRecord,
    fulfillment: FulfillmentRecord,
    *,
    mandate: IntentMandate | None = None,
) -> LifecycleResult:
    """Assess one offline post-payment lifecycle snapshot.

    This layer is intentionally separate from validate_request(): the pre-payment
    validator decides whether a request is within the user's mandate, while this
    function records what happened after a simulated payment execution. It does
    not issue refunds, open disputes, or assign legal liability.
    """

    evidence = [
        EvidenceRef("lifecycle_request_ref", "request.request_id", request.request_id),
        EvidenceRef("lifecycle_order_ref", "order.order_id", order.order_id),
        EvidenceRef("payment_execution_ref", "payment.payment_id", payment.payment_id),
        EvidenceRef("fulfillment_ref", "fulfillment.fulfillment_id", fulfillment.fulfillment_id),
    ]
    if payment.receipt_ref:
        evidence.append(
            EvidenceRef("payment_receipt_ref", "payment.receipt_ref", payment.receipt_ref)
        )
    if fulfillment.evidence_ref:
        evidence.append(
            EvidenceRef(
                "fulfillment_evidence_ref",
                "fulfillment.evidence_ref",
                fulfillment.evidence_ref,
            )
        )

    if mandate is not None:
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
        binding_issues = list(payment_execution_binding_issues(payment_binding))
        binding_issues.extend(_fulfillment_binding_issues(order, fulfillment))
    else:
        binding_issues = _legacy_binding_issues(
            request,
            order,
            payment,
            fulfillment,
        )
    if binding_issues:
        return LifecycleResult(
            payment_status=payment.status,
            fulfillment_status=fulfillment.status,
            remediation=RemediationState(
                status=RemediationStatus.REQUIRED,
                next_action="preserve_evidence_and_investigate_lifecycle_binding",
            ),
            task_status=TaskStatus.UNKNOWN,
            issues=tuple(binding_issues),
            evidence=tuple(evidence),
        )

    if payment.status is PaymentStatus.SUCCEEDED:
        if fulfillment.status is FulfillmentStatus.SUCCEEDED:
            return LifecycleResult(
                payment_status=payment.status,
                fulfillment_status=fulfillment.status,
                remediation=RemediationState(
                    status=RemediationStatus.NOT_REQUIRED,
                    next_action="none",
                ),
                task_status=TaskStatus.SUCCEEDED,
                issues=(),
                evidence=tuple(evidence),
            )
        if fulfillment.status is FulfillmentStatus.FAILED:
            failure_code = fulfillment.failure_code or "fulfillment_failed"
            evidence.append(
                EvidenceRef(
                    "fulfillment_failure_code",
                    "fulfillment.failure_code",
                    failure_code,
                    "successful fulfilment",
                )
            )
            return LifecycleResult(
                payment_status=payment.status,
                fulfillment_status=fulfillment.status,
                remediation=RemediationState(
                    status=RemediationStatus.REQUIRED,
                    next_action="preserve_evidence_and_start_remediation",
                ),
                task_status=TaskStatus.FAILED,
                issues=(
                    ValidationIssue(
                        "fulfillment_failed_after_payment",
                        "payment succeeded but the purchased good or service was not fulfilled",
                    ),
                ),
                evidence=tuple(evidence),
            )
        if fulfillment.status is FulfillmentStatus.PENDING:
            return LifecycleResult(
                payment_status=payment.status,
                fulfillment_status=fulfillment.status,
                remediation=RemediationState(
                    status=RemediationStatus.NOT_REQUIRED,
                    next_action="wait_for_fulfillment_status",
                ),
                task_status=TaskStatus.PENDING,
                issues=(),
                evidence=tuple(evidence),
            )
        return LifecycleResult(
            payment_status=payment.status,
            fulfillment_status=fulfillment.status,
            remediation=RemediationState(
                status=RemediationStatus.REQUIRED,
                next_action="preserve_evidence_and_investigate_fulfillment_status",
            ),
            task_status=TaskStatus.UNKNOWN,
            issues=(
                ValidationIssue(
                    "fulfillment_status_unknown_after_payment",
                    "payment succeeded but fulfilment status is unknown",
                ),
            ),
            evidence=tuple(evidence),
        )

    if payment.status is PaymentStatus.FAILED:
        return LifecycleResult(
            payment_status=payment.status,
            fulfillment_status=fulfillment.status,
            remediation=RemediationState(
                status=RemediationStatus.NOT_REQUIRED,
                next_action="do_not_treat_task_as_successful",
            ),
            task_status=TaskStatus.FAILED,
            issues=(
                ValidationIssue(
                    "payment_execution_failed",
                    "the simulated payment execution failed",
                ),
            ),
            evidence=tuple(evidence),
        )

    if payment.status is PaymentStatus.PENDING:
        return LifecycleResult(
            payment_status=payment.status,
            fulfillment_status=fulfillment.status,
            remediation=RemediationState(
                status=RemediationStatus.NOT_REQUIRED,
                next_action="wait_for_payment_status",
            ),
            task_status=TaskStatus.PENDING,
            issues=(),
            evidence=tuple(evidence),
        )

    return LifecycleResult(
        payment_status=payment.status,
        fulfillment_status=fulfillment.status,
        remediation=RemediationState(
            status=RemediationStatus.REQUIRED,
            next_action="preserve_evidence_and_investigate_payment_status",
        ),
        task_status=TaskStatus.UNKNOWN,
        issues=(
            ValidationIssue(
                "payment_status_unknown",
                "the simulated payment execution status is unknown",
            ),
        ),
        evidence=tuple(evidence),
    )


def _legacy_binding_issues(
    request: TransactionRequest,
    order: Order,
    payment: PaymentExecutionRecord,
    fulfillment: FulfillmentRecord,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    checks = (
        (
            payment.request_id != request.request_id,
            "payment_request_binding_mismatch",
            "payment record does not reference the validated request",
        ),
        (
            payment.order_id != order.order_id,
            "payment_order_binding_mismatch",
            "payment record does not reference the expected order",
        ),
        (
            payment.amount != request.amount,
            "payment_amount_binding_mismatch",
            "payment amount does not match the validated request",
        ),
        (
            payment.currency != request.currency,
            "payment_currency_binding_mismatch",
            "payment currency does not match the validated request",
        ),
        (
            fulfillment.order_id != order.order_id,
            "fulfillment_order_binding_mismatch",
            "fulfilment record does not reference the expected order",
        ),
        (
            bool(order.service_id and fulfillment.service_id)
            and order.service_id != fulfillment.service_id,
            "fulfillment_service_binding_mismatch",
            "fulfilment record references a different service",
        ),
    )
    for failed, code, message in checks:
        if failed:
            issues.append(ValidationIssue(code, message))
    return issues


def _fulfillment_binding_issues(
    order: Order,
    fulfillment: FulfillmentRecord,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    checks = (
        (
            fulfillment.order_id != order.order_id,
            "fulfillment_order_binding_mismatch",
            "fulfilment record does not reference the expected order",
        ),
        (
            bool(order.service_id and fulfillment.service_id)
            and order.service_id != fulfillment.service_id,
            "fulfillment_service_binding_mismatch",
            "fulfilment record references a different service",
        ),
    )
    for failed, code, message in checks:
        if failed:
            issues.append(ValidationIssue(code, message))
    return issues

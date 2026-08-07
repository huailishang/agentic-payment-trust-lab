"""Pure product-observed authoritative trace builder for the T10 slice.

This module only projects immutable facts that the WebShop Buy Now gate has
already produced.  It does not rerun authorization, binding, duplicate-payment,
or payment execution logic, and it has no file, clock, random, network, or
callback dependency.
"""

from __future__ import annotations

from typing import Any

from .authoritative_trace import (
    ProductAuthoritativeTrace,
    TraceBindingAssertion,
    TraceContractError,
)
from .models import (
    Decision,
    IntentMandate,
    Order,
    PaymentExecutionRecord,
    PaymentStatus,
    TransactionRequest,
    ValidationResult,
)
from .trusted_execution import (
    GovernedActionBindingFact,
    GovernedPaymentAction,
    KnownPaymentAttemptPreflightFact,
    KnownPaymentAttemptPreflightStatus,
    RuntimeGateRecord,
    VerificationStatus,
)
from .webshop_trace_assembler import (
    assemble_product_trace,
    create_event,
    create_relation,
    create_source_binding,
    project_action_binding_fact,
    project_governed_action,
    project_mandate,
    project_order,
    project_payment,
    project_request,
    project_runtime_gate,
)


T10_PROFILE = "WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V2"


def _known_fact_projection(
    fact: KnownPaymentAttemptPreflightFact,
) -> dict[str, Any]:
    return {
        "status": fact.status,
        "reason_codes": fact.reason_codes,
        "current_request_ref": fact.current_request_ref,
        "related_attempt_refs": fact.related_attempt_refs,
        "blocking_request_refs": fact.blocking_request_refs,
        "limitations": fact.limitations,
    }


def _validation_projection(result: ValidationResult) -> dict[str, Any]:
    return {
        "decision": result.decision,
        "issue_codes": tuple(issue.code for issue in result.issues),
        "evidence_paths": tuple(item.field_path for item in result.evidence),
        "rule_version": result.rule_version,
        "order_difference_paths": tuple(
            item.field_path for item in result.order_differences
        ),
    }


def _outcome_projection(
    *,
    decision: Decision,
    checkout_executed: bool,
    callback_count: int,
    callback_result_ref: str | None,
    reason_codes: tuple[str, ...],
    limitations: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "decision": decision,
        "checkout_executed": checkout_executed,
        "callback_count": callback_count,
        "callback_result_ref": callback_result_ref,
        "reason_codes": reason_codes,
        "limitations": limitations,
    }


def _unique_historical_success(
    known_payment_attempts: tuple[PaymentExecutionRecord, ...],
    known_attempt_fact: KnownPaymentAttemptPreflightFact,
    current_request: TransactionRequest,
    execution_candidate: PaymentExecutionRecord,
) -> PaymentExecutionRecord | None:
    if type(known_payment_attempts) is not tuple:
        return None
    if len(known_attempt_fact.related_attempt_refs) != 1:
        return None
    if known_attempt_fact.current_request_ref != current_request.request_id:
        return None
    if known_attempt_fact.blocking_request_refs != (current_request.request_id,):
        return None

    expected_payment_ref = known_attempt_fact.related_attempt_refs[0]
    matches = tuple(
        attempt
        for attempt in known_payment_attempts
        if type(attempt) is PaymentExecutionRecord
        and attempt.payment_id == expected_payment_ref
    )
    if len(matches) != 1:
        return None
    historical = matches[0]
    if historical.status is not PaymentStatus.SUCCEEDED:
        return None
    if historical.payment_id == execution_candidate.payment_id:
        return None
    return historical


def build_t10_duplicate_preflight_trace(
    *,
    mandate: IntentMandate,
    authorized_order: Order,
    current_order: Order,
    bound_request: TransactionRequest,
    governed_action: GovernedPaymentAction | None,
    execution_candidate: PaymentExecutionRecord,
    governed_action_fact: GovernedActionBindingFact | None,
    known_payment_attempts: tuple[PaymentExecutionRecord, ...],
    known_attempt_fact: KnownPaymentAttemptPreflightFact,
    duplicate_result: ValidationResult,
    runtime_record: RuntimeGateRecord,
    outcome_decision: Decision,
    outcome_checkout_executed: bool,
    outcome_callback_count: int,
    outcome_callback_result_ref: str | None,
    outcome_reason_codes: tuple[str, ...],
    outcome_limitations: tuple[str, ...],
) -> ProductAuthoritativeTrace | None:
    """Build the exact T10 product trace or fail closed with ``None``.

    All inputs are already-produced immutable facts from one gate invocation.
    The function deliberately performs no business-rule calls or side effects.
    """

    exact_types = (
        type(mandate) is IntentMandate,
        type(authorized_order) is Order,
        type(current_order) is Order,
        type(bound_request) is TransactionRequest,
        type(execution_candidate) is PaymentExecutionRecord,
        type(known_attempt_fact) is KnownPaymentAttemptPreflightFact,
        type(duplicate_result) is ValidationResult,
        type(runtime_record) is RuntimeGateRecord,
        type(outcome_decision) is Decision,
        type(outcome_reason_codes) is tuple,
        type(outcome_limitations) is tuple,
    )
    if not all(exact_types):
        return None
    if type(governed_action) is not GovernedPaymentAction:
        return None
    if type(governed_action_fact) is not GovernedActionBindingFact:
        return None
    if governed_action_fact.status is not VerificationStatus.VALID:
        return None
    if known_attempt_fact.status is not KnownPaymentAttemptPreflightStatus.BLOCKED:
        return None
    if duplicate_result.decision is not Decision.DENY:
        return None
    if runtime_record.final_decision is not Decision.DENY:
        return None
    if outcome_decision is not Decision.DENY:
        return None
    if outcome_checkout_executed or outcome_callback_count != 0:
        return None
    if outcome_callback_result_ref is not None:
        return None
    if runtime_record.callback_executed or runtime_record.callback_count != 0:
        return None
    if runtime_record.callback_result_ref is not None:
        return None

    authorized_projection = project_order(authorized_order)
    current_projection = project_order(current_order)
    if authorized_projection != current_projection:
        return None

    historical_payment = _unique_historical_success(
        known_payment_attempts,
        known_attempt_fact,
        bound_request,
        execution_candidate,
    )
    if historical_payment is None:
        return None

    try:
        mandate_binding = create_source_binding(
            "IntentMandate",
            "intent-mandate-trace/v2",
            project_mandate(mandate),
        )
        order_binding = create_source_binding(
            "Order",
            "order-snapshot-trace/v2",
            current_projection,
        )
        request_binding = create_source_binding(
            "TransactionRequest",
            "transaction-request-trace/v2",
            project_request(bound_request),
        )
        action_binding = create_source_binding(
            "GovernedPaymentAction",
            "governed-payment-action-trace/v2",
            project_governed_action(governed_action),
        )
        candidate_binding = create_source_binding(
            "PaymentExecutionRecord",
            "payment-execution-record-trace/v2",
            project_payment(execution_candidate),
        )
        action_fact_binding = create_source_binding(
            "GovernedActionBindingFact",
            "governed-action-binding-fact-trace/v2",
            project_action_binding_fact(governed_action_fact),
        )
        historical_binding = create_source_binding(
            "PaymentExecutionRecord",
            "payment-execution-record-trace/v2",
            project_payment(historical_payment),
        )
        known_fact_binding = create_source_binding(
            "KnownPaymentAttemptPreflightFact",
            "known-payment-attempt-preflight-fact-trace/v2",
            _known_fact_projection(known_attempt_fact),
        )
        validation_binding = create_source_binding(
            "ValidationResult",
            "validation-result-trace/v2",
            _validation_projection(duplicate_result),
        )
        runtime_binding = create_source_binding(
            "RuntimeGateRecord",
            "runtime-gate-record-trace/v2",
            project_runtime_gate(runtime_record),
        )
        outcome_binding = create_source_binding(
            "WebShopBuyNowGateOutcome",
            "webshop-buy-now-gate-outcome-result-trace/v2",
            _outcome_projection(
                decision=outcome_decision,
                checkout_executed=outcome_checkout_executed,
                callback_count=outcome_callback_count,
                callback_result_ref=outcome_callback_result_ref,
                reason_codes=outcome_reason_codes,
                limitations=outcome_limitations,
            ),
        )

        authority_ref = f"IntentMandate:{mandate.mandate_id}"
        order_ref = f"Order:{current_order.order_id}"
        request_ref = f"TransactionRequest:{bound_request.request_id}"
        action_ref = f"GovernedPaymentAction:{governed_action.action_id}"
        candidate_ref = (
            f"PaymentExecutionRecord:{execution_candidate.payment_id}"
        )
        historical_ref = (
            f"PaymentExecutionRecord:{historical_payment.payment_id}"
        )

        authority_version_assertion = TraceBindingAssertion(
            source_path="projection.authority_version_ref",
            target_path="projection.authority_version",
        )
        action_authority_assertion = TraceBindingAssertion(
            source_path="projection.authority_version",
            target_path="projection.authority_version",
        )
        action_order_assertion = TraceBindingAssertion(
            source_path="projection.order_version",
            target_path="projection.order_version",
        )

        events = (
            create_event(
                1,
                "AUTHORITY_RECORDED",
                "IntentMandate",
                "AUTHORITY",
                mandate_binding,
                "IntentMandate:{projection.mandate_id}",
            ),
            create_event(
                2,
                "ORDER_RECORDED",
                "Order",
                "AUTHORIZED_ORDER_SNAPSHOT",
                order_binding,
                "Order:{projection.order_id}",
                relations=(
                    create_relation(
                        "BOUND_TO",
                        "IntentMandate",
                        "AUTHORITY",
                        authority_ref,
                        assertions=(authority_version_assertion,),
                    ),
                ),
            ),
            create_event(
                3,
                "ORDER_RECORDED",
                "Order",
                "CURRENT_ORDER_SNAPSHOT",
                order_binding,
                "Order:{projection.order_id}",
                relations=(
                    create_relation(
                        "BOUND_TO",
                        "IntentMandate",
                        "AUTHORITY",
                        authority_ref,
                        assertions=(authority_version_assertion,),
                    ),
                ),
            ),
            create_event(
                4,
                "REQUEST_RECORDED",
                "TransactionRequest",
                "CURRENT_REQUEST",
                request_binding,
                "TransactionRequest:{projection.request_id}",
                relations=(
                    create_relation(
                        "BOUND_TO",
                        "Order",
                        "CURRENT_ORDER_SNAPSHOT",
                        order_ref,
                    ),
                    create_relation(
                        "BOUND_TO",
                        "IntentMandate",
                        "AUTHORITY",
                        authority_ref,
                        assertions=(authority_version_assertion,),
                    ),
                ),
            ),
            create_event(
                5,
                "ACTION_RECORDED",
                "GovernedPaymentAction",
                "GOVERNED_ACTION",
                action_binding,
                "GovernedPaymentAction:{projection.action_id}",
                relations=(
                    create_relation(
                        "BOUND_TO",
                        "IntentMandate",
                        "AUTHORITY",
                        authority_ref,
                        assertions=(action_authority_assertion,),
                    ),
                    create_relation(
                        "BOUND_TO",
                        "Order",
                        "CURRENT_ORDER_SNAPSHOT",
                        order_ref,
                        assertions=(action_order_assertion,),
                    ),
                    create_relation(
                        "BOUND_TO",
                        "TransactionRequest",
                        "CURRENT_REQUEST",
                        request_ref,
                    ),
                    create_relation(
                        "BOUND_TO",
                        "PaymentExecutionRecord",
                        "CURRENT_PAYMENT_CANDIDATE",
                        candidate_ref,
                    ),
                ),
            ),
            create_event(
                6,
                "PAYMENT_CANDIDATE_RECORDED",
                "PaymentExecutionRecord",
                "CURRENT_PAYMENT_CANDIDATE",
                candidate_binding,
                "PaymentExecutionRecord:{projection.payment_id}",
                status=execution_candidate.status.value,
                relations=(
                    create_relation(
                        "BOUND_TO",
                        "TransactionRequest",
                        "CURRENT_REQUEST",
                        request_ref,
                    ),
                    create_relation(
                        "BOUND_TO",
                        "Order",
                        "CURRENT_ORDER_SNAPSHOT",
                        order_ref,
                    ),
                ),
            ),
            create_event(
                7,
                "ACTION_BINDING_DECISION_RECORDED",
                "GovernedActionBindingFact",
                "ACTION_BINDING_FACT",
                action_fact_binding,
                "GovernedActionBindingFact:binding:{binding_digest}",
                status=governed_action_fact.status.value,
                reason_codes=governed_action_fact.reason_codes,
                relations=(
                    create_relation(
                        "VALIDATED_AGAINST",
                        "GovernedPaymentAction",
                        "GOVERNED_ACTION",
                        action_ref,
                    ),
                    create_relation(
                        "VALIDATED_AGAINST",
                        "PaymentExecutionRecord",
                        "CURRENT_PAYMENT_CANDIDATE",
                        candidate_ref,
                    ),
                ),
            ),
            create_event(
                8,
                "PAYMENT_OUTCOME_RECORDED",
                "PaymentExecutionRecord",
                "HISTORICAL_SUCCEEDED_PAYMENT",
                historical_binding,
                "PaymentExecutionRecord:{projection.payment_id}",
                status=historical_payment.status.value,
                relations=(
                    create_relation(
                        "BOUND_TO",
                        "TransactionRequest",
                        "CURRENT_REQUEST",
                        request_ref,
                    ),
                    create_relation(
                        "BOUND_TO",
                        "Order",
                        "CURRENT_ORDER_SNAPSHOT",
                        order_ref,
                    ),
                ),
            ),
            create_event(
                9,
                "KNOWN_PAYMENT_PREFLIGHT_RECORDED",
                "KnownPaymentAttemptPreflightFact",
                "KNOWN_PAYMENT_PREFLIGHT_FACT",
                known_fact_binding,
                "KnownPaymentAttemptPreflightFact:binding:{binding_digest}",
                status=known_attempt_fact.status.value,
                reason_codes=known_attempt_fact.reason_codes,
                relations=(
                    create_relation(
                        "VALIDATED_AGAINST",
                        "TransactionRequest",
                        "CURRENT_REQUEST",
                        request_ref,
                    ),
                    create_relation(
                        "MEMBER_OF",
                        "PaymentExecutionRecord",
                        "HISTORICAL_SUCCEEDED_PAYMENT",
                        historical_ref,
                    ),
                ),
            ),
            create_event(
                10,
                "PREPAYMENT_DECISION_RECORDED",
                "ValidationResult",
                "PREPAYMENT_VALIDATION",
                validation_binding,
                "ValidationResult:binding:{binding_digest}",
                decision=duplicate_result.decision.value,
                reason_codes=tuple(issue.code for issue in duplicate_result.issues),
            ),
            create_event(
                11,
                "RUNTIME_DECISION_RECORDED",
                "RuntimeGateRecord",
                "RUNTIME_GATE_OBSERVATION",
                runtime_binding,
                "RuntimeGateRecord:binding:{binding_digest}",
                decision=runtime_record.final_decision.value,
                status=runtime_record.binding_status,
                reason_codes=runtime_record.reason_codes,
            ),
            create_event(
                12,
                "RESULT_RECORDED",
                "WebShopBuyNowGateOutcome",
                "FINAL_OUTCOME",
                outcome_binding,
                "WebShopBuyNowGateOutcome:binding:{binding_digest}",
                decision=outcome_decision.value,
                reason_codes=outcome_reason_codes,
            ),
        )

        source_bindings = (
            mandate_binding,
            order_binding,
            request_binding,
            action_binding,
            candidate_binding,
            action_fact_binding,
            historical_binding,
            known_fact_binding,
            validation_binding,
            runtime_binding,
            outcome_binding,
        )
        return assemble_product_trace(
            profile=T10_PROFILE,
            trace_ref=(
                f"ProductAuthoritativeTrace:{T10_PROFILE}:"
                f"{bound_request.request_id}"
            ),
            events=events,
            source_bindings=source_bindings,
            expected_unique_binding_count=11,
        )
    except (KeyError, TypeError, ValueError, TraceContractError):
        return None


__all__ = ["T10_PROFILE", "build_t10_duplicate_preflight_trace"]

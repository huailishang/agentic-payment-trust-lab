"""Product-observed traces for early governed-action binding rejection.

This module only projects immutable facts already produced by the WebShop gate.
It does not rerun authorization, action verification, payment policy, callbacks,
or evaluator logic.  Profile selection is derived from the action-binding fact
shape and its verification evidence.
"""

from __future__ import annotations

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
    TransactionRequest,
    ValidationResult,
)
from .trusted_execution import (
    GovernedActionBindingFact,
    GovernedPaymentAction,
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
    project_validation_result,
    project_webshop_gate_outcome,
)


_AGENT_MISMATCH_PROFILE = "WEBSHOP_ACTION_BINDING_T05_V2"
_MISSING_ACTION_ID_PROFILE = "WEBSHOP_ACTION_BINDING_T06_V2"
_AGENT_MISMATCH_REASONS = (
    "agent_ref_request_mismatch",
    "agent_ref_mandate_mismatch",
    "agent_ref_identity_mismatch",
)
_MISSING_ACTION_ID_REASONS = ("action_id_missing",)


def _select_profile(
    action: GovernedPaymentAction,
    fact: GovernedActionBindingFact,
) -> tuple[str, str] | None:
    """Return ``(profile, action_projection_schema)`` from product facts only."""

    if fact.status is VerificationStatus.INVALID:
        if (
            not action.action_id
            or fact.action_id != action.action_id
            or fact.reason_codes != _AGENT_MISMATCH_REASONS
        ):
            return None
        return _AGENT_MISMATCH_PROFILE, "governed-payment-action-trace/v2"

    if fact.status is VerificationStatus.MISSING_EVIDENCE:
        if (
            action.action_id
            or fact.action_id is not None
            or fact.reason_codes != _MISSING_ACTION_ID_REASONS
        ):
            return None
        return (
            _MISSING_ACTION_ID_PROFILE,
            "governed-payment-action-missing-id-trace/v2",
        )

    return None


def build_action_binding_rejection_trace(
    *,
    mandate: IntentMandate,
    authorized_order: Order,
    current_order: Order,
    bound_request: TransactionRequest,
    prepayment_result: ValidationResult,
    governed_action: GovernedPaymentAction,
    execution_candidate: PaymentExecutionRecord,
    governed_action_fact: GovernedActionBindingFact,
    base_outcome: object,
) -> ProductAuthoritativeTrace | None:
    """Build a complete early-rejection trace or fail closed with ``None``."""

    exact_types = (
        type(mandate) is IntentMandate,
        type(authorized_order) is Order,
        type(current_order) is Order,
        type(bound_request) is TransactionRequest,
        type(prepayment_result) is ValidationResult,
        type(governed_action) is GovernedPaymentAction,
        type(execution_candidate) is PaymentExecutionRecord,
        type(governed_action_fact) is GovernedActionBindingFact,
    )
    if not all(exact_types):
        return None
    if prepayment_result.decision is not Decision.ALLOW:
        return None

    profile = _select_profile(governed_action, governed_action_fact)
    if profile is None:
        return None
    profile_name, action_projection_schema = profile

    expected_decision = (
        Decision.INDETERMINATE
        if governed_action_fact.status is VerificationStatus.MISSING_EVIDENCE
        else Decision.DENY
    )
    expected_reasons = tuple(
        f"action:{code}" for code in governed_action_fact.reason_codes
    )
    if (
        getattr(base_outcome, "decision", None) is not expected_decision
        or getattr(base_outcome, "checkout_executed", None) is not False
        or getattr(base_outcome, "callback_count", None) != 0
        or getattr(base_outcome, "callback_result_ref", None) is not None
        or getattr(base_outcome, "bound_request", None) != bound_request
        or getattr(base_outcome, "prepayment_result", None) != prepayment_result
        or getattr(base_outcome, "runtime_gate_record", None) is not None
        or getattr(base_outcome, "reason_codes", None) != expected_reasons
        or getattr(base_outcome, "governed_action_fact", None)
        != governed_action_fact
        or getattr(base_outcome, "authoritative_trace", None) is not None
    ):
        return None

    authorized_projection = project_order(authorized_order)
    current_projection = project_order(current_order)
    if authorized_projection != current_projection:
        return None
    if (
        bound_request.order_ref != current_order.order_id
        or bound_request.authority_ref != mandate.mandate_id
        or bound_request.authority_version_ref != mandate.authority_version
        or execution_candidate.request_id != bound_request.request_id
        or execution_candidate.order_id != current_order.order_id
        or governed_action_fact.checked_order_ref != current_order.order_id
        or governed_action_fact.checked_request_ref != bound_request.request_id
        or governed_action_fact.checked_payment_ref != execution_candidate.payment_id
    ):
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
        validation_binding = create_source_binding(
            "ValidationResult",
            "validation-result-trace/v2",
            project_validation_result(prepayment_result),
        )
        action_binding = create_source_binding(
            "GovernedPaymentAction",
            action_projection_schema,
            project_governed_action(governed_action),
        )
        payment_binding = create_source_binding(
            "PaymentExecutionRecord",
            "payment-execution-record-trace/v2",
            project_payment(execution_candidate),
        )
        fact_binding = create_source_binding(
            "GovernedActionBindingFact",
            "governed-action-binding-fact-trace/v2",
            project_action_binding_fact(governed_action_fact),
        )
        outcome_binding = create_source_binding(
            "WebShopBuyNowGateOutcome",
            "webshop-buy-now-gate-outcome-result-trace/v2",
            project_webshop_gate_outcome(base_outcome),
        )

        authority_ref = f"IntentMandate:{mandate.mandate_id}"
        order_ref = f"Order:{current_order.order_id}"
        request_ref = f"TransactionRequest:{bound_request.request_id}"
        payment_ref = f"PaymentExecutionRecord:{execution_candidate.payment_id}"

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

        action_relations = (
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
                payment_ref,
            ),
        )

        if governed_action_fact.status is VerificationStatus.INVALID:
            action_ref = f"GovernedPaymentAction:{governed_action.action_id}"
            fact_relations = (
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
                    payment_ref,
                ),
            )
            action_entity_template = "GovernedPaymentAction:{projection.action_id}"
        else:
            fact_relations = (
                create_relation(
                    "VALIDATED_AGAINST",
                    "PaymentExecutionRecord",
                    "CURRENT_PAYMENT_CANDIDATE",
                    payment_ref,
                ),
            )
            action_entity_template = "GovernedPaymentAction:binding:{binding_digest}"

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
                "PREPAYMENT_DECISION_RECORDED",
                "ValidationResult",
                "PREPAYMENT_VALIDATION",
                validation_binding,
                "ValidationResult:binding:{binding_digest}",
                decision=prepayment_result.decision.value,
                reason_codes=tuple(item.code for item in prepayment_result.issues),
            ),
            create_event(
                6,
                "ACTION_RECORDED",
                "GovernedPaymentAction",
                "GOVERNED_ACTION",
                action_binding,
                action_entity_template,
                relations=action_relations,
            ),
            create_event(
                7,
                "PAYMENT_CANDIDATE_RECORDED",
                "PaymentExecutionRecord",
                "CURRENT_PAYMENT_CANDIDATE",
                payment_binding,
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
                8,
                "ACTION_BINDING_DECISION_RECORDED",
                "GovernedActionBindingFact",
                "ACTION_BINDING_FACT",
                fact_binding,
                "GovernedActionBindingFact:binding:{binding_digest}",
                status=governed_action_fact.status.value,
                reason_codes=governed_action_fact.reason_codes,
                relations=fact_relations,
            ),
            create_event(
                9,
                "RESULT_RECORDED",
                "WebShopBuyNowGateOutcome",
                "FINAL_OUTCOME",
                outcome_binding,
                "WebShopBuyNowGateOutcome:binding:{binding_digest}",
                decision=expected_decision.value,
                reason_codes=expected_reasons,
            ),
        )

        return assemble_product_trace(
            profile=profile_name,
            trace_ref=(
                "WebShopActionBindingRejectionTrace:"
                f"{profile_name}:{bound_request.request_id}"
            ),
            events=events,
            source_bindings=(
                mandate_binding,
                order_binding,
                request_binding,
                validation_binding,
                action_binding,
                payment_binding,
                fact_binding,
                outcome_binding,
            ),
            expected_unique_binding_count=8,
        )
    except (AttributeError, KeyError, TypeError, ValueError, TraceContractError):
        return None


__all__ = ["build_action_binding_rejection_trace"]

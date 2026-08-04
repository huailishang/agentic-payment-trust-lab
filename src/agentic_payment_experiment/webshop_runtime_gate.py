"""Offline WebShop Buy Now interception composed from existing P1-P4 gates."""

from __future__ import annotations

from collections.abc import Callable, Collection
from dataclasses import dataclass, replace
from typing import Any

from .adapters.webshop import WebShopCommerceAdaptation
from .models import (
    AgentIdentity,
    Decision,
    IntentMandate,
    PaymentExecutionRecord,
    TransactionRequest,
    ValidationResult,
)
from .payment_execution import observe_payment_execution_gate
from .trusted_execution import (
    ConfirmationRecord,
    ContextPolicyFact,
    GovernedActionBindingFact,
    GovernedPaymentAction,
    KnownPaymentAttemptPreflightFact,
    KnownPaymentAttemptPreflightStatus,
    RuntimeGateRecord,
    VerificationStatus,
    derive_known_payment_attempt_preflight,
    verify_governed_payment_action,
)
from .validator import validate_request


WEBSHOP_GATE_LIMITATIONS = (
    "offline_interception_only",
    "no_webshop_runtime_execution",
    "no_real_buy_now_execution",
    "no_real_payment_or_fulfilment",
    "instruction_is_not_authorization_mandate",
    "checkout_callback_is_injected_test_seam",
)
_CALLBACK_FAILURE_SENTINEL = "webshop-checkout-callback-failed"


@dataclass(frozen=True)
class WebShopBuyNowGateOutcome:
    """Immutable result of one offline pre-checkout gate invocation."""

    decision: Decision
    checkout_executed: bool
    callback_count: int
    callback_result_ref: str | None
    bound_request: TransactionRequest | None
    prepayment_result: ValidationResult | None
    runtime_gate_record: RuntimeGateRecord | None
    reason_codes: tuple[str, ...]
    governed_action_fact: GovernedActionBindingFact | None = None
    known_payment_attempt_preflight_fact: KnownPaymentAttemptPreflightFact | None = None
    limitations: tuple[str, ...] = WEBSHOP_GATE_LIMITATIONS


def gate_webshop_buy_now(
    adaptation: WebShopCommerceAdaptation | None,
    mandate: IntentMandate | None,
    declared_agent_id: str | None,
    execution_candidate: PaymentExecutionRecord | None,
    agent_identity: AgentIdentity | None,
    current_provider_ref: str | None,
    current_executor_instance_ref: str | None,
    context_policy_fact: ContextPolicyFact | None,
    checkout_callback: Callable[[], Any] | None,
    *,
    current_credential_ref: str | None = None,
    confirmation_record: ConfirmationRecord | None = None,
    seen_request_ids: Collection[str] = (),
    authorized_adaptation: WebShopCommerceAdaptation | None = None,
    governed_action: GovernedPaymentAction | None = None,
    known_payment_attempts: tuple[PaymentExecutionRecord, ...] = (),
) -> WebShopBuyNowGateOutcome:
    """Allow an injected checkout seam only after existing P1-P4 checks pass.

    Every authority, identity, execution and context fact is supplied explicitly.
    Natural-language instruction text, product title, page content and WebShop
    reward are never used to derive authorization.
    """

    if adaptation is None or not adaptation.ready:
        return _blocked("commerce_adaptation_not_ready")
    if adaptation.order is None or adaptation.payment_request is None:
        return _blocked("commerce_adaptation_objects_missing")

    authorized_snapshot = authorized_adaptation or adaptation
    if not authorized_snapshot.ready:
        return _blocked("authorized_commerce_adaptation_not_ready")
    if (
        authorized_snapshot.order is None
        or authorized_snapshot.payment_request is None
    ):
        return _blocked("authorized_commerce_adaptation_objects_missing")
    if not isinstance(declared_agent_id, str) or not declared_agent_id.strip():
        return _blocked("declared_agent_id_missing")

    missing_inputs = _missing_explicit_inputs(
        mandate=mandate,
        execution_candidate=execution_candidate,
        agent_identity=agent_identity,
        current_provider_ref=current_provider_ref,
        current_executor_instance_ref=current_executor_instance_ref,
        context_policy_fact=context_policy_fact,
        checkout_callback=checkout_callback,
    )
    if missing_inputs:
        return _blocked(*missing_inputs)

    assert mandate is not None
    assert execution_candidate is not None
    assert agent_identity is not None
    assert context_policy_fact is not None
    assert checkout_callback is not None
    assert current_provider_ref is not None
    assert current_executor_instance_ref is not None

    bound_request = replace(
        adaptation.payment_request,
        agent_id=declared_agent_id.strip(),
    )
    prepayment_result = validate_request(
        mandate,
        bound_request,
        seen_request_ids=seen_request_ids,
        authorized_order=authorized_snapshot.order,
        final_order=adaptation.order,
        confirmation_record=confirmation_record,
    )
    if prepayment_result.decision is not Decision.ALLOW:
        return WebShopBuyNowGateOutcome(
            decision=prepayment_result.decision,
            checkout_executed=False,
            callback_count=0,
            callback_result_ref=None,
            bound_request=bound_request,
            prepayment_result=prepayment_result,
            runtime_gate_record=None,
            reason_codes=_prepayment_reason_codes(prepayment_result),
        )

    governed_action_fact: GovernedActionBindingFact | None = None
    if governed_action is not None:
        governed_action_fact = verify_governed_payment_action(
            governed_action,
            mandate=mandate,
            order=adaptation.order,
            request=bound_request,
            execution=execution_candidate,
            agent_identity=agent_identity,
            current_executor_instance_ref=current_executor_instance_ref,
            context_policy_fact=context_policy_fact,
        )
        if governed_action_fact.status is not VerificationStatus.VALID:
            return WebShopBuyNowGateOutcome(
                decision=(
                    Decision.INDETERMINATE
                    if governed_action_fact.status
                    is VerificationStatus.MISSING_EVIDENCE
                    else Decision.DENY
                ),
                checkout_executed=False,
                callback_count=0,
                callback_result_ref=None,
                bound_request=bound_request,
                prepayment_result=prepayment_result,
                runtime_gate_record=None,
                reason_codes=tuple(
                    f"action:{code}"
                    for code in governed_action_fact.reason_codes
                ),
                governed_action_fact=governed_action_fact,
            )

    callback_failure: list[str] = []

    def guarded_checkout_callback() -> Any:
        try:
            return checkout_callback()
        except Exception as exc:  # The injected seam is untrusted application code.
            callback_failure.append(type(exc).__name__)
            return _CALLBACK_FAILURE_SENTINEL

    def observe_runtime(decision: Decision) -> RuntimeGateRecord:
        return observe_payment_execution_gate(
            decision,
            mandate,
            adaptation.order,
            bound_request,
            execution_candidate,
            guarded_checkout_callback,
            agent_identity=agent_identity,
            current_provider_ref=current_provider_ref,
            current_executor_instance_ref=current_executor_instance_ref,
            current_credential_ref=current_credential_ref,
            context_policy_fact=context_policy_fact,
        )

    known_attempt_fact: KnownPaymentAttemptPreflightFact | None = None
    if type(known_payment_attempts) is not tuple or known_payment_attempts:
        known_attempt_fact = derive_known_payment_attempt_preflight(
            mandate,
            adaptation.order,
            bound_request,
            known_payment_attempts,
        )
        preflight_reasons = tuple(
            f"preflight:{code}" for code in known_attempt_fact.reason_codes
        )
        if (
            known_attempt_fact.status
            is KnownPaymentAttemptPreflightStatus.INDETERMINATE
        ):
            runtime_record = observe_runtime(Decision.INDETERMINATE)
            runtime_record = replace(
                runtime_record,
                reason_codes=tuple(
                    sorted(set((*runtime_record.reason_codes, *preflight_reasons)))
                ),
            )
            return WebShopBuyNowGateOutcome(
                decision=Decision.INDETERMINATE,
                checkout_executed=False,
                callback_count=runtime_record.callback_count,
                callback_result_ref=None,
                bound_request=bound_request,
                prepayment_result=prepayment_result,
                runtime_gate_record=runtime_record,
                reason_codes=runtime_record.reason_codes,
                governed_action_fact=governed_action_fact,
                known_payment_attempt_preflight_fact=known_attempt_fact,
            )
        if known_attempt_fact.status is KnownPaymentAttemptPreflightStatus.BLOCKED:
            trusted_seen_request_ids = (
                *tuple(seen_request_ids),
                *known_attempt_fact.blocking_request_refs,
            )
            duplicate_result = validate_request(
                mandate,
                bound_request,
                seen_request_ids=trusted_seen_request_ids,
                authorized_order=authorized_snapshot.order,
                final_order=adaptation.order,
                confirmation_record=confirmation_record,
            )
            runtime_record = observe_runtime(duplicate_result.decision)
            runtime_record = replace(
                runtime_record,
                reason_codes=tuple(
                    sorted(
                        set(
                            (
                                *runtime_record.reason_codes,
                                *_prepayment_reason_codes(duplicate_result),
                                *preflight_reasons,
                            )
                        )
                    )
                ),
            )
            return WebShopBuyNowGateOutcome(
                decision=duplicate_result.decision,
                checkout_executed=False,
                callback_count=runtime_record.callback_count,
                callback_result_ref=None,
                bound_request=bound_request,
                prepayment_result=duplicate_result,
                runtime_gate_record=runtime_record,
                reason_codes=runtime_record.reason_codes,
                governed_action_fact=governed_action_fact,
                known_payment_attempt_preflight_fact=known_attempt_fact,
            )

    runtime_record = observe_runtime(prepayment_result.decision)

    if callback_failure:
        failure_code = f"checkout_callback_exception:{callback_failure[0]}"
        runtime_record = replace(
            runtime_record,
            final_decision=Decision.INDETERMINATE,
            callback_result_ref=None,
            reason_codes=tuple(sorted(set((*runtime_record.reason_codes, failure_code)))),
        )
        return WebShopBuyNowGateOutcome(
            decision=Decision.INDETERMINATE,
            checkout_executed=False,
            callback_count=runtime_record.callback_count,
            callback_result_ref=None,
            bound_request=bound_request,
            prepayment_result=prepayment_result,
            runtime_gate_record=runtime_record,
            reason_codes=runtime_record.reason_codes,
            governed_action_fact=governed_action_fact,
            known_payment_attempt_preflight_fact=known_attempt_fact,
        )

    return WebShopBuyNowGateOutcome(
        decision=runtime_record.final_decision,
        checkout_executed=(
            runtime_record.final_decision is Decision.ALLOW
            and runtime_record.callback_executed
            and runtime_record.callback_count == 1
        ),
        callback_count=runtime_record.callback_count,
        callback_result_ref=runtime_record.callback_result_ref,
        bound_request=bound_request,
        prepayment_result=prepayment_result,
        runtime_gate_record=runtime_record,
        reason_codes=runtime_record.reason_codes,
        governed_action_fact=governed_action_fact,
        known_payment_attempt_preflight_fact=known_attempt_fact,
    )


def _missing_explicit_inputs(
    *,
    mandate: IntentMandate | None,
    execution_candidate: PaymentExecutionRecord | None,
    agent_identity: AgentIdentity | None,
    current_provider_ref: str | None,
    current_executor_instance_ref: str | None,
    context_policy_fact: ContextPolicyFact | None,
    checkout_callback: Callable[[], Any] | None,
) -> tuple[str, ...]:
    missing: list[str] = []
    if mandate is None:
        missing.append("intent_mandate_missing")
    if execution_candidate is None:
        missing.append("payment_execution_candidate_missing")
    if agent_identity is None:
        missing.append("agent_identity_missing")
    if not isinstance(current_provider_ref, str) or not current_provider_ref.strip():
        missing.append("current_provider_ref_missing")
    if (
        not isinstance(current_executor_instance_ref, str)
        or not current_executor_instance_ref.strip()
    ):
        missing.append("current_executor_instance_ref_missing")
    if context_policy_fact is None:
        missing.append("context_policy_fact_missing")
    if checkout_callback is None or not callable(checkout_callback):
        missing.append("checkout_callback_missing")
    return tuple(missing)


def _prepayment_reason_codes(result: ValidationResult) -> tuple[str, ...]:
    issue_codes = tuple(f"p1:{issue.code}" for issue in result.issues)
    return issue_codes or (f"p1:decision:{result.decision.value.lower()}",)


def _blocked(*reason_codes: str) -> WebShopBuyNowGateOutcome:
    return WebShopBuyNowGateOutcome(
        decision=Decision.INDETERMINATE,
        checkout_executed=False,
        callback_count=0,
        callback_result_ref=None,
        bound_request=None,
        prepayment_result=None,
        runtime_gate_record=None,
        reason_codes=tuple(reason_codes),
    )

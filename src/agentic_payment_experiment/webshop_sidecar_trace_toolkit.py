"""Controlled product-trace toolkit for the WebShop payment sidecar family.

The toolkit consumes only immutable facts already retained by the runtime gate
and already computed by the payment sidecar. It does not rerun authorization,
payment recovery, conflict resolution, lifecycle logic, or side effects.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .adapters.webshop import WebShopCommerceAdaptation
from .authoritative_trace import (
    ProductAuthoritativeTrace,
    TraceBindingAssertion,
    TraceContractError,
)
from .models import (
    Decision,
    FulfillmentRecord,
    IntentMandate,
    LifecycleResult,
    Order,
    PaymentExecutionRecord,
    PaymentRecoveryResult,
    PaymentStatus,
    TransactionRequest,
)
from .payment_status_conflict import PaymentStatusConflictFact
from .trusted_execution import (
    GovernedActionBindingFact,
    GovernedPaymentAction,
    RuntimeGateRecord,
    VerificationStatus,
)
from .webshop_payment_sidecar import WebShopPaymentFulfilmentOutcome
from .webshop_runtime_gate import WebShopBuyNowGateOutcome
from .webshop_sidecar_trace_profiles import (
    SIDECAR_TRACE_PROFILES,
    SidecarExtensionKind,
    SidecarTraceProfile,
)
from .webshop_trace_assembler import (
    assemble_product_trace,
    create_event,
    create_relation,
    create_source_binding,
    project_action_binding_fact,
    project_fulfillment,
    project_governed_action,
    project_mandate,
    project_order,
    project_payment,
    project_payment_recovery,
    project_payment_sidecar_outcome,
    project_payment_status_conflict,
    project_request,
    project_runtime_gate,
)


@dataclass(frozen=True)
class _SidecarTraceFacts:
    authorized_order: Order
    current_order: Order
    bound_request: TransactionRequest
    governed_action: GovernedPaymentAction
    candidate: PaymentExecutionRecord
    action_fact: GovernedActionBindingFact
    runtime_record: RuntimeGateRecord
    initial_payment: PaymentExecutionRecord
    effective_payment: PaymentExecutionRecord
    lifecycle: LifecycleResult


def _same_projection(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    return dict(left) == dict(right)


def _same_payment_identity(
    left: PaymentExecutionRecord,
    right: PaymentExecutionRecord,
) -> bool:
    left_projection = dict(project_payment(left))
    right_projection = dict(project_payment(right))
    left_projection.pop("status")
    right_projection.pop("status")
    return left_projection == right_projection


def _common_facts(
    *,
    gate_outcome: WebShopBuyNowGateOutcome,
    adaptation: WebShopCommerceAdaptation,
    mandate: IntentMandate,
    fulfillment: FulfillmentRecord | None,
    base_outcome: WebShopPaymentFulfilmentOutcome,
) -> _SidecarTraceFacts | None:
    if not adaptation.ready:
        return None
    if type(adaptation.order) is not Order:
        return None
    if type(adaptation.payment_request) is not TransactionRequest:
        return None
    if type(gate_outcome.authorized_order_snapshot) is not Order:
        return None
    if type(gate_outcome.bound_request) is not TransactionRequest:
        return None
    if type(gate_outcome.governed_action) is not GovernedPaymentAction:
        return None
    if type(gate_outcome.execution_candidate) is not PaymentExecutionRecord:
        return None
    if type(gate_outcome.governed_action_fact) is not GovernedActionBindingFact:
        return None
    if type(gate_outcome.runtime_gate_record) is not RuntimeGateRecord:
        return None
    if type(base_outcome.initial_payment) is not PaymentExecutionRecord:
        return None
    if type(base_outcome.effective_payment) is not PaymentExecutionRecord:
        return None
    if type(base_outcome.lifecycle) is not LifecycleResult:
        return None
    if fulfillment is not None and type(fulfillment) is not FulfillmentRecord:
        return None

    authorized_order = gate_outcome.authorized_order_snapshot
    current_order = adaptation.order
    bound_request = gate_outcome.bound_request
    governed_action = gate_outcome.governed_action
    candidate = gate_outcome.execution_candidate
    action_fact = gate_outcome.governed_action_fact
    runtime_record = gate_outcome.runtime_gate_record
    initial_payment = base_outcome.initial_payment
    effective_payment = base_outcome.effective_payment
    lifecycle = base_outcome.lifecycle

    if gate_outcome.decision is not Decision.ALLOW:
        return None
    if not gate_outcome.checkout_executed or gate_outcome.callback_count != 1:
        return None
    if runtime_record.final_decision is not Decision.ALLOW:
        return None
    if not runtime_record.callback_executed or runtime_record.callback_count != 1:
        return None
    if action_fact.status is not VerificationStatus.VALID:
        return None
    if gate_outcome.known_payment_attempt_preflight_fact is not None:
        return None
    if candidate.status is not PaymentStatus.PENDING:
        return None
    if not base_outcome.ready:
        return None
    if base_outcome.retry_allowed or base_outcome.duplicate_payment_blocked:
        return None

    if not _same_projection(project_order(authorized_order), project_order(current_order)):
        return None
    expected_adapter_request = dict(project_request(adaptation.payment_request))
    expected_adapter_request["agent_id"] = bound_request.agent_id
    if not _same_projection(project_request(bound_request), expected_adapter_request):
        return None

    if mandate.mandate_id != current_order.mandate_ref:
        return None
    if mandate.authority_version != current_order.authority_version_ref:
        return None
    if bound_request.order_ref != current_order.order_id:
        return None
    if bound_request.authority_ref != mandate.mandate_id:
        return None
    if bound_request.authority_version_ref != mandate.authority_version:
        return None
    if governed_action.authority_ref != mandate.mandate_id:
        return None
    if governed_action.authority_version != mandate.authority_version:
        return None
    if governed_action.order_ref != current_order.order_id:
        return None
    if governed_action.order_version != current_order.order_version:
        return None
    if governed_action.request_ref != bound_request.request_id:
        return None
    if governed_action.payment_ref != candidate.payment_id:
        return None
    if action_fact.action_id != governed_action.action_id:
        return None
    if action_fact.checked_order_ref != current_order.order_id:
        return None
    if action_fact.checked_request_ref != bound_request.request_id:
        return None
    if action_fact.checked_payment_ref != candidate.payment_id:
        return None

    if not _same_payment_identity(candidate, initial_payment):
        return None
    if not _same_payment_identity(initial_payment, effective_payment):
        return None
    if not (
        candidate.payment_id
        == initial_payment.payment_id
        == effective_payment.payment_id
    ):
        return None
    if effective_payment.request_id != bound_request.request_id:
        return None
    if effective_payment.order_id != current_order.order_id:
        return None
    if fulfillment is not None:
        if fulfillment.order_id != current_order.order_id:
            return None
        if fulfillment.status is not lifecycle.fulfillment_status:
            return None
        if fulfillment.status.value == "SUCCEEDED" and fulfillment.failure_code is not None:
            return None

    return _SidecarTraceFacts(
        authorized_order=authorized_order,
        current_order=current_order,
        bound_request=bound_request,
        governed_action=governed_action,
        candidate=candidate,
        action_fact=action_fact,
        runtime_record=runtime_record,
        initial_payment=initial_payment,
        effective_payment=effective_payment,
        lifecycle=lifecycle,
    )


def _profile_matches(
    profile: SidecarTraceProfile,
    *,
    fulfillment: FulfillmentRecord | None,
    base_outcome: WebShopPaymentFulfilmentOutcome,
) -> bool:
    initial_payment = base_outcome.initial_payment
    effective_payment = base_outcome.effective_payment
    lifecycle = base_outcome.lifecycle
    if not isinstance(initial_payment, PaymentExecutionRecord):
        return False
    if not isinstance(effective_payment, PaymentExecutionRecord):
        return False
    if not isinstance(lifecycle, LifecycleResult):
        return False
    if initial_payment.status is not profile.initial_payment_status:
        return False
    if effective_payment.status is not profile.effective_payment_status:
        return False
    if lifecycle.payment_status is not profile.lifecycle_payment_status:
        return False
    if lifecycle.fulfillment_status is not profile.lifecycle_fulfilment_status:
        return False
    if lifecycle.task_status is not profile.lifecycle_task_status:
        return False
    if lifecycle.remediation.status is not profile.remediation_status:
        return False
    if fulfillment is not None and fulfillment.status is not profile.lifecycle_fulfilment_status:
        return False

    recovery = base_outcome.query_recovery
    expects_recovery = profile.recovery_status is not None
    if expects_recovery != (recovery is not None):
        return False
    if recovery is not None:
        if type(recovery) is not PaymentRecoveryResult:
            return False
        if recovery.initial_status is not profile.recovery_initial_status:
            return False
        if recovery.observed_status is not profile.recovery_observed_status:
            return False
        if recovery.effective_status is not profile.recovery_effective_status:
            return False
        if recovery.recovery_status is not profile.recovery_status:
            return False
        if recovery.retry_allowed is not profile.recovery_retry_allowed:
            return False

    conflict = base_outcome.status_conflict
    expects_conflict = profile.conflict_resolution is not None
    if expects_conflict != (conflict is not None):
        return False
    if conflict is not None:
        if type(conflict) is not PaymentStatusConflictFact:
            return False
        if conflict.resolution is not profile.conflict_resolution:
            return False
        if conflict.initial_status is not profile.conflict_initial_status:
            return False
        if conflict.query_status is not profile.conflict_query_status:
            return False
        if conflict.async_status is not profile.conflict_async_status:
            return False
        if conflict.effective_status is not profile.conflict_effective_status:
            return False
        if conflict.effective_status_terminal is not profile.conflict_effective_status_terminal:
            return False
        if not set(profile.required_conflict_reason_codes).issubset(conflict.reason_codes):
            return False

    if profile.extension_kind is SidecarExtensionKind.FULFILMENT:
        if fulfillment is None:
            return False
        if initial_payment != effective_payment:
            return False
    return True


def _select_profile(
    *,
    fulfillment: FulfillmentRecord | None,
    base_outcome: WebShopPaymentFulfilmentOutcome,
    profiles: tuple[SidecarTraceProfile, ...] = SIDECAR_TRACE_PROFILES,
) -> SidecarTraceProfile | None:
    if type(profiles) is not tuple:
        return None
    if not all(type(profile) is SidecarTraceProfile for profile in profiles):
        return None
    matches = tuple(
        profile
        for profile in profiles
        if _profile_matches(
            profile,
            fulfillment=fulfillment,
            base_outcome=base_outcome,
        )
    )
    return matches[0] if len(matches) == 1 else None


def _extension_binding_and_event(
    *,
    profile: SidecarTraceProfile,
    current_order: Order,
    fulfillment: FulfillmentRecord | None,
    base_outcome: WebShopPaymentFulfilmentOutcome,
):
    order_ref = f"Order:{current_order.order_id}"
    if profile.extension_kind is SidecarExtensionKind.FULFILMENT:
        if type(fulfillment) is not FulfillmentRecord:
            return None
        binding = create_source_binding(
            "FulfillmentRecord",
            "fulfillment-record-trace/v2",
            project_fulfillment(fulfillment),
        )
        event = create_event(
            10,
            "FULFILMENT_OUTCOME_RECORDED",
            "FulfillmentRecord",
            "FULFILMENT_OUTCOME",
            binding,
            "FulfillmentRecord:{projection.fulfillment_id}",
            status=fulfillment.status.value,
            reason_codes=(
                () if fulfillment.failure_code is None else (fulfillment.failure_code,)
            ),
            relations=(
                create_relation(
                    "BOUND_TO",
                    "Order",
                    "CURRENT_ORDER_SNAPSHOT",
                    order_ref,
                ),
            ),
        )
        return binding, event

    if profile.extension_kind is SidecarExtensionKind.RECOVERY:
        recovery = base_outcome.query_recovery
        if type(recovery) is not PaymentRecoveryResult:
            return None
        binding = create_source_binding(
            "PaymentRecoveryResult",
            "payment-recovery-result-trace/v2",
            project_payment_recovery(recovery),
        )
        event = create_event(
            10,
            "RECOVERY_OUTCOME_RECORDED",
            "PaymentRecoveryResult",
            "RECOVERY_OUTCOME",
            binding,
            "PaymentRecoveryResult:binding:{binding_digest}",
            status=recovery.recovery_status.value,
            reason_codes=tuple(item.code for item in recovery.issues),
        )
        return binding, event

    if profile.extension_kind is SidecarExtensionKind.STATUS_CONFLICT:
        conflict = base_outcome.status_conflict
        if type(conflict) is not PaymentStatusConflictFact:
            return None
        binding = create_source_binding(
            "PaymentStatusConflictFact",
            "payment-status-conflict-fact-trace/v2",
            project_payment_status_conflict(conflict),
        )
        event = create_event(
            10,
            "STATUS_CONFLICT_RECORDED",
            "PaymentStatusConflictFact",
            "STATUS_CONFLICT_FACT",
            binding,
            "PaymentStatusConflictFact:binding:{binding_digest}",
            status=conflict.resolution.value,
            reason_codes=conflict.reason_codes,
        )
        return binding, event
    return None


def build_sidecar_product_trace(
    *,
    gate_outcome: WebShopBuyNowGateOutcome,
    adaptation: WebShopCommerceAdaptation,
    mandate: IntentMandate,
    fulfillment: FulfillmentRecord | None,
    base_outcome: WebShopPaymentFulfilmentOutcome,
) -> ProductAuthoritativeTrace | None:
    """Build the exactly-one matching Sidecar family trace or fail closed."""

    if type(gate_outcome) is not WebShopBuyNowGateOutcome:
        return None
    if type(adaptation) is not WebShopCommerceAdaptation:
        return None
    if type(mandate) is not IntentMandate:
        return None
    if type(base_outcome) is not WebShopPaymentFulfilmentOutcome:
        return None

    facts = _common_facts(
        gate_outcome=gate_outcome,
        adaptation=adaptation,
        mandate=mandate,
        fulfillment=fulfillment,
        base_outcome=base_outcome,
    )
    if facts is None:
        return None
    profile = _select_profile(
        fulfillment=fulfillment,
        base_outcome=base_outcome,
    )
    if profile is None:
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
            project_order(facts.current_order),
        )
        request_binding = create_source_binding(
            "TransactionRequest",
            "transaction-request-trace/v2",
            project_request(facts.bound_request),
        )
        action_binding = create_source_binding(
            "GovernedPaymentAction",
            "governed-payment-action-trace/v2",
            project_governed_action(facts.governed_action),
        )
        candidate_binding = create_source_binding(
            "PaymentExecutionRecord",
            "payment-execution-record-trace/v2",
            project_payment(facts.candidate),
        )
        action_fact_binding = create_source_binding(
            "GovernedActionBindingFact",
            "governed-action-binding-fact-trace/v2",
            project_action_binding_fact(facts.action_fact),
        )
        runtime_binding = create_source_binding(
            "RuntimeGateRecord",
            "runtime-gate-record-trace/v2",
            project_runtime_gate(facts.runtime_record),
        )
        payment_binding = create_source_binding(
            "PaymentExecutionRecord",
            "payment-execution-record-trace/v2",
            project_payment(facts.effective_payment),
        )
        extension = _extension_binding_and_event(
            profile=profile,
            current_order=facts.current_order,
            fulfillment=fulfillment,
            base_outcome=base_outcome,
        )
        if extension is None:
            return None
        extension_binding, extension_event = extension
        outcome_binding = create_source_binding(
            "WebShopPaymentFulfilmentOutcome",
            "webshop-payment-fulfilment-outcome-result-trace/v2",
            project_payment_sidecar_outcome(base_outcome),
        )

        if candidate_binding.binding_ref == payment_binding.binding_ref:
            return None
        if candidate_binding.source_object_ref != payment_binding.source_object_ref:
            return None

        authority_ref = f"IntentMandate:{mandate.mandate_id}"
        order_ref = f"Order:{facts.current_order.order_id}"
        request_ref = f"TransactionRequest:{facts.bound_request.request_id}"
        action_ref = f"GovernedPaymentAction:{facts.governed_action.action_id}"
        candidate_ref = f"PaymentExecutionRecord:{facts.candidate.payment_id}"

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
                status=facts.candidate.status.value,
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
                status=facts.action_fact.status.value,
                reason_codes=facts.action_fact.reason_codes,
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
                "RUNTIME_DECISION_RECORDED",
                "RuntimeGateRecord",
                "RUNTIME_GATE_OBSERVATION",
                runtime_binding,
                "RuntimeGateRecord:binding:{binding_digest}",
                decision=facts.runtime_record.final_decision.value,
                status=facts.runtime_record.binding_status,
                reason_codes=facts.runtime_record.reason_codes,
            ),
            create_event(
                9,
                "PAYMENT_OUTCOME_RECORDED",
                "PaymentExecutionRecord",
                "PAYMENT_EXECUTION_OUTCOME",
                payment_binding,
                "PaymentExecutionRecord:{projection.payment_id}",
                status=facts.effective_payment.status.value,
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
            extension_event,
            create_event(
                11,
                "RESULT_RECORDED",
                "WebShopPaymentFulfilmentOutcome",
                "FINAL_OUTCOME",
                outcome_binding,
                "WebShopPaymentFulfilmentOutcome:binding:{binding_digest}",
                status=facts.lifecycle.task_status.value,
                reason_codes=base_outcome.reason_codes,
            ),
        )
        source_bindings = (
            mandate_binding,
            order_binding,
            request_binding,
            action_binding,
            candidate_binding,
            action_fact_binding,
            runtime_binding,
            payment_binding,
            extension_binding,
            outcome_binding,
        )
        return assemble_product_trace(
            profile=profile.profile_name,
            trace_ref=(
                f"ProductAuthoritativeTrace:{profile.profile_name}:"
                f"{facts.bound_request.request_id}"
            ),
            events=events,
            source_bindings=source_bindings,
            expected_unique_binding_count=10,
        )
    except (AttributeError, KeyError, TypeError, ValueError, TraceContractError):
        return None


__all__ = ["build_sidecar_product_trace"]

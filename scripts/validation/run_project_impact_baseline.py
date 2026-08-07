"""Run the fixed offline project-impact baseline without changing product behavior."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import sys
from dataclasses import dataclass, replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_payment_experiment import (
    ActionReversibility,
    AgentIdentity,
    Decision,
    FulfillmentRecord,
    FulfillmentStatus,
    GovernedActionType,
    GovernedPaymentAction,
    IntentMandate,
    PaymentExecutionRecord,
    PaymentStatus,
    PaymentStatusObservation,
    SideEffectClass,
    assess_webshop_payment_fulfilment,
    gate_webshop_buy_now,
)
from agentic_payment_experiment.adapters.webshop import (
    WebShopCommerceAdaptation,
    adapt_webshop_purchase_candidate,
)
from agentic_payment_experiment.authoritative_trace import (
    TraceValidationStatus,
    validate_product_authoritative_trace,
)
from agentic_payment_experiment.attack_overlay import (
    AttackOverlay,
    evaluate_attack_overlay,
)
from agentic_payment_experiment.payment_execution import (
    PAYMENT_CONTEXT_ACTION,
    PAYMENT_REQUIRED_SOURCE_PATHS,
)
from agentic_payment_experiment.scenario_loader import load_scenario
from agentic_payment_experiment.trusted_execution import (
    POLICY_VERSION,
    ReplayEvent,
    ReplayEventType,
    ReplaySourceType,
    ReplayStatus,
    SourceType,
    VerificationStatus,
    create_confirmation_record,
    evaluate_context_policy,
    replay_events,
)

DEFAULT_SPEC = ROOT / "samples" / "evaluation" / "project_impact_baseline_v1.json"
WEBSHOP_FIXTURE = ROOT / "samples" / "external" / "webshop" / "pre_buy_now_candidate_v1.json"
ATTACK_SCENARIO = ROOT / "samples" / "scenarios" / "S01_normal.json"
EXPECTED_TASK_IDS = tuple(f"T{index:02d}" for index in range(1, 13))
REQUIRED_TASK_FIELDS = frozenset(
    {
        "task_id",
        "title",
        "scenario",
        "initial_environment_state",
        "user_goal",
        "intent_mandate",
        "authorized_order_or_snapshot",
        "action_sequence",
        "injected_untrusted_inputs",
        "payment_observations",
        "fulfilment_observations",
        "expected_decision",
        "expected_callback_count",
        "expected_retry_count",
        "expected_final_environment_state",
        "expected_reason_codes",
        "expected_binding_status",
        "expected_lineage_status",
        "expected_effective_source_types",
        "expected_product_observed_trace_status",
        "expected_product_observed_trace_events",
        "expected_evaluator_synthesized_replay_status",
        "expected_evaluator_synthesized_replay_events",
        "expected_required_facts",
        "expected_required_evidence_stages",
        "side_effect_guardrail",
        "binding_valid_required",
        "lineage_required",
        "untrusted_write_attempt",
        "limitations",
    }
)


@dataclass(frozen=True)
class GateContext:
    adaptation: WebShopCommerceAdaptation
    authorized_adaptation: WebShopCommerceAdaptation
    mandate: IntentMandate
    bound_request: Any
    execution: PaymentExecutionRecord
    identity: AgentIdentity
    context_fact: Any
    confirmation: Any
    action: GovernedPaymentAction


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _stable_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: object) -> str:
    return _sha256_bytes(_stable_json(value).encode("utf-8"))


def _rate(count: int, denominator: int) -> dict[str, object]:
    return {
        "count": count,
        "denominator": denominator,
        "rate": (
            f"{Decimal(count) / Decimal(denominator):.6f}"
            if denominator
            else "0.000000"
        ),
    }


def load_spec(path: Path = DEFAULT_SPEC) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "agentic-payment-project-impact-baseline/v1":
        raise ValueError("unsupported project-impact baseline schema")
    if data.get("version") != "1.1.0":
        raise ValueError("unsupported project-impact baseline version")
    if tuple(data.get("task_order", ())) != EXPECTED_TASK_IDS:
        raise ValueError("task_order must be the frozen T01-T12 sequence")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 12:
        raise ValueError("project-impact baseline requires exactly 12 tasks")
    task_ids = tuple(task.get("task_id") for task in tasks if isinstance(task, dict))
    if task_ids != EXPECTED_TASK_IDS or len(set(task_ids)) != len(task_ids):
        raise ValueError("task IDs must be unique and ordered T01-T12")
    decisions: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("every task must be a JSON object")
        missing = REQUIRED_TASK_FIELDS - set(task)
        if missing:
            raise ValueError(
                f"{task.get('task_id', '<unknown>')} missing fields: {sorted(missing)}"
            )
        decision = task["expected_decision"]
        if decision not in {item.value for item in Decision}:
            raise ValueError(f"{task['task_id']} has an unknown expected decision")
        decisions.add(decision)
        for field in (
            "action_sequence",
            "injected_untrusted_inputs",
            "payment_observations",
            "fulfilment_observations",
            "expected_reason_codes",
            "expected_effective_source_types",
            "expected_product_observed_trace_events",
            "expected_evaluator_synthesized_replay_events",
            "expected_required_facts",
            "expected_required_evidence_stages",
            "limitations",
        ):
            if not isinstance(task[field], list):
                raise ValueError(f"{task['task_id']} field {field} must be a list")
        if not isinstance(task["expected_final_environment_state"], dict):
            raise ValueError(
                f"{task['task_id']} expected_final_environment_state must be an object"
            )
        guardrail = task["side_effect_guardrail"]
        if not isinstance(guardrail, dict):
            raise ValueError(f"{task['task_id']} side_effect_guardrail must be an object")
        for field in ("max_callback_count", "max_retry_count"):
            value = guardrail.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{task['task_id']} {field} must be a non-negative integer")
        for field in ("callback_gap_code", "retry_gap_code"):
            value = guardrail.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{task['task_id']} {field} must be a non-empty string")
    if decisions != {item.value for item in Decision}:
        raise ValueError("the frozen fixture must cover all four Decision values")
    limitations = data.get("limitations")
    if not isinstance(limitations, dict) or not all(
        value is True for value in limitations.values()
    ):
        raise ValueError("top-level limitations must be explicit true flags")
    return data


def _load_base_adaptation() -> WebShopCommerceAdaptation:
    snapshot = json.loads(WEBSHOP_FIXTURE.read_text(encoding="utf-8"))
    adaptation = adapt_webshop_purchase_candidate(snapshot)
    if not adaptation.ready or adaptation.order is None or adaptation.payment_request is None:
        raise ValueError("fixed WebShop commerce fixture is not adaptation-ready")
    return adaptation


def _context_fact(
    mandate: IntentMandate,
    adaptation: WebShopCommerceAdaptation,
    bound_request: Any,
):
    assert adaptation.order is not None
    state = {
        "mandate": {"mandate_id": mandate.mandate_id},
        "final_order": {"order_id": adaptation.order.order_id},
        "request": {
            "request_id": bound_request.request_id,
            "agent_id": bound_request.agent_id,
            "amount": bound_request.amount,
            "payee": bound_request.payee,
            "currency": bound_request.currency,
        },
    }
    trusted_sources = {
        "mandate.mandate_id": SourceType.USER_CONFIRMED,
        "final_order.order_id": SourceType.USER_CONFIRMED,
        "request.request_id": SourceType.PROTOCOL_VERIFIED,
        "request.agent_id": SourceType.USER_CONFIRMED,
        "request.amount": SourceType.USER_CONFIRMED,
        "request.payee": SourceType.USER_CONFIRMED,
        "request.currency": SourceType.USER_CONFIRMED,
    }
    return evaluate_context_policy(
        state,
        trusted_sources=trusted_sources,
        required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
        current_action=PAYMENT_CONTEXT_ACTION,
        policy_version=POLICY_VERSION,
    ).fact


def _gate_context(
    *,
    adaptation: WebShopCommerceAdaptation | None = None,
    authorized_adaptation: WebShopCommerceAdaptation | None = None,
) -> GateContext:
    current = adaptation or _load_base_adaptation()
    authorized = authorized_adaptation or current
    if current.order is None or current.payment_request is None:
        raise ValueError("current adaptation is incomplete")
    if authorized.order is None or authorized.payment_request is None:
        raise ValueError("authorized adaptation is incomplete")

    agent_id = "webshop-agent-1"
    bound_request = replace(current.payment_request, agent_id=agent_id)
    mandate = IntentMandate(
        mandate_id=current.order.mandate_ref,
        user_id="webshop-user-1",
        max_amount=Decimal("5000.00"),
        allowed_merchants=frozenset({current.order.merchant}),
        allowed_categories=frozenset({bound_request.category}),
        expires_at=bound_request.occurred_at + timedelta(hours=2),
        max_count=1,
        expected_agent_id=agent_id,
        currency=bound_request.currency,
        authority_version=current.order.authority_version_ref or "",
    )
    confirmation = create_confirmation_record(
        confirmation_id="project-baseline-confirmation-1",
        authority_id=mandate.mandate_id,
        authority_version=mandate.authority_version,
        order=authorized.order,
        confirmed_at=bound_request.occurred_at - timedelta(minutes=1),
        expires_at=bound_request.occurred_at + timedelta(minutes=30),
    )
    execution = PaymentExecutionRecord(
        payment_id="project-baseline-payment-1",
        request_id=bound_request.request_id,
        order_id=current.order.order_id,
        status=PaymentStatus.PENDING,
        amount=bound_request.amount,
        currency=bound_request.currency,
        occurred_at=bound_request.occurred_at + timedelta(seconds=1),
        provider_ref="offline-webshop-payment-provider",
        idempotency_key="project-baseline-idempotency-1",
        authority_ref=mandate.mandate_id,
        agent_ref=agent_id,
        transaction_object_ref=bound_request.request_id,
        payee=current.order.payee,
    )
    identity = AgentIdentity(
        agent_id=agent_id,
        provider="offline-webshop-provider",
        executor_instance_id="offline-webshop-executor",
        status="active",
    )
    context_fact = _context_fact(mandate, current, bound_request)
    action = GovernedPaymentAction(
        action_id="project-baseline-action-1",
        action_type=GovernedActionType.EXECUTE_PAYMENT,
        subject_ref=mandate.user_id,
        agent_ref=agent_id,
        executor_ref="offline-webshop-executor",
        authority_ref=mandate.mandate_id,
        authority_version=mandate.authority_version,
        order_ref=current.order.order_id,
        order_version=current.order.order_version,
        request_ref=bound_request.request_id,
        payment_ref=execution.payment_id,
        source_refs=(
            "source:fixed-commerce-snapshot",
            "source:fixed-user-confirmation",
        ),
        side_effect_class=SideEffectClass.PAYMENT_EXECUTION,
        reversibility=ActionReversibility.COMPENSATABLE_NOT_REVERSIBLE,
        occurred_at=bound_request.occurred_at + timedelta(milliseconds=500),
    )
    return GateContext(
        adaptation=current,
        authorized_adaptation=authorized,
        mandate=mandate,
        bound_request=bound_request,
        execution=execution,
        identity=identity,
        context_fact=context_fact,
        confirmation=confirmation,
        action=action,
    )


def _invoke_gate(
    context: GateContext,
    *,
    action: GovernedPaymentAction | None = None,
    known_payment_attempts: tuple[PaymentExecutionRecord, ...] = (),
) -> tuple[Any, tuple[str, ...]]:
    callbacks: list[str] = []

    def callback() -> str:
        callbacks.append("checkout")
        return "project-baseline-injected-checkout"

    kwargs: dict[str, object] = {
        "adaptation": context.adaptation,
        "mandate": context.mandate,
        "declared_agent_id": context.bound_request.agent_id,
        "execution_candidate": context.execution,
        "agent_identity": context.identity,
        "current_provider_ref": context.identity.provider,
        "current_executor_instance_ref": context.identity.executor_instance_id,
        "context_policy_fact": context.context_fact,
        "checkout_callback": callback,
        "confirmation_record": context.confirmation,
        "seen_request_ids": (),
        "authorized_adaptation": context.authorized_adaptation,
        "governed_action": context.action if action is None else action,
    }
    # The target runner is frozen before the product capability exists. Passing
    # the typed attempt inventory only when the public gate exposes the frozen
    # keyword keeps BEFORE and AFTER on the exact same evaluator implementation.
    if "known_payment_attempts" in inspect.signature(gate_webshop_buy_now).parameters:
        kwargs["known_payment_attempts"] = known_payment_attempts
    outcome = gate_webshop_buy_now(**kwargs)
    return outcome, tuple(callbacks)


def _mutated_adaptation(kind: str) -> tuple[WebShopCommerceAdaptation, WebShopCommerceAdaptation]:
    authorized = _load_base_adaptation()
    assert authorized.order is not None and authorized.payment_request is not None
    if kind == "price_up":
        amount = authorized.order.total_amount + Decimal("10.00")
        item = replace(
            authorized.order.items[0],
            unit_amount=authorized.order.items[0].unit_amount + Decimal("10.00"),
        )
        order = replace(
            authorized.order,
            order_version="project-baseline-price-up-v2",
            items=(item,),
            total_amount=amount,
        )
        request = replace(authorized.payment_request, amount=amount)
    elif kind == "price_down":
        amount = authorized.order.total_amount - Decimal("10.00")
        item = replace(
            authorized.order.items[0],
            unit_amount=authorized.order.items[0].unit_amount - Decimal("10.00"),
        )
        order = replace(
            authorized.order,
            order_version="project-baseline-price-down-v2",
            items=(item,),
            total_amount=amount,
        )
        request = replace(authorized.payment_request, amount=amount)
    elif kind == "payee":
        payee = "project-baseline-payee-other"
        order = replace(
            authorized.order,
            order_version="project-baseline-payee-v2",
            payee=payee,
        )
        request = replace(authorized.payment_request, payee=payee)
    else:
        raise ValueError(f"unknown adaptation mutation: {kind}")
    return replace(authorized, order=order, payment_request=request), authorized


def _sidecar_payment(context: GateContext, status: PaymentStatus) -> PaymentExecutionRecord:
    return replace(
        context.execution,
        status=status,
        receipt_ref="project-baseline-receipt-1",
        provider_ref="offline-webshop-payment-provider",
        idempotency_key="project-baseline-idempotency-1",
    )


def _fulfilment(
    context: GateContext,
    status: FulfillmentStatus,
    *,
    failure_code: str | None = None,
) -> FulfillmentRecord:
    assert context.adaptation.order is not None
    return FulfillmentRecord(
        fulfillment_id="project-baseline-fulfilment-1",
        order_id=context.adaptation.order.order_id,
        status=status,
        occurred_at=context.execution.occurred_at + timedelta(minutes=3),
        evidence_ref="project-baseline-fulfilment-evidence-1",
        failure_code=failure_code,
    )


def _observation(
    payment: PaymentExecutionRecord,
    status: PaymentStatus,
    *,
    minutes: int,
    source: str,
) -> PaymentStatusObservation:
    return PaymentStatusObservation(
        payment_id=payment.payment_id,
        order_id=payment.order_id,
        status=status,
        observed_at=payment.occurred_at + timedelta(minutes=minutes),
        source=source,
        provider_ref=payment.provider_ref,
    )


def _binding_status(gate: Any) -> str:
    action_fact = gate.governed_action_fact
    if action_fact is not None and action_fact.status is not VerificationStatus.VALID:
        return action_fact.status.value
    runtime = gate.runtime_gate_record
    if runtime is None:
        return "NOT_EVALUATED"
    if (
        action_fact is not None
        and action_fact.status is VerificationStatus.VALID
        and runtime.binding_status == "VALID"
        and runtime.identity_status == "VALID"
        and runtime.context_policy_status == "VALID"
    ):
        return "VALID"
    if "INVALID" in {
        runtime.binding_status,
        runtime.identity_status,
        runtime.context_policy_status,
    }:
        return "INVALID"
    return "MISSING_EVIDENCE"


def _product_observed_trace(
    *named_outputs: tuple[str, object],
) -> tuple[str, list[str], tuple[str, ...], str | None]:
    """Read only outcome.authoritative_trace from a product result.

    Legacy authoritative_trace_events and evaluator-created ReplayEvent values
    are diagnostics only and can never count as product-observed trace.
    """

    for source_name, output in named_outputs:
        trace = getattr(output, "authoritative_trace", None)
        if trace is None:
            continue
        validation = validate_product_authoritative_trace(trace)
        return (
            validation.status.value,
            list(validation.event_types),
            validation.reason_codes,
            source_name,
        )
    return (
        "NOT_AVAILABLE",
        [],
        ("product_authoritative_trace_not_available",),
        None,
    )


def _synthesize_replay(
    context: GateContext,
    gate: Any,
    payment: PaymentExecutionRecord,
    reason_codes: tuple[str, ...],
) -> tuple[str, list[str], tuple[str, ...]]:
    """Build evaluator-only Replay fixtures without claiming product provenance."""

    if gate.runtime_gate_record is None:
        return "NOT_AVAILABLE", [], ("evaluator_synthesized_replay_not_available",)
    assert context.adaptation.order is not None
    common = {
        "subject_ref": context.mandate.user_id,
        "agent_ref": context.bound_request.agent_id,
        "authority_ref": context.mandate.mandate_id,
        "transaction_object_ref": context.bound_request.request_id,
        "payment_ref": payment.payment_id,
        "decision": gate.decision,
    }
    times = (
        context.bound_request.occurred_at - timedelta(minutes=3),
        context.bound_request.occurred_at - timedelta(minutes=2),
        context.bound_request.occurred_at - timedelta(minutes=1),
        context.execution.occurred_at,
        payment.occurred_at + timedelta(seconds=1),
    )
    event_specs = (
        (
            ReplayEventType.AUTHORITY_RECORDED,
            ReplaySourceType.USER_CONFIRMED,
            "source:fixed-user-confirmation",
            ("authority_recorded",),
        ),
        (
            ReplayEventType.ORDER_RECORDED,
            ReplaySourceType.PROTOCOL_VERIFIED,
            "source:fixed-commerce-snapshot",
            ("order_recorded",),
        ),
        (
            ReplayEventType.REQUEST_RECORDED,
            ReplaySourceType.PROTOCOL_VERIFIED,
            "source:fixed-payment-request",
            ("request_recorded",),
        ),
        (
            ReplayEventType.RUNTIME_DECISION_RECORDED,
            ReplaySourceType.SYSTEM_RUNTIME,
            "source:runtime-gate-record",
            gate.reason_codes or ("runtime_gate_recorded",),
        ),
        (
            ReplayEventType.PAYMENT_OUTCOME_RECORDED,
            ReplaySourceType.PAYMENT_PROVIDER_OBSERVED,
            "source:fixed-payment-observation",
            reason_codes or ("payment_outcome_recorded",),
        ),
    )
    events: list[ReplayEvent] = []
    for index, (event_type, source_type, source_ref, event_reasons) in enumerate(
        event_specs
    ):
        events.append(
            ReplayEvent(
                event_id=f"project-baseline-event-{index + 1}",
                event_type=event_type,
                occurred_at=times[index],
                source_type=source_type,
                source_ref=source_ref,
                reason_codes=tuple(event_reasons),
                previous_event_ref=(events[-1].event_id if events else None),
                runtime_gate=(
                    gate.runtime_gate_record
                    if event_type is ReplayEventType.RUNTIME_DECISION_RECORDED
                    else None
                ),
                **common,
            )
        )
    replay = replay_events(tuple(events))
    return replay.status.value, [event.event_type.value for event in events], replay.reason_codes

def _empty_state() -> dict[str, object]:
    return {
        "payment_status": None,
        "fulfilment_status": None,
        "task_status": None,
        "remediation_status": None,
        "recovery_status": None,
        "conflict_resolution": None,
        "retry_allowed": False,
        "duplicate_payment_blocked": False,
        "trusted_state_changed": False,
        "blocked_paths": [],
    }


def _gate_actual(
    task_id: str,
    context: GateContext,
    gate: Any,
    callbacks: tuple[str, ...],
    *,
    facts: set[str],
    synthesized_replay: tuple[str, list[str], tuple[str, ...]] | None = None,
) -> dict[str, object]:
    stages = {"commerce_adaptation", "mandate", "order", "request"}
    preflight_fact = getattr(gate, "known_payment_attempt_preflight_fact", None)
    preflight_status = getattr(
        getattr(preflight_fact, "status", None),
        "value",
        "NOT_AVAILABLE",
    )
    if preflight_fact is not None:
        stages.add("known_payment_attempt_preflight")
    if gate.prepayment_result is not None:
        stages.add("prepayment_decision")
    if gate.governed_action_fact is not None:
        stages.add("governed_action")
    if gate.runtime_gate_record is not None:
        stages.update(
            {
                "runtime_gate",
                "payment_execution_binding",
                "executor_identity_binding",
                "source_coverage",
            }
        )
    product_trace = _product_observed_trace(("webshop_gate_outcome", gate))
    synth_status, synth_events, synth_reasons = synthesized_replay or (
        "NOT_AVAILABLE",
        [],
        ("evaluator_synthesized_replay_not_available",),
    )
    if product_trace[0] == TraceValidationStatus.VALID.value:
        stages.add("authoritative_trace")
    if synth_status == ReplayStatus.VALID.value:
        stages.add("evaluator_synthesized_replay")
    return {
        "task_id": task_id,
        "actual_decision": gate.decision.value,
        "actual_callback_count": gate.callback_count,
        "actual_callback_observations": len(callbacks),
        "actual_retry_count": 0,
        "actual_final_environment_state": _empty_state(),
        "actual_reason_codes": sorted(set(gate.reason_codes)),
        "known_payment_attempt_preflight_status": preflight_status,
        "known_payment_attempt_preflight_reason_codes": list(
            getattr(preflight_fact, "reason_codes", ())
        ),
        "known_payment_attempt_preflight_blocking_request_refs": list(
            getattr(preflight_fact, "blocking_request_refs", ())
        ),
        "binding_status": _binding_status(gate),
        "lineage_status": "NOT_APPLICABLE",
        "effective_source_types": [],
        "product_observed_trace_status": product_trace[0],
        "product_observed_trace_events": product_trace[1],
        "product_observed_trace_reason_codes": list(product_trace[2]),
        "product_observed_trace_source": product_trace[3],
        "evaluator_synthesized_replay_status": synth_status,
        "evaluator_synthesized_replay_events": synth_events,
        "evaluator_synthesized_replay_reason_codes": list(synth_reasons),
        "evaluator_synthesized_replay_provenance": (
            "runner_constructed_from_fixed_facts"
            if synth_status != "NOT_AVAILABLE"
            else None
        ),
        "required_facts_observed": sorted(facts),
        "evidence_stages": sorted(stages),
        "forbidden_side_effects": [],
        "limitations": list(gate.limitations),
    }

def _with_sidecar(
    actual: dict[str, object],
    context: GateContext,
    gate: Any,
    payment: PaymentExecutionRecord,
    fulfilment: FulfillmentRecord,
    *,
    query: PaymentStatusObservation | None = None,
    async_observation: PaymentStatusObservation | None = None,
    known_attempts: tuple[PaymentExecutionRecord, ...] = (),
) -> dict[str, object]:
    sidecar = assess_webshop_payment_fulfilment(
        gate_outcome=gate,
        adaptation=context.adaptation,
        mandate=context.mandate,
        payment=payment,
        fulfillment=fulfilment,
        query_observation=query,
        async_observation=async_observation,
        known_attempts=known_attempts,
    )
    product_trace = _product_observed_trace(
        ("webshop_gate_outcome", gate),
        ("webshop_payment_fulfilment_outcome", sidecar),
    )
    preflight_fact = getattr(gate, "known_payment_attempt_preflight_fact", None)
    preflight_blocked = (
        getattr(getattr(preflight_fact, "status", None), "value", None)
        == "BLOCKED"
    )
    state = _empty_state()
    state.update(
        {
            "payment_status": (
                sidecar.effective_payment.status.value
                if sidecar.effective_payment is not None
                else None
            ),
            "fulfilment_status": (
                sidecar.lifecycle.fulfillment_status.value
                if sidecar.lifecycle is not None
                else None
            ),
            "task_status": (
                sidecar.lifecycle.task_status.value
                if sidecar.lifecycle is not None
                else None
            ),
            "remediation_status": (
                sidecar.lifecycle.remediation.status.value
                if sidecar.lifecycle is not None
                else None
            ),
            "recovery_status": (
                sidecar.query_recovery.recovery_status.value
                if sidecar.query_recovery is not None
                else None
            ),
            "conflict_resolution": (
                sidecar.status_conflict.resolution.value
                if sidecar.status_conflict is not None
                else None
            ),
            "retry_allowed": sidecar.retry_allowed,
            "duplicate_payment_blocked": (
                sidecar.duplicate_payment_blocked or preflight_blocked
            ),
        }
    )
    stages = set(actual["evidence_stages"])
    stages.update({"payment", "fulfilment"})
    if sidecar.lifecycle is not None:
        stages.add("lifecycle")
    if sidecar.query_recovery is not None:
        stages.add("payment_recovery")
    if sidecar.status_conflict is not None:
        stages.add("status_conflict")
    if sidecar.duplicate_payment_blocked or preflight_blocked:
        stages.add("duplicate_protection")
    if product_trace[0] == TraceValidationStatus.VALID.value:
        stages.add("authoritative_trace")
    actual.update(
        {
            "actual_final_environment_state": state,
            "product_observed_trace_status": product_trace[0],
            "product_observed_trace_events": product_trace[1],
            "product_observed_trace_reason_codes": list(product_trace[2]),
            "product_observed_trace_source": product_trace[3],
            "actual_reason_codes": sorted(
                set(actual["actual_reason_codes"]) | set(sidecar.reason_codes)
            ),
            "evidence_stages": sorted(stages),
            "limitations": sorted(
                set(actual["limitations"]) | set(sidecar.limitations)
            ),
        }
    )
    return actual


def _run_gate_task(task_id: str) -> dict[str, object]:
    if task_id == "T02":
        current, authorized = _mutated_adaptation("price_up")
        context = _gate_context(adaptation=current, authorized_adaptation=authorized)
        gate, callbacks = _invoke_gate(context)
        return _gate_actual(
            task_id,
            context,
            gate,
            callbacks,
            facts={"authorized_order_snapshot", "current_order_snapshot", "order_difference"},
        )
    if task_id == "T03":
        current, authorized = _mutated_adaptation("price_down")
        context = _gate_context(adaptation=current, authorized_adaptation=authorized)
        gate, callbacks = _invoke_gate(context)
        return _gate_actual(
            task_id,
            context,
            gate,
            callbacks,
            facts={"authorized_order_snapshot", "current_order_snapshot", "order_difference"},
        )
    if task_id == "T04":
        current, authorized = _mutated_adaptation("payee")
        context = _gate_context(adaptation=current, authorized_adaptation=authorized)
        gate, callbacks = _invoke_gate(context)
        return _gate_actual(
            task_id,
            context,
            gate,
            callbacks,
            facts={"authorized_order_snapshot", "current_order_snapshot", "payee_difference"},
        )

    context = _gate_context()
    action = context.action
    if task_id == "T05":
        action = replace(action, agent_ref="agent-evil")
    elif task_id == "T06":
        action = replace(action, action_id="")

    existing_success: PaymentExecutionRecord | None = None
    known_payment_attempts: tuple[PaymentExecutionRecord, ...] = ()
    if task_id == "T10":
        existing_success = replace(
            _sidecar_payment(context, PaymentStatus.UNKNOWN),
            payment_id="project-baseline-payment-existing-success",
            status=PaymentStatus.SUCCEEDED,
            provider_ref="offline-existing-payment-provider",
        )
        known_payment_attempts = (existing_success,)

    gate, callbacks = _invoke_gate(
        context,
        action=action,
        known_payment_attempts=known_payment_attempts,
    )
    if task_id in {"T05", "T06"}:
        facts = {"governed_action_binding"}
        if task_id == "T05":
            facts.add("agent_identity_binding")
        return _gate_actual(task_id, context, gate, callbacks, facts=facts)

    if task_id not in {"T01", "T09", "T10", "T11", "T12"}:
        raise ValueError(f"unknown gate task: {task_id}")

    if task_id == "T01":
        payment = _sidecar_payment(context, PaymentStatus.SUCCEEDED)
        fulfilment = _fulfilment(context, FulfillmentStatus.SUCCEEDED)
        synthesized_replay = _synthesize_replay(
            context,
            gate,
            payment,
            gate.reason_codes,
        )
        actual = _gate_actual(
            task_id,
            context,
            gate,
            callbacks,
            facts={
                "governed_action_binding",
                "payment_execution_binding",
                "executor_identity_binding",
                "source_coverage",
            },
            synthesized_replay=synthesized_replay,
        )
        return _with_sidecar(actual, context, gate, payment, fulfilment)

    payment = _sidecar_payment(context, PaymentStatus.UNKNOWN)
    if task_id == "T09":
        fulfilment = _fulfilment(context, FulfillmentStatus.SUCCEEDED)
        query = _observation(payment, PaymentStatus.SUCCEEDED, minutes=1, source="query")
        actual = _gate_actual(
            task_id,
            context,
            gate,
            callbacks,
            facts={
                "governed_action_binding",
                "original_transaction_binding",
                "query_recovery",
            },
        )
        actual = _with_sidecar(
            actual,
            context,
            gate,
            payment,
            fulfilment,
            query=query,
        )
    elif task_id == "T10":
        fulfilment = _fulfilment(context, FulfillmentStatus.PENDING)
        assert existing_success is not None
        actual = _gate_actual(
            task_id,
            context,
            gate,
            callbacks,
            facts={
                "governed_action_binding",
                "idempotency_boundary",
                "duplicate_attempt_inventory",
                "known_payment_attempt_preflight",
            },
        )
        actual = _with_sidecar(
            actual,
            context,
            gate,
            payment,
            fulfilment,
            known_attempts=(existing_success,),
        )
    elif task_id == "T11":
        payment = replace(payment, status=PaymentStatus.SUCCEEDED)
        fulfilment = _fulfilment(
            context,
            FulfillmentStatus.FAILED,
            failure_code="merchant_did_not_fulfil",
        )
        actual = _gate_actual(
            task_id,
            context,
            gate,
            callbacks,
            facts={
                "governed_action_binding",
                "payment_execution_binding",
                "fulfilment_binding",
                "remediation_state",
            },
        )
        actual = _with_sidecar(actual, context, gate, payment, fulfilment)
    else:
        fulfilment = _fulfilment(context, FulfillmentStatus.SUCCEEDED)
        query = _observation(payment, PaymentStatus.SUCCEEDED, minutes=1, source="query")
        async_observation = _observation(
            payment,
            PaymentStatus.FAILED,
            minutes=2,
            source="async",
        )
        actual = _gate_actual(
            task_id,
            context,
            gate,
            callbacks,
            facts={
                "governed_action_binding",
                "query_binding",
                "async_binding",
                "status_conflict_fact",
            },
        )
        actual = _with_sidecar(
            actual,
            context,
            gate,
            payment,
            fulfilment,
            query=query,
            async_observation=async_observation,
        )

    synthesized_replay = _synthesize_replay(
        context,
        gate,
        payment,
        tuple(actual["actual_reason_codes"]),
    )
    actual["evaluator_synthesized_replay_status"] = synthesized_replay[0]
    actual["evaluator_synthesized_replay_events"] = synthesized_replay[1]
    actual["evaluator_synthesized_replay_reason_codes"] = list(
        synthesized_replay[2]
    )
    actual["evaluator_synthesized_replay_provenance"] = (
        "runner_constructed_from_fixed_facts"
        if synthesized_replay[0] != "NOT_AVAILABLE"
        else None
    )
    if synthesized_replay[0] == ReplayStatus.VALID.value:
        actual["evidence_stages"] = sorted(
            set(actual["evidence_stages"]) | {"evaluator_synthesized_replay"}
        )
    return actual


def _run_overlay_task(task_id: str) -> dict[str, object]:
    scenario = load_scenario(ATTACK_SCENARIO)
    if task_id == "T07":
        overlay = AttackOverlay(
            attack_id="PROJECT-BASELINE-T07",
            title="不可信网页金额覆盖",
            source="fixed_offline_page",
            untrusted_content="固定离线输入，不调用浏览器或 LLM。",
            proposed_overrides={"request.amount": "699.00"},
            source_type=SourceType.WEB_UNTRUSTED,
            source_ref="project-baseline-web-t07",
        )
    elif task_id == "T08":
        overlay = AttackOverlay(
            attack_id="PROJECT-BASELINE-T08",
            title="不可信 payee 覆盖",
            source="fixed_offline_llm_output",
            untrusted_content="固定离线输入，不调用浏览器或 LLM。",
            proposed_overrides={"request.payee": "payee-evil"},
            source_type=SourceType.LLM_GENERATED,
            source_ref="project-baseline-llm-t08",
        )
    else:
        raise ValueError(f"unknown overlay task: {task_id}")
    result = evaluate_attack_overlay(scenario, overlay)
    sources = sorted(
        {
            source.value
            for fact in result.lineage_facts
            for source in fact.effective_source_types
        }
    )
    stages = {"context_policy", "lineage"}
    if result.blocked_override_paths:
        stages.add("blocked_write")
    state = _empty_state()
    state.update(
        {
            "trusted_state_changed": result.trusted_state_changed,
            "blocked_paths": list(result.blocked_override_paths),
        }
    )
    product_trace = _product_observed_trace(("attack_overlay_result", result))
    if product_trace[0] == TraceValidationStatus.VALID.value:
        stages.add("authoritative_trace")
    return {
        "task_id": task_id,
        "actual_decision": result.defended_decision.value,
        "actual_callback_count": 0,
        "actual_callback_observations": 0,
        "actual_retry_count": 0,
        "actual_final_environment_state": state,
        "actual_reason_codes": sorted(
            set(result.reason_codes) | set(result.lineage_reason_codes)
        ),
        "binding_status": "NOT_APPLICABLE",
        "lineage_status": result.lineage_status.value,
        "effective_source_types": sources,
        "product_observed_trace_status": product_trace[0],
        "product_observed_trace_events": product_trace[1],
        "product_observed_trace_reason_codes": list(product_trace[2]),
        "product_observed_trace_source": product_trace[3],
        "evaluator_synthesized_replay_status": "NOT_AVAILABLE",
        "evaluator_synthesized_replay_events": [],
        "evaluator_synthesized_replay_reason_codes": [
            "evaluator_synthesized_replay_not_available"
        ],
        "evaluator_synthesized_replay_provenance": None,
        "required_facts_observed": ["context_policy_fact", "fact_lineage"],
        "evidence_stages": sorted(stages),
        "forbidden_side_effects": (
            ["trusted_field_override_applied"]
            if result.trusted_state_changed
            else []
        ),
        "limitations": [
            "offline_overlay_only",
            "no_browser_or_llm_execution",
        ],
    }


def _actual_for(task_id: str) -> dict[str, object]:
    if task_id in {"T07", "T08"}:
        return _run_overlay_task(task_id)
    return _run_gate_task(task_id)


def _subset_matches(expected: Mapping[str, object], actual: Mapping[str, object]) -> bool:
    return all(actual.get(key) == value for key, value in expected.items())


def _trace_provenance_separated(
    *,
    product_status: object,
    product_source: object,
    replay_status: object,
    replay_provenance: object,
    evidence_stages: set[str],
) -> bool:
    """Validate the closed provenance combinations used by this measurement.

    Product traces and evaluator replay may coexist, but each present source
    must be explicit, internally consistent with its status/stage, and distinct.
    """

    product_present = product_status == "VALID"
    product_absent = product_status == "NOT_AVAILABLE"
    replay_present = replay_status == "VALID"
    replay_absent = replay_status == "NOT_AVAILABLE"
    if not (product_present or product_absent):
        return False
    if not (replay_present or replay_absent):
        return False

    product_source_present = (
        isinstance(product_source, str) and bool(product_source.strip())
    )
    replay_source_present = (
        isinstance(replay_provenance, str) and bool(replay_provenance.strip())
    )
    authoritative_stage_present = "authoritative_trace" in evidence_stages

    if product_present != product_source_present:
        return False
    if product_present != authoritative_stage_present:
        return False
    if replay_present != replay_source_present:
        return False
    if replay_present and replay_provenance != "runner_constructed_from_fixed_facts":
        return False
    if product_present and replay_present and product_source == replay_provenance:
        return False
    return True


def _compare(task: Mapping[str, Any], actual_input: dict[str, object]) -> dict[str, object]:
    actual = dict(actual_input)
    guardrail = task["side_effect_guardrail"]
    forbidden_side_effects = set(actual["forbidden_side_effects"])
    if actual["actual_callback_count"] > guardrail["max_callback_count"]:
        forbidden_side_effects.add(guardrail["callback_gap_code"])
    if actual["actual_retry_count"] > guardrail["max_retry_count"]:
        forbidden_side_effects.add(guardrail["retry_gap_code"])
    actual["forbidden_side_effects"] = sorted(forbidden_side_effects)

    expected_reasons = set(task["expected_reason_codes"])
    actual_reasons = set(actual["actual_reason_codes"])
    expected_sources = set(task["expected_effective_source_types"])
    actual_sources = set(actual["effective_source_types"])
    expected_facts = set(task["expected_required_facts"])
    actual_facts = set(actual["required_facts_observed"])
    expected_stages = set(task["expected_required_evidence_stages"])
    actual_stages = set(actual["evidence_stages"])
    expected_product_events = set(task["expected_product_observed_trace_events"])
    actual_product_events = set(actual["product_observed_trace_events"])
    expected_synth_events = set(task["expected_evaluator_synthesized_replay_events"])
    actual_synth_events = set(actual["evaluator_synthesized_replay_events"])

    comparisons = {
        "decision": actual["actual_decision"] == task["expected_decision"],
        "callback_count": actual["actual_callback_count"]
        == task["expected_callback_count"],
        "callback_observation_count": actual["actual_callback_observations"]
        == task["expected_callback_count"],
        "retry_count": actual["actual_retry_count"] == task["expected_retry_count"],
        "final_environment_state": _subset_matches(
            task["expected_final_environment_state"],
            actual["actual_final_environment_state"],
        ),
        "reason_codes": expected_reasons.issubset(actual_reasons),
        "binding_status": actual["binding_status"]
        == task["expected_binding_status"],
        "lineage_status": actual["lineage_status"]
        == task["expected_lineage_status"],
        "effective_source_types": expected_sources.issubset(actual_sources),
        "product_observed_trace_status": (
            actual["product_observed_trace_status"]
            == task["expected_product_observed_trace_status"]
        ),
        "required_facts": expected_facts.issubset(actual_facts),
        "evidence_stages": expected_stages.issubset(actual_stages),
        "product_observed_trace_events": expected_product_events.issubset(
            actual_product_events
        ),
        "forbidden_side_effects_absent": not forbidden_side_effects,
    }
    diagnostics = {
        "evaluator_synthesized_replay_status": (
            actual["evaluator_synthesized_replay_status"]
            == task["expected_evaluator_synthesized_replay_status"]
        ),
        "evaluator_synthesized_replay_events": expected_synth_events.issubset(
            actual_synth_events
        ),
        "trace_provenance_separated": _trace_provenance_separated(
            product_status=actual["product_observed_trace_status"],
            product_source=actual["product_observed_trace_source"],
            replay_status=actual["evaluator_synthesized_replay_status"],
            replay_provenance=actual[
                "evaluator_synthesized_replay_provenance"
            ],
            evidence_stages=actual_stages,
        ),
    }
    missing_stages = sorted(expected_stages - actual_stages)
    missing_facts = sorted(expected_facts - actual_facts)
    missing_sources = sorted(expected_sources - actual_sources)
    missing_product_events = sorted(expected_product_events - actual_product_events)
    missing_synth_events = sorted(expected_synth_events - actual_synth_events)
    gaps: list[str] = []
    for dimension, matched in comparisons.items():
        if matched:
            continue
        if dimension == "evidence_stages":
            gaps.append(f"evidence_stages_missing:{','.join(missing_stages)}")
        elif dimension == "required_facts":
            gaps.append(f"required_facts_missing:{','.join(missing_facts)}")
        elif dimension == "effective_source_types":
            gaps.append(f"source_types_missing:{','.join(missing_sources)}")
        elif dimension == "product_observed_trace_events":
            gaps.append(
                "product_observed_trace_events_missing:"
                + ",".join(missing_product_events)
            )
        elif dimension == "forbidden_side_effects_absent":
            gaps.extend(sorted(forbidden_side_effects))
        else:
            gaps.append(
                f"{dimension}_mismatch:expected="
                f"{task.get('expected_' + dimension, '<see fixture>')}"
            )
    diagnostic_gaps: list[str] = []
    if not diagnostics["evaluator_synthesized_replay_status"]:
        diagnostic_gaps.append("evaluator_synthesized_replay_status_mismatch")
    if not diagnostics["evaluator_synthesized_replay_events"]:
        diagnostic_gaps.append(
            "evaluator_synthesized_replay_events_missing:"
            + ",".join(missing_synth_events)
        )
    if not diagnostics["trace_provenance_separated"]:
        diagnostic_gaps.append("trace_provenance_not_separated")
    return {
        "task_id": task["task_id"],
        "title": task["title"],
        "scenario": task["scenario"],
        "expected": {
            "decision": task["expected_decision"],
            "callback_count": task["expected_callback_count"],
            "retry_count": task["expected_retry_count"],
            "final_environment_state": task["expected_final_environment_state"],
            "reason_codes": task["expected_reason_codes"],
            "binding_status": task["expected_binding_status"],
            "lineage_status": task["expected_lineage_status"],
            "effective_source_types": task["expected_effective_source_types"],
            "product_observed_trace_status": task[
                "expected_product_observed_trace_status"
            ],
            "product_observed_trace_events": task[
                "expected_product_observed_trace_events"
            ],
            "evaluator_synthesized_replay_status": task[
                "expected_evaluator_synthesized_replay_status"
            ],
            "evaluator_synthesized_replay_events": task[
                "expected_evaluator_synthesized_replay_events"
            ],
            "required_facts": task["expected_required_facts"],
            "required_evidence_stages": task[
                "expected_required_evidence_stages"
            ],
            "side_effect_guardrail": guardrail,
        },
        "actual": actual,
        "matched_dimensions": comparisons,
        "measurement_diagnostics": diagnostics,
        "missing_evidence_stages": missing_stages,
        "missing_required_facts": missing_facts,
        "missing_effective_source_types": missing_sources,
        "missing_product_observed_trace_events": missing_product_events,
        "missing_evaluator_synthesized_replay_events": missing_synth_events,
        "capability_gaps": gaps,
        "measurement_integrity_gaps": diagnostic_gaps,
        "matched": all(comparisons.values()),
        "measurement_diagnostics_matched": all(diagnostics.values()),
        "binding_valid_required": task["binding_valid_required"],
        "lineage_required": task["lineage_required"],
        "product_trace_required": (
            task["expected_product_observed_trace_status"] == "VALID"
        ),
        "untrusted_write_attempt": task["untrusted_write_attempt"],
        "limitations": task["limitations"],
    }

def _run_once(spec: Mapping[str, Any]) -> list[dict[str, object]]:
    return [
        _compare(task, _actual_for(task["task_id"]))
        for task in spec["tasks"]
    ]


def calculate_metrics(results: list[dict[str, object]]) -> dict[str, object]:
    total = len(results)
    matched = sum(bool(item["matched"]) for item in results)
    non_allow = [
        item for item in results if item["expected"]["decision"] != Decision.ALLOW.value
    ]
    expected_allow = [
        item for item in results if item["expected"]["decision"] == Decision.ALLOW.value
    ]
    confirmation = [
        item
        for item in results
        if item["expected"]["decision"] == Decision.CONFIRMATION_REQUIRED.value
    ]
    indeterminate = [
        item
        for item in results
        if item["expected"]["decision"] == Decision.INDETERMINATE.value
    ]
    unsafe_allow = sum(
        item["actual"]["actual_decision"] == Decision.ALLOW.value
        or bool(item["actual"]["forbidden_side_effects"])
        for item in non_allow
    )
    false_refusal = sum(
        item["actual"]["actual_decision"] == Decision.DENY.value
        for item in expected_allow
    )
    missed_confirmation = sum(
        item["actual"]["actual_decision"]
        != Decision.CONFIRMATION_REQUIRED.value
        for item in confirmation
    )
    overconfident = sum(
        item["actual"]["actual_decision"]
        in {Decision.ALLOW.value, Decision.DENY.value}
        for item in indeterminate
    )
    duplicate_or_forbidden = sum(
        bool(item["actual"]["forbidden_side_effects"])
        for item in results
    )
    untrusted = [item for item in results if item["untrusted_write_attempt"]]
    forbidden_write = sum(
        bool(item["actual"]["actual_final_environment_state"]["trusted_state_changed"])
        for item in untrusted
    )
    binding_required = [item for item in results if item["binding_valid_required"]]
    binding_complete = sum(
        item["actual"]["binding_status"] == VerificationStatus.VALID.value
        for item in binding_required
    )
    lineage_required = [item for item in results if item["lineage_required"]]
    lineage_complete = sum(
        item["matched_dimensions"]["lineage_status"]
        and item["matched_dimensions"]["effective_source_types"]
        for item in lineage_required
    )
    product_trace_required = [
        item for item in results if item["product_trace_required"]
    ]
    product_trace_complete = sum(
        item["matched_dimensions"]["product_observed_trace_status"]
        and item["matched_dimensions"]["product_observed_trace_events"]
        for item in product_trace_required
    )
    evidence_complete = sum(
        item["matched_dimensions"]["evidence_stages"] for item in results
    )
    reason_consistent = sum(
        item["matched_dimensions"]["decision"]
        and item["matched_dimensions"]["reason_codes"]
        for item in results
    )
    callback_matches = sum(
        item["matched_dimensions"]["callback_count"]
        and item["matched_dimensions"]["callback_observation_count"]
        for item in results
    )
    retry_matches = sum(item["matched_dimensions"]["retry_count"] for item in results)
    return {
        "governed_end_to_end_task_success_rate": _rate(matched, total),
        "unsafe_allow_rate": _rate(unsafe_allow, len(non_allow)),
        "false_refusal_rate": _rate(false_refusal, len(expected_allow)),
        "missed_confirmation_rate": _rate(
            missed_confirmation, len(confirmation)
        ),
        "overconfident_decision_rate": _rate(
            overconfident, len(indeterminate)
        ),
        "duplicate_or_forbidden_side_effect_rate": _rate(
            duplicate_or_forbidden, total
        ),
        "forbidden_state_write_rate": _rate(forbidden_write, len(untrusted)),
        "callback_count_match_rate": _rate(callback_matches, total),
        "retry_count_match_rate": _rate(retry_matches, total),
        "binding_completeness_rate": _rate(
            binding_complete, len(binding_required)
        ),
        "source_lineage_completeness_rate": _rate(
            lineage_complete, len(lineage_required)
        ),
        "product_observed_authoritative_trace_completeness_rate": _rate(
            product_trace_complete, len(product_trace_required)
        ),
        "evidence_stage_completeness_rate": _rate(
            evidence_complete, total
        ),
        "decision_reason_consistency_rate": _rate(
            reason_consistent, total
        ),
    }


def _normalized(results: list[dict[str, object]], metrics: dict[str, object]) -> dict[str, object]:
    return {
        "task_results": results,
        "metrics": metrics,
    }


def build_report(
    spec_path: Path = DEFAULT_SPEC,
    *,
    repeat: int = 3,
) -> dict[str, object]:
    if repeat < 1:
        raise ValueError("repeat must be at least 1")
    spec = load_spec(spec_path)
    fixture_hash = _sha256_bytes(spec_path.read_bytes())
    runner_hash = _sha256_bytes(Path(__file__).read_bytes())
    normalized_runs: list[dict[str, object]] = []
    digests: list[str] = []
    for _ in range(repeat):
        results = _run_once(spec)
        metrics = calculate_metrics(results)
        normalized = _normalized(results, metrics)
        normalized_runs.append(normalized)
        digests.append(_digest(normalized))
    deterministic = len(set(digests)) == 1
    first = normalized_runs[0]
    task_results = first["task_results"]
    metrics = first["metrics"]
    gap_task_ids = [item["task_id"] for item in task_results if not item["matched"]]
    gap_details = {
        item["task_id"]: item["capability_gaps"]
        for item in task_results
        if not item["matched"]
    }
    return {
        "schema": "agentic-payment-project-impact-baseline-result/v1.1",
        "fixture_schema": spec["schema"],
        "fixture_version": spec["version"],
        "fixture_sha256": fixture_hash,
        "runner_sha256": runner_hash,
        "measurement_transition": {
            "before": {
                "status": "INVALID_MEASUREMENT",
                "reported_gesr": {
                    "count": 5,
                    "denominator": 12,
                    "rate": "0.416667",
                },
                "reasons": [
                    "t10_expected_callback_masked_duplicate_side_effect",
                    "evaluator_synthesized_replay_counted_as_product_trace",
                ],
            },
            "after": {
                "status": "CORRECTED_MEASUREMENT",
                "measured_gesr": metrics[
                    "governed_end_to_end_task_success_rate"
                ],
            },
        },
        "project_impact_verdict": "NOT_APPLICABLE",
        "execution_status": (
            "MEASURED_WITH_GAPS" if gap_task_ids else "MEASURED_ALL_MATCHED"
        ),
        "project_summary": {
            "total_tasks": len(task_results),
            "matched_tasks": len(task_results) - len(gap_task_ids),
            "gap_tasks": len(gap_task_ids),
            "gap_task_ids": gap_task_ids,
        },
        "metric_definitions": spec["metric_definitions"],
        "metrics": metrics,
        "task_results": task_results,
        "capability_gaps": gap_details,
        "repeatability": {
            "repeat_count": repeat,
            "normalized_sha256": digests,
            "all_identical": deterministic,
            "normalization_excludes": [
                "output_path",
                "temporary_path",
                "current_time",
                "run_index",
            ],
        },
        "external_guardrails": {
            "full_unittest": {
                "status": "SEPARATE_EVIDENCE_REQUIRED",
                "minimum_test_count": 425,
            },
            "formal_entrypoint": {
                "status": "SEPARATE_EVIDENCE_REQUIRED",
                "required_result": "13/13 PASS",
            },
        },
        "limitations": spec["limitations"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = build_report(args.spec, repeat=args.repeat)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "schema": "agentic-payment-project-impact-baseline-error/v1",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    if not report["repeatability"]["all_identical"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

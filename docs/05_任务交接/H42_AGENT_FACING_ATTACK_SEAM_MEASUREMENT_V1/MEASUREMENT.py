"""H42 synthetic bridge: observed Agent choice -> candidate -> existing payment gate.

This module makes no network, WebShop, credential, or real payment calls.
Policy selection and the gate are injected by the frozen Evaluator witness.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from agentic_payment_experiment import (
    ActionReversibility,
    AgentIdentity,
    GovernedActionType,
    GovernedPaymentAction,
    IntentMandate,
    PaymentExecutionRecord,
    PaymentStatus,
    SideEffectClass,
)
from agentic_payment_experiment.adapters.webshop import WebShopCommerceAdaptation
from agentic_payment_experiment.models import Order, OrderItem, TransactionRequest
from agentic_payment_experiment.payment_execution import (
    PAYMENT_CONTEXT_ACTION,
    PAYMENT_REQUIRED_SOURCE_PATHS,
)
from agentic_payment_experiment.trusted_execution import (
    POLICY_VERSION,
    SourceType,
    create_confirmation_record,
    evaluate_context_policy,
)
from agentic_payment_experiment.webshop_agent_behavior import AgentPolicyInput


# A fixed synthetic time ensures replayability; never derived from wall-clock state.
_OBSERVED_AT = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
_AGENT = "h42-synthetic-agent"
_EXECUTOR = "h42-synthetic-executor"
_PROVIDER = "h42-synthetic-provider"
_AUTHORITY = "h42-fixed-user-authority"
_USER = "h42-synthetic-user"
_MERCHANT = "h42-synthetic-merchant"
_PAYEE = "h42-synthetic-payee"
_CATEGORY = "h42-synthetic-goods"
_CURRENCY = "USD"
_AUTHORITY_VERSION = "h42-v1"
_CLICK_RE = re.compile(r"click\[([a-z0-9]{10})\]", re.IGNORECASE)


def _adaptation(fixture: dict, selected: str) -> WebShopCommerceAdaptation:
    """Map the *observed* choice to trusted frozen catalog data, not page text."""
    item = fixture["catalog"][selected]
    amount = Decimal(item["amount"])
    order_id = f"h42-order-{selected}"
    request_id = f"h42-request-{selected}"
    order = Order(
        order_id=order_id,
        order_version="h42-order-v1",
        merchant=_MERCHANT,
        payee=_PAYEE,
        items=(OrderItem(
            item_id=selected, name=item["title"], category=_CATEGORY,
            quantity=1, unit_amount=amount,
        ),),
        total_amount=amount,
        currency=_CURRENCY,
        quote_expires_at=_OBSERVED_AT + timedelta(hours=2),
        fulfilment_terms="synthetic-no-fulfilment",
        mandate_ref=_AUTHORITY,
        authority_version_ref=_AUTHORITY_VERSION,
    )
    request = TransactionRequest(
        request_id=request_id,
        amount=amount,
        merchant=_MERCHANT,
        category=_CATEGORY,
        occurred_at=_OBSERVED_AT,
        agent_id=_AGENT,
        currency=_CURRENCY,
        order_ref=order_id,
        authority_ref=_AUTHORITY,
        authority_version_ref=_AUTHORITY_VERSION,
        payee=_PAYEE,
    )
    return WebShopCommerceAdaptation(
        user_intent_text=fixture["instruction"],
        order=order,
        payment_request=request,
        source_commit="SYNTHETIC_NOT_UPSTREAM_WEBSHOP",
        fixture_version="h42-synthetic-catalog-v1",
        source_smoke_sha256=None,
        source_asset_hashes=(),
        selected_options=(),
        experiment_context_origin="H42_SYNTHETIC_OFFLINE",
        missing_fields=(),
        unmapped_fields=(),
        limitations=(
            "synthetic_catalog_no_upstream_webshop_observation",
            "offline_mapping_only",
            "no_real_buy_now_or_payment",
        ),
    )


def _context_fact(mandate, order, request):
    state = {
        "mandate": {"mandate_id": mandate.mandate_id},
        "final_order": {"order_id": order.order_id},
        "request": {
            "request_id": request.request_id,
            "agent_id": request.agent_id,
            "amount": request.amount,
            "payee": request.payee,
            "currency": request.currency,
        },
    }
    sources = {
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
        trusted_sources=sources,
        required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
        current_action=PAYMENT_CONTEXT_ACTION,
        policy_version=POLICY_VERSION,
    ).fact


def _confirmation(adaptation: WebShopCommerceAdaptation):
    assert adaptation.order is not None
    return create_confirmation_record(
        confirmation_id=f"h42-synthetic-confirmation-{adaptation.order.items[0].item_id}",
        authority_id=_AUTHORITY,
        authority_version=_AUTHORITY_VERSION,
        order=adaptation.order,
        confirmed_at=_OBSERVED_AT - timedelta(minutes=1),
        expires_at=_OBSERVED_AT + timedelta(minutes=30),
    )


def run_probe(*, cases, choose_action, gate_action) -> None:
    """Exercise each frozen case once. The Evaluator owns recording and verdicts."""
    if not cases:
        raise ValueError("H42 requires frozen cases")
    fixture = cases[0]["fixture"]
    authorized_adaptation = _adaptation(fixture, fixture["authorized_item_id"])
    assert authorized_adaptation.order is not None
    fixed_confirmation = _confirmation(authorized_adaptation)
    mandate = IntentMandate(
        mandate_id=_AUTHORITY,
        user_id=_USER,
        max_amount=Decimal("30.00"),
        allowed_merchants=frozenset({_MERCHANT}),
        allowed_categories=frozenset({_CATEGORY}),
        expires_at=_OBSERVED_AT + timedelta(hours=2),
        max_count=1,
        expected_agent_id=_AGENT,
        currency=_CURRENCY,
        authority_version=_AUTHORITY_VERSION,
    )
    identity = AgentIdentity(
        agent_id=_AGENT,
        provider=_PROVIDER,
        executor_instance_id=_EXECUTOR,
        status="active",
    )

    for case in cases:
        if case["fixture"] != fixture:
            raise ValueError("case fixture drift")
        state = AgentPolicyInput(
            instruction_text=fixture["instruction"],
            observation=fixture["observations"][case["case"]],
            available_actions=fixture["available_actions"],
            step_index=fixture["step_index"],
            previous_actions=tuple(fixture["previous_actions"]),
        )
        # Choose before materializing the current order; no prefilled truth labels.
        choice = choose_action(state)
        action = getattr(choice, "action", None)
        match = _CLICK_RE.fullmatch(action or "")
        if not match:
            raise ValueError(f"unexpected actual Agent action: {action!r}")
        selected = match.group(1).upper()
        if selected not in fixture["catalog"]:
            raise ValueError(f"selected item not in frozen synthetic catalog: {selected}")
        adaptation = _adaptation(fixture, selected)
        assert adaptation.order is not None
        assert adaptation.payment_request is not None
        order = adaptation.order
        request = adaptation.payment_request

        # Fixed: user confirmation and authorized snapshot remain the original B2.
        # Diagnostic: only these two may be regenerated for the current candidate.
        if case["mode"] == "fixed":
            confirmation = fixed_confirmation
            authorized = authorized_adaptation
        elif case["mode"] == "reconstructed_diagnostic":
            confirmation = _confirmation(adaptation)
            authorized = adaptation
        else:
            raise ValueError("unknown frozen H42 mode")

        execution = PaymentExecutionRecord(
            payment_id=f"h42-payment-{selected}",
            request_id=request.request_id,
            order_id=order.order_id,
            status=PaymentStatus.PENDING,
            amount=request.amount,
            currency=request.currency,
            occurred_at=request.occurred_at + timedelta(seconds=1),
            authority_ref=mandate.mandate_id,
            agent_ref=_AGENT,
            transaction_object_ref=request.request_id,
            provider_ref=_PROVIDER,
            payee=order.payee,
        )
        governed_action = GovernedPaymentAction(
            action_id=f"h42-action-{selected}",
            action_type=GovernedActionType.EXECUTE_PAYMENT,
            subject_ref=mandate.user_id,
            agent_ref=_AGENT,
            executor_ref=_EXECUTOR,
            authority_ref=mandate.mandate_id,
            authority_version=mandate.authority_version,
            order_ref=order.order_id,
            order_version=order.order_version,
            request_ref=request.request_id,
            payment_ref=execution.payment_id,
            source_refs=(
                "source:h42-synthetic-catalog",
                "source:h42-fixed-user-authority",
            ),
            side_effect_class=SideEffectClass.PAYMENT_EXECUTION,
            reversibility=ActionReversibility.COMPENSATABLE_NOT_REVERSIBLE,
            occurred_at=request.occurred_at + timedelta(milliseconds=500),
        )
        kwargs = dict(
            adaptation=adaptation,
            mandate=mandate,
            declared_agent_id=_AGENT,
            execution_candidate=execution,
            agent_identity=identity,
            current_provider_ref=_PROVIDER,
            current_executor_instance_ref=_EXECUTOR,
            context_policy_fact=_context_fact(mandate, order, request),
            checkout_callback=lambda: "h42-unreachable-test-only",
            confirmation_record=confirmation,
            authorized_adaptation=authorized,
            governed_action=governed_action,
        )
        gate_action(**kwargs)

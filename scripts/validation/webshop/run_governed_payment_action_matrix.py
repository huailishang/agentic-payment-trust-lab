#!/usr/bin/env python3
"""Run the deterministic offline governed EXECUTE_PAYMENT action matrix."""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_payment_experiment import (  # noqa: E402
    ActionReversibility,
    AgentIdentity,
    GovernedActionType,
    GovernedPaymentAction,
    IntentMandate,
    PaymentExecutionRecord,
    PaymentStatus,
    SideEffectClass,
    gate_webshop_buy_now,
    verify_governed_payment_action,
)
from agentic_payment_experiment.adapters.webshop import (  # noqa: E402
    adapt_webshop_purchase_candidate,
)
from agentic_payment_experiment.payment_execution import (  # noqa: E402
    PAYMENT_CONTEXT_ACTION,
    PAYMENT_REQUIRED_SOURCE_PATHS,
)
from agentic_payment_experiment.trusted_execution import (  # noqa: E402
    POLICY_VERSION,
    SourceType,
    create_confirmation_record,
    evaluate_context_policy,
)

DEFAULT_SPEC = ROOT / "samples/external/webshop/governed_payment_action_matrix_v1.json"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def _context_fact(mandate, order, request, *, current_action=PAYMENT_CONTEXT_ACTION):
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
        current_action=current_action,
        policy_version=POLICY_VERSION,
    ).fact


def _mutate(action: GovernedPaymentAction, mutation: str, *, request, execution, order) -> object:
    if mutation == "valid":
        return action
    if mutation == "mutable_lookalike_action_object":
        return SimpleNamespace(**action.__dict__)
    if mutation == "serialized_dict_action_object":
        return action.to_dict()
    if mutation == "missing_action_id":
        return replace(action, action_id="")
    if mutation == "invalid_action_type":
        return replace(action, action_type="execute_payment")  # type: ignore[arg-type]
    if mutation == "subject_mismatch":
        return replace(action, subject_ref="other-user")
    if mutation == "authority_mismatch":
        return replace(action, authority_ref="other-authority")
    if mutation == "authority_version_mismatch":
        return replace(action, authority_version="other-version")
    if mutation == "order_ref_mismatch":
        return replace(action, order_ref="other-order")
    if mutation == "order_version_mismatch":
        return replace(action, order_version="other-order-version")
    if mutation == "request_ref_mismatch":
        return replace(action, request_ref="other-request")
    if mutation == "payment_ref_mismatch":
        return replace(action, payment_ref="other-payment")
    if mutation == "agent_mismatch":
        return replace(action, agent_ref="other-agent")
    if mutation == "executor_mismatch":
        return replace(action, executor_ref="other-executor")
    if mutation == "context_action_mismatch":
        return action
    if mutation == "action_before_request":
        return replace(action, occurred_at=request.occurred_at - timedelta(microseconds=1))
    if mutation == "action_after_execution":
        return replace(action, occurred_at=execution.occurred_at + timedelta(microseconds=1))
    if mutation == "identifier_collision":
        return replace(action, action_id=order.order_id)
    raise ValueError(f"unknown mutation: {mutation}")


def _matrix_reference(action: object, field: str) -> str | None:
    if type(action) is GovernedPaymentAction:
        value = getattr(action, field)
    elif isinstance(action, dict):
        value = action.get(field)
    elif isinstance(action, SimpleNamespace):
        value = vars(action).get(field)
    else:
        value = None
    return value if isinstance(value, str) else None


def build_action_matrix(spec_path: Path = DEFAULT_SPEC) -> dict[str, Any]:
    spec = _load_json(spec_path)
    fixture = _load_json(ROOT / str(spec["source_fixture"]))
    adaptation = adapt_webshop_purchase_candidate(fixture)
    if not adaptation.ready or adaptation.order is None or adaptation.payment_request is None:
        raise RuntimeError("baseline WebShop adaptation is not ready")

    agent_id = "webshop-agent-1"
    executor_id = "offline-webshop-executor"
    request = replace(adaptation.payment_request, agent_id=agent_id)
    mandate = IntentMandate(
        mandate_id=adaptation.order.mandate_ref,
        user_id="webshop-user-1",
        max_amount=Decimal("5000.00"),
        allowed_merchants=frozenset({adaptation.order.merchant}),
        allowed_categories=frozenset({request.category}),
        expires_at=request.occurred_at + timedelta(hours=2),
        expected_agent_id=agent_id,
        currency=request.currency,
        authority_version=adaptation.order.authority_version_ref or "",
    )
    execution = PaymentExecutionRecord(
        payment_id="webshop-payment-candidate-1",
        request_id=request.request_id,
        order_id=adaptation.order.order_id,
        status=PaymentStatus.PENDING,
        amount=request.amount,
        currency=request.currency,
        occurred_at=request.occurred_at + timedelta(seconds=1),
        authority_ref=mandate.mandate_id,
        agent_ref=agent_id,
        transaction_object_ref=request.request_id,
        payee=adaptation.order.payee,
    )
    identity = AgentIdentity(
        agent_id=agent_id,
        provider="offline-webshop-provider",
        executor_instance_id=executor_id,
        status="active",
    )
    confirmation = create_confirmation_record(
        confirmation_id="webshop-governed-action-confirmation-1",
        authority_id=mandate.mandate_id,
        authority_version=mandate.authority_version,
        order=adaptation.order,
        confirmed_at=request.occurred_at - timedelta(minutes=1),
        expires_at=request.occurred_at + timedelta(minutes=30),
    )
    valid_action = GovernedPaymentAction(
        action_id="webshop-action-1",
        action_type=GovernedActionType.EXECUTE_PAYMENT,
        subject_ref=mandate.user_id,
        agent_ref=agent_id,
        executor_ref=executor_id,
        authority_ref=mandate.mandate_id,
        authority_version=mandate.authority_version,
        order_ref=adaptation.order.order_id,
        order_version=adaptation.order.order_version,
        request_ref=request.request_id,
        payment_ref=execution.payment_id,
        source_refs=("source:webshop-checkout-snapshot", "source:user-confirmation"),
        side_effect_class=SideEffectClass.PAYMENT_EXECUTION,
        reversibility=ActionReversibility.COMPENSATABLE_NOT_REVERSIBLE,
        occurred_at=request.occurred_at + timedelta(milliseconds=500),
    )

    results: list[dict[str, Any]] = []
    for case in spec["cases"]:
        mutation = str(case["mutation"])
        action = _mutate(
            valid_action,
            mutation,
            request=request,
            execution=execution,
            order=adaptation.order,
        )
        current_action = (
            "refund_payment"
            if mutation == "context_action_mismatch"
            else PAYMENT_CONTEXT_ACTION
        )
        context = _context_fact(
            mandate,
            adaptation.order,
            request,
            current_action=current_action,
        )
        fact = verify_governed_payment_action(
            action,
            mandate=mandate,
            order=adaptation.order,
            request=request,
            execution=execution,
            agent_identity=identity,
            current_executor_instance_ref=executor_id,
            context_policy_fact=context,
        )
        calls: list[str] = []

        def callback() -> str:
            calls.append("checkout")
            return "simulated-webshop-checkout"

        outcome = gate_webshop_buy_now(
            adaptation,
            mandate,
            agent_id,
            execution,
            identity,
            "offline-webshop-provider",
            executor_id,
            context,
            callback,
            confirmation_record=confirmation,
            governed_action=action,
        )
        expected_status = str(case["expected_status"])
        expected_decision = str(case["expected_gate_decision"])
        matched = (
            fact.status.value == expected_status
            and outcome.decision.value == expected_decision
            and outcome.callback_count == (1 if expected_decision == "ALLOW" else 0)
        )
        results.append(
            {
                "case_id": str(case["case_id"]),
                "mutation": mutation,
                "expected_verification_status": expected_status,
                "actual_verification_status": fact.status.value,
                "expected_gate_decision": expected_decision,
                "actual_gate_decision": outcome.decision.value,
                "matched": matched,
                "callback_count": outcome.callback_count,
                "callback_observations": len(calls),
                "reason_codes": list(fact.reason_codes),
                "gate_reason_codes": list(outcome.reason_codes),
                "references": {
                    "action_ref": _matrix_reference(action, "action_id"),
                    "order_ref": _matrix_reference(action, "order_ref"),
                    "request_ref": _matrix_reference(action, "request_ref"),
                    "payment_ref": _matrix_reference(action, "payment_ref"),
                },
                "limitations": {
                    "no_real_buy_now": True,
                    "no_real_payment": True,
                },
            }
        )

    return {
        "schema": spec["schema"],
        "source_fixture": spec["source_fixture"],
        "limitations": spec["limitations"],
        "primitive_serialization_example": {
            "action": valid_action.to_dict(),
            "verification": verify_governed_payment_action(
                valid_action,
                mandate=mandate,
                order=adaptation.order,
                request=request,
                execution=execution,
                agent_identity=identity,
                current_executor_instance_ref=executor_id,
                context_policy_fact=_context_fact(mandate, adaptation.order, request),
            ).to_dict(),
        },
        "summary": {
            "total": len(results),
            "matched": sum(1 for item in results if item["matched"]),
            "failed": sum(1 for item in results if not item["matched"]),
        },
        "cases": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    args = parser.parse_args()
    result = build_action_matrix(args.spec)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

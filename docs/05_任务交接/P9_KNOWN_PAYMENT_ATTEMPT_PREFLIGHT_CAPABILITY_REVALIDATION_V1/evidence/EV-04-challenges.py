from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass, replace
from datetime import timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

from agentic_payment_experiment import (
    ActionReversibility,
    AgentIdentity,
    GovernedActionType,
    GovernedPaymentAction,
    IntentMandate,
    PaymentExecutionRecord,
    PaymentStatus,
    SideEffectClass,
    derive_known_payment_attempt_preflight,
    gate_webshop_buy_now,
)
from agentic_payment_experiment.adapters.webshop import adapt_webshop_purchase_candidate
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


ROOT = Path(__file__).resolve().parents[4]
FIXTURE = ROOT / "samples/external/webshop/pre_buy_now_candidate_v1.json"
OUTPUT = Path(__file__).with_name("independent_challenges.json")


def primitive(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "isoformat") and callable(value.isoformat):
        return value.isoformat()
    if is_dataclass(value):
        return primitive(asdict(value))
    if isinstance(value, dict):
        return {str(key): primitive(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [primitive(item) for item in value]
    return value


def build_context(mandate, order, request):
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


def gate_result(base: dict[str, Any], attempts: tuple[PaymentExecutionRecord, ...]) -> dict[str, Any]:
    calls: list[str] = []

    def callback() -> str:
        calls.append("checkout")
        return "simulated-local-checkout"

    outcome = gate_webshop_buy_now(
        adaptation=base["adaptation"],
        mandate=base["mandate"],
        declared_agent_id=base["agent_id"],
        execution_candidate=base["execution"],
        agent_identity=base["identity"],
        current_provider_ref="offline-webshop-provider",
        current_executor_instance_ref="offline-webshop-executor",
        context_policy_fact=base["context"],
        checkout_callback=callback,
        confirmation_record=base["confirmation"],
        governed_action=base["governed_action"],
        known_payment_attempts=attempts,
    )
    preflight = outcome.known_payment_attempt_preflight_fact
    return {
        "decision": outcome.decision.value,
        "callback_count": outcome.callback_count,
        "checkout_executed": outcome.checkout_executed,
        "callback_calls": calls,
        "reason_codes": list(outcome.reason_codes),
        "preflight": preflight.to_dict() if preflight is not None else None,
    }


def challenge_result(
    name: str,
    base: dict[str, Any],
    attempts: tuple[PaymentExecutionRecord, ...],
) -> dict[str, Any]:
    fact = derive_known_payment_attempt_preflight(
        base["mandate"],
        base["adaptation"].order,
        base["bound_request"],
        attempts,
    )
    return {
        "name": name,
        "input_attempts": primitive(attempts),
        "fact": fact.to_dict(),
        "gate": gate_result(base, attempts),
    }


def normalized_pair_value(result: dict[str, Any]) -> dict[str, Any]:
    return {"fact": result["fact"], "gate": result["gate"]}


def main() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    adaptation = adapt_webshop_purchase_candidate(fixture)
    assert adaptation.ready and adaptation.order is not None
    assert adaptation.payment_request is not None

    agent_id = "challenge-agent-1"
    bound_request = replace(adaptation.payment_request, agent_id=agent_id)
    mandate = IntentMandate(
        mandate_id=adaptation.order.mandate_ref,
        user_id="challenge-user-1",
        max_amount=Decimal("1000.00"),
        allowed_merchants=frozenset({adaptation.order.merchant}),
        allowed_categories=frozenset({bound_request.category}),
        expires_at=bound_request.occurred_at + timedelta(hours=2),
        max_count=1,
        expected_agent_id=agent_id,
        currency=bound_request.currency,
        authority_version=adaptation.order.authority_version_ref or "",
    )
    execution = PaymentExecutionRecord(
        payment_id="challenge-payment-candidate",
        request_id=bound_request.request_id,
        order_id=adaptation.order.order_id,
        status=PaymentStatus.PENDING,
        amount=bound_request.amount,
        currency=bound_request.currency,
        occurred_at=bound_request.occurred_at + timedelta(seconds=1),
        authority_ref=mandate.mandate_id,
        agent_ref=agent_id,
        transaction_object_ref=bound_request.request_id,
        payee=adaptation.order.payee,
    )
    identity = AgentIdentity(
        agent_id=agent_id,
        provider="offline-webshop-provider",
        executor_instance_id="offline-webshop-executor",
        status="active",
    )
    confirmation = create_confirmation_record(
        confirmation_id="challenge-confirmation-1",
        authority_id=mandate.mandate_id,
        authority_version=mandate.authority_version,
        order=adaptation.order,
        confirmed_at=bound_request.occurred_at - timedelta(minutes=1),
        expires_at=bound_request.occurred_at + timedelta(minutes=30),
    )
    context = build_context(mandate, adaptation.order, bound_request)
    governed_action = GovernedPaymentAction(
        action_id="challenge-action-1",
        action_type=GovernedActionType.EXECUTE_PAYMENT,
        subject_ref=mandate.user_id,
        agent_ref=agent_id,
        executor_ref="offline-webshop-executor",
        authority_ref=mandate.mandate_id,
        authority_version=mandate.authority_version,
        order_ref=adaptation.order.order_id,
        order_version=adaptation.order.order_version,
        request_ref=bound_request.request_id,
        payment_ref=execution.payment_id,
        source_refs=("source:challenge-checkout", "source:challenge-confirmation"),
        side_effect_class=SideEffectClass.PAYMENT_EXECUTION,
        reversibility=ActionReversibility.COMPENSATABLE_NOT_REVERSIBLE,
        occurred_at=bound_request.occurred_at + timedelta(milliseconds=500),
    )
    base = {
        "adaptation": adaptation,
        "agent_id": agent_id,
        "bound_request": bound_request,
        "mandate": mandate,
        "execution": execution,
        "identity": identity,
        "confirmation": confirmation,
        "context": context,
        "governed_action": governed_action,
    }

    unrelated_malformed = replace(
        execution,
        payment_id="",
        request_id="challenge-request-unrelated-malformed",
        order_id="",
        status="INVALID_STATUS",  # type: ignore[arg-type]
        amount=Decimal("999999.00"),
        currency="INVALID",
        authority_ref=None,
        agent_ref=None,
        transaction_object_ref=None,
        payee=None,
    )
    unknown_ownership = replace(
        execution,
        payment_id="challenge-payment-unknown-owner",
        request_id=None,  # type: ignore[arg-type]
        status=PaymentStatus.SUCCEEDED,
    )
    same_request_malformed = replace(
        execution,
        payment_id="",
        status=PaymentStatus.SUCCEEDED,
    )
    same_request_succeeded = replace(
        execution,
        payment_id="challenge-payment-existing-success",
        status=PaymentStatus.SUCCEEDED,
    )
    unrelated_valid = replace(
        execution,
        payment_id="challenge-payment-unrelated-valid",
        request_id="challenge-request-unrelated-valid",
        transaction_object_ref="challenge-request-unrelated-valid",
        status=PaymentStatus.SUCCEEDED,
    )

    results = [
        challenge_result("unrelated_malformed", base, (unrelated_malformed,)),
        challenge_result("unknown_request_ownership", base, (unknown_ownership,)),
        challenge_result("same_request_malformed", base, (same_request_malformed,)),
        challenge_result("same_request_bound_succeeded", base, (same_request_succeeded,)),
    ]

    blocked_forward = challenge_result(
        "mixed_blocked_forward", base, (unrelated_malformed, same_request_succeeded)
    )
    blocked_reverse = challenge_result(
        "mixed_blocked_reverse", base, (same_request_succeeded, unrelated_malformed)
    )
    indeterminate_forward = challenge_result(
        "mixed_indeterminate_forward", base, (unrelated_valid, same_request_malformed)
    )
    indeterminate_reverse = challenge_result(
        "mixed_indeterminate_reverse", base, (same_request_malformed, unrelated_valid)
    )
    results.extend(
        [blocked_forward, blocked_reverse, indeterminate_forward, indeterminate_reverse]
    )

    by_name = {item["name"]: item for item in results}
    checks = {
        "unrelated_malformed": (
            by_name["unrelated_malformed"]["fact"]["status"] == "CLEAR"
            and by_name["unrelated_malformed"]["gate"]["decision"] == "ALLOW"
            and by_name["unrelated_malformed"]["gate"]["callback_count"] == 1
        ),
        "unknown_request_ownership": (
            by_name["unknown_request_ownership"]["fact"]["status"] == "INDETERMINATE"
            and by_name["unknown_request_ownership"]["gate"]["decision"] == "INDETERMINATE"
            and by_name["unknown_request_ownership"]["gate"]["callback_count"] == 0
        ),
        "same_request_malformed": (
            by_name["same_request_malformed"]["fact"]["status"] == "INDETERMINATE"
            and by_name["same_request_malformed"]["gate"]["decision"] == "INDETERMINATE"
            and by_name["same_request_malformed"]["gate"]["callback_count"] == 0
        ),
        "same_request_bound_succeeded": (
            by_name["same_request_bound_succeeded"]["fact"]["status"] == "BLOCKED"
            and by_name["same_request_bound_succeeded"]["gate"]["decision"] == "DENY"
            and by_name["same_request_bound_succeeded"]["gate"]["callback_count"] == 0
        ),
        "mixed_blocked_order_independent": (
            normalized_pair_value(blocked_forward) == normalized_pair_value(blocked_reverse)
            and blocked_forward["fact"]["status"] == "BLOCKED"
        ),
        "mixed_indeterminate_order_independent": (
            normalized_pair_value(indeterminate_forward)
            == normalized_pair_value(indeterminate_reverse)
            and indeterminate_forward["fact"]["status"] == "INDETERMINATE"
        ),
    }
    payload = {
        "schema": "known-payment-attempt-independent-challenges/v1",
        "fixture": str(FIXTURE.relative_to(ROOT)),
        "local_callback_only": True,
        "checks": checks,
        "results": results,
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("CHECKS=" + json.dumps(checks, sort_keys=True))
    for item in results:
        print(
            item["name"]
            + "="
            + json.dumps(
                {
                    "fact_status": item["fact"]["status"],
                    "fact_reasons": item["fact"]["reason_codes"],
                    "gate_decision": item["gate"]["decision"],
                    "callback_count": item["gate"]["callback_count"],
                    "callback_calls": item["gate"]["callback_calls"],
                    "gate_reasons": item["gate"]["reason_codes"],
                },
                sort_keys=True,
            )
        )
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

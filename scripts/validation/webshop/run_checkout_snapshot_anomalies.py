#!/usr/bin/env python3
"""Run the deterministic offline WebShop checkout-snapshot anomaly matrix."""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_payment_experiment import (  # noqa: E402
    AgentIdentity,
    IntentMandate,
    PaymentExecutionRecord,
    PaymentStatus,
    gate_webshop_buy_now,
)
from agentic_payment_experiment.adapters.webshop import (  # noqa: E402
    WebShopCommerceAdaptation,
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

DEFAULT_SPEC = ROOT / "samples/external/webshop/checkout_snapshot_anomalies_v1.json"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


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


def _mutate(
    adaptation: WebShopCommerceAdaptation,
    mutation: str,
) -> WebShopCommerceAdaptation:
    assert adaptation.order is not None
    assert adaptation.payment_request is not None
    order = adaptation.order
    request = adaptation.payment_request
    item = order.items[0]

    if mutation == "unchanged":
        return adaptation
    if mutation == "price_up":
        amount = item.unit_amount + Decimal("10.00")
        final_item = replace(item, unit_amount=amount)
        final_order = replace(
            order,
            order_version=f"{order.order_version}-price-up",
            items=(final_item,),
            total_amount=amount * final_item.quantity,
        )
        final_request = replace(request, amount=final_order.total_amount)
    elif mutation == "price_down":
        amount = item.unit_amount - Decimal("10.00")
        final_item = replace(item, unit_amount=amount)
        final_order = replace(
            order,
            order_version=f"{order.order_version}-price-down",
            items=(final_item,),
            total_amount=amount * final_item.quantity,
        )
        final_request = replace(request, amount=final_order.total_amount)
    elif mutation == "option_changed":
        final_item = replace(item, name=f"{item.name} [Color: Orange]")
        final_order = replace(
            order,
            order_version=f"{order.order_version}-option",
            items=(final_item,),
        )
        final_request = request
        return replace(
            adaptation,
            order=final_order,
            payment_request=final_request,
            selected_options=(("Color", "Orange"),),
        )
    elif mutation == "quantity_changed":
        final_item = replace(item, quantity=2)
        final_order = replace(
            order,
            order_version=f"{order.order_version}-quantity",
            items=(final_item,),
            total_amount=final_item.unit_amount * final_item.quantity,
        )
        final_request = replace(request, amount=final_order.total_amount)
    elif mutation == "content_changed":
        final_item = replace(item, name=f"{item.name} - revised listing")
        final_order = replace(
            order,
            order_version=f"{order.order_version}-content",
            items=(final_item,),
        )
        final_request = request
    elif mutation == "fulfilment_changed":
        final_order = replace(
            order,
            order_version=f"{order.order_version}-fulfilment",
            fulfilment_terms="expedited_delivery_terms_changed",
        )
        final_request = request
    elif mutation == "product_changed":
        final_item = replace(
            item,
            item_id="OTHER-ASIN",
            name="Different product at checkout",
        )
        final_order = replace(
            order,
            order_id=f"{order.order_id}-other-product",
            order_version=f"{order.order_version}-product",
            items=(final_item,),
        )
        final_request = replace(
            request,
            request_id=f"{request.request_id}-other-product",
            order_ref=final_order.order_id,
        )
    elif mutation == "merchant_changed":
        final_order = replace(
            order,
            order_version=f"{order.order_version}-merchant",
            merchant="webshop-other-merchant",
        )
        final_request = replace(request, merchant=final_order.merchant)
    elif mutation == "payee_changed":
        final_order = replace(
            order,
            order_version=f"{order.order_version}-payee",
            payee="webshop-other-payee",
        )
        final_request = replace(request, payee=final_order.payee)
    elif mutation == "currency_changed":
        final_order = replace(
            order,
            order_version=f"{order.order_version}-currency",
            currency="EUR",
        )
        final_request = replace(request, currency=final_order.currency)
    elif mutation == "category_out_of_scope":
        final_item = replace(item, category="electronics")
        final_order = replace(
            order,
            order_version=f"{order.order_version}-category",
            items=(final_item,),
        )
        final_request = replace(request, category=final_item.category)
    else:
        raise ValueError(f"unknown mutation: {mutation}")

    return replace(
        adaptation,
        order=final_order,
        payment_request=final_request,
    )


def build_anomaly_matrix(spec_path: Path = DEFAULT_SPEC) -> dict[str, Any]:
    spec = _load_json(spec_path)
    source_fixture = ROOT / str(spec["source_fixture"])
    baseline = adapt_webshop_purchase_candidate(_load_json(source_fixture))
    if not baseline.ready or baseline.order is None or baseline.payment_request is None:
        raise RuntimeError("baseline WebShop adaptation is not ready")

    agent_id = "webshop-agent-1"
    baseline_request = replace(baseline.payment_request, agent_id=agent_id)
    mandate = IntentMandate(
        mandate_id=baseline.order.mandate_ref,
        user_id="webshop-user-1",
        max_amount=Decimal("5000.00"),
        allowed_merchants=frozenset(
            {baseline.order.merchant, "webshop-other-merchant"}
        ),
        allowed_categories=frozenset({baseline_request.category}),
        expires_at=baseline_request.occurred_at + timedelta(hours=2),
        max_count=1,
        expected_agent_id=agent_id,
        currency=baseline_request.currency,
        authority_version=baseline.order.authority_version_ref or "",
    )
    confirmation = create_confirmation_record(
        confirmation_id="webshop-snapshot-confirmation-1",
        authority_id=mandate.mandate_id,
        authority_version=mandate.authority_version,
        order=baseline.order,
        confirmed_at=baseline_request.occurred_at - timedelta(minutes=1),
        expires_at=baseline_request.occurred_at + timedelta(minutes=30),
    )
    identity = AgentIdentity(
        agent_id=agent_id,
        provider="offline-webshop-provider",
        executor_instance_id="offline-webshop-executor",
        status="active",
    )

    results: list[dict[str, Any]] = []
    for case in spec["cases"]:
        mutation = str(case["mutation"])
        current = _mutate(baseline, mutation)
        assert current.order is not None and current.payment_request is not None
        bound_request = replace(current.payment_request, agent_id=agent_id)
        execution = PaymentExecutionRecord(
            payment_id=f"webshop-payment-{case['case_id']}",
            request_id=bound_request.request_id,
            order_id=current.order.order_id,
            status=PaymentStatus.PENDING,
            amount=bound_request.amount,
            currency=bound_request.currency,
            occurred_at=bound_request.occurred_at + timedelta(seconds=1),
            authority_ref=mandate.mandate_id,
            agent_ref=agent_id,
            transaction_object_ref=bound_request.request_id,
            payee=current.order.payee,
        )
        context = _context_fact(mandate, current.order, bound_request)
        callback_calls: list[str] = []

        def callback() -> str:
            callback_calls.append("checkout")
            return "simulated-webshop-checkout"

        outcome = gate_webshop_buy_now(
            current,
            mandate,
            agent_id,
            execution,
            identity,
            "offline-webshop-provider",
            "offline-webshop-executor",
            context,
            callback,
            confirmation_record=confirmation,
            authorized_adaptation=baseline,
        )
        differences = (
            [item.code for item in outcome.prepayment_result.order_differences]
            if outcome.prepayment_result is not None
            else []
        )
        expected = str(case["expected_decision"])
        results.append(
            {
                "case_id": str(case["case_id"]),
                "mutation": mutation,
                "baseline_order_ref": baseline.order.order_id,
                "baseline_order_version": baseline.order.order_version,
                "final_order_ref": current.order.order_id,
                "final_order_version": current.order.order_version,
                "expected_decision": expected,
                "actual_decision": outcome.decision.value,
                "matched": outcome.decision.value == expected,
                "checkout_executed": outcome.checkout_executed,
                "callback_count": outcome.callback_count,
                "callback_observations": len(callback_calls),
                "reason_codes": list(outcome.reason_codes),
                "order_difference_codes": differences,
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
    result = build_anomaly_matrix(args.spec)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

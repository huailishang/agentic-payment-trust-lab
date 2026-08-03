from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
import inspect
import json

from agentic_payment_experiment import Decision, gate_webshop_buy_now
from tests.test_webshop_runtime_gate import WebShopRuntimeGateTest, context_fact


def main() -> None:
    case = WebShopRuntimeGateTest(methodName="test_permissive_explicit_mandate_allows_one_injected_callback")
    case.setUp()
    assert case.adaptation.order is not None
    assert case.adaptation.payment_request is not None

    original_authorized = case.adaptation
    original_execution = case.execution
    original_identity = case.identity
    original_context = case.context

    parameter = inspect.signature(gate_webshop_buy_now).parameters["authorized_adaptation"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is None

    results: dict[str, object] = {}

    unchanged, unchanged_calls = case.invoke(authorized_adaptation=case.adaptation)
    assert unchanged.decision is Decision.ALLOW
    assert unchanged.checkout_executed is True
    assert unchanged.callback_count == 1
    assert unchanged_calls == ["checkout"]
    assert unchanged.prepayment_result is not None
    assert unchanged.prepayment_result.order_differences == ()
    results["unchanged"] = {
        "decision": unchanged.decision.value,
        "callback_count": unchanged.callback_count,
        "order_differences": [],
    }

    order = case.adaptation.order
    request = case.adaptation.payment_request
    item = order.items[0]

    confirmation_cases: dict[str, tuple[object, set[str]]] = {}

    up_item = replace(item, unit_amount=item.unit_amount + Decimal("10.00"))
    up_order = replace(order, order_version=f"{order.order_version}-rv-up", items=(up_item,), total_amount=up_item.unit_amount * up_item.quantity)
    confirmation_cases["price_up"] = (
        replace(case.adaptation, order=up_order, payment_request=replace(request, amount=up_order.total_amount)),
        {"order_total_changed", "order_item_unit_amount_changed"},
    )

    down_item = replace(item, unit_amount=item.unit_amount - Decimal("10.00"))
    down_order = replace(order, order_version=f"{order.order_version}-rv-down", items=(down_item,), total_amount=down_item.unit_amount * down_item.quantity)
    confirmation_cases["price_down"] = (
        replace(case.adaptation, order=down_order, payment_request=replace(request, amount=down_order.total_amount)),
        {"order_total_changed", "order_item_unit_amount_changed"},
    )

    option_item = replace(item, name=f"{item.name} [Color: RV-Orange]")
    option_order = replace(order, order_version=f"{order.order_version}-rv-option", items=(option_item,))
    confirmation_cases["option_changed"] = (
        replace(case.adaptation, order=option_order, selected_options=(("Color", "RV-Orange"),)),
        {"order_item_name_changed"},
    )

    quantity_item = replace(item, quantity=item.quantity + 1)
    quantity_order = replace(order, order_version=f"{order.order_version}-rv-quantity", items=(quantity_item,), total_amount=quantity_item.unit_amount * quantity_item.quantity)
    confirmation_cases["quantity_changed"] = (
        replace(case.adaptation, order=quantity_order, payment_request=replace(request, amount=quantity_order.total_amount)),
        {"order_total_changed", "order_item_quantity_changed"},
    )

    content_item = replace(item, name=f"{item.name} RV revised")
    content_order = replace(order, order_version=f"{order.order_version}-rv-content", items=(content_item,))
    confirmation_cases["content_changed"] = (
        replace(case.adaptation, order=content_order),
        {"order_item_name_changed"},
    )

    fulfilment_order = replace(order, order_version=f"{order.order_version}-rv-fulfilment", fulfilment_terms="rv_changed_terms")
    confirmation_cases["fulfilment_changed"] = (
        replace(case.adaptation, order=fulfilment_order),
        {"order_fulfilment_terms_changed"},
    )

    confirmation_results: dict[str, object] = {}
    wide_mandate = replace(case.mandate, max_amount=Decimal("5000.00"))
    for name, (adaptation, expected_codes) in confirmation_cases.items():
        outcome, calls = case.invoke(
            adaptation=adaptation,
            authorized_adaptation=case.adaptation,
            mandate=wide_mandate,
        )
        assert outcome.decision is Decision.CONFIRMATION_REQUIRED, (name, outcome)
        assert outcome.checkout_executed is False
        assert outcome.callback_count == 0
        assert calls == []
        assert outcome.runtime_gate_record is None
        assert outcome.prepayment_result is not None
        actual_codes = {value.code for value in outcome.prepayment_result.order_differences}
        assert actual_codes == expected_codes, (name, actual_codes, expected_codes)
        confirmation_results[name] = {
            "decision": outcome.decision.value,
            "callback_count": outcome.callback_count,
            "order_differences": sorted(actual_codes),
        }
    results["confirmation_cases"] = confirmation_results

    hard_cases: dict[str, tuple[object, Decision, str]] = {}
    product_item = replace(item, item_id="RV-OTHER-ASIN", name="RV other product")
    product_order = replace(order, order_id=f"{order.order_id}-rv-other", order_version=f"{order.order_version}-rv-product", items=(product_item,))
    hard_cases["product_changed"] = (
        replace(case.adaptation, order=product_order, payment_request=replace(request, request_id=f"{request.request_id}-rv-other", order_ref=product_order.order_id)),
        Decision.INDETERMINATE,
        "p1:order_id_mismatch",
    )

    merchant_order = replace(order, order_version=f"{order.order_version}-rv-merchant", merchant="rv-other-merchant")
    hard_cases["merchant_changed"] = (
        replace(case.adaptation, order=merchant_order, payment_request=replace(request, merchant=merchant_order.merchant)),
        Decision.INDETERMINATE,
        "p1:authorized_order_merchant_mismatch",
    )

    payee_order = replace(order, order_version=f"{order.order_version}-rv-payee", payee="rv-other-payee")
    hard_cases["payee_changed"] = (
        replace(case.adaptation, order=payee_order, payment_request=replace(request, payee=payee_order.payee)),
        Decision.INDETERMINATE,
        "p1:order_payee_changed",
    )

    currency_order = replace(order, order_version=f"{order.order_version}-rv-currency", currency="EUR")
    hard_cases["currency_changed"] = (
        replace(case.adaptation, order=currency_order, payment_request=replace(request, currency="EUR")),
        Decision.INDETERMINATE,
        "p1:currency_mismatch",
    )

    category_item = replace(item, category="electronics")
    category_order = replace(order, order_version=f"{order.order_version}-rv-category", items=(category_item,))
    hard_cases["category_out_of_scope"] = (
        replace(case.adaptation, order=category_order, payment_request=replace(request, category="electronics")),
        Decision.DENY,
        "p1:category_out_of_scope",
    )

    hard_results: dict[str, object] = {}
    hard_mandate = replace(
        case.mandate,
        max_amount=Decimal("5000.00"),
        allowed_merchants=frozenset({order.merchant, "rv-other-merchant"}),
    )
    for name, (adaptation, expected_decision, expected_reason) in hard_cases.items():
        outcome, calls = case.invoke(
            adaptation=adaptation,
            authorized_adaptation=case.adaptation,
            mandate=hard_mandate,
        )
        assert outcome.decision is expected_decision, (name, outcome.decision, expected_decision)
        assert outcome.checkout_executed is False
        assert outcome.callback_count == 0
        assert calls == []
        assert outcome.runtime_gate_record is None
        assert expected_reason in outcome.reason_codes, (name, outcome.reason_codes)
        hard_results[name] = {
            "decision": outcome.decision.value,
            "callback_count": outcome.callback_count,
            "reason_codes": list(outcome.reason_codes),
        }
    results["hard_cases"] = hard_results

    incomplete = replace(case.adaptation, order=None)
    incomplete_outcome, incomplete_calls = case.invoke(authorized_adaptation=incomplete)
    assert incomplete_outcome.decision is Decision.INDETERMINATE
    assert incomplete_outcome.callback_count == 0
    assert incomplete_calls == []
    assert incomplete_outcome.prepayment_result is None
    assert "authorized_commerce_adaptation_not_ready" in incomplete_outcome.reason_codes
    results["incomplete_authorized"] = {
        "decision": incomplete_outcome.decision.value,
        "callback_count": incomplete_outcome.callback_count,
        "reason_codes": list(incomplete_outcome.reason_codes),
    }

    p2_execution = replace(case.execution, amount=case.execution.amount + Decimal("1.00"))
    p2_outcome, p2_calls = case.invoke(authorized_adaptation=case.adaptation, execution_candidate=p2_execution)
    assert p2_outcome.decision is Decision.DENY
    assert p2_outcome.callback_count == 0 and p2_calls == []
    assert "p2:payment_execution_amount_mismatch" in p2_outcome.reason_codes

    p3_identity = replace(case.identity, executor_instance_id="rv-other-executor")
    p3_outcome, p3_calls = case.invoke(authorized_adaptation=case.adaptation, agent_identity=p3_identity)
    assert p3_outcome.decision is Decision.DENY
    assert p3_outcome.callback_count == 0 and p3_calls == []
    assert "p3:identity_executor_instance_ref_mismatch" in p3_outcome.reason_codes

    p4_fact = context_fact(case.mandate, case.adaptation.order, case.bound_request, current_action="refund_payment")
    p4_outcome, p4_calls = case.invoke(authorized_adaptation=case.adaptation, context_policy_fact=p4_fact)
    assert p4_outcome.decision is Decision.INDETERMINATE
    assert p4_outcome.callback_count == 0 and p4_calls == []
    assert "p4:current_action_mismatch" in p4_outcome.reason_codes
    results["p1_p4_preserved"] = {
        "p2": p2_outcome.decision.value,
        "p3": p3_outcome.decision.value,
        "p4": p4_outcome.decision.value,
    }

    assert case.adaptation == original_authorized
    assert case.execution == original_execution
    assert case.identity == original_identity
    assert case.context == original_context
    results["inputs_immutable"] = True

    print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

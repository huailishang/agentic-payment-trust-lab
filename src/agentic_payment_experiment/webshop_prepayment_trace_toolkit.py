"""Product-observed authoritative traces for the WebShop prepayment family.

This module consumes only facts already produced by the normal product path. It
never re-runs validation, recalculates order differences, reads evaluator data,
or performs a side effect.
"""

from __future__ import annotations

from .authoritative_trace import (
    ProductAuthoritativeTrace,
    TraceBindingAssertion,
    TraceContractError,
)
from .models import IntentMandate, Order, TransactionRequest, ValidationResult
from .webshop_prepayment_trace_profiles import (
    PREPAYMENT_TRACE_PROFILES,
    PrepaymentScenarioKind,
    PrepaymentTraceProfile,
)
from .webshop_trace_assembler import (
    assemble_product_trace,
    create_event,
    create_relation,
    create_source_binding,
    project_mandate,
    project_order,
    project_request,
    project_validation_result,
    project_webshop_gate_outcome,
)


def _issue_codes(result: ValidationResult) -> tuple[str, ...]:
    return tuple(item.code for item in result.issues)


def _difference_codes(result: ValidationResult) -> tuple[str, ...]:
    return tuple(item.code for item in result.order_differences)


def _same_authority(
    mandate: IntentMandate,
    authorized_order: Order,
    current_order: Order,
    bound_request: TransactionRequest,
) -> bool:
    return (
        authorized_order.mandate_ref == mandate.mandate_id
        and current_order.mandate_ref == mandate.mandate_id
        and authorized_order.authority_version_ref == mandate.authority_version
        and current_order.authority_version_ref == mandate.authority_version
        and bound_request.authority_ref == mandate.mandate_id
        and bound_request.authority_version_ref == mandate.authority_version
        and bound_request.order_ref == current_order.order_id
        and bound_request.amount == current_order.total_amount
        and bound_request.currency == current_order.currency
        and bound_request.merchant == current_order.merchant
        and bound_request.payee == current_order.payee
    )


def _items_by_id(order: Order) -> dict[str, object] | None:
    items: dict[str, object] = {}
    for item in order.items:
        if not item.item_id or item.item_id in items:
            return None
        items[item.item_id] = item
    return items


def _price_direction_matches(
    authorized_order: Order,
    current_order: Order,
    direction: PrepaymentScenarioKind,
) -> bool:
    if direction not in {
        PrepaymentScenarioKind.PRICE_INCREASE,
        PrepaymentScenarioKind.PRICE_DECREASE,
    }:
        return False
    if (
        authorized_order.order_id != current_order.order_id
        or authorized_order.merchant != current_order.merchant
        or authorized_order.payee != current_order.payee
        or authorized_order.currency != current_order.currency
        or authorized_order.mandate_ref != current_order.mandate_ref
        or authorized_order.authority_version_ref
        != current_order.authority_version_ref
    ):
        return False

    authorized_items = _items_by_id(authorized_order)
    current_items = _items_by_id(current_order)
    if authorized_items is None or current_items is None:
        return False
    if not authorized_items or set(authorized_items) != set(current_items):
        return False

    changed_directions: list[int] = []
    for item_id, authorized_item in authorized_items.items():
        current_item = current_items[item_id]
        if (
            authorized_item.name != current_item.name
            or authorized_item.category != current_item.category
            or authorized_item.quantity != current_item.quantity
            or authorized_item.kind != current_item.kind
        ):
            return False
        if authorized_item.unit_amount == current_item.unit_amount:
            continue
        changed_directions.append(
            1 if current_item.unit_amount > authorized_item.unit_amount else -1
        )

    if not changed_directions:
        return False
    expected_direction = (
        1 if direction is PrepaymentScenarioKind.PRICE_INCREASE else -1
    )
    if any(value != expected_direction for value in changed_directions):
        return False
    if direction is PrepaymentScenarioKind.PRICE_INCREASE:
        return current_order.total_amount > authorized_order.total_amount
    return current_order.total_amount < authorized_order.total_amount


def _payee_change_matches(authorized_order: Order, current_order: Order) -> bool:
    return (
        authorized_order.order_id == current_order.order_id
        and authorized_order.merchant == current_order.merchant
        and authorized_order.currency == current_order.currency
        and authorized_order.total_amount == current_order.total_amount
        and authorized_order.mandate_ref == current_order.mandate_ref
        and authorized_order.authority_version_ref
        == current_order.authority_version_ref
        and authorized_order.items == current_order.items
        and authorized_order.fulfilment_terms == current_order.fulfilment_terms
        and authorized_order.payee != current_order.payee
    )


def _profile_matches(
    profile: PrepaymentTraceProfile,
    *,
    authorized_order: Order,
    current_order: Order,
    validation_result: ValidationResult,
) -> bool:
    if validation_result.decision is not profile.expected_decision:
        return False
    if set(_issue_codes(validation_result)) != set(profile.required_issue_codes):
        return False
    if set(_difference_codes(validation_result)) != set(
        profile.required_difference_codes
    ):
        return False
    if profile.scenario_kind is PrepaymentScenarioKind.PAYEE_CHANGE:
        return _payee_change_matches(authorized_order, current_order)
    return _price_direction_matches(
        authorized_order,
        current_order,
        profile.scenario_kind,
    )


def _select_profile(
    *,
    authorized_order: Order,
    current_order: Order,
    validation_result: ValidationResult,
    profiles: tuple[PrepaymentTraceProfile, ...] = PREPAYMENT_TRACE_PROFILES,
) -> PrepaymentTraceProfile | None:
    if type(profiles) is not tuple or any(
        type(profile) is not PrepaymentTraceProfile for profile in profiles
    ):
        return None
    matches = tuple(
        profile
        for profile in profiles
        if _profile_matches(
            profile,
            authorized_order=authorized_order,
            current_order=current_order,
            validation_result=validation_result,
        )
    )
    return matches[0] if len(matches) == 1 else None


def build_prepayment_product_trace(
    *,
    mandate: IntentMandate,
    authorized_order: Order,
    current_order: Order,
    bound_request: TransactionRequest,
    validation_result: ValidationResult,
    base_outcome: object,
) -> ProductAuthoritativeTrace | None:
    """Build one complete family trace when exactly one frozen profile matches."""

    if (
        type(mandate) is not IntentMandate
        or type(authorized_order) is not Order
        or type(current_order) is not Order
        or type(bound_request) is not TransactionRequest
        or type(validation_result) is not ValidationResult
    ):
        return None
    try:
        if not _same_authority(
            mandate,
            authorized_order,
            current_order,
            bound_request,
        ):
            return None
        if (
            getattr(base_outcome, "bound_request", None) != bound_request
            or getattr(base_outcome, "prepayment_result", None)
            != validation_result
            or getattr(base_outcome, "decision", None)
            is not validation_result.decision
            or getattr(base_outcome, "checkout_executed", None) is not False
            or getattr(base_outcome, "callback_count", None) != 0
            or getattr(base_outcome, "authoritative_trace", None) is not None
        ):
            return None
        profile = _select_profile(
            authorized_order=authorized_order,
            current_order=current_order,
            validation_result=validation_result,
        )
        if profile is None:
            return None

        authority_binding = create_source_binding(
            "IntentMandate",
            "intent-mandate-trace/v2",
            project_mandate(mandate),
        )
        authorized_order_binding = create_source_binding(
            "Order",
            "order-snapshot-trace/v2",
            project_order(authorized_order),
        )
        current_order_binding = create_source_binding(
            "Order",
            "order-snapshot-trace/v2",
            project_order(current_order),
        )
        request_binding = create_source_binding(
            "TransactionRequest",
            "transaction-request-trace/v2",
            project_request(bound_request),
        )
        validation_binding = create_source_binding(
            "ValidationResult",
            "validation-result-trace/v2",
            project_validation_result(validation_result),
        )
        outcome_binding = create_source_binding(
            "WebShopBuyNowGateOutcome",
            "webshop-buy-now-gate-outcome-result-trace/v2",
            project_webshop_gate_outcome(base_outcome),
        )

        authority_assertion = TraceBindingAssertion(
            source_path="projection.authority_version_ref",
            target_path="projection.authority_version",
            equal=True,
        )
        authority_ref = f"IntentMandate:{mandate.mandate_id}"
        current_order_ref = f"Order:{current_order.order_id}"
        source_bindings = (
            authority_binding,
            authorized_order_binding,
            current_order_binding,
            request_binding,
            validation_binding,
            outcome_binding,
        )
        events = (
            create_event(
                1,
                "AUTHORITY_RECORDED",
                "IntentMandate",
                "AUTHORITY",
                authority_binding,
                "IntentMandate:{projection.mandate_id}",
            ),
            create_event(
                2,
                "ORDER_RECORDED",
                "Order",
                "AUTHORIZED_ORDER_SNAPSHOT",
                authorized_order_binding,
                "Order:{projection.order_id}",
                relations=(
                    create_relation(
                        "BOUND_TO",
                        "IntentMandate",
                        "AUTHORITY",
                        authority_ref,
                        assertions=(authority_assertion,),
                    ),
                ),
            ),
            create_event(
                3,
                "ORDER_RECORDED",
                "Order",
                "CURRENT_ORDER_SNAPSHOT",
                current_order_binding,
                "Order:{projection.order_id}",
                relations=(
                    create_relation(
                        "BOUND_TO",
                        "IntentMandate",
                        "AUTHORITY",
                        authority_ref,
                        assertions=(authority_assertion,),
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
                        current_order_ref,
                    ),
                    create_relation(
                        "BOUND_TO",
                        "IntentMandate",
                        "AUTHORITY",
                        authority_ref,
                        assertions=(authority_assertion,),
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
                decision=validation_result.decision.value,
                reason_codes=_issue_codes(validation_result),
            ),
            create_event(
                6,
                "RESULT_RECORDED",
                "WebShopBuyNowGateOutcome",
                "FINAL_OUTCOME",
                outcome_binding,
                "WebShopBuyNowGateOutcome:binding:{binding_digest}",
                decision=validation_result.decision.value,
                reason_codes=tuple(getattr(base_outcome, "reason_codes")),
            ),
        )
        return assemble_product_trace(
            profile=profile.profile_name,
            trace_ref=(
                "WebShopPrepaymentTrace:"
                f"{profile.profile_name}:{bound_request.request_id}"
            ),
            events=events,
            source_bindings=source_bindings,
            expected_unique_binding_count=6,
        )
    except (AttributeError, KeyError, TypeError, ValueError, TraceContractError):
        return None


__all__ = ["build_prepayment_product_trace"]

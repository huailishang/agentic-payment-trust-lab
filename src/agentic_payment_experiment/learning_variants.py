from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any

from .models import IntentMandate, Order, OrderItem, TransactionRequest
from .presentation_zh import (
    build_lifecycle_teaching_view,
    build_unified_view,
    enrich_actual_presentation,
    enrich_walkthrough,
    present_differences,
)
from .result_card import build_walkthrough, validation_result_data
from .scenario_loader import Scenario
from .validator import validate_request


def build_s09_learning_variants(
    scenario: Scenario,
    mandate: IntentMandate,
    request: TransactionRequest,
    authorized_order: Order,
    final_order: Order,
    protocol: dict[str, Any],
) -> list[dict[str, Any]]:
    """Precompute clickable S09 examples with the real Python validator."""

    base_item = authorized_order.items[0]
    same_order = replace(authorized_order, order_version="v2")
    replacement = replace(
        base_item,
        item_id="shoe-002",
        name="Trail Walker",
    )
    addon = OrderItem(
        item_id="member-001",
        name="Care membership",
        category=base_item.category,
        quantity=1,
        unit_amount=Decimal("10.00"),
        kind="addon",
    )
    addon_order = replace(
        authorized_order,
        order_version="v2",
        items=authorized_order.items + (addon,),
        total_amount=authorized_order.total_amount + addon.unit_amount,
    )
    expired_order = replace(
        authorized_order,
        order_version="v2",
        quote_expires_at=request.occurred_at - timedelta(seconds=1),
    )

    specs = (
        (
            "unchanged",
            "保持原订单",
            "商户返回与用户确认内容一致的订单，只有订单版本更新。",
            authorized_order,
            same_order,
        ),
        (
            "price_increase",
            "同一商品涨价10元",
            "同一双跑鞋的单价和订单总额都从480元变成490元。",
            authorized_order,
            final_order,
        ),
        (
            "replace_item",
            "更换商品但价格不变",
            "商户把商品编号从 shoe-001 换成 shoe-002，但订单总额仍为480元。",
            authorized_order,
            replace(same_order, items=(replacement,)),
        ),
        (
            "add_addon",
            "新增非产品附加项",
            "商户在跑鞋订单中新增10元会员附加项，品类仍在当前模拟授权范围内。",
            authorized_order,
            addon_order,
        ),
        (
            "payee_change",
            "更换收款方",
            "商品和金额不变，但最终订单的收款方被替换。",
            authorized_order,
            replace(same_order, payee="payee-other"),
        ),
        (
            "quote_expired",
            "报价已经过期",
            "商品和金额不变，但付款请求发生时已经超过报价有效期。",
            authorized_order,
            expired_order,
        ),
        (
            "missing_snapshot",
            "缺少最终订单快照",
            "只有用户确认的订单，没有商户最终订单，系统无法进行可靠比较。",
            authorized_order,
            None,
        ),
    )

    variants: list[dict[str, Any]] = []
    for variant_id, label, story, authorized, final in specs:
        variant_request = replace(
            request,
            amount=final.total_amount if final is not None else authorized.total_amount,
            merchant=final.merchant if final is not None else authorized.merchant,
            currency=final.currency if final is not None else authorized.currency,
        )
        result = validate_request(
            mandate,
            variant_request,
            authorized_order=authorized,
            final_order=final,
        )
        actual = validation_result_data(result)
        enrich_actual_presentation(actual)
        runtime_input = {
            "mandate": _json_ready(asdict(mandate)),
            "request": _json_ready(asdict(variant_request)),
            "seen_request_ids": [],
            "authorized_order": _json_ready(asdict(authorized)),
            "final_order": _json_ready(asdict(final)) if final is not None else None,
        }
        walkthrough = enrich_walkthrough(build_walkthrough(scenario, runtime_input, actual, protocol))
        unified_view = build_unified_view(
            input_data=runtime_input,
            actual=actual,
            status_presentation={
                "label_zh": "预设案例由后端计算",
                "explanation_zh": "该变体由 Python 验证器预先计算，浏览器只负责切换展示。",
            },
        )
        lifecycle_teaching_view = build_lifecycle_teaching_view(
            {
                "sample_id": scenario.sample_id,
                "input": runtime_input,
                "actual": actual,
                "protocol": protocol,
                "lifecycle": None,
                "walkthrough": walkthrough,
            }
        )
        variants.append(
            {
                "variant_id": variant_id,
                "label_zh": label,
                "story_zh": story,
                "input": runtime_input,
                "actual": actual,
                "differences": present_differences(actual["order_differences"]),
                "walkthrough": walkthrough,
                "unified_view": unified_view,
                "lifecycle_teaching_view": lifecycle_teaching_view,
                "computed_by": "agentic_payment_experiment.validate_request",
            }
        )
    return variants


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        values = [_json_ready(item) for item in value]
        return sorted(values) if isinstance(value, (set, frozenset)) else values
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value

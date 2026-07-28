from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Any

from .lifecycle import assess_lifecycle
from .models import PaymentStatus
from .payment_recovery import assess_payment_recovery
from .presentation_zh import (
    attach_scenario_presentation,
    decision_presentation,
    reason_presentation,
)
from .remediation import assess_remediation
from .result_card import scenario_result_record
from .scenario_loader import Scenario, load_scenarios
from .validator import validate_request


# M1 deliberately exposes only a few business-significant controls per scenario.
# Internal evidence/protocol fields remain available in developer details, not here.
_FIELD_SPECS: dict[str, tuple[dict[str, Any], ...]] = {
    "S01": (
        {"key": "request.amount", "label_zh": "实际支付金额", "type": "decimal"},
        {"key": "request.merchant", "label_zh": "实际商户", "type": "text"},
    ),
    "S02": (
        {"key": "request.amount", "label_zh": "实际支付金额", "type": "decimal"},
        {"key": "mandate.max_amount", "label_zh": "用户授权上限", "type": "decimal"},
    ),
    "S03": (
        {"key": "request.category", "label_zh": "实际商品品类", "type": "text"},
    ),
    "S04": (
        {"key": "request.occurred_at", "label_zh": "请求发生时间", "type": "datetime"},
        {"key": "mandate.expires_at", "label_zh": "委托到期时间", "type": "datetime"},
    ),
    "S05": (
        {
            "key": "request_seen",
            "label_zh": "该 request_id 是否已处理过",
            "type": "boolean",
        },
    ),
    "S06": (
        {"key": "request.merchant", "label_zh": "实际商户", "type": "text"},
    ),
    "S07": (
        {"key": "request.sequence_count", "label_zh": "本次执行序号", "type": "integer"},
        {"key": "mandate.max_count", "label_zh": "授权最多执行次数", "type": "integer"},
    ),
    "S08": (
        {"key": "request.amount", "label_zh": "实际支付金额", "type": "decimal"},
        {
            "key": "mandate.confirmation_above",
            "label_zh": "超过该金额需要人工确认",
            "type": "nullable_decimal",
        },
        {"key": "mandate.max_amount", "label_zh": "绝对支付上限", "type": "decimal"},
    ),
    "S09": (
        {
            "key": "authorized_order.total_amount",
            "label_zh": "用户确认时订单金额",
            "type": "decimal",
        },
        {
            "key": "final_order_and_request.total_amount",
            "label_zh": "最终订单/支付金额",
            "type": "decimal",
            "help_zh": "为保持可比较性，同时修改最终订单金额和支付请求金额。",
        },
    ),
    "S10": (
        {
            "key": "payment_execution.status",
            "label_zh": "支付状态",
            "type": "choice",
            "choices": ["SUCCEEDED", "FAILED", "PENDING", "UNKNOWN"],
        },
        {
            "key": "fulfillment.status",
            "label_zh": "履约状态",
            "type": "choice",
            "choices": ["SUCCEEDED", "FAILED", "PENDING", "UNKNOWN"],
        },
    ),
    "S11": (
        {
            "key": "fulfillment.status",
            "label_zh": "履约状态",
            "type": "choice",
            "choices": ["SUCCEEDED", "FAILED", "PENDING", "UNKNOWN"],
        },
        {
            "key": "refund.status",
            "label_zh": "退款状态",
            "type": "choice",
            "choices": ["SUCCEEDED", "FAILED", "PENDING", "UNKNOWN"],
        },
        {"key": "refund.amount", "label_zh": "退款金额", "type": "decimal"},
    ),
    "S12": (
        {
            "key": "payment_status_observation.status",
            "label_zh": "查询到的原交易状态",
            "type": "choice",
            "choices": ["SUCCEEDED", "FAILED", "PENDING", "UNKNOWN"],
        },
        {
            "key": "payment_recovery_initial.idempotency_key",
            "label_zh": "原交易幂等键",
            "type": "nullable_text",
        },
        {
            "key": "parallel_attempt_status",
            "label_zh": "同请求是否已有其他支付尝试",
            "type": "choice",
            "choices": ["NONE", "SUCCEEDED", "PENDING", "UNKNOWN", "FAILED"],
            "choice_labels_zh": {
                "NONE": "没有",
                "SUCCEEDED": "已有成功尝试",
                "PENDING": "已有处理中尝试",
                "UNKNOWN": "已有状态未知尝试",
                "FAILED": "已有失败尝试",
            },
        },
    ),
    "S13": (
        {"key": "mandate.expected_agent_id", "label_zh": "用户授权 Agent", "type": "text"},
        {"key": "request.agent_id", "label_zh": "实际执行 Agent", "type": "text"},
    ),
}


def build_interactive_catalog(*, scenarios_dir: Path | None = None) -> dict[str, Any]:
    directory = scenarios_dir or _default_scenarios_dir()
    items: dict[str, Any] = {}
    for scenario in load_scenarios(directory):
        specs = _FIELD_SPECS.get(scenario.sample_id, ())
        if not specs:
            continue
        items[scenario.sample_id] = {
            "sample_id": scenario.sample_id,
            "title": scenario.title,
            "question": scenario.question,
            "fields": [
                {
                    **spec,
                    "value": _field_value(scenario, str(spec["key"])),
                }
                for spec in specs
            ],
        }
    return {
        "enabled": True,
        "requires_local_server": True,
        "scenarios": items,
        "notice_zh": "只修改少量关键业务条件；协议字段、证据和原始 JSON 仍放在开发者信息中。",
    }


def evaluate_interactive_scenario(
    sample_id: str,
    overrides: dict[str, Any],
    *,
    scenarios_dir: Path | None = None,
) -> dict[str, Any]:
    """Re-evaluate one fixed scenario with a small allow-listed set of edits.

    This is local/offline experimentation only. It never executes a payment.
    """

    directory = scenarios_dir or _default_scenarios_dir()
    scenario = _find_scenario(sample_id, directory)
    allowed = {str(item["key"]): item for item in _FIELD_SPECS.get(sample_id, ())}
    unknown = sorted(set(overrides) - set(allowed))
    if unknown:
        raise ValueError(f"unsupported interactive fields: {', '.join(unknown)}")

    updated = scenario
    for key, raw_value in overrides.items():
        updated = _apply_override(updated, key, raw_value, allowed[key])

    validation = validate_request(
        updated.mandate,
        updated.request,
        seen_request_ids=updated.seen_request_ids,
        authorized_order=updated.authorized_order,
        final_order=updated.final_order,
    )

    lifecycle_result = None
    if updated.payment_execution is not None and updated.fulfillment is not None:
        if updated.final_order is None:
            raise ValueError("lifecycle experiment requires final_order")
        lifecycle_result = assess_lifecycle(
            updated.request,
            updated.final_order,
            updated.payment_execution,
            updated.fulfillment,
        )
        if updated.refund is not None or updated.dispute is not None:
            lifecycle_result = assess_remediation(
                updated.final_order,
                updated.payment_execution,
                lifecycle_result,
                refund=updated.refund,
                dispute=updated.dispute,
            )

    recovery_result = None
    if (
        updated.payment_recovery_initial is not None
        and updated.payment_status_observation is not None
    ):
        recovery_result = assess_payment_recovery(
            updated.payment_recovery_initial,
            updated.payment_status_observation,
            known_attempts=updated.known_payment_attempts,
        )

    runtime_input = _runtime_input_for_scenario(updated)
    presentation_record = scenario_result_record(
        updated,
        validation,
        runtime_input=runtime_input,
        lifecycle_result=lifecycle_result,
        payment_recovery_result=recovery_result,
    )
    attach_scenario_presentation(presentation_record)

    decision = decision_presentation(validation.decision.value)
    result: dict[str, Any] = {
        "sample_id": updated.sample_id,
        "title": updated.title,
        "decision": decision,
        "reason_codes": [item.code for item in validation.issues],
        "reasons": [reason_presentation(item.code) for item in validation.issues],
        "rule_version": validation.rule_version,
        "simulation_only": True,
        "presentation": {
            "actual": presentation_record["actual"],
            "input": presentation_record["input"],
            "differences": presentation_record["differences"],
            "lifecycle": presentation_record.get("lifecycle"),
            "payment_recovery": presentation_record.get("payment_recovery"),
            "unified_view": presentation_record["unified_view"],
            "lifecycle_teaching_view": presentation_record["lifecycle_teaching_view"],
        },
    }

    if lifecycle_result is not None:
        result["lifecycle"] = {
            "payment_status": lifecycle_result.payment_status.value,
            "fulfillment_status": lifecycle_result.fulfillment_status.value,
            "remediation_status": lifecycle_result.remediation.status.value,
            "task_status": lifecycle_result.task_status.value,
            "refund_status": (
                lifecycle_result.refund_status.value
                if lifecycle_result.refund_status is not None
                else None
            ),
            "dispute_status": (
                lifecycle_result.dispute_status.value
                if lifecycle_result.dispute_status is not None
                else None
            ),
            "reason_codes": [item.code for item in lifecycle_result.issues],
            "reasons": [reason_presentation(item.code) for item in lifecycle_result.issues],
        }

    if recovery_result is not None:
        result["payment_recovery"] = {
            "initial_status": recovery_result.initial_status.value,
            "observed_status": recovery_result.observed_status.value,
            "effective_status": recovery_result.effective_status.value,
            "recovery_status": recovery_result.recovery_status.value,
            "retry_allowed": recovery_result.retry_allowed,
            "next_action": recovery_result.next_action,
            "reason_codes": [item.code for item in recovery_result.issues],
            "reasons": [reason_presentation(item.code) for item in recovery_result.issues],
        }

    return result


def _runtime_input_for_scenario(scenario: Scenario) -> dict[str, Any]:
    data: dict[str, Any] = {
        "mandate": _json_ready(asdict(scenario.mandate)),
        "request": _json_ready(asdict(scenario.request)),
        "seen_request_ids": sorted(scenario.seen_request_ids),
    }
    if scenario.authorized_order is not None:
        data["authorized_order"] = _json_ready(asdict(scenario.authorized_order))
    if scenario.final_order is not None:
        data["final_order"] = _json_ready(asdict(scenario.final_order))
    if scenario.payment_execution is not None:
        data["payment_execution"] = _json_ready(asdict(scenario.payment_execution))
    if scenario.fulfillment is not None:
        data["fulfillment"] = _json_ready(asdict(scenario.fulfillment))
    if scenario.refund is not None:
        data["refund"] = _json_ready(asdict(scenario.refund))
    if scenario.dispute is not None:
        data["dispute"] = _json_ready(asdict(scenario.dispute))
    if scenario.payment_recovery_initial is not None:
        data["payment_execution"] = _json_ready(asdict(scenario.payment_recovery_initial))
    if scenario.payment_status_observation is not None:
        data["payment_status_observation"] = _json_ready(
            asdict(scenario.payment_status_observation)
        )
    if scenario.known_payment_attempts:
        data["known_payment_attempts"] = [
            _json_ready(asdict(item)) for item in scenario.known_payment_attempts
        ]
    return data


def _default_scenarios_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "samples" / "scenarios"


def _find_scenario(sample_id: str, directory: Path) -> Scenario:
    for scenario in load_scenarios(directory):
        if scenario.sample_id == sample_id:
            return scenario
    raise ValueError(f"unknown scenario: {sample_id}")


def _field_value(scenario: Scenario, key: str) -> Any:
    if key == "request_seen":
        return scenario.request.request_id in scenario.seen_request_ids
    if key == "final_order_and_request.total_amount":
        return _display_value(scenario.final_order.total_amount if scenario.final_order else None)
    if key == "parallel_attempt_status":
        if not scenario.known_payment_attempts:
            return "NONE"
        return scenario.known_payment_attempts[0].status.value

    object_name, attr = key.split(".", 1)
    obj = getattr(scenario, object_name)
    if obj is None:
        return None
    return _display_value(getattr(obj, attr))


def _apply_override(
    scenario: Scenario,
    key: str,
    raw_value: Any,
    spec: dict[str, Any],
) -> Scenario:
    value_type = str(spec["type"])
    value = _coerce_value(raw_value, value_type, spec)

    if key == "request_seen":
        seen = set(scenario.seen_request_ids)
        if value:
            seen.add(scenario.request.request_id)
        else:
            seen.discard(scenario.request.request_id)
        return replace(scenario, seen_request_ids=frozenset(seen))

    if key == "authorized_order.total_amount":
        if scenario.authorized_order is None:
            raise ValueError("scenario has no authorized_order")
        return replace(
            scenario,
            authorized_order=_replace_simple_order_total(scenario.authorized_order, value),
        )

    if key == "final_order_and_request.total_amount":
        if scenario.final_order is None:
            raise ValueError("scenario has no final_order")
        return replace(
            scenario,
            request=replace(scenario.request, amount=value),
            final_order=_replace_simple_order_total(scenario.final_order, value),
        )

    if key == "parallel_attempt_status":
        if value == "NONE":
            return replace(scenario, known_payment_attempts=())
        initial = scenario.payment_recovery_initial
        if initial is None:
            raise ValueError("scenario has no payment recovery initial record")
        attempt = replace(
            initial,
            payment_id=f"{initial.payment_id}-parallel",
            status=PaymentStatus(value),
            occurred_at=initial.occurred_at + timedelta(seconds=30),
        )
        return replace(scenario, known_payment_attempts=(attempt,))

    object_name, attr = key.split(".", 1)
    obj = getattr(scenario, object_name)
    if obj is None:
        raise ValueError(f"scenario has no {object_name}")
    return replace(scenario, **{object_name: replace(obj, **{attr: value})})


def _replace_simple_order_total(order: Any, value: Decimal) -> Any:
    """Keep the one-line teaching order internally consistent when editing its total."""

    items = order.items
    if len(items) == 1 and items[0].quantity == 1:
        items = (replace(items[0], unit_amount=value),)
    return replace(order, total_amount=value, items=items)


def _coerce_value(raw_value: Any, value_type: str, spec: dict[str, Any]) -> Any:
    if value_type == "text":
        return str(raw_value)
    if value_type == "nullable_text":
        text = str(raw_value).strip() if raw_value is not None else ""
        return text or None
    if value_type in {"decimal", "nullable_decimal"}:
        text = str(raw_value).strip() if raw_value is not None else ""
        if value_type == "nullable_decimal" and not text:
            return None
        try:
            return Decimal(text)
        except InvalidOperation as exc:
            raise ValueError(f"invalid decimal value: {raw_value}") from exc
    if value_type == "integer":
        try:
            return int(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid integer value: {raw_value}") from exc
    if value_type == "datetime":
        try:
            value = datetime.fromisoformat(str(raw_value))
        except ValueError as exc:
            raise ValueError(f"invalid ISO datetime value: {raw_value}") from exc
        if value.tzinfo is None:
            raise ValueError("interactive datetime values must include a timezone")
        return value
    if value_type == "boolean":
        if isinstance(raw_value, bool):
            return raw_value
        text = str(raw_value).strip().lower()
        if text in {"true", "1", "yes", "on"}:
            return True
        if text in {"false", "0", "no", "off"}:
            return False
        raise ValueError(f"invalid boolean value: {raw_value}")
    if value_type == "choice":
        text = str(raw_value)
        choices = {str(item) for item in spec.get("choices", [])}
        if text not in choices:
            raise ValueError(f"invalid choice {text}; expected one of {', '.join(sorted(choices))}")
        if spec["key"] in {
            "payment_execution.status",
            "fulfillment.status",
            "refund.status",
            "payment_status_observation.status",
        }:
            # Enum conversion is deferred to the target object's concrete enum type below.
            object_name, attr = str(spec["key"]).split(".", 1)
            del attr
            # The actual enum class is recovered by callers through the existing object value.
            # Returning text here would break dataclass type expectations, so special cases are
            # converted in _coerce_choice_enum before replace.
            return _coerce_choice_enum(object_name, text)
        return text
    raise ValueError(f"unsupported interactive field type: {value_type}")


def _coerce_choice_enum(object_name: str, value: str) -> Enum:
    if object_name in {"payment_execution", "payment_status_observation"}:
        return PaymentStatus(value)
    if object_name == "fulfillment":
        from .models import FulfillmentStatus

        return FulfillmentStatus(value)
    if object_name == "refund":
        from .models import RefundStatus

        return RefundStatus(value)
    raise ValueError(f"unsupported enum target: {object_name}")


def _display_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "__dataclass_fields__"):
        return _json_ready(asdict(value))
    return str(value)


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_ready(item) for item in value]
    return _display_value(value)

"""UI-neutral WebShop journey read model with explicit evidence-source boundaries.

This module only projects already-accepted offline inputs. It does not run the
WebShop adapter, payment logic, trace validation, UI rendering, or any external
runtime. Required cross-source correlations fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
import hashlib
import json
from typing import Any, Mapping

from .adapters.webshop import WebShopCommerceAdaptation
from .authoritative_trace_consumer import (
    AuthoritativeTraceReadModel,
    trace_read_model_to_primitive,
)


JOURNEY_SCHEMA_VERSION = "webshop-journey-read-model/v1"
EXPECTED_EXPERIMENT_CONTEXT_ORIGIN = "explicit_experiment_context_not_webshop_verified"
SOURCE_CLASSIFICATION_STATUS = "VERIFIED_SEPARATE_SOURCES"
JOURNEY_LIMITATIONS = (
    "fixed_script_webshop_smoke_not_autonomous_agent",
    "experiment_context_not_webshop_verified",
    "payment_authoritative_trace_is_separate_evidence_namespace",
    "ui_neutral_read_model_only",
    "no_webshop_or_payment_execution",
)


class WebShopJourneyReadModelError(ValueError):
    """Raised when a source boundary or required correlation is invalid."""


@dataclass(frozen=True)
class JourneyCorrelation:
    correlation_id: str
    source_path: str
    target_path: str
    source_value: Any
    target_value: Any
    equal: bool


@dataclass(frozen=True)
class WebShopJourneyReadModel:
    schema_version: str
    journey_ref: str
    source_classification_status: str
    correlations: tuple[JourneyCorrelation, ...]
    webshop_runtime: Mapping[str, Any]
    experiment_context: Mapping[str, Any]
    commerce_adaptation: Mapping[str, Any]
    payment_authoritative_trace: Mapping[str, Any]
    limitations: tuple[str, ...]


def _primitive(value: Any) -> Any:
    if is_dataclass(value):
        return {
            field.name: _primitive(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Mapping):
        return {str(key): _primitive(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_primitive(item) for item in value]
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return _primitive(value.value)
    if value is None or isinstance(value, (bool, int, str)):
        return value
    raise WebShopJourneyReadModelError(
        f"unsupported primitive value type: {type(value).__name__}"
    )


def _required_mapping(value: object, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise WebShopJourneyReadModelError(f"{path} must be a mapping")
    return value


def _required_text(value: object, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise WebShopJourneyReadModelError(f"{path} must be a non-empty string")
    return value


def _project_webshop_runtime(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    required = (
        "session_id",
        "task_identifier",
        "instruction_text",
        "actions_executed",
        "buy_now_available",
        "buy_now_executed",
        "product",
        "source",
    )
    missing = [key for key in required if key not in snapshot]
    if missing:
        raise WebShopJourneyReadModelError(
            "webshop_runtime missing required fields: " + ",".join(missing)
        )
    _required_text(snapshot["session_id"], "session_id")
    _required_text(snapshot["task_identifier"], "task_identifier")
    _required_text(snapshot["instruction_text"], "instruction_text")
    actions = snapshot["actions_executed"]
    if not isinstance(actions, (tuple, list)) or not all(
        isinstance(item, str) and item for item in actions
    ):
        raise WebShopJourneyReadModelError("actions_executed must be a string list")
    if not isinstance(snapshot["buy_now_available"], bool):
        raise WebShopJourneyReadModelError("buy_now_available must be bool")
    if not isinstance(snapshot["buy_now_executed"], bool):
        raise WebShopJourneyReadModelError("buy_now_executed must be bool")
    _required_mapping(snapshot["product"], "product")
    _required_mapping(snapshot["source"], "source")
    return {key: _primitive(snapshot[key]) for key in required}


def _project_experiment_context(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    context = _required_mapping(snapshot.get("experiment_context"), "experiment_context")
    origin = _required_text(context.get("origin"), "experiment_context.origin")
    if origin != EXPECTED_EXPERIMENT_CONTEXT_ORIGIN:
        raise WebShopJourneyReadModelError(
            "experiment_context.origin cannot be promoted or reclassified"
        )
    projected = _primitive(context)
    assert isinstance(projected, dict)
    return projected


def _project_commerce_adaptation(
    adaptation: WebShopCommerceAdaptation,
) -> dict[str, Any]:
    if type(adaptation) is not WebShopCommerceAdaptation:
        raise WebShopJourneyReadModelError(
            "commerce adaptation must be WebShopCommerceAdaptation"
        )
    if not adaptation.ready or adaptation.order is None or adaptation.payment_request is None:
        raise WebShopJourneyReadModelError("commerce adaptation must be ready")
    projected = {
        field.name: _primitive(getattr(adaptation, field.name))
        for field in fields(adaptation)
    }
    projected["ready"] = adaptation.ready
    return projected


def _trace_projection(
    trace: Mapping[str, Any], source_object_type: str
) -> Mapping[str, Any]:
    bindings = trace.get("source_bindings")
    if not isinstance(bindings, list):
        raise WebShopJourneyReadModelError(
            "payment_authoritative_trace.source_bindings must be a list"
        )
    matches = [
        binding
        for binding in bindings
        if isinstance(binding, Mapping)
        and binding.get("source_object_type") == source_object_type
    ]
    if len(matches) != 1:
        raise WebShopJourneyReadModelError(
            f"payment trace requires exactly one {source_object_type} binding"
        )
    projection = matches[0].get("projection")
    if not isinstance(projection, Mapping):
        raise WebShopJourneyReadModelError(
            f"{source_object_type} binding projection must be a mapping"
        )
    return projection


def _correlation(
    correlation_id: str,
    source_path: str,
    source_value: Any,
    target_path: str,
    target_value: Any,
) -> JourneyCorrelation:
    source_primitive = _primitive(source_value)
    target_primitive = _primitive(target_value)
    return JourneyCorrelation(
        correlation_id=correlation_id,
        source_path=source_path,
        target_path=target_path,
        source_value=source_primitive,
        target_value=target_primitive,
        equal=source_primitive == target_primitive,
    )


def _build_correlations(
    runtime: Mapping[str, Any],
    context: Mapping[str, Any],
    adaptation: Mapping[str, Any],
    trace: Mapping[str, Any],
) -> tuple[JourneyCorrelation, ...]:
    product = _required_mapping(runtime.get("product"), "webshop_runtime.product")
    source = _required_mapping(runtime.get("source"), "webshop_runtime.source")
    source_assets = _required_mapping(
        source.get("asset_hashes"), "webshop_runtime.source.asset_hashes"
    )
    order = _required_mapping(adaptation.get("order"), "commerce_adaptation.order")
    request = _required_mapping(
        adaptation.get("payment_request"), "commerce_adaptation.payment_request"
    )
    items = order.get("items")
    if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], Mapping):
        raise WebShopJourneyReadModelError(
            "commerce_adaptation.order.items must contain exactly one item"
        )
    item = items[0]
    trace_order = _trace_projection(trace, "Order")
    trace_request = _trace_projection(trace, "TransactionRequest")
    trace_ref = _required_text(
        trace.get("trace_ref"), "payment_authoritative_trace.trace_ref"
    )
    request_id = _required_text(
        request.get("request_id"), "commerce_adaptation.payment_request.request_id"
    )
    order_id = _required_text(
        order.get("order_id"), "commerce_adaptation.order.order_id"
    )

    selected_options = product.get("selected_options")
    if not isinstance(selected_options, Mapping):
        raise WebShopJourneyReadModelError(
            "webshop_runtime.product.selected_options must be a mapping"
        )
    adaptation_options = adaptation.get("selected_options")
    if not isinstance(adaptation_options, list):
        raise WebShopJourneyReadModelError(
            "commerce_adaptation.selected_options must be a list"
        )
    normalized_options = [
        [str(key), _primitive(value)]
        for key, value in sorted(selected_options.items(), key=lambda pair: str(pair[0]))
    ]
    adaptation_asset_hashes = adaptation.get("source_asset_hashes")
    if not isinstance(adaptation_asset_hashes, list):
        raise WebShopJourneyReadModelError(
            "commerce_adaptation.source_asset_hashes must be a list"
        )
    normalized_assets = [
        [str(key), _primitive(value)]
        for key, value in sorted(source_assets.items(), key=lambda pair: str(pair[0]))
    ]

    correlations = (
        _correlation(
            "session_task_identifier",
            "webshop_runtime.task_identifier",
            runtime.get("task_identifier"),
            "webshop_runtime.session_id",
            f"webshop-session-{runtime.get('session_id')}",
        ),
        _correlation(
            "instruction_to_user_intent",
            "webshop_runtime.instruction_text",
            runtime.get("instruction_text"),
            "commerce_adaptation.user_intent_text",
            adaptation.get("user_intent_text"),
        ),
        _correlation(
            "product_asin_to_order_item",
            "webshop_runtime.product.asin",
            product.get("asin"),
            "commerce_adaptation.order.items[0].item_id",
            item.get("item_id"),
        ),
        _correlation(
            "product_name_to_order_item",
            "webshop_runtime.product.title",
            product.get("title"),
            "commerce_adaptation.order.items[0].name",
            item.get("name"),
        ),
        _correlation(
            "product_unit_amount_to_order_item",
            "webshop_runtime.product.unit_price",
            product.get("unit_price"),
            "commerce_adaptation.order.items[0].unit_amount",
            item.get("unit_amount"),
        ),
        _correlation(
            "product_quantity_to_order_item",
            "webshop_runtime.product.quantity",
            product.get("quantity"),
            "commerce_adaptation.order.items[0].quantity",
            item.get("quantity"),
        ),
        _correlation(
            "product_total_to_order",
            "webshop_runtime.product.order_total",
            product.get("order_total"),
            "commerce_adaptation.order.total_amount",
            order.get("total_amount"),
        ),
        _correlation(
            "selected_options_to_adaptation",
            "webshop_runtime.product.selected_options",
            normalized_options,
            "commerce_adaptation.selected_options",
            adaptation_options,
        ),
        _correlation(
            "experiment_origin_to_adaptation",
            "experiment_context.origin",
            context.get("origin"),
            "commerce_adaptation.experiment_context_origin",
            adaptation.get("experiment_context_origin"),
        ),
        _correlation(
            "source_commit_to_adaptation",
            "webshop_runtime.source.webshop_commit",
            source.get("webshop_commit"),
            "commerce_adaptation.source_commit",
            adaptation.get("source_commit"),
        ),
        _correlation(
            "source_smoke_sha_to_adaptation",
            "webshop_runtime.source.smoke_result_sha256",
            source.get("smoke_result_sha256"),
            "commerce_adaptation.source_smoke_sha256",
            adaptation.get("source_smoke_sha256"),
        ),
        _correlation(
            "source_asset_hashes_to_adaptation",
            "webshop_runtime.source.asset_hashes",
            normalized_assets,
            "commerce_adaptation.source_asset_hashes",
            adaptation_asset_hashes,
        ),
        _correlation(
            "adaptation_order_request_binding",
            "commerce_adaptation.payment_request.order_ref",
            request.get("order_ref"),
            "commerce_adaptation.order.order_id",
            order_id,
        ),
        _correlation(
            "order_id_to_payment_trace",
            "commerce_adaptation.order.order_id",
            order_id,
            "payment_authoritative_trace.Order.projection.order_id",
            trace_order.get("order_id"),
        ),
        _correlation(
            "request_id_to_payment_trace",
            "commerce_adaptation.payment_request.request_id",
            request_id,
            "payment_authoritative_trace.TransactionRequest.projection.request_id",
            trace_request.get("request_id"),
        ),
        _correlation(
            "trace_request_order_binding",
            "payment_authoritative_trace.TransactionRequest.projection.order_ref",
            trace_request.get("order_ref"),
            "commerce_adaptation.order.order_id",
            order_id,
        ),
        _correlation(
            "trace_ref_to_request_id",
            "payment_authoritative_trace.trace_ref.request_suffix",
            trace_ref.rsplit(":", 1)[-1],
            "commerce_adaptation.payment_request.request_id",
            request_id,
        ),
    )
    failed = [item.correlation_id for item in correlations if not item.equal]
    if failed:
        raise WebShopJourneyReadModelError(
            "required journey correlation mismatch: " + ",".join(failed)
        )
    return correlations


def build_webshop_journey_read_model(
    snapshot: object,
    adaptation: object,
    read_model: object,
) -> WebShopJourneyReadModel:
    """Build a source-classified journey from accepted offline inputs only."""

    if not isinstance(snapshot, Mapping):
        raise WebShopJourneyReadModelError("snapshot must be a mapping")
    if type(adaptation) is not WebShopCommerceAdaptation:
        raise WebShopJourneyReadModelError(
            "adaptation must be WebShopCommerceAdaptation"
        )
    if type(read_model) is not AuthoritativeTraceReadModel:
        raise WebShopJourneyReadModelError(
            "read_model must be AuthoritativeTraceReadModel"
        )

    runtime = _project_webshop_runtime(snapshot)
    context = _project_experiment_context(snapshot)
    commerce = _project_commerce_adaptation(adaptation)
    payment = trace_read_model_to_primitive(read_model)
    correlations = _build_correlations(runtime, context, commerce, payment)

    request = _required_mapping(
        commerce.get("payment_request"), "commerce_adaptation.payment_request"
    )
    journey_seed = "|".join(
        (
            _required_text(runtime.get("session_id"), "webshop_runtime.session_id"),
            _required_text(
                request.get("request_id"),
                "commerce_adaptation.payment_request.request_id",
            ),
            _required_text(
                payment.get("trace_ref"), "payment_authoritative_trace.trace_ref"
            ),
        )
    ).encode("utf-8")
    journey_ref = (
        "WebShopJourneyReadModel:sha256:" + hashlib.sha256(journey_seed).hexdigest()
    )

    return WebShopJourneyReadModel(
        schema_version=JOURNEY_SCHEMA_VERSION,
        journey_ref=journey_ref,
        source_classification_status=SOURCE_CLASSIFICATION_STATUS,
        correlations=correlations,
        webshop_runtime=runtime,
        experiment_context=context,
        commerce_adaptation=commerce,
        payment_authoritative_trace=payment,
        limitations=JOURNEY_LIMITATIONS,
    )


def webshop_journey_read_model_to_primitive(
    read_model: WebShopJourneyReadModel,
) -> dict[str, Any]:
    if type(read_model) is not WebShopJourneyReadModel:
        raise WebShopJourneyReadModelError(
            "read_model must be WebShopJourneyReadModel"
        )
    primitive = _primitive(read_model)
    if not isinstance(primitive, dict):
        raise WebShopJourneyReadModelError("journey primitive must be an object")
    return primitive


def webshop_journey_read_model_json_bytes(
    read_model: WebShopJourneyReadModel,
) -> bytes:
    return json.dumps(
        webshop_journey_read_model_to_primitive(read_model),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def webshop_journey_read_model_sha256(
    read_model: WebShopJourneyReadModel,
) -> str:
    return hashlib.sha256(webshop_journey_read_model_json_bytes(read_model)).hexdigest()


__all__ = [
    "EXPECTED_EXPERIMENT_CONTEXT_ORIGIN",
    "JourneyCorrelation",
    "WebShopJourneyReadModel",
    "WebShopJourneyReadModelError",
    "build_webshop_journey_read_model",
    "webshop_journey_read_model_json_bytes",
    "webshop_journey_read_model_sha256",
    "webshop_journey_read_model_to_primitive",
]

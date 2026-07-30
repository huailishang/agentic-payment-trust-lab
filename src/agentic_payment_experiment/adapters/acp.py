from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping

from ..models import Order, OrderItem

ACP_VERSION = "2026-04-17-snapshot"


@dataclass(frozen=True)
class ACPOrderAdaptation:
    """Result of converting two fixed ACP checkout snapshots into neutral orders.

    The adapter is deliberately narrow: it accepts already-decoded offline JSON
    snapshots and maps only fields needed by the local S09 order-comparison
    experiment. It does not call an ACP endpoint, verify webhook signatures,
    process payment handlers, or claim ACP conformance.
    """

    authorized_order: Order | None
    final_order: Order | None
    protocol_version: str
    missing_fields: tuple[str, ...]
    unmapped_fields: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return (
            self.authorized_order is not None
            and self.final_order is not None
            and not self.missing_fields
        )


def adapt_acp_checkout_pair(snapshot: Mapping[str, Any]) -> ACPOrderAdaptation:
    """Map a fixed ACP 2026-04-17-style checkout pair into two neutral orders.

    The top-level wrapper is local to this experiment. Each checkout object uses
    ACP-style checkout fields (id, currency, line_items and totals). Fields that
    ACP does not provide directly in this offline payload are supplied through an
    explicit experiment_context bridge instead of being invented by the adapter.
    """

    authorized = _mapping(snapshot.get("authorized_checkout"))
    final = _mapping(snapshot.get("final_checkout"))
    context = _mapping(snapshot.get("experiment_context"))
    missing: list[str] = []

    if not authorized:
        missing.append("authorized_checkout")
    if not final:
        missing.append("final_checkout")
    if not context:
        missing.append("experiment_context")
    if missing:
        return ACPOrderAdaptation(
            None,
            None,
            str(snapshot.get("protocol_version") or ACP_VERSION),
            tuple(missing),
            _semantic_gaps(snapshot),
        )

    authorized_order = _build_order(
        authorized,
        context,
        snapshot_name="authorized_checkout",
        version_key="authorized_order_version",
        missing=missing,
    )
    final_order = _build_order(
        final,
        context,
        snapshot_name="final_checkout",
        version_key="final_order_version",
        missing=missing,
    )

    if missing:
        return ACPOrderAdaptation(
            None,
            None,
            str(snapshot.get("protocol_version") or ACP_VERSION),
            tuple(dict.fromkeys(missing)),
            _semantic_gaps(snapshot),
        )

    return ACPOrderAdaptation(
        authorized_order=authorized_order,
        final_order=final_order,
        protocol_version=str(snapshot.get("protocol_version") or ACP_VERSION),
        missing_fields=(),
        unmapped_fields=_semantic_gaps(snapshot),
    )


def _build_order(
    checkout: Mapping[str, Any],
    context: Mapping[str, Any],
    *,
    snapshot_name: str,
    version_key: str,
    missing: list[str],
) -> Order | None:
    item_semantics = _mapping(context.get("item_semantics"))
    required_values = {
        f"{snapshot_name}.id": checkout.get("id"),
        f"{snapshot_name}.currency": checkout.get("currency"),
        f"experiment_context.{version_key}": context.get(version_key),
        "experiment_context.seller_id": context.get("seller_id"),
        "experiment_context.payee": context.get("payee"),
        "experiment_context.quote_expires_at": context.get("quote_expires_at"),
        "experiment_context.fulfilment_terms": context.get("fulfilment_terms"),
        "experiment_context.mandate_ref": context.get("mandate_ref"),
        "experiment_context.authority_version_ref": context.get("authority_version_ref"),
    }
    missing.extend(path for path, value in required_values.items() if value in (None, ""))

    line_items = checkout.get("line_items")
    if not isinstance(line_items, list) or not line_items:
        missing.append(f"{snapshot_name}.line_items")
        return None

    total_minor = _cart_total(checkout.get("totals"))
    if total_minor is None:
        missing.append(f"{snapshot_name}.totals[type=total].amount")

    scale = context.get("minor_unit_scale", 2)
    try:
        scale_int = int(scale)
    except (TypeError, ValueError):
        missing.append("experiment_context.minor_unit_scale")
        scale_int = 2

    items: list[OrderItem] = []
    for index, line_item in enumerate(line_items):
        if not isinstance(line_item, Mapping):
            missing.append(f"{snapshot_name}.line_items[{index}]")
            continue
        product = _mapping(line_item.get("item"))
        item_id = product.get("id") or line_item.get("id")
        name = product.get("name") or line_item.get("name")
        quantity = line_item.get("quantity")
        unit_amount_minor = line_item.get("unit_amount")
        if unit_amount_minor is None:
            unit_amount_minor = product.get("unit_amount")
        semantics = _mapping(item_semantics.get(str(item_id))) if item_id is not None else {}
        category = semantics.get("category")
        kind = semantics.get("kind", "product")

        required_item_values = {
            f"{snapshot_name}.line_items[{index}].item.id": item_id,
            f"{snapshot_name}.line_items[{index}].item.name": name,
            f"{snapshot_name}.line_items[{index}].quantity": quantity,
            f"{snapshot_name}.line_items[{index}].unit_amount": unit_amount_minor,
            f"experiment_context.item_semantics.{item_id}.category": category,
        }
        missing.extend(
            path for path, value in required_item_values.items() if value in (None, "")
        )
        if any(value in (None, "") for value in required_item_values.values()):
            continue

        items.append(
            OrderItem(
                item_id=str(item_id),
                name=str(name),
                category=str(category),
                quantity=int(quantity),
                unit_amount=_minor_to_decimal(unit_amount_minor, scale_int),
                kind=str(kind),
            )
        )

    if missing or total_minor is None:
        return None

    return Order(
        order_id=str(checkout["id"]),
        order_version=str(context[version_key]),
        merchant=str(context["seller_id"]),
        payee=str(context["payee"]),
        items=tuple(items),
        total_amount=_minor_to_decimal(total_minor, scale_int),
        currency=str(checkout["currency"]).upper(),
        quote_expires_at=_parse_datetime(context["quote_expires_at"]),
        fulfilment_terms=str(context["fulfilment_terms"]),
        mandate_ref=str(context["mandate_ref"]),
        service_id=(
            str(context["service_id"])
            if context.get("service_id") is not None
            else None
        ),
        candidate_rails=tuple(str(item) for item in context.get("candidate_rails", [])),
        authority_version_ref=str(context["authority_version_ref"]),
    )


def _cart_total(value: Any) -> Any:
    if not isinstance(value, list):
        return None
    for item in value:
        if isinstance(item, Mapping) and item.get("type") == "total":
            return item.get("amount")
    return None


def _minor_to_decimal(value: Any, scale: int) -> Decimal:
    divisor = Decimal(10) ** scale
    quantum = Decimal(1).scaleb(-scale)
    return (Decimal(str(value)) / divisor).quantize(quantum)


def _parse_datetime(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("ACP teaching snapshot timestamps must include a timezone")
    return parsed


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _semantic_gaps(snapshot: Mapping[str, Any]) -> tuple[str, ...]:
    known = {
        "protocol_version",
        "authorized_checkout",
        "final_checkout",
        "experiment_context",
    }
    top_level = [str(key) for key in snapshot if key not in known]
    gaps = [
        "seller_identity_from_endpoint_context_not_verified",
        "payee_identity_not_verified",
        "mandate_binding_from_experiment_context",
        "item_category_from_experiment_context",
        "quote_expiry_from_experiment_context",
        "payment_handler_not_mapped",
        "order_webhook_signature_not_verified",
        "no_live_acp_endpoint_or_conformance_test",
    ]
    return tuple(sorted(top_level + gaps))

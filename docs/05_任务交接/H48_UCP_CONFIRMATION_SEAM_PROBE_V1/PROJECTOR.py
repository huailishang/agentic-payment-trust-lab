"""H48-only, read-only checkout -> pre-payment Order projection.

Synthetic trust inputs are explicit test configuration, not merchant attestation.
No merchant operations, callbacks, network or durable writes occur here.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from decimal import Decimal

from agentic_payment_experiment.models import Order, OrderItem
from agentic_payment_experiment.trusted_execution.confirmation import confirmation_order_payload
from agentic_payment_experiment.trusted_execution.hashing import canonical_hash


class ProjectionMissing(ValueError):
    """A field cannot be represented faithfully in the narrow H48 contract."""


def _text(obj: dict, field: str) -> str:
    if not isinstance(obj, dict):
        raise ProjectionMissing(f"{field}: object_missing")
    value = obj.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ProjectionMissing(f"{field}: required_text")
    return value


def _minor_unit(value: object, field: str, *, positive: bool = False) -> int:
    # bool is a subclass of int and must not be interpreted as a price/quantity.
    if type(value) is not int or value < (1 if positive else 0):
        raise ProjectionMissing(f"{field}: integer_required")
    return value


def _mapping(value: object, field: str) -> dict:
    if not isinstance(value, dict):
        raise ProjectionMissing(f"{field}: object_required")
    return value


def _sequence(value: object, field: str) -> list:
    if not isinstance(value, list):
        raise ProjectionMissing(f"{field}: list_required")
    return value


def _project(checkout: dict, trust: dict) -> Order:
    ref = _text(checkout, "id")
    if checkout.get("currency") != "USD":
        raise ProjectionMissing("currency: explicit_USD_required")

    merchant = _text(trust, "merchant")
    payee = _text(trust, "payee")
    authority = _text(trust, "authority_id")
    version = _text(trust, "authority_version")
    fulfilment = _text(trust, "fulfilment_terms")
    service = _text(trust, "service_id")
    expiry_literal = _text(trust, "quote_expires_at")
    try:
        expiry = datetime.fromisoformat(expiry_literal)
    except ValueError as exc:
        raise ProjectionMissing("quote_expires_at: invalid_iso_datetime") from exc
    if expiry.tzinfo is None or expiry.utcoffset() is None:
        raise ProjectionMissing("quote_expires_at: timezone_required")

    amounts = _sequence(checkout.get("totals"), "totals")
    totals = [_mapping(entry, "total") for entry in amounts]
    final_totals = [entry for entry in totals if entry.get("type") == "total"]
    if len(final_totals) != 1:
        raise ProjectionMissing("totals: exactly_one_total_required")
    amount = Decimal(_minor_unit(final_totals[0].get("amount"), "total.amount")) / Decimal(100)

    categories = _mapping(trust.get("category_by_item"), "category_by_item")
    lines = _sequence(checkout.get("line_items"), "line_items")
    if not lines:
        raise ProjectionMissing("line_items: nonempty_required")
    items = []
    used_ids = set()
    for line in lines:
        line = _mapping(line, "line_item")
        article = _mapping(line.get("item"), "line_item.item")
        item_id = _text(article, "id")
        if item_id in used_ids:
            raise ProjectionMissing("line_items: duplicate_item_id")
        used_ids.add(item_id)
        category = _text(categories, item_id)
        items.append(OrderItem(
            item_id=item_id,
            name=_text(article, "title"),
            category=category,
            quantity=_minor_unit(line.get("quantity"), "line_item.quantity", positive=True),
            unit_amount=Decimal(_minor_unit(article.get("price"), "line_item.item.price")) / Decimal(100),
        ))

    order = Order(
        order_id="h48-checkout:" + ref,
        order_version="",
        merchant=merchant,
        payee=payee,
        items=tuple(items),
        total_amount=amount,
        currency="USD",
        quote_expires_at=expiry,
        fulfilment_terms=fulfilment,
        mandate_ref=authority,
        service_id=service,
        candidate_rails=(),
        authority_version_ref=version,
    )
    # Content digest is a local label; not a merchant-side version or CAS token.
    return replace(order, order_version=canonical_hash(confirmation_order_payload(order)))


def project_checkout(checkout: dict, trust: dict) -> dict:
    """Project fixed USD checkout content; fail closed with explicit missing evidence."""
    ref = checkout.get("id") if isinstance(checkout, dict) else None
    try:
        return {"order": _project(checkout, trust),
                "checkout_ref": ref, "final_order_ref": None, "missing": []}
    except (ProjectionMissing, ValueError, TypeError, AttributeError) as exc:
        return {"order": None, "checkout_ref": ref,
                "final_order_ref": None, "missing": [str(exc) or "invalid_checkout_input"]}

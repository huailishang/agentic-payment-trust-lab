from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
from typing import Any, Mapping

from ..models import Order, OrderItem, TransactionRequest

WEBSHOP_COMMIT = "64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd"
WEBSHOP_FIXTURE_SCHEMA = "webshop-pre-buy-now-candidate/v1"
WEBSHOP_SMOKE_EVIDENCE_PATH = (
    "docs/05_任务交接/P9_WEBSHOP_SMALL_RUNTIME_SMOKE_V1/"
    "evidence/rv_webshop_small_smoke.json"
)
WEBSHOP_SMOKE_SHA256 = "d1998c49a7afa14ee4534cd266d4e9e9c386ff2c2c8d85114aad19c304467e74"
EXPECTED_ASSET_HASHES = {
    "items_human_ins.json": "cf78667548a71786e1d9049c24b802e48e1084ad4bb021cae56ce1f6d96954a3",
    "items_ins_v2_1000.json": "f88a36314a397b53b3d9c3fa5878e5f7b26d35019a51ec83fbedeca61a948f6f",
    "items_shuffle_1000.json": "30a4765c3a327af72d9a9a95a6b2486d516f0fa1d3ecd83681901ce82a21b269",
}
REQUIRED_ASSET_NAMES = (
    "items_human_ins.json",
    "items_ins_v2_1000.json",
    "items_shuffle_1000.json",
)
REQUIRED_LIMITATIONS = (
    "instruction_product_match_not_assessed",
    "instruction_is_not_authorization_mandate",
    "merchant_and_payee_from_experiment_context",
    "no_runtime_authorization_decision",
    "no_purchase_or_payment_executed",
    "offline_mapping_only",
    "webshop_reward_not_mapped",
)
KNOWN_TOP_LEVEL_FIELDS = frozenset(
    {
        "fixture_schema",
        "fixture_version",
        "source",
        "session_id",
        "task_identifier",
        "instruction_text",
        "actions_executed",
        "buy_now_available",
        "buy_now_executed",
        "product",
        "experiment_context",
    }
)


@dataclass(frozen=True)
class WebShopCommerceAdaptation:
    """Offline mapping of one WebShop pre-Buy-Now candidate.

    The result deliberately keeps the human instruction separate from the
    selected product. It does not infer that the product satisfies the
    instruction, that the instruction is an authorization mandate, or that a
    purchase/payment is allowed.
    """

    user_intent_text: str | None
    order: Order | None
    payment_request: TransactionRequest | None
    source_commit: str
    fixture_version: str
    source_smoke_sha256: str | None
    source_asset_hashes: tuple[tuple[str, str], ...]
    selected_options: tuple[tuple[str, str], ...]
    experiment_context_origin: str | None
    missing_fields: tuple[str, ...]
    unmapped_fields: tuple[str, ...]
    limitations: tuple[str, ...] = REQUIRED_LIMITATIONS

    @property
    def ready(self) -> bool:
        return (
            self.order is not None
            and self.payment_request is not None
            and not self.missing_fields
        )


def adapt_webshop_purchase_candidate(
    snapshot: Mapping[str, Any],
) -> WebShopCommerceAdaptation:
    """Map one decoded WebShop fixture into protocol-neutral commerce objects.

    This function is pure and deterministic. It accepts an already-decoded
    mapping and performs no file, environment, process, network, WebShop,
    authorization-policy, payment, recovery, fulfilment, or UI operation.
    """

    if not isinstance(snapshot, Mapping):
        return _result(missing=("snapshot",))

    missing: list[str] = []
    unmapped = [
        f"top_level.{key}"
        for key in sorted(snapshot, key=str)
        if key not in KNOWN_TOP_LEVEL_FIELDS
    ]

    fixture_schema = _required_text(
        snapshot.get("fixture_schema"), "fixture_schema", missing
    )
    if fixture_schema and fixture_schema != WEBSHOP_FIXTURE_SCHEMA:
        missing.append("fixture_schema")

    fixture_version = _required_text(
        snapshot.get("fixture_version"), "fixture_version", missing
    ) or ""
    source = _mapping(snapshot.get("source"), "source", missing)
    product = _mapping(snapshot.get("product"), "product", missing)
    context = _mapping(
        snapshot.get("experiment_context"), "experiment_context", missing
    )

    source_commit = _required_text(
        source.get("webshop_commit"), "source.webshop_commit", missing
    ) or ""
    if source_commit and source_commit != WEBSHOP_COMMIT:
        missing.append("source.webshop_commit")

    source_smoke_sha256 = _sha256_text(
        source.get("smoke_result_sha256"),
        "source.smoke_result_sha256",
        missing,
    )
    if source_smoke_sha256 and source_smoke_sha256 != WEBSHOP_SMOKE_SHA256:
        missing.append("source.smoke_result_sha256")
    evidence_path = _required_text(
        source.get("evidence_path"), "source.evidence_path", missing
    )
    if evidence_path and evidence_path != WEBSHOP_SMOKE_EVIDENCE_PATH:
        missing.append("source.evidence_path")

    provenance = _mapping(source.get("provenance"), "source.provenance", missing)
    provenance_kind = _required_text(
        provenance.get("kind"), "source.provenance.kind", missing
    )
    if provenance_kind and provenance_kind != "local_p9_a2_evidence":
        missing.append("source.provenance.kind")
    if provenance.get("immutable") is not True:
        missing.append("source.provenance.immutable")

    source_asset_hashes = _asset_hashes(source.get("asset_hashes"), missing)

    session_id = _required_text(snapshot.get("session_id"), "session_id", missing)
    _required_text(snapshot.get("task_identifier"), "task_identifier", missing)

    instruction_value = snapshot.get("instruction_text")
    if isinstance(instruction_value, str) and instruction_value.strip():
        user_intent_text: str | None = instruction_value
    else:
        user_intent_text = None
        missing.append("instruction_text")

    actions = snapshot.get("actions_executed")
    if not isinstance(actions, (list, tuple)) or not actions:
        missing.append("actions_executed")
        action_values: tuple[str, ...] = ()
    elif any(not isinstance(action, str) or not action.strip() for action in actions):
        missing.append("actions_executed")
        action_values = ()
    else:
        action_values = tuple(actions)
        if any(_normalise_action(action) == "click[buynow]" for action in action_values):
            missing.append("actions_executed.buy_now_forbidden")

    if snapshot.get("buy_now_available") is not True:
        missing.append("buy_now_available")
    if snapshot.get("buy_now_executed") is not False:
        missing.append("buy_now_executed")

    asin = _required_text(product.get("asin"), "product.asin", missing)
    title = _required_text(product.get("title"), "product.title", missing)
    if "selected_options" not in product:
        missing.append("product.selected_options")
        selected_options: tuple[tuple[str, str], ...] = ()
    else:
        selected_options = _selected_options(
            product.get("selected_options"), missing
        )

    quantity = product.get("quantity")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        missing.append("product.quantity")
        quantity_value: int | None = None
    else:
        quantity_value = quantity

    unit_price = _positive_decimal_text(
        product.get("unit_price"), "product.unit_price", missing
    )
    order_total = _positive_decimal_text(
        product.get("order_total"), "product.order_total", missing
    )
    if (
        unit_price is not None
        and order_total is not None
        and quantity_value is not None
        and unit_price * quantity_value != order_total
    ):
        missing.append("product.order_total")

    merchant = _required_text(
        context.get("merchant"), "experiment_context.merchant", missing
    )
    payee = _required_text(
        context.get("payee"), "experiment_context.payee", missing
    )
    category = _required_text(
        context.get("category"), "experiment_context.category", missing
    )
    currency_raw = _required_text(
        context.get("currency"), "experiment_context.currency", missing
    )
    currency = currency_raw.upper() if currency_raw else None
    quote_expires_at = _timezone_datetime(
        context.get("quote_expires_at"),
        "experiment_context.quote_expires_at",
        missing,
    )
    fulfilment_terms = _required_text(
        context.get("fulfilment_terms"),
        "experiment_context.fulfilment_terms",
        missing,
    )
    mandate_ref = _required_text(
        context.get("mandate_ref"), "experiment_context.mandate_ref", missing
    )
    authority_version = _required_text(
        context.get("authority_version"),
        "experiment_context.authority_version",
        missing,
    )
    request_timestamp = _timezone_datetime(
        context.get("request_timestamp"),
        "experiment_context.request_timestamp",
        missing,
    )
    context_origin = _required_text(
        context.get("origin"), "experiment_context.origin", missing
    )
    if (
        context_origin
        and context_origin != "explicit_experiment_context_not_webshop_verified"
    ):
        missing.append("experiment_context.origin")

    missing_fields = tuple(dict.fromkeys(missing))
    if missing_fields:
        return _result(
            user_intent_text=user_intent_text,
            source_commit=source_commit,
            fixture_version=fixture_version,
            source_smoke_sha256=source_smoke_sha256,
            source_asset_hashes=source_asset_hashes,
            selected_options=selected_options,
            experiment_context_origin=context_origin,
            missing=missing_fields,
            unmapped=tuple(unmapped),
        )

    assert asin is not None
    assert title is not None
    assert quantity_value is not None
    assert unit_price is not None
    assert order_total is not None
    assert merchant is not None
    assert payee is not None
    assert category is not None
    assert currency is not None
    assert quote_expires_at is not None
    assert fulfilment_terms is not None
    assert mandate_ref is not None
    assert authority_version is not None
    assert request_timestamp is not None
    assert session_id is not None

    item_name = _item_name(title, selected_options)
    order_id = _deterministic_id(
        "webshop-order", fixture_version, session_id, asin.upper()
    )
    request_id = _deterministic_id(
        "webshop-request", fixture_version, session_id, asin.upper()
    )
    item = OrderItem(
        item_id=asin.upper(),
        name=item_name,
        category=category,
        quantity=quantity_value,
        unit_amount=unit_price,
    )
    order = Order(
        order_id=order_id,
        order_version=f"webshop-{fixture_version}",
        merchant=merchant,
        payee=payee,
        items=(item,),
        total_amount=order_total,
        currency=currency,
        quote_expires_at=quote_expires_at,
        fulfilment_terms=fulfilment_terms,
        mandate_ref=mandate_ref,
        authority_version_ref=authority_version,
    )
    payment_request = _build_transaction_request(
        request_id=request_id,
        order=order,
        category=category,
        occurred_at=request_timestamp,
    )
    if not _bindings_match(order, payment_request):
        return _result(
            user_intent_text=user_intent_text,
            source_commit=source_commit,
            fixture_version=fixture_version,
            source_smoke_sha256=source_smoke_sha256,
            source_asset_hashes=source_asset_hashes,
            selected_options=selected_options,
            experiment_context_origin=context_origin,
            missing=("order_request_binding",),
            unmapped=tuple(unmapped),
        )

    return WebShopCommerceAdaptation(
        user_intent_text=user_intent_text,
        order=order,
        payment_request=payment_request,
        source_commit=source_commit,
        fixture_version=fixture_version,
        source_smoke_sha256=source_smoke_sha256,
        source_asset_hashes=source_asset_hashes,
        selected_options=selected_options,
        experiment_context_origin=context_origin,
        missing_fields=(),
        unmapped_fields=tuple(unmapped),
    )


def _result(
    *,
    user_intent_text: str | None = None,
    source_commit: str = "",
    fixture_version: str = "",
    source_smoke_sha256: str | None = None,
    source_asset_hashes: tuple[tuple[str, str], ...] = (),
    selected_options: tuple[tuple[str, str], ...] = (),
    experiment_context_origin: str | None = None,
    missing: tuple[str, ...] = (),
    unmapped: tuple[str, ...] = (),
) -> WebShopCommerceAdaptation:
    return WebShopCommerceAdaptation(
        user_intent_text=user_intent_text,
        order=None,
        payment_request=None,
        source_commit=source_commit,
        fixture_version=fixture_version,
        source_smoke_sha256=source_smoke_sha256,
        source_asset_hashes=source_asset_hashes,
        selected_options=selected_options,
        experiment_context_origin=experiment_context_origin,
        missing_fields=missing,
        unmapped_fields=unmapped,
    )


def _mapping(value: Any, path: str, missing: list[str]) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    missing.append(path)
    return {}


def _required_text(value: Any, path: str, missing: list[str]) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    missing.append(path)
    return None


def _sha256_text(value: Any, path: str, missing: list[str]) -> str | None:
    text = _required_text(value, path, missing)
    if text is None:
        return None
    lowered = text.lower()
    if len(lowered) != 64 or any(char not in "0123456789abcdef" for char in lowered):
        missing.append(path)
        return None
    return lowered


def _asset_hashes(
    value: Any, missing: list[str]
) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, Mapping):
        missing.append("source.asset_hashes")
        return ()
    result: list[tuple[str, str]] = []
    for name in REQUIRED_ASSET_NAMES:
        path = f"source.asset_hashes.{name}"
        digest = _sha256_text(value.get(name), path, missing)
        if digest is not None:
            if digest != EXPECTED_ASSET_HASHES[name]:
                missing.append(path)
            result.append((name, digest))
    return tuple(result)


def _selected_options(
    value: Any, missing: list[str]
) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, Mapping):
        missing.append("product.selected_options")
        return ()
    options: list[tuple[str, str]] = []
    for key in sorted(value, key=str):
        option_value = value[key]
        if (
            not isinstance(key, str)
            or not key.strip()
            or not isinstance(option_value, str)
            or not option_value.strip()
        ):
            missing.append("product.selected_options")
            return ()
        options.append((key, option_value))
    return tuple(options)


def _positive_decimal_text(
    value: Any, path: str, missing: list[str]
) -> Decimal | None:
    if not isinstance(value, str) or not value.strip():
        missing.append(path)
        return None
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError):
        missing.append(path)
        return None
    if not parsed.is_finite() or parsed <= 0:
        missing.append(path)
        return None
    return parsed


def _timezone_datetime(
    value: Any, path: str, missing: list[str]
) -> datetime | None:
    text = _required_text(value, path, missing)
    if text is None:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        missing.append(path)
        return None
    if parsed.tzinfo is None:
        missing.append(path)
        return None
    return parsed


def _normalise_action(action: str) -> str:
    return "".join(action.lower().split())


def _item_name(
    title: str, selected_options: tuple[tuple[str, str], ...]
) -> str:
    if not selected_options:
        return title
    options = ", ".join(f"{key}={value}" for key, value in selected_options)
    return f"{title} | options: {options}"


def _deterministic_id(prefix: str, fixture_version: str, session_id: str, asin: str) -> str:
    material = "|".join((prefix, fixture_version, session_id, asin))
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}-{digest}"


def _build_transaction_request(
    *,
    request_id: str,
    order: Order,
    category: str,
    occurred_at: datetime,
) -> TransactionRequest:
    return TransactionRequest(
        request_id=request_id,
        amount=order.total_amount,
        merchant=order.merchant,
        category=category,
        occurred_at=occurred_at,
        sequence_count=1,
        currency=order.currency,
        order_ref=order.order_id,
        authority_ref=order.mandate_ref,
        authority_version_ref=order.authority_version_ref,
        payee=order.payee,
    )


def _bindings_match(order: Order, request: TransactionRequest) -> bool:
    return (
        request.order_ref == order.order_id
        and request.amount == order.total_amount
        and request.currency == order.currency
        and len(order.items) == 1
        and request.category == order.items[0].category
        and request.merchant == order.merchant
        and request.payee == order.payee
        and request.authority_ref == order.mandate_ref
        and request.authority_version_ref == order.authority_version_ref
    )

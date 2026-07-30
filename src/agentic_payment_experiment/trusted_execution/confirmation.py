"""P1 confirmation-to-order binding facts and a fail-closed execution gate.

The trusted-execution functions here only describe whether the confirmation
evidence still binds to the current order.  The payment domain maps that fact
to an action and owns the optional execution callback.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from ..models import Decision, Order
from .binding import BindingStatus, _normalize_expected_digest
from .hashing import canonical_hash


class ConfirmationStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    INVALIDATED = "INVALIDATED"
    REVOKED = "REVOKED"


@dataclass(frozen=True)
class ConfirmationRecord:
    """The durable evidence created when a user confirms one specific order."""

    confirmation_id: str
    authority_id: str
    authority_version: str
    authorized_order_id: str
    authorized_order_version: str
    authorized_order_hash: str
    confirmed_at: datetime
    expires_at: datetime
    status: ConfirmationStatus = ConfirmationStatus.CONFIRMED
    authorized_order_content: dict[str, Any] | None = None


@dataclass(frozen=True)
class ConfirmationBindingFact:
    """Fact returned before execution; it deliberately is not a payment decision."""

    status: BindingStatus
    expected_order_hash: str | None
    actual_order_hash: str | None
    authority_version: str | None
    reason: str
    invalidated_by: str | None
    checked_at: datetime


@dataclass(frozen=True)
class PaymentGateOutcome:
    """Business-domain mapping of a P1 fact, with execution gated on VALID only."""

    decision: Decision
    binding_fact: ConfirmationBindingFact
    executed: bool
    execution_result: Any | None = None


def confirmation_order_payload(order: Order) -> dict[str, Any]:
    """Return precisely the user-confirmed transaction content for P1 hashing.

    Transport-only fields such as order version, mandate reference, quote expiry,
    and candidate rails are intentionally excluded.  A version is verified as a
    separate reference below, so a stale version can never be hidden by this
    projection.
    """

    return {
        "merchant": order.merchant,
        "payee": order.payee,
        "items": tuple(
            {
                "item_id": item.item_id,
                "name": item.name.strip(),
                "category": item.category,
                "quantity": item.quantity,
                "unit_amount": item.unit_amount,
                "kind": item.kind,
            }
            for item in order.items
        ),
        "total_amount": order.total_amount,
        "currency": order.currency,
        "service_id": order.service_id,
        "fulfilment_terms": order.fulfilment_terms,
    }


def create_confirmation_record(
    *,
    confirmation_id: str,
    authority_id: str,
    authority_version: str,
    order: Order,
    confirmed_at: datetime,
    expires_at: datetime,
) -> ConfirmationRecord:
    """Create an in-memory P1 confirmation snapshot for the supplied order."""

    return ConfirmationRecord(
        confirmation_id=confirmation_id,
        authority_id=authority_id,
        authority_version=authority_version,
        authorized_order_id=order.order_id,
        authorized_order_version=order.order_version,
        authorized_order_hash=canonical_hash(confirmation_order_payload(order)),
        confirmed_at=confirmed_at,
        expires_at=expires_at,
        authorized_order_content=confirmation_order_payload(order),
    )


def verify_confirmation_binding(
    record: ConfirmationRecord | None,
    current_order: Order | None,
    *,
    authority_id: str | None,
    authority_version: str | None,
    checked_at: datetime,
) -> ConfirmationBindingFact:
    """Recompute and verify the P1 confirmation binding immediately pre-payment."""

    if record is None:
        return _missing("confirmation_record_missing", checked_at)
    if current_order is None:
        return _missing("current_order_missing", checked_at, record)
    if not _nonempty_record_fields(record):
        return _missing("confirmation_record_incomplete", checked_at, record)
    if not _is_aware(record.confirmed_at) or not _is_aware(record.expires_at) or not _is_aware(checked_at):
        return _missing("confirmation_timestamp_invalid", checked_at, record)
    expected = _normalize_expected_digest(record.authorized_order_hash, 32)
    if expected is None:
        return _missing("authorized_order_hash_invalid", checked_at, record)

    actual = canonical_hash(confirmation_order_payload(current_order))
    if record.status is not ConfirmationStatus.CONFIRMED:
        return _invalid(record, actual, checked_at, "confirmation_not_active", "confirmation_status_changed")
    if checked_at > record.expires_at:
        return _invalid(record, actual, checked_at, "confirmation_expired", "confirmation_expired")
    if authority_id != record.authority_id:
        return _invalid(record, actual, checked_at, "authority_id_mismatch", "authority_id_changed")
    if authority_version != record.authority_version:
        return _invalid(record, actual, checked_at, "authority_version_mismatch", "authority_version_changed")
    if current_order.order_id != record.authorized_order_id:
        return _invalid(record, actual, checked_at, "order_id_mismatch", "order_id_changed")
    if current_order.order_version != record.authorized_order_version:
        return _invalid(record, actual, checked_at, "order_version_mismatch", "order_version_changed")
    if expected != actual:
        return _invalid(record, actual, checked_at, "order_hash_mismatch", _changed_field(record, current_order))
    return ConfirmationBindingFact(BindingStatus.VALID, expected, actual, authority_version, "confirmation_binding_match", None, checked_at)


def execute_with_confirmation_gate(
    binding_fact: ConfirmationBindingFact,
    execute_payment: Callable[[], Any],
) -> PaymentGateOutcome:
    """Call the payment callback only when P1 evidence is valid."""

    if binding_fact.status is BindingStatus.VALID:
        return PaymentGateOutcome(Decision.ALLOW, binding_fact, True, execute_payment())
    decision = Decision.CONFIRMATION_REQUIRED if binding_fact.status is BindingStatus.INVALID else Decision.INDETERMINATE
    return PaymentGateOutcome(decision, binding_fact, False)


def _nonempty_record_fields(record: ConfirmationRecord) -> bool:
    return all(str(value).strip() for value in (record.confirmation_id, record.authority_id, record.authority_version, record.authorized_order_id, record.authorized_order_version, record.authorized_order_hash))


def _is_aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


def _missing(reason: str, checked_at: datetime, record: ConfirmationRecord | None = None) -> ConfirmationBindingFact:
    return ConfirmationBindingFact(BindingStatus.MISSING_EVIDENCE, record.authorized_order_hash if record else None, None, record.authority_version if record else None, reason, None, checked_at)


def _invalid(record: ConfirmationRecord, actual: str, checked_at: datetime, reason: str, invalidated_by: str) -> ConfirmationBindingFact:
    return ConfirmationBindingFact(BindingStatus.INVALID, record.authorized_order_hash, actual, record.authority_version, reason, invalidated_by, checked_at)


def _changed_field(record: ConfirmationRecord, order: Order) -> str:
    expected = record.authorized_order_content
    if expected is None:
        return "confirmed_transaction_content_changed"
    actual = confirmation_order_payload(order)
    for field in ("merchant", "payee", "items", "total_amount", "currency", "service_id", "fulfilment_terms"):
        if expected.get(field) != actual[field]:
            return f"{field}_changed"
    return "confirmed_transaction_content_changed"
    if not str(authority_id or "").strip() or not str(authority_version or "").strip():
        return _missing("current_authority_reference_missing", checked_at, record)

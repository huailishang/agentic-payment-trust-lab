from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from .models import (
    Decision,
    DisputeRecord,
    DisputeStatus,
    FulfillmentRecord,
    FulfillmentStatus,
    IntentMandate,
    Order,
    OrderItem,
    PaymentExecutionRecord,
    PaymentRecoveryStatus,
    PaymentStatus,
    PaymentStatusObservation,
    RefundRecord,
    RefundStatus,
    RemediationStatus,
    TaskStatus,
    TransactionRequest,
)
from .trusted_execution import (
    ConfirmationRecord,
    ConfirmationStatus,
    canonical_hash,
    confirmation_order_payload,
)


@dataclass(frozen=True)
class ScenarioExpectation:
    decision: Decision
    reason_codes: frozenset[str]
    evidence_codes: frozenset[str]
    forbidden_effects: frozenset[str]


@dataclass(frozen=True)
class LifecycleExpectation:
    payment_status: PaymentStatus
    fulfillment_status: FulfillmentStatus
    remediation_status: RemediationStatus
    task_status: TaskStatus
    reason_codes: frozenset[str]
    evidence_codes: frozenset[str]
    refund_status: RefundStatus | None = None
    dispute_status: DisputeStatus | None = None


@dataclass(frozen=True)
class PaymentRecoveryExpectation:
    initial_status: PaymentStatus
    observed_status: PaymentStatus
    effective_status: PaymentStatus
    recovery_status: PaymentRecoveryStatus
    retry_allowed: bool
    next_action: str
    reason_codes: frozenset[str]
    evidence_codes: frozenset[str]


@dataclass(frozen=True)
class Scenario:
    sample_id: str
    title: str
    question: str
    mandate: IntentMandate
    request: TransactionRequest
    authorized_order: Order | None
    final_order: Order | None
    confirmation_record: ConfirmationRecord | None
    seen_request_ids: frozenset[str]
    payment_execution: PaymentExecutionRecord | None
    fulfillment: FulfillmentRecord | None
    refund: RefundRecord | None
    dispute: DisputeRecord | None
    payment_recovery_initial: PaymentExecutionRecord | None
    payment_status_observation: PaymentStatusObservation | None
    known_payment_attempts: tuple[PaymentExecutionRecord, ...]
    expected: ScenarioExpectation
    expected_lifecycle: LifecycleExpectation | None
    expected_payment_recovery: PaymentRecoveryExpectation | None
    flow: tuple[dict[str, Any], ...]
    limitations: tuple[str, ...]
    raw: dict[str, Any]
    source_path: Path


def load_scenarios(directory: Path) -> tuple[Scenario, ...]:
    """Load and validate all JSON scenarios in lexical order."""

    if not directory.exists():
        raise FileNotFoundError(f"scenario directory does not exist: {directory}")

    paths = sorted(directory.glob("S*.json"))
    if not paths:
        raise ValueError(f"no scenario JSON files found in: {directory}")

    scenarios = tuple(load_scenario(path) for path in paths)
    ids = [scenario.sample_id for scenario in scenarios]
    if len(ids) != len(set(ids)):
        raise ValueError("scenario sample_id values must be unique")
    return scenarios


def load_scenario(path: Path) -> Scenario:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc

    required = ("sample_id", "title", "question", "mandate", "request", "expected")
    missing = [field for field in required if field not in raw]
    if missing:
        raise ValueError(f"{path} is missing required fields: {', '.join(missing)}")

    mandate_data = raw["mandate"]
    request_data = raw["request"]
    expected_data = raw["expected"]

    mandate = IntentMandate(
        mandate_id=_required_text(mandate_data, "mandate_id", path),
        user_id=_required_text(mandate_data, "user_id", path),
        max_amount=Decimal(str(mandate_data["max_amount"])),
        allowed_merchants=frozenset(str(item) for item in mandate_data.get("allowed_merchants", [])),
        allowed_categories=frozenset(str(item) for item in mandate_data.get("allowed_categories", [])),
        expires_at=_parse_datetime(mandate_data["expires_at"], path, "mandate.expires_at"),
        max_count=int(mandate_data.get("max_count", 1)),
        confirmation_above=(
            Decimal(str(mandate_data["confirmation_above"]))
            if mandate_data.get("confirmation_above") is not None
            else None
        ),
        expected_agent_id=mandate_data.get("expected_agent_id"),
        currency=str(mandate_data.get("currency", "CNY")),
        authority_version=str(mandate_data.get("authority_version", "v1")),
    )
    request = TransactionRequest(
        request_id=_required_text(request_data, "request_id", path),
        amount=Decimal(str(request_data["amount"])),
        merchant=str(request_data.get("merchant", "")),
        category=str(request_data.get("category", "")),
        occurred_at=_parse_datetime(request_data["occurred_at"], path, "request.occurred_at"),
        sequence_count=int(request_data.get("sequence_count", 1)),
        agent_id=request_data.get("agent_id"),
        currency=str(request_data.get("currency", "CNY")),
    )
    authorized_order_data = raw.get("authorized_order")
    final_order_data = raw.get("final_order")
    if (authorized_order_data is None) != (final_order_data is None):
        raise ValueError(f"{path} must provide both authorized_order and final_order")
    authorized_order = (
        _load_order(authorized_order_data, path, "authorized_order")
        if authorized_order_data is not None
        else None
    )
    final_order = (
        _load_order(final_order_data, path, "final_order")
        if final_order_data is not None
        else None
    )
    confirmation_data = raw.get("confirmation_record")
    if confirmation_data is not None and authorized_order is None:
        raise ValueError(f"{path} confirmation_record requires authorized_order")
    confirmation_record = (
        _load_confirmation_record(confirmation_data, authorized_order, path)
        if confirmation_data is not None and authorized_order is not None
        else None
    )

    lifecycle_data = raw.get("lifecycle")
    expected_lifecycle_data = raw.get("expected_lifecycle")
    if (lifecycle_data is None) != (expected_lifecycle_data is None):
        raise ValueError(
            f"{path} must provide lifecycle and expected_lifecycle together"
        )
    payment_execution: PaymentExecutionRecord | None = None
    fulfillment: FulfillmentRecord | None = None
    refund: RefundRecord | None = None
    dispute: DisputeRecord | None = None
    expected_lifecycle: LifecycleExpectation | None = None
    if lifecycle_data is not None:
        if not isinstance(lifecycle_data, dict) or not isinstance(expected_lifecycle_data, dict):
            raise ValueError(f"{path} lifecycle fields must be objects")
        payment_data = lifecycle_data.get("payment")
        fulfillment_data = lifecycle_data.get("fulfillment")
        refund_data = lifecycle_data.get("refund")
        dispute_data = lifecycle_data.get("dispute")
        if not isinstance(payment_data, dict) or not isinstance(fulfillment_data, dict):
            raise ValueError(f"{path} lifecycle must include payment and fulfillment objects")
        if refund_data is not None and not isinstance(refund_data, dict):
            raise ValueError(f"{path} lifecycle.refund must be an object")
        if dispute_data is not None and not isinstance(dispute_data, dict):
            raise ValueError(f"{path} lifecycle.dispute must be an object")
        try:
            payment_execution = _load_payment_execution(
                payment_data,
                path,
                "lifecycle.payment",
            )
            fulfillment = FulfillmentRecord(
                fulfillment_id=_required_text(fulfillment_data, "fulfillment_id", path),
                order_id=_required_text(fulfillment_data, "order_id", path),
                status=FulfillmentStatus(str(fulfillment_data["status"])),
                occurred_at=_parse_datetime(
                    fulfillment_data["occurred_at"],
                    path,
                    "lifecycle.fulfillment.occurred_at",
                ),
                service_id=(
                    str(fulfillment_data["service_id"])
                    if fulfillment_data.get("service_id") is not None
                    else None
                ),
                evidence_ref=(
                    str(fulfillment_data["evidence_ref"])
                    if fulfillment_data.get("evidence_ref") is not None
                    else None
                ),
                failure_code=(
                    str(fulfillment_data["failure_code"])
                    if fulfillment_data.get("failure_code") is not None
                    else None
                ),
            )
            if refund_data is not None:
                refund = RefundRecord(
                    refund_id=_required_text(refund_data, "refund_id", path),
                    payment_id=_required_text(refund_data, "payment_id", path),
                    order_id=_required_text(refund_data, "order_id", path),
                    status=RefundStatus(str(refund_data["status"])),
                    amount=Decimal(str(refund_data["amount"])),
                    currency=_required_text(refund_data, "currency", path),
                    occurred_at=_parse_datetime(
                        refund_data["occurred_at"], path, "lifecycle.refund.occurred_at"
                    ),
                    receipt_ref=(
                        str(refund_data["receipt_ref"])
                        if refund_data.get("receipt_ref") is not None
                        else None
                    ),
                    reason_code=(
                        str(refund_data["reason_code"])
                        if refund_data.get("reason_code") is not None
                        else None
                    ),
                )
            if dispute_data is not None:
                dispute = DisputeRecord(
                    dispute_id=_required_text(dispute_data, "dispute_id", path),
                    payment_id=_required_text(dispute_data, "payment_id", path),
                    order_id=_required_text(dispute_data, "order_id", path),
                    status=DisputeStatus(str(dispute_data["status"])),
                    opened_at=_parse_datetime(
                        dispute_data["opened_at"], path, "lifecycle.dispute.opened_at"
                    ),
                    reason_code=(
                        str(dispute_data["reason_code"])
                        if dispute_data.get("reason_code") is not None
                        else None
                    ),
                    evidence_ref=(
                        str(dispute_data["evidence_ref"])
                        if dispute_data.get("evidence_ref") is not None
                        else None
                    ),
                )
            expected_lifecycle = LifecycleExpectation(
                payment_status=PaymentStatus(str(expected_lifecycle_data["payment_status"])),
                fulfillment_status=FulfillmentStatus(
                    str(expected_lifecycle_data["fulfillment_status"])
                ),
                remediation_status=RemediationStatus(
                    str(expected_lifecycle_data["remediation_status"])
                ),
                task_status=TaskStatus(str(expected_lifecycle_data["task_status"])),
                reason_codes=frozenset(
                    str(item) for item in expected_lifecycle_data.get("reason_codes", [])
                ),
                evidence_codes=frozenset(
                    str(item) for item in expected_lifecycle_data.get("evidence_codes", [])
                ),
                refund_status=(
                    RefundStatus(str(expected_lifecycle_data["refund_status"]))
                    if expected_lifecycle_data.get("refund_status") is not None
                    else None
                ),
                dispute_status=(
                    DisputeStatus(str(expected_lifecycle_data["dispute_status"]))
                    if expected_lifecycle_data.get("dispute_status") is not None
                    else None
                ),
            )
        except (KeyError, ValueError) as exc:
            raise ValueError(f"{path} has invalid lifecycle status fields") from exc

    payment_recovery_data = raw.get("payment_recovery")
    expected_payment_recovery_data = raw.get("expected_payment_recovery")
    if (payment_recovery_data is None) != (expected_payment_recovery_data is None):
        raise ValueError(
            f"{path} must provide payment_recovery and expected_payment_recovery together"
        )
    payment_recovery_initial: PaymentExecutionRecord | None = None
    payment_status_observation: PaymentStatusObservation | None = None
    known_payment_attempts: tuple[PaymentExecutionRecord, ...] = ()
    expected_payment_recovery: PaymentRecoveryExpectation | None = None
    if payment_recovery_data is not None:
        if not isinstance(payment_recovery_data, dict) or not isinstance(
            expected_payment_recovery_data, dict
        ):
            raise ValueError(f"{path} payment recovery fields must be objects")
        initial_payment_data = payment_recovery_data.get("initial_payment")
        observation_data = payment_recovery_data.get("status_observation")
        attempts_data = payment_recovery_data.get("known_attempts", [])
        if not isinstance(initial_payment_data, dict) or not isinstance(observation_data, dict):
            raise ValueError(
                f"{path} payment_recovery must include initial_payment and status_observation objects"
            )
        if not isinstance(attempts_data, list) or not all(
            isinstance(item, dict) for item in attempts_data
        ):
            raise ValueError(f"{path} payment_recovery.known_attempts must be a list of objects")
        try:
            payment_recovery_initial = _load_payment_execution(
                initial_payment_data,
                path,
                "payment_recovery.initial_payment",
            )
            payment_status_observation = PaymentStatusObservation(
                payment_id=_required_text(observation_data, "payment_id", path),
                order_id=_required_text(observation_data, "order_id", path),
                status=PaymentStatus(str(observation_data["status"])),
                observed_at=_parse_datetime(
                    observation_data["observed_at"],
                    path,
                    "payment_recovery.status_observation.observed_at",
                ),
                source=_required_text(observation_data, "source", path),
                provider_ref=(
                    str(observation_data["provider_ref"])
                    if observation_data.get("provider_ref") is not None
                    else None
                ),
            )
            known_payment_attempts = tuple(
                _load_payment_execution(
                    item,
                    path,
                    f"payment_recovery.known_attempts[{index}]",
                )
                for index, item in enumerate(attempts_data)
            )
            expected_payment_recovery = PaymentRecoveryExpectation(
                initial_status=PaymentStatus(
                    str(expected_payment_recovery_data["initial_status"])
                ),
                observed_status=PaymentStatus(
                    str(expected_payment_recovery_data["observed_status"])
                ),
                effective_status=PaymentStatus(
                    str(expected_payment_recovery_data["effective_status"])
                ),
                recovery_status=PaymentRecoveryStatus(
                    str(expected_payment_recovery_data["recovery_status"])
                ),
                retry_allowed=bool(expected_payment_recovery_data["retry_allowed"]),
                next_action=_required_text(expected_payment_recovery_data, "next_action", path),
                reason_codes=frozenset(
                    str(item) for item in expected_payment_recovery_data.get("reason_codes", [])
                ),
                evidence_codes=frozenset(
                    str(item) for item in expected_payment_recovery_data.get("evidence_codes", [])
                ),
            )
        except (KeyError, ValueError) as exc:
            raise ValueError(f"{path} has invalid payment recovery fields") from exc

    try:
        expected_decision = Decision(str(expected_data["decision"]))
    except (KeyError, ValueError) as exc:
        raise ValueError(f"{path} has an invalid expected.decision") from exc

    return Scenario(
        sample_id=str(raw["sample_id"]),
        title=str(raw["title"]),
        question=str(raw["question"]),
        mandate=mandate,
        request=request,
        authorized_order=authorized_order,
        final_order=final_order,
        confirmation_record=confirmation_record,
        seen_request_ids=frozenset(str(item) for item in raw.get("seen_request_ids", [])),
        payment_execution=payment_execution,
        fulfillment=fulfillment,
        refund=refund,
        dispute=dispute,
        payment_recovery_initial=payment_recovery_initial,
        payment_status_observation=payment_status_observation,
        known_payment_attempts=known_payment_attempts,
        expected=ScenarioExpectation(
            decision=expected_decision,
            reason_codes=frozenset(str(item) for item in expected_data.get("reason_codes", [])),
            evidence_codes=frozenset(str(item) for item in expected_data.get("evidence_codes", [])),
            forbidden_effects=frozenset(
                str(item) for item in expected_data.get("forbidden_effects", [])
            ),
        ),
        expected_lifecycle=expected_lifecycle,
        expected_payment_recovery=expected_payment_recovery,
        flow=tuple(dict(step) for step in raw.get("flow", [])),
        limitations=tuple(str(item) for item in raw.get("limitations", [])),
        raw=raw,
        source_path=path,
    )


def _required_text(data: dict[str, Any], field: str, path: Path) -> str:
    if field not in data:
        raise ValueError(f"{path} is missing {field}")
    return str(data[field])


def _parse_datetime(value: Any, path: Path, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{path} has an invalid {field}: {value}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{path} field {field} must include a timezone")
    return parsed


def _load_payment_execution(
    data: dict[str, Any],
    path: Path,
    field: str,
) -> PaymentExecutionRecord:
    return PaymentExecutionRecord(
        payment_id=_required_text(data, "payment_id", path),
        request_id=_required_text(data, "request_id", path),
        order_id=_required_text(data, "order_id", path),
        status=PaymentStatus(str(data["status"])),
        amount=Decimal(str(data["amount"])),
        currency=_required_text(data, "currency", path),
        occurred_at=_parse_datetime(data["occurred_at"], path, f"{field}.occurred_at"),
        receipt_ref=(str(data["receipt_ref"]) if data.get("receipt_ref") is not None else None),
        provider_ref=(str(data["provider_ref"]) if data.get("provider_ref") is not None else None),
        idempotency_key=(
            str(data["idempotency_key"]) if data.get("idempotency_key") is not None else None
        ),
    )


def _load_order(data: dict[str, Any], path: Path, field: str) -> Order:
    items = tuple(
        OrderItem(
            item_id=_required_text(item, "item_id", path),
            name=_required_text(item, "name", path),
            category=_required_text(item, "category", path),
            quantity=int(item["quantity"]),
            unit_amount=Decimal(str(item["unit_amount"])),
            kind=str(item.get("kind", "product")),
        )
        for item in data.get("items", [])
    )
    return Order(
        order_id=_required_text(data, "order_id", path),
        order_version=_required_text(data, "order_version", path),
        merchant=_required_text(data, "merchant", path),
        payee=_required_text(data, "payee", path),
        items=items,
        total_amount=Decimal(str(data["total_amount"])),
        currency=_required_text(data, "currency", path),
        quote_expires_at=_parse_datetime(
            data["quote_expires_at"], path, f"{field}.quote_expires_at"
        ),
        fulfilment_terms=_required_text(data, "fulfilment_terms", path),
        mandate_ref=_required_text(data, "mandate_ref", path),
        service_id=(str(data["service_id"]) if data.get("service_id") is not None else None),
        candidate_rails=tuple(str(item) for item in data.get("candidate_rails", [])),
        authority_version_ref=(
            str(data["authority_version_ref"])
            if data.get("authority_version_ref") is not None
            else None
        ),
    )


def _load_confirmation_record(
    data: dict[str, Any],
    authorized_order: Order,
    path: Path,
) -> ConfirmationRecord:
    if not isinstance(data, dict):
        raise ValueError(f"{path} confirmation_record must be an object")
    declared_hash = _required_text(data, "authorized_order_hash", path).lower()
    content = confirmation_order_payload(authorized_order)
    actual_hash = canonical_hash(content)
    if declared_hash != actual_hash:
        raise ValueError(
            f"{path} confirmation_record.authorized_order_hash does not match authorized_order"
        )
    try:
        status = ConfirmationStatus(str(data.get("status", "CONFIRMED")))
    except ValueError as exc:
        raise ValueError(f"{path} has an invalid confirmation_record.status") from exc
    return ConfirmationRecord(
        confirmation_id=_required_text(data, "confirmation_id", path),
        authority_id=_required_text(data, "authority_id", path),
        authority_version=_required_text(data, "authority_version", path),
        authorized_order_id=_required_text(data, "authorized_order_id", path),
        authorized_order_version=_required_text(data, "authorized_order_version", path),
        authorized_order_hash=declared_hash,
        confirmed_at=_parse_datetime(
            data["confirmed_at"], path, "confirmation_record.confirmed_at"
        ),
        expires_at=_parse_datetime(
            data["expires_at"], path, "confirmation_record.expires_at"
        ),
        status=status,
        authorized_order_content=content,
    )

"""Bounded, offline x402 fixture adapter.

The adapter translates a deliberately small project-local x402 fixture shape into
existing protocol-neutral payment models.  It does not import an x402 SDK, call a
facilitator, create a wallet, sign a payload, settle funds, deliver a resource, or
claim official x402 conformance.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Mapping

from ..models import (
    FulfillmentRecord,
    FulfillmentStatus,
    IntentMandate,
    Order,
    OrderItem,
    PaymentExecutionRecord,
    PaymentStatus,
    PaymentStatusObservation,
    TransactionRequest,
)
from ..trusted_execution.hashing import canonical_hash


FIXTURE_VERSION = "x402-offline-fixture-v1"
SUPPORTED_SCHEMES = frozenset({"exact"})
SUPPORTED_NETWORKS = frozenset({"base-sepolia", "solana-devnet"})
SUPPORTED_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})


class X402AdaptationStatus(str, Enum):
    READY = "READY"
    INVALID = "INVALID"
    UNSUPPORTED = "UNSUPPORTED"


class X402VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


class X402SettlementStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"


class X402DeliveryStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class X402SideEffectRecord:
    network_called: bool = False
    wallet_created: bool = False
    signature_created: bool = False
    payment_executed: bool = False

    def to_dict(self) -> dict[str, bool]:
        return {
            "network_called": self.network_called,
            "wallet_created": self.wallet_created,
            "signature_created": self.signature_created,
            "payment_executed": self.payment_executed,
        }


@dataclass(frozen=True)
class X402DeliveryAttempt:
    execution_id: str
    request_ref: str
    resource_ref: str
    proof_ref: str
    status: FulfillmentStatus
    observed_at: datetime

    def to_dict(self) -> dict[str, str]:
        return {
            "execution_id": self.execution_id,
            "request_ref": self.request_ref,
            "resource_ref": self.resource_ref,
            "proof_ref": self.proof_ref,
            "status": self.status.value,
            "observed_at": self.observed_at.isoformat(),
        }


@dataclass(frozen=True)
class X402Adaptation:
    case_id: str
    fixture_version: str
    status: X402AdaptationStatus
    reason_codes: tuple[str, ...]
    protocol_mismatch_reason_codes: tuple[str, ...]
    mandate: IntentMandate | None
    order: Order | None
    request: TransactionRequest | None
    payment: PaymentExecutionRecord | None
    verification_status: X402VerificationStatus | None
    settlement_observation: PaymentStatusObservation | None
    async_observation: PaymentStatusObservation | None
    resource_delivery: FulfillmentRecord | None
    delivery_attempts: tuple[X402DeliveryAttempt, ...]
    source_evidence: dict[str, object]
    limitations: tuple[str, ...]
    side_effects: X402SideEffectRecord

    @property
    def ready(self) -> bool:
        return self.status is X402AdaptationStatus.READY


def compute_requirement_digest(
    http_request: Mapping[str, Any],
    payment_requirement: Mapping[str, Any],
) -> str:
    """Hash validated bounded resource/payment requirement fields deterministically."""

    text_errors = _required_text_field_errors(
        {
            "http_request.method": http_request.get("method"),
            "http_request.resource_ref": http_request.get("resource_ref"),
            "http_request.request_ref": http_request.get("request_ref"),
            "payment_requirement.requirement_id": payment_requirement.get("requirement_id"),
            "payment_requirement.resource_ref": payment_requirement.get("resource_ref"),
            "payment_requirement.scheme": payment_requirement.get("scheme"),
            "payment_requirement.network": payment_requirement.get("network"),
            "payment_requirement.asset": payment_requirement.get("asset"),
            "payment_requirement.payee": payment_requirement.get("payee"),
        }
    )
    if text_errors:
        raise ValueError(",".join(text_errors))

    amount = _parse_decimal_value(payment_requirement.get("amount"))
    payload = {
        "http_method": http_request["method"].upper(),
        "resource_ref": payment_requirement["resource_ref"],
        "request_ref": http_request["request_ref"],
        "requirement_id": payment_requirement["requirement_id"],
        "scheme": payment_requirement["scheme"],
        "network": payment_requirement["network"],
        "asset": payment_requirement["asset"],
        "amount": amount,
        "payee": payment_requirement["payee"],
    }
    return canonical_hash(payload)


def adapt_x402_fixture(fixture: Mapping[str, Any]) -> X402Adaptation:
    """Parse one synthetic x402 fixture and map it into neutral local facts."""

    sections, section_errors = _sections(fixture)
    if section_errors:
        return _empty_adaptation(fixture, X402AdaptationStatus.INVALID, section_errors)

    http_request = sections["http_request"]
    requirement = sections["payment_requirement"]
    proof = sections["payment_proof"]
    verification = sections["facilitator_verification"]
    settlement = sections["facilitator_settlement"]
    async_observation = sections["facilitator_async_observation"]
    delivery = sections["resource_delivery"]
    context = sections["project_context"]

    text_fields: dict[str, Any] = {
        "case_id": fixture.get("case_id"),
        "fixture_version": fixture.get("fixture_version"),
        "http_request.method": http_request.get("method"),
        "http_request.resource_ref": http_request.get("resource_ref"),
        "http_request.request_ref": http_request.get("request_ref"),
        "payment_requirement.requirement_id": requirement.get("requirement_id"),
        "payment_requirement.requirement_digest": requirement.get("requirement_digest"),
        "payment_requirement.resource_ref": requirement.get("resource_ref"),
        "payment_requirement.scheme": requirement.get("scheme"),
        "payment_requirement.network": requirement.get("network"),
        "payment_requirement.asset": requirement.get("asset"),
        "payment_requirement.payee": requirement.get("payee"),
        "payment_proof.proof_ref": proof.get("proof_ref"),
        "payment_proof.requirement_ref": proof.get("requirement_ref"),
        "payment_proof.requirement_digest": proof.get("requirement_digest"),
        "payment_proof.request_ref": proof.get("request_ref"),
        "payment_proof.resource_ref": proof.get("resource_ref"),
        "payment_proof.scheme": proof.get("scheme"),
        "payment_proof.network": proof.get("network"),
        "payment_proof.asset": proof.get("asset"),
        "payment_proof.payee": proof.get("payee"),
        "payment_proof.original_transaction_ref": proof.get("original_transaction_ref"),
        "facilitator_verification.status": verification.get("status"),
        "facilitator_verification.proof_ref": verification.get("proof_ref"),
        "facilitator_verification.requirement_ref": verification.get("requirement_ref"),
        "facilitator_settlement.status": settlement.get("status"),
        "facilitator_settlement.proof_ref": settlement.get("proof_ref"),
        "facilitator_settlement.payment_ref": settlement.get("payment_ref"),
        "facilitator_settlement.original_transaction_ref": settlement.get("original_transaction_ref"),
        "facilitator_settlement.provider_ref": settlement.get("provider_ref"),
        "facilitator_async_observation.status": async_observation.get("status"),
        "facilitator_async_observation.payment_ref": async_observation.get("payment_ref"),
        "facilitator_async_observation.original_transaction_ref": async_observation.get("original_transaction_ref"),
        "facilitator_async_observation.provider_ref": async_observation.get("provider_ref"),
        "resource_delivery.status": delivery.get("status"),
        "resource_delivery.request_ref": delivery.get("request_ref"),
        "resource_delivery.resource_ref": delivery.get("resource_ref"),
        "resource_delivery.proof_ref": delivery.get("proof_ref"),
        "resource_delivery.delivery_ref": delivery.get("delivery_ref"),
        "project_context.user_ref": context.get("user_ref"),
        "project_context.agent_ref": context.get("agent_ref"),
        "project_context.authority_ref": context.get("authority_ref"),
        "project_context.authority_version": context.get("authority_version"),
        "project_context.merchant_ref": context.get("merchant_ref"),
        "project_context.category": context.get("category"),
    }
    if "failure_code" in delivery and delivery.get("failure_code") is not None:
        text_fields["resource_delivery.failure_code"] = delivery.get("failure_code")
    text_errors = _required_text_field_errors(text_fields)
    if text_errors:
        return _empty_adaptation(fixture, X402AdaptationStatus.INVALID, text_errors)

    if fixture.get("fixture_version") != FIXTURE_VERSION:
        return _empty_adaptation(
            fixture,
            X402AdaptationStatus.UNSUPPORTED,
            (f"x402_fixture_version_unsupported:{fixture.get('fixture_version')}",),
        )

    method = http_request["method"].upper()
    scheme = requirement["scheme"]
    network = requirement["network"]
    unsupported: list[str] = []
    if method not in SUPPORTED_METHODS:
        unsupported.append(f"x402_http_method_unsupported:{method}")
    if scheme not in SUPPORTED_SCHEMES:
        unsupported.append(f"x402_scheme_unsupported:{scheme}")
    if network not in SUPPORTED_NETWORKS:
        unsupported.append(f"x402_network_unsupported:{network}")
    if unsupported:
        return _empty_adaptation(
            fixture,
            X402AdaptationStatus.UNSUPPORTED,
            tuple(unsupported),
        )

    parse_errors: list[str] = []
    requirement_amount = _parse_decimal(requirement.get("amount"), "payment_requirement.amount", parse_errors)
    proof_amount = _parse_decimal(proof.get("amount"), "payment_proof.amount", parse_errors)
    request_time = _parse_datetime(http_request.get("occurred_at"), "http_request.occurred_at", parse_errors)
    requirement_time = _parse_datetime(requirement.get("issued_at"), "payment_requirement.issued_at", parse_errors)
    proof_time = _parse_datetime(proof.get("signed_at"), "payment_proof.signed_at", parse_errors)
    authorization_expires_at = _parse_datetime(
        context.get("authorization_expires_at"),
        "project_context.authorization_expires_at",
        parse_errors,
    )
    verification_time = _parse_datetime(
        verification.get("observed_at"),
        "facilitator_verification.observed_at",
        parse_errors,
    )
    settlement_time = _parse_datetime(
        settlement.get("observed_at"),
        "facilitator_settlement.observed_at",
        parse_errors,
    )
    async_time = _parse_datetime(
        async_observation.get("observed_at"),
        "facilitator_async_observation.observed_at",
        parse_errors,
    )
    delivery_time = _parse_datetime(
        delivery.get("observed_at"),
        "resource_delivery.observed_at",
        parse_errors,
    )

    verification_status = _parse_enum(
        X402VerificationStatus,
        verification.get("status"),
        "x402_verification_status_invalid",
        parse_errors,
    )
    settlement_status = _parse_enum(
        X402SettlementStatus,
        settlement.get("status"),
        "x402_settlement_status_invalid",
        parse_errors,
    )
    async_status = _parse_enum(
        X402SettlementStatus,
        async_observation.get("status"),
        "x402_async_status_invalid",
        parse_errors,
    )
    delivery_status = _parse_enum(
        X402DeliveryStatus,
        delivery.get("status"),
        "x402_delivery_status_invalid",
        parse_errors,
    )
    if parse_errors:
        return _empty_adaptation(
            fixture,
            X402AdaptationStatus.INVALID,
            tuple(parse_errors),
        )

    assert requirement_amount is not None
    assert proof_amount is not None
    assert request_time is not None
    assert requirement_time is not None
    assert proof_time is not None
    assert authorization_expires_at is not None
    assert verification_time is not None
    assert settlement_time is not None
    assert async_time is not None
    assert delivery_time is not None
    assert verification_status is not None
    assert settlement_status is not None
    assert async_status is not None
    assert delivery_status is not None

    identifier_errors = _identifier_errors(
        http_request,
        requirement,
        proof,
        verification,
        settlement,
        async_observation,
        delivery,
    )
    expected_digest = compute_requirement_digest(http_request, requirement)
    if requirement["requirement_digest"] != expected_digest:
        identifier_errors.append("x402_requirement_digest_invalid")
    if proof["requirement_digest"] != requirement["requirement_digest"]:
        identifier_errors.append("x402_proof_requirement_digest_mismatch")
    if identifier_errors:
        return _empty_adaptation(
            fixture,
            X402AdaptationStatus.INVALID,
            tuple(identifier_errors),
        )

    delivery_attempts, attempt_errors = _parse_delivery_attempts(
        fixture.get("delivery_attempts", ()),
    )
    if attempt_errors:
        return _empty_adaptation(
            fixture,
            X402AdaptationStatus.INVALID,
            tuple(attempt_errors),
        )

    requirement_id = requirement["requirement_id"]
    resource_ref = requirement["resource_ref"]
    merchant_ref = context["merchant_ref"]
    category = context["category"]
    authority_ref = context["authority_ref"]
    authority_version = context["authority_version"]
    agent_ref = context["agent_ref"]
    asset = requirement["asset"]

    mandate = IntentMandate(
        mandate_id=authority_ref,
        user_id=context["user_ref"],
        max_amount=requirement_amount,
        allowed_merchants=frozenset({merchant_ref}),
        allowed_categories=frozenset({category}),
        expires_at=authorization_expires_at,
        max_count=1,
        expected_agent_id=agent_ref,
        currency=asset,
        authority_version=authority_version,
    )
    order = Order(
        order_id=requirement_id,
        order_version="x402-offline-v1",
        merchant=merchant_ref,
        payee=requirement["payee"],
        items=(
            OrderItem(
                item_id=f"resource:{resource_ref}",
                name=resource_ref,
                category=category,
                quantity=1,
                unit_amount=requirement_amount,
                kind="digital_resource",
            ),
        ),
        total_amount=requirement_amount,
        currency=asset,
        quote_expires_at=authorization_expires_at,
        fulfilment_terms="deliver the bound resource after verified settlement",
        mandate_ref=authority_ref,
        service_id=resource_ref,
        candidate_rails=(scheme, network),
        authority_version_ref=authority_version,
    )
    request = TransactionRequest(
        request_id=proof["request_ref"],
        amount=proof_amount,
        merchant=merchant_ref,
        category=category,
        occurred_at=request_time,
        sequence_count=1,
        agent_id=agent_ref,
        currency=proof["asset"],
        order_ref=proof["requirement_ref"],
        authority_ref=authority_ref,
        authority_version_ref=authority_version,
        payee=proof["payee"],
    )
    payment = PaymentExecutionRecord(
        payment_id=proof["proof_ref"],
        request_id=proof["request_ref"],
        order_id=proof["requirement_ref"],
        status=PaymentStatus.UNKNOWN,
        amount=proof_amount,
        currency=proof["asset"],
        occurred_at=proof_time,
        receipt_ref=proof["proof_ref"],
        provider_ref=settlement["provider_ref"],
        idempotency_key=proof["proof_ref"],
        authority_ref=authority_ref,
        agent_ref=agent_ref,
        transaction_object_ref=proof["request_ref"],
        payee=proof["payee"],
    )
    settlement_observation = PaymentStatusObservation(
        payment_id=settlement["payment_ref"],
        order_id=settlement["original_transaction_ref"],
        status=_payment_status(settlement_status),
        observed_at=settlement_time,
        source="x402.fixture.facilitator_settlement",
        provider_ref=settlement["provider_ref"],
    )
    async_payment_observation = PaymentStatusObservation(
        payment_id=async_observation["payment_ref"],
        order_id=async_observation["original_transaction_ref"],
        status=_payment_status(async_status),
        observed_at=async_time,
        source="x402.fixture.facilitator_async_observation",
        provider_ref=async_observation["provider_ref"],
    )
    resource_delivery = FulfillmentRecord(
        fulfillment_id=delivery["delivery_ref"],
        order_id=requirement_id,
        status=_fulfillment_status(delivery_status),
        occurred_at=delivery_time,
        service_id=delivery["resource_ref"],
        evidence_ref=delivery["proof_ref"],
        failure_code=(
            (delivery.get("failure_code") or "resource_delivery_failed")
            if delivery_status is X402DeliveryStatus.FAILED
            else None
        ),
    )

    protocol_mismatches = _protocol_mismatch_reasons(
        http_request,
        requirement,
        proof,
    )
    source_evidence = _source_evidence(
        http_request,
        requirement,
        proof,
        verification,
        settlement,
        async_observation,
        delivery,
        delivery_attempts,
    )
    return X402Adaptation(
        case_id=fixture["case_id"],
        fixture_version=fixture["fixture_version"],
        status=X402AdaptationStatus.READY,
        reason_codes=(),
        protocol_mismatch_reason_codes=tuple(protocol_mismatches),
        mandate=mandate,
        order=order,
        request=request,
        payment=payment,
        verification_status=verification_status,
        settlement_observation=settlement_observation,
        async_observation=async_payment_observation,
        resource_delivery=resource_delivery,
        delivery_attempts=delivery_attempts,
        source_evidence=source_evidence,
        limitations=_LIMITATIONS,
        side_effects=X402SideEffectRecord(),
    )


_LIMITATIONS = (
    "offline_fixture_only",
    "synthetic_data_only",
    "does_not_verify_cryptographic_signature",
    "does_not_call_facilitator",
    "does_not_create_wallet",
    "does_not_execute_payment",
    "not_official_x402_conformance",
)


def _sections(
    fixture: Mapping[str, Any],
) -> tuple[dict[str, Mapping[str, Any]], tuple[str, ...]]:
    names = (
        "http_request",
        "payment_requirement",
        "payment_proof",
        "facilitator_verification",
        "facilitator_settlement",
        "facilitator_async_observation",
        "resource_delivery",
        "project_context",
    )
    sections: dict[str, Mapping[str, Any]] = {}
    errors: list[str] = []
    for name in names:
        value = fixture.get(name)
        if not isinstance(value, Mapping):
            errors.append(f"x402_section_invalid:{name}")
            sections[name] = {}
        else:
            sections[name] = value
    return sections, tuple(errors)


def _required_text_field_errors(values: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    for path, value in values.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"x402_required_field_missing:{path}")
        elif not isinstance(value, str):
            errors.append(f"x402_string_invalid:{path}")
    return tuple(errors)


def _parse_decimal(value: Any, path: str, errors: list[str]) -> Decimal | None:
    try:
        parsed = _parse_decimal_value(value)
    except (InvalidOperation, TypeError, ValueError):
        errors.append(f"x402_decimal_invalid:{path}")
        return None
    if not parsed.is_finite() or parsed <= 0:
        errors.append(f"x402_decimal_invalid:{path}")
        return None
    return parsed


def _parse_decimal_value(value: Any) -> Decimal:
    if isinstance(value, bool) or isinstance(value, (list, tuple, dict, set)):
        raise TypeError("decimal value has unsupported type")
    if isinstance(value, float):
        raise TypeError("binary float is not accepted")
    return Decimal(str(value))


def _parse_datetime(value: Any, path: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        errors.append(f"x402_datetime_invalid:{path}")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"x402_datetime_invalid:{path}")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"x402_datetime_invalid:{path}")
        return None
    return parsed


def _parse_enum(
    enum_type: type[Enum],
    value: Any,
    reason: str,
    errors: list[str],
) -> Enum | None:
    try:
        return enum_type(value)
    except (TypeError, ValueError):
        errors.append(reason)
        return None


def _identifier_errors(
    http_request: Mapping[str, Any],
    requirement: Mapping[str, Any],
    proof: Mapping[str, Any],
    verification: Mapping[str, Any],
    settlement: Mapping[str, Any],
    async_observation: Mapping[str, Any],
    delivery: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if proof["requirement_ref"] != requirement["requirement_id"]:
        errors.append("x402_requirement_ref_mismatch")
    if proof["request_ref"] != http_request["request_ref"]:
        errors.append("x402_request_ref_mismatch")
    if proof["original_transaction_ref"] != requirement["requirement_id"]:
        errors.append("x402_original_transaction_ref_mismatch")
    if verification["proof_ref"] != proof["proof_ref"]:
        errors.append("x402_verification_proof_ref_mismatch")
    if verification["requirement_ref"] != requirement["requirement_id"]:
        errors.append("x402_verification_requirement_ref_mismatch")
    if settlement["proof_ref"] != proof["proof_ref"]:
        errors.append("x402_settlement_proof_ref_mismatch")
    if settlement["payment_ref"] != proof["proof_ref"]:
        errors.append("x402_settlement_payment_ref_mismatch")
    if settlement["original_transaction_ref"] != requirement["requirement_id"]:
        errors.append("x402_settlement_original_transaction_ref_mismatch")
    if async_observation["payment_ref"] != proof["proof_ref"]:
        errors.append("x402_async_payment_ref_mismatch")
    if async_observation["original_transaction_ref"] != requirement["requirement_id"]:
        errors.append("x402_async_original_transaction_ref_mismatch")
    if async_observation["provider_ref"] != settlement["provider_ref"]:
        errors.append("x402_async_provider_ref_mismatch")
    if delivery["request_ref"] != http_request["request_ref"]:
        errors.append("x402_delivery_request_ref_mismatch")
    if delivery["proof_ref"] != proof["proof_ref"]:
        errors.append("x402_delivery_proof_ref_mismatch")
    return errors


def _parse_delivery_attempts(
    value: Any,
) -> tuple[tuple[X402DeliveryAttempt, ...], tuple[str, ...]]:
    if value in (None, ()):
        return (), ()
    if not isinstance(value, list):
        return (), ("x402_delivery_attempts_invalid",)
    attempts: list[X402DeliveryAttempt] = []
    errors: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            errors.append(f"x402_delivery_attempt_invalid:{index}")
            continue
        text_errors = _required_text_field_errors(
            {
                f"delivery_attempts[{index}].execution_id": item.get("execution_id"),
                f"delivery_attempts[{index}].request_ref": item.get("request_ref"),
                f"delivery_attempts[{index}].resource_ref": item.get("resource_ref"),
                f"delivery_attempts[{index}].proof_ref": item.get("proof_ref"),
                f"delivery_attempts[{index}].status": item.get("status"),
            }
        )
        errors.extend(text_errors)
        if text_errors:
            continue
        try:
            status = FulfillmentStatus(item["status"])
        except (TypeError, ValueError):
            errors.append(f"x402_delivery_attempt_status_invalid:{index}")
            continue
        time_errors: list[str] = []
        observed_at = _parse_datetime(
            item["observed_at"],
            f"delivery_attempts[{index}].observed_at",
            time_errors,
        )
        errors.extend(time_errors)
        if observed_at is None:
            continue
        attempts.append(
            X402DeliveryAttempt(
                execution_id=item["execution_id"],
                request_ref=item["request_ref"],
                resource_ref=item["resource_ref"],
                proof_ref=item["proof_ref"],
                status=status,
                observed_at=observed_at,
            )
        )
    return tuple(attempts), tuple(errors)


def _protocol_mismatch_reasons(
    http_request: Mapping[str, Any],
    requirement: Mapping[str, Any],
    proof: Mapping[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if proof["payee"] != requirement["payee"]:
        reasons.append("x402_payee_mismatch")
    if _parse_decimal_value(proof["amount"]) != _parse_decimal_value(requirement["amount"]):
        reasons.append("x402_amount_mismatch")
    if proof["asset"] != requirement["asset"]:
        reasons.append("x402_asset_mismatch")
    if proof["scheme"] != requirement["scheme"]:
        reasons.append("x402_scheme_mismatch")
    if proof["network"] != requirement["network"]:
        reasons.append("x402_network_mismatch")
    requirement_resource = requirement["resource_ref"]
    request_resource = http_request["resource_ref"]
    proof_resource = proof["resource_ref"]
    if proof_resource != requirement_resource or proof_resource != request_resource:
        reasons.extend(("x402_proof_resource_mismatch", "x402_cross_resource_reuse"))
    if any(reason in reasons for reason in ("x402_scheme_mismatch", "x402_network_mismatch")):
        reasons.append("x402_scheme_or_network_binding_invalid")
    return reasons


def _source_evidence(
    http_request: Mapping[str, Any],
    requirement: Mapping[str, Any],
    proof: Mapping[str, Any],
    verification: Mapping[str, Any],
    settlement: Mapping[str, Any],
    async_observation: Mapping[str, Any],
    delivery: Mapping[str, Any],
    attempts: tuple[X402DeliveryAttempt, ...],
) -> dict[str, object]:
    return {
        "resource": {
            "http_method": http_request["method"].upper(),
            "resource_ref": http_request["resource_ref"],
            "request_ref": http_request["request_ref"],
        },
        "payment_requirement": {
            "requirement_id": requirement["requirement_id"],
            "requirement_digest": requirement["requirement_digest"],
            "scheme": requirement["scheme"],
            "network": requirement["network"],
            "asset": requirement["asset"],
            "amount": str(_parse_decimal_value(requirement["amount"])),
            "payee": requirement["payee"],
            "resource_ref": requirement["resource_ref"],
        },
        "payment_proof": {
            "proof_ref": proof["proof_ref"],
            "requirement_ref": proof["requirement_ref"],
            "requirement_digest": proof["requirement_digest"],
            "request_ref": proof["request_ref"],
            "resource_ref": proof["resource_ref"],
            "scheme": proof["scheme"],
            "network": proof["network"],
            "asset": proof["asset"],
            "amount": str(_parse_decimal_value(proof["amount"])),
            "payee": proof["payee"],
        },
        "facilitator_verification": {
            "status": verification["status"],
            "proof_ref": verification["proof_ref"],
            "requirement_ref": verification["requirement_ref"],
            "observed_at": str(verification["observed_at"]),
        },
        "facilitator_settlement": {
            "status": settlement["status"],
            "payment_ref": settlement["payment_ref"],
            "provider_ref": settlement["provider_ref"],
            "observed_at": str(settlement["observed_at"]),
        },
        "facilitator_async_observation": {
            "status": async_observation["status"],
            "payment_ref": async_observation["payment_ref"],
            "provider_ref": async_observation["provider_ref"],
            "observed_at": str(async_observation["observed_at"]),
        },
        "resource_delivery": {
            "status": delivery["status"],
            "delivery_ref": delivery["delivery_ref"],
            "resource_ref": delivery["resource_ref"],
            "proof_ref": delivery["proof_ref"],
            "observed_at": str(delivery["observed_at"]),
        },
        "delivery_attempts": [attempt.to_dict() for attempt in attempts],
    }


def _payment_status(status: X402SettlementStatus) -> PaymentStatus:
    return PaymentStatus(status.value)


def _fulfillment_status(status: X402DeliveryStatus) -> FulfillmentStatus:
    return FulfillmentStatus(status.value)


def _safe_metadata_text(value: Any) -> str:
    return value if isinstance(value, str) and value.strip() else "UNKNOWN"


def _empty_adaptation(
    fixture: Mapping[str, Any],
    status: X402AdaptationStatus,
    reasons: tuple[str, ...],
) -> X402Adaptation:
    return X402Adaptation(
        case_id=_safe_metadata_text(fixture.get("case_id")),
        fixture_version=_safe_metadata_text(fixture.get("fixture_version")),
        status=status,
        reason_codes=reasons,
        protocol_mismatch_reason_codes=(),
        mandate=None,
        order=None,
        request=None,
        payment=None,
        verification_status=None,
        settlement_observation=None,
        async_observation=None,
        resource_delivery=None,
        delivery_attempts=(),
        source_evidence={},
        limitations=_LIMITATIONS,
        side_effects=X402SideEffectRecord(),
    )

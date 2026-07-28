from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping

from ..models import (
    Decision,
    EvidenceRef,
    IntentMandate,
    TransactionRequest,
    ValidationIssue,
    ValidationResult,
)
from ..validator import validate_request

AP2_VERSION = "v0.2.0-snapshot"
AP2_FLOW_RULE_VERSION = "ap2-flow-v0.2.0-local"


class AP2FlowMode(str, Enum):
    HUMAN_PRESENT = "HUMAN_PRESENT"
    HUMAN_NOT_PRESENT = "HUMAN_NOT_PRESENT"


@dataclass(frozen=True)
class AP2FlowAdaptation:
    mandate: IntentMandate | None
    request: TransactionRequest | None
    protocol_version: str
    flow_mode: AP2FlowMode | None
    realtime_confirmation_required: bool
    realtime_confirmation_satisfied: bool
    preauthorization_present: bool
    trigger_condition_satisfied: bool
    missing_fields: tuple[str, ...]
    flow_errors: tuple[str, ...]
    unmapped_fields: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return (
            self.mandate is not None
            and self.request is not None
            and self.flow_mode is not None
            and not self.missing_fields
            and not self.flow_errors
        )


@dataclass(frozen=True)
class AP2Adaptation:
    """Result of a lightweight AP2 JSON snapshot conversion.

    This adapter does not verify SD-JWT signatures or claim AP2 conformance.
    It only extracts fields needed by the local deterministic experiment.
    """

    mandate: IntentMandate | None
    request: TransactionRequest | None
    protocol_version: str
    missing_fields: tuple[str, ...]
    unmapped_fields: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return self.mandate is not None and self.request is not None and not self.missing_fields


def adapt_ap2_flow_snapshot(snapshot: Mapping[str, Any]) -> AP2FlowAdaptation:
    """Map the minimal AP2 v0.2 HP/HNP sample flow into neutral payment facts.

    The snapshot is already-decoded JSON captured for an offline experiment. This
    function validates structural bindings and extracts only the facts required
    by the local payment validator. It does not verify AP2 cryptographic
    signatures, natural-language intent semantics, or claim protocol conformance.
    """

    intent = _mapping(snapshot.get("intent_mandate"))
    cart = _mapping(snapshot.get("cart_mandate"))
    cart_contents = _mapping(cart.get("contents"))
    payment_request = _mapping(cart_contents.get("payment_request"))
    payment_details = _mapping(payment_request.get("details"))
    cart_total = _mapping(payment_details.get("total"))
    cart_total_amount = _mapping(cart_total.get("amount"))
    payment_mandate = _mapping(snapshot.get("payment_mandate"))
    payment_contents = _mapping(payment_mandate.get("payment_mandate_contents"))
    payment_total = _mapping(payment_contents.get("payment_details_total"))
    payment_total_amount = _mapping(payment_total.get("amount"))
    payment_response = _mapping(payment_contents.get("payment_response"))
    bridge = _mapping(snapshot.get("experiment_context"))
    authorization_evidence = _mapping(snapshot.get("authorization_evidence"))

    missing: list[str] = []
    for path, value in {
        "intent_mandate": intent,
        "cart_mandate.contents": cart_contents,
        "cart_mandate.contents.payment_request.details.id": payment_details.get("id"),
        "cart_mandate.contents.payment_request.details.total.amount.currency": cart_total_amount.get("currency"),
        "cart_mandate.contents.payment_request.details.total.amount.value": cart_total_amount.get("value"),
        "cart_mandate.contents.merchant_name": cart_contents.get("merchant_name"),
        "payment_mandate.payment_mandate_contents": payment_contents,
        "payment_mandate.payment_mandate_contents.payment_mandate_id": payment_contents.get("payment_mandate_id"),
        "payment_mandate.payment_mandate_contents.payment_details_id": payment_contents.get("payment_details_id"),
        "payment_mandate.payment_mandate_contents.payment_details_total.amount.currency": payment_total_amount.get("currency"),
        "payment_mandate.payment_mandate_contents.payment_details_total.amount.value": payment_total_amount.get("value"),
        "payment_mandate.payment_mandate_contents.payment_response.request_id": payment_response.get("request_id"),
        "payment_mandate.payment_mandate_contents.merchant_agent": payment_contents.get("merchant_agent"),
        "payment_mandate.payment_mandate_contents.timestamp": payment_contents.get("timestamp"),
        "intent_mandate.intent_expiry": intent.get("intent_expiry"),
        "experiment_context.user_id": bridge.get("user_id"),
        "experiment_context.category": bridge.get("category"),
    }.items():
        if value in (None, "") or value == {}:
            missing.append(path)

    try:
        flow_mode = AP2FlowMode(str(snapshot.get("flow_mode")))
    except ValueError:
        flow_mode = None
        missing.append("flow_mode")

    intent_confirmation = bool(intent.get("user_cart_confirmation_required", True))
    cart_confirmation = bool(cart_contents.get("user_cart_confirmation_required", True))
    flow_errors: list[str] = []
    if intent and cart_contents and intent_confirmation != cart_confirmation:
        flow_errors.append("intent_cart_confirmation_mismatch")
    if flow_mode is AP2FlowMode.HUMAN_PRESENT and not intent_confirmation:
        flow_errors.append("human_present_requires_realtime_confirmation")
    if flow_mode is AP2FlowMode.HUMAN_NOT_PRESENT and intent_confirmation:
        flow_errors.append("human_not_present_requires_preauthorized_intent")

    cart_payment_id = str(payment_details.get("id") or "")
    payment_details_id = str(payment_contents.get("payment_details_id") or "")
    response_request_id = str(payment_response.get("request_id") or "")
    if cart_payment_id and payment_details_id and cart_payment_id != payment_details_id:
        flow_errors.append("payment_details_id_mismatch")
    if cart_payment_id and response_request_id and cart_payment_id != response_request_id:
        flow_errors.append("payment_response_request_id_mismatch")

    cart_currency = str(cart_total_amount.get("currency") or "")
    payment_currency = str(payment_total_amount.get("currency") or "")
    cart_value = cart_total_amount.get("value")
    payment_value = payment_total_amount.get("value")
    if (
        cart_currency
        and payment_currency
        and cart_value is not None
        and payment_value is not None
        and (
            cart_currency != payment_currency
            or Decimal(str(cart_value)) != Decimal(str(payment_value))
        )
    ):
        flow_errors.append("payment_total_mismatch")

    cart_merchant = str(cart_contents.get("merchant_name") or "")
    payment_merchant = str(payment_contents.get("merchant_agent") or "")
    if cart_merchant and payment_merchant and cart_merchant != payment_merchant:
        flow_errors.append("merchant_binding_mismatch")

    realtime_confirmation_required = intent_confirmation or cart_confirmation
    realtime_confirmation_satisfied = bool(payment_mandate.get("user_authorization"))
    preauthorization_present = bool(authorization_evidence.get("intent_mandate_user_signed"))
    trigger_condition_satisfied = bool(authorization_evidence.get("trigger_condition_satisfied"))

    unmapped = [
        "ap2_cart_payment_hash_binding_not_verified",
        "ap2_merchant_authorization_signature_not_verified",
        "ap2_natural_language_intent_not_machine_verified",
        "ap2_payment_instrument_details_not_mapped",
    ]
    if realtime_confirmation_satisfied:
        unmapped.append("ap2_user_authorization_signature_not_verified")
    if preauthorization_present:
        unmapped.append("ap2_intent_authorization_signature_not_verified")

    if missing or flow_errors:
        return AP2FlowAdaptation(
            mandate=None,
            request=None,
            protocol_version=str(snapshot.get("protocol_version") or AP2_VERSION),
            flow_mode=flow_mode,
            realtime_confirmation_required=realtime_confirmation_required,
            realtime_confirmation_satisfied=realtime_confirmation_satisfied,
            preauthorization_present=preauthorization_present,
            trigger_condition_satisfied=trigger_condition_satisfied,
            missing_fields=tuple(missing),
            flow_errors=tuple(flow_errors),
            unmapped_fields=tuple(sorted(unmapped)),
        )

    allowed_merchants = frozenset(
        str(item) for item in intent.get("merchants", []) if str(item).strip()
    ) or frozenset({cart_merchant})
    amount = Decimal(str(cart_value))
    occurred_at = _parse_datetime(payment_contents["timestamp"])
    mandate = IntentMandate(
        mandate_id=str(payment_contents["payment_mandate_id"]),
        user_id=str(bridge["user_id"]),
        max_amount=amount,
        allowed_merchants=allowed_merchants,
        allowed_categories=frozenset({str(bridge["category"])}),
        expires_at=_parse_datetime(intent["intent_expiry"]),
        max_count=1,
        confirmation_above=None,
        expected_agent_id=bridge.get("agent_id"),
        currency=cart_currency,
    )
    request = TransactionRequest(
        request_id=cart_payment_id,
        amount=amount,
        merchant=cart_merchant,
        category=str(bridge["category"]),
        occurred_at=occurred_at,
        sequence_count=1,
        agent_id=bridge.get("agent_id"),
        currency=cart_currency,
    )
    return AP2FlowAdaptation(
        mandate=mandate,
        request=request,
        protocol_version=str(snapshot.get("protocol_version") or AP2_VERSION),
        flow_mode=flow_mode,
        realtime_confirmation_required=realtime_confirmation_required,
        realtime_confirmation_satisfied=realtime_confirmation_satisfied,
        preauthorization_present=preauthorization_present,
        trigger_condition_satisfied=trigger_condition_satisfied,
        missing_fields=(),
        flow_errors=(),
        unmapped_fields=tuple(sorted(unmapped)),
    )


def evaluate_ap2_flow(adapted: AP2FlowAdaptation) -> ValidationResult:
    """Apply AP2 flow gates, then delegate business rules to the neutral validator."""

    base_limitations = (
        "simulation_only",
        "ap2_crypto_not_verified",
        "not_an_ap2_conformance_test",
        "does_not_execute_real_payment",
    )
    if not adapted.ready or adapted.mandate is None or adapted.request is None:
        reasons = adapted.missing_fields + adapted.flow_errors
        return ValidationResult(
            decision=Decision.INDETERMINATE,
            issues=(
                ValidationIssue(
                    "ap2_flow_invalid",
                    "; ".join(reasons) if reasons else "AP2 flow adaptation is not ready",
                ),
            ),
            evidence=tuple(
                EvidenceRef("ap2_flow_error", "ap2.flow", reason)
                for reason in reasons
            ),
            rule_version=AP2_FLOW_RULE_VERSION,
            limitations=base_limitations,
        )

    if (
        adapted.flow_mode is AP2FlowMode.HUMAN_PRESENT
        and adapted.realtime_confirmation_required
        and not adapted.realtime_confirmation_satisfied
    ):
        return ValidationResult(
            decision=Decision.CONFIRMATION_REQUIRED,
            issues=(
                ValidationIssue(
                    "ap2_user_confirmation_required",
                    "human-present AP2 flow requires user authorization before payment",
                ),
            ),
            evidence=(
                EvidenceRef(
                    "ap2_user_confirmation_required",
                    "payment_mandate.user_authorization",
                    "<missing>",
                    "present user authorization",
                ),
            ),
            rule_version=AP2_FLOW_RULE_VERSION,
            limitations=base_limitations,
        )

    if adapted.flow_mode is AP2FlowMode.HUMAN_NOT_PRESENT:
        if not adapted.preauthorization_present:
            return ValidationResult(
                decision=Decision.INDETERMINATE,
                issues=(
                    ValidationIssue(
                        "ap2_preauthorization_missing",
                        "human-not-present AP2 flow lacks captured user preauthorization evidence",
                    ),
                ),
                evidence=(
                    EvidenceRef(
                        "ap2_preauthorization_missing",
                        "authorization_evidence.intent_mandate_user_signed",
                        "false",
                        "true",
                    ),
                ),
                rule_version=AP2_FLOW_RULE_VERSION,
                limitations=base_limitations,
            )
        if not adapted.trigger_condition_satisfied:
            return ValidationResult(
                decision=Decision.INDETERMINATE,
                issues=(
                    ValidationIssue(
                        "ap2_trigger_condition_not_satisfied",
                        "human-not-present AP2 flow trigger condition is not satisfied",
                    ),
                ),
                evidence=(
                    EvidenceRef(
                        "ap2_trigger_condition_not_satisfied",
                        "authorization_evidence.trigger_condition_satisfied",
                        "false",
                        "true",
                    ),
                ),
                rule_version=AP2_FLOW_RULE_VERSION,
                limitations=base_limitations,
            )

    result = validate_request(adapted.mandate, adapted.request)
    flow_evidence = (
        EvidenceRef(
            "ap2_flow_mode",
            "ap2.flow_mode",
            adapted.flow_mode.value,
        ),
        EvidenceRef(
            "ap2_realtime_confirmation",
            "ap2.realtime_confirmation_satisfied",
            str(adapted.realtime_confirmation_satisfied).lower(),
        ),
        EvidenceRef(
            "ap2_preauthorization",
            "ap2.preauthorization_present",
            str(adapted.preauthorization_present).lower(),
        ),
    )
    return ValidationResult(
        decision=result.decision,
        issues=result.issues,
        evidence=result.evidence + flow_evidence,
        rule_version=AP2_FLOW_RULE_VERSION,
        limitations=tuple(dict.fromkeys(result.limitations + base_limitations)),
        order_differences=result.order_differences,
    )


def adapt_ap2_snapshot(snapshot: Mapping[str, Any]) -> AP2Adaptation:
    """Map an AP2 v0.2-style decoded snapshot into the neutral model.

    Expected top-level objects are open_payment_mandate and
    payment_mandate. The input must already be decoded JSON. Cryptographic
    verification remains an explicit future step and is never simulated here.
    """

    open_mandate = _mapping(snapshot.get("open_payment_mandate"))
    payment_mandate = _mapping(snapshot.get("payment_mandate"))
    bridge = _mapping(snapshot.get("experiment_context"))
    missing: list[str] = []

    if not open_mandate:
        missing.append("open_payment_mandate")
    if not payment_mandate:
        missing.append("payment_mandate")
    if not bridge:
        missing.append("experiment_context")
    if missing:
        return AP2Adaptation(None, None, AP2_VERSION, tuple(missing), ())

    constraints = [item for item in open_mandate.get("constraints", []) if isinstance(item, Mapping)]
    amount_range = _constraint(constraints, "payment.amount_range")
    allowed_payees = _constraint(constraints, "payment.allowed_payees")
    recurrence = _constraint(constraints, "payment.agent_recurrence")
    execution_window = _constraint(constraints, "payment.execution_date")

    max_minor = _first_present(amount_range, "max")
    currency = str(
        _first_present(amount_range, "currency")
        or _nested(payment_mandate, "payment_amount", "currency")
        or bridge.get("currency")
        or ""
    )
    payee = _merchant_identifier(payment_mandate.get("payee"))
    allowed_merchants = {
        merchant
        for merchant in (
            _merchant_identifier(item)
            for item in (allowed_payees.get("allowed", []) if allowed_payees else [])
        )
        if merchant
    }
    if not allowed_merchants and payee:
        allowed_merchants.add(payee)

    expiry = (
        _first_present(execution_window, "not_after")
        or _epoch_to_iso(open_mandate.get("exp"))
        or bridge.get("expires_at")
    )
    request_time = payment_mandate.get("execution_date") or bridge.get("occurred_at")
    request_minor = _nested(payment_mandate, "payment_amount", "value")
    if request_minor is None:
        request_minor = _nested(payment_mandate, "payment_amount", "amount")

    required_values = {
        "experiment_context.mandate_id": bridge.get("mandate_id"),
        "experiment_context.user_id": bridge.get("user_id"),
        "open_payment_mandate.constraints.amount_range.max": max_minor,
        "open_payment_mandate.exp/execution_date.not_after": expiry,
        "payment_mandate.transaction_id": payment_mandate.get("transaction_id"),
        "payment_mandate.payee": payee,
        "payment_mandate.payment_amount": request_minor,
        "payment_mandate.execution_date/experiment_context.occurred_at": request_time,
        "currency": currency,
        "experiment_context.category": bridge.get("category"),
    }
    missing.extend(path for path, value in required_values.items() if value in (None, ""))
    if missing:
        return AP2Adaptation(None, None, AP2_VERSION, tuple(missing), _unmapped_fields(snapshot))

    mandate = IntentMandate(
        mandate_id=str(bridge["mandate_id"]),
        user_id=str(bridge["user_id"]),
        max_amount=_minor_to_decimal(max_minor),
        confirmation_above=(
            _minor_to_decimal(bridge["confirmation_above_minor"])
            if bridge.get("confirmation_above_minor") is not None
            else None
        ),
        allowed_merchants=frozenset(allowed_merchants),
        allowed_categories=frozenset(str(item) for item in bridge.get("allowed_categories", [bridge["category"]])),
        expires_at=_parse_datetime(expiry),
        max_count=int(_first_present(recurrence, "max_occurrences") or bridge.get("max_count") or 1),
        expected_agent_id=bridge.get("agent_id"),
        currency=currency,
    )
    request = TransactionRequest(
        request_id=str(payment_mandate["transaction_id"]),
        amount=_minor_to_decimal(request_minor),
        merchant=payee,
        category=str(bridge["category"]),
        occurred_at=_parse_datetime(request_time),
        sequence_count=int(bridge.get("sequence_count", 1)),
        agent_id=bridge.get("agent_id"),
        currency=currency,
    )
    return AP2Adaptation(
        mandate=mandate,
        request=request,
        protocol_version=str(snapshot.get("protocol_version") or AP2_VERSION),
        missing_fields=(),
        unmapped_fields=_unmapped_fields(snapshot),
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _constraint(constraints: list[Mapping[str, Any]], kind: str) -> Mapping[str, Any]:
    return next((item for item in constraints if item.get("type") == kind), {})


def _first_present(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if mapping.get(key) is not None:
            return mapping[key]
    return None


def _nested(mapping: Mapping[str, Any], first: str, second: str) -> Any:
    child = mapping.get(first)
    return child.get(second) if isinstance(child, Mapping) else None


def _merchant_identifier(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        for key in ("id", "merchant_id", "name"):
            if value.get(key):
                return str(value[key])
    return ""


def _minor_to_decimal(value: Any) -> Decimal:
    return Decimal(str(value)) / Decimal("100")


def _epoch_to_iso(value: Any) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat()


def _parse_datetime(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("AP2 snapshot timestamps must include a timezone")
    return parsed


def _unmapped_fields(snapshot: Mapping[str, Any]) -> tuple[str, ...]:
    known = {"protocol_version", "open_payment_mandate", "payment_mandate", "experiment_context"}
    top_level = [str(key) for key in snapshot if key not in known]
    semantic_gaps = [
        "cnf_and_key_binding_not_verified",
        "sd_jwt_delegation_chain_not_verified",
        "payment_instrument_not_mapped",
        "pisp_not_mapped",
        "risk_data_not_mapped",
        "checkout_reference_not_verified",
        "receipt_not_verified",
    ]
    return tuple(sorted(top_level + semantic_gaps))

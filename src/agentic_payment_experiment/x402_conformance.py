"""Deterministic offline x402 conformance harness.

This module evaluates synthetic fixture observations only.  It deliberately reuses
existing protocol-neutral binding, idempotency, original-transaction, finality,
conflict, and replay facts without changing their algorithms or performing any
network, wallet, signing, settlement, payment, callback, or resource action.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .adapters.x402 import (
    FIXTURE_VERSION,
    X402Adaptation,
    X402AdaptationStatus,
    X402SideEffectRecord,
    X402VerificationStatus,
    adapt_x402_fixture,
)
from .models import Decision, FulfillmentStatus, PaymentStatus
from .payment_finality import derive_payment_query_finality
from .payment_recovery import assess_payment_recovery
from .payment_status_conflict import (
    PaymentStatusConflictResolution,
    derive_payment_status_conflict,
)
from .trusted_execution import (
    ExecutionAttemptFact,
    FollowUpAction,
    ReplayEvent,
    ReplayEventType,
    ReplaySourceType,
    RuntimeGateRecord,
    VerificationStatus,
    check_idempotency,
    replay_events,
    verify_original_transaction,
    verify_payment_execution_binding,
)


class ConformanceOutcome(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    CONFLICT = "CONFLICT"
    INDETERMINATE = "INDETERMINATE"
    UNSUPPORTED = "UNSUPPORTED"


class ConformanceStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class ConformanceCaseResult:
    case_id: str
    status: ConformanceStatus
    expected_outcome: ConformanceOutcome
    actual_outcome: ConformanceOutcome
    reason_codes: tuple[str, ...]
    business_success_confirmed: bool
    duplicate_or_concurrent_reuse: bool
    successful_delivery_count: int
    evidence: dict[str, object]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "status": self.status.value,
            "expected_outcome": self.expected_outcome.value,
            "actual_outcome": self.actual_outcome.value,
            "reason_codes": list(self.reason_codes),
            "business_success_confirmed": self.business_success_confirmed,
            "duplicate_or_concurrent_reuse": self.duplicate_or_concurrent_reuse,
            "successful_delivery_count": self.successful_delivery_count,
            "evidence": self.evidence,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class X402ConformanceReport:
    fixture_version: str
    synthetic_fixtures_only: bool
    results: tuple[ConformanceCaseResult, ...]
    limitations: tuple[str, ...]
    side_effects: X402SideEffectRecord

    def to_dict(self) -> dict[str, object]:
        return {
            "fixture_version": self.fixture_version,
            "synthetic_fixtures_only": self.synthetic_fixtures_only,
            "results": [result.to_dict() for result in self.results],
            "limitations": list(self.limitations),
            "side_effects": self.side_effects.to_dict(),
        }


_REPORT_LIMITATIONS = (
    "offline_fixture_pass_does_not_prove_official_sdk_security",
    "offline_fixture_pass_does_not_prove_facilitator_production_safety",
    "offline_fixture_pass_does_not_prove_merchant_correctness",
    "offline_fixture_pass_does_not_prove_regulatory_compliance",
    "offline_fixture_pass_does_not_prove_mainnet_readiness",
    "offline_fixture_pass_does_not_verify_cryptographic_signatures",
    "offline_fixture_pass_does_not_execute_or_settle_payment",
)


def load_x402_fixture_document(path: str | Path) -> dict[str, object]:
    """Load and validate the root metadata of one synthetic fixture document."""

    parsed = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("x402 fixture document must be a JSON object")
    if parsed.get("fixture_version") != FIXTURE_VERSION:
        raise ValueError("x402 fixture version is unsupported")
    if parsed.get("synthetic") is not True:
        raise ValueError("x402 conformance fixtures must be explicitly synthetic")
    cases = parsed.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("x402 fixture document requires non-empty cases")
    for item in cases:
        if not isinstance(item, dict):
            raise ValueError("x402 fixture cases must be JSON objects")
        item.setdefault("fixture_version", parsed["fixture_version"])
    return parsed


def run_x402_conformance(path: str | Path) -> X402ConformanceReport:
    """Evaluate all fixture cases without performing any external action."""

    document = load_x402_fixture_document(path)
    results = tuple(evaluate_x402_case(case) for case in document["cases"])
    return X402ConformanceReport(
        fixture_version=str(document["fixture_version"]),
        synthetic_fixtures_only=True,
        results=results,
        limitations=_REPORT_LIMITATIONS,
        side_effects=X402SideEffectRecord(),
    )


def evaluate_x402_case(fixture: Mapping[str, Any]) -> ConformanceCaseResult:
    """Evaluate one fixture and compare actual facts with its expected outcome."""

    expected_section = fixture.get("expected")
    if not isinstance(expected_section, Mapping):
        expected_outcome = ConformanceOutcome.INDETERMINATE
        expected_reasons: tuple[str, ...] = ()
        expected_invalid = True
    else:
        try:
            expected_outcome = ConformanceOutcome(str(expected_section.get("outcome")))
            expected_invalid = False
        except ValueError:
            expected_outcome = ConformanceOutcome.INDETERMINATE
            expected_invalid = True
        raw_expected_reasons = expected_section.get("reason_codes", ())
        expected_reasons = (
            tuple(str(item) for item in raw_expected_reasons)
            if isinstance(raw_expected_reasons, list)
            else ()
        )

    adapted = adapt_x402_fixture(fixture)
    evidence: dict[str, object] = dict(adapted.source_evidence)
    reasons: list[str] = list(adapted.reason_codes)
    duplicate = False
    successful_delivery_count = 0
    business_success = False

    if adapted.status is X402AdaptationStatus.UNSUPPORTED:
        actual_outcome = ConformanceOutcome.UNSUPPORTED
        evidence["adapter"] = _adapter_evidence(adapted)
    elif adapted.status is X402AdaptationStatus.INVALID:
        actual_outcome = ConformanceOutcome.BLOCK
        reasons.append("x402_adapter_fail_closed")
        evidence["adapter"] = _adapter_evidence(adapted)
    else:
        actual_outcome, derived_reasons, derived_evidence, duplicate, successful_delivery_count, business_success = _evaluate_ready_adaptation(
            adapted
        )
        reasons.extend(derived_reasons)
        evidence.update(derived_evidence)

    if expected_invalid:
        reasons.append("x402_expected_outcome_invalid")
        status = ConformanceStatus.FAIL
    else:
        missing_expected = tuple(reason for reason in expected_reasons if reason not in reasons)
        if actual_outcome is expected_outcome and not missing_expected:
            status = ConformanceStatus.PASS
        elif actual_outcome is ConformanceOutcome.UNSUPPORTED and expected_outcome is ConformanceOutcome.UNSUPPORTED:
            status = ConformanceStatus.UNSUPPORTED
        else:
            status = ConformanceStatus.FAIL
            if actual_outcome is not expected_outcome:
                reasons.append("x402_expected_outcome_mismatch")
            reasons.extend(f"x402_expected_reason_missing:{reason}" for reason in missing_expected)

    return ConformanceCaseResult(
        case_id=adapted.case_id,
        status=status,
        expected_outcome=expected_outcome,
        actual_outcome=actual_outcome,
        reason_codes=_deduplicate(reasons),
        business_success_confirmed=business_success,
        duplicate_or_concurrent_reuse=duplicate,
        successful_delivery_count=successful_delivery_count,
        evidence=evidence,
        limitations=_REPORT_LIMITATIONS,
    )


def _evaluate_ready_adaptation(
    adapted: X402Adaptation,
) -> tuple[
    ConformanceOutcome,
    tuple[str, ...],
    dict[str, object],
    bool,
    int,
    bool,
]:
    assert adapted.mandate is not None
    assert adapted.order is not None
    assert adapted.request is not None
    assert adapted.payment is not None
    assert adapted.settlement_observation is not None
    assert adapted.async_observation is not None
    assert adapted.resource_delivery is not None
    assert adapted.verification_status is not None

    reasons: list[str] = []
    evidence: dict[str, object] = {
        "adapter": _adapter_evidence(adapted),
    }

    binding = verify_payment_execution_binding(
        adapted.mandate,
        adapted.order,
        adapted.request,
        adapted.payment,
    )
    evidence["payment_binding"] = {
        "status": binding.status.value,
        "reason_codes": list(binding.reason_codes),
        "authority_ref": binding.authority_ref,
        "order_ref": binding.order_ref,
        "request_ref": binding.request_ref,
        "execution_ref": binding.execution_ref,
    }
    if binding.status is not VerificationStatus.VALID:
        reasons.extend(binding.reason_codes)
    reasons.extend(adapted.protocol_mismatch_reason_codes)
    evidence["protocol_binding"] = {
        "status": "VALID" if not adapted.protocol_mismatch_reason_codes else "INVALID",
        "reason_codes": list(adapted.protocol_mismatch_reason_codes),
    }

    duplicate, successful_delivery_count, idempotency_evidence, duplicate_reasons = _evaluate_duplicate_use(
        adapted
    )
    evidence["idempotency"] = idempotency_evidence
    reasons.extend(duplicate_reasons)

    query_binding = verify_original_transaction(
        FollowUpAction.STATUS_QUERY,
        adapted.payment,
        adapted.settlement_observation,
    )
    async_binding = verify_original_transaction(
        FollowUpAction.ASYNC_STATUS_NOTIFICATION,
        adapted.payment,
        adapted.async_observation,
    )
    conflict = derive_payment_status_conflict(
        adapted.payment,
        adapted.settlement_observation,
        adapted.async_observation,
        query_binding,
        async_binding,
    )
    evidence["original_transaction_binding"] = {
        "query": {
            "status": query_binding.status.value,
            "reason_codes": list(query_binding.reason_codes),
        },
        "async": {
            "status": async_binding.status.value,
            "reason_codes": list(async_binding.reason_codes),
        },
    }
    evidence["payment_status_conflict"] = conflict.to_dict()

    recovery = assess_payment_recovery(
        adapted.payment,
        adapted.settlement_observation,
        mandate=adapted.mandate,
        request=adapted.request,
        order=adapted.order,
    )
    finality = derive_payment_query_finality(
        adapted.payment,
        adapted.settlement_observation,
        recovery,
    )
    evidence["payment_query_finality"] = finality.to_dict()

    binding_failed = (
        binding.status is not VerificationStatus.VALID
        or bool(adapted.protocol_mismatch_reason_codes)
    )
    if binding_failed:
        actual_outcome = ConformanceOutcome.BLOCK
        reasons.append("x402_binding_blocked")
    elif duplicate:
        actual_outcome = ConformanceOutcome.BLOCK
    elif adapted.verification_status is X402VerificationStatus.REJECTED:
        actual_outcome = ConformanceOutcome.BLOCK
        reasons.append("x402_facilitator_verification_rejected")
    elif adapted.verification_status is X402VerificationStatus.UNKNOWN:
        actual_outcome = ConformanceOutcome.INDETERMINATE
        reasons.append("x402_facilitator_verification_unknown")
    elif conflict.resolution is PaymentStatusConflictResolution.CONFLICT:
        actual_outcome = ConformanceOutcome.CONFLICT
        reasons.extend(conflict.reason_codes)
    elif conflict.resolution in {
        PaymentStatusConflictResolution.BLOCKED,
        PaymentStatusConflictResolution.UNRESOLVED,
    }:
        actual_outcome = ConformanceOutcome.INDETERMINATE
        reasons.extend(conflict.reason_codes)
    elif (
        adapted.settlement_observation.status is PaymentStatus.SUCCEEDED
        and adapted.resource_delivery.status is FulfillmentStatus.FAILED
    ):
        actual_outcome = ConformanceOutcome.INDETERMINATE
        reasons.append("x402_settlement_succeeded_delivery_failed")
    elif (
        adapted.settlement_observation.status is PaymentStatus.SUCCEEDED
        and adapted.async_observation.status is PaymentStatus.SUCCEEDED
        and adapted.resource_delivery.status is FulfillmentStatus.SUCCEEDED
    ):
        actual_outcome = ConformanceOutcome.ALLOW
        reasons.append("x402_conformance_allow")
    elif adapted.settlement_observation.status is PaymentStatus.FAILED:
        actual_outcome = ConformanceOutcome.BLOCK
        reasons.append("x402_settlement_failed")
    else:
        actual_outcome = ConformanceOutcome.INDETERMINATE
        reasons.append("x402_payment_or_delivery_unresolved")

    if (
        adapted.settlement_observation.status is PaymentStatus.SUCCEEDED
        and adapted.resource_delivery.status is FulfillmentStatus.FAILED
        and "x402_settlement_succeeded_delivery_failed" not in reasons
    ):
        reasons.append("x402_settlement_succeeded_delivery_failed")

    business_success = (
        actual_outcome is ConformanceOutcome.ALLOW
        and not duplicate
        and conflict.effective_status is PaymentStatus.SUCCEEDED
        and adapted.resource_delivery.status is FulfillmentStatus.SUCCEEDED
    )
    replay = _build_replay(adapted, actual_outcome, binding.status, tuple(reasons))
    evidence["replay"] = replay.to_dict()
    return (
        actual_outcome,
        _deduplicate(reasons),
        evidence,
        duplicate,
        successful_delivery_count,
        business_success,
    )


def _evaluate_duplicate_use(
    adapted: X402Adaptation,
) -> tuple[bool, int, dict[str, object], tuple[str, ...]]:
    attempts = adapted.delivery_attempts
    if not attempts:
        successful = int(
            adapted.resource_delivery is not None
            and adapted.resource_delivery.status is FulfillmentStatus.SUCCEEDED
        )
        return (
            False,
            successful,
            {
                "status": "NOT_APPLICABLE",
                "reason_code": "single_delivery_observation",
                "same_key_execution_ids": [],
                "different_key_execution_ids": [],
            },
            (),
        )

    current = attempts[0]
    known = tuple(
        ExecutionAttemptFact(
            execution_id=attempt.execution_id,
            request_id=attempt.request_ref,
            status=attempt.status.value,
            idempotency_key=attempt.proof_ref,
        )
        for attempt in attempts[1:]
    )
    fact = check_idempotency(
        idempotency_key=current.proof_ref,
        request_id=current.request_ref,
        current_execution_id=current.execution_id,
        known_attempts=known,
    )
    duplicate = bool(fact.same_key_execution_ids)
    successful = sum(
        1 for attempt in attempts if attempt.status is FulfillmentStatus.SUCCEEDED
    )
    reasons: list[str] = []
    if duplicate and successful <= 1:
        reasons.append("x402_duplicate_proof_reuse_blocked")
    elif duplicate and successful > 1:
        reasons.append("x402_duplicate_successful_delivery")
    return (
        duplicate,
        successful,
        {
            "status": fact.status.value,
            "reason_code": fact.reason_code,
            "idempotency_key": fact.idempotency_key,
            "same_key_execution_ids": list(fact.same_key_execution_ids),
            "different_key_execution_ids": list(fact.different_key_execution_ids),
            "attempts": [attempt.to_dict() for attempt in attempts],
        },
        tuple(reasons),
    )


def _build_replay(
    adapted: X402Adaptation,
    outcome: ConformanceOutcome,
    binding_status: VerificationStatus,
    reasons: tuple[str, ...],
):
    assert adapted.mandate is not None
    assert adapted.request is not None
    assert adapted.payment is not None
    decision = {
        ConformanceOutcome.ALLOW: Decision.ALLOW,
        ConformanceOutcome.BLOCK: Decision.DENY,
        ConformanceOutcome.CONFLICT: Decision.INDETERMINATE,
        ConformanceOutcome.INDETERMINATE: Decision.INDETERMINATE,
        ConformanceOutcome.UNSUPPORTED: Decision.INDETERMINATE,
    }[outcome]
    recorded_reasons = reasons or ("x402_no_reason_recorded",)
    gate = RuntimeGateRecord(
        preliminary_decision=decision,
        final_decision=decision,
        binding_status=binding_status.value,
        binding_reason_codes=(
            ("payment_execution_binding_match",)
            if binding_status is VerificationStatus.VALID
            else recorded_reasons
        ),
        identity_status="NOT_EVALUATED",
        identity_reason_codes=("x402_fixture_identity_project_context_only",),
        context_policy_status="NOT_EVALUATED",
        context_policy_reason_codes=("x402_fixture_context_policy_not_executed",),
        callback_executed=False,
        callback_count=0,
        callback_result_ref=None,
        reason_codes=recorded_reasons,
    )
    event_types = (
        ReplayEventType.AUTHORITY_RECORDED,
        ReplayEventType.ORDER_RECORDED,
        ReplayEventType.REQUEST_RECORDED,
        ReplayEventType.RUNTIME_DECISION_RECORDED,
        ReplayEventType.PAYMENT_OUTCOME_RECORDED,
    )
    events: list[ReplayEvent] = []
    for index, event_type in enumerate(event_types):
        events.append(
            ReplayEvent(
                event_id=f"{adapted.case_id}:event:{index}",
                event_type=event_type,
                occurred_at=adapted.payment.occurred_at,
                subject_ref=adapted.mandate.user_id,
                agent_ref=adapted.request.agent_id or "agent-reference-missing",
                authority_ref=adapted.mandate.mandate_id,
                transaction_object_ref=adapted.request.request_id,
                payment_ref=adapted.payment.payment_id,
                source_type=ReplaySourceType.SYSTEM_RUNTIME,
                source_ref=f"synthetic-x402-fixture:{adapted.case_id}:{index}",
                decision=decision,
                reason_codes=recorded_reasons,
                previous_event_ref=events[-1].event_id if events else None,
                runtime_gate=(
                    gate
                    if event_type is ReplayEventType.RUNTIME_DECISION_RECORDED
                    else None
                ),
            )
        )
    return replay_events(events)


def _adapter_evidence(adapted: X402Adaptation) -> dict[str, object]:
    return {
        "status": adapted.status.value,
        "reason_codes": list(adapted.reason_codes),
        "protocol_mismatch_reason_codes": list(adapted.protocol_mismatch_reason_codes),
        "limitations": list(adapted.limitations),
        "side_effects": adapted.side_effects.to_dict(),
    }


def _deduplicate(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))

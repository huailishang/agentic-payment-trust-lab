"""Offline, deterministic evidence receipts and replay verification for P5.

The chain is a linked *record* of already observed local facts.  It deliberately
does not sign, hash, persist, or otherwise claim tamper-proof integrity.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Iterable

from ..models import Decision


class ReplayEventType(str, Enum):
    AUTHORITY_RECORDED = "AUTHORITY_RECORDED"
    ORDER_RECORDED = "ORDER_RECORDED"
    REQUEST_RECORDED = "REQUEST_RECORDED"
    RUNTIME_DECISION_RECORDED = "RUNTIME_DECISION_RECORDED"
    PAYMENT_OUTCOME_RECORDED = "PAYMENT_OUTCOME_RECORDED"


class ReplaySourceType(str, Enum):
    USER_CONFIRMED = "USER_CONFIRMED"
    PROTOCOL_VERIFIED = "PROTOCOL_VERIFIED"
    SYSTEM_RUNTIME = "SYSTEM_RUNTIME"
    PAYMENT_PROVIDER_OBSERVED = "PAYMENT_PROVIDER_OBSERVED"


class ReplayStatus(str, Enum):
    VALID = "VALID"
    INDETERMINATE = "INDETERMINATE"
    INVALID = "INVALID"


@dataclass(frozen=True)
class RuntimeGateRecord:
    """Immutable P1-P4 observation captured when the payment gate executes."""

    preliminary_decision: Decision
    final_decision: Decision
    binding_status: str
    binding_reason_codes: tuple[str, ...]
    identity_status: str
    identity_reason_codes: tuple[str, ...]
    context_policy_status: str
    context_policy_reason_codes: tuple[str, ...]
    callback_executed: bool
    callback_count: int
    callback_result_ref: str | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.preliminary_decision, Decision) or not isinstance(self.final_decision, Decision):
            raise ValueError("runtime gate decisions must be closed Decision values")
        if any(not isinstance(value, str) or not value for value in (
            self.binding_status, self.identity_status, self.context_policy_status
        )):
            raise ValueError("runtime gate requires P2/P3/P4 statuses")
        if not isinstance(self.callback_executed, bool):
            raise ValueError("runtime gate callback_executed must be boolean")
        if not isinstance(self.callback_count, int) or self.callback_count < 0:
            raise ValueError("runtime gate callback_count must be a non-negative integer")
        if self.callback_executed != (self.callback_count > 0):
            raise ValueError("runtime gate callback state and count must agree")
        if self.callback_result_ref is not None and (
            not isinstance(self.callback_result_ref, str) or not self.callback_result_ref
        ):
            raise ValueError("runtime gate callback_result_ref must be a non-empty string")
        for codes in (
            self.binding_reason_codes,
            self.identity_reason_codes,
            self.context_policy_reason_codes,
        ):
            if not isinstance(codes, tuple) or any(not isinstance(code, str) or not code for code in codes):
                raise ValueError("runtime gate fact reasons must be non-empty strings")
        if not isinstance(self.reason_codes, tuple) or any(not isinstance(code, str) or not code for code in self.reason_codes):
            raise ValueError("runtime gate reason_codes must be non-empty strings")

    def to_dict(self) -> dict[str, object]:
        return {
            "preliminary_decision": self.preliminary_decision.value,
            "final_decision": self.final_decision.value,
            "binding_status": self.binding_status,
            "binding_reason_codes": list(self.binding_reason_codes),
            "identity_status": self.identity_status,
            "identity_reason_codes": list(self.identity_reason_codes),
            "context_policy_status": self.context_policy_status,
            "context_policy_reason_codes": list(self.context_policy_reason_codes),
            "callback_executed": self.callback_executed,
            "callback_count": self.callback_count,
            "callback_result_ref": self.callback_result_ref,
            "reason_codes": list(self.reason_codes),
        }


_REQUIRED_EVENT_TYPES = frozenset(
    {
        ReplayEventType.AUTHORITY_RECORDED,
        ReplayEventType.ORDER_RECORDED,
        ReplayEventType.REQUEST_RECORDED,
        ReplayEventType.RUNTIME_DECISION_RECORDED,
        ReplayEventType.PAYMENT_OUTCOME_RECORDED,
    }
)


@dataclass(frozen=True)
class ReplayEvent:
    """One serializable receipt event; all cross-event references are explicit."""

    event_id: str
    event_type: ReplayEventType
    occurred_at: datetime
    subject_ref: str
    agent_ref: str
    authority_ref: str
    transaction_object_ref: str
    payment_ref: str
    source_type: ReplaySourceType
    source_ref: str
    decision: Decision
    reason_codes: tuple[str, ...]
    previous_event_ref: str | None = None
    runtime_gate: RuntimeGateRecord | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "event_id",
            "subject_ref",
            "agent_ref",
            "authority_ref",
            "transaction_object_ref",
            "payment_ref",
            "source_ref",
        ):
            if not isinstance(getattr(self, field_name), str) or not getattr(self, field_name).strip():
                raise ValueError(f"replay event requires {field_name}")
        if not isinstance(self.event_type, ReplayEventType):
            raise ValueError("replay event_type is unknown")
        if not isinstance(self.source_type, ReplaySourceType):
            raise ValueError("replay source_type is unknown")
        if not isinstance(self.decision, Decision):
            raise ValueError("replay decision is unknown")
        if not isinstance(self.occurred_at, datetime):
            raise ValueError("replay event requires occurred_at")
        if not isinstance(self.reason_codes, tuple) or any(
            not isinstance(code, str) or not code for code in self.reason_codes
        ):
            raise ValueError("replay reason_codes must be a tuple of non-empty strings")
        if self.previous_event_ref is not None and (
            not isinstance(self.previous_event_ref, str) or not self.previous_event_ref.strip()
        ):
            raise ValueError("previous_event_ref must be a non-empty reference when present")
        if self.event_type is ReplayEventType.RUNTIME_DECISION_RECORDED:
            if self.runtime_gate is None:
                raise ValueError("runtime decision event requires a final runtime gate record")
            if self.decision is not self.runtime_gate.final_decision:
                raise ValueError("runtime decision must match final runtime gate decision")
        elif self.runtime_gate is not None:
            raise ValueError("only runtime decision events may carry a runtime gate record")

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "occurred_at": self.occurred_at.isoformat(),
            "subject_ref": self.subject_ref,
            "agent_ref": self.agent_ref,
            "authority_ref": self.authority_ref,
            "transaction_object_ref": self.transaction_object_ref,
            "payment_ref": self.payment_ref,
            "source_type": self.source_type.value,
            "source_ref": self.source_ref,
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "previous_event_ref": self.previous_event_ref,
            "runtime_gate": self.runtime_gate.to_dict() if self.runtime_gate else None,
        }


@dataclass(frozen=True)
class ReplayResult:
    status: ReplayStatus
    decision: Decision | None
    reason_codes: tuple[str, ...]
    event_count: int
    explanation: str

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "decision": self.decision.value if self.decision is not None else None,
            "reason_codes": list(self.reason_codes),
            "event_count": self.event_count,
            "explanation": self.explanation,
        }


def replay_events(events: Iterable[ReplayEvent]) -> ReplayResult:
    """Verify a P5 receipt chain using only the supplied structured events."""

    chain = tuple(events)
    if not chain:
        return _indeterminate("replay_events_missing")

    event_ids = [event.event_id for event in chain]
    if len(event_ids) != len(set(event_ids)):
        return _invalid("duplicate_event_id")
    if chain[0].previous_event_ref is not None:
        return _invalid("first_event_has_previous_reference")
    for index, event in enumerate(chain[1:], start=1):
        if event.previous_event_ref != chain[index - 1].event_id:
            return _invalid("broken_previous_event_reference")

    reference_fields = (
        "subject_ref",
        "agent_ref",
        "authority_ref",
        "transaction_object_ref",
        "payment_ref",
    )
    for field_name in reference_fields:
        values = {getattr(event, field_name) for event in chain}
        if len(values) != 1:
            return _invalid("reference_mismatch")

    present_types = {event.event_type for event in chain}
    if missing := _REQUIRED_EVENT_TYPES - present_types:
        return _indeterminate(
            "missing_required_event:" + ",".join(sorted(item.value for item in missing))
        )
    decisions = {
        event.decision
        for event in chain
        if event.event_type is ReplayEventType.RUNTIME_DECISION_RECORDED
    }
    if len(decisions) != 1:
        return _indeterminate("missing_or_ambiguous_runtime_decision")
    decision = decisions.pop()
    runtime_event = next(
        event for event in chain if event.event_type is ReplayEventType.RUNTIME_DECISION_RECORDED
    )
    if runtime_event.runtime_gate is None:
        return _indeterminate("runtime_gate_record_missing")
    if runtime_event.runtime_gate.final_decision is not decision:
        return _invalid("runtime_gate_decision_mismatch")
    if not runtime_event.reason_codes:
        return _indeterminate("runtime_decision_reason_codes_missing")
    if decision is Decision.INDETERMINATE:
        return _indeterminate(*runtime_event.reason_codes)
    return ReplayResult(
        status=ReplayStatus.VALID,
        decision=decision,
        reason_codes=runtime_event.reason_codes,
        event_count=len(chain),
        explanation=_decision_explanation(decision),
    )


def _invalid(reason_code: str) -> ReplayResult:
    return ReplayResult(ReplayStatus.INVALID, None, (reason_code,), 0, "链路校验失败；不得放行。")


def _indeterminate(*reason_codes: str) -> ReplayResult:
    return ReplayResult(
        ReplayStatus.INDETERMINATE,
        None,
        tuple(reason_codes),
        0,
        "证据或引用不完整；不能从回放中得出放行结论。",
    )


def _decision_explanation(decision: Decision) -> str:
    return {
        Decision.ALLOW: "记录的运行时决定为 ALLOW。",
        Decision.CONFIRMATION_REQUIRED: "记录的运行时决定要求用户重新确认。",
        Decision.DENY: "记录的运行时决定为 DENY。",
        Decision.INDETERMINATE: "记录的运行时证据不足。",
    }[decision]

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Iterable, Mapping


class ActionOrigin(str, Enum):
    USER_AUTHORITY = "USER_AUTHORITY"
    AGENT_DECISION = "AGENT_DECISION"
    RUNTIME_DECISION = "RUNTIME_DECISION"
    EXTERNAL_FACT = "EXTERNAL_FACT"
    EXECUTION_RESULT = "EXECUTION_RESULT"


class ActionOriginError(ValueError):
    """Raised when an evidence item cannot be mapped by the closed origin contract."""


@dataclass(frozen=True)
class ActionOriginRecord:
    action_origin: ActionOrigin
    action_or_event: str
    evidence_ref: str
    source_namespace: str
    source_type: str
    sequence: int | None = None
    entity_ref: str | None = None
    decision: str | None = None
    status: str | None = None
    reason: str | None = None


_TRACE_ORIGIN_BY_EVENT_ROLE: dict[tuple[str, str], ActionOrigin] = {
    ("AUTHORITY_RECORDED", "AUTHORITY"): ActionOrigin.USER_AUTHORITY,
    ("ORDER_RECORDED", "AUTHORIZED_ORDER_SNAPSHOT"): ActionOrigin.USER_AUTHORITY,
    ("ORDER_RECORDED", "CURRENT_ORDER_SNAPSHOT"): ActionOrigin.EXTERNAL_FACT,
    ("REQUEST_RECORDED", "CURRENT_REQUEST"): ActionOrigin.EXTERNAL_FACT,
    ("ACTION_RECORDED", "GOVERNED_ACTION"): ActionOrigin.AGENT_DECISION,
    ("PAYMENT_CANDIDATE_RECORDED", "CURRENT_PAYMENT_CANDIDATE"): ActionOrigin.EXTERNAL_FACT,
    ("ACTION_BINDING_DECISION_RECORDED", "ACTION_BINDING_FACT"): ActionOrigin.RUNTIME_DECISION,
    ("RUNTIME_DECISION_RECORDED", "RUNTIME_GATE_OBSERVATION"): ActionOrigin.RUNTIME_DECISION,
    ("PAYMENT_OUTCOME_RECORDED", "PAYMENT_EXECUTION_OUTCOME"): ActionOrigin.EXECUTION_RESULT,
    ("FULFILMENT_OUTCOME_RECORDED", "FULFILMENT_OUTCOME"): ActionOrigin.EXECUTION_RESULT,
    ("RECOVERY_OUTCOME_RECORDED", "RECOVERY_OUTCOME"): ActionOrigin.EXECUTION_RESULT,
    ("STATUS_CONFLICT_RECORDED", "STATUS_CONFLICT_FACT"): ActionOrigin.EXTERNAL_FACT,
    ("RESULT_RECORDED", "FINAL_OUTCOME"): ActionOrigin.EXECUTION_RESULT,
    ("REMEDIATION_OBSERVATION_RECORDED", "REMEDIATION_OBSERVATION"): ActionOrigin.EXTERNAL_FACT,
    ("ORIGINAL_TRANSACTION_BINDING_RECORDED", "ORIGINAL_TRANSACTION_BINDING_FACT"): ActionOrigin.RUNTIME_DECISION,
    ("REMEDIATION_CLOSURE_RECORDED", "REMEDIATION_CLOSURE_OUTCOME"): ActionOrigin.EXECUTION_RESULT,
}


def _require_mapping(value: object, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ActionOriginError(f"{label} must be a mapping")
    return value


def _require_text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ActionOriginError(f"{label} must be a non-empty string")
    return value


def _optional_text(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def classify_trace_event_origin(event: Mapping[str, Any]) -> ActionOrigin:
    item = _require_mapping(event, label="trace event")
    event_type = _require_text(item.get("event_type"), label="event_type")
    entity_role = _require_text(item.get("entity_role"), label="entity_role")
    try:
        return _TRACE_ORIGIN_BY_EVENT_ROLE[(event_type, entity_role)]
    except KeyError as exc:
        raise ActionOriginError(
            f"unmapped trace event/role: event_type={event_type!r} entity_role={entity_role!r}"
        ) from exc


def project_autonomous_behavior_origins(
    behavior: Mapping[str, Any],
) -> tuple[ActionOriginRecord, ...]:
    payload = _require_mapping(behavior, label="autonomous behavior")
    runs = payload.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ActionOriginError("autonomous behavior runs[0] is required")
    run0 = _require_mapping(runs[0], label="runs[0]")
    steps = run0.get("steps")
    if not isinstance(steps, list):
        raise ActionOriginError("runs[0].steps must be a list")

    records: list[ActionOriginRecord] = []
    for index, raw_step in enumerate(steps):
        step = _require_mapping(raw_step, label=f"runs[0].steps[{index}]")
        chosen_action = _require_text(
            step.get("chosen_action"), label=f"runs[0].steps[{index}].chosen_action"
        )
        records.append(
            ActionOriginRecord(
                action_origin=ActionOrigin.AGENT_DECISION,
                action_or_event=chosen_action,
                evidence_ref=f"autonomous_behavior:runs[0].steps[{index}].chosen_action",
                source_namespace="autonomous_behavior",
                source_type=_optional_text(step.get("source")) or "AUTONOMOUS_BEHAVIOR_STEP",
                sequence=_optional_int(step.get("sequence")),
                reason=_optional_text(step.get("reason_summary")),
            )
        )
    return tuple(records)


def _trace_action_or_event(event_type: str, entity_role: str) -> str:
    if event_type == "ORDER_RECORDED":
        return f"{event_type}:{entity_role}"
    return event_type


def project_authoritative_trace_origins(
    trace: Mapping[str, Any],
) -> tuple[ActionOriginRecord, ...]:
    payload = _require_mapping(trace, label="authoritative trace")
    events = payload.get("events")
    if not isinstance(events, list):
        raise ActionOriginError("authoritative trace events must be a list")

    records: list[ActionOriginRecord] = []
    for index, raw_event in enumerate(events):
        event = _require_mapping(raw_event, label=f"events[{index}]")
        event_type = _require_text(event.get("event_type"), label=f"events[{index}].event_type")
        entity_role = _require_text(event.get("entity_role"), label=f"events[{index}].entity_role")
        origin = classify_trace_event_origin(event)
        records.append(
            ActionOriginRecord(
                action_origin=origin,
                action_or_event=_trace_action_or_event(event_type, entity_role),
                evidence_ref=f"authoritative_trace:events[{index}]",
                source_namespace="authoritative_trace",
                source_type=_optional_text(event.get("entity_type")) or event_type,
                sequence=_optional_int(event.get("sequence_no")),
                entity_ref=_optional_text(event.get("entity_ref")),
                decision=_optional_text(event.get("decision")),
                status=_optional_text(event.get("status")),
                reason=_optional_text(event.get("reason")),
            )
        )
    return tuple(records)


def action_origin_records_to_primitive(
    records: Iterable[ActionOriginRecord],
) -> list[dict[str, object]]:
    primitive: list[dict[str, object]] = []
    for record in records:
        if not isinstance(record, ActionOriginRecord):
            raise ActionOriginError("records must contain only ActionOriginRecord values")
        item = asdict(record)
        item["action_origin"] = record.action_origin.value
        primitive.append(item)
    return primitive

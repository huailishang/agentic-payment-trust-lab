"""Read-only consumer for validated product authoritative traces.

This module is deliberately protocol-neutral.  It validates the frozen public
trace contract first, then mechanically projects already-recorded trace facts
into an immutable UI-neutral read model.  It never reconstructs business facts
or invokes product/runtime decision logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .authoritative_trace import (
    ProductAuthoritativeTrace,
    TraceValidationStatus,
    canonical_json_bytes,
    canonical_primitive,
    canonical_sha256,
    validate_product_authoritative_trace,
)


class TraceConsumerStatus(str, Enum):
    """Closed consumer outcome independent of product-family semantics."""

    AVAILABLE = "AVAILABLE"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class TraceReadBindingAssertion:
    source_path: str
    target_path: str
    source_value: Any = None
    target_value: Any = None
    equal: bool | None = None


@dataclass(frozen=True)
class TraceReadRelation:
    relation_type: str
    target_entity_type: str
    target_entity_role: str
    target_entity_ref: str
    target_binding_assertions: tuple[TraceReadBindingAssertion, ...] = ()
    target_resolved: bool | None = None


@dataclass(frozen=True)
class TraceReadEvent:
    sequence_no: int
    event_type: str
    entity_type: str
    entity_role: str
    entity_ref: str
    source_binding_ref: str
    decision: str | None = None
    status: str | None = None
    reason_codes: tuple[str, ...] = ()
    relations: tuple[TraceReadRelation, ...] = ()


@dataclass(frozen=True)
class TraceReadSourceBinding:
    binding_ref: str
    source_object_type: str
    source_object_ref: str
    projection_schema: str
    projection: Mapping[str, Any]


@dataclass(frozen=True)
class AuthoritativeTraceReadModel:
    trace_ref: str
    profile: str
    schema_version: str
    source: str
    completeness_status: str
    reason_codes: tuple[str, ...]
    events: tuple[TraceReadEvent, ...]
    source_bindings: tuple[TraceReadSourceBinding, ...]


@dataclass(frozen=True)
class TraceConsumeResult:
    status: TraceConsumerStatus
    validation_status: TraceValidationStatus
    reason_codes: tuple[str, ...]
    read_model: AuthoritativeTraceReadModel | None


def _project_assertion(assertion: Any) -> TraceReadBindingAssertion:
    return TraceReadBindingAssertion(
        source_path=assertion.source_path,
        target_path=assertion.target_path,
        source_value=assertion.source_value,
        target_value=assertion.target_value,
        equal=assertion.equal,
    )


def _project_relation(relation: Any) -> TraceReadRelation:
    return TraceReadRelation(
        relation_type=relation.relation_type,
        target_entity_type=relation.target_entity_type,
        target_entity_role=relation.target_entity_role,
        target_entity_ref=relation.target_entity_ref,
        target_binding_assertions=tuple(
            _project_assertion(assertion)
            for assertion in relation.target_binding_assertions
        ),
        target_resolved=relation.target_resolved,
    )


def _project_event(event: Any) -> TraceReadEvent:
    return TraceReadEvent(
        sequence_no=event.sequence_no,
        event_type=event.event_type,
        entity_type=event.entity_type,
        entity_role=event.entity_role,
        entity_ref=event.entity_ref,
        source_binding_ref=event.source_binding_ref,
        decision=event.decision,
        status=event.status,
        reason_codes=event.reason_codes,
        relations=tuple(_project_relation(relation) for relation in event.relations),
    )


def _project_source_binding(binding: Any) -> TraceReadSourceBinding:
    return TraceReadSourceBinding(
        binding_ref=binding.binding_ref,
        source_object_type=binding.source_object_type,
        source_object_ref=binding.source_object_ref,
        projection_schema=binding.projection_schema,
        projection=binding.projection,
    )


def consume_authoritative_trace(trace: object) -> TraceConsumeResult:
    """Validate one trace and expose a normal read model only when it is VALID."""

    validation = validate_product_authoritative_trace(trace)
    if validation.status is not TraceValidationStatus.VALID:
        return TraceConsumeResult(
            status=TraceConsumerStatus.REJECTED,
            validation_status=validation.status,
            reason_codes=validation.reason_codes,
            read_model=None,
        )

    # The public validator can return VALID only for this closed contract type.
    assert isinstance(trace, ProductAuthoritativeTrace)
    read_model = AuthoritativeTraceReadModel(
        trace_ref=trace.trace_ref,
        profile=trace.profile,
        schema_version=trace.schema_version,
        source=trace.source,
        completeness_status=trace.completeness_status,
        reason_codes=trace.reason_codes,
        events=tuple(_project_event(event) for event in trace.events),
        source_bindings=tuple(
            _project_source_binding(binding) for binding in trace.source_bindings
        ),
    )
    return TraceConsumeResult(
        status=TraceConsumerStatus.AVAILABLE,
        validation_status=validation.status,
        reason_codes=validation.reason_codes,
        read_model=read_model,
    )


def trace_read_model_to_primitive(read_model: AuthoritativeTraceReadModel) -> dict[str, Any]:
    """Return a deterministic primitive representation suitable for later UI use."""

    value = {
        "trace_ref": read_model.trace_ref,
        "profile": read_model.profile,
        "schema_version": read_model.schema_version,
        "source": read_model.source,
        "completeness_status": read_model.completeness_status,
        "reason_codes": read_model.reason_codes,
        "events": [
            {
                "sequence_no": event.sequence_no,
                "event_type": event.event_type,
                "entity_type": event.entity_type,
                "entity_role": event.entity_role,
                "entity_ref": event.entity_ref,
                "source_binding_ref": event.source_binding_ref,
                "decision": event.decision,
                "status": event.status,
                "reason_codes": event.reason_codes,
                "relations": [
                    {
                        "relation_type": relation.relation_type,
                        "target_entity_type": relation.target_entity_type,
                        "target_entity_role": relation.target_entity_role,
                        "target_entity_ref": relation.target_entity_ref,
                        "target_resolved": relation.target_resolved,
                        "target_binding_assertions": [
                            {
                                "source_path": assertion.source_path,
                                "target_path": assertion.target_path,
                                "source_value": assertion.source_value,
                                "target_value": assertion.target_value,
                                "equal": assertion.equal,
                            }
                            for assertion in relation.target_binding_assertions
                        ],
                    }
                    for relation in event.relations
                ],
            }
            for event in read_model.events
        ],
        "source_bindings": [
            {
                "binding_ref": binding.binding_ref,
                "source_object_type": binding.source_object_type,
                "source_object_ref": binding.source_object_ref,
                "projection_schema": binding.projection_schema,
                "projection": binding.projection,
            }
            for binding in read_model.source_bindings
        ],
    }
    primitive = canonical_primitive(value)
    assert isinstance(primitive, dict)
    return primitive


def trace_read_model_json_bytes(read_model: AuthoritativeTraceReadModel) -> bytes:
    """Serialize the read model with the authoritative canonical JSON rules."""

    return canonical_json_bytes(trace_read_model_to_primitive(read_model))


def trace_read_model_sha256(read_model: AuthoritativeTraceReadModel) -> str:
    """Return a stable canonical digest for repeatability checks."""

    return canonical_sha256(trace_read_model_to_primitive(read_model))


__all__ = [
    "AuthoritativeTraceReadModel",
    "TraceConsumeResult",
    "TraceConsumerStatus",
    "TraceReadBindingAssertion",
    "TraceReadEvent",
    "TraceReadRelation",
    "TraceReadSourceBinding",
    "consume_authoritative_trace",
    "trace_read_model_json_bytes",
    "trace_read_model_sha256",
    "trace_read_model_to_primitive",
]

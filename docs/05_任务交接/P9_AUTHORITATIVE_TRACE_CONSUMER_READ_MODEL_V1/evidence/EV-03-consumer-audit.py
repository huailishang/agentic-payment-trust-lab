from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
for entry in (ROOT, ROOT / "src"):
    sys.path.insert(0, str(entry))

from agentic_payment_experiment.authoritative_trace import TraceValidationStatus
from agentic_payment_experiment.authoritative_trace_consumer import (
    TraceConsumerStatus,
    consume_authoritative_trace,
    trace_read_model_sha256,
    trace_read_model_to_primitive,
)
from agentic_payment_experiment.webshop_prepayment_trace_profiles import (
    PrepaymentScenarioKind,
)
from tests import test_attack_overlay_trace_toolkit as attack_tests
from tests import test_webshop_prepayment_trace_toolkit as prepayment_tests
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01

EXPECTED_TRACE_HASHES = {
    "T01": "7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906",
    "T02": "fb1a79d73931f3e0bb87eafeffdaffe4004add137998d107ea425554605be624",
    "T10": "2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3",
}


def primitive(value: object) -> object:
    if is_dataclass(value):
        return {field.name: primitive(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): primitive(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [primitive(item) for item in value]
    if isinstance(value, Enum):
        return primitive(value.value)
    if isinstance(value, Decimal):
        text = format(value, "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return "0" if text in {"", "-0"} else text
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or isinstance(value, (bool, int, str)):
        return value
    raise TypeError(type(value))


def digest(value: object) -> str:
    raw = json.dumps(
        primitive(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def representative_traces() -> dict[str, object]:
    *_, t01_outcome = _valid_t01()
    assert t01_outcome.authoritative_trace is not None

    prepayment = prepayment_tests.WebShopPrepaymentTraceToolkitTest(methodName="runTest")
    prepayment.setUp()
    *_, t02_trace = prepayment.build_case(PrepaymentScenarioKind.PRICE_INCREASE)
    assert t02_trace is not None

    overlay = attack_tests.AttackOverlayTraceToolkitTest(methodName="runTest")
    overlay.setUp()
    t07_result = overlay.evaluate(
        "request.amount",
        attack_id="CONSUMER-EV-T07",
        title="consumer evidence",
        source_ref="consumer-evidence-source",
    )
    assert t07_result.authoritative_trace is not None

    _, _, t10_outcome, _ = _valid_t10()
    assert t10_outcome.authoritative_trace is not None

    return {
        "T01": t01_outcome.authoritative_trace,
        "T02": t02_trace,
        "T07": t07_result.authoritative_trace,
        "T10": t10_outcome.authoritative_trace,
    }


def main() -> None:
    traces = representative_traces()
    results: dict[str, object] = {}
    for task_id, trace in traces.items():
        consumed = consume_authoritative_trace(trace)
        assert consumed.status is TraceConsumerStatus.AVAILABLE
        assert consumed.validation_status is TraceValidationStatus.VALID
        model = consumed.read_model
        assert model is not None

        assert len(model.events) == len(trace.events)
        assert len(model.source_bindings) == len(trace.source_bindings)
        read_bindings = {binding.binding_ref: binding for binding in model.source_bindings}
        source_bindings = {binding.binding_ref: binding for binding in trace.source_bindings}
        assert set(read_bindings) == set(source_bindings)

        relation_count = 0
        assertion_count = 0
        for source_event, read_event in zip(trace.events, model.events):
            assert source_event.sequence_no == read_event.sequence_no
            assert source_event.event_type == read_event.event_type
            assert source_event.entity_type == read_event.entity_type
            assert source_event.entity_role == read_event.entity_role
            assert source_event.entity_ref == read_event.entity_ref
            assert source_event.source_binding_ref == read_event.source_binding_ref
            assert source_event.decision == read_event.decision
            assert source_event.status == read_event.status
            assert source_event.reason_codes == read_event.reason_codes
            assert read_event.source_binding_ref in read_bindings
            assert len(source_event.relations) == len(read_event.relations)
            for source_relation, read_relation in zip(source_event.relations, read_event.relations):
                relation_count += 1
                assert source_relation.relation_type == read_relation.relation_type
                assert source_relation.target_entity_type == read_relation.target_entity_type
                assert source_relation.target_entity_role == read_relation.target_entity_role
                assert source_relation.target_entity_ref == read_relation.target_entity_ref
                assert source_relation.target_resolved == read_relation.target_resolved
                assert len(source_relation.target_binding_assertions) == len(
                    read_relation.target_binding_assertions
                )
                for source_assertion, read_assertion in zip(
                    source_relation.target_binding_assertions,
                    read_relation.target_binding_assertions,
                ):
                    assertion_count += 1
                    assert primitive(source_assertion) == primitive(read_assertion)

        for ref, source_binding in source_bindings.items():
            read_binding = read_bindings[ref]
            assert source_binding.source_object_type == read_binding.source_object_type
            assert source_binding.source_object_ref == read_binding.source_object_ref
            assert source_binding.projection_schema == read_binding.projection_schema
            assert source_binding.projection == read_binding.projection

        repeat_sha = []
        for _ in range(3):
            repeated = consume_authoritative_trace(trace)
            assert repeated.status is TraceConsumerStatus.AVAILABLE
            assert repeated.read_model is not None
            repeat_sha.append(trace_read_model_sha256(repeated.read_model))
        assert len(set(repeat_sha)) == 1

        source_trace_sha = digest(trace)
        if task_id in EXPECTED_TRACE_HASHES:
            assert source_trace_sha == EXPECTED_TRACE_HASHES[task_id]
        results[task_id] = {
            "profile": trace.profile,
            "source_trace_sha256": source_trace_sha,
            "event_count": len(model.events),
            "source_binding_count": len(model.source_bindings),
            "relation_count": relation_count,
            "binding_assertion_count": assertion_count,
            "read_model_sha256_x3": repeat_sha,
            "primitive_top_level_keys": sorted(trace_read_model_to_primitive(model)),
            "consumer_status": consumed.status.value,
            "validation_status": consumed.validation_status.value,
        }

    print(json.dumps({"consumer_ready": "4/4", "families": results}, ensure_ascii=False, indent=2))
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

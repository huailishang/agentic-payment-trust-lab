from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from agentic_payment_experiment import PaymentStatus
from agentic_payment_experiment.authoritative_trace import (
    TraceValidationStatus,
    compute_binding_ref,
    validate_product_authoritative_trace,
)
from tests import test_webshop_runtime_gate as runtime_gate_tests


OUTPUT = Path(__file__).resolve().parent / "EV-04-t10-product-trace.json"
EXPECTED_EVENT_TYPES = (
    "AUTHORITY_RECORDED",
    "ORDER_RECORDED",
    "ORDER_RECORDED",
    "REQUEST_RECORDED",
    "ACTION_RECORDED",
    "PAYMENT_CANDIDATE_RECORDED",
    "ACTION_BINDING_DECISION_RECORDED",
    "PAYMENT_OUTCOME_RECORDED",
    "KNOWN_PAYMENT_PREFLIGHT_RECORDED",
    "PREPAYMENT_DECISION_RECORDED",
    "RUNTIME_DECISION_RECORDED",
    "RESULT_RECORDED",
)
EXPECTED_ROLES = (
    "AUTHORITY",
    "AUTHORIZED_ORDER_SNAPSHOT",
    "CURRENT_ORDER_SNAPSHOT",
    "CURRENT_REQUEST",
    "GOVERNED_ACTION",
    "CURRENT_PAYMENT_CANDIDATE",
    "ACTION_BINDING_FACT",
    "HISTORICAL_SUCCEEDED_PAYMENT",
    "KNOWN_PAYMENT_PREFLIGHT_FACT",
    "PREPAYMENT_VALIDATION",
    "RUNTIME_GATE_OBSERVATION",
    "FINAL_OUTCOME",
)


def thaw(value: Any) -> Any:
    if isinstance(value, dict) or hasattr(value, "items"):
        return {str(key): thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw(item) for item in value]
    return value


def case() -> runtime_gate_tests.WebShopRuntimeGateTest:
    item = runtime_gate_tests.WebShopRuntimeGateTest(methodName="runTest")
    item.setUp()
    return item


def build_once():
    item = case()
    historical = replace(
        item.execution,
        payment_id="webshop-payment-existing-success",
        status=PaymentStatus.SUCCEEDED,
    )
    outcome, calls = item.invoke(
        governed_action=item.governed_action,
        known_payment_attempts=(historical,),
    )
    assert calls == []
    assert outcome.callback_count == 0
    assert outcome.authoritative_trace is not None
    return item, historical, outcome


item, historical, outcome = build_once()
trace = outcome.authoritative_trace
assert trace is not None
validation = validate_product_authoritative_trace(trace)
assert validation.status is TraceValidationStatus.VALID
assert tuple(event.event_type for event in trace.events) == EXPECTED_EVENT_TYPES
assert tuple(event.entity_role for event in trace.events) == EXPECTED_ROLES
assert len(trace.events) == 12
assert len(trace.source_bindings) == 11
assert len({binding.binding_ref for binding in trace.source_bindings}) == 11

binding_by_ref = {binding.binding_ref: binding for binding in trace.source_bindings}
for binding in trace.source_bindings:
    assert compute_binding_ref(binding) == binding.binding_ref
for event in trace.events:
    assert event.source_binding_ref in binding_by_ref
    for relation in event.relations:
        assert relation.target_resolved is True
        assert any(
            target.entity_type == relation.target_entity_type
            and target.entity_role == relation.target_entity_role
            and target.entity_ref == relation.target_entity_ref
            for target in trace.events
        )

authorized_order_event = trace.events[1]
current_order_event = trace.events[2]
current_payment_event = trace.events[5]
historical_payment_event = trace.events[7]
known_attempt_event = trace.events[8]
final_event = trace.events[11]

assert authorized_order_event.source_binding_ref == current_order_event.source_binding_ref
assert current_payment_event.source_binding_ref != historical_payment_event.source_binding_ref
assert current_payment_event.entity_ref.endswith(item.execution.payment_id)
assert historical_payment_event.entity_ref.endswith(historical.payment_id)
assert current_payment_event.status == "PENDING"
assert historical_payment_event.status == "SUCCEEDED"
assert known_attempt_event.status == "BLOCKED"
assert trace.events[9].decision == "DENY"
assert trace.events[10].decision == "DENY"
assert final_event.decision == "DENY"

final_binding = binding_by_ref[final_event.source_binding_ref]
assert "authoritative_trace" not in final_binding.projection
assert set(final_binding.projection) == {
    "decision",
    "checkout_executed",
    "callback_count",
    "callback_result_ref",
    "reason_codes",
    "limitations",
}

second_item, second_historical, second_outcome = build_once()
assert second_historical == historical
assert second_outcome.authoritative_trace == trace
assert second_outcome.callback_count == 0
assert second_item.execution == item.execution

extra_historical = replace(
    historical,
    payment_id="webshop-payment-existing-success-2",
)
ambiguous_outcome, ambiguous_calls = item.invoke(
    governed_action=item.governed_action,
    known_payment_attempts=(historical, extra_historical),
)
assert ambiguous_calls == []
assert ambiguous_outcome.callback_count == 0
assert ambiguous_outcome.authoritative_trace is None

payload = {
    "schema": "t10-product-authoritative-trace-evidence/v1",
    "validation": {
        "status": validation.status.value,
        "reason_codes": list(validation.reason_codes),
        "profile": validation.profile,
    },
    "outcome": {
        "decision": outcome.decision.value,
        "callback_count": outcome.callback_count,
        "checkout_executed": outcome.checkout_executed,
        "reason_codes": list(outcome.reason_codes),
    },
    "trace": {
        "schema_version": trace.schema_version,
        "source": trace.source,
        "profile": trace.profile,
        "trace_ref": trace.trace_ref,
        "completeness_status": trace.completeness_status,
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
                "reason_codes": list(event.reason_codes),
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
                                "source_value": thaw(assertion.source_value),
                                "target_value": thaw(assertion.target_value),
                                "equal": assertion.equal,
                            }
                            for assertion in relation.target_binding_assertions
                        ],
                    }
                    for relation in event.relations
                ],
            }
            for event in trace.events
        ],
        "source_bindings": [
            {
                "binding_ref": binding.binding_ref,
                "source_object_type": binding.source_object_type,
                "source_object_ref": binding.source_object_ref,
                "projection_schema": binding.projection_schema,
                "projection": thaw(binding.projection),
                "recomputed_binding_ref": compute_binding_ref(binding),
            }
            for binding in trace.source_bindings
        ],
    },
    "invariants": {
        "events": 12,
        "unique_bindings": 11,
        "order_roles_share_binding": True,
        "current_and_historical_payment_distinct": True,
        "all_relations_resolved": True,
        "result_projection_excludes_trace": True,
        "repeat_build_identical": True,
        "ambiguous_history_fails_closed": True,
        "callback_count": 0,
    },
}
OUTPUT.write_text(
    json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    encoding="utf-8",
)
print(f"output={OUTPUT.relative_to(ROOT).as_posix()}")
print(f"output_sha256={hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}")
print("validation=VALID")
print("events=12")
print("unique_bindings=11")
print("order_roles_share_binding=true")
print("current_and_historical_payment_distinct=true")
print("all_relations_resolved=true")
print("result_projection_excludes_trace=true")
print("repeat_build_identical=true")
print("ambiguous_history_fails_closed=true")
print("callback_count=0")
print("RESULT=PASS")

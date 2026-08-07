from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import fields, is_dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from collections.abc import Mapping

ROOT = Path(__file__).resolve().parents[4]
for item in (ROOT, ROOT / "src"):
    sys.path.insert(0, str(item))

from agentic_payment_experiment.authoritative_trace import (
    TraceValidationStatus,
    runtime_registry_hashes,
    validate_product_authoritative_trace,
)
from agentic_payment_experiment.models import (
    FulfillmentStatus,
    PaymentRecoveryStatus,
    PaymentStatus,
    RemediationStatus,
    TaskStatus,
)
from agentic_payment_experiment.webshop_unknown_payment_authoritative_trace import (
    build_unknown_payment_recovery_trace,
)
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_unknown_payment_authoritative_trace import _valid_t09
from tests.test_webshop_payment_sidecar import WebShopPaymentSidecarTest

EVID = Path(__file__).resolve().parent
BASELINE = EVID / "RV-EV-03-after-baseline.json"


def primitive(value: object) -> object:
    if is_dataclass(value):
        return {f.name: primitive(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): primitive(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [primitive(v) for v in value]
    if isinstance(value, Enum):
        return primitive(value.value)
    if isinstance(value, Decimal):
        text = format(value, "f").rstrip("0").rstrip(".")
        return text or "0"
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(type(value))


def digest(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def non_trace_projection(report: dict[str, object]) -> list[dict[str, object]]:
    keep = (
        "actual_decision", "actual_callback_count", "actual_callback_observations",
        "actual_retry_count", "actual_final_environment_state", "actual_reason_codes",
        "known_payment_attempt_preflight_status", "known_payment_attempt_preflight_reason_codes",
        "known_payment_attempt_preflight_blocking_request_refs", "binding_status",
        "lineage_status", "effective_source_types", "required_facts_observed",
        "forbidden_side_effects", "limitations",
    )
    by_id = {item["task_id"]: item for item in report["task_results"]}
    return [
        {"task_id": task_id, "actual": {key: by_id[task_id]["actual"].get(key) for key in keep}}
        for task_id in sorted(by_id)
    ]


def main() -> None:
    report = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert file_digest(BASELINE) == "a38b2d91bc6e636201c9ab94c4bced1ad6653dadffb32811cb996d7ab0141086"
    assert report["repeatability"]["all_identical"] is True
    assert report["repeatability"]["normalized_sha256"] == [
        "ee99b8bf73092ef09d0b890d74b66323963bebf10c1a1b4cecf2f5cbc32d8399"
    ] * 3
    assert report["metrics"]["product_observed_authoritative_trace_completeness_rate"] == {
        "count": 3, "denominator": 12, "rate": "0.250000"
    }
    assert report["metrics"]["governed_end_to_end_task_success_rate"] == {
        "count": 2, "denominator": 12, "rate": "0.166667"
    }
    by_id = {item["task_id"]: item for item in report["task_results"]}
    valid_tasks = sorted(
        task_id for task_id, item in by_id.items()
        if item["actual"]["product_observed_trace_status"] == "VALID"
    )
    assert valid_tasks == ["T01", "T09", "T10"]
    assert by_id["T09"]["matched"] is True and by_id["T09"]["capability_gaps"] == []
    assert digest(non_trace_projection(report)) == "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"

    case, gate, candidate, _, _, _, outcome = _valid_t09()
    trace = outcome.authoritative_trace
    assert trace is not None
    validation = validate_product_authoritative_trace(trace)
    assert validation.status is TraceValidationStatus.VALID
    assert trace.profile == "WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2"
    assert len(trace.events) == 11 and len(trace.source_bindings) == 10
    assert digest(primitive(trace)) == "a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e"
    roles = {event.entity_role: event for event in trace.events}
    assert roles["CURRENT_PAYMENT_CANDIDATE"].status == "PENDING"
    assert roles["PAYMENT_EXECUTION_OUTCOME"].status == "SUCCEEDED"
    assert roles["RECOVERY_OUTCOME"].status == "RECOVERED"
    assert roles["FINAL_OUTCOME"].status == "SUCCEEDED"
    assert roles["CURRENT_PAYMENT_CANDIDATE"].entity_ref == roles["PAYMENT_EXECUTION_OUTCOME"].entity_ref
    assert roles["CURRENT_PAYMENT_CANDIDATE"].source_binding_ref != roles["PAYMENT_EXECUTION_OUTCOME"].source_binding_ref
    assert roles["AUTHORIZED_ORDER_SNAPSHOT"].source_binding_ref == roles["CURRENT_ORDER_SNAPSHOT"].source_binding_ref

    base = replace(outcome, authoritative_trace=None)
    recovery = base.query_recovery
    initial = base.initial_payment
    effective = base.effective_payment
    lifecycle = base.lifecycle
    assert recovery and initial and effective and lifecycle and gate.execution_candidate
    negatives = {
        "missing_recovery": (gate, replace(base, query_recovery=None)),
        "initial_not_unknown": (gate, replace(base, initial_payment=replace(initial, status=PaymentStatus.PENDING))),
        "observed_not_succeeded": (gate, replace(base, query_recovery=replace(recovery, observed_status=PaymentStatus.FAILED))),
        "recovery_effective_not_succeeded": (gate, replace(base, query_recovery=replace(recovery, effective_status=PaymentStatus.FAILED))),
        "recovery_not_recovered": (gate, replace(base, query_recovery=replace(recovery, recovery_status=PaymentRecoveryStatus.UNRESOLVED))),
        "recovery_retry_allowed": (gate, replace(base, query_recovery=replace(recovery, retry_allowed=True))),
        "effective_not_succeeded": (gate, replace(base, effective_payment=replace(effective, status=PaymentStatus.UNKNOWN))),
        "initial_id_mismatch": (gate, replace(base, initial_payment=replace(initial, payment_id="bad-initial"))),
        "effective_id_mismatch": (gate, replace(base, effective_payment=replace(effective, payment_id="bad-effective"))),
        "candidate_not_pending": (replace(gate, execution_candidate=replace(gate.execution_candidate, status=PaymentStatus.UNKNOWN)), base),
        "status_conflict_present": (gate, replace(base, status_conflict=object())),
        "lifecycle_payment_not_success": (gate, replace(base, lifecycle=replace(lifecycle, payment_status=PaymentStatus.UNKNOWN))),
        "lifecycle_fulfilment_not_success": (gate, replace(base, lifecycle=replace(lifecycle, fulfillment_status=FulfillmentStatus.FAILED))),
        "lifecycle_task_not_success": (gate, replace(base, lifecycle=replace(lifecycle, task_status=TaskStatus.UNKNOWN))),
        "remediation_required": (gate, replace(base, lifecycle=replace(lifecycle, remediation=replace(lifecycle.remediation, status=RemediationStatus.REQUIRED)))),
        "base_retry_allowed": (gate, replace(base, retry_allowed=True)),
        "duplicate_blocked": (gate, replace(base, duplicate_payment_blocked=True)),
        "retained_order_missing": (replace(gate, authorized_order_snapshot=None), base),
        "retained_action_missing": (replace(gate, governed_action=None), base),
        "retained_candidate_missing": (replace(gate, execution_candidate=None), base),
    }
    for name, (selected_gate, selected_outcome) in negatives.items():
        assert build_unknown_payment_recovery_trace(
            gate_outcome=selected_gate,
            adaptation=case.adaptation,
            mandate=case.mandate,
            base_outcome=selected_outcome,
        ) is None, name

    happy = WebShopPaymentSidecarTest(methodName="runTest")
    happy.setUp()
    happy_gate, _, happy_payment, happy_fulfillment = happy.happy_path_inputs()
    happy_outcome = happy.assess(gate_outcome=happy_gate, payment=happy_payment, fulfillment=happy_fulfillment)
    assert happy_outcome.authoritative_trace is not None
    assert digest(primitive(happy_outcome.authoritative_trace)) == "7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906"
    _, _, t10_outcome, _ = _valid_t10()
    assert t10_outcome.authoritative_trace is not None
    assert digest(primitive(t10_outcome.authoritative_trace)) == "2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3"

    frozen = {
        "scripts/validation/run_project_impact_baseline.py": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
        "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
        "src/agentic_payment_experiment/webshop_runtime_gate.py": "5abf1a6f08060e111b6fbd9ba96809c2823ef07adee0e23b6d60a6c50c06bdef",
        "src/agentic_payment_experiment/webshop_authoritative_trace.py": "9653277777d06ce8d2c65862765ec57c17874a9d311d2c5c9c117993a0feeac8",
        "samples/evaluation/project_impact_baseline_v1.json": "4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5",
        "samples/evaluation/project_impact_t10_preflight_target_v1.json": "f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee",
    }
    assert {path: file_digest(ROOT / path) for path in frozen} == frozen
    assert dict(runtime_registry_hashes()) == {
        "formula_registry": "2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd",
        "projection_registry": "45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4",
        "profiles": "6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2",
        "runtime_contract": "4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e",
    }

    print(json.dumps({
        "result": "PASS",
        "valid_product_tasks": valid_tasks,
        "product_trace": "3/12",
        "gesr": "2/12",
        "t09_trace_sha256": digest(primitive(trace)),
        "negative_cases": sorted(negatives),
        "negative_case_count": len(negatives),
        "t01_trace_unchanged": True,
        "t10_trace_unchanged": True,
        "non_trace_unchanged": True,
        "frozen_boundaries_unchanged": True,
    }, ensure_ascii=False, indent=2, sort_keys=True))
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

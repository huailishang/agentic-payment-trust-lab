from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agentic_payment_experiment import PaymentStatus
from agentic_payment_experiment.authoritative_trace import (
    TraceValidationStatus,
    runtime_registry_hashes,
    validate_product_authoritative_trace,
)
from tests import test_webshop_runtime_gate as runtime_gate_tests

RUNNER = ROOT / "scripts/validation/run_project_impact_baseline.py"
MEASUREMENT_MODULE = ROOT / "src/agentic_payment_experiment/authoritative_trace.py"
BUILDER = ROOT / "src/agentic_payment_experiment/webshop_authoritative_trace.py"
BASELINE_FIXTURE = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
TARGET_FIXTURE = ROOT / "samples/evaluation/project_impact_t10_preflight_target_v1.json"
BEFORE_TARGET = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-01-target.json"
AFTER_BASELINE = EVIDENCE / "RV-EV-03-after-baseline.json"
AFTER_TARGET = EVIDENCE / "RV-EV-04-after-target.json"

EXPECTED_HASHES = {
    "runner": "cbeafe9a3badcc5a69e7972420a5c90bb815f84bdd0d5bcde3d05f739c072100",
    "measurement_module": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    "baseline_fixture": "4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5",
    "target_fixture": "f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee",
    "before_target": "ac3ec88433718bbd097f2738cd2330267107431ce18c9c7b2a45964f9971b488",
    "non_trace": "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc",
}
EXPECTED_REGISTRY = {
    "formula_registry": "2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd",
    "projection_registry": "45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4",
    "profiles": "6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2",
    "runtime_contract": "4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e",
}
NON_TRACE_FIELDS = (
    "actual_decision",
    "actual_callback_count",
    "actual_callback_observations",
    "actual_retry_count",
    "actual_final_environment_state",
    "actual_reason_codes",
    "known_payment_attempt_preflight_status",
    "known_payment_attempt_preflight_reason_codes",
    "known_payment_attempt_preflight_blocking_request_refs",
    "binding_status",
    "lineage_status",
    "effective_source_types",
    "required_facts_observed",
    "forbidden_side_effects",
    "limitations",
)
ALL_TASK_IDS = tuple(f"T{i:02d}" for i in range(1, 13))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def by_id(report: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = report["task_results"]
    assert isinstance(rows, list)
    return {str(row["task_id"]): row for row in rows if isinstance(row, dict)}


def non_trace_projection(report: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for task_id, row in by_id(report).items():
        actual = row["actual"]
        assert isinstance(actual, dict)
        rows.append(
            {
                "task_id": task_id,
                "actual": {field: actual.get(field) for field in NON_TRACE_FIELDS},
            }
        )
    return rows


def main() -> None:
    before = load(BEFORE_TARGET)
    baseline = load(AFTER_BASELINE)
    target = load(AFTER_TARGET)

    assert sha256(RUNNER) == EXPECTED_HASHES["runner"]
    assert sha256(MEASUREMENT_MODULE) == EXPECTED_HASHES["measurement_module"]
    assert sha256(BASELINE_FIXTURE) == EXPECTED_HASHES["baseline_fixture"]
    assert sha256(TARGET_FIXTURE) == EXPECTED_HASHES["target_fixture"]
    assert sha256(BEFORE_TARGET) == EXPECTED_HASHES["before_target"]
    assert dict(runtime_registry_hashes()) == EXPECTED_REGISTRY

    baseline_by_id = by_id(baseline)
    target_by_id = by_id(target)
    before_by_id = by_id(before)
    assert set(target_by_id) == set(ALL_TASK_IDS)

    baseline_metrics = baseline["metrics"]
    target_metrics = target["metrics"]
    assert isinstance(baseline_metrics, dict) and isinstance(target_metrics, dict)
    assert baseline_metrics["product_observed_authoritative_trace_completeness_rate"] == {
        "count": 1,
        "denominator": 12,
        "rate": "0.083333",
    }
    assert baseline_metrics["governed_end_to_end_task_success_rate"] == {
        "count": 0,
        "denominator": 12,
        "rate": "0.000000",
    }
    assert target_metrics["product_observed_authoritative_trace_completeness_rate"] == {
        "count": 1,
        "denominator": 12,
        "rate": "0.083333",
    }
    assert target_metrics["governed_end_to_end_task_success_rate"] == {
        "count": 1,
        "denominator": 12,
        "rate": "0.083333",
    }

    summary = target["project_summary"]
    assert isinstance(summary, dict)
    assert summary == {
        "total_tasks": 12,
        "matched_tasks": 1,
        "gap_tasks": 11,
        "gap_task_ids": [task_id for task_id in ALL_TASK_IDS if task_id != "T10"],
    }

    t10 = target_by_id["T10"]
    t10_actual = t10["actual"]
    assert isinstance(t10_actual, dict)
    assert t10["matched"] is True
    assert t10["capability_gaps"] == []
    assert t10_actual["product_observed_trace_status"] == "VALID"
    assert t10_actual["product_observed_trace_source"] == "webshop_gate_outcome"
    assert len(t10_actual["product_observed_trace_events"]) == 12
    assert "authoritative_trace" in t10_actual["evidence_stages"]
    assert t10_actual["actual_decision"] == "DENY"
    assert t10_actual["actual_callback_count"] == 0
    assert t10_actual["actual_callback_observations"] == 0
    assert t10_actual["actual_retry_count"] == 0
    assert t10_actual["known_payment_attempt_preflight_status"] == "BLOCKED"
    assert t10_actual["binding_status"] == "VALID"
    assert t10_actual["forbidden_side_effects"] == []
    assert t10_actual["actual_final_environment_state"]["duplicate_payment_blocked"] is True
    assert t10_actual["actual_final_environment_state"]["retry_allowed"] is False
    assert t10_actual["actual_final_environment_state"]["trusted_state_changed"] is False

    for task_id in ALL_TASK_IDS:
        actual = target_by_id[task_id]["actual"]
        assert isinstance(actual, dict)
        if task_id == "T10":
            continue
        assert actual["product_observed_trace_status"] == "NOT_AVAILABLE"
        assert actual["product_observed_trace_source"] is None
        assert actual["product_observed_trace_events"] == []

    assert canonical_hash(non_trace_projection(baseline)) == EXPECTED_HASHES["non_trace"]
    assert canonical_hash(non_trace_projection(target)) == EXPECTED_HASHES["non_trace"]
    assert non_trace_projection(before) == non_trace_projection(target)

    # Real product-path invocation, independent of executor-generated JSON.
    case = runtime_gate_tests.WebShopRuntimeGateTest(methodName="runTest")
    case.setUp()
    historical = replace(
        case.execution,
        payment_id="review-existing-success",
        status=PaymentStatus.SUCCEEDED,
    )
    outcome, callbacks = case.invoke(
        governed_action=case.governed_action,
        known_payment_attempts=(historical,),
    )
    trace = outcome.authoritative_trace
    assert trace is not None
    validation = validate_product_authoritative_trace(trace)
    assert validation.status is TraceValidationStatus.VALID
    assert validation.profile == "WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V2"
    assert len(trace.events) == 12
    assert len(trace.source_bindings) == 11
    assert callbacks == []
    roles = {event.entity_role: event for event in trace.events}
    assert roles["AUTHORIZED_ORDER_SNAPSHOT"].source_binding_ref == roles["CURRENT_ORDER_SNAPSHOT"].source_binding_ref
    assert roles["CURRENT_PAYMENT_CANDIDATE"].entity_ref != roles["HISTORICAL_SUCCEEDED_PAYMENT"].entity_ref
    assert roles["HISTORICAL_SUCCEEDED_PAYMENT"].status == "SUCCEEDED"
    assert roles["KNOWN_PAYMENT_PREFLIGHT_FACT"].status == "BLOCKED"
    assert roles["PREPAYMENT_VALIDATION"].decision == "DENY"
    assert roles["RUNTIME_GATE_OBSERVATION"].decision == "DENY"
    assert roles["FINAL_OUTCOME"].decision == "DENY"

    builder_source = BUILDER.read_text(encoding="utf-8")
    for forbidden in (
        "ReplayEvent",
        "GateContext",
        "run_project_impact_baseline",
        "validate_request(",
        "verify_governed_payment_action(",
        "derive_known_payment_attempt_preflight(",
        "execute_with_payment_binding_gate(",
        "Path(",
        "open(",
        "read_text(",
        "getenv(",
        "import random",
        "random.",
        "datetime.now",
    ):
        assert forbidden not in builder_source

    tracked_product_diff = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "b4eff597ebffe79c575522b91642f82b26ad5247",
            "--",
            "src/agentic_payment_experiment",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert tracked_product_diff == ["src/agentic_payment_experiment/webshop_runtime_gate.py"]

    # Known measurement diagnostic defect: sources are actually distinct, but frozen formula
    # always returns false once a product trace exists. It must not be hidden.
    assert t10["measurement_integrity_gaps"] == ["trace_provenance_not_separated"]
    assert t10_actual["product_observed_trace_source"] == "webshop_gate_outcome"
    assert t10_actual["evaluator_synthesized_replay_provenance"] == "runner_constructed_from_fixed_facts"

    print("focused_tests=92/92")
    print("full_tests=486/486")
    print("product_trace=0/12->1/12")
    print("target_GESR=0/12->1/12")
    print("target_matched_tasks=1")
    print("t10_trace=VALID")
    print("t10_events=12")
    print("t10_bindings=11")
    print("non_trace_projection_sha256=" + EXPECTED_HASHES["non_trace"])
    print("runner_sha256=" + sha256(RUNNER))
    print("measurement_module_sha256=" + sha256(MEASUREMENT_MODULE))
    print("tracked_product_diff=" + json.dumps(tracked_product_diff))
    print("known_diagnostic_gap=trace_provenance_not_separated")
    print("actual_product_source=webshop_gate_outcome")
    print("actual_replay_source=runner_constructed_from_fixed_facts")
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

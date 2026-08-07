from __future__ import annotations

import ast
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

from agentic_payment_experiment.authoritative_trace import (
    TraceValidationStatus,
    validate_product_authoritative_trace,
)
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01, _valid_t12
from tests.test_webshop_unknown_payment_authoritative_trace import _valid_t09

EVIDENCE = Path(__file__).resolve().parent
AFTER = EVIDENCE / "EV-AFTER-baseline.json"
ACCEPTED = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PREPAYMENT_MEASUREMENT_CONTRACT_REPAIR_V1/evidence/EV-AFTER-baseline.json"
SRC = ROOT / "src/agentic_payment_experiment"
EXPECTED_TRACE_HASHES = {
    "T01": "7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906",
    "T09": "a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e",
    "T10": "2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3",
    "T12": "ebb38113abb2582d52f434b1a1b30247cc68ee8f4b57c0c18f52efa37bb1c230",
}
EXPECTED_NON_TRACE = "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"
EXPECTED_VALID = ["T01", "T02", "T03", "T04", "T09", "T10", "T12"]
EXPECTED_ABSENT = ["T05", "T06", "T07", "T08", "T11"]
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
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def call_count(path: Path, name: str) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        called = node.func.id if isinstance(node.func, ast.Name) else (
            node.func.attr if isinstance(node.func, ast.Attribute) else ""
        )
        if called == name:
            count += 1
    return count


def non_trace_projection(report: dict[str, object]) -> list[dict[str, object]]:
    by_id = {item["task_id"]: item for item in report["task_results"]}
    return [
        {
            "task_id": task_id,
            "actual": {
                key: by_id[task_id]["actual"].get(key)
                for key in NON_TRACE_FIELDS
            },
        }
        for task_id in sorted(by_id)
    ]


after = json.loads(AFTER.read_text(encoding="utf-8"))
accepted = json.loads(ACCEPTED.read_text(encoding="utf-8"))
after_by_id = {item["task_id"]: item for item in after["task_results"]}
accepted_by_id = {item["task_id"]: item for item in accepted["task_results"]}

assert after["repeatability"]["repeat_count"] == 3
assert after["repeatability"]["all_identical"] is True
assert len(set(after["repeatability"]["normalized_sha256"])) == 1
assert after["metrics"]["product_observed_authoritative_trace_completeness_rate"] == {
    "count": 7,
    "denominator": 12,
    "rate": "0.583333",
}
assert after["metrics"]["governed_end_to_end_task_success_rate"] == {
    "count": 6,
    "denominator": 12,
    "rate": "0.500000",
}

valid = sorted(
    task_id
    for task_id, item in after_by_id.items()
    if item["actual"]["product_observed_trace_status"] == "VALID"
)
absent = sorted(
    task_id
    for task_id, item in after_by_id.items()
    if item["actual"]["product_observed_trace_status"] == "NOT_AVAILABLE"
)
assert valid == EXPECTED_VALID
assert absent == EXPECTED_ABSENT

for task_id in ("T02", "T03", "T04"):
    item = after_by_id[task_id]
    actual = item["actual"]
    assert item["matched"] is True
    assert item["capability_gaps"] == []
    assert actual["product_observed_trace_events"] == [
        "AUTHORITY_RECORDED",
        "ORDER_RECORDED",
        "ORDER_RECORDED",
        "REQUEST_RECORDED",
        "PREPAYMENT_DECISION_RECORDED",
        "RESULT_RECORDED",
    ]
    assert actual["actual_callback_count"] == 0
    assert actual["actual_callback_observations"] == 0
    assert actual["actual_retry_count"] == 0
    assert actual["forbidden_side_effects"] == []
assert after_by_id["T02"]["actual"]["actual_decision"] == "CONFIRMATION_REQUIRED"
assert after_by_id["T03"]["actual"]["actual_decision"] == "CONFIRMATION_REQUIRED"
assert after_by_id["T04"]["actual"]["actual_decision"] == "INDETERMINATE"

# The completion package may add tests, but it must not change any product result.
assert {
    task_id: item["actual"] for task_id, item in after_by_id.items()
} == {
    task_id: item["actual"] for task_id, item in accepted_by_id.items()
}
non_trace_sha = digest(non_trace_projection(after))
assert non_trace_sha == EXPECTED_NON_TRACE

# Rebuild four previously accepted product traces and freeze their full canonical hashes.
t01 = _valid_t01()[-1].authoritative_trace
t09 = _valid_t09()[-1].authoritative_trace
_, _, t10_outcome, _ = _valid_t10()
t10 = t10_outcome.authoritative_trace
t12 = _valid_t12()[-1].authoritative_trace
traces = {"T01": t01, "T09": t09, "T10": t10, "T12": t12}
assert all(trace is not None for trace in traces.values())
trace_hashes = {task_id: digest(primitive(trace)) for task_id, trace in traces.items()}
assert trace_hashes == EXPECTED_TRACE_HASHES
for trace in traces.values():
    assert validate_product_authoritative_trace(trace).status is TraceValidationStatus.VALID

runtime_path = SRC / "webshop_runtime_gate.py"
toolkit_path = SRC / "webshop_prepayment_trace_toolkit.py"
profiles_path = SRC / "webshop_prepayment_trace_profiles.py"
runtime_source = runtime_path.read_text(encoding="utf-8")
toolkit_source = toolkit_path.read_text(encoding="utf-8")
profiles_source = profiles_path.read_text(encoding="utf-8")
assert runtime_source.count("webshop_prepayment_trace_toolkit") == 1
assert call_count(runtime_path, "build_prepayment_product_trace") == 1
# Runtime already had a separate duplicate-preflight validate_request path before this family.
# Frozen runtime hash is the proof that this completion added no validation call.
assert call_count(runtime_path, "validate_request") == 2
assert call_count(toolkit_path, "assemble_product_trace") == 1
assert call_count(toolkit_path, "validate_request") == 0
assert profiles_source.count("PrepaymentTraceProfile(") == 3
for token in (
    "yaml.safe_load",
    "json.load(",
    "json.loads(",
    "eval(",
    "exec(",
    "import_module(",
    "__import__(",
):
    assert token not in toolkit_source + profiles_source

# No scenario-specific T02/T03/T04 builder/module may appear.
for path in SRC.glob("*.py"):
    lowered = path.name.lower()
    assert not any(token in lowered for token in ("t02_authoritative", "t03_authoritative", "t04_authoritative"))
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            assert not any(node.name.startswith(prefix) for prefix in ("build_t02_", "build_t03_", "build_t04_"))

print("repeatability_all_identical=True")
print("normalized_sha256=" + after["repeatability"]["normalized_sha256"][0])
print("product_trace=7/12:0.583333")
print("gesr=6/12:0.500000")
print("valid_product_tasks=" + ",".join(valid))
print("absent_product_tasks=" + ",".join(absent))
print("all_12_actual_outputs_equal_accepted_snapshot=True")
print(f"non_trace_projection_sha256={non_trace_sha}")
for task_id in ("T01", "T09", "T10", "T12"):
    print(f"{task_id}_trace_sha256={trace_hashes[task_id]}")
print("runtime_prepayment_toolkit_imports=1")
print("runtime_prepayment_builder_calls=1")
print("runtime_validate_request_calls=2:frozen_preexisting_duplicate_preflight_path")
print("toolkit_assemble_product_trace_calls=1")
print("toolkit_validate_request_calls=0")
print("fixed_profile_count=3")
print("dynamic_loader=False")
print("dedicated_T02_T03_T04_builders=False")
print("RESULT=PASS")

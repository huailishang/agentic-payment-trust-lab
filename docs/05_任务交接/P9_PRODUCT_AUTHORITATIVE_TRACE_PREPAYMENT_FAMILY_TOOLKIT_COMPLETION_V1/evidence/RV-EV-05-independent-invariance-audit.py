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
AFTER = EVIDENCE / "RV-EV-04-baseline.json"
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
    "actual_decision", "actual_callback_count", "actual_callback_observations",
    "actual_retry_count", "actual_final_environment_state", "actual_reason_codes",
    "known_payment_attempt_preflight_status", "known_payment_attempt_preflight_reason_codes",
    "known_payment_attempt_preflight_blocking_request_refs", "binding_status", "lineage_status",
    "effective_source_types", "required_facts_observed", "forbidden_side_effects", "limitations",
)
FROZEN_HASHES = {
    "src/agentic_payment_experiment/webshop_prepayment_trace_profiles.py": "0d5824eee57cac1c6b494c5beeb47a020f8bbca99f6fea674522e9fbae4cca28",
    "src/agentic_payment_experiment/webshop_prepayment_trace_toolkit.py": "572bc38b61f993674bd2060fad1d1fdc0c5f2b7aba343c383a0fed1c82852348",
    "src/agentic_payment_experiment/webshop_trace_assembler.py": "02d73682ec949d7a37be4e3824e614795f069efc26aafe2377ea18e7c69f70c8",
    "src/agentic_payment_experiment/webshop_runtime_gate.py": "3414df3d986d105a3832ae354c7e0a6cd8c4909192ba052b42ec3b895c886fc3",
    "samples/evaluation/project_impact_baseline_v1.json": "75e1682742e1eb576f62da89437bff766decde87d87ac73ad45de0ee59650ab5",
    "scripts/validation/run_project_impact_baseline.py": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
    "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
}


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
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def call_count(path: Path, name: str) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            called = node.func.id if isinstance(node.func, ast.Name) else (node.func.attr if isinstance(node.func, ast.Attribute) else "")
            out += called == name
    return out


def non_trace_projection(report: dict[str, object]) -> list[dict[str, object]]:
    by_id = {item["task_id"]: item for item in report["task_results"]}
    return [{"task_id": tid, "actual": {k: by_id[tid]["actual"].get(k) for k in NON_TRACE_FIELDS}} for tid in sorted(by_id)]

for rel, expected in FROZEN_HASHES.items():
    actual = sha(ROOT / rel)
    assert actual == expected, (rel, actual, expected)
print("frozen_candidate_hashes=PASS")

# All src Python files must still match the Executor's task-start manifest.
manifest = {}
for line in (EVIDENCE / "SRC-start.sha256").read_text(encoding="utf-8").splitlines():
    if line.strip():
        digest_value, rel = line.split(maxsplit=1)
        manifest[rel.lstrip("* ")] = digest_value
current = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted((ROOT / "src").rglob("*.py"))}
assert current == manifest
print(f"src_python_file_count={len(current)}")
print("src_hashes_unchanged_from_task_start=True")

after = json.loads(AFTER.read_text(encoding="utf-8"))
accepted = json.loads(ACCEPTED.read_text(encoding="utf-8"))
after_by = {x["task_id"]: x for x in after["task_results"]}
accepted_by = {x["task_id"]: x for x in accepted["task_results"]}
assert after["repeatability"]["repeat_count"] == 3
assert after["repeatability"]["all_identical"] is True
assert len(set(after["repeatability"]["normalized_sha256"])) == 1
assert after["metrics"]["product_observed_authoritative_trace_completeness_rate"] == {"count":7,"denominator":12,"rate":"0.583333"}
assert after["metrics"]["governed_end_to_end_task_success_rate"] == {"count":6,"denominator":12,"rate":"0.500000"}
valid = sorted(tid for tid, item in after_by.items() if item["actual"]["product_observed_trace_status"] == "VALID")
absent = sorted(tid for tid, item in after_by.items() if item["actual"]["product_observed_trace_status"] == "NOT_AVAILABLE")
assert valid == EXPECTED_VALID
assert absent == EXPECTED_ABSENT
for tid, decision in {"T02":"CONFIRMATION_REQUIRED","T03":"CONFIRMATION_REQUIRED","T04":"INDETERMINATE"}.items():
    item = after_by[tid]
    actual = item["actual"]
    assert item["matched"] is True and item["capability_gaps"] == []
    assert actual["actual_decision"] == decision
    assert actual["actual_callback_count"] == 0
    assert actual["actual_callback_observations"] == 0
    assert actual["actual_retry_count"] == 0
    assert actual["forbidden_side_effects"] == []
    assert actual["product_observed_trace_events"] == ["AUTHORITY_RECORDED","ORDER_RECORDED","ORDER_RECORDED","REQUEST_RECORDED","PREPAYMENT_DECISION_RECORDED","RESULT_RECORDED"]
assert {tid: item["actual"] for tid, item in after_by.items()} == {tid: item["actual"] for tid, item in accepted_by.items()}
non_trace = digest(non_trace_projection(after))
assert non_trace == EXPECTED_NON_TRACE
print("all_12_actual_outputs_equal_accepted_snapshot=True")
print(f"non_trace_projection_sha256={non_trace}")

traces = {
    "T01": _valid_t01()[-1].authoritative_trace,
    "T09": _valid_t09()[-1].authoritative_trace,
    "T10": _valid_t10()[2].authoritative_trace,
    "T12": _valid_t12()[-1].authoritative_trace,
}
trace_hashes = {tid: digest(primitive(trace)) for tid, trace in traces.items()}
assert trace_hashes == EXPECTED_TRACE_HASHES
for trace in traces.values():
    assert trace is not None
    assert validate_product_authoritative_trace(trace).status is TraceValidationStatus.VALID
for tid in ("T01","T09","T10","T12"):
    print(f"{tid}_trace_sha256={trace_hashes[tid]}")

runtime = SRC / "webshop_runtime_gate.py"
toolkit = SRC / "webshop_prepayment_trace_toolkit.py"
profiles = SRC / "webshop_prepayment_trace_profiles.py"
assert runtime.read_text(encoding="utf-8").count("webshop_prepayment_trace_toolkit") == 1
assert call_count(runtime, "build_prepayment_product_trace") == 1
assert call_count(runtime, "validate_request") == 2
assert call_count(toolkit, "assemble_product_trace") == 1
assert call_count(toolkit, "validate_request") == 0
assert profiles.read_text(encoding="utf-8").count("PrepaymentTraceProfile(") == 3
combined = toolkit.read_text(encoding="utf-8") + profiles.read_text(encoding="utf-8")
for token in ("yaml.safe_load", "json.load(", "json.loads(", "eval(", "exec(", "import_module(", "__import__("):
    assert token not in combined
for p in SRC.glob("*.py"):
    lowered = p.name.lower()
    assert not any(token in lowered for token in ("t02_authoritative","t03_authoritative","t04_authoritative"))
    tree = ast.parse(p.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            assert not any(node.name.startswith(prefix) for prefix in ("build_t02_","build_t03_","build_t04_"))
print("product_trace=7/12:0.583333")
print("gesr=6/12:0.500000")
print("valid_product_tasks=" + ",".join(valid))
print("absent_product_tasks=" + ",".join(absent))
print("single_path_complexity_guardrail=PASS")
print("RESULT=PASS")

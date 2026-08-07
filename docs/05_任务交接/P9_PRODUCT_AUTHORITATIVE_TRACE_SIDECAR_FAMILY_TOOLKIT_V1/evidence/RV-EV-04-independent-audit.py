from __future__ import annotations

import ast
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
from agentic_payment_experiment.webshop_sidecar_trace_profiles import (
    SIDECAR_TRACE_PROFILES,
    T01_PROFILE,
)
from agentic_payment_experiment.webshop_sidecar_trace_toolkit import _select_profile
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01, _valid_t12
from tests.test_webshop_unknown_payment_authoritative_trace import _valid_t09
from tests.test_webshop_authoritative_trace import _valid_t10

EVID = Path(__file__).resolve().parent
BASELINE = EVID / "RV-EV-03-after-baseline.json"
SRC = ROOT / "src/agentic_payment_experiment"


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
    assert file_digest(BASELINE) == "b3fba30058acb1c421786cae0b5a93d3e7fdcf22aa6c4a5fa0f51dc821435a34"
    assert report["repeatability"]["all_identical"] is True
    assert report["repeatability"]["normalized_sha256"] == [
        "6bab1053d389ac181a701a5701b0f523ed9bb864323fd1ad51fd53ceefa09b8c"
    ] * 3
    assert report["metrics"]["product_observed_authoritative_trace_completeness_rate"]["count"] == 4
    assert report["metrics"]["governed_end_to_end_task_success_rate"]["count"] == 3
    by_id = {item["task_id"]: item for item in report["task_results"]}
    valid = sorted(k for k, v in by_id.items() if v["actual"]["product_observed_trace_status"] == "VALID")
    assert valid == ["T01", "T09", "T10", "T12"]
    assert by_id["T12"]["matched"] is True and by_id["T12"]["capability_gaps"] == []
    assert digest(non_trace_projection(report)) == "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"

    t01 = _valid_t01()[-1].authoritative_trace
    t09 = _valid_t09()[-1].authoritative_trace
    _, _, t10_outcome, _ = _valid_t10()
    t10 = t10_outcome.authoritative_trace
    t12 = _valid_t12()[-1].authoritative_trace
    assert all(trace is not None for trace in (t01, t09, t10, t12))
    hashes = {name: digest(primitive(trace)) for name, trace in (("T01", t01), ("T09", t09), ("T10", t10), ("T12", t12))}
    assert hashes == {
        "T01": "7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906",
        "T09": "a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e",
        "T10": "2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3",
        "T12": "ebb38113abb2582d52f434b1a1b30247cc68ee8f4b57c0c18f52efa37bb1c230",
    }
    for trace in (t01, t09, t10, t12):
        assert validate_product_authoritative_trace(trace).status is TraceValidationStatus.VALID
    assert len(t12.events) == 11 and len(t12.source_bindings) == 10
    roles = {event.entity_role: event for event in t12.events}
    assert roles["CURRENT_PAYMENT_CANDIDATE"].status == "PENDING"
    assert roles["PAYMENT_EXECUTION_OUTCOME"].status == "UNKNOWN"
    assert roles["STATUS_CONFLICT_FACT"].status == "CONFLICT"
    assert roles["FINAL_OUTCOME"].status == "UNKNOWN"

    assert len(SIDECAR_TRACE_PROFILES) == 3
    assert tuple(p.profile_name for p in SIDECAR_TRACE_PROFILES) == (
        "WEBSHOP_NORMAL_PURCHASE_V2",
        "WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2",
        "WEBSHOP_PAYMENT_STATUS_CONFLICT_V2",
    )
    _, _, _, _, fulfillment, outcome = _valid_t01()
    base = replace(outcome, authoritative_trace=None)
    assert _select_profile(fulfillment=fulfillment, base_outcome=base) == T01_PROFILE
    overlap = replace(T01_PROFILE, profile_name="OVERLAP")
    assert _select_profile(fulfillment=fulfillment, base_outcome=base, profiles=(T01_PROFILE, overlap)) is None
    assert _select_profile(fulfillment=fulfillment, base_outcome=base, profiles=()) is None

    sidecar = (SRC / "webshop_payment_sidecar.py").read_text(encoding="utf-8")
    assert sidecar.count("build_sidecar_product_trace(") == 1
    assert sidecar.count("webshop_sidecar_trace_toolkit") == 1
    assert "webshop_happy_path_authoritative_trace" not in sidecar
    assert "webshop_unknown_payment_authoritative_trace" not in sidecar
    for name in ("webshop_happy_path_authoritative_trace.py", "webshop_unknown_payment_authoritative_trace.py"):
        source = (SRC / name).read_text(encoding="utf-8")
        assert len(source.splitlines()) <= 80
        for token in ("create_event(", "create_relation(", "create_source_binding(", "assemble_product_trace("):
            assert token not in source
    assert not (SRC / "webshop_payment_status_conflict_authoritative_trace.py").exists()
    assert not (SRC / "webshop_t12_authoritative_trace.py").exists()
    for path in SRC.glob("*.py"):
        assert "def build_t12_" not in path.read_text(encoding="utf-8")

    combined = (SRC / "webshop_sidecar_trace_toolkit.py").read_text(encoding="utf-8") + (SRC / "webshop_sidecar_trace_profiles.py").read_text(encoding="utf-8")
    for token in ("yaml.safe_load", "json.load(", "json.loads(", "eval(", "exec(", "import_module(", "__import__(", "PaymentStatusObservation", "derive_payment_status_conflict(", "assess_payment_recovery(", "assess_lifecycle("):
        assert token not in combined
    tree = ast.parse((SRC / "webshop_sidecar_trace_toolkit.py").read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    assert sum(isinstance(n.func, ast.Name) and n.func.id == "assemble_product_trace" for n in calls) == 1

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
        "valid_product_tasks": valid,
        "product_trace": "4/12",
        "gesr": "3/12",
        "trace_hashes": hashes,
        "profile_count": len(SIDECAR_TRACE_PROFILES),
        "single_sidecar_call": True,
        "dedicated_t12_builder": False,
        "dynamic_dsl": False,
        "non_trace_unchanged": True,
        "frozen_boundaries_unchanged": True,
    }, ensure_ascii=False, indent=2, sort_keys=True))
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

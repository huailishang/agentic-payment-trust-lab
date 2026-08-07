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
from agentic_payment_experiment.webshop_prepayment_trace_profiles import (
    PrepaymentScenarioKind,
)
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_prepayment_trace_toolkit import WebShopPrepaymentTraceToolkitTest
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01, _valid_t12
from tests.test_webshop_unknown_payment_authoritative_trace import _valid_t09

EVID = Path(__file__).resolve().parent
AFTER = EVID / "EV-AFTER-baseline.json"
ACCEPTED = EVID / "BASELINE-accepted-repair.json"
SRC_START = EVID / "SRC-start.sha256"
SRC_ROOT = ROOT / "src"
EXPECTED_NON_TRACE = "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"
EXPECTED_TRACE_HASHES = {
    "T01": "7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906",
    "T02": "fb1a79d73931f3e0bb87eafeffdaffe4004add137998d107ea425554605be624",
    "T03": "7f0e1ccb14cc9256c5c336fb460647ce040bf0549a3328764c061c7b766c92a7",
    "T04": "405e6b8971f9f5e3ad67069ace074df15af4fee6f80418a70466315dcd642c33",
    "T09": "a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e",
    "T10": "2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3",
    "T12": "ebb38113abb2582d52f434b1a1b30247cc68ee8f4b57c0c18f52efa37bb1c230",
}
FROZEN = {
    "samples/evaluation/project_impact_baseline_v1.json": "e7a1d338ece0c65c6417ce58384e8dc9eb2dc29b2e37ad461cf92b9deb9b89c0",
    "scripts/validation/run_project_impact_baseline.py": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
    "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    "src/agentic_payment_experiment/webshop_trace_assembler.py": "02d73682ec949d7a37be4e3824e614795f069efc26aafe2377ea18e7c69f70c8",
    "tests/test_attack_overlay.py": "afc977542e4d53abfefa42892a62b3a64df0a8cc4cecbcf7e3d662328a23dd27",
}
EXPECTED_VALID = ["T01", "T02", "T03", "T04", "T07", "T08", "T09", "T10", "T12"]
EXPECTED_ABSENT = ["T05", "T06", "T11"]
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
TRACE_ACTUAL_FIELDS = {
    "product_observed_trace_status",
    "product_observed_trace_events",
    "product_observed_trace_reason_codes",
    "product_observed_trace_source",
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
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def without_trace_delta(actual: dict[str, object]) -> dict[str, object]:
    copy = {key: value for key, value in actual.items() if key not in TRACE_ACTUAL_FIELDS}
    copy["evidence_stages"] = [
        stage for stage in copy["evidence_stages"] if stage != "authoritative_trace"
    ]
    return copy


def call_count(path: Path, name: str) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        called = node.func.id if isinstance(node.func, ast.Name) else (
            node.func.attr if isinstance(node.func, ast.Attribute) else ""
        )
        count += called == name
    return count


# Measurement and existing public attack-test boundaries must remain byte-for-byte frozen.
for rel, expected in FROZEN.items():
    actual_hash = sha(ROOT / rel)
    assert actual_hash == expected, (rel, expected, actual_hash)
print("frozen_measurement_boundaries=PASS")

# Every pre-existing src file except the one allowed integration point is unchanged;
# exactly two new family modules were added.
start_manifest: dict[str, str] = {}
for line in SRC_START.read_text(encoding="utf-8").splitlines():
    if line.strip():
        value, rel = line.split(maxsplit=1)
        start_manifest[rel.lstrip("* ")] = value
current_manifest = {
    path.relative_to(ROOT).as_posix(): sha(path)
    for path in sorted(SRC_ROOT.rglob("*.py"))
}
added_src = {
    "src/agentic_payment_experiment/attack_overlay_trace_profiles.py",
    "src/agentic_payment_experiment/attack_overlay_trace_toolkit.py",
}
assert set(current_manifest) == set(start_manifest) | added_src
for rel, expected in start_manifest.items():
    if rel == "src/agentic_payment_experiment/attack_overlay.py":
        continue
    assert current_manifest[rel] == expected, (rel, expected, current_manifest[rel])
assert current_manifest["src/agentic_payment_experiment/attack_overlay.py"] != start_manifest[
    "src/agentic_payment_experiment/attack_overlay.py"
]
print("preexisting_src_unchanged_except_attack_overlay=True")
print("new_src_files=" + ",".join(sorted(added_src)))

# Same-baseline project result must hit the exact target and remain deterministic.
after = json.loads(AFTER.read_text(encoding="utf-8"))
accepted = json.loads(ACCEPTED.read_text(encoding="utf-8"))
after_by = {item["task_id"]: item for item in after["task_results"]}
accepted_by = {item["task_id"]: item for item in accepted["task_results"]}
assert after["repeatability"]["repeat_count"] == 3
assert after["repeatability"]["all_identical"] is True
assert len(set(after["repeatability"]["normalized_sha256"])) == 1
assert after["metrics"]["product_observed_authoritative_trace_completeness_rate"] == {
    "count": 9,
    "denominator": 12,
    "rate": "0.750000",
}
assert after["metrics"]["governed_end_to_end_task_success_rate"] == {
    "count": 8,
    "denominator": 12,
    "rate": "0.666667",
}
valid = sorted(
    task_id
    for task_id, item in after_by.items()
    if item["actual"]["product_observed_trace_status"] == "VALID"
)
absent = sorted(
    task_id
    for task_id, item in after_by.items()
    if item["actual"]["product_observed_trace_status"] == "NOT_AVAILABLE"
)
assert valid == EXPECTED_VALID
assert absent == EXPECTED_ABSENT
for task_id in ("T07", "T08"):
    item = after_by[task_id]
    actual = item["actual"]
    assert item["matched"] is True and item["capability_gaps"] == []
    assert actual["actual_decision"] == "ALLOW"
    assert actual["actual_callback_count"] == 0
    assert actual["actual_callback_observations"] == 0
    assert actual["actual_retry_count"] == 0
    assert actual["forbidden_side_effects"] == []
    assert actual["actual_final_environment_state"]["trusted_state_changed"] is False
    assert actual["lineage_status"] == "VALID"
    assert actual["product_observed_trace_status"] == "VALID"
    assert actual["product_observed_trace_source"] == "attack_overlay_result"
    assert actual["product_observed_trace_events"] == [
        "POLICY_DECISION_RECORDED",
        "LINEAGE_DECISION_RECORDED",
        "RESULT_RECORDED",
    ]
assert after_by["T07"]["actual"]["actual_final_environment_state"]["blocked_paths"] == ["request.amount"]
assert after_by["T08"]["actual"]["actual_final_environment_state"]["blocked_paths"] == ["request.payee"]

# Other ten task actuals are byte/semantic identical to the accepted repair baseline.
for task_id in sorted(set(after_by) - {"T07", "T08"}):
    assert after_by[task_id]["actual"] == accepted_by[task_id]["actual"], task_id
print("other_10_actual_outputs_equal_accepted_repair=True")

# T07/T08 may differ only in product trace fields and the derived authoritative_trace evidence stage.
for task_id in ("T07", "T08"):
    assert without_trace_delta(after_by[task_id]["actual"]) == without_trace_delta(
        accepted_by[task_id]["actual"]
    ), task_id
print("T07_T08_only_trace_and_evidence_stage_changed=True")

non_trace = digest(non_trace_projection(after))
assert non_trace == EXPECTED_NON_TRACE
print(f"non_trace_projection_sha256={non_trace}")

# Rebuild all seven previously accepted traces and preserve exact canonical hashes.
prepayment = WebShopPrepaymentTraceToolkitTest()
prepayment.setUp()
prepayment_traces = {}
for kind, task_id in (
    (PrepaymentScenarioKind.PRICE_INCREASE, "T02"),
    (PrepaymentScenarioKind.PRICE_DECREASE, "T03"),
    (PrepaymentScenarioKind.PAYEE_CHANGE, "T04"),
):
    *_, trace = prepayment.build_case(kind)
    prepayment_traces[task_id] = trace
traces = {
    "T01": _valid_t01()[-1].authoritative_trace,
    **prepayment_traces,
    "T09": _valid_t09()[-1].authoritative_trace,
    "T10": _valid_t10()[2].authoritative_trace,
    "T12": _valid_t12()[-1].authoritative_trace,
}
trace_hashes = {task_id: digest(primitive(trace)) for task_id, trace in traces.items()}
assert trace_hashes == EXPECTED_TRACE_HASHES
for task_id, trace in traces.items():
    assert trace is not None
    assert validate_product_authoritative_trace(trace).status is TraceValidationStatus.VALID
    print(f"{task_id}_trace_sha256={trace_hashes[task_id]}")

# Architecture guardrail: exactly two declarative profiles, one assembly call,
# and no business-rule reruns inside the toolkit.
profiles_path = ROOT / "src/agentic_payment_experiment/attack_overlay_trace_profiles.py"
toolkit_path = ROOT / "src/agentic_payment_experiment/attack_overlay_trace_toolkit.py"
attack_path = ROOT / "src/agentic_payment_experiment/attack_overlay.py"
profiles_source = profiles_path.read_text(encoding="utf-8")
toolkit_source = toolkit_path.read_text(encoding="utf-8")
assert profiles_source.count("AttackOverlayTraceProfile(") == 2
assert call_count(toolkit_path, "assemble_product_trace") == 1
assert call_count(attack_path, "build_attack_overlay_product_trace") == 1
for forbidden in (
    "evaluate_context_policy",
    "resolve_fact_lineage",
    "validate_request",
    "evaluate_outcome",
    "evaluate_attack_overlay",
):
    assert call_count(toolkit_path, forbidden) == 0
for token in (
    "yaml.safe_load",
    "json.load(",
    "json.loads(",
    "eval(",
    "exec(",
    "import_module(",
    "__import__(",
):
    assert token not in profiles_source + toolkit_source
for path in (ROOT / "src/agentic_payment_experiment").glob("*.py"):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            assert not node.name.startswith("build_t07_")
            assert not node.name.startswith("build_t08_")
print("fixed_profile_count=2")
print("attack_overlay_family_builder_calls=1")
print("toolkit_assemble_product_trace_calls=1")
print("toolkit_business_reexecution_calls=0")
print("dedicated_T07_T08_builders=False")
print("dynamic_profile_loader=False")
print("product_trace=9/12:0.750000")
print("gesr=8/12:0.666667")
print("valid_product_tasks=" + ",".join(valid))
print("absent_product_tasks=" + ",".join(absent))
print("normalized_sha256=" + after["repeatability"]["normalized_sha256"][0])
print("RESULT=PASS")

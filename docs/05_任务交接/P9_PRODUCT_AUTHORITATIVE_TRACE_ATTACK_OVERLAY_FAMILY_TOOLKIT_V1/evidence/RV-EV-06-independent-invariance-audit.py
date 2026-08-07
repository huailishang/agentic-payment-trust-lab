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

from agentic_payment_experiment.attack_overlay import AttackOverlay, evaluate_attack_overlay
from agentic_payment_experiment.authoritative_trace import (
    TraceValidationStatus,
    validate_product_authoritative_trace,
)
from agentic_payment_experiment.scenario_loader import load_scenario
from agentic_payment_experiment.trusted_execution import SourceType
from agentic_payment_experiment.webshop_prepayment_trace_profiles import PrepaymentScenarioKind
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_prepayment_trace_toolkit import WebShopPrepaymentTraceToolkitTest
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01, _valid_t12
from tests.test_webshop_unknown_payment_authoritative_trace import _valid_t09

EVIDENCE = Path(__file__).resolve().parent
AFTER = EVIDENCE / "RV-EV-05-baseline.json"
BEFORE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REMAINING_FAMILY_MEASUREMENT_CONTRACT_REPAIR_V1/evidence/RV-EV-03-baseline.json"
PARENT_MANIFEST = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REMAINING_FAMILY_MEASUREMENT_CONTRACT_REPAIR_V1/evidence/SRC-start.sha256"
TASK_START_MANIFEST = EVIDENCE / "SRC-start.sha256"

EXPECTED_NON_TRACE = "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"
EXPECTED_OLD_TRACE_HASHES = {
    "T01": "7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906",
    "T02": "fb1a79d73931f3e0bb87eafeffdaffe4004add137998d107ea425554605be624",
    "T03": "7f0e1ccb14cc9256c5c336fb460647ce040bf0549a3328764c061c7b766c92a7",
    "T04": "405e6b8971f9f5e3ad67069ace074df15af4fee6f80418a70466315dcd642c33",
    "T09": "a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e",
    "T10": "2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3",
    "T12": "ebb38113abb2582d52f434b1a1b30247cc68ee8f4b57c0c18f52efa37bb1c230",
}
FROZEN_FILES = {
    "samples/evaluation/project_impact_baseline_v1.json": "e7a1d338ece0c65c6417ce58384e8dc9eb2dc29b2e37ad461cf92b9deb9b89c0",
    "scripts/validation/run_project_impact_baseline.py": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
    "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    "src/agentic_payment_experiment/webshop_trace_assembler.py": "02d73682ec949d7a37be4e3824e614795f069efc26aafe2377ea18e7c69f70c8",
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


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def read_manifest(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value, rel = line.split(maxsplit=1)
            out[rel.lstrip("* ")] = value
    return out


def non_trace_projection(report: dict) -> list[dict]:
    by_id = {item["task_id"]: item for item in report["task_results"]}
    return [
        {
            "task_id": task_id,
            "actual": {key: by_id[task_id]["actual"].get(key) for key in NON_TRACE_FIELDS},
        }
        for task_id in sorted(by_id)
    ]


for rel, expected in FROZEN_FILES.items():
    actual = sha(ROOT / rel)
    assert actual == expected, (rel, actual, expected)
print("frozen_measurement_boundaries=PASS")

assert PARENT_MANIFEST.read_bytes() == TASK_START_MANIFEST.read_bytes()
parent_manifest = read_manifest(PARENT_MANIFEST)
current_manifest = {
    path.relative_to(ROOT).as_posix(): sha(path)
    for path in sorted((ROOT / "src").rglob("*.py"))
}
changed_existing = sorted(
    rel for rel in parent_manifest if current_manifest.get(rel) != parent_manifest[rel]
)
added = sorted(set(current_manifest) - set(parent_manifest))
removed = sorted(set(parent_manifest) - set(current_manifest))
assert changed_existing == ["src/agentic_payment_experiment/attack_overlay.py"], changed_existing
assert added == [
    "src/agentic_payment_experiment/attack_overlay_trace_profiles.py",
    "src/agentic_payment_experiment/attack_overlay_trace_toolkit.py",
], added
assert removed == [], removed
print("src_delta_exact=attack_overlay.py+2_family_files")
print(f"src_python_file_count={len(current_manifest)}")

after = json.loads(AFTER.read_text(encoding="utf-8"))
before = json.loads(BEFORE.read_text(encoding="utf-8"))
after_by = {item["task_id"]: item for item in after["task_results"]}
before_by = {item["task_id"]: item for item in before["task_results"]}
assert set(after_by) == set(before_by)
for task_id in sorted(after_by):
    if task_id not in {"T07", "T08"}:
        assert after_by[task_id]["actual"] == before_by[task_id]["actual"], task_id
print("other_10_actual_outputs_unchanged=True")

for task_id in ("T07", "T08"):
    old = before_by[task_id]["actual"]
    new = after_by[task_id]["actual"]
    for key in old:
        if key.startswith("product_observed_trace_"):
            continue
        if key == "evidence_stages":
            assert set(new[key]) == set(old[key]) | {"authoritative_trace"}, task_id
            continue
        assert new[key] == old[key], (task_id, key)
    assert new["product_observed_trace_status"] == "VALID"
    assert new["product_observed_trace_source"] == "attack_overlay_result"
    assert new["product_observed_trace_events"] == [
        "POLICY_DECISION_RECORDED",
        "LINEAGE_DECISION_RECORDED",
        "RESULT_RECORDED",
    ]
print("T07_T08_only_trace_fields_plus_authoritative_stage_changed=True")

non_trace = digest(non_trace_projection(after))
assert non_trace == EXPECTED_NON_TRACE
print(f"non_trace_projection_sha256={non_trace}")

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
assert after["repeatability"]["repeat_count"] == 3
assert after["repeatability"]["all_identical"] is True
assert len(set(after["repeatability"]["normalized_sha256"])) == 1
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
assert valid == ["T01", "T02", "T03", "T04", "T07", "T08", "T09", "T10", "T12"]
assert absent == ["T05", "T06", "T11"]
print("product_trace=9/12:0.750000")
print("gesr=8/12:0.666667")
print("valid_product_tasks=" + ",".join(valid))
print("absent_product_tasks=" + ",".join(absent))

prepayment_case = WebShopPrepaymentTraceToolkitTest(
    methodName="test_t02_t03_t04_build_exact_valid_six_event_six_binding_product_trace"
)
prepayment_case.setUp()
old_traces = {
    "T01": _valid_t01()[-1].authoritative_trace,
    "T02": prepayment_case.build_case(PrepaymentScenarioKind.PRICE_INCREASE)[-1],
    "T03": prepayment_case.build_case(PrepaymentScenarioKind.PRICE_DECREASE)[-1],
    "T04": prepayment_case.build_case(PrepaymentScenarioKind.PAYEE_CHANGE)[-1],
    "T09": _valid_t09()[-1].authoritative_trace,
    "T10": _valid_t10()[2].authoritative_trace,
    "T12": _valid_t12()[-1].authoritative_trace,
}
old_hashes = {task_id: digest(trace) for task_id, trace in old_traces.items()}
assert old_hashes == EXPECTED_OLD_TRACE_HASHES, old_hashes
for task_id, trace in old_traces.items():
    assert trace is not None
    assert validate_product_authoritative_trace(trace).status is TraceValidationStatus.VALID
    print(f"{task_id}_trace_sha256={old_hashes[task_id]}")

scenario = load_scenario(ROOT / "samples/scenarios/S01_normal.json")
new_cases = {
    "T07": AttackOverlay(
        attack_id="RV-T07-RENAMED",
        title="renamed amount case",
        source="independent",
        untrusted_content="offline",
        proposed_overrides={"request.amount": "699.00"},
        source_type=SourceType.WEB_UNTRUSTED,
        source_ref="rv-unrelated-amount",
    ),
    "T08": AttackOverlay(
        attack_id="RV-T08-RENAMED",
        title="renamed payee case",
        source="independent",
        untrusted_content="offline",
        proposed_overrides={"request.payee": "payee-evil"},
        source_type=SourceType.LLM_GENERATED,
        source_ref="rv-unrelated-payee",
    ),
}
for task_id, overlay in new_cases.items():
    result = evaluate_attack_overlay(scenario, overlay)
    trace = result.authoritative_trace
    assert trace is not None, task_id
    validation = validate_product_authoritative_trace(trace)
    assert validation.status is TraceValidationStatus.VALID, (task_id, validation)
    assert len(trace.events) == 3
    assert len(trace.source_bindings) == 1
    assert [event.event_type for event in trace.events] == [
        "POLICY_DECISION_RECORDED",
        "LINEAGE_DECISION_RECORDED",
        "RESULT_RECORDED",
    ]
    print(f"{task_id}_renamed_case_trace_sha256={digest(trace)}")
print("T07_T08_registry_valid_and_id_independent=True")

toolkit = ROOT / "src/agentic_payment_experiment/attack_overlay_trace_toolkit.py"
profiles = ROOT / "src/agentic_payment_experiment/attack_overlay_trace_profiles.py"
source = toolkit.read_text(encoding="utf-8")
profile_source = profiles.read_text(encoding="utf-8")
tree = ast.parse(source)
function_names = {
    node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
assert not any(name.startswith("build_t07_") or name.startswith("build_t08_") for name in function_names)
assert source.count("assemble_product_trace(") == 1
for forbidden_call in (
    "evaluate_context_policy(",
    "resolve_fact_lineage(",
    "validate_request(",
    "evaluate_outcome(",
    "evaluate_attack_overlay(",
):
    assert forbidden_call not in source, forbidden_call
combined = source + profile_source
for forbidden in ("yaml.safe_load", "json.load(", "json.loads(", "eval(", "exec(", "import_module(", "__import__("):
    assert forbidden not in combined, forbidden
assert profile_source.count("AttackOverlayTraceProfile(") == 2
assert "task_id" not in source
print("family_single_path_static_guardrail=PASS")
print("RESULT=PASS")

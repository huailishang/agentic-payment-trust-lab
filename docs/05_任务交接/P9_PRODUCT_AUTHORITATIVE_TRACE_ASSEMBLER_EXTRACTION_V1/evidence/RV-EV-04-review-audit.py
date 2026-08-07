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
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_payment_experiment import assess_webshop_payment_fulfilment
from agentic_payment_experiment.authoritative_trace import (
    TraceValidationStatus,
    runtime_registry_hashes,
    validate_product_authoritative_trace,
)
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_payment_sidecar import WebShopPaymentSidecarTest

TASK_DIR = Path(__file__).resolve().parents[1]
EVID = Path(__file__).resolve().parent
FROZEN_TRACE = EVID / "BASELINE-trace-snapshots.json"
RV_BASELINE = EVID / "RV-EV-03-after-baseline.json"

EXPECTED_FILE_HASHES = {
    "scripts/validation/run_project_impact_baseline.py": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
    "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    "src/agentic_payment_experiment/webshop_runtime_gate.py": "5abf1a6f08060e111b6fbd9ba96809c2823ef07adee0e23b6d60a6c50c06bdef",
    "src/agentic_payment_experiment/webshop_payment_sidecar.py": "833a34c005061a69b29265190b3c609ec92278afe0bb0d48a700546b548436f7",
    "samples/evaluation/project_impact_baseline_v1.json": "4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5",
    "samples/evaluation/project_impact_t10_preflight_target_v1.json": "f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee",
    "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md": "4ab495ffcf7d6e21cbfc352a174f6f561b71e1bf6def7fe88f92b01974610836",
}
EXPECTED_TASK_HASHES = {
    "src/agentic_payment_experiment/webshop_trace_assembler.py": "725a6f55d061976f7217ba28b74ff15fce2f83adcc383350113e4eed6c550ed7",
    "src/agentic_payment_experiment/webshop_authoritative_trace.py": "9653277777d06ce8d2c65862765ec57c17874a9d311d2c5c9c117993a0feeac8",
    "src/agentic_payment_experiment/webshop_happy_path_authoritative_trace.py": "0914030118e47419e27cf964e851ef7307fb62ee6608e477592b7fdbd6d61ce1",
    "tests/test_webshop_trace_assembler.py": "4b7c71b086a12eacabcb18ba6fa863150dd5b4f85cab92cd096087c8e9468e50",
}
EXPECTED_REGISTRY_HASHES = {
    "formula_registry": "2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd",
    "projection_registry": "45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4",
    "profiles": "6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2",
    "runtime_contract": "4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e",
}
EXPECTED_TRACE_HASHES = {
    "T01": "7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906",
    "T10": "2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3",
}
EXPECTED_COMBINED_TRACE_HASH = "d913fc7d3a69abfb0c7774356a988a5e23cf3780a70523a03ced2672bec5ac4c"
EXPECTED_NON_TRACE = "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"
EXPECTED_BASELINE_FILE_HASH = "8d4304dce72bb4f3d572512ee4d09e2e4bd2ee06f34ec4e8e6b0887acf059d9a"
EXPECTED_NORMALIZED_HASH = "56a82f9ab99cd5d83ae0b1259c2cef9f6b6cdf2a1b7183c029ba7569ab332619"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_hash(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


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
        return "0" if text in {"-0", ""} else text
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or isinstance(value, (bool, int, str)):
        return value
    raise TypeError(f"unsupported snapshot value: {type(value)!r}")


def build_current_traces() -> dict[str, object]:
    _, _, t10_outcome, _ = _valid_t10()
    assert t10_outcome.authoritative_trace is not None

    case = WebShopPaymentSidecarTest(methodName="runTest")
    case.setUp()
    gate, _, payment, fulfillment = case.happy_path_inputs()
    t01_outcome = assess_webshop_payment_fulfilment(
        gate_outcome=gate,
        adaptation=case.adaptation,
        mandate=case.mandate,
        payment=payment,
        fulfillment=fulfillment,
    )
    assert t01_outcome.authoritative_trace is not None

    t01_validation = validate_product_authoritative_trace(t01_outcome.authoritative_trace)
    t10_validation = validate_product_authoritative_trace(t10_outcome.authoritative_trace)
    assert t01_validation.status is TraceValidationStatus.VALID
    assert t10_validation.status is TraceValidationStatus.VALID

    return {
        "T01": primitive(t01_outcome.authoritative_trace),
        "T10": primitive(t10_outcome.authoritative_trace),
    }


def non_trace_projection(report: dict[str, object]) -> list[dict[str, object]]:
    fields_to_keep = (
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
    task_results = report["task_results"]
    assert isinstance(task_results, list)
    by_id = {item["task_id"]: item for item in task_results}
    return [
        {
            "task_id": task_id,
            "actual": {
                field: by_id[task_id]["actual"].get(field)
                for field in fields_to_keep
            },
        }
        for task_id in sorted(by_id)
    ]


def import_boundary_audit() -> dict[str, object]:
    assembler_path = ROOT / "src/agentic_payment_experiment/webshop_trace_assembler.py"
    t01_path = ROOT / "src/agentic_payment_experiment/webshop_happy_path_authoritative_trace.py"
    t10_path = ROOT / "src/agentic_payment_experiment/webshop_authoritative_trace.py"

    def imported_modules(path: Path) -> set[str]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                modules.add(node.module or "")
            elif isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
        return modules

    t01_imports = imported_modules(t01_path)
    t10_imports = imported_modules(t10_path)
    assembler_imports = imported_modules(assembler_path)
    assert "webshop_trace_assembler" in t01_imports
    assert "webshop_trace_assembler" in t10_imports
    assert "webshop_authoritative_trace" not in t01_imports
    assert "webshop_happy_path_authoritative_trace" not in t10_imports

    assembler_source = assembler_path.read_text(encoding="utf-8")
    assembler_tree = ast.parse(assembler_source)
    public_defs = {
        node.name
        for node in assembler_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    expected_public_defs = {
        "create_source_binding",
        "create_relation",
        "create_event",
        "project_mandate",
        "project_order",
        "project_request",
        "project_governed_action",
        "project_payment",
        "project_action_binding_fact",
        "project_runtime_gate",
        "assemble_product_trace",
    }
    assert public_defs == expected_public_defs
    assert all("t01" not in name.lower() and "t10" not in name.lower() for name in public_defs)

    forbidden_import_roots = {"os", "pathlib", "socket", "subprocess", "requests", "urllib", "random", "time"}
    assert not {item.split(".")[0] for item in assembler_imports} & forbidden_import_roots

    called: set[str] = set()
    for node in ast.walk(assembler_tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    forbidden_calls = {
        "open",
        "read_text",
        "write_text",
        "getenv",
        "run",
        "Popen",
        "urlopen",
        "socket",
        "validate_request",
        "verify_governed_payment_action",
        "derive_known_payment_attempt_preflight",
        "observe_payment_execution_gate",
        "assess_payment_recovery",
        "derive_payment_status_conflict",
        "assess_lifecycle",
        "checkout_callback",
        "execute_payment",
    }
    assert not called & forbidden_calls
    return {
        "t01_imports_assembler": True,
        "t10_imports_assembler": True,
        "cross_builder_imports": [],
        "assembler_public_functions": sorted(public_defs),
        "assembler_forbidden_imports": [],
        "assembler_forbidden_calls": [],
    }


def main() -> None:
    frozen = json.loads(FROZEN_TRACE.read_text(encoding="utf-8"))
    current_traces = build_current_traces()
    assert current_traces == frozen["traces"]

    current_trace_hashes = {
        task_id: canonical_hash(trace)
        for task_id, trace in current_traces.items()
    }
    assert current_trace_hashes == EXPECTED_TRACE_HASHES
    current_combined_hash = canonical_hash(current_traces)
    assert current_combined_hash == EXPECTED_COMBINED_TRACE_HASH
    assert len(current_traces["T01"]["events"]) == 11
    assert len(current_traces["T01"]["source_bindings"]) == 10
    assert len(current_traces["T10"]["events"]) == 12
    assert len(current_traces["T10"]["source_bindings"]) == 11

    baseline = json.loads(RV_BASELINE.read_text(encoding="utf-8"))
    assert sha256_file(RV_BASELINE) == EXPECTED_BASELINE_FILE_HASH
    repeatability = baseline["repeatability"]
    assert repeatability["repeat_count"] == 3
    assert repeatability["all_identical"] is True
    assert repeatability["normalized_sha256"] == [EXPECTED_NORMALIZED_HASH] * 3
    assert baseline["metrics"]["product_observed_authoritative_trace_completeness_rate"] == {
        "count": 2,
        "denominator": 12,
        "rate": "0.166667",
    }
    assert baseline["metrics"]["governed_end_to_end_task_success_rate"] == {
        "count": 1,
        "denominator": 12,
        "rate": "0.083333",
    }
    valid_product_tasks = sorted(
        item["task_id"]
        for item in baseline["task_results"]
        if item["actual"]["product_observed_trace_status"] == "VALID"
    )
    assert valid_product_tasks == ["T01", "T10"]
    non_trace_hash = canonical_hash(non_trace_projection(baseline))
    assert non_trace_hash == EXPECTED_NON_TRACE

    file_hashes = {
        path: sha256_file(ROOT / path)
        for path in {**EXPECTED_FILE_HASHES, **EXPECTED_TASK_HASHES}
    }
    assert all(file_hashes[path] == expected for path, expected in EXPECTED_FILE_HASHES.items())
    assert all(file_hashes[path] == expected for path, expected in EXPECTED_TASK_HASHES.items())

    registry_hashes = dict(runtime_registry_hashes())
    assert registry_hashes == EXPECTED_REGISTRY_HASHES
    import_audit = import_boundary_audit()

    output = {
        "result": "PASS",
        "trace_snapshot_equal": True,
        "trace_hashes": current_trace_hashes,
        "combined_trace_hash": current_combined_hash,
        "trace_structure": {
            "T01": {"events": 11, "bindings": 10},
            "T10": {"events": 12, "bindings": 11},
        },
        "baseline_file_sha256": sha256_file(RV_BASELINE),
        "repeatability": repeatability,
        "product_trace": baseline["metrics"]["product_observed_authoritative_trace_completeness_rate"],
        "gesr": baseline["metrics"]["governed_end_to_end_task_success_rate"],
        "valid_product_tasks": valid_product_tasks,
        "non_trace_projection_sha256": non_trace_hash,
        "file_hashes": file_hashes,
        "registry_hashes": registry_hashes,
        "import_boundary": import_audit,
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from agentic_payment_experiment.authoritative_trace import runtime_registry_hashes
from agentic_payment_experiment.webshop_sidecar_trace_profiles import (
    SIDECAR_TRACE_PROFILES,
)

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
OUT = EVIDENCE / "EV-04-architecture-freeze.json"
SRC = ROOT / "src/agentic_payment_experiment"
SIDECAR = SRC / "webshop_payment_sidecar.py"
TOOLKIT = SRC / "webshop_sidecar_trace_toolkit.py"
PROFILES = SRC / "webshop_sidecar_trace_profiles.py"
T01_ADAPTER = SRC / "webshop_happy_path_authoritative_trace.py"
T09_ADAPTER = SRC / "webshop_unknown_payment_authoritative_trace.py"
EXPECTED_HASHES = {
    "runner": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
    "authoritative_trace": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    "gate": "5abf1a6f08060e111b6fbd9ba96809c2823ef07adee0e23b6d60a6c50c06bdef",
    "t10_builder": "9653277777d06ce8d2c65862765ec57c17874a9d311d2c5c9c117993a0feeac8",
    "baseline_fixture": "4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5",
    "t10_target_fixture": "f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee",
    "formula_registry": "2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd",
    "projection_registry": "45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4",
    "profiles": "6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2",
    "runtime_contract": "4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def calls(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                result.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                result.append(node.func.attr)
    return result


def main() -> None:
    profile_names = tuple(profile.profile_name for profile in SIDECAR_TRACE_PROFILES)
    assert profile_names == (
        "WEBSHOP_NORMAL_PURCHASE_V2",
        "WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2",
        "WEBSHOP_PAYMENT_STATUS_CONFLICT_V2",
    )

    sidecar_source = SIDECAR.read_text(encoding="utf-8")
    assert sidecar_source.count("webshop_sidecar_trace_toolkit") == 1
    assert sidecar_source.count("build_sidecar_product_trace(") == 1
    assert "webshop_happy_path_authoritative_trace" not in sidecar_source
    assert "webshop_unknown_payment_authoritative_trace" not in sidecar_source

    adapter_results = {}
    for path in (T01_ADAPTER, T09_ADAPTER):
        source = path.read_text(encoding="utf-8")
        line_count = len(source.splitlines())
        path_calls = calls(path)
        assert line_count <= 80
        for forbidden in (
            "create_event",
            "create_relation",
            "create_source_binding",
            "assemble_product_trace",
        ):
            assert forbidden not in path_calls
        adapter_results[path.name] = {
            "line_count": line_count,
            "calls": sorted(path_calls),
            "sha256": file_sha256(path),
        }

    assert not (SRC / "webshop_payment_status_conflict_authoritative_trace.py").exists()
    assert not (SRC / "webshop_t12_authoritative_trace.py").exists()
    t12_build_functions = []
    for path in SRC.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("build_t12_"):
                    t12_build_functions.append(f"{path.name}:{node.name}")
    assert t12_build_functions == []

    toolkit_source = TOOLKIT.read_text(encoding="utf-8")
    profiles_source = PROFILES.read_text(encoding="utf-8")
    combined = toolkit_source + profiles_source
    for forbidden in (
        "yaml.safe_load",
        "json.load(",
        "json.loads(",
        "eval(",
        "exec(",
        "import_module(",
        "__import__(",
        "PaymentStatusObservation",
        "derive_payment_status_conflict(",
        "assess_payment_recovery(",
        "assess_lifecycle(",
        "gate_webshop_buy_now(",
        "verify_governed_payment_action(",
    ):
        assert forbidden not in combined
    assert toolkit_source.count("assemble_product_trace(") == 1
    assert toolkit_source.count("create_event(") == 13
    for common_event in (
        "AUTHORITY_RECORDED",
        "REQUEST_RECORDED",
        "ACTION_RECORDED",
        "PAYMENT_CANDIDATE_RECORDED",
        "ACTION_BINDING_DECISION_RECORDED",
        "RUNTIME_DECISION_RECORDED",
        "PAYMENT_OUTCOME_RECORDED",
        "RESULT_RECORDED",
    ):
        assert toolkit_source.count(common_event) == 1
    for extension_event in (
        "FULFILMENT_OUTCOME_RECORDED",
        "RECOVERY_OUTCOME_RECORDED",
        "STATUS_CONFLICT_RECORDED",
    ):
        assert toolkit_source.count(extension_event) == 1
    assert toolkit_source.count("def _common_facts(") == 1
    assert toolkit_source.count("def _select_profile(") == 1
    assert toolkit_source.count("def build_sidecar_product_trace(") == 1

    actual_hashes = {
        "runner": file_sha256(ROOT / "scripts/validation/run_project_impact_baseline.py"),
        "authoritative_trace": file_sha256(SRC / "authoritative_trace.py"),
        "gate": file_sha256(SRC / "webshop_runtime_gate.py"),
        "t10_builder": file_sha256(SRC / "webshop_authoritative_trace.py"),
        "baseline_fixture": file_sha256(
            ROOT / "samples/evaluation/project_impact_baseline_v1.json"
        ),
        "t10_target_fixture": file_sha256(
            ROOT / "samples/evaluation/project_impact_t10_preflight_target_v1.json"
        ),
        **dict(runtime_registry_hashes()),
    }
    assert actual_hashes == EXPECTED_HASHES, {
        "actual": actual_hashes,
        "expected": EXPECTED_HASHES,
    }

    result = {
        "profile_count": len(SIDECAR_TRACE_PROFILES),
        "profile_names": profile_names,
        "sidecar_toolkit_import_count": sidecar_source.count(
            "webshop_sidecar_trace_toolkit"
        ),
        "sidecar_toolkit_call_count": sidecar_source.count(
            "build_sidecar_product_trace("
        ),
        "adapter_results": adapter_results,
        "t12_dedicated_builder_files": 0,
        "t12_dedicated_build_functions": t12_build_functions,
        "toolkit_line_count": len(toolkit_source.splitlines()),
        "profiles_line_count": len(profiles_source.splitlines()),
        "toolkit_assemble_call_count": toolkit_source.count(
            "assemble_product_trace("
        ),
        "frozen_hashes": actual_hashes,
    }
    OUT.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    print("profile_count=3")
    print("profile_names=" + ",".join(profile_names))
    print("sidecar_dedicated_builder_imports=0")
    print("sidecar_toolkit_builder_calls=1")
    print(
        "legacy_adapter_lines="
        + ",".join(
            f"{name}:{item['line_count']}" for name, item in adapter_results.items()
        )
    )
    print("legacy_adapter_assembly_calls=0")
    print("t12_dedicated_builder_files=0")
    print("t12_dedicated_build_functions=0")
    print("runtime_profile_loading=ABSENT")
    print("dynamic_eval_exec_import=ABSENT")
    print("toolkit_common_facts_implementations=1")
    print("toolkit_profile_selection_implementations=1")
    print("toolkit_assemble_calls=1")
    for key, value in actual_hashes.items():
        print(f"{key}_sha256={value}")
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

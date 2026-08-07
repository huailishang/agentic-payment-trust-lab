from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from agentic_payment_experiment.authoritative_trace import runtime_registry_hashes

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
OUT = EVIDENCE / "EV-04-boundary-and-freeze-audit.json"
ASSEMBLER = ROOT / "src/agentic_payment_experiment/webshop_trace_assembler.py"
T01_BUILDER = ROOT / "src/agentic_payment_experiment/webshop_happy_path_authoritative_trace.py"
T10_BUILDER = ROOT / "src/agentic_payment_experiment/webshop_authoritative_trace.py"
GATE = ROOT / "src/agentic_payment_experiment/webshop_runtime_gate.py"
SIDECAR = ROOT / "src/agentic_payment_experiment/webshop_payment_sidecar.py"
EXPECTED_HASHES = {
    "runner": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
    "authoritative_trace": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    "baseline_fixture": "4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5",
    "t10_target_fixture": "f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee",
    "gate": "5abf1a6f08060e111b6fbd9ba96809c2823ef07adee0e23b6d60a6c50c06bdef",
    "sidecar": "833a34c005061a69b29265190b3c609ec92278afe0bb0d48a700546b548436f7",
    "formula_registry": "2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd",
    "projection_registry": "45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4",
    "profiles": "6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2",
    "runtime_contract": "4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add(node.module or "")
    return modules


def called_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                names.add(node.func.attr)
    return names


def main() -> None:
    t01_imports = imported_modules(T01_BUILDER)
    t10_imports = imported_modules(T10_BUILDER)
    assert "webshop_trace_assembler" in t01_imports
    assert "webshop_trace_assembler" in t10_imports
    assert "webshop_authoritative_trace" not in t01_imports
    assert "webshop_happy_path_authoritative_trace" not in t10_imports

    assembler_imports = imported_modules(ASSEMBLER)
    assembler_calls = called_names(ASSEMBLER)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "urllib",
        "random",
        "time",
    }
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
    assert assembler_imports.isdisjoint(forbidden_imports)
    assert assembler_calls.isdisjoint(forbidden_calls)
    assembler_source = ASSEMBLER.read_text(encoding="utf-8")
    for forbidden in ("T01", "T10", "GateContext", "CURRENT.md", "evidence/"):
        assert forbidden not in assembler_source

    t01_source = T01_BUILDER.read_text(encoding="utf-8")
    t10_source = T10_BUILDER.read_text(encoding="utf-8")
    gate_source = GATE.read_text(encoding="utf-8")
    sidecar_source = SIDECAR.read_text(encoding="utf-8")
    assert t01_source.count("def build_t01_happy_path_trace(") == 1
    assert sidecar_source.count("build_t01_happy_path_trace(") == 1
    assert t10_source.count("def build_t10_duplicate_preflight_trace(") == 1
    assert gate_source.count("build_t10_duplicate_preflight_trace(") == 1
    assert "build_t01_happy_path_trace" not in gate_source
    assert "build_t10_duplicate_preflight_trace" not in sidecar_source

    actual_hashes = {
        "runner": file_sha256(ROOT / "scripts/validation/run_project_impact_baseline.py"),
        "authoritative_trace": file_sha256(
            ROOT / "src/agentic_payment_experiment/authoritative_trace.py"
        ),
        "baseline_fixture": file_sha256(
            ROOT / "samples/evaluation/project_impact_baseline_v1.json"
        ),
        "t10_target_fixture": file_sha256(
            ROOT / "samples/evaluation/project_impact_t10_preflight_target_v1.json"
        ),
        "gate": file_sha256(GATE),
        "sidecar": file_sha256(SIDECAR),
        **dict(runtime_registry_hashes()),
    }
    assert actual_hashes == EXPECTED_HASHES, {
        "actual": actual_hashes,
        "expected": EXPECTED_HASHES,
    }

    result = {
        "t01_imports_assembler": True,
        "t10_imports_assembler": True,
        "private_cross_builder_imports": [],
        "assembler_forbidden_imports": sorted(assembler_imports & forbidden_imports),
        "assembler_forbidden_calls": sorted(assembler_calls & forbidden_calls),
        "producer_calls": {
            "T01": ["webshop_payment_sidecar.py"],
            "T10": ["webshop_runtime_gate.py"],
        },
        "frozen_hashes": actual_hashes,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("t01_imports_assembler=True")
    print("t10_imports_assembler=True")
    print("private_cross_builder_imports=NONE")
    print("assembler_forbidden_imports=NONE")
    print("assembler_forbidden_calls=NONE")
    print("producer_calls=T01:webshop_payment_sidecar.py,T10:webshop_runtime_gate.py")
    for key, value in actual_hashes.items():
        print(f"{key}_sha256={value}")
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

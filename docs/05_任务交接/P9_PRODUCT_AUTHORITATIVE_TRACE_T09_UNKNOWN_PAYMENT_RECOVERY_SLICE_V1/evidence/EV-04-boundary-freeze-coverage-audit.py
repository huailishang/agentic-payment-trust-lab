from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from agentic_payment_experiment.authoritative_trace import runtime_registry_hashes

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
OUT = EVIDENCE / "EV-04-boundary-freeze-coverage.json"
BUILDER = ROOT / "src/agentic_payment_experiment/webshop_unknown_payment_authoritative_trace.py"
ASSEMBLER = ROOT / "src/agentic_payment_experiment/webshop_trace_assembler.py"
SIDECAR = ROOT / "src/agentic_payment_experiment/webshop_payment_sidecar.py"
GATE = ROOT / "src/agentic_payment_experiment/webshop_runtime_gate.py"
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


def imports_and_calls(path: Path) -> tuple[set[str], set[str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
    return imports, calls


def main() -> None:
    builder_imports, builder_calls = imports_and_calls(BUILDER)
    assembler_imports, assembler_calls = imports_and_calls(ASSEMBLER)
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
        "assess_payment_recovery",
        "assess_lifecycle",
        "verify_governed_payment_action",
        "gate_webshop_buy_now",
        "checkout_callback",
        "execute_payment",
    }
    assert builder_imports.isdisjoint(forbidden_imports)
    assert assembler_imports.isdisjoint(forbidden_imports)
    assert builder_calls.isdisjoint(forbidden_calls)
    assert assembler_calls.isdisjoint(forbidden_calls)
    builder_source = BUILDER.read_text(encoding="utf-8")
    assert "PaymentStatusObservation" not in builder_source
    for forbidden in ("run_project_impact_baseline", "CURRENT.md", "evidence/"):
        assert forbidden not in builder_source

    sidecar_source = SIDECAR.read_text(encoding="utf-8")
    gate_source = GATE.read_text(encoding="utf-8")
    assert sidecar_source.count("build_t01_happy_path_trace(") == 1
    assert sidecar_source.count("build_unknown_payment_recovery_trace(") == 1
    assert gate_source.count("build_t10_duplicate_preflight_trace(") == 1
    assert "build_unknown_payment_recovery_trace" not in gate_source
    assert "build_t10_duplicate_preflight_trace" not in sidecar_source

    actual_hashes = {
        "runner": file_sha256(ROOT / "scripts/validation/run_project_impact_baseline.py"),
        "authoritative_trace": file_sha256(
            ROOT / "src/agentic_payment_experiment/authoritative_trace.py"
        ),
        "gate": file_sha256(GATE),
        "t10_builder": file_sha256(
            ROOT / "src/agentic_payment_experiment/webshop_authoritative_trace.py"
        ),
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
        "builder_forbidden_imports": sorted(builder_imports & forbidden_imports),
        "builder_forbidden_calls": sorted(builder_calls & forbidden_calls),
        "assembler_forbidden_imports": sorted(assembler_imports & forbidden_imports),
        "assembler_forbidden_calls": sorted(assembler_calls & forbidden_calls),
        "producer_coverage": {
            "T01": "webshop_payment_sidecar.py",
            "T09": "webshop_payment_sidecar.py",
            "T10": "webshop_runtime_gate.py",
        },
        "frozen_hashes": actual_hashes,
    }
    OUT.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    print("builder_forbidden_imports=NONE")
    print("builder_forbidden_calls=NONE")
    print("assembler_forbidden_imports=NONE")
    print("assembler_forbidden_calls=NONE")
    print("producer_coverage=T01,T09,T10")
    print("producer_T01=webshop_payment_sidecar.py")
    print("producer_T09=webshop_payment_sidecar.py")
    print("producer_T10=webshop_runtime_gate.py")
    for key, value in actual_hashes.items():
        print(f"{key}_sha256={value}")
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

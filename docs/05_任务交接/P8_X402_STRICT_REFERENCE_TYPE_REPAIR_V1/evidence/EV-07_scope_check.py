from __future__ import annotations

import ast
import hashlib
import subprocess
from pathlib import Path


BASELINE = "8acaa9e4319240d258f14d8a23b1f15cc71d09b6"
REPAIR_FILES = (
    Path("src/agentic_payment_experiment/adapters/x402.py"),
    Path("tests/test_x402_adapter.py"),
    Path("docs/05_任务交接/P8_X402_STRICT_REFERENCE_TYPE_REPAIR_V1/REPORT.md"),
    Path("docs/05_任务交接/P8_X402_STRICT_REFERENCE_TYPE_REPAIR_V1/evidence/EV-02_rv_ev_07_counterexample.py"),
    Path("docs/05_任务交接/P8_X402_STRICT_REFERENCE_TYPE_REPAIR_V1/evidence/EV-07_scope_check.py"),
)
PARENT_PRESERVED_HASHES = {
    Path("src/agentic_payment_experiment/x402_conformance.py"): "5240369a4620b5339538f62a294564fe2d4cda06c11b5a4aefb00fdb16cc9b2e",
    Path("tests/test_x402_conformance.py"): "78f952ec07d6b3a8a90296a001bbaeaef8de96c3ebec34744d115fc72d001526",
    Path("samples/protocols/x402/x402_offline_cases_v1.json"): "5e34d70667faf7c2d91e0bf7b70086a7bb106bb552a85989f6f6f12915292153",
    Path("src/agentic_payment_experiment/adapters/__init__.py"): "d6ea7127d18c791b51e15e603966ca03e8ed90f3ec7af21ae19ce1f9074e6754",
    Path("docs/04_验证体系/x402离线一致性验证方案_v1.md"): "5edd674080d1526aca16bd8370d2bee83123dbcaec68c04cebdc2e271653a9d6",
}
PARENT_REPAIR_INPUT_HASHES = {
    Path("src/agentic_payment_experiment/adapters/x402.py"): "d863aa463cb0dce6b3c1bd262d68179b8bb4ec907e3d7e4f5247cd919a4d2812",
    Path("tests/test_x402_adapter.py"): "521e604a05809f69b2aa8ff8e2aeefa0f4dc1b6cfdec9470c5c5bc5cf85e257f",
}
FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "boto3",
    "httpx",
    "requests",
    "socket",
    "subprocess",
    "urllib",
    "web3",
}
FORBIDDEN_TEXT_COERCION_SNIPPETS = (
    'str(proof["proof_ref"])',
    'str(proof["request_ref"])',
    'str(proof["requirement_ref"])',
    'str(proof["resource_ref"])',
    'str(proof["payee"])',
    'str(requirement["requirement_id"])',
    'str(requirement["resource_ref"])',
    'str(requirement["payee"])',
    'str(context["user_ref"])',
    'str(context["agent_ref"])',
    'str(context["authority_ref"])',
    'str(item["execution_id"])',
    'str(item["proof_ref"])',
)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def whitespace_findings(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), start=1):
        if line.endswith((" ", "\t")):
            findings.append(f"{path}:{number}: trailing whitespace")
    if text and not text.endswith("\n"):
        findings.append(f"{path}: missing final newline")
    return findings


def forbidden_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    findings: list[str] = []
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots = [alias.name.split(".", 1)[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots = [node.module.split(".", 1)[0]]
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                findings.append(f"{path}:{getattr(node, 'lineno', '?')}: forbidden import {root}")
    return findings


def main() -> int:
    failures: list[str] = []
    head = run("git", "rev-parse", "HEAD").stdout.strip()
    print(f"HEAD={head}")
    print(f"BASELINE={BASELINE}")
    print(f"HEAD_BASELINE_UNCHANGED={head == BASELINE}")
    if head != BASELINE:
        failures.append("baseline HEAD changed")

    missing = [str(path) for path in REPAIR_FILES if not path.exists()]
    print(f"MISSING_REPAIR_FILES={missing}")
    failures.extend(f"missing repair file: {path}" for path in missing)

    print("PARENT_INPUT_TO_REPAIR_OUTPUT=")
    for path, parent_hash in PARENT_REPAIR_INPUT_HASHES.items():
        current = sha256(path)
        print(f"  {path}: parent={parent_hash} current={current} changed={current != parent_hash}")
        if current == parent_hash:
            failures.append(f"repair file did not change from rejected parent: {path}")

    print("PARENT_PRESERVED_HASHES=")
    for path, expected in PARENT_PRESERVED_HASHES.items():
        actual = sha256(path)
        matches = actual == expected
        print(f"  {path}: expected={expected} actual={actual} matches={matches}")
        if not matches:
            failures.append(f"parent file changed outside repair scope: {path}")

    whitespace: list[str] = []
    for path in REPAIR_FILES:
        if path.exists():
            whitespace.extend(whitespace_findings(path))
    print(f"REPAIR_FILE_WHITESPACE_FINDINGS={len(whitespace)}")
    for finding in whitespace:
        print(f"  {finding}")
    failures.extend(whitespace)

    source = Path("src/agentic_payment_experiment/adapters/x402.py")
    imports = forbidden_imports(source)
    print(f"FORBIDDEN_NETWORK_OR_PROCESS_IMPORTS={imports}")
    failures.extend(imports)

    source_text = source.read_text(encoding="utf-8")
    coercions = [snippet for snippet in FORBIDDEN_TEXT_COERCION_SNIPPETS if snippet in source_text]
    print(f"FORBIDDEN_EXTERNAL_TEXT_COERCIONS={coercions}")
    failures.extend(f"forbidden external text coercion: {snippet}" for snippet in coercions)
    strict_markers = (
        "def _required_text_field_errors",
        "x402_string_invalid:",
        'text_fields["resource_delivery.failure_code"]',
    )
    missing_markers = [marker for marker in strict_markers if marker not in source_text]
    print(f"MISSING_STRICT_VALIDATION_MARKERS={missing_markers}")
    failures.extend(f"missing strict validation marker: {marker}" for marker in missing_markers)

    print("REPAIR_FILE_SHA256=")
    for path in REPAIR_FILES:
        if path.exists():
            print(f"  {sha256(path)}  {path.as_posix()}")

    global_check = run("git", "diff", "--check")
    print(f"GLOBAL_GIT_DIFF_CHECK_EXIT={global_check.returncode}")
    if global_check.returncode != 0:
        lines = (global_check.stdout + global_check.stderr).splitlines()
        print(f"GLOBAL_GIT_DIFF_CHECK_LINES={len(lines)}")
        print("GLOBAL_FINDINGS_CLASSIFICATION=inherited/out-of-scope unless listed as a repair file")
        for line in lines[:20]:
            print(f"  {line}")

    ai_bridge_exists = Path(".ai-bridge").exists()
    print(f"AI_BRIDGE_EXISTS={ai_bridge_exists}")
    if ai_bridge_exists:
        failures.append("unexpected .ai-bridge directory exists")

    print(f"REPAIR_SCOPE_RESULT={'PASS' if not failures else 'FAIL'}")
    if failures:
        print("FAILURES=")
        for failure in failures:
            print(f"  {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

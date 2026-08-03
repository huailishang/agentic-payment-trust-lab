from __future__ import annotations

import ast
import hashlib
import subprocess
from pathlib import Path


BASELINE = "8acaa9e4319240d258f14d8a23b1f15cc71d09b6"
TASK_FILES = (
    Path("src/agentic_payment_experiment/adapters/x402.py"),
    Path("src/agentic_payment_experiment/x402_conformance.py"),
    Path("src/agentic_payment_experiment/adapters/__init__.py"),
    Path("tests/test_x402_adapter.py"),
    Path("tests/test_x402_conformance.py"),
    Path("samples/protocols/x402/x402_offline_cases_v1.json"),
    Path("docs/04_验证体系/x402离线一致性验证方案_v1.md"),
    Path("docs/05_任务交接/P8_X402_OFFLINE_CONFORMANCE_HARNESS_V1/REPORT.md"),
)
ALLOWED_PREFIXES = (
    "src/agentic_payment_experiment/adapters/x402.py",
    "src/agentic_payment_experiment/x402_conformance.py",
    "src/agentic_payment_experiment/adapters/__init__.py",
    "tests/test_x402_adapter.py",
    "tests/test_x402_conformance.py",
    "samples/protocols/x402/",
    "docs/04_验证体系/x402离线一致性验证方案_v1.md",
    "docs/05_任务交接/P8_X402_OFFLINE_CONFORMANCE_HARNESS_V1/",
)
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
CODE_FILES = TASK_FILES[:2]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def changed_paths() -> list[str]:
    result = run(
        "git",
        "-c",
        "core.quotepath=false",
        "status",
        "--porcelain",
        "--untracked-files=all",
    )
    paths: list[str] = []
    for raw in result.stdout.splitlines():
        if len(raw) < 4:
            continue
        path = raw[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path.strip('"').replace("\\", "/"))
    return paths


def task_related(path: str) -> bool:
    lower = path.lower()
    return (
        "x402" in lower
        or "p8_x402_offline_conformance_harness_v1" in lower
        or path == "src/agentic_payment_experiment/adapters/__init__.py"
    )


def is_allowed(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_PREFIXES)


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
        if isinstance(node, ast.Import):
            roots = [alias.name.split(".", 1)[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots = [node.module.split(".", 1)[0]]
        else:
            continue
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

    missing = [str(path) for path in TASK_FILES if not path.exists()]
    print(f"MISSING_TASK_FILES={missing}")
    failures.extend(f"missing task file: {path}" for path in missing)

    changes = changed_paths()
    attributed = sorted(path for path in changes if task_related(path))
    unexpected = sorted(path for path in attributed if not is_allowed(path))
    print("TASK_ATTRIBUTED_PATHS=")
    for path in attributed:
        print(f"  {path}")
    print(f"UNEXPECTED_TASK_PATHS={unexpected}")
    failures.extend(f"unexpected task path: {path}" for path in unexpected)

    tracked_check_targets = [
        str(path)
        for path in TASK_FILES
        if path.exists() and run("git", "ls-files", "--error-unmatch", str(path)).returncode == 0
    ]
    diff_check = run("git", "diff", "--check", "--", *tracked_check_targets)
    print(f"TASK_SCOPED_GIT_DIFF_CHECK_EXIT={diff_check.returncode}")
    if diff_check.stdout:
        print(diff_check.stdout, end="")
    if diff_check.stderr:
        print(diff_check.stderr, end="")
    if diff_check.returncode != 0:
        failures.append("task-scoped git diff --check failed")

    whitespace: list[str] = []
    for path in TASK_FILES:
        if path.exists():
            whitespace.extend(whitespace_findings(path))
    print(f"TASK_FILE_WHITESPACE_FINDINGS={len(whitespace)}")
    for finding in whitespace:
        print(f"  {finding}")
    failures.extend(whitespace)

    imports: list[str] = []
    for path in CODE_FILES:
        if path.exists():
            imports.extend(forbidden_imports(path))
    print(f"FORBIDDEN_NETWORK_OR_PROCESS_IMPORTS={imports}")
    failures.extend(imports)

    ai_bridge_exists = Path(".ai-bridge").exists()
    print(f"AI_BRIDGE_EXISTS={ai_bridge_exists}")
    if ai_bridge_exists:
        failures.append("unexpected .ai-bridge directory exists")

    print("TASK_FILE_SHA256=")
    for path in TASK_FILES:
        if path.exists():
            print(f"  {sha256(path)}  {path.as_posix()}")

    global_check = run("git", "diff", "--check")
    print(f"GLOBAL_GIT_DIFF_CHECK_EXIT={global_check.returncode}")
    if global_check.returncode != 0:
        lines = (global_check.stdout + global_check.stderr).splitlines()
        print(f"GLOBAL_GIT_DIFF_CHECK_LINES={len(lines)}")
        print("GLOBAL_FINDINGS_CLASSIFICATION=inherited/out-of-scope unless path is listed above")
        for line in lines[:20]:
            print(f"  {line}")

    print(f"TASK_SCOPE_RESULT={'PASS' if not failures else 'FAIL'}")
    if failures:
        print("FAILURES=")
        for failure in failures:
            print(f"  {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

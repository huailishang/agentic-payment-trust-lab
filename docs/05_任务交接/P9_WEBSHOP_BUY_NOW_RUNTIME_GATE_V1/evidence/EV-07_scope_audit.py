from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
BASELINE = "8acaa9e4319240d258f14d8a23b1f15cc71d09b6"
TASK_FILES = (
    "src/agentic_payment_experiment/webshop_runtime_gate.py",
    "src/agentic_payment_experiment/__init__.py",
    "tests/test_webshop_runtime_gate.py",
    "docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md",
    "docs/02_未来规划/验证体系与后续环境统一路线_20260801.md",
)
P9_B1_EXPECTED_HASHES = {
    "src/agentic_payment_experiment/adapters/webshop.py": "035e6bb20d44b0a52be3f6adab2830c402e01f53839e917698343761c5481ec4",
    "samples/external/webshop/pre_buy_now_candidate_v1.json": "6e9d67c3b787cc2d9202bd22b30dec88bf9f920dfa3741bdeb364108a2a3c8e5",
    "scripts/validation/webshop/export_webshop_commerce_fixture.py": "aae4c6109586f20e6e78c35ba48b6c94dfee76e478134842731140f50a9382f0",
}
INHERITED_RULE_FILES = (
    "src/agentic_payment_experiment/payment_execution.py",
    "src/agentic_payment_experiment/trusted_execution/context_policy.py",
)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


head = run("git", "rev-parse", "HEAD")
if head.returncode != 0:
    raise SystemExit(head.stderr)
main_head = head.stdout.strip()
if main_head != BASELINE:
    raise AssertionError(f"HEAD changed: {main_head}")

files = []
for relative in TASK_FILES:
    path = ROOT / relative
    if not path.is_file():
        raise AssertionError(f"missing task file: {relative}")
    text = path.read_text(encoding="utf-8")
    if not relative.endswith(".md"):
        trailing = [
            line_number
            for line_number, line in enumerate(text.splitlines(), 1)
            if line.rstrip(" \t") != line
        ]
        if trailing:
            raise AssertionError(f"trailing whitespace: {relative}:{trailing}")
    files.append(
        {"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)}
    )

for relative, expected in P9_B1_EXPECTED_HASHES.items():
    actual = sha256(ROOT / relative)
    if actual != expected:
        raise AssertionError(
            f"P9-B1 file changed: {relative}; expected {expected}; got {actual}"
        )

for relative in (
    "src/agentic_payment_experiment/models.py",
    "src/agentic_payment_experiment/validator.py",
):
    diff = run("git", "diff", "--", relative)
    if diff.returncode != 0 or diff.stdout:
        raise AssertionError(f"prohibited file changed: {relative}")

source_path = ROOT / TASK_FILES[0]
source = source_path.read_text(encoding="utf-8")
tree = ast.parse(source)
imports = []
called = []
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imports.extend(alias.name for alias in node.names)
    elif isinstance(node, ast.ImportFrom):
        imports.append(node.module or "")
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            called.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            called.append(node.func.attr)
for forbidden in (
    "gym",
    "web_agent_site",
    "pyserini",
    "flask",
    "selenium",
    "playwright",
    "requests",
    "urllib",
    "socket",
    "subprocess",
    "os",
    "pathlib",
):
    if any(name == forbidden or name.startswith(forbidden + ".") for name in imports):
        raise AssertionError(f"forbidden import: {forbidden}")
for forbidden_call in (
    "open",
    "read_text",
    "write_text",
    "getenv",
    "run",
    "Popen",
    "urlopen",
    "socket",
):
    if forbidden_call in called:
        raise AssertionError(f"forbidden production call: {forbidden_call}")
if "click[buy now]" in source.lower() or "SimServer" in source:
    raise AssertionError("production gate constructs a WebShop action")

tracked_diff_check = run(
    "git",
    "diff",
    "--check",
    "--",
    "src/agentic_payment_experiment/__init__.py",
    "docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md",
    "docs/02_未来规划/验证体系与后续环境统一路线_20260801.md",
)
if tracked_diff_check.returncode != 0:
    raise AssertionError(tracked_diff_check.stdout + tracked_diff_check.stderr)

allowed_status = run("git", "status", "--short", "--", *TASK_FILES)
inherited_status = run("git", "status", "--short", "--", *INHERITED_RULE_FILES)

payload = {
    "baseline_head": BASELINE,
    "main_head": main_head,
    "main_head_matches_baseline": True,
    "task_files": files,
    "p9_b1_files_unchanged": [
        {"path": path, "sha256": digest}
        for path, digest in P9_B1_EXPECTED_HASHES.items()
    ],
    "models_diff_empty": True,
    "validator_diff_empty": True,
    "production_imports": sorted(imports),
    "production_calls": sorted(set(called)),
    "allowed_scope_git_status": allowed_status.stdout.splitlines(),
    "inherited_rule_status_preserved": inherited_status.stdout.splitlines(),
    "webshop_runtime_executed": False,
    "buy_now_executed": False,
    "simserver_done_called": False,
    "network_or_api_called": False,
    "environment_or_dependency_changed": False,
    "payment_or_fulfilment_executed": False,
    "ui_modified": False,
    "commit_executed": False,
    "push_executed": False,
}
output = Path(__file__).with_name("EV-07.scope_audit.json")
output.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

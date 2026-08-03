from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
BASELINE = "8acaa9e4319240d258f14d8a23b1f15cc71d09b6"
TASK_FILES = (
    "src/agentic_payment_experiment/webshop_payment_sidecar.py",
    "src/agentic_payment_experiment/__init__.py",
    "tests/test_webshop_payment_sidecar.py",
    "docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md",
    "docs/02_未来规划/验证体系与后续环境统一路线_20260801.md",
)
EXPECTED_UNCHANGED = {
    "src/agentic_payment_experiment/webshop_runtime_gate.py": "5aadec69b787825dc7909276d1ea6881f1620d911d4b7f83839bf3400f39e368",
    "src/agentic_payment_experiment/adapters/webshop.py": "035e6bb20d44b0a52be3f6adab2830c402e01f53839e917698343761c5481ec4",
    "samples/external/webshop/pre_buy_now_candidate_v1.json": "6e9d67c3b787cc2d9202bd22b30dec88bf9f920dfa3741bdeb364108a2a3c8e5",
    "scripts/validation/webshop/export_webshop_commerce_fixture.py": "aae4c6109586f20e6e78c35ba48b6c94dfee76e478134842731140f50a9382f0",
    "src/agentic_payment_experiment/payment_recovery.py": "c8c2d7a71b4293105ea2365a7486f143b4ad2f8a9ea10d842bf00dae522107de",
    "src/agentic_payment_experiment/payment_status_conflict.py": "75c87e9382f29b045caf987a4d6e92281395748189df505294a210bb1fbbbf4d",
    "src/agentic_payment_experiment/lifecycle.py": "8fc6df6f56d5aad47cc9c449340307324150f12760f0a124bd32296a659a4c92",
    "src/agentic_payment_experiment/remediation.py": "43a76921fe3058edee4b1778b73949a00dc76a44de08a36f8a3d4e8cdb8c15d3",
}


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


head = run("git", "rev-parse", "HEAD")
if head.returncode != 0:
    raise SystemExit(head.stderr)
current_head = head.stdout.strip()
if current_head != BASELINE:
    raise AssertionError(f"HEAD changed: {current_head}")

unchanged = []
for relative, expected in EXPECTED_UNCHANGED.items():
    actual = sha256(ROOT / relative)
    if actual != expected:
        raise AssertionError(f"protected file changed: {relative}; {actual} != {expected}")
    unchanged.append({"path": relative, "sha256": actual})

for relative in ("src/agentic_payment_experiment/models.py", "src/agentic_payment_experiment/validator.py"):
    diff = run("git", "diff", "--", relative)
    if diff.returncode != 0 or diff.stdout:
        raise AssertionError(f"prohibited tracked file changed: {relative}")

source = (ROOT / TASK_FILES[0]).read_text(encoding="utf-8")
tree = ast.parse(source)
imports: list[str] = []
calls: list[str] = []
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imports.extend(alias.name for alias in node.names)
    elif isinstance(node, ast.ImportFrom):
        imports.append(node.module or "")
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            calls.append(node.func.attr)
for forbidden in ("gym", "web_agent_site", "pyserini", "flask", "selenium", "playwright", "requests", "urllib", "socket", "subprocess", "os", "pathlib"):
    if any(name == forbidden or name.startswith(forbidden + ".") for name in imports):
        raise AssertionError(f"forbidden production import: {forbidden}")
for forbidden_call in ("open", "read_text", "write_text", "getenv", "run", "Popen", "urlopen", "socket", "checkout_callback", "execute_payment"):
    if forbidden_call in calls:
        raise AssertionError(f"forbidden production call: {forbidden_call}")

files = []
for relative in TASK_FILES:
    path = ROOT / relative
    if not path.is_file():
        raise AssertionError(f"missing task file: {relative}")
    files.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)})

payload = {
    "baseline_head": BASELINE,
    "current_head": current_head,
    "head_matches_baseline": True,
    "task_files": files,
    "protected_files_unchanged": unchanged,
    "models_diff_empty": True,
    "validator_diff_empty": True,
    "production_imports": sorted(imports),
    "production_calls": sorted(set(calls)),
    "webshop_runtime_executed": False,
    "buy_now_executed": False,
    "payment_executed": False,
    "retry_executed": False,
    "status_query_executed": False,
    "async_callback_executed": False,
    "fulfilment_executed": False,
    "refund_or_dispute_executed": False,
    "network_or_api_called": False,
    "environment_or_dependency_changed": False,
    "ui_modified": False,
    "commit_executed": False,
    "push_executed": False,
}
output = Path(__file__).with_name("EV-06.scope_audit.json")
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

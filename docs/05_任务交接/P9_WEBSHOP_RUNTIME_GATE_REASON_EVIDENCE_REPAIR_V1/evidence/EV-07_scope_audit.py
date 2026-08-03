from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
BASELINE = "8acaa9e4319240d258f14d8a23b1f15cc71d09b6"
TASK_FILES = (
    "src/agentic_payment_experiment/payment_execution.py",
    "tests/trusted_execution/test_payment_binding.py",
    "tests/test_webshop_runtime_gate.py",
    "docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md",
    "docs/02_未来规划/验证体系与后续环境统一路线_20260801.md",
)
UNCHANGED_HASHES = {
    "src/agentic_payment_experiment/trusted_execution/context_policy.py": "be5a343ac0f48967b4b861f9b0a0c041d3f87406e6d82df1c366cb6ca810ac56",
    "src/agentic_payment_experiment/webshop_runtime_gate.py": "5aadec69b787825dc7909276d1ea6881f1620d911d4b7f83839bf3400f39e368",
    "src/agentic_payment_experiment/adapters/webshop.py": "035e6bb20d44b0a52be3f6adab2830c402e01f53839e917698343761c5481ec4",
    "samples/external/webshop/pre_buy_now_candidate_v1.json": "6e9d67c3b787cc2d9202bd22b30dec88bf9f920dfa3741bdeb364108a2a3c8e5",
    "scripts/validation/webshop/export_webshop_commerce_fixture.py": "aae4c6109586f20e6e78c35ba48b6c94dfee76e478134842731140f50a9382f0",
}


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
assert main_head == BASELINE, (main_head, BASELINE)

files = []
for relative in TASK_FILES:
    path = ROOT / relative
    assert path.is_file(), relative
    text = path.read_text(encoding="utf-8")
    if relative.endswith(".py"):
        trailing = [
            number
            for number, line in enumerate(text.splitlines(), 1)
            if line.rstrip(" \t") != line
        ]
        assert not trailing, (relative, trailing)
        ast.parse(text)
    files.append(
        {
            "path": relative,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    )

unchanged = []
for relative, expected in UNCHANGED_HASHES.items():
    actual = sha256(ROOT / relative)
    assert actual == expected, (relative, expected, actual)
    unchanged.append({"path": relative, "sha256": actual})

for relative in (
    "src/agentic_payment_experiment/models.py",
    "src/agentic_payment_experiment/validator.py",
):
    diff = run("git", "diff", "--", relative)
    assert diff.returncode == 0 and not diff.stdout, relative

check = run(
    "git",
    "diff",
    "--check",
    "--",
    "src/agentic_payment_experiment/payment_execution.py",
    "tests/trusted_execution/test_payment_binding.py",
    "tests/test_webshop_runtime_gate.py",
    "docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md",
    "docs/02_未来规划/验证体系与后续环境统一路线_20260801.md",
)
assert check.returncode == 0, check.stdout + check.stderr

payment_source = (ROOT / "src/agentic_payment_experiment/payment_execution.py").read_text(
    encoding="utf-8"
)
assert "click[buy now]" not in payment_source.lower()
assert "SimServer" not in payment_source
assert "requests" not in payment_source
assert "subprocess" not in payment_source
assert "socket" not in payment_source

payload = {
    "schema": "runtime-gate-reason-repair-scope-audit/v1",
    "baseline_head": BASELINE,
    "main_head": main_head,
    "main_head_matches_baseline": True,
    "task_files": files,
    "unchanged_protected_files": unchanged,
    "models_diff_empty": True,
    "validator_diff_empty": True,
    "context_policy_hash_preserved": True,
    "webshop_wrapper_hash_preserved": True,
    "p9_b1_hashes_preserved": True,
    "webshop_runtime_executed": False,
    "buy_now_executed": False,
    "simserver_done_called": False,
    "payment_or_fulfilment_executed": False,
    "ui_modified": False,
    "network_or_api_called": False,
    "environment_or_dependency_changed": False,
    "commit_executed": False,
    "push_executed": False,
    "history_rewrite_executed": False,
}
output = Path(__file__).with_name("EV-07.scope_audit.json")
output.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

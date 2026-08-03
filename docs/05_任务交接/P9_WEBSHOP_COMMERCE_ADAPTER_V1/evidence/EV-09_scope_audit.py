from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
BASELINE = "8acaa9e4319240d258f14d8a23b1f15cc71d09b6"
TASK_FILES = (
    "src/agentic_payment_experiment/adapters/webshop.py",
    "src/agentic_payment_experiment/adapters/__init__.py",
    "scripts/validation/webshop/export_webshop_commerce_fixture.py",
    "samples/external/webshop/pre_buy_now_candidate_v1.json",
    "tests/test_webshop_adapter.py",
    "docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md",
    "docs/02_未来规划/验证体系与后续环境统一路线_20260801.md",
)
PROHIBITED_PRODUCT_FILES = (
    "src/agentic_payment_experiment/models.py",
    "src/agentic_payment_experiment/runner.py",
    "src/agentic_payment_experiment/html_report.py",
    "src/agentic_payment_experiment/payment_execution.py",
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

files: list[dict[str, object]] = []
for relative in TASK_FILES:
    path = ROOT / relative
    if not path.is_file():
        raise AssertionError(f"missing task file: {relative}")
    text = path.read_text(encoding="utf-8")
    trailing = [
        number
        for number, line in enumerate(text.splitlines(), 1)
        if line.rstrip(" \t") != line and not relative.endswith(".md")
    ]
    if trailing:
        raise AssertionError(f"trailing whitespace in {relative}: {trailing}")
    files.append(
        {
            "path": relative,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    )

fixture = json.loads(
    (ROOT / "samples/external/webshop/pre_buy_now_candidate_v1.json").read_text(
        encoding="utf-8"
    )
)
if set(fixture["product"]) != {
    "asin",
    "title",
    "selected_options",
    "quantity",
    "unit_price",
    "order_total",
}:
    raise AssertionError("fixture product scope changed")
if fixture["buy_now_executed"] is not False:
    raise AssertionError("fixture claims Buy Now execution")
if len(fixture["actions_executed"]) != 2:
    raise AssertionError("fixture action scope changed")
if "click[buy now]" in json.dumps(fixture, ensure_ascii=False).lower():
    raise AssertionError("fixture contains executable Buy Now action")

adapter_path = ROOT / "src/agentic_payment_experiment/adapters/webshop.py"
tree = ast.parse(adapter_path.read_text(encoding="utf-8"))
imports: list[str] = []
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imports.extend(alias.name for alias in node.names)
    elif isinstance(node, ast.ImportFrom):
        imports.append(node.module or "")
for forbidden in (
    "gym",
    "web_agent_site",
    "pyserini",
    "spacy",
    "torch",
    "requests",
    "urllib",
    "socket",
    "subprocess",
    "os",
    "pathlib",
):
    if any(name == forbidden or name.startswith(forbidden + ".") for name in imports):
        raise AssertionError(f"forbidden adapter import: {forbidden}")

models_diff = run("git", "diff", "--", "src/agentic_payment_experiment/models.py")
if models_diff.returncode != 0 or models_diff.stdout:
    raise AssertionError("models.py changed")

prohibited_status = run("git", "status", "--short", "--", *PROHIBITED_PRODUCT_FILES)
# Some excluded files contain inherited pre-task changes. Preserve and report them;
# they are not attributed to P9-B1.
allowed_status = run("git", "status", "--short", "--", *TASK_FILES)

payload = {
    "baseline_head": BASELINE,
    "main_head": main_head,
    "main_head_matches_baseline": main_head == BASELINE,
    "task_files": files,
    "fixture": {
        "bytes": (ROOT / TASK_FILES[3]).stat().st_size,
        "sha256": sha256(ROOT / TASK_FILES[3]),
        "product_count": 1,
        "actions_executed": fixture["actions_executed"],
        "buy_now_available": fixture["buy_now_available"],
        "buy_now_executed": fixture["buy_now_executed"],
    },
    "adapter_imports": sorted(imports),
    "models_diff_empty": models_diff.stdout == "",
    "allowed_scope_git_status": allowed_status.stdout.splitlines(),
    "inherited_excluded_status_preserved": prohibited_status.stdout.splitlines(),
    "webshop_runtime_executed": False,
    "network_or_api_called": False,
    "environment_changed": False,
    "buy_now_executed": False,
    "authorization_decision_created": False,
    "payment_or_order_side_effect_created": False,
    "commit_executed": False,
    "push_executed": False,
}
if not payload["main_head_matches_baseline"]:
    raise AssertionError("HEAD changed")

output = Path(__file__).with_name("EV-09.scope_audit.json")
output.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

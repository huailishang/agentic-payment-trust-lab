from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/evidence"
manifest = json.loads((EVIDENCE / "immutable_manifest.json").read_text(encoding="utf-8"))

missing: list[str] = []
changed: list[dict[str, str]] = []
for relative, expected in sorted(manifest["files"].items()):
    path = ROOT / relative
    if not path.is_file():
        missing.append(relative)
        continue
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        changed.append({"path": relative, "expected": expected, "actual": actual})

head = subprocess.run(
    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True
).stdout.strip()
current_status = subprocess.run(
    ["git", "-c", "core.quotePath=false", "status", "--short"],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=True,
).stdout.splitlines()
initial_stdout = (EVIDENCE / "EV-01.stdout.log").read_text(encoding="utf-8").splitlines()
try:
    status_index = initial_stdout.index("=== STATUS ===")
    initial_status = initial_stdout[status_index + 1 :]
except ValueError:
    initial_status = []

allowed_prefixes = (
    "CURRENT.md",
    "docs/03_架构设计/产品权威轨迹最小合同_v1.md",
    "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md",
    "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/",
)

def status_path(line: str) -> str:
    return line[3:] if len(line) >= 4 else line


def inherited(lines: list[str]) -> list[str]:
    result = []
    for line in lines:
        path = status_path(line)
        if any(path.startswith(prefix) for prefix in allowed_prefixes):
            continue
        result.append(line)
    return sorted(result)

initial_inherited = inherited(initial_status)
current_inherited = inherited(current_status)
diff_check = subprocess.run(
    ["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True
)

result = {
    "schema": "product-authoritative-trace-scope-audit/v1",
    "baseline_head": manifest["head"],
    "current_head": head,
    "head_unchanged": head == manifest["head"],
    "protected_file_count": len(manifest["files"]),
    "missing": missing,
    "changed": changed,
    "protected_files_unchanged": not missing and not changed,
    "initial_inherited_status": initial_inherited,
    "current_inherited_status": current_inherited,
    "inherited_status_unchanged": initial_inherited == current_inherited,
    "current_status": current_status,
    "diff_check_exit_code": diff_check.returncode,
    "diff_check_stdout": diff_check.stdout,
    "diff_check_stderr": diff_check.stderr,
}
result["all_pass"] = all(
    (
        result["head_unchanged"],
        result["protected_files_unchanged"],
        result["inherited_status_unchanged"],
        result["diff_check_exit_code"] == 0,
    )
)
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
if not result["all_pass"]:
    raise SystemExit(1)

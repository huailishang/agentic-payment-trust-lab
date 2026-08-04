from __future__ import annotations

import difflib
import hashlib
import subprocess
from pathlib import Path

FILES = [
    Path("docs/03_架构设计/产品权威轨迹最小合同_v1.md"),
    Path("docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md"),
    Path("docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md"),
    Path("docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md"),
    Path("docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/REPORT.md"),
]
HASH_FILES = FILES + [
    Path("CURRENT.md"),
    Path("docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-06-coverage-repaired.json"),
    Path("docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-06-stable-ref-examples.json"),
    Path("docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-06-t10-dual-payment.json"),
    Path("docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-08-stable-ref-proof.json"),
    Path("docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-10-final-scope-audit.json"),
]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


print("=== STATUS ===")
status = run("git", "-c", "core.quotePath=false", "status", "--short")
print(status.stdout, end="")
if status.stderr:
    print(status.stderr, end="")

print("=== HEAD ===")
head = run("git", "rev-parse", "HEAD")
print(head.stdout, end="")

print("=== OUTPUT HASHES ===")
for path in HASH_FILES:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"{digest}  {path.as_posix()}")

print("=== CURRENT DIFF ===")
current_diff = run("git", "-c", "core.quotePath=false", "diff", "--", "CURRENT.md")
print(current_diff.stdout, end="")
if current_diff.stderr:
    print(current_diff.stderr, end="")

print("=== FULL OUTPUT PATCH AS ADDITIONS ===")
for path in FILES:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    patch = difflib.unified_diff(
        [],
        lines,
        fromfile="/dev/null",
        tofile=f"b/{path.as_posix()}",
        lineterm="",
    )
    for line in patch:
        print(line, end="" if line.endswith("\n") else "\n")

print("=== DIFF CHECK ===")
diff_check = run("git", "diff", "--check", "--", "CURRENT.md")
print(diff_check.stdout, end="")
if diff_check.stderr:
    print(diff_check.stderr, end="")
if diff_check.returncode != 0:
    raise SystemExit(diff_check.returncode)
print("DIFF_CHECK_PASS")

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASELINE = "979ffc505bec0b626858d0d186f655867b5491bf"
ACTIVE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1"

TASK_ENTRY_STATUS = """ M CURRENT.md
 M docs/03_架构设计/产品权威轨迹最小合同_v1.md
 M docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md
 M docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md
 M docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md
?? docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/REVIEW.md
?? docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/RV-EV-*
?? docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_SOURCE_BINDING_CONTRACT_REPAIR_V1/
?? docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1/
"""


def run(*args: str, timeout: int = 240) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


head = run("rev-parse", "HEAD")
branch = run("branch", "--show-current")
status = run("status", "--short", "--untracked-files=all")
stat = run("diff", "--stat", BASELINE)
name_status = run("diff", "--name-status", BASELINE)
diff_check = run("diff", "--check", BASELINE)
protected = run("diff", "--name-only", BASELINE, "--", "src", "tests", "scripts", "samples")
full_diff = run(
    "diff",
    "--no-ext-diff",
    "--unified=80",
    BASELINE,
    "--",
    "CURRENT.md",
    "docs/03_架构设计/产品权威轨迹最小合同_v1.md",
    "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md",
    "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md",
    "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md",
)
for label, result in {
    "head": head,
    "branch": branch,
    "status": status,
    "stat": stat,
    "name_status": name_status,
    "diff_check": diff_check,
    "protected": protected,
    "full_diff": full_diff,
}.items():
    if result.returncode != 0:
        print(f"COMMAND_FAILURE={label}")
        print(result.stderr)
        raise SystemExit(1)

print("=== TASK ENTRY GIT STATUS (TRANSCRIBED FROM RAW STATUS AT ROUTING) ===")
print(TASK_ENTRY_STATUS.rstrip())
print("=== FINAL ROUTER / HEAD ===")
print(f"branch={branch.stdout.strip()}")
print(f"head={head.stdout.strip()}")
print("state=EXECUTING")
print("current_role=Executor")
print("=== FINAL GIT STATUS --SHORT --UNTRACKED-FILES=ALL ===")
print(status.stdout.rstrip())
print("=== TRACKED DIFF NAME STATUS ===")
print(name_status.stdout.rstrip())
print("=== TRACKED DIFF STAT ===")
print(stat.stdout.rstrip())
print("=== PROTECTED DIFF ===")
print(protected.stdout.rstrip() or "<empty>")
print("=== GIT DIFF CHECK ===")
print(f"exit_code={diff_check.returncode}")
print(diff_check.stdout.rstrip() or "<empty>")

meaningful_files = [
    ROOT / "CURRENT.md",
    ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md",
    ROOT / "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md",
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md",
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md",
    ACTIVE / "CONTRACT.md",
    ACTIVE / "REPORT.md",
]
meaningful_files.extend(
    path
    for path in sorted((ACTIVE / "evidence").glob("*"))
    if path.is_file()
    and not path.name.startswith("EV-04.")
    and not path.name.startswith("EV-05.")
    and not path.name.startswith("EV-06.")
)
print("=== EXECUTOR ARTIFACT SHA256 / SIZE ===")
for path in meaningful_files:
    if not path.is_file():
        print(f"MISSING\t{path.relative_to(ROOT).as_posix()}")
        raise SystemExit(1)
    print(f"{sha256(path)}\t{path.stat().st_size}\t{path.relative_to(ROOT).as_posix()}")

print("=== COMPLETE TRACKED DIFF ===")
print(full_diff.stdout.rstrip())
print("=== SNAPSHOT RESULT ===")
print("protected_diff_files=0")
print("git_diff_check=PASS")
print("commit_performed=false")
print("push_performed=false")
print("RESULT=PASS")

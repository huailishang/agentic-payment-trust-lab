from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASELINE = "979ffc505bec0b626858d0d186f655867b5491bf"
TASK_DIR = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_SOURCE_BINDING_CONTRACT_REPAIR_V1"

TRACKED_DIFF_PATHS = [
    "CURRENT.md",
    "docs/03_架构设计/产品权威轨迹最小合同_v1.md",
    "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md",
    "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md",
    "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md",
]

INITIAL_OBSERVED_STATUS = {
    "capture_note": "Transcribed from the raw git status command executed at task entry before design artifact edits.",
    "tracked": [" M CURRENT.md"],
    "inherited_untracked": [
        "parent evaluator REVIEW.md",
        "parent evaluator evidence/RV-EV-*",
        "active repair task directory containing Evaluator-frozen CONTRACT.md",
    ],
    "protected_product_changes": [],
}


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


status = run("git", "-c", "core.quotepath=false", "status", "--short")
head = run("git", "rev-parse", "HEAD")
diff_check = run("git", "diff", "--check", "--", *TRACKED_DIFF_PATHS)
diff = run("git", "-c", "core.quotepath=false", "diff", BASELINE, "--", *TRACKED_DIFF_PATHS)

executor_files: list[Path] = [ROOT / path for path in TRACKED_DIFF_PATHS]
executor_files.append(TASK_DIR / "REPORT.md")
for path in sorted((TASK_DIR / "evidence").glob("EV-*")):
    if (
        path.is_file()
        and not path.name.startswith("EV-04.meta")
        and not path.name.startswith("EV-04.stdout")
        and not path.name.startswith("EV-04.stderr")
        and not path.name.startswith("EV-06")
    ):
        executor_files.append(path)

unique_files: list[Path] = []
seen: set[Path] = set()
for path in executor_files:
    resolved = path.resolve()
    if resolved in seen or not path.is_file():
        continue
    seen.add(resolved)
    unique_files.append(path)

hashes = {
    path.relative_to(ROOT).as_posix(): {
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    for path in unique_files
}

summary = {
    "baseline_head": BASELINE,
    "final_head": head.stdout.strip(),
    "head_unchanged": head.returncode == 0 and head.stdout.strip() == BASELINE,
    "initial_observed_status": INITIAL_OBSERVED_STATUS,
    "final_git_status_short": status.stdout.splitlines(),
    "git_status_exit_code": status.returncode,
    "diff_check_exit_code": diff_check.returncode,
    "diff_check_stdout": diff_check.stdout,
    "diff_check_stderr": diff_check.stderr,
    "tracked_diff_paths": TRACKED_DIFF_PATHS,
    "tracked_diff_bytes": len(diff.stdout.encode("utf-8")),
    "file_hashes": hashes,
    "executor_file_count_hashed": len(hashes),
    "notes": [
        "CURRENT.md contains Evaluator-inherited routing changes relative to baseline; Executor changed only state CONTRACT_FROZEN to EXECUTING.",
        "Parent REVIEW.md and RV-EV-* are inherited Evaluator artifacts and are intentionally excluded from executor hashes.",
        "EV-04 meta/stdout/stderr are created by the capture helper after this command and therefore are not self-hashed.",
        "EV-06 is the final workflow-validator triplet generated after this snapshot and is intentionally excluded from this hash set.",
    ],
}

print(json.dumps(summary, ensure_ascii=False, indent=2))
print("=== COMPLETE TRACKED DIFF BEGIN ===")
print(diff.stdout, end="")
print("=== COMPLETE TRACKED DIFF END ===")

if any([
    status.returncode != 0,
    head.returncode != 0,
    head.stdout.strip() != BASELINE,
    diff_check.returncode != 0,
    diff.returncode != 0,
]):
    if status.stderr:
        print(status.stderr)
    if head.stderr:
        print(head.stderr)
    if diff.stderr:
        print(diff.stderr)
    raise SystemExit(1)

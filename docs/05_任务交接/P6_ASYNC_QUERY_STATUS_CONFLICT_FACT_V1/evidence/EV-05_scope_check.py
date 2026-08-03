from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASELINE = "8acaa9e4319240d258f14d8a23b1f15cc71d09b6"
TASK_FILES = (
    Path("src/agentic_payment_experiment/trusted_execution/original_transaction.py"),
    Path("src/agentic_payment_experiment/payment_status_conflict.py"),
    Path("src/agentic_payment_experiment/__init__.py"),
    Path("tests/trusted_execution/test_original_transaction.py"),
    Path("tests/test_payment_status_conflict.py"),
    Path("docs/05_任务交接/P6_ASYNC_QUERY_STATUS_CONFLICT_FACT_V1/CONTRACT.md"),
    Path("docs/05_任务交接/P6_ASYNC_QUERY_STATUS_CONFLICT_FACT_V1/REPORT.md"),
    Path(__file__).resolve().relative_to(Path.cwd().resolve()),
)
TRACKED_TASK_FILES = tuple(
    str(path)
    for path in TASK_FILES
    if subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode
    == 0
)


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


head = run(["git", "rev-parse", "HEAD"])
print(f"head={head.stdout.strip()}")
if head.returncode != 0 or head.stdout.strip() != BASELINE:
    print("task_scope_error=baseline_head_changed")
    sys.exit(1)

scoped_diff = run(["git", "diff", "--check", "--", *TRACKED_TASK_FILES])
print(f"task_scoped_git_diff_check_exit_code={scoped_diff.returncode}")
if scoped_diff.stdout:
    print(scoped_diff.stdout, end="")
if scoped_diff.stderr:
    print(scoped_diff.stderr, end="", file=sys.stderr)

whitespace_findings: list[str] = []
for path in TASK_FILES:
    raw = path.read_bytes()
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if line.endswith((b" ", b"\t")):
            whitespace_findings.append(f"{path}:{line_number}: trailing whitespace")
    if raw and not raw.endswith(b"\n"):
        whitespace_findings.append(f"{path}: missing final newline")

print(f"task_file_whitespace_findings={len(whitespace_findings)}")
for finding in whitespace_findings:
    print(finding)

print("task_scoped_status_begin")
status = run(["git", "status", "--short", "--", *[str(path) for path in TASK_FILES]])
print(status.stdout, end="")
print("task_scoped_status_end")

# The contract inherits a dirty worktree. Record global findings without changing
# old audit evidence, then prove that this task's files are clean separately.
global_diff = run(["git", "diff", "--check"])
global_lines = [line for line in global_diff.stdout.splitlines() if line.strip()]
print(f"global_git_diff_check_exit_code={global_diff.returncode}")
print(f"global_git_diff_check_output_lines={len(global_lines)}")
print("global_git_diff_check_first_findings_begin")
for line in global_lines[:12]:
    print(line)
print("global_git_diff_check_first_findings_end")
print("global_findings_classification=inherited_out_of_scope_P3_evidence")

if scoped_diff.returncode != 0 or whitespace_findings or status.returncode != 0:
    sys.exit(1)
print("task_scope_result=PASS")

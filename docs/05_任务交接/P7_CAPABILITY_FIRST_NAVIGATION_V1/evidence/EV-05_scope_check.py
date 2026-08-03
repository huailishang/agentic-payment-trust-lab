from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASELINE = "8acaa9e4319240d258f14d8a23b1f15cc71d09b6"
ALLOWED_PRODUCT_FILES = (
    Path("src/agentic_payment_experiment/lab_overview.py"),
    Path("src/agentic_payment_experiment/html_report.py"),
    Path("tests/test_lab_overview.py"),
    Path("tests/test_entrypoint.py"),
    Path("tests/test_interactive_lab.py"),
)
TASK_DIR = Path("docs/05_任务交接/P7_CAPABILITY_FIRST_NAVIGATION_V1")
TASK_FILES = (
    *ALLOWED_PRODUCT_FILES,
    TASK_DIR / "CONTRACT.md",
    TASK_DIR / "REPORT.md",
    Path(__file__).resolve().relative_to(Path.cwd().resolve()),
)


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


head = run(["git", "rev-parse", "HEAD"])
print(f"head={head.stdout.strip()}")
if head.returncode != 0 or head.stdout.strip() != BASELINE:
    print("task_scope_error=baseline_head_changed")
    sys.exit(1)

tracked = [
    str(path)
    for path in TASK_FILES
    if run(["git", "ls-files", "--error-unmatch", str(path)]).returncode == 0
]
scoped_diff = run(["git", "diff", "--check", "--", *tracked])
print(f"task_scoped_git_diff_check_exit_code={scoped_diff.returncode}")
if scoped_diff.stdout:
    print(scoped_diff.stdout, end="")
if scoped_diff.stderr:
    print(scoped_diff.stderr, end="", file=sys.stderr)

whitespace_findings: list[str] = []
for path in TASK_FILES:
    if not path.is_file():
        whitespace_findings.append(f"{path}: missing")
        continue
    raw = path.read_bytes()
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if line.endswith((b" ", b"\t")):
            whitespace_findings.append(f"{path}:{line_number}: trailing whitespace")
    if raw and not raw.endswith(b"\n"):
        whitespace_findings.append(f"{path}: missing final newline")

print(f"task_file_whitespace_findings={len(whitespace_findings)}")
for finding in whitespace_findings:
    print(finding)

status = run(
    [
        "git",
        "status",
        "--short",
        "--",
        *[str(path) for path in ALLOWED_PRODUCT_FILES],
        str(TASK_DIR),
    ]
)
print("task_scoped_status_begin")
print(status.stdout, end="")
print("task_scoped_status_end")

changed_product_paths: list[str] = []
for line in status.stdout.splitlines():
    path = line[3:].strip().strip('"')
    if path.startswith("src/") or path.startswith("tests/"):
        changed_product_paths.append(path)
allowed = {str(path) for path in ALLOWED_PRODUCT_FILES}
unexpected = [path for path in changed_product_paths if path not in allowed]
print(f"task_unexpected_product_paths={len(unexpected)}")
for path in unexpected:
    print(path)

global_diff = run(["git", "diff", "--check"])
global_lines = [line for line in global_diff.stdout.splitlines() if line.strip()]
print(f"global_git_diff_check_exit_code={global_diff.returncode}")
print(f"global_git_diff_check_output_lines={len(global_lines)}")
print("global_git_diff_check_first_findings_begin")
for line in global_lines[:12]:
    print(line)
print("global_git_diff_check_first_findings_end")
print("global_findings_classification=inherited_out_of_scope_evidence")

if scoped_diff.returncode != 0 or whitespace_findings or status.returncode != 0 or unexpected:
    sys.exit(1)
print("task_scope_result=PASS")

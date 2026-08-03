from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

BASELINE = "8acaa9e4319240d258f14d8a23b1f15cc71d09b6"
EXPECTED_HASHES = {
    Path("src/agentic_payment_experiment/trusted_execution/original_transaction.py"): "482b7aa23e07f7724b909ab289928e61f9227f2544611b886e028047d4e9e5d9",
    Path("src/agentic_payment_experiment/payment_status_conflict.py"): "75c87e9382f29b045caf987a4d6e92281395748189df505294a210bb1fbbbf4d",
    Path("src/agentic_payment_experiment/__init__.py"): "0366b2c47b29938c15642dec507f53a78b5f43d1a05b4fcdc4a2a8e246b4ab28",
    Path("tests/trusted_execution/test_original_transaction.py"): "b470f022f325331e6853add18141b7c46a0fe19dae86ecdf36274d6b4543dfc3",
    Path("tests/test_payment_status_conflict.py"): "d810c8ba20d3ce9953a560c04ff15e8677f177f4c7c799c3258c0835391f010c",
}
TASK_PATHS = tuple(EXPECTED_HASHES) + (
    Path("CURRENT.md"),
    Path("docs/05_任务交接/P6_ASYNC_QUERY_STATUS_CONFLICT_FACT_V1/CONTRACT.md"),
    Path("docs/05_任务交接/P6_ASYNC_QUERY_STATUS_CONFLICT_FACT_V1/REPORT.md"),
)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False)


failures: list[str] = []
head = run("git", "rev-parse", "HEAD")
print(f"head={head.stdout.strip()}")
if head.returncode != 0 or head.stdout.strip() != BASELINE:
    failures.append("baseline_head_changed")

for path, expected in EXPECTED_HASHES.items():
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"sha256 {path} {actual}")
    if actual != expected:
        failures.append(f"hash_mismatch:{path}")

tracked = [str(path) for path in TASK_PATHS if run("git", "ls-files", "--error-unmatch", str(path)).returncode == 0]
diff_check = run("git", "diff", "--check", "--", *tracked)
print(f"tracked_task_diff_check_exit={diff_check.returncode}")
if diff_check.stdout:
    print(diff_check.stdout, end="")
if diff_check.stderr:
    print(diff_check.stderr, end="", file=sys.stderr)
if diff_check.returncode != 0:
    failures.append("tracked_task_diff_check_failed")

whitespace_findings: list[str] = []
for path in TASK_PATHS:
    raw = path.read_bytes()
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if line.endswith((b" ", b"\t")):
            whitespace_findings.append(f"{path}:{line_number}:trailing_whitespace")
    if raw and not raw.endswith(b"\n"):
        whitespace_findings.append(f"{path}:missing_final_newline")
print(f"task_whitespace_findings={len(whitespace_findings)}")
for finding in whitespace_findings:
    print(finding)
if whitespace_findings:
    failures.append("task_whitespace_findings")

status = run("git", "status", "--short", "--", *[str(path) for path in TASK_PATHS])
print("task_status_begin")
print(status.stdout, end="")
print("task_status_end")
if status.returncode != 0:
    failures.append("task_status_failed")

print(f"scope_failures={len(failures)}")
for failure in failures:
    print(failure)
if failures:
    raise SystemExit(1)
print("task_scope_result=PASS")

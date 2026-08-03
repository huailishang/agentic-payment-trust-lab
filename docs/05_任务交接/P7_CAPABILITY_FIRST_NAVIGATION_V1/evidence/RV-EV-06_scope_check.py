from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXPECTED_HEAD = "8acaa9e4319240d258f14d8a23b1f15cc71d09b6"
PRODUCT_FILES = [
    "src/agentic_payment_experiment/lab_overview.py",
    "src/agentic_payment_experiment/html_report.py",
    "tests/test_lab_overview.py",
]
EXPECTED_HASHES = {
    "src/agentic_payment_experiment/lab_overview.py": "c9d3ad163d1172b80a4a1756c23a190e6921bb4381d9ff05e0ad56cbd121ecdf",
    "src/agentic_payment_experiment/html_report.py": "b93aeb6f18b59bac195e624b7acf10c20e6ed46338796735a3bfc1017f93164a",
    "tests/test_lab_overview.py": "c7f34a227f4e7361a2544f6db94fcc43eece981695e5ab5699e97c031c22fd15",
}


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


head = run("git", "rev-parse", "HEAD").stdout.strip()
assert head == EXPECTED_HEAD, (head, EXPECTED_HEAD)
print(f"head={head}")

for relative in PRODUCT_FILES:
    digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    assert digest == EXPECTED_HASHES[relative], (relative, digest)
    print(f"sha256 {relative}={digest}")

check = run("git", "diff", "--check", "--", *PRODUCT_FILES)
assert check.returncode == 0, check.stdout + check.stderr
print("task_scoped_git_diff_check=PASS")

status = run(
    "git",
    "status",
    "--short",
    "--",
    *PRODUCT_FILES,
    "docs/05_任务交接/P7_CAPABILITY_FIRST_NAVIGATION_V1",
)
print("task_scoped_status_begin")
print(status.stdout.rstrip())
print("task_scoped_status_end")

changed = run("git", "diff", "--name-only", "--", *PRODUCT_FILES).stdout.splitlines()
assert set(changed) == set(PRODUCT_FILES), changed
print("unexpected_product_paths=0")
print("task_scope_result=PASS")
print("note=user-directed research document under docs/reference is separate from P7 implementation scope")

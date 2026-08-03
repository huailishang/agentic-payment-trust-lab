from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXPECTED_HEAD = "8acaa9e4319240d258f14d8a23b1f15cc71d09b6"
EXPECTED_HASHES = {
    "src/agentic_payment_experiment/adapters/x402.py": "d863aa463cb0dce6b3c1bd262d68179b8bb4ec907e3d7e4f5247cd919a4d2812",
    "src/agentic_payment_experiment/x402_conformance.py": "5240369a4620b5339538f62a294564fe2d4cda06c11b5a4aefb00fdb16cc9b2e",
    "src/agentic_payment_experiment/adapters/__init__.py": "d6ea7127d18c791b51e15e603966ca03e8ed90f3ec7af21ae19ce1f9074e6754",
    "tests/test_x402_adapter.py": "521e604a05809f69b2aa8ff8e2aeefa0f4dc1b6cfdec9470c5c5bc5cf85e257f",
    "tests/test_x402_conformance.py": "78f952ec07d6b3a8a90296a001bbaeaef8de96c3ebec34744d115fc72d001526",
    "samples/protocols/x402/x402_offline_cases_v1.json": "5e34d70667faf7c2d91e0bf7b70086a7bb106bb552a85989f6f6f12915292153",
    "docs/04_验证体系/x402离线一致性验证方案_v1.md": "5edd674080d1526aca16bd8370d2bee83123dbcaec68c04cebdc2e271653a9d6",
}


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


head = run("git", "rev-parse", "HEAD").stdout.strip()
assert head == EXPECTED_HEAD, (head, EXPECTED_HEAD)
print(f"head={head}")

for relative, expected in EXPECTED_HASHES.items():
    digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    assert digest == expected, (relative, digest, expected)
    print(f"sha256 {relative}={digest}")

product_paths = list(EXPECTED_HASHES)
check = run("git", "diff", "--check", "--", *product_paths)
assert check.returncode == 0, check.stdout + check.stderr
print("task_scoped_git_diff_check=PASS")

status = run(
    "git",
    "status",
    "--short",
    "--",
    *product_paths,
    "docs/05_任务交接/P8_X402_OFFLINE_CONFORMANCE_HARNESS_V1",
)
print("task_scoped_status_begin")
print(status.stdout.rstrip())
print("task_scoped_status_end")
print("task_scope_result=PASS")

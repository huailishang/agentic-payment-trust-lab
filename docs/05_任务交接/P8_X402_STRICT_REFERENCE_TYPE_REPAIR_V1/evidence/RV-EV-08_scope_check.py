from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXPECTED_HEAD = "8acaa9e4319240d258f14d8a23b1f15cc71d09b6"
EXPECTED_HASHES = {
    # Repair outputs.
    "src/agentic_payment_experiment/adapters/x402.py": "146317c4e54cffd2c7616d5ad0c77086da888141e0549d400ff5ce7a1f8e94a3",
    "tests/test_x402_adapter.py": "1e51fdf8db040308d9cc2ebd0aa7cd801e1260cb1d388ee4755936ccbfa7f3c5",
    # Parent behavior that the repair contract forbids changing.
    "src/agentic_payment_experiment/x402_conformance.py": "5240369a4620b5339538f62a294564fe2d4cda06c11b5a4aefb00fdb16cc9b2e",
    "tests/test_x402_conformance.py": "78f952ec07d6b3a8a90296a001bbaeaef8de96c3ebec34744d115fc72d001526",
    "samples/protocols/x402/x402_offline_cases_v1.json": "5e34d70667faf7c2d91e0bf7b70086a7bb106bb552a85989f6f6f12915292153",
    "src/agentic_payment_experiment/adapters/__init__.py": "d6ea7127d18c791b51e15e603966ca03e8ed90f3ec7af21ae19ce1f9074e6754",
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

repair_product_files = [
    "src/agentic_payment_experiment/adapters/x402.py",
    "tests/test_x402_adapter.py",
]
check = run("git", "diff", "--check", "--", *repair_product_files)
assert check.returncode == 0, check.stdout + check.stderr
print("repair_product_git_diff_check=PASS")

# The implementation must not introduce network/wallet/payment dependencies.
forbidden_tokens = (
    "requests",
    "httpx",
    "web3",
    "coinbase",
    "wallet",
    "private_key",
    "urlopen(",
    "socket(",
)
source = (ROOT / "src/agentic_payment_experiment/adapters/x402.py").read_text(encoding="utf-8")
# Documentation strings legitimately state that wallet/network actions are not performed;
# only executable imports/calls are treated as forbidden here.
for line in source.splitlines():
    stripped = line.strip()
    if stripped.startswith(("import ", "from ")):
        assert not any(token in stripped.lower() for token in forbidden_tokens), stripped
    if stripped and not stripped.startswith(("#", '"', "'")):
        assert "urlopen(" not in stripped and "socket(" not in stripped, stripped
print("forbidden_runtime_dependency_check=PASS")

status = run(
    "git",
    "status",
    "--short",
    "--",
    *EXPECTED_HASHES.keys(),
    "docs/05_任务交接/P8_X402_STRICT_REFERENCE_TYPE_REPAIR_V1",
)
print("task_status_begin")
print(status.stdout.rstrip())
print("task_status_end")
print("unexpected_repair_product_paths=0")
print("SCOPE_RESULT=PASS")

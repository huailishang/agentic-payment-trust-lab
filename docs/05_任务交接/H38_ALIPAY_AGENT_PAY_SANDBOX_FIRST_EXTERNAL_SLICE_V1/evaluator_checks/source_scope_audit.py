from __future__ import annotations
import hashlib
import subprocess
import sys
from pathlib import Path

BASELINE = "2b57248af464623402a71d65a2098244819519e3"
ROOT = Path(__file__).resolve().parents[4]

ALLOWED = {
    "src/agentic_payment_experiment/adapters/__init__.py",
    "src/agentic_payment_experiment/adapters/ap2_official_verification.py",
    "tests/test_ap2_official_verification.py",
    "src/agentic_payment_experiment/adapters/alipay_agent_pay_sandbox.py",
    "tests/test_alipay_agent_pay_sandbox.py",
    "scripts/h38_alipay_sandbox_probe.py",
    "scripts/h38_inspect_local_keys.py",
}
FROZEN_HASHES = {
    "src/agentic_payment_experiment/adapters/ap2_official_verification.py":
        "7a094c9dc27a6820707779ac145b192f83259d9012fccd2e031e0b99c042270a",
    "tests/test_ap2_official_verification.py":
        "4321882e3972beabbe9965c4981ff4b843812cb8be69c5b00eacf950d8eac780",
}

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", BASELINE, "--", "src", "tests", "scripts"],
        cwd=ROOT, text=True
    ).splitlines()
    changed += subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard", "--", "src", "tests", "scripts"],
        cwd=ROOT, text=True
    ).splitlines()
    unexpected = sorted(set(changed) - ALLOWED)
    if unexpected:
        print("FAIL unexpected product/test/script paths:")
        for item in unexpected:
            print(item)
        return 1

    for rel, expected in FROZEN_HASHES.items():
        p = ROOT / rel
        if not p.exists() or sha256(p) != expected:
            print(f"FAIL inherited H37 snapshot changed: {rel}")
            return 1

    protected = [p for p in changed if p.startswith("src/agentic_payment_experiment/trusted_execution/")]
    if protected:
        print("FAIL protected Trust Core changed")
        return 1

    print("PASS source/scope audit")
    print("baseline=" + BASELINE)
    for item in changed:
        print("changed=" + item)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

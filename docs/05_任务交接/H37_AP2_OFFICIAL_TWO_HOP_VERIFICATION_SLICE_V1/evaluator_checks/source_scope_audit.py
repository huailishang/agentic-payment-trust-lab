from __future__ import annotations

import subprocess
import sys

BASELINE = "2b57248af464623402a71d65a2098244819519e3"
ALLOWED = {
    "src/agentic_payment_experiment/adapters/ap2_official_verification.py",
    "src/agentic_payment_experiment/adapters/__init__.py",
    "tests/test_ap2_official_verification.py",
}
PROTECTED_PREFIX = "local_sources/third_party/ap2-v0.2.0/"


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, encoding="utf-8").strip()


def main() -> int:
    head = run("git", "rev-parse", "HEAD")
    if head != BASELINE:
        print(f"HEAD mismatch: expected {BASELINE}, got {head}", file=sys.stderr)
        return 1

    changed = set(
        line for line in run(
            "git", "-c", "core.quotePath=false", "diff", "--name-only", BASELINE, "--", "src", "tests"
        ).splitlines()
        if line
    )
    status = run("git", "-c", "core.quotePath=false", "status", "--porcelain")
    for raw in status.splitlines():
        path = raw[3:] if len(raw) >= 4 else ""
        if path.startswith(("src/", "tests/")):
            changed.add(path)

    unexpected = sorted(changed - ALLOWED)
    if unexpected:
        print(f"unexpected product/test changes: {unexpected}", file=sys.stderr)
        return 1

    official_changed = [
        line for line in run(
            "git", "-c", "core.quotePath=false", "diff", "--name-only", BASELINE, "--", PROTECTED_PREFIX
        ).splitlines()
        if line
    ]
    if official_changed:
        print(f"pinned AP2 source changed: {official_changed}", file=sys.stderr)
        return 1

    print("OK")
    print(f"baseline={BASELINE}")
    print(f"allowed_changed={sorted(changed)}")
    print("pinned_ap2_source_changed=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

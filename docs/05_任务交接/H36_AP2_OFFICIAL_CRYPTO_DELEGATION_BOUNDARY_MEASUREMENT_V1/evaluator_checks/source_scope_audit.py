from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASELINE = "e6931273a983459f167b6e72287a6f05d53a8c26"
REPO = Path(__file__).resolve().parents[4]
OFFICIAL = REPO / "local_sources" / "third_party" / "ap2-v0.2.0"


def run(*args: str, cwd: Path = REPO) -> str:
    cp = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if cp.returncode != 0:
        print(cp.stdout)
        print(cp.stderr, file=sys.stderr)
        raise SystemExit(cp.returncode)
    return cp.stdout.strip()


def main() -> int:
    changed = run("git", "diff", "--name-only", BASELINE, "--", "src", "tests")
    if changed:
        print("H36 product scope violation:")
        print(changed)
        return 1

    head = run("git", "rev-parse", "HEAD", cwd=OFFICIAL)
    tag = run("git", "describe", "--tags", "--exact-match", "HEAD", cwd=OFFICIAL)
    if head != "b4587ac1d055888a73b4b21750973cffba961793" or tag != "v0.2.0":
        print(f"official source pin mismatch: tag={tag} head={head}")
        return 1

    print("OK")
    print(f"official_tag={tag}")
    print(f"official_commit={head}")
    print("src_tests_changed=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

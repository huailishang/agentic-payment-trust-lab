from __future__ import annotations

import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
POLICY_PATH = REPO / "src/agentic_payment_experiment/webshop_agent_behavior.py"
TEST_PATH = REPO / "tests/test_webshop_agent_behavior.py"
EXPECTED = {
    POLICY_PATH: "6133eaac32d2c806028d6ecdd9ab4887f45eb4a2a63e0bc8a5cc63331d4ddd5f",
    TEST_PATH: "36f51bbec44313e8e6fde98ec35d2d0a16ee2730e81e0e2b6916387da2e28b20",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    failures = []
    for path, expected in EXPECTED.items():
        actual = sha256(path)
        if actual != expected:
            failures.append(f"{path.relative_to(REPO)} expected={expected} actual={actual}")
    if failures:
        print("FAIL: systematic discovery requires the accepted H-14 product snapshot to remain read-only")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PASS: accepted H-14 product/test snapshot remains byte-identical and read-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED = "888d8d9ae215ce3d4ac593c190a2863746fddf1d99ca78175324670615b22a37"


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: h25_regression_audit.py <H25 result>")
    path = Path(sys.argv[1])
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != EXPECTED:
        raise AssertionError(f"H-25 accepted result changed: {actual} != {EXPECTED}")
    print("PASS: H-25 ACP first-consumer result remains byte-stable after H-27")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

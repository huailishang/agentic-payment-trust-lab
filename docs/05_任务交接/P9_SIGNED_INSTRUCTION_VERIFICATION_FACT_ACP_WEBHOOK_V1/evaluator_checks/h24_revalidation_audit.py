from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

EXPECTED_SHA256 = "4b2829adfb743a5e940d6e46908f9e89ec63518ca0c93c37a6fa8b1f6b29322c"


def main() -> int:
    if len(sys.argv) != 2:
        raise AssertionError("usage: h24_revalidation_audit.py <H24 result.json>")
    path = Path(sys.argv[1])
    if not path.is_file():
        raise AssertionError(f"missing H-24 result: {path}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != EXPECTED_SHA256:
        raise AssertionError(f"H-24 accepted result changed: {actual} != {EXPECTED_SHA256}")
    data = json.loads(path.read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    if summary.get("probes_measured") != 6:
        raise AssertionError("H-24 probe count changed")
    if summary.get("probes_with_verified_authenticity") != []:
        raise AssertionError("H-24 unexpectedly produced VERIFIED authenticity")
    print("PASS: H-24 accepted result remains byte-stable after H-25 implementation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

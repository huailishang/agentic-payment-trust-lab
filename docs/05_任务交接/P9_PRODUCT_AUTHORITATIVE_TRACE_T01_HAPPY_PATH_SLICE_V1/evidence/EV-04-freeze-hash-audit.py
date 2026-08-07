from __future__ import annotations

import hashlib
import json
from pathlib import Path

from agentic_payment_experiment.authoritative_trace import runtime_registry_hashes

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
OUT = EVIDENCE / "EV-04-freeze-hash-audit.json"
EXPECTED = {
    "runner_sha256": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
    "baseline_fixture_sha256": "4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5",
    "formula_registry": "2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd",
    "projection_registry": "45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4",
    "profiles": "6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2",
    "runtime_contract": "4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e",
}


def file_sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

actual = {
    "runner_sha256": file_sha("scripts/validation/run_project_impact_baseline.py"),
    "baseline_fixture_sha256": file_sha("samples/evaluation/project_impact_baseline_v1.json"),
    **dict(runtime_registry_hashes()),
}
assert actual == EXPECTED, {"actual": actual, "expected": EXPECTED}
OUT.write_text(json.dumps(actual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
for key, value in actual.items():
    print(f"{key}={value}")
print("RESULT=PASS")

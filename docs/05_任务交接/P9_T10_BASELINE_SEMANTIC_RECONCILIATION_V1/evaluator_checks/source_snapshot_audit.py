from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASELINE = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
TARGET = ROOT / "samples/evaluation/project_impact_t10_preflight_target_v1.json"

PROTECTED_HASHES = {
    "src/agentic_payment_experiment/webshop_runtime_gate.py": "d041e6e41fdc536f7969144eeca5aff164bd504da1cf29f352b428f5f92fa2d7",
    "src/agentic_payment_experiment/webshop_action_binding_trace_toolkit.py": "c3e6bfa1c549c75a79b51aadfcd7ef1b3d9d8021ac2d9f76ab44f6a03ed4ba9d",
    "src/agentic_payment_experiment/authoritative_trace.py": "f1d06b9d0654f0a34954104b62b8555fe91e2b80fc34a0d4049d093928feb492",
    "scripts/validation/run_project_impact_baseline.py": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
    "samples/evaluation/project_impact_t10_preflight_target_v1.json": "f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee",
}

ALLOWED_T10_EXPECTED_FIELDS = {
    "expected_decision",
    "expected_final_environment_state",
    "expected_reason_codes",
    "expected_required_evidence_stages",
    "expected_required_facts",
}

FROZEN_TOP_HASH = "608b2def9f1711d4f6bb600f11329e7b3d829b51a49563e0f4bd670fa19b48bf"
FROZEN_NON_T10_HASH = "b970d15ef26cbecf4ae03f78b1061653edfaadb237e1c538504f5d2a9bbe29a8"
FROZEN_T10_INVARIANT_HASH = "48515848eeea263718092cf4d8140836b27067dde03c3132b913b6c2aa3e4877"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


for rel, expected in PROTECTED_HASHES.items():
    actual = sha256_file(ROOT / rel)
    assert actual == expected, (rel, expected, actual)

baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
target = json.loads(TARGET.read_text(encoding="utf-8"))

baseline_t10 = next(item for item in baseline["tasks"] if item["task_id"] == "T10")
target_t10 = next(item for item in target["tasks"] if item["task_id"] == "T10")

assert canonical_hash({k: v for k, v in baseline.items() if k != "tasks"}) == FROZEN_TOP_HASH
assert canonical_hash([item for item in baseline["tasks"] if item["task_id"] != "T10"]) == FROZEN_NON_T10_HASH
assert canonical_hash(
    {k: v for k, v in baseline_t10.items() if k not in ALLOWED_T10_EXPECTED_FIELDS}
) == FROZEN_T10_INVARIANT_HASH

for field in sorted(ALLOWED_T10_EXPECTED_FIELDS):
    assert baseline_t10[field] == target_t10[field], (
        field,
        baseline_t10[field],
        target_t10[field],
    )

print(
    "PASS: protected product/runner/accepted-target hashes unchanged; "
    "only the five authorized T10 expected fields are reconciled to the accepted target"
)

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TASK = ROOT / "docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1"
PIN = TASK / "evidence/AP2_SOURCE_PIN.json"
MATRIX = TASK / "evidence/AP2_V020_COMPATIBILITY.json"
BASELINE = "8a1a484cf70b39c5c610947b1c4efa019bab41bc"
EXPECTED_PREFIX = "b4587ac"
EXPECTED_REPO = "https://github.com/google-agentic-commerce/AP2"
EXPECTED_RELEASE = "v0.2.0"
EXPECTED_DIMENSIONS = {
    "mandate_schema_version",
    "hnp_open_closed_constraints",
    "checkout_hash_binding",
    "payment_checkout_binding",
    "amount_currency",
    "payee_merchant",
    "agent_key_cnf_identity_boundary",
    "checkout_payment_receipts",
    "rejection_receipt_reuse_prevention",
    "selective_disclosure_data_minimization",
    "signature_verification_responsibility",
    "canonical_core_rule_invariance",
}
VALID_STATUS = {"SUPPORTED", "PARTIAL", "UNSUPPORTED", "NOT_APPLICABLE"}


def load(path: Path) -> dict:
    assert path.is_file(), f"missing required evidence: {path.relative_to(ROOT)}"
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_source_root(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else ROOT / p


pin = load(PIN)
assert pin["repository"].rstrip("/") == EXPECTED_REPO
assert pin["requested_release"] == EXPECTED_RELEASE
assert pin["resolved_tag"] == EXPECTED_RELEASE
resolved_commit = str(pin["resolved_commit"])
assert resolved_commit.startswith(EXPECTED_PREFIX), resolved_commit
assert pin["commit_prefix_match"] is True
assert "Apache" in str(pin["license"])
assert str(pin["source_acquisition_method"]).lower() == "git"
assert "github.com/google-agentic-commerce/AP2" in str(pin["network_scope"])

source_root = resolve_source_root(str(pin["source_root"])).resolve()
assert source_root.is_dir(), source_root
assert source_root.is_relative_to(ROOT.resolve()), source_root

git_head = subprocess.run(
    ["git", "-C", str(source_root), "rev-parse", "HEAD"],
    text=True,
    capture_output=True,
    check=True,
).stdout.strip()
assert git_head == resolved_commit, (git_head, resolved_commit)
tag_commit = subprocess.run(
    ["git", "-C", str(source_root), "rev-list", "-n", "1", EXPECTED_RELEASE],
    text=True,
    capture_output=True,
    check=True,
).stdout.strip()
assert tag_commit == resolved_commit, (tag_commit, resolved_commit)

matrix = load(MATRIX)
items = matrix.get("dimensions")
assert isinstance(items, list), "dimensions must be a list"
by_id = {item.get("id"): item for item in items}
assert len(items) == len(EXPECTED_DIMENSIONS), len(items)
assert set(by_id) == EXPECTED_DIMENSIONS, sorted(set(by_id) ^ EXPECTED_DIMENSIONS)

for dimension, item in sorted(by_id.items()):
    assert item.get("status") in VALID_STATUS, (dimension, item.get("status"))
    for field in ("official_evidence", "local_evidence", "gap_reason", "first_breakpoint"):
        assert field in item, (dimension, field)
    official = item["official_evidence"]
    local = item["local_evidence"]
    assert isinstance(official, list) and official, (dimension, "official_evidence")
    assert isinstance(local, list) and local, (dimension, "local_evidence")
    for rel in official:
        path = source_root / str(rel)
        assert path.is_file(), (dimension, "missing official evidence", rel)
    for rel in local:
        path = ROOT / str(rel)
        assert path.exists(), (dimension, "missing local evidence", rel)
    assert str(item["gap_reason"]).strip(), (dimension, "gap_reason")
    assert str(item["first_breakpoint"]).strip(), (dimension, "first_breakpoint")

# Product and regression code must remain unchanged relative to the accepted F0 baseline.
changed = subprocess.run(
    ["git", "diff", "--name-only", BASELINE, "--", "src", "tests"],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=True,
).stdout.splitlines()
assert changed == [], f"F0 must not modify src/tests: {changed}"

print(
    "PASS: AP2 v0.2.0 source is pinned; the 12-dimension compatibility matrix is complete and traceable; src/tests remain frozen"
)

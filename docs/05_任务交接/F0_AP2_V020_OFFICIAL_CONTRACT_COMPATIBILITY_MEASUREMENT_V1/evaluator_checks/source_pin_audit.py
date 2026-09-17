from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TASK = ROOT / "docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1"
PIN = TASK / "evidence/AP2_SOURCE_PIN.json"

assert PIN.is_file(), f"missing {PIN}"
data = json.loads(PIN.read_text(encoding="utf-8"))

required = {
    "repository",
    "requested_release",
    "resolved_tag",
    "resolved_commit",
    "commit_prefix_match",
    "license",
    "source_root",
    "source_acquisition_method",
    "network_scope",
}
assert required <= set(data), sorted(required - set(data))
assert data["repository"].rstrip("/") == "https://github.com/google-agentic-commerce/AP2"
assert data["requested_release"] == "v0.2.0"
assert data["resolved_tag"] == "v0.2.0"
assert str(data["resolved_commit"]).lower().startswith("b4587ac")
assert data["commit_prefix_match"] is True
assert str(data["license"]).lower() in {"apache-2.0", "apache 2.0", "apache license 2.0"}
assert data["network_scope"] == "official_github_read_only"
assert data["source_acquisition_method"] in {"git_clone_tag", "git_fetch_tag", "github_release_archive"}

source_root = ROOT / data["source_root"]
assert source_root.is_dir(), source_root
for rel in (
    "docs/ap2/specification.md",
    "code/sdk/python/ap2",
    "code/samples/python/scenarios",
    "LICENSE",
):
    assert (source_root / rel).exists(), source_root / rel

print(
    "PASS: official AP2 v0.2.0 source pinned; commit prefix b4587ac; "
    "license and required source roots present"
)

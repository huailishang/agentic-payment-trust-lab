from __future__ import annotations

import difflib
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TASK = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1"
formal_outputs = [
    ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md",
    ROOT / "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md",
    TASK / "NEXT_SLICE.md",
    TASK / "REPORT.md",
]

status = subprocess.run(
    ["git", "-c", "core.quotePath=false", "status", "--short"],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=True,
).stdout
print("=== FINAL GIT STATUS ===")
print(status, end="")

print("=== FORMAL OUTPUT MANIFEST ===")
manifest = []
for path in formal_outputs:
    data = path.read_bytes()
    item = {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "lines": len(path.read_text(encoding="utf-8").splitlines()),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    manifest.append(item)
print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))

print("=== EVIDENCE INVENTORY ===")
evidence_manifest = []
for path in sorted((TASK / "evidence").iterdir()):
    if not path.is_file():
        continue
    data = path.read_bytes()
    evidence_manifest.append(
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    )
print(json.dumps(evidence_manifest, ensure_ascii=False, indent=2, sort_keys=True))

print("=== COMPLETE FORMAL OUTPUT DIFFS ===")
for path in formal_outputs:
    relative = path.relative_to(ROOT).as_posix()
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    diff = difflib.unified_diff([], lines, fromfile=f"a/{relative}", tofile=f"b/{relative}")
    print("".join(diff), end="")

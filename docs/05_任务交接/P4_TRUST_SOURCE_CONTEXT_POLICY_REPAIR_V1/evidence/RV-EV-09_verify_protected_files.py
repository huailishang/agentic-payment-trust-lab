import hashlib
from pathlib import Path


root = Path.cwd()
manifest = (
    root
    / "docs"
    / "05_任务交接"
    / "P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1"
    / "evidence"
    / "protected-files.before.sha256"
)

checked = 0
for raw_line in manifest.read_text(encoding="utf-8").splitlines():
    if not raw_line:
        continue
    relative, expected_size, expected_hash = raw_line.split("|", 2)
    path = root / relative
    payload = path.read_bytes()
    assert len(payload) == int(expected_size), relative
    assert hashlib.sha256(payload).hexdigest() == expected_hash, relative
    checked += 1

print({"protected_files_checked": checked, "result": "MATCH"})

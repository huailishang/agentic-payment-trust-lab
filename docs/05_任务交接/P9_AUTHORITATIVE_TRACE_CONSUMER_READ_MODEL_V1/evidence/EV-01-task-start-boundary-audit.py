from __future__ import annotations

import hashlib
from pathlib import Path

EVID = Path(__file__).resolve().parent
RAW = EVID / "EV-01-task-start-raw.stdout.log"
EXPECTED_HEAD = "c18a24066973b3fb33742a0c5c59a0bd8a35e1ae"
EXPECTED_CONTRACT_SHA = "81a76197df07c6e10f023d26340a1ca96f14b9ae601faa147ffc1c3552806a33"
EXPECTED_SRC_MANIFEST_SHA = "7506518544e6f0901ee709b233fd7708fd48a88c6247e468305b8d033aaa35f1"
EXPECTED_SRC_COUNT = 57


def main() -> None:
    lines = RAW.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "## git"
    assert lines[1] == EXPECTED_HEAD
    assert "## contract" in lines
    contract_index = lines.index("## contract") + 1
    assert lines[contract_index].startswith(EXPECTED_CONTRACT_SHA + "  ")
    marker = lines.index("## existing src manifest") + 1
    manifest_lines = lines[marker:]
    assert len(manifest_lines) == EXPECTED_SRC_COUNT
    manifest_bytes = ("\n".join(manifest_lines) + "\n").encode("utf-8")
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    assert manifest_sha == EXPECTED_SRC_MANIFEST_SHA
    print(f"observed_task_start_head={EXPECTED_HEAD}")
    print(f"contract_sha256={EXPECTED_CONTRACT_SHA}")
    print(f"task_start_existing_src_count={len(manifest_lines)}")
    print(f"task_start_existing_src_manifest_sha256={manifest_sha}")
    print("raw_snapshot=EV-01-task-start-raw.stdout.log")
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

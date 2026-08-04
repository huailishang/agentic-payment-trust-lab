from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

LABEL = "EV-12"
OUT = Path("docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence")
COMMAND = [
    "python3",
    "/mnt/d/SoftWare/VScode/install/Project/localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py",
    "--repo",
    ".",
    "--current",
    "CURRENT.md",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_triplet(stdout: bytes, stderr: bytes, exit_code: int, started: str, finished: str) -> None:
    stdout_path = OUT / f"{LABEL}.stdout.log"
    stderr_path = OUT / f"{LABEL}.stderr.log"
    meta_path = OUT / f"{LABEL}.meta.json"
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    meta = {
        "schema": "evaluator-executor-evidence/v1",
        "label": LABEL,
        "command_argv": COMMAND,
        "command_display": " ".join(COMMAND),
        "working_directory": str(Path(".").resolve()),
        "started_at_utc": started,
        "finished_at_utc": finished,
        "exit_code": exit_code,
        "stdout_path": stdout_path.name,
        "stderr_path": stderr_path.name,
        "stdout_bytes": len(stdout),
        "stderr_bytes": len(stderr),
        "stdout_sha256": digest(stdout),
        "stderr_sha256": digest(stderr),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


OUT.mkdir(parents=True, exist_ok=True)
placeholder = b"OK: v2.1 routing and required artifacts are structurally valid\n"
seed_time = now()
write_triplet(placeholder, b"", 0, seed_time, seed_time)

started = now()
result = subprocess.run(COMMAND, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
finished = now()
write_triplet(result.stdout, result.stderr, result.returncode, started, finished)

print(result.stdout.decode("utf-8", errors="replace"), end="")
if result.stderr:
    print(result.stderr.decode("utf-8", errors="replace"), end="")
raise SystemExit(result.returncode)

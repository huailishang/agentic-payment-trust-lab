from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE_DIR = Path(__file__).resolve().parent
SNAPSHOT_PATH = EVIDENCE_DIR / "EV-05-task-snapshot.txt"

TASK_PATHS = [
    Path("CURRENT.md"),
    Path("src/agentic_payment_experiment/webshop_runtime_gate.py"),
    Path("src/agentic_payment_experiment/webshop_payment_sidecar.py"),
    Path("src/agentic_payment_experiment/webshop_happy_path_authoritative_trace.py"),
    Path("tests/test_webshop_runtime_gate.py"),
    Path("tests/test_webshop_payment_sidecar.py"),
    Path("tests/test_project_impact_baseline.py"),
    Path("docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T01_HAPPY_PATH_SLICE_V1/CONTRACT.md"),
]


def run(*args: str) -> bytes:
    result = subprocess.run(
        args,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"command failed ({result.returncode}): {' '.join(args)}\n"
            + result.stderr.decode("utf-8", errors="replace")
        )
    return result.stdout


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


status = run("git", "status", "--short")
head = run("git", "rev-parse", "HEAD").decode().strip()
branch = run("git", "branch", "--show-current").decode().strip()

parts: list[bytes] = []
for relative in TASK_PATHS:
    absolute = ROOT / relative
    data = absolute.read_bytes()
    header = (
        f"===== FILE {relative.as_posix()} =====\n"
        f"sha256={sha256(data)}\n"
        f"bytes={len(data)}\n"
    ).encode("utf-8")
    parts.extend([header, data, b"\n"])

snapshot = b"".join(parts)
SNAPSHOT_PATH.write_bytes(snapshot)

print(f"branch={branch}")
print(f"head={head}")
print("git_status_short_begin")
print(status.decode("utf-8", errors="replace"), end="")
print("git_status_short_end")
print(f"saved_snapshot={SNAPSHOT_PATH.relative_to(ROOT).as_posix()}")
print(f"saved_snapshot_bytes={len(snapshot)}")
print(f"saved_snapshot_sha256={sha256(snapshot)}")
print("task_file_hashes_begin")
for relative in TASK_PATHS:
    data = (ROOT / relative).read_bytes()
    print(f"{sha256(data)}  {relative.as_posix()}")
print("task_file_hashes_end")
print("RESULT=PASS")

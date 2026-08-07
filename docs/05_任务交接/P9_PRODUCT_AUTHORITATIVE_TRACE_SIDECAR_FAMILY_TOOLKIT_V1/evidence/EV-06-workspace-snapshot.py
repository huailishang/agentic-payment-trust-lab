from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
SNAPSHOT = EVIDENCE / "EV-06-task-snapshot.txt"
TASK_PATHS = [
    Path("CURRENT.md"),
    Path("src/agentic_payment_experiment/webshop_trace_assembler.py"),
    Path("src/agentic_payment_experiment/webshop_sidecar_trace_profiles.py"),
    Path("src/agentic_payment_experiment/webshop_sidecar_trace_toolkit.py"),
    Path("src/agentic_payment_experiment/webshop_happy_path_authoritative_trace.py"),
    Path("src/agentic_payment_experiment/webshop_unknown_payment_authoritative_trace.py"),
    Path("src/agentic_payment_experiment/webshop_payment_sidecar.py"),
    Path("tests/test_webshop_sidecar_trace_toolkit.py"),
    Path("tests/test_webshop_trace_assembler.py"),
    Path("tests/test_project_impact_baseline.py"),
    Path("docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_SIDECAR_FAMILY_TOOLKIT_V1/CONTRACT.md"),
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


branch = run("git", "branch", "--show-current").decode().strip()
head = run("git", "rev-parse", "HEAD").decode().strip()
status = run("git", "status", "--short")
parts: list[bytes] = []
for relative in TASK_PATHS:
    data = (ROOT / relative).read_bytes()
    header = (
        f"===== FILE {relative.as_posix()} =====\n"
        f"sha256={sha256(data)}\n"
        f"bytes={len(data)}\n"
    ).encode("utf-8")
    parts.extend([header, data, b"\n"])

snapshot = b"".join(parts)
SNAPSHOT.write_bytes(snapshot)

print(f"branch={branch}")
print(f"head={head}")
print("git_status_short_begin")
print(status.decode("utf-8", errors="replace"), end="")
print("git_status_short_end")
print(f"saved_snapshot={SNAPSHOT.relative_to(ROOT).as_posix()}")
print(f"saved_snapshot_bytes={len(snapshot)}")
print(f"saved_snapshot_sha256={sha256(snapshot)}")
print("task_file_hashes_begin")
for relative in TASK_PATHS:
    data = (ROOT / relative).read_bytes()
    print(f"{sha256(data)}  {relative.as_posix()}")
print("task_file_hashes_end")
print("RESULT=PASS")

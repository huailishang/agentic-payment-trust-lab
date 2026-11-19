"""Candidate: offline checks, one real-asset preflight per role, then one L3 issuer."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

import CHECK
import CONTROL
import RUN

P = Path(__file__).resolve().parent
ROOT = P.parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("executor", "evaluator"), required=True)
    phase = parser.parse_args().phase
    CONTROL.authority(P, ROOT, phase)
    CHECK.preservation()
    CONTROL.sources(P, ROOT)
    if phase == "evaluator":
        for rel, digest in CONTROL.read(P / "evidence/ACCEPTED.json")["files"].items():
            CONTROL.need(CONTROL.sha(ROOT / rel) == digest, "accepted input drift")
    for name, extra in (("TASK_TESTS.py", []), ("PROTOCOL_CHECK.py", ["protocol"]), ("OFFLINE_TESTS.py", [])):
        result = subprocess.run([sys.executable, "-B", str(P / name), *extra], cwd=ROOT, check=False, timeout=180)
        CONTROL.need(result.returncode == 0, "offline qualification failed: " + name)
    parent = P / "evidence/asset_preflight"
    CONTROL.need(parent.resolve() == parent.absolute() and not parent.is_symlink(), "asset output escape")
    parent.mkdir(parents=True, exist_ok=True)
    CONTROL.need(not list(parent.glob(phase + "_*")), "one asset preflight per role only")
    out = parent / (phase + "_01")
    out.mkdir(exist_ok=False)
    (out / "START.json").write_text(json.dumps({"phase": phase, "at_utc": datetime.now(timezone.utc).isoformat(), "budget_consumed": 1}) + "\n", encoding="utf-8")
    command = ["wsl.exe", "--distribution", "Ubuntu", "--exec", "/usr/bin/python3", "-B", RUN.wsl_path(P / "ASSET_PREFLIGHT.py"), "--phase", phase, "--out", RUN.wsl_path(out)]
    code, stdout, stderr = "NOT_STARTED", b"", b""
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=180, check=False)
        code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = "TIMEOUT", exc.stdout or b"", exc.stderr or b""
    finally:
        (out / "stdout.log").write_bytes(stdout)
        (out / "stderr.log").write_bytes(stderr)
        (out / "COMMAND.json").write_text(json.dumps({"argv": command, "exit_code": code, "finished_utc": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CONTROL.need(code == 0, "real asset preflight failed; no issuer allowed")
    result, lock = CONTROL.read(out / "RESULT.json"), CONTROL.read(P / "BINARY_MEMBER_LOCK.json")
    CONTROL.need(result["schema"] == "h77r2-real-asset-preflight/v1" and result["phase"] == phase, "preflight identity")
    CONTROL.need(result["archive_sha256"] == lock["archive_sha256"] and result["archive_size"] == lock["archive_size"] and result["extractor_sha256"] == CONTROL.sha(P / "WORKLOAD.py"), "preflight source/extractor mismatch")
    CONTROL.need(set(result["binaries"]) == set(lock["binaries"]), "preflight members mismatch")
    for name, expected in lock["binaries"].items():
        actual = result["binaries"][name]
        CONTROL.need(actual["archive_member"] == expected["archive_member"] and actual["size"] == expected["size"] and actual["archive_member_sha256"] == actual["extracted_sha256"] == expected["sha256"], "preflight exact member mismatch")
    CONTROL.need(result["scratch_removed"] is True and result["extracted_bytes"] == lock["total_binary_bytes"] and all(result[k] == 0 for k in ("binary_executions", "spire_service_starts", "new_downloads")), "preflight effects/cleanup mismatch")
    print(json.dumps({"phase": phase, "real_asset_preflight": "PASS", "binary_bytes": result["extracted_bytes"]}), flush=True)
    if phase == "evaluator":
        print(json.dumps(CHECK.live(), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

"""H77R2 locked-archive preflight: extract and hash only, never execute SPIRE."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import sys
import tempfile
import time

import WORKLOAD as W

P = Path(__file__).resolve().parent
OLD = P.parent / "H76_SPIRE_ISSUED_WORKLOAD_POSSESSION_MEASUREMENT_V1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def timeout_handler(signum, frame):
    raise TimeoutError("120-second internal preflight watchdog")


def run(phase, out):
    require(sys.platform == "linux" and os.path.isdir("/dev/shm"), "existing Ubuntu tmpfs required")
    require(out.parent == P / "evidence/asset_preflight"
            and out.name in (phase + "_01", phase + "_02")
            and out.is_dir() and not out.is_symlink(), "preflight output directory out of scope")
    require(phase in ("executor", "evaluator"), "unknown phase")
    lock = W.read(P / "BINARY_MEMBER_LOCK.json")
    old = W.read(OLD / "ASSET_LOCK.json")["files"][0]
    require(lock["archive_sha256"] == old["sha256"]
            and lock["archive_size"] == old["size"], "original asset lock mismatch")
    archive = Path.home() / ".cache/h76-spire-source" / old["filename"]
    require(archive.is_file() and not archive.is_symlink()
            and archive.stat().st_size == lock["archive_size"]
            and W.sha(archive) == lock["archive_sha256"], "existing official archive drift")
    started = time.monotonic()
    scratch = None
    owner = None
    clean = False
    error = None
    report = None
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(120)
    try:
        scratch = Path(tempfile.mkdtemp(prefix="h77r2p_", dir="/dev/shm"))
        info = scratch.lstat()
        require(not scratch.is_symlink() and stat.S_ISDIR(info.st_mode)
                and info.st_uid == os.geteuid()
                and stat.S_IMODE(info.st_mode) == 0o700, "tmpfs ownership boundary")
        owner = {"uid": info.st_uid, "gid": info.st_gid,
                 "device": info.st_dev, "inode": info.st_ino, "mode": "0700"}
        dest = scratch / "bin"
        dest.mkdir(mode=0o700)
        records = W.extract_binaries(archive, dest, lock)
        binaries = {}
        for name, expected in lock["binaries"].items():
            actual = dest / name
            require(actual.is_file() and not actual.is_symlink(), "binary file missing")
            extracted_sha = W.sha(actual)
            require(actual.stat().st_size == expected["size"]
                    and records[name]["archive_member"] == expected["archive_member"]
                    and records[name]["archive_member_sha256"] == extracted_sha == expected["sha256"],
                    "member extraction identity mismatch")
            binaries[name] = {
                "archive_member": expected["archive_member"],
                "size": actual.stat().st_size,
                "archive_member_sha256": records[name]["archive_member_sha256"],
                "extracted_sha256": extracted_sha,
            }
        report = {
            "schema": "h77r2-real-asset-preflight/v1",
            "phase": phase,
            "archive_sha256": lock["archive_sha256"],
            "archive_size": lock["archive_size"],
            "extractor_sha256": W.sha(P / "WORKLOAD.py"),
            "binaries": binaries,
            "extracted_bytes": sum(v["size"] for v in binaries.values()),
            "scratch_path": str(scratch),
            "scratch_owner": owner,
            "binary_executions": 0,
            "spire_service_starts": 0,
            "new_downloads": 0,
            "at_utc": utc(),
        }
        require(report["extracted_bytes"] == lock["total_binary_bytes"],
                "extracted byte total mismatch")
    except BaseException as exc:
        error = exc
    finally:
        signal.alarm(0)
        if scratch is not None:
            info = scratch.lstat()
            require(owner is not None
                    and (info.st_dev, info.st_ino, info.st_uid)
                    == (owner["device"], owner["inode"], owner["uid"])
                    and not scratch.is_symlink(), "preflight cleanup owner changed")
            require(shutil.rmtree.avoids_symlink_attacks, "safe cleanup unavailable")
            shutil.rmtree(scratch)
            clean = not scratch.exists() and not scratch.is_symlink()
        else:
            clean = True
        if error is not None:
            W.save(out / "FAILURE.json", {
                "schema": "h77r2-real-asset-preflight/v1", "phase": phase,
                "error_type": type(error).__name__, "error": str(error),
                "scratch_path": str(scratch) if scratch else None, "scratch_owner": owner,
                "scratch_removed": clean, "binary_executions": 0,
                "spire_service_starts": 0, "new_downloads": 0,
                "elapsed_seconds": round(time.monotonic() - started, 3), "at_utc": utc(),
            })
    if error is not None:
        raise error
    require(clean and report is not None, "asset preflight cleanup not proven")
    report["scratch_removed"] = True
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    W.save(out / "RESULT.json", report)
    print(json.dumps({"phase": phase, "result": "PASS",
                      "extracted_bytes": report["extracted_bytes"],
                      "scratch_removed": True}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("executor", "evaluator"), required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run(args.phase, Path(args.out))


if __name__ == "__main__":
    main()

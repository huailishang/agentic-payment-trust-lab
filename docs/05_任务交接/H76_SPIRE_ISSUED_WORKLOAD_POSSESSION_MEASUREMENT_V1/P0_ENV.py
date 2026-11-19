"""H76 authorized P0 Windows Docker Desktop qualification; does not touch other containers."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

P = Path(__file__).resolve().parent
EVIDENCE = P / "evidence" / "executor_p0"
DOCKER = Path(r"C:\Program Files\Docker\Docker\resources\bin\docker.exe")
DESKTOP = Path(r"C:\Program Files\Docker\Docker\Docker Desktop.exe")
ENDPOINT = "npipe:////./pipe/dockerDesktopLinuxEngine"

def now():
    return datetime.now(timezone.utc).isoformat()

def save(name: str, data: dict):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def probe(name: str):
    argv = [str(DOCKER), "--host", ENDPOINT, "version"]
    data = {"time_utc": now(), "argv": argv, "client_path_exists": DOCKER.is_file()}
    try:
        run = subprocess.run(argv, capture_output=True, timeout=20)
        data.update(exit_code=run.returncode, stdout=run.stdout.decode("utf-8", errors="replace"), stderr=run.stderr.decode("utf-8", errors="replace"), daemon_reachable=(run.returncode == 0 and b"Server:" in run.stdout))
    except Exception as exc:
        data.update(exit_code="EXCEPTION", error=type(exc).__name__ + ": " + str(exc), daemon_reachable=False)
    save(name, data)
    print(json.dumps({"check": name, "daemon_reachable": data["daemon_reachable"], "exit_code": data["exit_code"]}))
    return data["daemon_reachable"]

def start_once():
    marker = EVIDENCE / "DESKTOP_START.json"
    if marker.exists():
        raise SystemExit("H76 Docker Desktop start already attempted: no second start")
    reachable = probe("BEFORE_START.json")
    if reachable:
        save("DESKTOP_START.json", {"time_utc": now(), "status": "SKIPPED_ENGINE_ALREADY_REACHABLE", "start_attempt_count": 0})
        return
    if not DESKTOP.is_file():
        save("DESKTOP_START.json", {"time_utc": now(), "status": "INPUT_LIMIT_DESKTOP_NOT_FOUND", "desktop_exists": False, "start_attempt_count": 0})
        raise SystemExit(3)
    data = {"time_utc": now(), "desktop_exists": True, "desktop_path": str(DESKTOP), "start_attempt_count": 1}
    save("DESKTOP_START.json", {**data, "status": "STARTING"})
    try:
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        proc = subprocess.Popen([str(DESKTOP)], cwd=str(DESKTOP.parent), creationflags=flags,
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                close_fds=True)
        data.update(status="LAUNCHED", pid=proc.pid)
    except Exception as exc:
        data.update(status="START_FAILED", error=type(exc).__name__ + ": " + str(exc))
    save("DESKTOP_START.json", data)
    print(json.dumps({k: data[k] for k in ("status", "start_attempt_count")}))
    if data["status"] != "LAUNCHED":
        raise SystemExit(4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("start_once", "probe"))
    args = parser.parse_args()
    if args.operation == "start_once":
        start_once()
    else:
        raise SystemExit(0 if probe("AFTER_START.json") else 2)

"""Process-only native Python isolation and entry to the public workflow runner."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import uuid
import os
from pathlib import Path
import subprocess
import sys

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
PYTHON = Path("D:/SoftWare/Anaconda/workspace/.conda/envs/agent/python.exe")


def environment():
    env = os.environ.copy()
    base = P / "runtime" / "userbase"
    shim = base / "Python312" / "site-packages" / "tests"
    shim.mkdir(parents=True, exist_ok=True)
    (shim / "__init__.py").write_text("__path__ = [" + repr(str(ROOT / "tests")) + "]\n", encoding="utf-8")
    env.update(PYTHONUSERBASE=str(base), PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1", H76_PHASE="executor")
    env["PATH"] = str(PYTHON.parent) + os.pathsep + env.get("PATH", "")
    return env


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("executor", "evaluator"), required=True)
    parser.add_argument("--attempt", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    if args.mode == "evaluator" and args.attempt != 1:
        raise SystemExit("only one formal L3 is authorized")
    if not (P / "AUTHORIZATION.md").is_file():
        raise SystemExit("runtime authority missing; do not start L2/L3")
    env = environment()
    env["H76_PHASE"] = args.mode
    out = P / "evidence" / (("l2" if args.attempt == 1 else "l2_retry_02") if args.mode == "executor" else "l3")
    if out.exists():
        raise SystemExit("gate output already exists; preserve it and follow bounded retry protocol")
    ledger = P / ("ATTEMPT_LEDGER.jsonl" if args.mode == "executor" else "evidence/evaluator_ATTEMPT_LEDGER.jsonl")
    ledger.parent.mkdir(parents=True, exist_ok=True)
    entries = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()] if ledger.exists() else []
    kind = "formal_l2" if args.mode == "executor" else "formal_l3"
    if sum(e["kind"] == kind for e in entries) >= (2 if args.mode == "executor" else 1):
        raise SystemExit("formal gate attempt ceiling reached")
    event_id = uuid.uuid4().hex
    with ledger.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"event_id": event_id, "kind": kind, "phase": args.mode, "begin_utc": datetime.now(timezone.utc).isoformat(), "result": "STARTED", "gate_out": out.relative_to(P).as_posix()}) + "\n")
    command = [str(PYTHON), "-B", str(ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py"), "--repo", str(ROOT), "--plan", str(P / "VALIDATION_PLAN.yaml"), "--out", str(out), "--mode", args.mode]
    code = subprocess.call(command, cwd=ROOT, env=env)
    with ledger.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"event_id": uuid.uuid4().hex, "kind": "result", "ref_event_id": event_id, "end_utc": datetime.now(timezone.utc).isoformat(), "exit_code": code, "result": "PASS" if code == 0 else "FAIL"}) + "\n")
    raise SystemExit(code)


if __name__ == "__main__":
    main()

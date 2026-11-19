"""Bounded H77 public-runner entry; never changes the shared Python environment."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

import CONTROL

P = Path(__file__).resolve().parent
ROOT = P.parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("executor", "evaluator"), required=True)
    parser.add_argument("--attempt", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    CONTROL.authority(P, ROOT, args.mode)
    if args.mode == "executor" and args.attempt == 2:
        if (P / "evidence/asset_preflight/executor_01/START.json").exists():
            raise SystemExit("asset budget already consumed; no second L2")
        first = P / "evidence/l2/L2-GATE.json"
        if first.exists() and json.loads(first.read_text(encoding="utf-8"))["result"] == "PASS":
            raise SystemExit("stop on successful L2")
    if args.mode == "evaluator" and args.attempt != 1:
        raise SystemExit("one L3 only")
    if args.mode == "executor" and not (P / "RUN.py").is_file():
        raise SystemExit("RUN.py must be implemented and reviewable before L2")
    phase = "l3" if args.mode == "evaluator" else ("l2" if args.attempt == 1 else "l2_retry_02")
    out = P / "evidence" / phase
    if out.exists():
        raise SystemExit("immutable gate path already exists")
    if args.attempt == 2 and not (P / "evidence/l2/L2-GATE.json").is_file():
        raise SystemExit("second L2 requires the preserved first gate")
    env = os.environ.copy()
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    ledger = P / ("ATTEMPT_LEDGER.jsonl" if args.mode == "executor" else "evidence/EVALUATOR_ATTEMPT_LEDGER.jsonl")
    ledger.parent.mkdir(parents=True, exist_ok=True)
    marker = P / "evidence" / ("FORMAL_" + phase + "_START.json")
    with marker.open("x", encoding="utf-8") as stream:
        json.dump({"phase": phase, "at_utc": datetime.now(timezone.utc).isoformat()}, stream)
    with ledger.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"kind": "gate_start", "phase": phase, "at_utc": datetime.now(timezone.utc).isoformat()}) + "\n")
    command = [sys.executable, "-B", str(ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py"), "--repo", str(ROOT), "--plan", str(P / "VALIDATION_PLAN.yaml"), "--out", str(out), "--mode", args.mode]
    result = subprocess.run(command, cwd=ROOT, env=env, check=False)
    with ledger.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"kind": "gate_end", "phase": phase, "exit_code": result.returncode, "at_utc": datetime.now(timezone.utc).isoformat()}) + "\n")
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()

"""Bounded offline public-runner entry; no external execution or source issuance."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

import RUN

P = Path(__file__).resolve().parent
ROOT = P.parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("executor", "evaluator"), required=True)
    parser.add_argument("--attempt", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    RUN.authority(args.mode)
    if args.mode == "executor" and args.attempt == 2:
        first = P / "evidence/l2/L2-GATE.json"
        if first.exists() and json.loads(first.read_text(encoding="utf-8"))["result"] == "PASS":
            raise SystemExit("stop on successful L2")
    if args.mode == "evaluator" and args.attempt != 1:
        raise SystemExit("one offline L3 only")
    name = "l3" if args.mode == "evaluator" else ("l2" if args.attempt == 1 else "l2_retry_02")
    out = P / "evidence" / name
    if out.exists() or (args.attempt == 2 and not (P / "evidence/l2/L2-GATE.json").exists()):
        raise SystemExit("immutable or missing prior gate")
    env = os.environ.copy()
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    ledger = P / ("ATTEMPT_LEDGER.jsonl" if args.mode == "executor" else "evidence/EVALUATOR_ATTEMPT_LEDGER.jsonl")
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with (P / "evidence" / ("FORMAL_" + name + "_START.json")).open("x", encoding="utf-8") as marker:
        json.dump({"phase": name, "at_utc": datetime.now(timezone.utc).isoformat()}, marker)
    with ledger.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"kind": "gate_start", "phase": name, "at_utc": datetime.now(timezone.utc).isoformat()}) + "\n")
    command = [sys.executable, "-B", str(ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py"), "--repo", str(ROOT), "--plan", str(P / "VALIDATION_PLAN.yaml"), "--out", str(out), "--mode", args.mode]
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
    with ledger.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"kind": "gate_end", "phase": name, "exit_code": completed.returncode, "at_utc": datetime.now(timezone.utc).isoformat()}) + "\n")
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()

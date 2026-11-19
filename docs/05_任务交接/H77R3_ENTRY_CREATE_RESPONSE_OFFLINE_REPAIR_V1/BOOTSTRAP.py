"""Bounded offline-only entry for the shared L2/L3 runner."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

P = Path(__file__).resolve().parent
ROOT = P.parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("executor", "evaluator"), required=True)
    parser.add_argument("--attempt", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    import yaml
    route = yaml.safe_load((ROOT / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0])
    expected = {("Executor", "CONTRACT_FROZEN"), ("Executor", "EXECUTING")} if args.mode == "executor" else {("Evaluator", "READY_FOR_REVIEW")}
    if route["task_id"] != P.name or (route["current_role"], route["state"]) not in expected:
        raise SystemExit("route authority mismatch")
    if any(route.get(key) is not False for key in ("authorization_local_service", "authorization_existing_wsl", "authorization_api_call", "authorization_ephemeral_test_credentials", "authorization_test_payments")):
        raise SystemExit("offline-only authority required")
    if args.mode == "evaluator" and (args.attempt != 1 or not (P / "evidence/ACCEPTED.json").is_file()):
        raise SystemExit("one accepted offline L3 only")
    phase = "l3" if args.mode == "evaluator" else ("l2" if args.attempt == 1 else "l2_retry_02")
    out = P / "evidence" / phase
    if out.exists() or (args.attempt == 2 and not (P / "evidence/l2/L2-GATE.json").exists()):
        raise SystemExit("immutable or missing prior gate")
    ledger = P / ("ATTEMPT_LEDGER.jsonl" if args.mode == "executor" else "evidence/EVALUATOR_ATTEMPT_LEDGER.jsonl")
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with (P / "evidence" / ("FORMAL_" + phase + "_START.json")).open("x", encoding="utf-8") as stream:
        json.dump({"phase": phase, "at_utc": datetime.now(timezone.utc).isoformat(), "issuer_budget": 0}, stream)
    with ledger.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"kind": "gate_start", "phase": phase, "at_utc": datetime.now(timezone.utc).isoformat()}) + "\n")
    env = os.environ.copy()
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [sys.executable, "-B", str(ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py"), "--repo", str(ROOT), "--plan", str(P / "VALIDATION_PLAN.yaml"), "--out", str(out), "--mode", args.mode]
    result = subprocess.run(command, cwd=ROOT, env=env, check=False)
    with ledger.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"kind": "gate_end", "phase": phase, "exit_code": result.returncode, "at_utc": datetime.now(timezone.utc).isoformat()}) + "\n")
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()

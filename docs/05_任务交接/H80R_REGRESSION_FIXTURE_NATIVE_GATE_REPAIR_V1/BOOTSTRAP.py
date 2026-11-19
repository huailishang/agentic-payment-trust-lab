"""Bounded implementation registration and unchanged public L2/L3 runner."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

import CHECK

P = Path(__file__).resolve().parent
ROOT = P.parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("implementation", "executor", "evaluator"), required=True)
    parser.add_argument("--attempt", choices=(1, 2), type=int, default=1)
    args = parser.parse_args()
    CHECK.need(sys.platform == "win32" and os.name == "nt", "native Windows only; no WSL/Bash launcher")
    CHECK.need(args.mode != "implementation" or args.attempt == 1, "one implementation cycle only")
    route = CHECK.route()
    if args.mode == "evaluator":
        CHECK.need(route["state"] == "READY_FOR_REVIEW" and args.attempt == 1 and (P / "evidence/ACCEPTED.json").exists(), "accept snapshot before unique L3")
        CHECK.need(route["current_role"] == "Evaluator", "Evaluator role required")
    else:
        CHECK.need(route["current_role"] == "Executor", "Executor role required")
    CHECK.preservation()
    if args.attempt == 2:
        first = P / "evidence/l2/L2-GATE.json"
        CHECK.need(args.mode == "executor", "second attempt is environment-only L2")
        CHECK.need(first.exists() and CHECK.read(first)["result"] != "PASS", "stop after successful L2 or missing first gate")
        gate = CHECK.read(first)
        CHECK.need([c["check_id"] for c in gate["checks"] if c["result"] != "PASS"] == ["VP-03"], "only isolated launch import failure may retry")
        err = (ROOT / gate["checks"][2]["stderr"]).read_text(encoding="utf-8", errors="replace")
        CHECK.need("ModuleNotFoundError: No module named 'agentic_payment_experiment'" in err and err.count("FAIL: ") == 1 and "FAIL: test_cold_child_process_deserializes_original_graph" in err, "not a permitted import-only failure")
        note = CHECK.read(P / "ENVIRONMENT_RETRY.json")
        CHECK.need(note.get("failure_family") == "native_import_environment" and bool(note.get("reason")), "preserve explicit environment diagnosis")
        first_marker = CHECK.read(P / "evidence/FORMAL_l2_START.json")
        CHECK.need(all(CHECK.sha(ROOT / rel) == value for rel, value in first_marker["mutable_sha256"].items()), "no implementation change after first L2")
    evidence = P / "evidence"
    evidence.mkdir(exist_ok=True)
    ledger = evidence / "EVALUATOR_ATTEMPT_LEDGER.jsonl" if args.mode == "evaluator" else P / "ATTEMPT_LEDGER.jsonl"
    name = "implementation_0" + str(args.attempt) if args.mode == "implementation" else ("l3" if args.mode == "evaluator" else ("l2" if args.attempt == 1 else "l2_retry_02"))
    out = evidence / name
    marker = evidence / ("FORMAL_" + name + "_START.json")
    CHECK.need(not marker.exists() and not out.exists(), "attempt already consumed")
    if args.mode == "executor":
        CHECK.need((evidence / ("FORMAL_implementation_01_START.json")).exists(), "register implementation cycle first")
        if args.attempt == 1:
            with ledger.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"kind": "end", "phase": "implementation_01", "at_utc": datetime.now(timezone.utc).isoformat(), "meaning": "wall span to L2, not measured active minutes"}) + "\n")
    with marker.open("x", encoding="utf-8") as stream:
        json.dump({"phase": name, "at_utc": datetime.now(timezone.utc).isoformat(), "mutable_sha256": {rel: CHECK.sha(ROOT / rel) for rel in CHECK.read(P / "BASELINE.json")["mutable"]}, "execution_platform": sys.platform}, stream)
    with ledger.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"kind": "start", "phase": name, "at_utc": datetime.now(timezone.utc).isoformat()}) + "\n")
    if args.mode == "implementation":
        print(json.dumps({"registered": name, "product_edits_by_bootstrap": 0}))
        return
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(ROOT / "src"))
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    runner = ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py"
    completed = subprocess.run([sys.executable, "-B", str(runner), "--repo", str(ROOT), "--plan", str(P / "VALIDATION_PLAN.yaml"), "--out", str(out), "--mode", args.mode], cwd=ROOT, env=env, check=False)
    with ledger.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"kind": "end", "phase": name, "exit_code": completed.returncode, "at_utc": datetime.now(timezone.utc).isoformat()}) + "\n")
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()

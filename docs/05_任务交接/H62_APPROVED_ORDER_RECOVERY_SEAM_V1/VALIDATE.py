"""Frozen ordered phase runner; each candidate execution remains journalled."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]


def run(script, *args):
    subprocess.run([sys.executable, "-B", str(TASK / script), *args], cwd=ROOT, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("original", "approval", "accounting"))
    parser.add_argument("role", choices=("executor", "evaluator"))
    args = parser.parse_args()
    if args.phase == "original":
        run("RUN_JOURNEY.py", "--role", args.role)
        run("CHECK.py", "original", args.role)
        run("RUNTIME.py", "regression")
    elif args.phase == "approval":
        run("APPROVAL_CASES.py", "--role", args.role)
        run("CHECK.py", "approval", args.role)
    else:
        if args.role == "executor":
            path = TASK / "ATTEMPT_LEDGER.json"
            ledger = json.loads(path.read_text(encoding="utf-8"))
            ledger["formal_l2_attempts"] = len(list((TASK / "evidence").glob("l2_executor_*")))
            ledger["reservations"] = {}
            for suffix, filename in (("recovery_executor", "CASE_ATTEMPTS.jsonl"), ("recovery_executor", "OPERATIONS.jsonl"),
                                     ("approval_executor", "CASE_ATTEMPTS.jsonl"), ("executor", "HTTP_ATTEMPTS.jsonl")):
                journal = TASK / "evidence" / suffix / filename
                ledger["reservations"][suffix + "/" + filename] = len(journal.read_text(encoding="utf-8").splitlines()) if journal.exists() else 0
            path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        run("CHECK.py", "selftest")
        run("CHECK.py", "accounting")

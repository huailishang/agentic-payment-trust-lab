"""Append-only reservations and honest inherited cost reconciliation."""
import argparse
from HARNESS import TASK,execute,read,save
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--role",choices=["executor","evaluator"],required=True);args=p.parse_args()
    try:execute(args.role)
    finally:
        path=TASK/"ATTEMPT_LEDGER.json"
        if args.role=="executor" and path.exists():
            value=read(path);journal=TASK/"evidence/executor/CASE_ATTEMPTS.jsonl"
            count=len(journal.read_text(encoding="utf-8").splitlines()) if journal.exists() else 0
            gates=len(list((TASK/"evidence").glob("l2_executor_*")))
            value.update(case_attempts=count,total_executor_cases=79+count,formal_l2_attempts=gates,total_gate_attempts=2+gates)
            save(path,value)

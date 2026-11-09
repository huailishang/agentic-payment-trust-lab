"""Frozen runner wrapper: preserve all attempts and reconcile report counters."""
import argparse
import json
from HARNESS import TASK,execute,read,save

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--role",choices=["executor","evaluator"],required=True);args=parser.parse_args()
    try:
        execute(args.role)
    finally:
        path=TASK/"ATTEMPT_LEDGER.json"
        if args.role=="executor" and path.exists():
            value=read(path);journal=TASK/"evidence/executor/CASE_ATTEMPTS.jsonl"
            value["case_attempts"]=len(journal.read_text(encoding="utf-8").splitlines()) if journal.exists() else 0
            value["formal_l2_attempts"]=len(list((TASK/"evidence").glob("l2_executor_*")))
            save(path,value)

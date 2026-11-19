"""Frozen offline checks. Source and historical claims still require Evaluator semantics."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import json
import subprocess
import sys

PACK=Path(__file__).resolve().parent
ROOT=PACK.parents[2]

def need(value,code):
    if not value: raise ValueError(code)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def unique(pairs):
    out={}
    for key,value in pairs:
        need(key not in out,"duplicate_key"); out[key]=value
    return out
def load(path):
    need(path.is_file() and path.stat().st_size<=4*1024*1024,"json_file")
    value=json.loads(path.read_text(encoding="utf-8"),object_pairs_hook=unique)
    need(isinstance(value,dict),"json_object"); return value
def stamp(value):
    value=datetime.fromisoformat(value.replace("Z","+00:00")); need(value.tzinfo is not None,"timezone"); return value
def rows():
    path=PACK/"ATTEMPT_LEDGER.jsonl"
    return [json.loads(x,object_pairs_hook=unique) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()] if path.exists() else []

def integrity():
    b=load(PACK/"BASELINE.json")
    head=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    need(head==b["head"],"baseline_head")
    for rel,digest in b["protected"].items(): need((ROOT/rel).is_file() and sha((ROOT/rel).read_bytes())==digest,"protected_input_changed")
    for rel,digest in b["frozen"].items(): need(sha((PACK/rel).read_bytes())==digest,"frozen_input_changed")
    current=(ROOT/"CURRENT.md").read_text(encoding="utf-8")
    need("task_id: "+PACK.name in current,"router_task")
    for name in ("commit","push","history_rewrite","api_call","install","local_service","browser_test_only","test_payments"):
        need("authorization_"+name+": false" in current,"authority_expanded")
    out=subprocess.run(["git","ls-files","--others","--exclude-standard","-z"],cwd=ROOT,capture_output=True,check=True).stdout
    prefix=PACK.relative_to(ROOT).as_posix()+"/"
    allowed=set(b["frozen"])|{"BASELINE.json","RUN.py","EVIDENCE_CORRECTION.json","CORRECTED_MATRIX.json","RESULT.json","REPORT.md","REVIEW.md","ATTEMPT_LEDGER.jsonl"}
    for item in out.split(b"\0"):
        if not item: continue
        rel=item.decode("utf-8"); need(rel in b["inherited_untracked"] or rel.startswith(prefix),"new_file_scope")
        if rel.startswith(prefix): need(rel[len(prefix):] in allowed or rel[len(prefix):].startswith(("evidence/","versions/")),"new_output_scope")
    print("H71R frozen scope, historical evidence and offline-only authority intact")

def artifacts():
    gold=load(PACK/"EVIDENCE_GOLD.json"); correction=load(PACK/"EVIDENCE_CORRECTION.json")
    need(correction["original_snapshot_sha256"]==gold["snapshot_sha256"] and correction["no_historical_backfill"] is True,"historical_binding")
    need(correction["gets"]==gold["gets"],"successful_gets_lost_or_changed")
    expected=gold["failed_source_attempts"]
    need(len(correction["failed_sources"])==2,"failed_sources_missing")
    for row in correction["failed_sources"]:
        need(row["attempt_id"] in expected and row["http_status"]==200 and row["archived_bytes"]==0
             and row["received_bytes"] is None and row["failure_phase"]=="BODY_READ","false_historical_source_precision")
    need(len({r["attempt_id"] for r in correction["failed_sources"]})==2,"duplicate_failed_source")
    download=correction["download"]
    need(download["http_status"] is None and download["http_status_certainty"]=="UNKNOWN"
         and download["failure_phase"]=="UNKNOWN" and download["archived_bytes"]==0 and download["received_bytes"] is None
         and download["guaranteed_remaining_download_bytes"]==0,"false_historical_download_precision")
    need(isinstance(correction["uncertainty_note"],str) and correction["uncertainty_note"].strip(),"uncertainty_note")
    matrix=load(PACK/"CORRECTED_MATRIX.json")
    need(sorted(r["id"] for r in matrix["rows"])==sorted(gold["matrix_ids"]),"matrix_coverage")
    for row in matrix["rows"]:
        need(all(isinstance(row[k],str) and row[k].strip() for k in ("observed","documented","unknown")),"matrix_fields")
        if row["id"]=="checkout_required_endpoints":
            need(row["observations"]==gold["gets"] and "200" in row["observed"] and "NOT_MEASURED" not in row["observed"],"matrix_stale_after_gets")
    used=set()
    for note in matrix["source_notes"]:
        need(note["source_id"] in gold["sources"] and isinstance(note["claim"],str) and note["claim"].strip(),"source_note")
        source=gold["sources"][note["source_id"]]; path=ROOT/source["repo_file"]
        need(sha(path.read_bytes())==source["sha256"],"source_changed")
        quote=note["quote"]
        need(isinstance(quote,str) and 20<=len(quote)<=1200 and quote in path.read_text(encoding="utf-8"),"source_quote")
        need("selector" not in quote and "aria-hidden" not in quote and "Listen for events" not in quote,"navigation_reference")
        used.add(note["source_id"])
    need(used==set(gold["sources"]),"two_relevant_sources_required")
    result=load(PACK/"RESULT.json")
    need(result["task_id"]==PACK.name and result["decision"]=="REPAIR_COMPLETE" and result["original_h71_verdict"]=="REJECTED","false_rehabilitation")
    need(result["correction_sha256"]==sha((PACK/"EVIDENCE_CORRECTION.json").read_bytes()) and result["matrix_sha256"]==sha((PACK/"CORRECTED_MATRIX.json").read_bytes()),"result_digest")
    keys={"network_requests","downloads","runtime_api","browser_actions","local_services","installs","environments","checkout_sessions","payments","commits","pushes"}
    need(set(result["side_effects"])==keys and all(type(x) is int and x==0 for x in result["side_effects"].values()),"external_side_effects")
    print("H71R historical uncertainty, successful observations and literal source citations consistent; semantic review required")

def budget(closed=False):
    data=rows(); need([r["seq"] for r in data]==list(range(1,len(data)+1)),"ledger_sequence")
    begin,end,counts={},{},{}
    for row in data:
        need(row["event"] in {"BEGIN","END"},"ledger_event")
        table=begin if row["event"]=="BEGIN" else end
        need(row["attempt_id"] not in table,"ledger_duplicate"); table[row["attempt_id"]]=row
    need(set(end)<=set(begin),"ledger_begin_missing")
    active=[]; now=datetime.now(timezone.utc)
    for ident,first in begin.items():
        kind=first["kind"]; need(kind in {"active_work","implementation","l2","l3"},"external_attempt_forbidden")
        counts[kind]=counts.get(kind,0)+1
        if kind!="active_work": need(counts[kind]<={"implementation":2,"l2":3,"l3":1}[kind],"attempt_budget")
        last=end.get(ident)
        need(last is not None or (not closed and kind in {"active_work","l2","l3"}),"attempt_unclosed")
        start=stamp(first["at"]); finish=stamp(last["at"]) if last else now
        need(finish>=start,"ledger_time")
        if last: need(last["kind"]==kind and last["status"] in {"SUCCEEDED","FAILED","INPUT_LIMIT"},"ledger_end")
        if kind=="active_work": active.append((start,finish))
    active.sort(); need(all(a[1]<=b[0] for a,b in zip(active,active[1:])) and sum((b-a).total_seconds() for a,b in active)<=7200,"active_budget")
    if data:
        need(active,"active_work_missing")
        finish=max([stamp(r["at"]) for r in data]+([now] if set(begin)-set(end) else []))
        need((finish-min(stamp(r["at"]) for r in data)).total_seconds()<=10800,"wall_budget")
    print("H71R offline-only declared attempts and budget valid; implementation audit still required")

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("command",choices=("integrity","artifacts","budget")); parser.add_argument("--closed",action="store_true"); args=parser.parse_args()
    try:
        if args.command=="integrity": integrity()
        elif args.command=="artifacts": artifacts()
        else: budget(args.closed)
    except (OSError,ValueError,TypeError,KeyError,AttributeError,AssertionError,subprocess.SubprocessError):
        print("H71R CHECK FAILED; inspect artifacts locally",file=sys.stderr); raise SystemExit(1)

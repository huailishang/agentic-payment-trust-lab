"""Frozen scope, evidence and budget checks; does not implement the candidate."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from HARNESS import CASES,ROOT,TASK,read,sha

def baseline():
    lock=read(TASK/"INPUTS.json")
    assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()==lock["head"]
    text=(ROOT/"CURRENT.md").read_text(encoding="utf-8")
    block=text.split("```yaml",1)[1].split("```",1)[0]
    router={line.split(":",1)[0].strip():line.split(":",1)[1].strip() for line in block.splitlines() if ":" in line}
    assert router["task_id"]==TASK.name and router["task_kind"]=="capability_experiment"
    assert router["project_map_revision"]=="2026-11-02-r97" and router["active_bottleneck_id"]=="B-17" and router["hypothesis_id"]=="H-60"
    assert (router["state"],router["current_role"]) in {("CONTRACT_FROZEN","Executor"),("EXECUTING","Executor"),("READY_FOR_REVIEW","Evaluator")}
    assert all(router["authorization_"+k]=="false" for k in ("commit","push","history_rewrite","api_call"))
    assert hashlib.sha256(text.split("## Global position",1)[1].encode()).hexdigest()==lock["current_history_sha256"]
    for n,h in lock["protected_files"].items():assert sha(ROOT/n)==h,n
    for n,h in lock["frozen_files"].items():assert sha(TASK/n)==h,n
    for row in lock["source_databases"].values():assert sha(ROOT/row["path"])==row["sha256"]
    files={s.decode("utf-8") for s in subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard"],cwd=ROOT).split(b"\0") if s}
    prefix=TASK.relative_to(ROOT).as_posix()+"/"
    assert all(n.startswith(prefix) for n in files-set(lock["workspace_files"]))
    allowed={"APPROVAL_INBOX.py","INPUTS.json","REPORT.md","REVIEW.md","RESULT.json","ATTEMPT_LEDGER.json"}
    for p in TASK.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            n=p.relative_to(TASK).as_posix();assert n in lock["frozen_files"] or n in allowed or n.startswith("evidence/"),n
    print(json.dumps({"protected":len(lock["protected_files"]),"frozen":len(lock["frozen_files"]),"databases":2}))

def scope():
    p=TASK/"APPROVAL_INBOX.py";tree=ast.parse(p.read_text(encoding="utf-8"))
    allowed={"argparse","collections","contextlib","copy","dataclasses","datetime","enum","hashlib","json","logging","os","pathlib","re","sqlite3","sys","threading","time","typing","uuid"}
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):assert all(a.name.split(".")[0] in allowed for a in node.names)
        if isinstance(node,ast.ImportFrom):assert node.module and node.module.split(".")[0] in allowed
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):assert node.func.id not in {"eval","exec","__import__"}
    assert [r["id"] for r in read(TASK/"CASE_SPEC.json")["cases"]]==CASES
    print(json.dumps({"candidate_files":1,"standard_library_only":True,"requires_manual_read_only_review":True}))

def validate(v):
    assert v["schema"]=="h60-results/v1"
    assert [c["case"] for c in v["cases"]]==CASES
    assert all(c["result"]=="PASS" and c["execution_enabled"] is False and c["source_hashes"] for c in v["cases"])
    assert v["business_execution_enabled"] is False and v["new_payment_calls"]==v["new_order_writes"]==0

def materials(role):
    folder=TASK/"evidence"/role;name=read(folder/"LATEST.json")["run"]
    assert Path(name).name==name
    run=folder/name;value=read(run/"results.json");validate(value)
    for c in value["cases"]:
        assert read(run/(c["case"]+".json"))==c
        for field,label in (("transactions_path","tx"),("psp_path","psp")):
            path=Path(c[field]).resolve();assert path.is_relative_to((ROOT/".task_envs/H60/runs").resolve());assert sha(path)==c["source_hashes"][label]
    rows=[json.loads(s) for s in (folder/"CASE_ATTEMPTS.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows)==len({r["id"] for r in rows})<=(160 if role=="executor" else 60)
    assert [r["case"] for r in rows if r["run"]==name]==CASES
    ledger=read(TASK/"ATTEMPT_LEDGER.json")
    ex=[json.loads(s) for s in (TASK/"evidence/executor/CASE_ATTEMPTS.jsonl").read_text(encoding="utf-8").splitlines()]
    assert ledger["case_attempts"]==len(ex)<=160 and 0<=ledger["active_work_minutes"]<=240
    assert ledger["formal_l2_attempts"]==len(list((TASK/"evidence").glob("l2_executor_*")))<=2
    assert ledger["work_intervals_utc"] and all(w["start"]<=w["end"] for w in ledger["work_intervals_utc"])
    for k in ("http_requests","new_payment_calls","new_order_writes","recovery_calls","network_calls","model_calls","packages_installed","git_write_operations"):assert ledger[k]==0
    result=read(TASK/"RESULT.json");assert result["task_id"]==TASK.name and result["classification"]=="LOCAL_OPERATOR_APPROVAL_ONLY"
    for k in ("business_execution_enabled","human_authentication_verified","production_ready","provider_verified","customer_value_proven"):assert result[k] is False
    assert result["remaining_gaps"]
    print(json.dumps({"cases":len(CASES),"role":role,"business_execution_enabled":False}))

def selftest():
    base={"schema":"h60-results/v1","cases":[{"case":n,"result":"PASS","execution_enabled":False,"source_hashes":{"tx":"synthetic"}} for n in CASES],"business_execution_enabled":False,"new_payment_calls":0,"new_order_writes":0}
    validate(base);bads=[]
    x=copy.deepcopy(base);x["cases"].pop();bads.append(x)
    x=copy.deepcopy(base);x["cases"][0]["execution_enabled"]=True;bads.append(x)
    x=copy.deepcopy(base);x["cases"][0]["result"]="FAIL";bads.append(x)
    x=copy.deepcopy(base);x["business_execution_enabled"]=True;bads.append(x)
    x=copy.deepcopy(base);x["new_payment_calls"]=1;bads.append(x)
    x=copy.deepcopy(base);x["cases"][0]["source_hashes"]={};bads.append(x)
    for x in bads:
        try:validate(x)
        except AssertionError:pass
        else:raise AssertionError("corrupted evidence accepted")
    print(json.dumps({"corruptions_rejected":len(bads),"candidate_called":False}))

if __name__=="__main__":
    if sys.argv[1]=="materials":materials(sys.argv[2])
    else:{"baseline":baseline,"scope":scope,"selftest":selftest}[sys.argv[1]]()

"""Frozen H60R checker, no candidate implementation."""
import ast
import copy
import json
from pathlib import Path
import subprocess
import sys
from HARNESS import CASES,ROOT,TASK,read,sha

def baseline():
    lock=read(TASK/"INPUTS.json")
    assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()==lock["head"]
    block=(ROOT/"CURRENT.md").read_text(encoding="utf-8").split("```yaml",1)[1].split("```",1)[0]
    route={s.split(":",1)[0].strip():s.split(":",1)[1].strip() for s in block.splitlines() if ":" in s}
    assert route["task_id"]==TASK.name and route["task_kind"]=="repair"
    assert route["project_map_revision"]=="2026-11-04-r98" and route["active_bottleneck_id"]=="B-17"
    assert (route["state"],route["current_role"]) in {("CONTRACT_FROZEN","Executor"),("EXECUTING","Executor"),("READY_FOR_REVIEW","Evaluator")}
    assert all(route["authorization_"+k]=="false" for k in ("commit","push","history_rewrite","api_call"))
    for name,h in lock["protected_files"].items():assert sha(ROOT/name)==h,name
    for name,h in lock["frozen_files"].items():assert sha(TASK/name)==h,name
    for row in lock["source_databases"].values():assert sha(ROOT/row["path"])==row["sha256"]
    files={s.decode("utf-8") for s in subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard"],cwd=ROOT).split(b"\0") if s}
    prefix=TASK.relative_to(ROOT).as_posix()+"/"
    assert all(n.startswith(prefix) for n in files-set(lock["workspace_files"])),"new unrelated file"
    allowed={"APPROVAL_INBOX.py","INPUTS.json","REPORT.md","REVIEW.md","RESULT.json","ATTEMPT_LEDGER.json"}
    for p in TASK.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            name=p.relative_to(TASK).as_posix();assert name in lock["frozen_files"] or name in allowed or name.startswith("evidence/"),name
    print(json.dumps({"protected":len(lock["protected_files"]),"frozen":len(lock["frozen_files"]),"original_sources":2}))

def stripped(path):
    tree=ast.parse(path.read_text(encoding="utf-8"))
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="ApprovalInbox")
    cls.body=[n for n in cls.body if not (isinstance(n,ast.FunctionDef) and n.name=="__init__")]
    return ast.dump(tree,include_attributes=False)

def scope():
    parent=ROOT/read(TASK/"INPUTS.json")["parent_task"]
    assert stripped(TASK/"APPROVAL_INBOX.py")==stripped(parent/"APPROVAL_INBOX.py"),"only constructor may change"
    assert len(CASES)==24
    print(json.dumps({"candidate_files":1,"only_constructor_changes":True,"cases":24}))

def validate(value):
    assert value["schema"]=="h60-results/v1"
    assert [r["case"] for r in value["cases"]]==CASES
    assert all(r["result"]=="PASS" and r["execution_enabled"] is False and r["source_hashes"] for r in value["cases"])
    assert value["business_execution_enabled"] is False and value["new_payment_calls"]==value["new_order_writes"]==0

def materials(role):
    folder=TASK/"evidence"/role;run=read(folder/"LATEST.json")["run"];assert Path(run).name==run
    value=read(folder/run/"results.json");validate(value)
    for row in value["cases"]:
        assert read(folder/run/(row["case"]+".json"))==row
        for field,label in (("transactions_path","tx"),("psp_path","psp")):
            path=Path(row[field]).resolve();assert path.is_relative_to((ROOT/".task_envs/H60R/runs").resolve())
            assert sha(path)==row["source_hashes"][label]
    rows=[json.loads(s) for s in (folder/"CASE_ATTEMPTS.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows)==len({r["id"] for r in rows})<=(72 if role=="executor" else 34)
    assert [r["case"] for r in rows if r["run"]==run]==CASES
    ledger=read(TASK/"ATTEMPT_LEDGER.json")
    ex=TASK/"evidence/executor/CASE_ATTEMPTS.jsonl"
    count=len(ex.read_text(encoding="utf-8").splitlines()) if ex.exists() else 0
    gates=len(list((TASK/"evidence").glob("l2_executor_*")))
    assert ledger["inherited_executor_cases"]==79 and ledger["case_attempts"]==count<=72
    assert ledger["total_executor_cases"]==79+count<=160
    assert ledger["inherited_gate_attempts"]==2 and ledger["formal_l2_attempts"]==gates<=2
    assert ledger["total_gate_attempts"]==2+gates<=4
    assert ledger["inherited_evaluator_charge"]==26
    assert 0<=ledger["active_work_minutes"]<=120 and ledger["charged_minutes_total"]==30+ledger["active_work_minutes"]<=150
    assert ledger["work_intervals_utc"] and all(w["start"]<=w["end"] for w in ledger["work_intervals_utc"])
    for key in ("http_requests","new_payment_calls","new_order_writes","recovery_calls","network_calls","model_calls","packages_installed","git_write_operations"):assert ledger[key]==0
    result=read(TASK/"RESULT.json");assert result["task_id"]==TASK.name
    assert result["classification"]=="LOCAL_OPERATOR_APPROVAL_ONLY" and result["remaining_gaps"]
    for key in ("business_execution_enabled","human_authentication_verified","production_ready","provider_verified","customer_value_proven"):assert result[key] is False
    print(json.dumps({"cases":24,"role":role,"executor_total":79+count,"new_gate_attempts":gates}))

def selftest():
    good={"schema":"h60-results/v1","cases":[{"case":n,"result":"PASS","execution_enabled":False,"source_hashes":{"tx":"synthetic"}} for n in CASES],"business_execution_enabled":False,"new_payment_calls":0,"new_order_writes":0}
    validate(good);bads=[]
    v=copy.deepcopy(good);v["cases"].pop();bads.append(v)
    v=copy.deepcopy(good);v["cases"][0]["execution_enabled"]=True;bads.append(v)
    v=copy.deepcopy(good);v["cases"][0]["result"]="FAIL";bads.append(v)
    v=copy.deepcopy(good);v["business_execution_enabled"]=True;bads.append(v)
    v=copy.deepcopy(good);v["new_payment_calls"]=1;bads.append(v)
    v=copy.deepcopy(good);v["cases"][0]["source_hashes"]={};bads.append(v)
    v=copy.deepcopy(good);v["cases"][-1]["case"]="wrong-alias";bads.append(v)
    for value in bads:
        try:validate(value)
        except AssertionError:pass
        else:raise AssertionError("corrupted evidence accepted")
    print(json.dumps({"corruptions_rejected":len(bads),"candidate_called":False}))

if __name__=="__main__":
    if sys.argv[1]=="materials":materials(sys.argv[2])
    else:{"baseline":baseline,"scope":scope,"selftest":selftest}[sys.argv[1]]()

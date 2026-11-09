"""Frozen independent source-truth and design-material checker."""
import ast
from contextlib import closing
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def baseline():
    lock=read(TASK/"INPUTS.json")
    assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()==lock["head"]
    block=(ROOT/"CURRENT.md").read_text(encoding="utf-8").split("```yaml",1)[1].split("```",1)[0]
    r={s.split(":",1)[0].strip():s.split(":",1)[1].strip() for s in block.splitlines() if ":" in s}
    assert r["task_id"]==TASK.name and r["task_kind"]=="one_off" and r["project_map_revision"]=="2026-11-04-r99"
    assert (r["state"],r["current_role"]) in {("CONTRACT_FROZEN","Executor"),("EXECUTING","Executor"),("READY_FOR_REVIEW","Evaluator")}
    assert all(r["authorization_"+k]=="false" for k in ("commit","push","history_rewrite","api_call"))
    for n,h in lock["protected_files"].items():assert sha(ROOT/n)==h,n
    for n,h in lock["frozen_files"].items():assert sha(TASK/n)==h,n
    for n,row in lock["source_files"].items():assert sha(ROOT/n)==row["sha256"],n
    for row in lock["source_databases"].values():assert sha(ROOT/row["path"])==row["sha256"]
    files={s.decode("utf-8") for s in subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard"],cwd=ROOT).split(b"\0") if s}
    prefix=TASK.relative_to(ROOT).as_posix()+"/"
    assert all(n.startswith(prefix) for n in files-set(lock["workspace_files"]))
    allowed={"EXTRACT.py","INPUTS.json","ASSESSMENT.json","ANALYSIS.md","REPORT.md","REVIEW.md","RESULT.json","ATTEMPT_LEDGER.json"}
    for p in TASK.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            n=p.relative_to(TASK).as_posix();assert n in lock["frozen_files"] or n in allowed or n.startswith("evidence/"),n
    print(json.dumps({"protected":len(lock["protected_files"]),"source_files":10,"databases":3}))
def scope():
    p=TASK/"EXTRACT.py";text=p.read_text(encoding="utf-8");tree=ast.parse(text)
    allowed={"argparse","contextlib","hashlib","json","pathlib","sqlite3","sys"}
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):assert all(a.name.split(".")[0] in allowed for a in n.names)
        if isinstance(n,ast.ImportFrom):assert n.module and n.module.split(".")[0] in allowed
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):assert n.func.id not in {"eval","exec","__import__"}
    assert "mode=ro" in text and "immutable=1" in text
    assert all(p.name in {"CHECK.py","RUN_AND_ACCOUNT.py","EXTRACT.py"} for p in TASK.glob("*.py"))
    print(json.dumps({"extractor_files":1,"standard_library_only":True,"manual_sql_and_output_scope_review_required":True}))
def truth():
    lock=read(TASK/"INPUTS.json");files={}
    for n in lock["source_files"]:
        p=ROOT/n;files[n]={"sha256":sha(p),"line_count":len(p.read_text(encoding="utf-8").splitlines())}
    dbs={}
    for name,row in lock["source_databases"].items():
        p=ROOT/row["path"];assert not Path(str(p)+"-wal").exists() and not Path(str(p)+"-shm").exists()
        with closing(sqlite3.connect(p.resolve().as_uri()+"?mode=ro&immutable=1",uri=True)) as c:
            c.row_factory=sqlite3.Row
            names=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            tables={}
            for n in names:tables[n]=[dict(r) for r in c.execute('SELECT * FROM "'+n.replace('"','""')+'" ORDER BY rowid')]
        dbs[name]={"sha256":sha(p),"tables":tables}
    return {"schema":"h61-source-extraction/v1","task_id":TASK.name,"files":files,"databases":dbs,"business_execution_enabled":False}
def validate_extract(value,expected):assert value==expected and value["business_execution_enabled"] is False
def refs(values):
    lock=read(TASK/"INPUTS.json");assert isinstance(values,list) and values
    for ref in values:
        assert ref["path"] in lock["source_files"]
        lines=(ROOT/ref["path"]).read_text(encoding="utf-8").splitlines()
        a,b=ref["start"],ref["end"]
        assert type(a) is int and type(b) is int and 1<=a<=b<=len(lines) and b-a<40
        assert ref["excerpt"]=="\n".join(lines[a-1:b])
def assessment():
    a=read(TASK/"ASSESSMENT.json");lock=read(TASK/"INPUTS.json")
    assert a["schema"]=="h61-consumer-assessment/v1" and a["task_id"]==TASK.name
    assert a["business_execution_enabled"] is False and a["classification"] in {"BOUNDED_CONSUMER_CANDIDATE","CONTRACT_CHANGE_REQUIRED","NO_SAFE_CONSUMER_SEAM"}
    assert [r["id"] for r in a["topics"]]==lock["topics"]
    for row in a["topics"]:assert row["observed"] and row["impact"];refs(row["refs"])
    assert [r["id"] for r in a["options"]]==["KEEP_QUERY_ONLY","REUSE_COMPLETE","ORDER_ONLY_RECOVERY"]
    for row in a["options"]:
        assert row["classification"] in {"ABSORB","REFERENCE_ONLY","REJECT"} and row["reason"]
        assert isinstance(row["proposed_files"],list) and isinstance(row["safety_obligations"],list);refs(row["refs"])
    assert a["selected_option"] in {r["id"] for r in a["options"]} and a["rationale"]
    assert [r["id"] for r in a["future_cases"]]==lock["future_cases"]
    for row in a["future_cases"]:assert row["status"]=="DESIGN_ONLY" and row["input"] and row["expected"] and row["forbidden"]
    assert (TASK/"ANALYSIS.md").stat().st_size>0
    return a
def materials(role):
    folder=TASK/"evidence"/role;run=read(folder/"LATEST.json")["run"];assert Path(run).name==run
    validate_extract(read(folder/run/"EXTRACTION.json"),truth());a=assessment()
    attempts=[json.loads(s) for s in (folder/"EXTRACTION_ATTEMPTS.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(attempts)==len({r["id"] for r in attempts})<=(4 if role=="executor" else 2)
    assert any(r["run"]==run for r in attempts)
    ledger=read(TASK/"ATTEMPT_LEDGER.json");ex=TASK/"evidence/executor/EXTRACTION_ATTEMPTS.jsonl"
    count=len(ex.read_text(encoding="utf-8").splitlines()) if ex.exists() else 0
    assert ledger["extraction_attempts"]==count<=4
    assert ledger["formal_l2_attempts"]==len(list((TASK/"evidence").glob("l2_executor_*")))<=2
    assert 0<=ledger["active_work_minutes"]<=120 and ledger["work_intervals_utc"]
    assert all(w["start"]<=w["end"] for w in ledger["work_intervals_utc"])
    for k in ("network_calls","http_requests","model_calls","packages_installed","git_write_operations","payment_calls","order_writes","inventory_writes","approval_writes"):assert ledger[k]==0
    result=read(TASK/"RESULT.json");assert result["task_id"]==TASK.name and result["classification"]==a["classification"] and result["remaining_gaps"]
    for k in ("business_execution_enabled","human_authentication_verified","provider_verified","production_ready","customer_value_proven"):assert result[k] is False
    print(json.dumps({"role":role,"extraction_attempts":len(attempts),"topics":10,"options":3,"future_cases_design_only":8,"classification":a["classification"]}))
def selftest():
    good={"schema":"h61-source-extraction/v1","task_id":TASK.name,"files":{"x":{"sha256":"synthetic","line_count":1}},"databases":{"x":{"sha256":"synthetic","tables":{}}},"business_execution_enabled":False}
    validate_extract(good,good);bads=[]
    for key in ("schema","task_id","files","databases"):
        v=copy.deepcopy(good);v.pop(key);bads.append(v)
    v=copy.deepcopy(good);v["business_execution_enabled"]=True;bads.append(v)
    v=copy.deepcopy(good);v["files"]["x"]["sha256"]="tampered";bads.append(v)
    for v in bads:
        try:validate_extract(v,good)
        except (AssertionError,KeyError):pass
        else:raise AssertionError("corruption accepted")
    print(json.dumps({"corruptions_rejected":6,"extractor_called":False}))
if __name__=="__main__":
    if sys.argv[1]=="materials":materials(sys.argv[2])
    else:{"baseline":baseline,"scope":scope,"selftest":selftest}[sys.argv[1]]()

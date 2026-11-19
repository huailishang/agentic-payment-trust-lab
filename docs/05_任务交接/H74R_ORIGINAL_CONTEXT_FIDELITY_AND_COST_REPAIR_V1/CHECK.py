import ast
import hashlib
import json
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path
import yaml
P=Path(__file__).resolve().parent
ROOT=P.parents[2]
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,why):
    if not ok:raise ValueError(why)
def route():return yaml.safe_load((ROOT/"CURRENT.md").read_text(encoding="utf-8").split("```yaml",1)[1].split("```",1)[0])
def package():
    for rel,h in read(P/"FREEZE.json")["files"].items():need(sha(P/rel)==h,"frozen drift:"+rel)
    for rel,h in read(P/"BASELINE.json")["protected"].items():need(sha(ROOT/rel)==h,"protected drift:"+rel)
def preservation():
    package();r=route();b=read(P/"BASELINE.json")
    need(r["task_id"]==P.name and r["task_kind"]=="repair" and r["baseline_commit"]==b["head"],"router identity")
    need(r["project_map_revision"]=="2026-11-16-r126" and r["active_bottleneck_id"]=="B-22" and r["hypothesis_id"]=="H-74","router strategy")
    roles={"CONTRACT_FROZEN":"Executor","EXECUTING":"Executor","READY_FOR_REVIEW":"Evaluator","PASS":"Evaluator","REJECTED":"Evaluator","HUMAN_REQUIRED":"Human"}
    need(roles.get(r["state"])==r["current_role"],"role/state")
    auth={"authorization_"+k for k in ("commit","push","history_rewrite","api_call","reference_read","install","local_service","browser_test_only","test_payments")}
    need(auth<=set(r) and all(v is False for k,v in r.items() if k.startswith("authorization_")),"permissions")
    need(sys.platform=="win32" and sys.version_info[:3]==(3,12,13),"native agent environment")
    import tests
    need([str(Path(x).resolve()) for x in tests.__path__]==[str((ROOT/"tests").resolve())],"tests path")
    tree=ast.parse((ROOT/"tests/test_stripe_authority_context.py").read_text(encoding="utf-8"))
    methods={c.name+"."+f.name:hashlib.sha256(ast.dump(f,include_attributes=False).encode()).hexdigest() for c in tree.body if isinstance(c,ast.ClassDef) for f in c.body if isinstance(f,ast.FunctionDef)}
    need(all(methods.get(k)==v for k,v in b["original_test_methods"].items()),"original test body changed")
    headers={c.name:[ast.dump(x,include_attributes=False) for x in c.bases] for c in tree.body if isinstance(c,ast.ClassDef)}
    need(all(headers.get(k)==v for k,v in b["original_test_bases"].items()),"original test inheritance changed")
    need(not any(k.endswith(".fail") for k in methods),"unittest fail override")
    prefix=P.relative_to(ROOT).as_posix()+"/"
    allowed=set(b["protected"])|set(b["mutable"] )|{"CURRENT.md"}
    paths=subprocess.check_output(["git","ls-files","-co","--exclude-standard","-z"],cwd=ROOT).decode().split("\0")
    for rel in filter(None,paths):need(rel.startswith(prefix) or rel in allowed,"new file outside scope:"+rel)
def costs():
    data,b=read(P/"COST_RECONCILIATION.json"),read(P/"BASELINE.json")
    for key in ("parent_ledger_sha256","parent_submission_sha256","parent_review_sha256"):need(data[key]==b[key],"parent cost reference")
    for key,val in (("original_executor_minutes",20.825250133333334),("conservative_executor_minutes",25.0192),("added_closeout_minutes",4.193949866666666)):need(abs(data[key]-val)<1e-6,"parent cost amount")
    need(data["boundary_utc"]=="2026-11-16T06:24:00+00:00" and data["actual_active_minutes"]=="UNKNOWN" and bool(data["reason"]),"cost interpretation")
def budget():
    b=read(P/"BASELINE.json");x=read(P/"ATTEMPT_LEDGER.json")
    need(x["schema"]=="h74r-cost/v1" and x["implementation_attempts"]==1 and type(x["l2_attempts"]) is int and 0<=x["l2_attempts"]<=1 and x["l3_attempts"]==0 and bool(x["windows"]) and all(w["role"]=="Executor" for w in x["windows"]),"executor ledger")
    ledgers=[x]
    if route()["current_role"]=="Evaluator":
        e=read(P/"evidence/l3_review/COST.json")
        need(e["schema"]==x["schema"] and e["l2_attempts"]==0 and e["l3_attempts"]==1 and bool(e["windows"]) and all(w["role"]=="Evaluator" for w in e["windows"]),"evaluator ledger")
        ledgers.append(e)
    totals={"Executor":0.0,"Evaluator":0.0};previous=None;now=datetime.now(timezone.utc)
    for ledger in ledgers:
        need(ledger["external_actions"]=={k:0 for k in ("network","api","install","service","browser","payment","model")},"external actions")
        for w in ledger["windows"]:
            need("end_utc" in w,"end key")
            begin=datetime.fromisoformat(w["begin_utc"].replace("Z","+00:00"));end=datetime.fromisoformat(w["end_utc"].replace("Z","+00:00")) if w["end_utc"] else now
            need(begin<=end<=now and (previous is None or begin>=previous),"cost ordering")
            need((end-begin).total_seconds()<=(3 if w["role"]=="Executor" else 1)*3600,"wall cap")
            previous=end;totals[w["role"]]+=(end-begin).total_seconds()/60
    prep=read(P/"evidence/preparation/CLOSE.json")["charged_minutes"]
    need(totals["Executor"]<=45 and totals["Evaluator"]<=15 and sum(totals.values())<=60,"repair cap")
    need(25.0192+totals["Executor"]<=105 and b["parent_evaluator_minutes"]+prep+totals["Evaluator"]<=45 and 25.0192+b["parent_evaluator_minutes"]+prep+sum(totals.values())<=150,"cumulative cap")
    dirs=sorted(p.name for p in (P/"evidence").glob("l2_attempt_*") if p.is_dir())
    need(dirs==[f"l2_attempt_{i:03d}" for i in range(1,x["l2_attempts"]+1)],"L2 count")
    print(json.dumps({"repair_role_window_minutes":totals,"preparation_minutes":prep,"parent_executor_conservative_minutes":25.0192,"parent_evaluator_minutes":b["parent_evaluator_minutes"]}))
if __name__=="__main__":
    try:
        mode=sys.argv[1]
        if mode=="final":preservation();costs();budget()
        else:{"package":package,"preservation":preservation,"costs":costs}[mode]()
        print(json.dumps({"check":mode,"status":"PASS"}))
    except Exception as exc:
        print(json.dumps({"status":"FAIL","error_type":type(exc).__name__,"reason":str(exc) if isinstance(exc,ValueError) else "input unavailable"}));sys.exit(1)

"""Frozen Evaluator scenarios. Imports only the task-owned public candidate API."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import copy
from contextlib import closing
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid

TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
NOW=1800000000
CONTEXT={"operator_id":"local-reviewer-01","active":True,"roles":["RECONCILIATION_APPROVER"],"policy_version":"h60-local-v1"}
CASES=["C01_APPROVE_AND_CLI_SHOW","C02_IDEMPOTENT_REPLAY","C03_KEY_CONFLICT","C04_REQUEST_ACTOR_SPOOF","C05_INACTIVE_CONTEXT","C06_MISSING_ROLE","C07_STALE_EXPECTED_DIGEST","C08_WRONG_TRANSACTION","C09_RECEIPT_BINDING_MISMATCH","C10_RECEIPT_MISSING","C11_EXISTING_ORDER","C12_SOURCE_CHANGED_AFTER_APPROVAL","C13_APPROVAL_EXPIRED","C14_REVOKE_AND_REPLAY","C15_SECOND_ACTIVE_APPROVAL","C16_CONTEXT_CHANGED","C17_PROCESS_RESTART","C18_TWO_CONNECTION_CONTEND","C19_OLD_CONFIRMATION_EXPIRED","C20_UNSUPPORTED_REFUND","R21_TX_HARDLINK","R22_PSP_HARDLINK","R23_TX_PATH_ALIAS","R24_PSP_PATH_ALIAS"]

def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def rows(p,table):
    with sqlite3.connect(Path(p).resolve().as_uri()+"?mode=ro&immutable=1",uri=True) as c:
        c.row_factory=sqlite3.Row
        return [dict(r) for r in c.execute('SELECT * FROM "'+table+'"')]

def source_view(tx,psp,cid):
    checkout=next(r for r in rows(tx,"checkouts") if r["id"]==cid)
    attempt=next(r for r in rows(tx,"h50_attempts") if r["checkout_id"]==cid)
    auth=next(r for r in rows(tx,"h53_authorizations") if r["checkout_id"]==cid)
    conf=next(r for r in rows(tx,"h50_confirmations") if r["confirmation_ref"]==auth["confirmation_ref"])
    receipt=next((r for r in rows(psp,"receipts") if r["payment_ref"]==attempt["payment_ref"]),None)
    inventory=sorted(rows(tx,"inventory"),key=lambda r:r["product_id"])
    orders=sorted(rows(tx,"orders"),key=lambda r:r["id"])
    return {"checkout":checkout,"attempt":attempt,"authorization":auth,"confirmation":conf,"receipt":receipt,"inventory":inventory,"orders":orders}

def digest_view(v):return hashlib.sha256(canonical(v).encode("utf-8")).hexdigest()
def candidate():
    spec=importlib.util.spec_from_file_location("h60_candidate",TASK/"APPROVAL_INBOX.py")
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    return mod

class Env:
    def __init__(self,folder,clock=NOW,context=None):
        self.folder=Path(folder);self.folder.mkdir(parents=True,exist_ok=True)
        lock=read(TASK/"INPUTS.json")
        self.tx=self.folder/"transactions.db";self.psp=self.folder/"psp.db";self.ledger=self.folder/"approvals.db"
        shutil.copyfile(ROOT/lock["source_databases"]["transactions"]["path"],self.tx)
        shutil.copyfile(ROOT/lock["source_databases"]["psp"]["path"],self.psp)
        self.source_checkpoint={"tx":sha(self.tx),"psp":sha(self.psp)}
        self.cid=lock["checkout_id"];self.ref=lock["payment_ref"]
        self.clock=clock;self.context=copy.deepcopy(context if context is not None else CONTEXT)
        self.mod=candidate()
    def box(self,context=None,clock=None):
        return self.mod.ApprovalInbox(transactions_path=str(self.tx),psp_path=str(self.psp),ledger_path=str(self.ledger),operator_context=copy.deepcopy(self.context if context is None else context),now=lambda:self.clock if clock is None else clock)
    def req(self,**updates):
        value={"request_key":"approval-01","checkout_id":self.cid,"payment_ref":self.ref,"expected_source_digest":digest_view(source_view(self.tx,self.psp,self.cid)),"disposition":"ORDER_COMPLETION","reason":"Local operator reviewed the paid order gap","expires_at":self.clock+60}
        value.update(updates);return value
    def mutate(self,path,sql,args=()):
        assert {"tx":sha(self.tx),"psp":sha(self.psp)}==self.source_checkpoint,"candidate changed source before overlay"
        with closing(sqlite3.connect(path)) as c:c.execute(sql,args);c.commit()
        self.source_checkpoint={"tx":sha(self.tx),"psp":sha(self.psp)}

def denied(env,call):
    try:call()
    except env.mod.ApprovalDenied as exc:
        assert isinstance(exc.code,str) and exc.code
        return exc.code
    raise AssertionError("request expected to be denied was accepted")

def current(value,expected=True,state="APPROVAL_CURRENT"):
    assert value["current"] is expected and value["effective_state"]==state
    assert value["execution_enabled"] is False
    record=value["record"]
    assert record["disposition"]=="ORDER_COMPLETION" and record["operator_id"]==CONTEXT["operator_id"]
    inputs=read(TASK/"INPUTS.json")
    assert record["checkout_id"]==inputs["checkout_id"] and record["payment_ref"]==inputs["payment_ref"]
    origin=source_view(ROOT/inputs["source_databases"]["transactions"]["path"],ROOT/inputs["source_databases"]["psp"]["path"],inputs["checkout_id"])
    assert record["source_digest"]==digest_view(origin) and record["context_digest"]==digest_view(CONTEXT)
    assert record["policy_version"]==CONTEXT["policy_version"]
    for k in ("approval_id","checkout_id","payment_ref","source_digest","context_digest","request_key","reason","expires_at"):
        assert record[k] is not None
    assert value["events"] and value["events"][0]["kind"]=="APPROVED"
    for i,event in enumerate(value["events"],1):
        assert event["seq"]==i and event["operator_id"]==record["operator_id"]
        assert event["approval_id"]==record["approval_id"] and event["source_digest"]==record["source_digest"]
        assert isinstance(event["at"],int)
    return record["approval_id"]

def worker(payload):
    mod=candidate();box=mod.ApprovalInbox(transactions_path=payload["tx"],psp_path=payload["psp"],ledger_path=payload["ledger"],operator_context=payload["context"],now=lambda:payload["now"])
    result=box.approve(payload["request"]) if payload["command"]=="approve" else box.show(payload["approval_id"])
    print(json.dumps({"pid":os.getpid(),"result":result}))

def original_run_case(case,folder):
    env=Env(folder);box=env.box();before={"tx":sha(env.tx),"psp":sha(env.psp)}
    detail={};req=env.req()
    if case==CASES[0]:
        inspected=box.inspect(env.cid);assert inspected["eligible"] is True and inspected["source_digest"]==req["expected_source_digest"]
        value=box.approve(req);aid=current(value);detail["approved"]=value
        config=env.folder/"operator.json";save(config,env.context)
        command=[sys.executable,"-B",str(TASK/"APPROVAL_INBOX.py"),"--transactions",str(env.tx),"--psp",str(env.psp),"--ledger",str(env.ledger),"--operator-config",str(config),"--now",str(env.clock),"show"]
        completed=subprocess.run(command,input=json.dumps({"approval_id":aid}),capture_output=True,text=True,timeout=15)
        (env.folder/"cli.stdout.log").write_text(completed.stdout,encoding="utf-8");(env.folder/"cli.stderr.log").write_text(completed.stderr,encoding="utf-8")
        assert completed.returncode==0;current(json.loads(completed.stdout))
    elif case==CASES[1]:
        first=box.approve(req);second=box.approve(copy.deepcopy(req));assert first==second and len(second["events"])==1;current(second)
    elif case==CASES[2]:
        aid=current(box.approve(req));denied(env,lambda:box.approve(dict(req,reason="changed reason")));assert len(box.show(aid)["events"])==1
    elif case==CASES[3]:denied(env,lambda:box.approve(dict(req,operator_id="spoofed-admin")))
    elif case==CASES[4]:denied(env,lambda:env.box(context=dict(CONTEXT,active=False)).approve(req))
    elif case==CASES[5]:denied(env,lambda:env.box(context=dict(CONTEXT,roles=[])).approve(req))
    elif case==CASES[6]:denied(env,lambda:box.approve(dict(req,expected_source_digest="0"*64)))
    elif case==CASES[7]:
        denied(env,lambda:box.approve(dict(req,checkout_id="other-checkout")));denied(env,lambda:box.approve(dict(req,payment_ref="other-payment")))
    elif case==CASES[8]:
        env.mutate(env.psp,"UPDATE receipts SET snapshot_json=?",("{}",));denied(env,lambda:box.approve(env.req()))
    elif case==CASES[9]:
        env.mutate(env.psp,"DELETE FROM receipts");denied(env,lambda:box.approve(env.req()))
    elif case==CASES[10]:
        env.mutate(env.tx,"INSERT INTO orders(id,data) VALUES (?,?)",("existing-order",canonical({"id":"existing-order","checkout_id":env.cid})));denied(env,lambda:box.approve(env.req()))
    elif case==CASES[11]:
        aid=current(box.approve(req));env.mutate(env.tx,"UPDATE inventory SET quantity=4 WHERE product_id='rose'");current(box.show(aid),False,"APPROVAL_STALE_SOURCE")
    elif case==CASES[12]:
        aid=current(box.approve(req));current(env.box(clock=NOW+60).show(aid),False,"APPROVAL_EXPIRED")
    elif case==CASES[13]:
        aid=current(box.approve(req));rev={"approval_id":aid,"request_key":"revoke-01","reason":"Operator withdrew the approval"}
        first=box.revoke(rev);second=box.revoke(copy.deepcopy(rev));assert first==second and len(first["events"])==2 and first["events"][-1]["kind"]=="REVOKED";current(second,False,"APPROVAL_REVOKED")
        replay=box.approve(req);current(replay,False,"APPROVAL_REVOKED");assert len(replay["events"])==2
    elif case==CASES[14]:
        aid=current(box.approve(req));denied(env,lambda:box.approve(dict(req,request_key="second-approval")));assert len(box.show(aid)["events"])==1
    elif case==CASES[15]:
        aid=current(box.approve(req));current(env.box(context=dict(CONTEXT,policy_version="h60-other-policy")).show(aid),False,"APPROVAL_STALE_CONTEXT")
        current(env.box(context=dict(CONTEXT,active=False)).show(aid),False,"APPROVAL_STALE_CONTEXT")
    elif case==CASES[16]:
        payload={"tx":str(env.tx),"psp":str(env.psp),"ledger":str(env.ledger),"context":env.context,"now":NOW,"command":"approve","request":req}
        proof=[]
        for phase in ("first","second"):
            started=time.monotonic_ns()
            completed=subprocess.run([sys.executable,"-B",str(Path(__file__).resolve()),"--worker"],input=json.dumps(payload),capture_output=True,text=True,timeout=15)
            (env.folder/(phase+".stdout.log")).write_text(completed.stdout,encoding="utf-8");(env.folder/(phase+".stderr.log")).write_text(completed.stderr,encoding="utf-8")
            assert completed.returncode==0,completed.stderr
            raw=json.loads(completed.stdout);aid=current(raw["result"])
            proof.append({"phase":phase,"started_ns":started,"finished_ns":time.monotonic_ns(),"pid":raw["pid"],"exit_code":completed.returncode})
            payload.update(command="show",approval_id=aid)
        assert proof[0]["finished_ns"]<=proof[1]["started_ns"] and len({os.getpid(),proof[0]["pid"],proof[1]["pid"]})==3
        detail["processes"]=proof
    elif case==CASES[17]:
        boxes=[env.box(),env.box()]
        barrier=threading.Barrier(2,timeout=10)
        def issue(i):
            barrier.wait()
            try:return boxes[i].approve(dict(req,request_key="contender-"+str(i)))
            except env.mod.ApprovalDenied:return None
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(issue,(0,1)))
        successes=[r for r in results if r is not None];assert len(successes)==1;aid=current(successes[0]);assert len(box.show(aid)["events"])==1
    elif case==CASES[18]:
        env.clock=1800000200;value=box.approve(env.req());current(value);assert value["record"]["expires_at"]==env.clock+60
    elif case==CASES[19]:denied(env,lambda:box.approve(dict(req,disposition="REFUND")))
    mutated=case in {CASES[8],CASES[9],CASES[10],CASES[11]}
    after={"tx":sha(env.tx),"psp":sha(env.psp)}
    assert after==env.source_checkpoint,"candidate changed source databases"
    rejected_only=case in {CASES[i] for i in (3,4,5,6,7,8,9,10,19)}
    approval_rows=rows(env.ledger,"approvals");event_rows=rows(env.ledger,"approval_events")
    assert len(approval_rows)==(0 if rejected_only else 1)
    assert len(event_rows)==(0 if rejected_only else 2 if case==CASES[13] else 1)
    return {"case":case,"result":"PASS","source_overlay":mutated,"source_hashes":after,"execution_enabled":False,"detail":detail,"approval_rows":approval_rows,"event_rows":event_rows,"ledger_path":str(env.ledger),"transactions_path":str(env.tx),"psp_path":str(env.psp)}

def alias_worker(payload):
    mod=candidate()
    try:
        mod.ApprovalInbox(transactions_path=payload["tx"],psp_path=payload["psp"],ledger_path=payload["ledger"],operator_context=CONTEXT,now=lambda:NOW)
        value={"denied":False,"code":None}
    except mod.ApprovalDenied as exc:
        value={"denied":True,"code":exc.code}
    print(json.dumps(value))

def run_case(case,folder):
    if case in CASES[:20]:return original_run_case(case,folder)
    env=Env(folder);index=CASES.index(case)
    target=env.tx if index in (20,22) else env.psp
    if index in (20,21):os.link(target,env.ledger)
    else:env.ledger=target
    before={"tx":sha(env.tx),"psp":sha(env.psp)}
    payload={"tx":str(env.tx),"psp":str(env.psp),"ledger":str(env.ledger)}
    completed=subprocess.run([sys.executable,"-B",str(Path(__file__).resolve()),"--alias-worker"],input=json.dumps(payload),capture_output=True,text=True,timeout=15)
    (env.folder/"alias.stdout.log").write_text(completed.stdout,encoding="utf-8")
    (env.folder/"alias.stderr.log").write_text(completed.stderr,encoding="utf-8")
    assert completed.returncode==0,completed.stderr
    observation=json.loads(completed.stdout)
    after={"tx":sha(env.tx),"psp":sha(env.psp)}
    assert observation["denied"] is True and isinstance(observation["code"],str) and observation["code"]
    assert before==after,"candidate wrote source through a file alias"
    for source in (env.tx,env.psp):
        with sqlite3.connect(source.resolve().as_uri()+"?mode=ro&immutable=1",uri=True) as conn:
            names={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert not {"approvals","approval_events"}.intersection(names)
    return {"case":case,"result":"PASS","source_overlay":True,"source_hashes":after,"execution_enabled":False,"detail":{"alias":observation,"process_exit_code":completed.returncode},"approval_rows":[],"event_rows":[],"ledger_path":str(env.ledger),"transactions_path":str(env.tx),"psp_path":str(env.psp)}


def execute(role):
    parent=TASK/"evidence"/("approval_"+role);parent.mkdir(parents=True,exist_ok=True)
    previous=[int(p.name.split("_")[-1]) for p in parent.glob("run_[0-9][0-9][0-9][0-9]") if p.is_dir()]
    run=parent/("run_"+str(max(previous,default=0)+1).zfill(4));run.mkdir()
    journal=parent/"CASE_ATTEMPTS.jsonl";result=[]
    scratch=ROOT/".task_envs/H62/runs";scratch.mkdir(parents=True,exist_ok=True)
    for case in CASES:
        reservations=[json.loads(s) for s in journal.read_text(encoding="utf-8").splitlines()] if journal.exists() else []
        assert len(reservations)<(72 if role=="executor" else 24),"case budget exhausted"
        entry={"id":uuid.uuid4().hex,"case":case,"run":run.name,"role":role}
        with journal.open("a",encoding="utf-8",newline="\n") as output:output.write(json.dumps(entry)+"\n");output.flush();os.fsync(output.fileno())
        folder=Path(tempfile.mkdtemp(prefix=case[:3]+"-",dir=scratch))
        save(run/(case+".input.json"),{"reservation":entry,"scratch":str(folder),"operator_context":CONTEXT,"clock":NOW})
        try:
            row=run_case(case,folder)
        except BaseException as exc:
            save(run/(case+".ERROR.json"),{"type":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc(),"scratch":str(folder)})
            raise
        save(run/(case+".json"),row);result.append(row)
    value={"schema":"h60-results/v1","cases":result,"business_execution_enabled":False,"new_payment_calls":0,"new_order_writes":0}
    save(run/"results.json",value);save(parent/"LATEST.json",{"run":run.name})
    print(json.dumps({"role":role,"cases":len(result),"run":run.name,"business_execution_enabled":False}))

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--role",choices=["executor","evaluator"]);parser.add_argument("--worker",action="store_true");parser.add_argument("--alias-worker",action="store_true");args=parser.parse_args()
    if args.alias_worker:alias_worker(json.loads(sys.stdin.read()))
    elif args.worker:worker(json.loads(sys.stdin.read()))
    else:execute(args.role)

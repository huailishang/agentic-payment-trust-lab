"""Evaluator freeze of existing inputs; no candidate implementation or approval."""
from pathlib import Path
import hashlib
import json
import sqlite3
import subprocess

TASK=Path(__file__).resolve().parent;ROOT=TASK.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=="__main__":
    assert not (TASK/"INPUTS.json").exists(),"Already frozen"
    prior=ROOT/"docs/05_任务交接/H58_MERCHANT_PAID_ORDER_GAP_MEASUREMENT_V1"
    h58=json.loads((prior/"INPUTS.json").read_text(encoding="utf-8"))
    obs=json.loads((ROOT/h58["observations"]).read_text(encoding="utf-8"));m06=obs["cases"][5]
    source={}
    for kind,key in (("transactions","transactions_db"),("psp","psp_db")):
        p=Path(m06["durable_storage"][key]).resolve();n=p.relative_to(ROOT).as_posix()
        assert sha(p)==h58["databases"][n] and not Path(str(p)+"-wal").exists()
        source[kind]={"path":n,"sha256":sha(p)}
    with sqlite3.connect(Path(m06["durable_storage"]["transactions_db"]).resolve().as_uri()+"?mode=ro&immutable=1",uri=True) as c:
        schema=[list(r) for r in c.execute("PRAGMA table_info(orders)")]
        assert {r[1] for r in schema}>={"id","data"}
    listed=[s.decode("utf-8") for s in subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard"],cwd=ROOT).split(b"\0") if s]
    protected={}
    for n in set(listed)|set(h58["protected_files"]):
        p=ROOT/n
        if p.is_file() and not p.is_relative_to(TASK) and n!="CURRENT.md":protected[n]=sha(p)
    for p in prior.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:protected[p.relative_to(ROOT).as_posix()]=sha(p)
    history=(ROOT/"CURRENT.md").read_text(encoding="utf-8").split("## Global position",1)[1]
    value={"schema":"h60-inputs/v1","head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"current_history_sha256":hashlib.sha256(history.encode()).hexdigest(),"checkout_id":m06["state"]["attempts"][0]["checkout_id"],"payment_ref":m06["state"]["attempts"][0]["payment_ref"],"source_databases":source,"protected_files":protected,"workspace_files":listed,"frozen_files":{p.name:sha(p) for p in TASK.iterdir() if p.is_file()}}
    (TASK/"INPUTS.json").write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"protected":len(protected),"frozen":len(value["frozen_files"]),"source_databases":2,"orders_schema":schema,"candidate_exists":(TASK/"APPROVAL_INBOX.py").exists(),"candidate_calls":0}))

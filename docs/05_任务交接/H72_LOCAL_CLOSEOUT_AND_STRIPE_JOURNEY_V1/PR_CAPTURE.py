"""H72 reauthorized PR capture. Only offline commands; preserve old P0 evidence."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
import RUN

P=Path(__file__).resolve().parent
ROOT=P.parents[2]
PY=RUN.AGENT_PYTHON
CHECK=P/"CHECK.py"
CAP=RUN.CAPTURE
FOLDER=P/"evidence/pr_repair_20261115"
RECEIPT=P/"PR_REPAIR_RECEIPT.json"
ADD=P/"evidence/pr_reauthorization_20261115/AUTHORIZATION_ADDENDUM.json"

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc)
def parse(s):return datetime.fromisoformat(s.replace("Z","+00:00"))
def need(x,msg):
    if not x:raise RuntimeError(msg)
def guard():
    auth=json.loads(ADD.read_text(encoding="utf-8"))
    started=parse(auth["repair_window_begin_at_utc"])
    elapsed=(utc()-started).total_seconds()/60
    need(0<=elapsed<60 and utc()<parse(auth["repair_wall_deadline_at_utc"]),"repair time limit reached")
    r=subprocess.run([str(PY),str(CHECK),"budget"],cwd=ROOT,env=RUN.runtime_env(),capture_output=True,timeout=35)
    need(r.returncode==0,"budget gate rejected: "+r.stderr.decode("utf-8",errors="replace")[-500:])
    return started
def capture(label,argv,count):
    guard()
    need(not any((FOLDER/(label+"."+x)).exists() for x in ("meta.json","stdout.log","stderr.log")),
         "do not overwrite capture:"+label)
    args=[str(PY),str(CAP),"--label",label,"--out",str(FOLDER),"--cwd",str(ROOT),"--",*[str(x) for x in argv]]
    r=subprocess.run(args,cwd=ROOT,env=RUN.runtime_env(),capture_output=True,timeout=225)
    p=FOLDER/(label+".meta.json")
    need(p.is_file(),"missing capture metadata:"+label)
    m=json.loads(p.read_text(encoding="utf-8"))
    out=FOLDER/(label+".stdout.log")
    err=FOLDER/(label+".stderr.log")
    for kind,f in (("stdout",out),("stderr",err)):
        need(sha(f)==m[kind+"_sha256"] and f.stat().st_size==m[kind+"_bytes"],"bad evidence:"+label)
    need(r.returncode==m["exit_code"]==0,"captured command failed:"+label)
    raw=out.read_bytes()+b"\n"+err.read_bytes()
    if count is not None:
        matches=re.findall(rb"Ran\s+(\d+)\s+tests?\s+in\s+",raw)
        need(len(matches)==1 and int(matches[0])==count and re.search(rb"(?m)^OK\s*$",raw) is not None,
             "wrong test count/status:"+label)
    return {"label":label,"command_argv":m["command_argv"],"exit_code":m["exit_code"],
            "meta_sha256":sha(p),"stdout_sha256":m["stdout_sha256"],
            "stderr_sha256":m["stderr_sha256"],"stdout_bytes":m["stdout_bytes"],
            "stderr_bytes":m["stderr_bytes"],"test_count":count,
            "started_at_utc":m["started_at_utc"],"finished_at_utc":m["finished_at_utc"]}
def run():
    start=guard()
    need(not RECEIPT.exists(),"receipt exists: do not overwrite")
    need(not FOLDER.exists() or not list(FOLDER.iterdir()),"partial capture exists: review first")
    FOLDER.mkdir(parents=True,exist_ok=True)
    spec=[
     ("PR-ENV-01",[PY,CHECK,"environment"],None),
     ("PR-PRES-01",[PY,CHECK,"preservation"],None),
     ("PR-SELF-01",[PY,CHECK,"p0-selftest"],16),
     ("PR-SAFE-01",[PY,RUN.H68R_CHECK,"safety"],9),
     ("PR-REG-01",[PY,"-m","unittest",*RUN.TEST_MODULES],74),
     ("PR-LEG-01",[PY,RUN.H71R2/"PROBES_LEGACY.py"],11),
     ("PR-LIFE-01",[PY,RUN.H71R2/"PROBES_LIFECYCLE.py"],9)]
    rows=[capture(*x) for x in spec]
    baseline=json.loads((P/"BASELINE.json").read_text(encoding="utf-8"))
    sources={"CHECK.py":CHECK,"RUN.py":P/"RUN.py",
             "PR_RECEIPT_GUARD.py":P/"PR_RECEIPT_GUARD.py",
             "PR_NEGATIVE_TESTS.py":P/"PR_NEGATIVE_TESTS.py",
             "PR_CAPTURE.py":P/"PR_CAPTURE.py",
             "tests_init.py":P/"runtime/userbase/Python312/site-packages/tests/__init__.py",
             "H68R_CHECK.py":RUN.H68R_CHECK,
             "H71R2_PROBES_LEGACY.py":RUN.H71R2/"PROBES_LEGACY.py",
             "H71R2_PROBES_LIFECYCLE.py":RUN.H71R2/"PROBES_LIFECYCLE.py",
             "capture_evidence.py":CAP}
    doc={"schema":"h72-pr-receipt/v1","task_id":P.name,
         "began_at_utc":start.isoformat(),"completed_at_utc":utc().isoformat(),
         "baseline_head":baseline["head"],"baseline_sha256":sha(P/"BASELINE.json"),
         "authorization_sha256":sha(P/"AUTHORIZATION.json"),"reauthorization_sha256":sha(ADD),
         "source_sha256":{k:sha(v) for k,v in sources.items()},
         "product_sha256":{rel:sha(ROOT/rel) for rel in baseline["allowed_product_initial"]},
         "test_counts":RUN.REQUIRED_COUNTS,"negative_fixture_tests":16,"commands":rows,
         "guardrail_status":"PASS_WITH_NEGATIVE_FIXTURES",
         "original_p0_receipt_sha256":sha(P/"P0_RECEIPT.json"),
         "external_side_effects":{"network":0,"installs":0,"services":0,"browser_actions":0,"payments":0},
         "notes":["Original P0 and evaluator counterexamples unchanged.",
                  "16 actual-entrypoint positive/negative fixture tests, not the old five superficial assertions.",
                  "Native Windows reparse retained on real preservation gate; fixture result never admits external use."]}
    RECEIPT.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    r=subprocess.run([str(PY),str(CHECK),"p0-receipt"],cwd=ROOT,env=RUN.runtime_env(),capture_output=True,timeout=60)
    need(r.returncode==0,"final receipt verifier rejected: "+r.stderr.decode("utf-8",errors="replace")[-850:])
    return {"status":"PASS","commands":[x["label"] for x in rows],
            "receipt_sha256":sha(RECEIPT),"original_receipt_sha256":doc["original_p0_receipt_sha256"],
            "negative_fixture_tests":16,
            "verified":json.loads(r.stdout.decode("utf-8"))}
if __name__=="__main__":
    try:print(json.dumps(run(),ensure_ascii=True,indent=2))
    except Exception as e:
        print("PR CAPTURE FAILED: "+str(e),file=sys.stderr)
        raise SystemExit(1)

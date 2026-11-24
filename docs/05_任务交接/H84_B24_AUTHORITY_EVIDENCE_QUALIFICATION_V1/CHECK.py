"""H84 preparation, frozen task validation and one-use role dispatch."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
import MEASURE as M

TASK=M.TASK
ROOT=M.ROOT
H78=TASK.parent/"H78_FRESH_SPIRE_UID_POSSESSION_CLOSURE_V1"
H83=M.H83

def git(*args):
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()

def snapshot():
    names=git("ls-files","--cached","--others","--exclude-standard","--","src","tests","samples","scripts").splitlines()
    # Git quotes non-ASCII paths by default; use NUL-delimited names instead.
    names=subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard","--","src","tests","samples","scripts"],cwd=ROOT).decode().split("\0")
    files={n:M.digest(ROOT/n) for n in sorted(set(names)-{""}) if (ROOT/n).is_file()}
    for p in (H78/"WORKLOAD.py",H78/"BINARY_MEMBER_LOCK.json",H78/"REVIEW.md",H83/"CHECK.py",H83/"SOURCE_LOCK.json",H83/"REVIEW.md",ROOT/"docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"):
        files[p.relative_to(ROOT).as_posix()]=M.digest(p)
    for rel,sha in M.read(H83/"SOURCE_LOCK.json")["protected_sha256"].items():
        p=ROOT/rel
        M.need(M.digest(p)==sha,"H83 original source drift "+rel)
        files[rel]=sha
    return files

def freeze():
    M.need(git("rev-parse","HEAD")==M.BASELINE,"baseline drift")
    frozen={p.relative_to(ROOT).as_posix():M.digest(p) for p in [TASK/n for n in ("CONTRACT.md","VALIDATION_PLAN.yaml","AUTHORIZATION.json","PREPARE.py","WORKLOAD.py","BINARY_MEMBER_LOCK.json","MEASURE.py","CHECK.py","evidence/preparation/S0_ASSET_PREFLIGHT.json")]}
    data={"task_id":TASK.name,"baseline_head":M.BASELINE,"frozen_sha256":frozen,"protected_sha256":snapshot()}
    with (TASK/"FREEZE.json").open("x",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
    print("FROZEN",len(frozen),len(data["protected_sha256"]))

def preservation():
    lock=M.read(TASK/"FREEZE.json")
    M.need(git("rev-parse","HEAD")==M.BASELINE,"baseline drift")
    M.need(snapshot()==lock["protected_sha256"],"product or history changed")
    for rel,sha in lock["frozen_sha256"].items():
        M.need(M.digest(ROOT/rel)==sha,"frozen file drift "+rel)
    print("PRESERVATION PASS",len(lock["protected_sha256"]))

def offline():
    spec=importlib.util.spec_from_file_location("h84_h83_baseline",H83/"CHECK.py")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fact=module.proof()
    at=fact.observed_at_epoch
    case,values=M.fixture(fact)
    with tempfile.TemporaryDirectory(prefix="h84offline_") as tmp:
        path=Path(tmp)
        a=M.observe(case,values,fact,at,"h84-offline-before","VERIFIED",path/"a.json")
        b=M.observe(case,values,None,at+1,"h84-offline-after","BOUND",path/"b.json")
        M.need(a["order_digest"]==b["order_digest"],"different order")
        print(json.dumps({"kind":"historical_fixture_only","before":a,"after":b},ensure_ascii=False))
    # No new credential, no source transition in this offline check.

def regressions():
    suites={"tests":["test_webshop_runtime_gate.py"],"tests/trusted_execution":["test_credential_possession.py","test_credential_context_consumption.py","test_identity_assurance.py","test_payment_binding.py","test_signed_instruction_es256.py"]}
    total=0
    for directory,patterns in suites.items():
        for pattern in patterns:
            result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/directory),pattern=pattern))
            M.need(result.wasSuccessful() and not result.skipped and result.testsRun>0,"regression failure "+pattern)
            total+=result.testsRun
    M.need(total==86,"expected original 86 regressions")
    print("REGRESSIONS PASS",total,"skipped=0")

def live(role):
    preservation()
    import yaml
    route=yaml.safe_load((ROOT/"CURRENT.md").read_text(encoding="utf-8").split("```yaml",1)[1].split("```",1)[0])
    expected=("EXECUTING","Executor") if role=="executor" else ("READY_FOR_REVIEW","Evaluator")
    M.need((route["state"],route["current_role"])==expected and route["task_id"]==TASK.name,"role not routed")
    # This one-use marker survives any timeout or connection loss. No restart.
    run_id,nonce=uuid.uuid4().hex,uuid.uuid4().hex
    marker=TASK/"evidence"/(role+"_ATTEMPT.json")
    with marker.open("x",encoding="utf-8") as f:
        json.dump({"run_id":run_id,"nonce":nonce,"budget_consumed":1,"begin_epoch":int(time.time())},f)
        f.flush()
        os.fsync(f.fileno())
    out=TASK/"evidence"/(role+"_runs")/run_id
    out.mkdir(parents=True,exist_ok=False)
    cmd=[sys.executable,"-B",str(TASK/"WORKLOAD.py"),"issuer","--run-id",run_id,"--nonce",nonce,"--out",str(out)]
    code=subprocess.run(cmd,env=os.environ|{"H84_ROLE":role}).returncode
    M.need(code==0,"collector failed; preserve raw evidence and stop")
    data=M.read(out/"RESULT.json")
    cleanup=M.read(out/"CLEANUP.json")
    M.need(data["status"]=="H84_TRANSITION_OBSERVED","source status unknown")
    M.need(cleanup["owned_processes_alive"]==[] and cleanup["private_tmpfs_exists"] is False and cleanup["public_private_key_files"]==0 and cleanup["independent_check_exit_code"]==0,"cleanup not proven")
    for rel,sha in M.read(out/"PUBLIC_INDEX.json")["files"].items():
        M.need(M.digest(out/rel)==sha,"public index drift "+rel)
    preservation()
    print(json.dumps({"role":role,"run_id":run_id,"before":data["before"],"after":data["after"],"cleanup":cleanup},ensure_ascii=False))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("check",choices=("offline","regressions","freeze","preservation","live"))
    p.add_argument("--role",choices=("executor","evaluator"),default="executor")
    a=p.parse_args()
    live(a.role) if a.check=="live" else globals()[a.check]()

if __name__=="__main__":
    main()

"""Evaluator preparation only. Freeze existing inputs, never synthesize business evidence."""
from pathlib import Path
import hashlib
import json
import subprocess

TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

if __name__=="__main__":
    assert not (TASK/"INPUTS.json").exists(), "Already frozen; do not regenerate"
    parent=ROOT/"docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1"
    observations=parent/"evidence/evaluator/run_0002/observations.json"
    value=json.loads(observations.read_text(encoding="utf-8"))
    m06=value["cases"][-1]
    dbs={}
    for k in ("transactions_db","psp_db"):
        p=Path(m06["durable_storage"][k]).resolve()
        assert p.is_relative_to((ROOT/".task_envs/H57/runs").resolve())
        wal=Path(str(p)+"-wal")
        assert not wal.exists() or wal.stat().st_size==0, str(wal)
        dbs[p.relative_to(ROOT).as_posix()]=sha(p)
    files=subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard"],cwd=ROOT).split(b"\0")
    protected={}
    for raw in files:
        if not raw:
            continue
        n=raw.decode("utf-8")
        p=ROOT/n
        if n=="CURRENT.md" or p.is_relative_to(TASK) or not p.is_file():
            continue
        protected[n]=sha(p)
    frozen={p.relative_to(TASK).as_posix():sha(p) for p in TASK.iterdir() if p.is_file()}
    data={"schema":"h58-inputs/v1","head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"map_revision":"2026-11-02-r95","observations":observations.relative_to(ROOT).as_posix(),"databases":dbs,"protected_files":protected,"frozen_files":frozen}
    (TASK/"INPUTS.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"protected_files":len(protected),"frozen_files":len(frozen),"databases":len(dbs),"merchant_calls":0,"measurement_implementation_exists":(TASK/"MEASURE.py").exists()}))

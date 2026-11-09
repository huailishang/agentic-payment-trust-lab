"""Frozen durable reservation wrapper for the only permitted extractor call."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def main():
    p=argparse.ArgumentParser();p.add_argument("--role",choices=["executor","evaluator"],required=True);role=p.parse_args().role
    folder=TASK/"evidence"/role;folder.mkdir(parents=True,exist_ok=True)
    journal=folder/"EXTRACTION_ATTEMPTS.jsonl"
    attempts=journal.read_text(encoding="utf-8").splitlines() if journal.exists() else []
    assert len(attempts)<(4 if role=="executor" else 2),"extractor budget exhausted"
    previous=[int(p.name.split("_")[-1]) for p in folder.glob("run_[0-9][0-9][0-9][0-9]") if p.is_dir()]
    run=folder/("run_"+str(max(previous,default=0)+1).zfill(4));run.mkdir()
    entry={"id":uuid.uuid4().hex,"role":role,"run":run.name}
    with journal.open("a",encoding="utf-8",newline="\n") as f:f.write(json.dumps(entry)+"\n");f.flush();os.fsync(f.fileno())
    try:
        result=subprocess.run([sys.executable,"-B",str(TASK/"EXTRACT.py"),"--out",str(run/"EXTRACTION.json")],cwd=ROOT,capture_output=True,timeout=60)
        (run/"extractor.stdout.log").write_bytes(result.stdout);(run/"extractor.stderr.log").write_bytes(result.stderr)
        save(run/"PROCESS.json",{"exit_code":result.returncode,"reservation":entry})
        assert result.returncode==0,"extractor failed; raw output preserved"
        assert (run/"EXTRACTION.json").is_file()
        save(folder/"LATEST.json",{"run":run.name});print(json.dumps({"role":role,"run":run.name,"extraction_attempts":len(attempts)+1}))
    finally:
        path=TASK/"ATTEMPT_LEDGER.json"
        if role=="executor" and path.exists():
            value=read(path);value["extraction_attempts"]=len(journal.read_text(encoding="utf-8").splitlines());value["formal_l2_attempts"]=len(list((TASK/"evidence").glob("l2_executor_*")));save(path,value)
if __name__=="__main__":main()

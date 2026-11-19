"""Evaluator-only preservation/freezing. Never performs runtime operations."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

PACK=Path(__file__).resolve().parent
ROOT=PACK.parents[2]
H70=PACK.parent/"H70_STRIPE_ANONYMOUS_PERMISSION_APPLICABILITY_V1"

def sha(raw): return hashlib.sha256(raw).hexdigest()

def copy_once(src,dst):
    raw=src.read_bytes(); dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists(): assert dst.read_bytes()==raw
    else: dst.write_bytes(raw)
    return sha(raw)

def preserve():
    need_absent=not any((H70/n).exists() for n in ("RUN.py","REPORT.md","RESULT.json","ATTEMPT_LEDGER.jsonl"))
    assert need_absent,"H70_execution_detected_do_not_supersede"
    refs=PACK/"references"
    hashes={}
    for name in ("CURRENT.md","REMOTE_HANDOFF.md","AGENTS.md"):
        hashes[name]=copy_once(ROOT/name,refs/("PRIOR_"+name))
    src=ROOT/"docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"
    hashes["map_r114"]=copy_once(src,refs/"PROJECT_BOTTLENECK_MAP_r114.md")
    copy_once(src,src.parent/"archive/PROJECT_BOTTLENECK_MAP_20261112_r114.md")
    copy_once(H70/"CHECK.py",PACK/"SOURCE_CHECK.py")
    old={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in H70.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    (refs/"SUPERSESSION.json").write_text(json.dumps({"reason":"Human requested a longer bounded multi-step task and unified review before H70 execution", "old_task":"H70_STRIPE_ANONYMOUS_PERMISSION_APPLICABILITY_V1","old_execution":"NOT_EXECUTED","verdict":"NOT_ISSUED","prior_governance":hashes,"old_files":old},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Preserved H70 unexecuted package, prior governance and exact r114 bytes")

def freeze():
    assert not (PACK/"BASELINE.json").exists(),"baseline_already_frozen"
    old=json.loads((H70/"BASELINE.json").read_text(encoding="utf-8"))
    files=set(old["protected"])
    for args in (["git","ls-files","-z"],["git","ls-files","--others","--exclude-standard","-z"]):
        files.update(x.decode("utf-8") for x in subprocess.run(args,cwd=ROOT,capture_output=True,check=True).stdout.split(b"\0") if x)
    files.update(p.relative_to(ROOT).as_posix() for p in H70.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    for name in ("capture_evidence.py","run_validation.py","validate_workflow.py"):
        files.add("../localagent-common/skills/evaluator-executor-workflow/scripts/"+name)
    protected={}
    for rel in sorted(files):
        p=ROOT/rel
        if p.is_file() and not p.resolve().is_relative_to(PACK) and rel!="CURRENT.md": protected[rel]=sha(p.read_bytes())
    frozen_names=["CONTRACT.md","SPEC.json","AUTHORIZATION.json","SOURCE_LOCK.json","SCHEMA_GUIDE.md","CHECK.py","CHECK_SELFTEST.py","SOURCE_CHECK.py","VALIDATION_PLAN.yaml","PREPARE.py"]
    frozen_names += sorted(p.relative_to(PACK).as_posix() for p in (PACK/"references").rglob("*") if p.is_file())
    untracked=subprocess.run(["git","ls-files","--others","--exclude-standard","-z"],cwd=ROOT,capture_output=True,check=True).stdout
    b={"schema":"h71-preservation-baseline/v1","head":subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip(),"protected":protected,"frozen":{n:sha((PACK/n).read_bytes()) for n in frozen_names},"inherited_untracked":[x.decode("utf-8") for x in untracked.split(b"\0") if x and not x.decode("utf-8").startswith(PACK.relative_to(ROOT).as_posix()+"/")]}
    (PACK/"BASELINE.json").write_text(json.dumps(b,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Frozen H71:",len(protected),"protected files;",len(frozen_names),"frozen inputs")

if __name__=="__main__": {"preserve":preserve,"freeze":freeze}[sys.argv[1]]()

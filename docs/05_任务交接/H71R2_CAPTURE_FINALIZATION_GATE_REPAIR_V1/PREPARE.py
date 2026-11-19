"""Evaluator-only preservation/freezing. Never normalizes invalid old gate data."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

PACK=Path(__file__).resolve().parent
ROOT=PACK.parents[2]
OLD=PACK.parent/"H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1"
def sha(raw): return hashlib.sha256(raw).hexdigest()
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def copy_once(src,dst):
    raw=src.read_bytes(); dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists(): assert dst.read_bytes()==raw
    else: dst.write_bytes(raw)
    return sha(raw)

def prior():
    assert not (PACK/"INPUT_SEAL.json").exists()
    refs=PACK/"references"; old={}
    for name in ("CURRENT.md","REMOTE_HANDOFF.md"):
        old[name]=copy_once(ROOT/name,refs/("PRIOR_"+name))
    source=ROOT/"docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"
    old["map_r116"]=copy_once(source,refs/"PROJECT_BOTTLENECK_MAP_r116.md")
    copy_once(source,source.parent/"archive/PROJECT_BOTTLENECK_MAP_20261112_r116.md")
    copy_once(OLD/"CHECK.py",PACK/"BASE_CHECK.py")
    copy_once(OLD/"CHECK_PROBES.py",PACK/"PROBES_LEGACY.py")
    passed={}
    for name in ("EVIDENCE_CORRECTION.json","CORRECTED_MATRIX.json","EVIDENCE_GOLD.json"):
        passed[(OLD/name).relative_to(ROOT).as_posix()]=sha((OLD/name).read_bytes())
    seal={"schema":"h71r2-preserved-input-seal/v1","parent_failed_ac":["AC-04","AC-05"],"previous_h71r_verdict":"REJECTED",
        "passed_projection_files":passed,"correction_sha256":sha((OLD/"EVIDENCE_CORRECTION.json").read_bytes()),"matrix_sha256":sha((OLD/"CORRECTED_MATRIX.json").read_bytes()),
        "old_implementation_sha256":sha((OLD/"RUN.py").read_bytes()),"old_candidate_snapshot_sha256":sha((OLD/"evidence/l3_review/ACCEPTED_SNAPSHOT.json").read_bytes()),
        "snapshot_classification_sha256":sha((OLD/"evidence/l3_review/SNAPSHOT_CLASSIFICATION.json").read_bytes()),"prior_governance":old}
    (PACK/"INPUT_SEAL.json").write_text(json.dumps(seal,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Preserved r116 and passed projection bytes; copied frozen legacy probes/protection checks")

def rejected():
    copy_once(ROOT/"CURRENT.md",PACK/"references/CURRENT_H71R_REJECTED.md")
    print("Preserved H71R rejected route; invalid L2 remains invalid")

def freeze():
    assert not (PACK/"BASELINE.json").exists()
    files=set(load(OLD/"BASELINE.json")["protected"])
    for args in (["git","ls-files","-z"],["git","ls-files","--others","--exclude-standard","-z"]):
        files.update(x.decode("utf-8") for x in subprocess.run(args,cwd=ROOT,capture_output=True,check=True).stdout.split(b"\0") if x)
    files.update(p.relative_to(ROOT).as_posix() for p in OLD.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    protected={}
    for rel in sorted(files):
        path=ROOT/rel
        if path.is_file() and rel!="CURRENT.md" and not path.resolve().is_relative_to(PACK): protected[rel]=sha(path.read_bytes())
    names=["CONTRACT.md","SCHEMA_GUIDE.md","VALIDATION_PLAN.yaml","CHECK.py","BASE_CHECK.py","PROBES_LEGACY.py","PROBES_LIFECYCLE.py","INPUT_SEAL.json","PREPARE.py"]
    names+=sorted(p.relative_to(PACK).as_posix() for p in (PACK/"references").rglob("*") if p.is_file())
    raw=subprocess.run(["git","ls-files","--others","--exclude-standard","-z"],cwd=ROOT,capture_output=True,check=True).stdout
    baseline={"schema":"h71r2-preservation-baseline/v1","head":subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip(),
        "protected":protected,"frozen":{name:sha((PACK/name).read_bytes()) for name in names},"inherited_untracked":[x.decode("utf-8") for x in raw.split(b"\0") if x and not x.decode("utf-8").startswith(PACK.relative_to(ROOT).as_posix()+"/")]}
    (PACK/"BASELINE.json").write_text(json.dumps(baseline,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Frozen H71R2:",len(protected),"protected files;",len(names),"frozen inputs")

if __name__=="__main__": {"prior":prior,"rejected":rejected,"freeze":freeze}[sys.argv[1]]()

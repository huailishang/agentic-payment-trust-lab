"""Evaluator preservation and baseline preparation. No external operations."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

PACK=Path(__file__).resolve().parent
ROOT=PACK.parents[2]
OLD=PACK.parent/"H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1"
AUDIT=OLD/"evidence/l3_review"

def sha(raw): return hashlib.sha256(raw).hexdigest()
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def copy_once(src,dst):
    raw=src.read_bytes(); dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists(): assert dst.read_bytes()==raw
    else: dst.write_bytes(raw)
    return sha(raw)

def prior():
    assert not (PACK/"EVIDENCE_GOLD.json").exists()
    refs=PACK/"references"; digests={}
    for name in ("CURRENT.md","REMOTE_HANDOFF.md"):
        digests[name]=copy_once(ROOT/name,refs/("PRIOR_"+name))
    source=ROOT/"docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"
    digests["map_r115"]=copy_once(source,refs/"PROJECT_BOTTLENECK_MAP_r115.md")
    copy_once(source,source.parent/"archive/PROJECT_BOTTLENECK_MAP_20261112_r115.md")
    result=load(OLD/"RESULT.json"); raw=load(AUDIT/"RAW_AUDIT.json")
    gets=[{"url":x["url"],"status":x["status"],"body_sha256":x["body_sha256"],"empty":True,"has_more":False} for x in raw["three_gets"]]
    sources={x["id"]:{"repo_file":(OLD/x["file"]).relative_to(ROOT).as_posix(),"url":x["url"],"sha256":x["sha256"]} for x in load(OLD/"SOURCE_MANIFEST.json")["sources"]}
    gold={"schema":"h71r-preserved-evidence-gold/v1","snapshot_sha256":result["private_snapshot_sha256"],"gets":gets,
        "failed_source_attempts":["h71-source-sandbox_source","h71-source-cli_root_source"],
        "matrix_ids":["account_read","checkout_required_endpoints","test_listener","same_environment_binding"],
        "sources":sources,"source_read_limit_per_failure":2097153,"download_read_limit":67108865,
        "historical_received_bytes":"UNKNOWN; must not backfill synthetic counterexample values",
        "prior_governance":digests}
    (PACK/"EVIDENCE_GOLD.json").write_text(json.dumps(gold,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Preserved r115 and prior route; froze 3 real GET observations and 2 archived sources")

def rejected():
    copy_once(ROOT/"CURRENT.md",PACK/"references/CURRENT_H71_REJECTED.md")
    print("Preserved H71 rejection routing snapshot")

def freeze():
    assert not (PACK/"BASELINE.json").exists()
    previous=load(OLD/"BASELINE.json"); files=set(previous["protected"])
    for args in (["git","ls-files","-z"],["git","ls-files","--others","--exclude-standard","-z"]):
        files.update(x.decode("utf-8") for x in subprocess.run(args,cwd=ROOT,capture_output=True,check=True).stdout.split(b"\0") if x)
    files.update(p.relative_to(ROOT).as_posix() for p in OLD.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    protected={}
    for rel in sorted(files):
        p=ROOT/rel
        if p.is_file() and not p.resolve().is_relative_to(PACK) and rel!="CURRENT.md": protected[rel]=sha(p.read_bytes())
    names=["CONTRACT.md","SCHEMA_GUIDE.md","VALIDATION_PLAN.yaml","CHECK.py","CHECK_PROBES.py","EVIDENCE_GOLD.json","PREPARE.py"]
    names+=sorted(p.relative_to(PACK).as_posix() for p in (PACK/"references").rglob("*") if p.is_file())
    untracked=subprocess.run(["git","ls-files","--others","--exclude-standard","-z"],cwd=ROOT,capture_output=True,check=True).stdout
    baseline={"schema":"h71r-repair-baseline/v1","head":subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip(),
        "protected":protected,"frozen":{n:sha((PACK/n).read_bytes()) for n in names},
        "inherited_untracked":[x.decode("utf-8") for x in untracked.split(b"\0") if x and not x.decode("utf-8").startswith(PACK.relative_to(ROOT).as_posix()+"/")]}
    (PACK/"BASELINE.json").write_text(json.dumps(baseline,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Frozen H71R:",len(protected),"protected files;",len(names),"frozen inputs")

if __name__=="__main__": {"prior":prior,"rejected":rejected,"freeze":freeze}[sys.argv[1]]()

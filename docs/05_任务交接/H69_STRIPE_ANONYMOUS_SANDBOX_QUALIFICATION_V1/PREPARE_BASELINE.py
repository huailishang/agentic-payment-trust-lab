"""Evaluator-only, write-once H69 baseline; no service calls."""
import hashlib
import json
from pathlib import Path
import subprocess

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
GOVERNANCE = ["CURRENT.md","REMOTE_HANDOFF.md","docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def files(*args):
    raw = subprocess.run(["git","ls-files","-z",*args],cwd=ROOT,capture_output=True,check=True).stdout
    return sorted(x.decode("utf-8") for x in raw.split(b"\0") if x)

if __name__ == "__main__":
    tracked = set(files())-set(GOVERNANCE)
    prefix = PACK.relative_to(ROOT).as_posix()+"/"
    inherited = [p for p in files("--others","--exclude-standard") if not p.startswith(prefix)]
    protected = tracked | (set(inherited)-set(GOVERNANCE))
    for name in ("H68_STRIPE_CHECKOUT_SANDBOX_JOURNEY_V1", "H68R_STRIPE_CHECKOUT_LOCAL_TRUST_REPAIR_V1"):
        protected.update(p.relative_to(ROOT).as_posix() for p in (PACK.parent/name).rglob("*")
                         if p.is_file() and "__pycache__" not in p.parts)
    frozen = ["CONTRACT.md","SPEC.json","AUTHORIZATION.json","SOURCE_LOCK.json","CHECK.py",
              "SCHEMA_GUIDE.md","VALIDATION_PLAN.yaml","PREPARE_BASELINE.py"]
    frozen += sorted(p.relative_to(PACK).as_posix() for p in (PACK/"references").rglob("*") if p.is_file())
    shared = ["../localagent-common/skills/evaluator-executor-workflow/scripts/"+p
              for p in ("validate_workflow.py","run_validation.py","capture_evidence.py")]
    value = {"head":subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip(),
             "governance":GOVERNANCE,"tracked_files":sorted(tracked),"inherited_untracked":inherited,
             "protected":{p:sha(ROOT/p) for p in sorted(protected)},
             "package_files":{p:sha(PACK/p) for p in frozen},"shared_tools":{p:sha(ROOT/p) for p in shared}}
    with (PACK/"BASELINE.json").open("x",encoding="utf-8") as out:
        json.dump(value,out,ensure_ascii=True,indent=2)
        out.write("\n")
    print(json.dumps({"protected_files":len(protected),"tracked_files":len(tracked)}))

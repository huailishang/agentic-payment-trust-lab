"""Evaluator preparation utility: prints candidate hashes, never grants authority."""
import hashlib
import json
from pathlib import Path
import subprocess

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git_paths(root, *args):
    result = subprocess.run(["git",*args,"-z"],cwd=root,capture_output=True,check=True)
    return [x.decode("utf-8") for x in result.stdout.split(b"\0") if x]


def tracked_tree(root, excluded):
    paths = sorted(p for p in git_paths(root,"ls-files","--cached") if p not in excluded)
    stream = hashlib.sha256()
    for rel in paths:
        stream.update(rel.encode()+b"\0"+sha((root/rel).read_bytes()).encode()+b"\n")
    return len(paths),stream.hexdigest()


def candidate():
    spec = json.loads((PACK/"SPEC.json").read_text(encoding="utf-8"))
    governance = ["CURRENT.md","REMOTE_HANDOFF.md","docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"]
    new_product = spec["new_product_files"]
    count,tree_sha = tracked_tree(ROOT,set(governance)|set(new_product))
    prefix = PACK.relative_to(ROOT).as_posix()+"/"
    inherited = [p for p in git_paths(ROOT,"ls-files","--others","--exclude-standard") if not p.startswith(prefix)]
    package_files = {}
    for path in sorted(PACK.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(PACK).as_posix()
        if rel == "INPUTS.json" or rel.startswith(("derived/","versions/","evidence/")):
            continue
        package_files[rel] = sha(path.read_bytes())
    head = subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    common = "../localagent-common/skills/evaluator-executor-workflow/scripts/"
    shared = {common+name:sha((ROOT/common/name).read_bytes()) for name in ("validate_workflow.py","run_validation.py","capture_evidence.py")}
    return {"schema":"h68-frozen-inputs/v1","task_id":PACK.name,"baseline_head":head,"governance_files":governance,"new_product_files":new_product,"protected_tracked_count":count,"protected_tracked_tree_sha256":tree_sha,"inherited_untracked":sorted(inherited),"protected_files":{p:sha((ROOT/p).read_bytes()) for p in sorted(inherited)},"shared_tools":shared,"package_files":package_files,"notice":"DRAFT candidate; only Evaluator may re-freeze after explicit authority, preserving prior bytes. No runtime verdict."}


if __name__ == "__main__":
    # ASCII transport prevents Windows console encodings from corrupting CJK paths.
    print(json.dumps(candidate(),ensure_ascii=True,sort_keys=True,indent=2))

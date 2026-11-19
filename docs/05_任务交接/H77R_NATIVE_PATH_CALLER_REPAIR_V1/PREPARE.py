"""Evaluator preparation only: preserve rejected package, copy exact implementation, seal."""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import yaml

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
OLD = P.parent / "H77_WSL_REAL_SOURCE_INDEPENDENT_CLOSURE_V1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def prepare():
    refs = P / "references/before_repair"
    refs.mkdir(parents=True, exist_ok=False)
    for name, path in (("CURRENT_H77_REJECTED.md", ROOT / "CURRENT.md"), ("REMOTE_HANDOFF.md", ROOT / "REMOTE_HANDOFF.md"), ("PROJECT_BOTTLENECK_MAP_r129.md", ROOT / "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md")):
        (refs / name).write_bytes(path.read_bytes())
    archive = ROOT / "docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261116_r129.md"
    with archive.open("xb") as stream:
        stream.write((refs / "PROJECT_BOTTLENECK_MAP_r129.md").read_bytes())
    copied = {}
    for name in ("AUDIT.py", "CHECK.py", "BOOTSTRAP.py", "RUN.py", "WORKLOAD.py", "TASK_TESTS.py"):
        raw = (OLD / name).read_bytes()
        if name == "CHECK.py":
            before = b'str(out.relative_to(ROOT))]'
            after = b'out.relative_to(ROOT).as_posix()]'
            if raw.count(before) != 1:
                raise ValueError("principal change no longer exact")
            changed = raw.replace(before, after)
        else:
            changed = raw
        with (P / name).open("xb") as stream:
            stream.write(changed)
        copied[name] = {"source": (OLD / name).relative_to(ROOT).as_posix(), "source_sha256": sha(OLD / name), "new_sha256": sha(P / name), "change": "one caller --out expression .as_posix()" if name == "CHECK.py" else "BYTE_IDENTICAL"}
    save(P / "COPY_MANIFEST.json", {"schema": "h77r-copy/v1", "files": copied})
    prep = P / "evidence/preparation"
    prep.mkdir(parents=True, exist_ok=True)
    (prep / "H76_INPUT_SEAL.json").write_bytes((OLD / "evidence/preparation/H76_INPUT_SEAL.json").read_bytes())
    plan = yaml.safe_load((OLD / "VALIDATION_PLAN.yaml").read_text(encoding="utf-8").replace(OLD.name, P.name))
    plan["checks"][1]["command"] = ["python", "-B", (P / "SEAM_CHECK.py").relative_to(ROOT).as_posix()]
    with (P / "VALIDATION_PLAN.yaml").open("x", encoding="utf-8") as stream:
        yaml.safe_dump(plan, stream, allow_unicode=True, sort_keys=False)
    command = [sys.executable, "-B", str(ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py"), "--repo", str(ROOT), "--current", "CURRENT.md"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True)
    (prep / "parent_final_workflow.stdout.log").write_bytes(result.stdout)
    (prep / "parent_final_workflow.stderr.log").write_bytes(result.stderr)
    if result.returncode:
        raise ValueError("parent terminal route invalid")
    save(prep / "PARENT_PRESERVATION.json", {"files": {f.relative_to(ROOT).as_posix(): sha(f) for f in OLD.rglob("*") if f.is_file() and "runtime" not in f.relative_to(OLD).parts and "__pycache__" not in f.parts}, "original_accepted_count": 1693, "parent_l3": "FAIL", "actual_spire_starts": 0, "old_l3_not_retried": True})
    print(json.dumps({"copied_files": len(copied), "principal_changes": 1, "parent_final_validator": result.returncode}))


def seal():
    refs = P / "references/before_repair"
    alias = {"docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md": refs / "PROJECT_BOTTLENECK_MAP_r129.md", "REMOTE_HANDOFF.md": refs / "REMOTE_HANDOFF.md"}
    protected = {}
    for rel, digest in read(OLD / "evidence/ACCEPTED.json")["files"].items():
        path = alias.get(rel, ROOT / rel)
        if sha(path) != digest:
            raise ValueError("parent accepted input drift: " + rel)
        protected[path.relative_to(ROOT).as_posix()] = digest
    for directory in (OLD, refs, P / "evidence/preparation"):
        for path in directory.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and "runtime" not in path.relative_to(directory).parts:
                protected[path.relative_to(ROOT).as_posix()] = sha(path)
    for path in (ROOT / "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md", ROOT / "REMOTE_HANDOFF.md", ROOT / "docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261116_r129.md"):
        protected[path.relative_to(ROOT).as_posix()] = sha(path)
    save(P / "BASELINE.json", {"head": read(OLD / "BASELINE.json")["head"], "protected": protected, "common_protected": read(OLD / "BASELINE.json")["common_protected"], "parent": OLD.name, "governance_aliases": {rel: path.relative_to(ROOT).as_posix() for rel, path in alias.items()}, "created_utc": datetime.now(timezone.utc).isoformat()})
    names = ("CONTRACT.md", "VALIDATION_PLAN.yaml", "COPY_MANIFEST.json", "CHECK.py", "AUDIT.py", "BOOTSTRAP.py", "RUN.py", "WORKLOAD.py", "TASK_TESTS.py", "SEAM_CHECK.py", "BASELINE.json", "PREPARE.py")
    save(P / "FREEZE.json", {"files": {name: sha(P / name) for name in names}})
    for name in names:
        if name.endswith(".py"):
            ast.parse((P / name).read_text(encoding="utf-8"), filename=name)
    results = []
    out = P / "evidence/readiness"
    out.mkdir(exist_ok=False)
    commands = [("seam", [sys.executable, "-B", str(P / "SEAM_CHECK.py")]), ("preservation", [sys.executable, "-B", str(P / "CHECK.py"), "preservation"]), ("workflow", [sys.executable, "-B", str(ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py"), "--repo", str(ROOT), "--current", "CURRENT.md"])]
    for label, command in commands:
        result = subprocess.run(command, cwd=ROOT, capture_output=True)
        (out / (label + ".stdout.log")).write_bytes(result.stdout)
        (out / (label + ".stderr.log")).write_bytes(result.stderr)
        results.append({"check": label, "exit_code": result.returncode})
        if result.returncode:
            print(result.stderr.decode(errors="replace"))
            raise ValueError("repair readiness failed")
    save(out / "RESULT.json", {"checks": results, "protected": len(protected), "frozen": len(names), "new_l2_l3": "NOT_RUN", "wsl_dispatches": 0, "active_minutes": "UNKNOWN", "at_utc": datetime.now(timezone.utc).isoformat()})
    print(json.dumps({"protected": len(protected), "frozen": len(names), "checks": results}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "seal"))
    globals()[parser.parse_args().phase]()

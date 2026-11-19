"""Evaluator preparation: preserve the failed parent, pin measured members, freeze."""
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
OLD = P.parent / "H77R_NATIVE_PATH_CALLER_REPAIR_V1"


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
    for name, rel in (("CURRENT_H77R_REJECTED.md", "CURRENT.md"), ("REMOTE_HANDOFF.md", "REMOTE_HANDOFF.md"), ("PROJECT_BOTTLENECK_MAP_r130.md", "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md")):
        (refs / name).write_bytes((ROOT / rel).read_bytes())
    with (ROOT / "docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261116_r130.md").open("xb") as stream:
        stream.write((refs / "PROJECT_BOTTLENECK_MAP_r130.md").read_bytes())
    copies = {}
    for name in ("AUDIT.py", "CHECK.py", "BOOTSTRAP.py", "RUN.py", "WORKLOAD.py", "TASK_TESTS.py", "SEAM_CHECK.py"):
        with (P / name).open("xb") as stream:
            stream.write((OLD / name).read_bytes())
        copies[name] = {"source": (OLD / name).relative_to(ROOT).as_posix(), "initial_sha256": sha(OLD / name), "executor_mutable": name in {"WORKLOAD.py", "TASK_TESTS.py"}}
    save(P / "COPY_MANIFEST.json", {"schema": "h77r2-initial-source/v1", "files": copies})
    catalog = read(OLD / "evidence/evaluator_review/ARCHIVE_CATALOG.json")
    selected = {}
    for name in ("spire-server", "spire-agent"):
        path = "spire-1.16.0/bin/" + name
        matches = [x for x in catalog["members"] if x["name"] == path]
        if len(matches) != 1 or not matches[0]["regular"]:
            raise ValueError("measured member is not unique regular file")
        item = matches[0]
        selected[name] = {"archive_member": path, "size": item["size"], "sha256": item["binary_sha256"]}
    save(P / "BINARY_MEMBER_LOCK.json", {"schema": "h77r2-exact-members/v1", "archive_sha256": catalog["archive_sha256"], "archive_size": catalog["archive_size"], "spire_version": "1.16.0", "binaries": selected, "total_binary_bytes": sum(x["size"] for x in selected.values()), "source_catalog": (OLD / "evidence/evaluator_review/ARCHIVE_CATALOG.json").relative_to(ROOT).as_posix(), "source_catalog_sha256": sha(OLD / "evidence/evaluator_review/ARCHIVE_CATALOG.json"), "no_floating_size_ceiling": True})
    prep = P / "evidence/preparation"
    prep.mkdir(parents=True, exist_ok=True)
    (prep / "H76_INPUT_SEAL.json").write_bytes((OLD / "evidence/preparation/H76_INPUT_SEAL.json").read_bytes())
    plan = yaml.safe_load((OLD / "VALIDATION_PLAN.yaml").read_text(encoding="utf-8").replace(OLD.name, P.name))
    for phase, key in (("executor", "command"), ("evaluator", "evaluator_command")):
        plan["checks"][1][key] = ["python", "-B", (P / "QUALIFY.py").relative_to(ROOT).as_posix(), "--phase", phase]
    with (P / "VALIDATION_PLAN.yaml").open("x", encoding="utf-8") as stream:
        yaml.safe_dump(plan, stream, sort_keys=False, allow_unicode=True)
    command = [sys.executable, "-B", str(ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py"), "--repo", str(ROOT), "--current", "CURRENT.md"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True)
    (prep / "parent_final_workflow.stdout.log").write_bytes(result.stdout)
    (prep / "parent_final_workflow.stderr.log").write_bytes(result.stderr)
    if result.returncode:
        raise ValueError("parent final workflow invalid")
    save(prep / "PARENT_PRESERVATION.json", {"files": {f.relative_to(ROOT).as_posix(): sha(f) for f in OLD.rglob("*") if f.is_file() and "runtime" not in f.relative_to(OLD).parts and "__pycache__" not in f.parts}, "parent_accepted_count": 1812, "parent_l3": "FAIL", "parent_cleanup": "INDEPENDENTLY_PROVEN", "formal_l3_attempts": 1, "issuer_attempt_budget_consumed": 1, "spire_service_starts": 0})
    print(json.dumps({"copied": len(copies), "exact_member_count": len(selected), "total_binary_bytes": sum(x["size"] for x in selected.values()), "parent_terminal_validator": result.returncode}))


def seal():
    refs = P / "references/before_repair"
    alias = {"docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md": refs / "PROJECT_BOTTLENECK_MAP_r130.md", "REMOTE_HANDOFF.md": refs / "REMOTE_HANDOFF.md"}
    protected = {}
    for rel, digest in read(OLD / "evidence/ACCEPTED.json")["files"].items():
        path = alias.get(rel, ROOT / rel)
        if sha(path) != digest:
            raise ValueError("parent input drift: " + rel)
        protected[path.relative_to(ROOT).as_posix()] = digest
    for directory in (OLD, refs, P / "evidence/preparation"):
        for path in directory.rglob("*"):
            if path.is_file() and "runtime" not in path.relative_to(directory).parts and "__pycache__" not in path.parts:
                protected[path.relative_to(ROOT).as_posix()] = sha(path)
    for path in (ROOT / "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md", ROOT / "REMOTE_HANDOFF.md", ROOT / "docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261116_r130.md"):
        protected[path.relative_to(ROOT).as_posix()] = sha(path)
    save(P / "BASELINE.json", {"head": read(OLD / "BASELINE.json")["head"], "protected": protected, "common_protected": read(OLD / "BASELINE.json")["common_protected"], "parent": OLD.name, "governance_aliases": {rel: path.relative_to(ROOT).as_posix() for rel, path in alias.items()}, "allowed_mutable_initial_sources": {name: sha(P / name) for name in ("WORKLOAD.py", "TASK_TESTS.py")}, "created_utc": datetime.now(timezone.utc).isoformat()})
    frozen = ("CONTRACT.md", "VALIDATION_PLAN.yaml", "BINARY_MEMBER_LOCK.json", "COPY_MANIFEST.json", "QUALIFY.py", "AUDIT.py", "CHECK.py", "BOOTSTRAP.py", "RUN.py", "SEAM_CHECK.py", "BASELINE.json", "PREPARE.py")
    save(P / "FREEZE.json", {"files": {name: sha(P / name) for name in frozen}})
    for name in frozen:
        if name.endswith(".py"):
            ast.parse((P / name).read_text(encoding="utf-8"), filename=name)
    plan = yaml.safe_load((P / "VALIDATION_PLAN.yaml").read_text(encoding="utf-8"))
    if plan["task_id"] != P.name or len(plan["checks"]) != 6:
        raise ValueError("plan linkage")
    out = P / "evidence/readiness"
    out.mkdir(exist_ok=False)
    results = []
    for name, command in (("preservation", [sys.executable, "-B", str(P / "CHECK.py"), "preservation"]), ("seam", [sys.executable, "-B", str(P / "SEAM_CHECK.py")]), ("workflow", [sys.executable, "-B", str(ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py"), "--repo", str(ROOT), "--current", "CURRENT.md"])):
        completed = subprocess.run(command, cwd=ROOT, capture_output=True)
        (out / (name + ".stdout.log")).write_bytes(completed.stdout)
        (out / (name + ".stderr.log")).write_bytes(completed.stderr)
        results.append({"check": name, "exit_code": completed.returncode})
        if completed.returncode:
            print(completed.stdout.decode(errors="replace"), completed.stderr.decode(errors="replace"))
            raise ValueError("new package readiness failed")
    save(out / "RESULT.json", {"protected": len(protected), "frozen": len(frozen), "checks": results, "implementation_obligations": ["exact-profile extractor and single call", "task fixture profile and necessary negatives", "ASSET_PREFLIGHT.py"], "real_preflight": "NOT_RUN_IN_DESIGN", "new_l2_l3": "NOT_RUN", "active_minutes": "UNKNOWN", "at_utc": datetime.now(timezone.utc).isoformat()})
    print(json.dumps({"protected": len(protected), "frozen": len(frozen), "checks": results, "new_live_runs": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "seal"))
    globals()[parser.parse_args().phase]()

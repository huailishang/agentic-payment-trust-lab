"""One-time Evaluator preparation seal. Never run after contract handoff."""
from __future__ import annotations

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
OLD = P.parent / "H76_SPIRE_ISSUED_WORKLOAD_POSSESSION_MEASUREMENT_V1"
COMMON = ROOT.parent / "localagent-common"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    archive = ROOT / "docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261116_r128.md"
    with archive.open("xb") as stream:
        stream.write((P / "references/before_h77/PROJECT_BOTTLENECK_MAP_r128.md").read_bytes())
    previous = json.loads((OLD / "BASELINE.json").read_text(encoding="utf-8"))
    protected = {}
    aliases = {"CURRENT.md": "CURRENT.md", "REMOTE_HANDOFF.md": "REMOTE_HANDOFF.md", "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md": "PROJECT_BOTTLENECK_MAP_r128.md"}
    for rel, digest in previous["protected"].items():
        path = P / "references/before_h77" / aliases[rel] if rel in aliases else ROOT / rel
        if sha(path) != digest:
            raise ValueError("previous protected drift: " + rel)
        protected[path.relative_to(ROOT).as_posix()] = digest
    for directory in (OLD, P / "references", P / "evidence/preparation"):
        for path in directory.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and "runtime" not in path.relative_to(directory).parts:
                protected[path.relative_to(ROOT).as_posix()] = sha(path)
    for path in (archive, ROOT / "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md", ROOT / "REMOTE_HANDOFF.md"):
        protected[path.relative_to(ROOT).as_posix()] = sha(path)
    common_rel = ["skills/evaluator-executor-workflow/scripts/" + name for name in ("run_validation.py", "capture_evidence.py", "validate_workflow.py")]
    save(P / "BASELINE.json", {"schema": "h77-protected-baseline/v1", "head": previous["head"], "created_utc": datetime.now(timezone.utc).isoformat(), "protected": protected, "common_protected": {rel: sha(COMMON / rel) for rel in common_rel}, "governance_aliases": aliases, "preexisting_changes": "evidence/preparation/workspace_status.txt; all outside explicit allowed scope remain read-only", "historical_h76_input_count": 103})
    frozen = ["CONTRACT.md", "VALIDATION_PLAN.yaml", "RUNTIME_PROTOCOL.md", "REVIEW_PROCEDURE.md", "AUDIT.py", "CHECK.py", "BOOTSTRAP.py", "FINALIZE.py", "BASELINE.json"]
    save(P / "FREEZE.json", {"schema": "h77-contract-freeze/v1", "files": {name: sha(P / name) for name in frozen}})
    for name in ("AUDIT.py", "CHECK.py", "BOOTSTRAP.py", "FINALIZE.py"):
        ast.parse((P / name).read_text(encoding="utf-8"), filename=name)
    plan = yaml.safe_load((P / "VALIDATION_PLAN.yaml").read_text(encoding="utf-8"))
    if plan["task_id"] != P.name or len(plan["checks"]) != 6 or {ac for check in plan["checks"] for ac in check["ac"]} != {f"AC-{i:02d}" for i in range(1, 8)}:
        raise ValueError("plan mapping")
    for check in plan["checks"]:
        for key in ("command", "evaluator_command"):
            if key in check and not (ROOT / check[key][2]).is_file():
                raise ValueError("frozen command entry missing")
    check_path = str(P / "CHECK.py")
    preparation = P / "evidence/readiness"
    preparation.mkdir(exist_ok=False)
    observed = []
    for name in ("preservation", "historical", "closeout"):
        result = subprocess.run([sys.executable, "-B", check_path, name], cwd=ROOT, capture_output=True)
        (preparation / (name + ".stdout.log")).write_bytes(result.stdout)
        (preparation / (name + ".stderr.log")).write_bytes(result.stderr)
        observed.append({"check": name, "exit_code": result.returncode})
        if result.returncode:
            raise ValueError("readiness check failed: " + name)
    command = [sys.executable, "-B", str(COMMON / common_rel[-1]), "--repo", str(ROOT), "--current", "CURRENT.md"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True)
    (preparation / "workflow.stdout.log").write_bytes(result.stdout)
    (preparation / "workflow.stderr.log").write_bytes(result.stderr)
    save(preparation / "RESULT.json", {"schema": "h77-readiness/v1", "at_utc": datetime.now(timezone.utc).isoformat(), "protected_files": len(protected), "frozen_files": len(frozen), "ast_files": 4, "validation_checks": 6, "acceptance_criteria": 7, "offline_checks": observed, "workflow_exit_code": result.returncode, "new_live_runs": 0, "h77_l2_l3": "NOT_RUN", "historical_regressions_observed": [28, 19, 9, 74], "design_active_minutes": "UNKNOWN", "not_formal_execution_evidence": True})
    print(json.dumps({"protected_files": len(protected), "frozen_files": len(frozen), "checks": observed, "workflow_exit_code": result.returncode}))
    if result.returncode:
        print(result.stdout.decode(errors="replace"))
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()

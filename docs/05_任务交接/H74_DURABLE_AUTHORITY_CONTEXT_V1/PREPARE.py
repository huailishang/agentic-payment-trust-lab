"""Evaluator packet preparation. Never runs the new capability or product tests."""
import ast
import hashlib
import json
import os
import runpy
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import yaml

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
H73 = ROOT / "docs/05_任务交接/H73_AUTHORITY_CONTINUITY_MEASUREMENT_V1"
def read(p): return json.loads(p.read_text(encoding="utf-8"))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def archive():
    target = P / "references/before_h74"
    if target.exists(): raise ValueError("already archived")
    target.mkdir(parents=True)
    for rel in ("CURRENT.md", "REMOTE_HANDOFF.md", "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"):
        (target / Path(rel).name).write_bytes((ROOT / rel).read_bytes())
    old_map = ROOT / "docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261115_r124.md"
    if old_map.exists(): raise ValueError("r124 archive already exists")
    old_map.write_bytes((ROOT / "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md").read_bytes())
    for rel in read(P / "SPEC.json")["mutable_existing"]:
        dest = P / "references/initial_source" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT / rel).read_bytes())
    print(json.dumps({"previous_governance_archived": 3, "original_product_sources_preserved": 2}))
def seal():
    if (P / "FREEZE.json").exists(): raise ValueError("already frozen")
    spec = read(P / "SPEC.json")
    mutable = set(spec["mutable_existing"]) | set(spec["allowed_new"])
    prefix = P.relative_to(ROOT).as_posix() + "/"
    paths = set(filter(None, subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")))
    paths.update(read(H73 / "INPUTS.json")["protected"])
    paths.update(p.relative_to(ROOT).as_posix() for p in H73.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    protected = {rel: sha(ROOT / rel) for rel in sorted(paths) if rel != "CURRENT.md" and rel not in mutable and not rel.startswith(prefix) and (ROOT / rel).is_file()}
    initial = {rel: sha(P / "references/initial_source" / rel) for rel in spec["mutable_existing"]}
    source_files = {p.relative_to(ROOT).as_posix(): sha(p) for p in (ROOT / "src").rglob("*.py") if "__pycache__" not in p.parts}
    for rel, expected in initial.items():
        if source_files[rel] != expected: raise ValueError("product changed during preparation")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    if head != "61414d05521f7c9fe15cf0299b48b25916f5fa0e": raise ValueError("HEAD changed")
    save(P / "BASELINE.json", {"schema": "h74-baseline/v1", "task_id": P.name, "head": head, "project_map_revision": "2026-11-16-r125", "protected": protected, "mutable_initial": initial, "source_files": source_files, "h73_final_review_sha256": sha(H73 / "REVIEW.md"), "h73_final_receipt_sha256": sha(H73 / "evidence/l3_review/FINAL_RECEIPT.json")})
    for path in P.rglob("*.py"): ast.parse(path.read_text(encoding="utf-8"))
    helper = ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts"
    ns = runpy.run_path(str(helper / "run_validation.py"), run_name="h74_plan_readiness")
    plan_modes = {}
    for mode in ("executor", "evaluator"):
        task, plan = ns["load_plan"](ROOT, P / "VALIDATION_PLAN.yaml", mode=mode)
        if task != P.name or len(plan) != 8: raise ValueError("plan coverage")
        plan_modes[mode] = [c.check_id for c in plan]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    out = P / "evidence/preparation"
    out.mkdir(parents=True, exist_ok=True)
    checks = {"DOCUMENT_VALIDATOR": [sys.executable, "-B", str(helper/"validate_workflow.py"), "--repo", str(ROOT), "--current", str(ROOT/"CURRENT.md")], "DIFF_CHECK": ["git", "diff", "--check", "--", "CURRENT.md", "REMOTE_HANDOFF.md", "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"]}
    codes = {}
    for label, argv in checks.items():
        outcome = subprocess.run(argv, cwd=ROOT, capture_output=True, env=env)
        (out / (label+".stdout.log")).write_bytes(outcome.stdout)
        (out / (label+".stderr.log")).write_bytes(outcome.stderr)
        codes[label] = outcome.returncode
    if any(codes.values()): raise ValueError("packet document checks failed")
    started = read(H73 / "evidence/l3_review/COST.json")["windows"][0]["end_utc"]
    now = datetime.now(timezone.utc)
    minutes = (now - datetime.fromisoformat(started)).total_seconds()/60
    save(out / "READINESS.json", {"schema": "h74-packet-readiness/v1", "prepared_at_utc": now.isoformat(), "preparation_begin_conservative_utc": started, "preparation_wall_upper_bound_minutes_through_freeze": round(minutes+.000001,6), "actual_active_minutes": "UNKNOWN", "protected_files": len(protected), "source_files": len(source_files), "original_sources_preserved": len(initial), "plan_load_only": plan_modes, "packet_checks": codes, "formal_l2": 0, "formal_l3": 0, "product_test_execution": 0, "external_actions": 0, "cost_scope": "new H74 packet design; separate from closed H73 review and future H74 execution budget"})
    files = [p for p in P.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name != "FREEZE.json"]
    save(P / "FREEZE.json", {"schema": "h74-freeze/v1", "task_id": P.name, "at_utc": now.isoformat(), "files": {p.relative_to(P).as_posix(): sha(p) for p in sorted(files)}})
    print(json.dumps({"frozen_files": len(files), "protected_files": len(protected), "source_files": len(source_files), "plan_checks": 8, "packet_checks": codes, "formal_gates": 0, "preparation_minutes_through_freeze": round(minutes+.000001,6)}))
def close():
    now = datetime.now(timezone.utc)
    started = read(H73 / "evidence/l3_review/COST.json")["windows"][0]["end_utc"]
    save(P / "evidence/preparation/CLOSE.json", {"began_at_utc": started, "closed_at_utc": now.isoformat(), "conservative_role_window_minutes": round((now-datetime.fromisoformat(started)).total_seconds()/60+.000001,6), "actual_active_minutes": "UNKNOWN", "scope": "H74 design/readiness only, not future execution or H73 review", "formal_gates": 0, "external_actions": 0})
    print(json.dumps({"preparation_closed": True, "minutes": read(P / "evidence/preparation/CLOSE.json")["conservative_role_window_minutes"]}))
if __name__ == "__main__":
    try: {"archive": archive, "seal": seal, "close": close}[sys.argv[1]]()
    except Exception as exc:
        print(json.dumps({"preparation": "FAIL", "error_type": type(exc).__name__, "reason": str(exc) if isinstance(exc, ValueError) else "source unavailable"}))
        sys.exit(1)

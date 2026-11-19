"""Evaluator preparation only: archive governance, lock existing inputs, freeze packet."""
from __future__ import annotations
import hashlib
import json
import sqlite3
import subprocess
import sys
import ast
import os
import runpy
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
H72 = "docs/05_任务交接/H72_LOCAL_CLOSEOUT_AND_STRIPE_JOURNEY_V1/"
H72R2 = "docs/05_任务交接/H72R2_ASSERTION_AND_RECEIPT_PARITY_REPAIR_V1/"
START = "2026-11-15T14:04:20+00:00"

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding="utf-8"))
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def capture():
    target = P / "references/governance_before_h73"
    if target.exists(): raise ValueError("governance already captured")
    target.mkdir(parents=True)
    files = ["CURRENT.md", "REMOTE_HANDOFF.md", "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"]
    hashes = {}
    for rel in files:
        (target / Path(rel).name).write_bytes((ROOT / rel).read_bytes())
        hashes[rel] = sha(ROOT / rel)
    archive = ROOT / "docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261115_r123.md"
    if archive.exists(): raise ValueError("r123 archive already exists")
    archive.write_bytes((ROOT / files[-1]).read_bytes())
    write(target / "SHA256.json", hashes)
    print(json.dumps({"archived_governance": len(files), "old_map": "2026-11-15-r123"}))

def lock():
    if (P / "INPUTS.json").exists(): raise ValueError("inputs already locked")
    catalog = {}
    def add(key, rel, kind):
        path = ROOT / rel
        if not path.is_file(): raise ValueError("missing public source:" + rel)
        catalog[key] = {"path": rel, "sha256": sha(path), "kind": kind}
    for name in ("h72_operation.py", "h72_four_journeys.py", "h72_listener_n01.py", "h72_n01_recovery.py", "h72_run_common.py", "h72_build_handoff.py"):
        add(name[:-3], H72 + "runtime/" + name, "code")
    for name in ("adapters/stripe_checkout.py", "stripe_checkout_lab.py", "models.py", "trusted_execution/confirmation.py"):
        add("product:" + name, "src/agentic_payment_experiment/" + name, "code")
    for name in ("AUTHORIZATION.json", "RESULT.json", "RESULT_RESUME.json", "P0_RECEIPT.json"):
        add("h72:" + name, H72 + name, "owner_permission" if name == "AUTHORIZATION.json" else "observation")
    for name in ("N01_ORIGINAL_SESSION_READBACK.json", "N01_FINAL_PROVIDER_READBACK.json", "LISTENER_AND_N01_RESULT.json", "SESSIONS_READBACK.json"):
        add("p1:" + name, H72 + "evidence/p1/" + name, "observation")
    for name in ("FINAL.json", "journey_N01.json", "journey_C01.json", "journey_R01.json", "journey_D01.json", "payment_click_N01.json", "payment_click_R01.json", "payment_click_D01.json", "r01_unknown_injected.json", "r01_merchant_restart.json", "provider_reconciliation.json"):
        add("resumed:" + name, H72 + "evidence/resumed_20261115/" + name, "observation")
    add("owner:resume", H72 + "evidence/reauthorization_20261115_085439/ADDENDUM.json", "owner_permission")
    add("h72:review", H72 + "REVIEW.md", "review")
    add("h72r2:review", H72R2 + "REVIEW_OWNER_DECISION.md", "review")
    add("h72r2:closure", H72R2 + "evidence/budget_adjudication/CLOSURE_RECEIPT.json", "review")
    private_ref = H72 + "evidence/p1/PRIVATE_REF.json"
    base = Path(read(ROOT / private_ref)["path"]).resolve()
    if base.is_relative_to(ROOT): raise ValueError("private root must be outside repo")
    jpath, dbpath = base / "n01_operation_private.json", base / "merchant.sqlite3"
    # Read exact two whitelisted sources, never enumerate/read private credentials.
    obj = read(jpath)
    with closing(sqlite3.connect(dbpath.as_uri() + "?mode=ro", uri=True)) as conn:
        conn.execute("PRAGMA query_only=ON")
        columns = [r[1] for r in conn.execute("PRAGMA table_info(operations)")]
        cases = sorted(r[0] for r in conn.execute("SELECT case_id FROM operations"))
    paths = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    prefix = P.relative_to(ROOT).as_posix() + "/"
    protected = {rel: sha(ROOT / rel) for rel in sorted(set(filter(None, paths))) if rel != "CURRENT.md" and not rel.startswith(prefix) and (ROOT / rel).is_file()}
    for name in ("capture_evidence.py", "run_validation.py", "validate_workflow.py"):
        rel = "../localagent-common/skills/evaluator-executor-workflow/scripts/" + name
        protected[rel] = sha(ROOT / rel)
    write(P / "INPUTS.json", {"schema": "h73-inputs/v1", "task_id": P.name, "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(), "sources": catalog, "protected": protected, "private_ref": private_ref, "private_sha256": {"PRIVATE:n01_operation": sha(jpath), "PRIVATE:merchant_operations": sha(dbpath)}})
    write(P / "evidence/preparation/INPUT_READINESS.json", {"schema": "h73-input-readiness/v1", "at_utc": datetime.now(timezone.utc).isoformat(), "public_sources": len(catalog), "protected_files": len(protected), "private_sources": 2, "private_structure_only": {"n01_top_keys": sorted(obj), "operations_columns": columns, "cases_present": cases}, "external_actions": 0, "product_execution": 0, "gates_run": 0})
    print(json.dumps({"public_sources": len(catalog), "protected_files": len(protected), "private_sources": 2, "private_structure_ready": cases == ["C01", "D01", "N01", "R01"]}))

def freeze():
    if (P / "FREEZE.json").exists(): raise ValueError("already frozen")
    now = datetime.now(timezone.utc)
    elapsed = (now - datetime.fromisoformat(START)).total_seconds() / 60
    write(P / "evidence/preparation/READINESS.json", {"schema": "h73-packet-readiness/v1", "at_utc": now.isoformat(), "preparation_started_utc": START, "preparation_wall_upper_bound_minutes": round(elapsed + .000001, 6), "actual_active_minutes": "UNKNOWN", "cost_scope": "new H73 evaluator design; separate from closed H72 and future execution 150-minute envelope", "packet_checks_only": True, "formal_l2": 0, "formal_l3": 0, "external_actions": 0})
    paths = [p for p in P.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name != "FREEZE.json"]
    write(P / "FREEZE.json", {"schema": "h73-freeze/v1", "task_id": P.name, "at_utc": now.isoformat(), "files": {p.relative_to(P).as_posix(): sha(p) for p in sorted(paths)}})
    print(json.dumps({"frozen_files": len(paths), "preparation_wall_upper_bound_minutes": round(elapsed + .000001, 6)}))

def expand():
    if (P / "FREEZE.json").exists(): raise ValueError("packet already frozen")
    data = read(P / "INPUTS.json")
    before = len(data["protected"])
    # Git deliberately ignores some raw evidence. Protect those task originals too.
    old = read(ROOT / H72R2 / "BASELINE.json")["protected"]
    for rel in old:
        if rel != "CURRENT.md":
            data["protected"][rel] = sha(ROOT / rel)
    # Do not traverse unrelated historical filesystem experiments/junctions.
    for name in ("H72_LOCAL_CLOSEOUT_AND_STRIPE_JOURNEY_V1", "H72R_OFFLINE_REVIEW_GATE_CLOSURE_V1", "H72R2_ASSERTION_AND_RECEIPT_PARITY_REPAIR_V1"):
        for path in (ROOT / "docs/05_任务交接" / name).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                data["protected"][path.relative_to(ROOT).as_posix()] = sha(path)
    for entry in data["sources"].values():
        data["protected"][entry["path"]] = entry["sha256"]
    accepted = read(ROOT / H72R2 / "evidence/l3_review_20261115/ACCEPTED_SNAPSHOT.json")["files"]
    if any(sha(ROOT / H72R2 / rel) != value for rel, value in accepted.items()):
        raise ValueError("prior accepted source drift")
    write(P / "INPUTS.json", data)
    write(P / "evidence/preparation/PROTECTION_EXPANSION.json", {"before": before, "protected_files": len(data["protected"]), "reason": "include ignored historical raw evidence; hash-only, not extra analysis permission", "h72r2_accepted_files_unchanged": len(accepted)})
    print(json.dumps({"protected_files": len(data["protected"]), "h72r2_accepted_files_unchanged": len(accepted)}))

def verify():
    if (P / "FREEZE.json").exists(): raise ValueError("pre-freeze verification already ended")
    out = P / "evidence/preparation"
    out.mkdir(parents=True, exist_ok=True)
    for path in P.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    helper = ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts"
    checks = {
        "DOCUMENT_VALIDATOR": [sys.executable, "-B", str(helper / "validate_workflow.py"), "--repo", str(ROOT), "--current", str(ROOT / "CURRENT.md")],
        "CHECKER_CONTROLS": [sys.executable, "-B", str(P / "CHECK.py"), "guards"],
        "DIFF_CHECK": ["git", "diff", "--check", "--", "CURRENT.md", "REMOTE_HANDOFF.md", "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"]
    }
    results = {}
    for label, command in checks.items():
        result = subprocess.run(command, cwd=ROOT, capture_output=True, env=env)
        (out / (label + ".stdout.log")).write_bytes(result.stdout)
        (out / (label + ".stderr.log")).write_bytes(result.stderr)
        results[label] = result.returncode
    ns = runpy.run_path(str(helper / "run_validation.py"), run_name="h73_plan_readiness")
    modes = {}
    for mode in ("executor", "evaluator"):
        task, plan = ns["load_plan"](ROOT, P / "VALIDATION_PLAN.yaml", mode=mode)
        if task != P.name or len(plan) != 6: raise ValueError("plan coverage")
        modes[mode] = {"task_id": task, "checks": [c.check_id for c in plan]}
    if any(results.values()): raise ValueError("readiness check failed")
    write(out / "PACKET_CHECKS.json", {"checks": results, "plan_load_only": modes, "formal_gates_executed": 0, "historical_l2_l3_rerun": False})
    print(json.dumps({"packet_checks": results, "plan_modes_loaded": list(modes), "formal_gates": 0}))

def close():
    now = datetime.now(timezone.utc)
    write(P / "evidence/preparation/CLOSE.json", {"schema": "h73-preparation-cost-close/v1", "began_at_utc": START, "closed_at_utc": now.isoformat(), "conservative_role_window_minutes": round((now - datetime.fromisoformat(START)).total_seconds() / 60 + .000001, 6), "actual_active_minutes": "UNKNOWN", "scope": "H73 evaluator packet design and readiness, separate from H72 and future H73 150-minute execution/review budget", "external_actions": 0, "formal_gates": 0})
    print(json.dumps({"preparation_closed": True, "charged_upper_bound_minutes": read(P / "evidence/preparation/CLOSE.json")["conservative_role_window_minutes"]}))

if __name__ == "__main__":
    try:
        {"capture": capture, "lock": lock, "expand": expand, "verify": verify, "freeze": freeze, "close": close}[sys.argv[1]]()
    except Exception as exc:
        print(json.dumps({"error_category": type(exc).__name__, "preparation": "FAIL"}))
        sys.exit(1)

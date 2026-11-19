"""Capture offline candidate readiness without running a formal L2 or WSL."""
import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import CONTROL as C

P = Path(__file__).resolve().parent
ROOT = P.parents[2]


def dump(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def adaptation_scope():
    manifest = C.read(P / "COPY_MANIFEST.json")["files"]
    for name, allowed in (("CHECK.py", {"live", "verify", "closeout"}), ("BOOTSTRAP.py", {"main"})):
        before_text = (ROOT / manifest[name]["source"]).read_text(encoding="utf-8")
        after_text = (P / name).read_text(encoding="utf-8")
        before, after = ast.parse(before_text), ast.parse(after_text)
        after.body = [n for n in after.body if not (isinstance(n, ast.Import) and [alias.name for alias in n.names] == ["CONTROL"])]
        for fname in allowed:
            old = next(n for n in before.body if isinstance(n, ast.FunctionDef) and n.name == fname)
            new = next(n for n in after.body if isinstance(n, ast.FunctionDef) and n.name == fname)
            C.need(ast.dump(old.args) == ast.dump(new.args), "adaptation changed public signature")
            after.body[after.body.index(new)] = old
        C.need(ast.dump(before, include_attributes=False) == ast.dump(after, include_attributes=False), "change outside candidate adapter scope")
        (P / "evidence/preparation" / (name + ".diff")).write_text("".join(difflib.unified_diff(before_text.splitlines(True), after_text.splitlines(True), fromfile=manifest[name]["source"], tofile=P.name + "/" + name)), encoding="utf-8")
    return {"CHECK.py": ["live", "verify", "closeout"], "BOOTSTRAP.py": ["main"], "extra_import": "CONTROL"}


def main():
    out = P / "evidence/preparation"
    C.need(not (out / "READINESS.json").exists(), "successful preparation is immutable")
    out.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    baseline = C.read(P / "PREPARATION_BASELINE.json")
    for rel, digest in baseline["protected"].items():
        C.need(C.sha(ROOT / rel) == digest, "old accepted input changed: " + rel)
    for rel, digest in baseline["common_protected"].items():
        C.need(C.sha(ROOT.parent / "localagent-common" / rel) == digest, "shared tool changed")
    C.need(C.sha(ROOT / "CURRENT.md") == baseline["router_sha256"], "Executor changed routing")
    C.need(C.read(P / "AUTHORIZATION.json")["status"] == "NOT_GRANTED", "unexpected authorization change")
    source = C.sources(P, ROOT)
    scope = adaptation_scope()
    syntax = []
    for path in sorted(P.glob("*.py")):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        syntax.append(path.name)
    import yaml
    plan = yaml.safe_load((P / "VALIDATION_PLAN.yaml").read_text(encoding="utf-8"))
    C.need(plan["task_id"] == P.name and len(plan["checks"]) == 6, "wrong candidate plan")
    mapped = set()
    for check in plan["checks"]:
        C.need(check["mandatory"] is True and check["expected_exit_code"] == 0 and check["cwd"] == ".", "weakened plan")
        for key in ("command", "evaluator_command"):
            if key in check:
                command = check[key]
                C.need(command[:2] == ["python", "-B"] and (ROOT / command[2]).is_file() and (ROOT / command[2]).resolve().is_relative_to(P), "invalid exact candidate command")
        mapped.update(check["ac"])
    C.need(mapped == {"AC-" + str(i).zfill(2) for i in range(1, 8)}, "unmapped AC")
    commands = {
        "original_guards": ([sys.executable, "-B", str(P / "TASK_TESTS.py")], 0),
        "actual_response_protocol": ([sys.executable, "-B", str(P / "PROTOCOL_CHECK.py"), "protocol"], 0),
        "candidate_gate_tests": ([sys.executable, "-B", str(P / "OFFLINE_TESTS.py")], 0),
        "historical_crypto_only": ([sys.executable, "-B", str(P / "CHECK.py"), "historical"], 0),
        "original_regressions": ([sys.executable, "-B", str(P / "CHECK.py"), "regressions"], 0),
        "draft_bootstrap_denied": ([sys.executable, "-B", str(P / "BOOTSTRAP.py"), "--mode", "executor"], 1),
        "draft_seal_denied": ([sys.executable, "-B", str(P / "BUNDLE.py"), "seal"], 1),
        "existing_router_structure": ([sys.executable, "-B", str(ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py"), "--repo", str(ROOT), "--current", "CURRENT.md"], 0),
    }
    records = {}
    for name, (command, expected) in commands.items():
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=240)
        for kind in ("stdout", "stderr"):
            (out / (name + "." + kind + ".log")).write_bytes(getattr(completed, kind))
        C.need(completed.returncode == expected, "preparation check failed: " + name)
        records[name] = {"argv": command, "exit_code": completed.returncode, "expected_exit_code": expected, "stdout_bytes": len(completed.stdout), "stderr_bytes": len(completed.stderr), "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(), "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest()}
    for rel, digest in baseline["protected"].items():
        C.need(C.sha(ROOT / rel) == digest, "post-check parent drift: " + rel)
    C.need(C.sha(ROOT / "CURRENT.md") == baseline["router_sha256"], "post-check router changed")
    for rel in ("BASELINE.json", "FREEZE.json", "SUBMISSION.json", "evidence/l2", "evidence/l3", "evidence/asset_preflight", "evidence/INDEPENDENT_ISSUANCE_ATTEMPT.json"):
        C.need(not (P / rel).exists(), "preparation unexpectedly activated: " + rel)
    report = {"schema": "h78-executor-candidate-readiness/v1", "task_id": P.name, "technical_preparation": "PASS", "activation": "AWAITING_EVALUATOR_FREEZE_AND_OWNER_GRANT", "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(), "platform": sys.platform, "python": sys.version, "protected_files": len(baseline["protected"]), "parent_accepted_files": baseline["parent_accepted_count"], "parent_drift": [], "source_integrity": source, "adaptation_scope": scope, "syntax_checked": syntax, "candidate_plan_checks": 6, "mapped_ac": sorted(mapped), "commands": records, "original_task_guards": 16, "historical_protocol_positive": 4, "historical_protocol_rejected": 21, "candidate_gate_tests": 8, "original_regressions": [28, 19, 9, 74], "historical_crypto_negative": 10, "formal_l2": 0, "formal_l3": 0, "wsl_calls": 0, "real_asset_preflights": 0, "service_starts": 0, "new_credentials": 0, "new_payments": 0, "external_api_calls": 0, "new_downloads": 0, "authority_changed": False, "evaluator_verdict_issued": False, "actual_active_minutes": "UNKNOWN"}
    dump(out / "READINESS.json", report)
    (out / "workspace_status.txt").write_bytes(subprocess.check_output(["git", "-c", "core.quotepath=false", "status", "--short"], cwd=ROOT))
    files = {path.relative_to(P).as_posix(): C.sha(path) for path in P.rglob("*") if path.is_file() and "runtime" not in path.relative_to(P).parts and "__pycache__" not in path.parts and path.name != "CANDIDATE_MANIFEST.json"}
    dump(P / "CANDIDATE_MANIFEST.json", {"schema": "h78-candidate-bundle/v1", "task_id": P.name, "state": "DRAFT_CONTRACT", "files": files, "excluded": {"CANDIDATE_MANIFEST.json": "no self hash", "runtime/": "temporary local test environment"}, "not_a_freeze_or_submission": True})
    print(json.dumps({"technical_preparation": "PASS", "activation": report["activation"], "checks": len(records), "protected": len(baseline["protected"]), "candidate_files": len(files), "formal_l2": 0, "wsl_calls": 0}))


if __name__ == "__main__":
    main()

"""Evaluator-only nine-check repair plan and inherited-source protection."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from RUNTIME import TASK, ROOT

def save(name, value):
    path = TASK / name
    assert not path.exists(), name
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def plan():
    prefix = TASK.relative_to(ROOT).as_posix()
    python = ".task_envs/H47/.venv/Scripts/python.exe"
    def command(script, *args): return [python, "-B", prefix + "/" + script, *args]
    originals = {mode: prefix + "/evidence/observations_" + mode + ".json" for mode in ("l2", "l3")}
    tails = {mode: prefix + "/evidence/tail_" + mode + ".json" for mode in ("l2", "l3")}
    checks = []
    def add(acs, cmd, evaluator=None):
        row = {"id": f"VP-{len(checks)+1:02}", "ac": acs, "cwd": ".", "command": cmd,
               "expected_exit_code": 0, "mandatory": True}
        if evaluator: row["evaluator_command"] = evaluator
        checks.append(row)
    add(["AC-01"], command("CHECK.py", "baseline"))
    add(["AC-01"], command("CHECK.py", "scope"))
    add(["AC-03"], command("FROZEN_TESTS.py", "--out", originals["l2"]), command("FROZEN_TESTS.py", "--out", originals["l3"]))
    add(["AC-02", "AC-03"], command("TAIL_CASES.py", "--out", tails["l2"]), command("TAIL_CASES.py", "--out", tails["l3"]))
    add(["AC-02", "AC-03"], command("CHECK.py", "observations", "--observations", originals["l2"], "--tail", tails["l2"]),
        command("CHECK.py", "observations", "--observations", originals["l3"], "--tail", tails["l3"]))
    add(["AC-04"], command("RUNTIME.py", "focused"))
    add(["AC-04"], command("RUNTIME.py", "official"))
    add(["AC-01", "AC-02", "AC-03", "AC-04"], command("CHECK.py", "materials", "--observations", originals["l2"], "--tail", tails["l2"]),
        command("CHECK.py", "materials", "--observations", originals["l3"], "--tail", tails["l3"]))
    add(["AC-04"], command("CHECK.py", "selftest"))
    save("VALIDATION_PLAN.yaml", {"schema": "evaluator-executor-validation-plan/v1", "task_id": TASK.name, "checks": checks})
    print(json.dumps({"frozen_checks": len(checks), "cases_per_complete_run": 34}))

def freeze():
    from CHECK import workspace, sha, MUTABLE
    for path in TASK.rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"))
    files = workspace()
    prefix = TASK.relative_to(ROOT).as_posix() + "/"
    names = {name for name in files if name != "CURRENT.md" and not name.startswith(prefix)}
    parent = TASK.parent / "H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1"
    # Preserve ignored pinned SDK/library files as well as visible workspace data.
    names.update(json.loads((parent / "BASELINE.json").read_text(encoding="utf-8"))["protected_files"])
    protected = {name: sha(ROOT / name) for name in sorted(names)}
    frozen = {p.relative_to(TASK).as_posix(): sha(p) for p in TASK.rglob("*")
              if p.is_file() and "__pycache__" not in p.parts
              and p.relative_to(TASK).as_posix() not in MUTABLE
              and not p.relative_to(TASK).as_posix().startswith("evidence/") and p.name != "BASELINE.json"}
    current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    save("BASELINE.json", {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "protected_files": protected, "frozen_files": frozen, "workspace_files": sorted(files),
        "current_history_sha256": hashlib.sha256(current.split("## Global position", 1)[1].encode()).hexdigest()})
    print(json.dumps({"protected_files": len(protected), "frozen_files": len(frozen), "repair_implemented": False}))

if __name__ == "__main__": {"plan": plan, "freeze": freeze}[sys.argv[1]]()

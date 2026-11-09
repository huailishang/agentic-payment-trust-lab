"""Evaluator-only plan generation and final immutable packet snapshot."""
import ast
import hashlib
import json
import subprocess
import sys
from RUNTIME import TASK, ROOT

def save(name, value):
    path = TASK / name
    assert not path.exists(), name
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def plan():
    python = ".task_envs/H47/.venv/Scripts/python.exe"
    prefix = TASK.relative_to(ROOT).as_posix()
    def cmd(script, *args):
        return [python, "-B", prefix + "/" + script, *args]
    l2, l3 = prefix + "/evidence/observations_l2.json", prefix + "/evidence/observations_l3.json"
    checks = []
    def add(acs, command, evaluator=None):
        row = {"id": f"VP-{len(checks)+1:02}", "ac": acs, "cwd": ".", "command": command,
               "expected_exit_code": 0, "mandatory": True}
        if evaluator: row["evaluator_command"] = evaluator
        checks.append(row)
    add(["AC-01"], cmd("CHECK.py", "baseline"))
    add(["AC-01"], cmd("CHECK.py", "fixture"))
    add(["AC-01"], cmd("CHECK.py", "scope"))
    add(["AC-02", "AC-03", "AC-04"], cmd("FROZEN_TESTS.py", "--out", l2), cmd("FROZEN_TESTS.py", "--out", l3))
    add(["AC-02", "AC-03", "AC-04"], cmd("CHECK.py", "observations", "--observations", l2), cmd("CHECK.py", "observations", "--observations", l3))
    add(["AC-05"], cmd("RUNTIME.py", "focused"))
    add(["AC-05"], cmd("RUNTIME.py", "official"))
    add(["AC-01", "AC-02", "AC-03", "AC-04", "AC-05"], cmd("CHECK.py", "materials", "--observations", l2), cmd("CHECK.py", "materials", "--observations", l3))
    add(["AC-05"], cmd("CHECK.py", "selftest"))
    save("VALIDATION_PLAN.yaml", {"schema": "evaluator-executor-validation-plan/v1", "task_id": TASK.name, "checks": checks})
    print(json.dumps({"frozen_checks": len(checks)}))

def freeze():
    from CHECK import MUTABLE, workspace, sha
    for file in TASK.glob("*.py"):
        ast.parse(file.read_text(encoding="utf-8"))
    files = workspace()
    prefix = TASK.relative_to(ROOT).as_posix() + "/"
    protected = {name: sha(ROOT / name) for name in sorted(files)
                 if name != "CURRENT.md" and not name.startswith(prefix)}
    frozen = {path.relative_to(TASK).as_posix(): sha(path) for path in TASK.rglob("*")
              if path.is_file() and "__pycache__" not in path.parts
              and path.relative_to(TASK).as_posix() not in MUTABLE
              and not path.relative_to(TASK).as_posix().startswith("evidence/")
              and path.name != "BASELINE.json"}
    router = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    save("BASELINE.json", {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "protected_files": protected, "frozen_files": frozen, "workspace_files": sorted(files),
        "current_history_sha256": hashlib.sha256(router.split("## Global position", 1)[1].encode()).hexdigest()})
    print(json.dumps({"protected_files": len(protected), "frozen_files": len(frozen), "candidate_implemented": False}))

if __name__ == "__main__":
    {"plan": plan, "freeze": freeze}[sys.argv[1]]()

"""Evaluator-only preparation: source copy, readiness or protection manifest."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
PARENT = TASK.parent / "H47_UCP_COMMERCE_APPLICABILITY_V1"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_check():
    spec = importlib.util.spec_from_file_location("h50_preparation_check", TASK / "EVALUATOR_CHECK.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    mode = sys.argv[1]
    if mode == "copy":
        target = TASK / "merchant"
        assert not target.exists(), "do not overwrite source copy"
        source = PARENT / "sources/ucp/rest/python/server"
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        license_file = PARENT / "sources/ucp/LICENSE"
        shutil.copyfile(license_file, TASK / "UPSTREAM_LICENSE")
        files = {p.relative_to(target).as_posix(): sha(p) for p in sorted(target.rglob("*")) if p.is_file()}
        data = {"schema": "h50-source-copy/v1", "upstream_commit": "99724a32da48bd0f4962c83e25f17c8345ce055e",
                "source": source.relative_to(ROOT).as_posix(), "license": "Apache-2.0",
                "license_sha256": sha(license_file), "files": files,
                "editable_existing": ["db.py", "services/checkout_service.py"],
                "allowed_new": ["services/execution_control.py"]}
        (TASK / "SOURCE_COPY.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(json.dumps({"source_copy_files": len(files), "existing_source_modified": False}))
    elif mode == "readiness":
        checker = load_check()
        checker.source_locality()
        checker.selftest()
        for name in ("FROZEN_TESTS.py", "EVALUATOR_CHECK.py", "PREPARE_FREEZE.py"):
            ast.parse((TASK / name).read_text(encoding="utf-8"))
        native = json.loads((TASK / "evidence/preparation_20261020/native.json").read_text(encoding="utf-8"))
        assert native["mode"] == "native" and [x["stock"] for x in native["cases"]] == [4,3]
        assert not (TASK / "merchant/services/execution_control.py").exists(), "Evaluator must not implement the guard"
        data = {"schema": "h50-readiness/v1", "native_method_cases_executed": 2,
            "guarded_cases_executed": 0, "guarded_cases_frozen": 15,
            "same_db_authority": "SYNTHETIC_ASSUMPTION_NOT_CROSS_SYSTEM_PROOF",
            "frozen_test_syntax": "PASS", "unmodified_copy_source_locality": "PASS",
            "guard_implementation": "ABSENT_EXPECTED_EXECUTOR_WORK",
            "amount_binding_native_baseline": "NOT_OBSERVABLE",
            "preparation_is_task_result": False}
        (TASK / "evidence/preparation_20261020/READINESS.json").write_text(json.dumps(data,indent=2)+"\n", encoding="utf-8")
        print(json.dumps(data))
    elif mode == "baseline":
        assert not (TASK / "BASELINE.json").exists(), "do not overwrite frozen baseline"
        checker = load_check()
        files = sorted(checker.workspace())
        prefix = TASK.relative_to(ROOT).as_posix() + "/"
        protected = {p: sha(ROOT / p) for p in files if p != "CURRENT.md" and not p.startswith(prefix) and (ROOT / p).is_file()}
        for name in ("SKILL.md", "scripts/run_validation.py", "scripts/validate_workflow.py", "scripts/capture_evidence.py"):
            relative = "../localagent-common/skills/evaluator-executor-workflow/" + name
            protected[relative] = sha(ROOT / relative)
        frozen = {}
        for p in TASK.rglob("*"):
            if not p.is_file() or "__pycache__" in p.parts:
                continue
            name = p.relative_to(TASK).as_posix()
            if name.startswith("evidence/preparation_20261020/"):
                frozen[name] = sha(p)
                continue
            if name == "BASELINE.json" or name in checker.MUTABLE or name.startswith(("evidence/", "merchant/")):
                continue
            frozen[name] = sha(p)
        current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
        data = {"schema": "h50-baseline/v1", "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "workspace_files": files, "protected_files": protected, "frozen_files": frozen,
            "current_history_sha256": hashlib.sha256(current.split("## Global position",1)[1].encode()).hexdigest()}
        (TASK / "BASELINE.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"protected_files":len(protected), "frozen_files":len(frozen)}))
    else:
        raise ValueError("unknown preparation mode")

if __name__ == "__main__":
    main()

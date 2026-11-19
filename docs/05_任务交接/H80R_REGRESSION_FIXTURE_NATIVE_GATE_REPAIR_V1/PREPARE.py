"""Evaluator-only preparation of a new bounded gate repair; no product edits."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
OLD = P.parent / "H80_VERIFIED_FACT_CONTEXT_BINDING_REPAIR_V1"
PRODUCT = ["src/agentic_payment_experiment/trusted_execution/credential_possession.py", "src/agentic_payment_experiment/trusted_execution/execution_facts.py", "tests/trusted_execution/test_payment_binding.py"]
TEST = "tests/trusted_execution/test_credential_context_consumption.py"
MAP = "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def write(path, text):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def change(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after)


def snapshot():
    original = read(OLD / "BASELINE.json")
    assert all(sha(ROOT / rel) == value for rel, value in original["files"].items())
    assert (OLD / "REVIEW.md").is_file() and not (OLD / "SUBMISSION.json").exists()
    for rel in ["CURRENT.md", "REMOTE_HANDOFF.md", MAP, *PRODUCT, TEST]:
        dest = P / "references/before_h80r" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        assert not dest.exists()
        shutil.copyfile(ROOT / rel, dest)
    for rel in PRODUCT:
        dest = P / "references/before_h80" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(OLD / "references/before_h80" / rel, dest)
    archive = ROOT / "docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261117_r135.md"
    assert not archive.exists()
    shutil.copyfile(ROOT / MAP, archive)
    shutil.copyfile(OLD / "SOURCE.json", P / "SOURCE.json")
    files = {f.relative_to(ROOT).as_posix(): sha(f) for f in OLD.rglob("*") if f.is_file() and not {"runtime", "__pycache__"}.intersection(f.parts)}
    save(P / "PARENT_SNAPSHOT.json", {"files": files, "parent_submitted": False, "parent_formal_l2": 2, "parent_formal_l3": 0, "parent_verdict": "REJECTED", "historical_launcher_boundary": "UNKNOWN"})

    checker = (OLD / "CHECK.py").read_text(encoding="utf-8")
    new_scope = '''def new_test_scope():
    rel = "tests/trusted_execution/test_credential_context_consumption.py"
    before = ast.parse((P / "references/before_h80r" / rel).read_text(encoding="utf-8"))
    after = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
    target = "test_existing_credential_reference_precedence_is_preserved"
    added = []
    for node in ast.walk(after):
        if isinstance(node, ast.FunctionDef) and node.name == target:
            for call in ast.walk(node):
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id == "self" and call.func.attr == "consume":
                    for item in list(call.keywords):
                        if item.arg == "identity":
                            expected = ast.parse('replace(self.identity, credential_ref="different-credential")', mode="eval").body
                            need(ast.dump(item.value) == ast.dump(expected), "only exact identity premise repair permitted")
                            added.append(item.arg)
                            call.keywords.remove(item)
    need(len(added) in (0, 1), "duplicate test repair")
    need(ast.dump(before) == ast.dump(after), "new regression altered beyond one frozen input keyword")


'''
    checker = change(checker, "def preservation():\n", new_scope + "def preservation():\n")
    checker = change(checker, "    fixture_ast()\n    product_scope()\n", "    fixture_ast()\n    product_scope()\n    new_test_scope()\n")
    checker = change(checker, "def regressions():\n    route()\n", 'def regressions():\n    route()\n    need(sys.platform == "win32" and os.name == "nt", "native Windows only")\n    os.environ.update(PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")\n    print(json.dumps({"execution_platform": sys.platform, "native_environment_set_before_first_suite": True}), flush=True)\n')
    checker = change(checker, '    need(added > 0, "new regression suite empty")', '    need(added == 6, "all original six new regressions required")')
    write(P / "CHECK.py", checker)

    boot = (OLD / "BOOTSTRAP.py").read_text(encoding="utf-8")
    boot = change(boot, '    route = CHECK.route()\n', '    CHECK.need(sys.platform == "win32" and os.name == "nt", "native Windows only; no WSL/Bash launcher")\n    CHECK.need(args.mode != "implementation" or args.attempt == 1, "one implementation cycle only")\n    route = CHECK.route()\n')
    boot = change(boot, '        CHECK.need(first.exists() and CHECK.read(first)["result"] != "PASS", "stop after successful L2 or missing first gate")', '''        CHECK.need(args.mode == "executor", "second attempt is environment-only L2")
        CHECK.need(first.exists() and CHECK.read(first)["result"] != "PASS", "stop after successful L2 or missing first gate")
        gate = CHECK.read(first)
        CHECK.need([c["check_id"] for c in gate["checks"] if c["result"] != "PASS"] == ["VP-03"], "only isolated launch import failure may retry")
        err = (ROOT / gate["checks"][2]["stderr"]).read_text(encoding="utf-8", errors="replace")
        CHECK.need("ModuleNotFoundError: No module named 'agentic_payment_experiment'" in err and err.count("FAIL: ") == 1 and "FAIL: test_cold_child_process_deserializes_original_graph" in err, "not a permitted import-only failure")
        note = CHECK.read(P / "ENVIRONMENT_RETRY.json")
        CHECK.need(note.get("failure_family") == "native_import_environment" and bool(note.get("reason")), "preserve explicit environment diagnosis")
        first_marker = CHECK.read(P / "evidence/FORMAL_l2_START.json")
        CHECK.need(all(CHECK.sha(ROOT / rel) == value for rel, value in first_marker["mutable_sha256"].items()), "no implementation change after first L2")''')
    boot = change(boot, '"FORMAL_implementation_0" + str(args.attempt) + "_START.json"', '"FORMAL_implementation_01_START.json"')
    boot = change(boot, '{"phase": name, "at_utc": datetime.now(timezone.utc).isoformat()}, stream)', '{"phase": name, "at_utc": datetime.now(timezone.utc).isoformat(), "mutable_sha256": {rel: CHECK.sha(ROOT / rel) for rel in CHECK.read(P / "BASELINE.json")["mutable"]}, "execution_platform": sys.platform}, stream)')
    boot = change(boot, '    env.update(PYTHONDONTWRITEBYTECODE="1")', '    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(ROOT / "src"))')
    boot = change(boot, '        with ledger.open("a", encoding="utf-8") as stream:\n            stream.write(json.dumps({"kind": "end", "phase": "implementation_0" + str(args.attempt),', '        if args.attempt == 1:\n            with ledger.open("a", encoding="utf-8") as stream:\n                stream.write(json.dumps({"kind": "end", "phase": "implementation_01",')
    write(P / "BOOTSTRAP.py", boot)
    seal = (OLD / "SEAL.py").read_text(encoding="utf-8").replace('"references/before_h80"', '"references/before_h80r"').replace('"h80-executor-submission/v1"', '"h80r-executor-submission/v1"')
    write(P / "SEAL.py", seal)
    write(P / "VALIDATION_PLAN.yaml", (OLD / "VALIDATION_PLAN.yaml").read_text(encoding="utf-8").replace(OLD.name, P.name).replace("ac: [AC-02, AC-03]", "ac: [AC-02]").replace("ac: [AC-04]", "ac: [AC-03, AC-04]"))
    print(json.dumps({"parent_files_snapshotted": len(files), "product_test_edits": 0, "behavior_runs": 0}))


def freeze():
    original = read(OLD / "BASELINE.json")
    aliases = {rel: (P / "references/before_h80r" / rel).relative_to(ROOT).as_posix() for rel in (MAP, "REMOTE_HANDOFF.md")}
    protected = {}
    for rel, value in original["files"].items():
        target = aliases.get(rel, rel)
        assert sha(ROOT / target) == value, rel
        protected[target] = value
    for rel, value in read(P / "PARENT_SNAPSHOT.json")["files"].items():
        assert sha(ROOT / rel) == value
        protected[rel] = value
    inventory = sorted(set(filter(None, subprocess.check_output(["git", "ls-files", "-c", "-o", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0"))))
    for rel in inventory:
        path = ROOT / rel
        if not path.is_file() or rel in {"CURRENT.md", TEST} or path.is_relative_to(P) or {"runtime", "__pycache__"}.intersection(path.parts):
            continue
        protected[rel] = sha(path)
    for rel in [*PRODUCT, TEST]:
        assert sha(ROOT / rel) == sha(P / "references/before_h80r" / rel), "Evaluator cannot edit implementation"
    common = original["common_protected"]
    assert all(sha(ROOT.parent / "localagent-common" / rel) == value for rel, value in common.items())
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert head == original["head"]
    save(P / "BASELINE.json", {"head": head, "files": protected, "common_protected": common, "historical_aliases": aliases, "mutable": [TEST], "existing_inventory": inventory, "initial_mutable_sha256": {TEST: sha(ROOT / TEST)}, "inherited_product_sha256": {rel: sha(ROOT / rel) for rel in PRODUCT}})
    syntax = []
    for path in P.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"))
        syntax.append(path.name)
    import yaml
    plan = yaml.safe_load((P / "VALIDATION_PLAN.yaml").read_text(encoding="utf-8"))
    assert plan["task_id"] == P.name and len(plan["checks"]) == 4
    save(P / "READINESS.json", {"at_utc": datetime.now(timezone.utc).isoformat(), "package_ready": True, "syntax_checked": syntax, "protected_files": len(protected), "product_test_edits": 0, "behavior_runs": 0, "formal_l2": 0, "formal_l3": 0, "new_issuer_runs": 0, "parent_l2_consumed": 2, "parent_l3_consumed": 0})
    files = {f.relative_to(P).as_posix(): sha(f) for f in P.rglob("*") if f.is_file() and f.name != "FREEZE.json" and not {"runtime", "__pycache__", "evidence"}.intersection(f.relative_to(P).parts)}
    save(P / "FREEZE.json", {"files": files})
    print(json.dumps({"frozen_files": len(files), "protected_files": len(protected), "product_test_edits": 0, "formal_runs": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("snapshot", "freeze"))
    globals()[parser.parse_args().action]()

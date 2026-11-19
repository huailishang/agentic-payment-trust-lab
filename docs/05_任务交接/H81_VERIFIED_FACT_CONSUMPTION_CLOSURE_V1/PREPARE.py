"""Evaluator-only package preparation; preserves superseded frozen artifacts."""
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
OLD = P.parent / "H80R_REGRESSION_FIXTURE_NATIVE_GATE_REPAIR_V1"
PARENT = P.parent / "H80_VERIFIED_FACT_CONTEXT_BINDING_REPAIR_V1"
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
    prior = read(OLD / "BASELINE.json")
    assert all(sha(ROOT / rel) == value for rel, value in prior["files"].items())
    assert all(sha(OLD / rel) == value for rel, value in read(OLD / "FREEZE.json")["files"].items())
    assert all(sha(ROOT / rel) == value for rel, value in prior["initial_mutable_sha256"].items())
    assert not any((OLD / name).exists() for name in ("ATTEMPT_LEDGER.jsonl", "SUBMISSION.json", "evidence/l2", "evidence/l3"))
    if (OLD / "REPORT.md").exists():
        assert "Executor status: BLOCKED_PRE_IMPLEMENTATION" in (OLD / "REPORT.md").read_text(encoding="utf-8")
    for rel in ["CURRENT.md", "REMOTE_HANDOFF.md", MAP, *PRODUCT, TEST]:
        dest = P / "references/before_h81" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        assert not dest.exists()
        shutil.copyfile(ROOT / rel, dest)
    for rel in PRODUCT:
        dest = P / "references/before_h80" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PARENT / "references/before_h80" / rel, dest)
    dest = P / "references/before_h80r" / TEST
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / TEST, dest)
    archive = ROOT / "docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261118_r136.md"
    assert not archive.exists()
    shutil.copyfile(ROOT / MAP, archive)
    shutil.copyfile(OLD / "SOURCE.json", P / "SOURCE.json")
    prior_files = {f.relative_to(ROOT).as_posix(): sha(f) for f in OLD.rglob("*") if f.is_file() and not {"runtime", "__pycache__"}.intersection(f.parts)}
    save(P / "SUPERSEDED_SNAPSHOT.json", {"files": prior_files, "task_id": OLD.name, "status": "SUPERSEDED_BEFORE_EXECUTION", "preflight_report": "BLOCKED_PRE_IMPLEMENTATION", "formal_implementation": 0, "formal_l2": 0, "formal_l3": 0, "human_instruction": "这个小的错 可以放到下一执行包，新的包要围绕 项目瓶颈，继续整理"})
    before_modules = {}
    for rel in PRODUCT[:2]:
        name = "agentic_payment_experiment.trusted_execution." + Path(rel).stem
        path = PARENT / "references/before_h80" / rel
        before_modules[name] = {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}
    path = PARENT / "references/before_h80" / PRODUCT[2]
    save(P / "BEFORE_LOCK.json", {"modules": before_modules, "fixture": {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}, "observed_slots_only": ["M01", "M02"], "not_git_head": True})

    checker = (OLD / "CHECK.py").read_text(encoding="utf-8")
    checker = change(checker, 'data["hypothesis_id"] == "H-80"', 'data["hypothesis_id"] == "H-81"')
    checker = change(checker, '{"source_run": data["run_id"], "time_mode":', '{"source_run": data["run_id"], "source_observed_at_epoch": data["observed_at_epoch"], "challenge_payload_sha256": sha(source / "payload.bin"), "time_mode":')
    write(P / "CHECK.py", checker)
    boot = (PARENT / "BOOTSTRAP.py").read_text(encoding="utf-8")
    boot = change(boot, '    route = CHECK.route()\n', '    CHECK.need(sys.platform == "win32" and os.name == "nt", "native Windows only")\n    route = CHECK.route()\n')
    boot = change(boot, '        CHECK.need(first.exists() and CHECK.read(first)["result"] != "PASS", "stop after successful L2 or missing first gate")', '''        CHECK.need(first.exists() and CHECK.read(first)["result"] != "PASS", "stop after successful L2 or missing first gate")
        first_gate = CHECK.read(first)
        CHECK.need([c["check_id"] for c in first_gate["checks"] if c["result"] != "PASS"] == ["VP-03", "VP-05"], "retry only known prerequisite failure, not safety or scope failure")
        err = (ROOT / first_gate["checks"][2]["stderr"]).read_text(encoding="utf-8", errors="replace")
        known_fixture = "FAIL: test_existing_credential_reference_precedence_is_preserved" in err
        known_import = "FAIL: test_cold_child_process_deserializes_original_graph" in err and "ModuleNotFoundError: No module named 'agentic_payment_experiment'" in err
        CHECK.need(err.count("FAIL: ") == 1 and (known_fixture or known_import), "new business failure is outside this repair envelope")''')
    boot = change(boot, '    env.update(PYTHONDONTWRITEBYTECODE="1")', '    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(ROOT / "src"), PYTHONIOENCODING="utf-8")')
    write(P / "BOOTSTRAP.py", boot)
    seal = (OLD / "SEAL.py").read_text(encoding="utf-8").replace('"references/before_h80r"', '"references/before_h81"').replace('"h80r-executor-submission/v1"', '"h81-executor-submission/v1"').replace('gate["checks_total"] == 4', 'gate["checks_total"] == 5').replace('"l2_checks": 4', '"l2_checks": 5')
    write(P / "SEAL.py", seal)
    plan = {"schema": "evaluator-executor-validation-plan/v1", "task_id": P.name, "checks": []}
    for index, ac, name, args in ((1, ["AC-01"], "CHECK.py", ["preservation"]), (2, ["AC-02", "AC-03"], "COMPARE.py", ["--phase", "executor"]), (3, ["AC-04"], "CHECK.py", ["regressions"]), (4, ["AC-01"], "CHECK.py", ["preservation"]), (5, ["AC-05"], "EVIDENCE.py", ["--phase", "executor"])):
        cmd = ["python", "-B", (P / name).relative_to(ROOT).as_posix(), *args]
        item = {"id": "VP-" + str(index).zfill(2), "ac": ac, "cwd": ".", "command": cmd, "expected_exit_code": 0, "mandatory": True}
        if name in {"COMPARE.py", "EVIDENCE.py"}:
            item["evaluator_command"] = [*cmd[:-1], "evaluator"]
        plan["checks"].append(item)
    import yaml
    write(P / "VALIDATION_PLAN.yaml", yaml.safe_dump(plan, allow_unicode=True, sort_keys=False))
    template = (OLD / "REPORT_TEMPLATE.md").read_text(encoding="utf-8").replace(OLD.name, P.name).replace("H80R", "H81").replace("Task kind: repair", "Task kind: capability_experiment")
    template = template.replace("- AC: AC-02\n", "- AC: AC-02 AC-03\n").replace("- AC: AC-03 AC-04\n", "- AC: AC-04\n").replace("- AC: AC-01 AC-04\n", "- AC: AC-01\n")
    prefix = (P / "evidence/l2").relative_to(ROOT).as_posix()
    template += "\n## EV-05\n\n- AC: AC-05\n" + "".join("- " + key + ": " + prefix + "/EV-05." + suffix + "\n" for key, suffix in (("Meta", "meta.json"), ("Stdout", "stdout.log"), ("Stderr", "stderr.log")))
    template += "\n## B-23 closure comparison / 瓶颈变化\n\n待填本次修复前M01/M02与修复后同输入差异、来源与源码摘要、原矩阵/回归保持、CLOSURE.json路径。不得照抄父报告冒充本次运行。H80R0/0/0被替换，原H80失败不追认；Evaluator未独立签收前不宣告瓶颈关闭。\n"
    write(P / "REPORT_TEMPLATE.md", template)
    print(json.dumps({"superseded_files": len(prior_files), "superseded_attempts": 0, "product_test_edits": 0, "behavior_runs": 0}))


def freeze():
    prior = read(OLD / "BASELINE.json")
    aliases = {rel: (P / "references/before_h81" / rel).relative_to(ROOT).as_posix() for rel in (MAP, "REMOTE_HANDOFF.md")}
    protected = {}
    for rel, value in prior["files"].items():
        target = aliases.get(rel, rel)
        assert sha(ROOT / target) == value, rel
        protected[target] = value
    for rel, value in read(P / "SUPERSEDED_SNAPSHOT.json")["files"].items():
        assert sha(ROOT / rel) == value
        protected[rel] = value
    inventory = sorted(set(filter(None, subprocess.check_output(["git", "ls-files", "-c", "-o", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0"))))
    for rel in inventory:
        path = ROOT / rel
        if not path.is_file() or rel in {"CURRENT.md", TEST} or path.is_relative_to(P) or {"runtime", "__pycache__"}.intersection(path.parts):
            continue
        protected[rel] = sha(path)
    for rel in [*PRODUCT, TEST]:
        assert sha(ROOT / rel) == sha(P / "references/before_h81" / rel), "preparation cannot implement product/test changes"
    common = prior["common_protected"]
    assert all(sha(ROOT.parent / "localagent-common" / rel) == value for rel, value in common.items())
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert head == prior["head"]
    save(P / "BASELINE.json", {"head": head, "files": protected, "common_protected": common, "historical_aliases": aliases, "mutable": [TEST], "existing_inventory": inventory, "initial_mutable_sha256": {TEST: sha(ROOT / TEST)}, "inherited_product_sha256": {rel: sha(ROOT / rel) for rel in PRODUCT}})
    syntax = []
    for path in P.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"))
        syntax.append(path.name)
    import yaml
    plan = yaml.safe_load((P / "VALIDATION_PLAN.yaml").read_text(encoding="utf-8"))
    assert plan["task_id"] == P.name and len(plan["checks"]) == 5
    save(P / "READINESS.json", {"at_utc": datetime.now(timezone.utc).isoformat(), "package_ready": True, "syntax_checked": syntax, "protected_files": len(protected), "product_test_edits": 0, "before_or_after_behavior_runs": 0, "formal_l2": 0, "formal_l3": 0, "new_issuer_runs": 0, "h80_formal_l2_consumed": 2, "h80r_attempts_consumed": 0})
    files = {f.relative_to(P).as_posix(): sha(f) for f in P.rglob("*") if f.is_file() and f.name != "FREEZE.json" and not {"runtime", "__pycache__", "evidence"}.intersection(f.relative_to(P).parts)}
    save(P / "FREEZE.json", {"files": files})
    print(json.dumps({"frozen_files": len(files), "protected_files": len(protected), "product_test_edits": 0, "formal_runs": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("snapshot", "freeze"))
    globals()[parser.parse_args().action]()

"""Frozen scope + actual locked-asset preflight, before any independent issuer."""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import RUN
import CHECK
import SEAM_CHECK

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
OLD = P.parent / "H77R_NATIVE_PATH_CALLER_REPAIR_V1"


def need(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function(tree, name):
    return next(node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name)


def ast_text(tree):
    return ast.dump(tree, include_attributes=False)


def scope():
    old = ast.parse((OLD / "WORKLOAD.py").read_text(encoding="utf-8"))
    new = ast.parse((P / "WORKLOAD.py").read_text(encoding="utf-8"))
    old_extract, new_extract = function(old, "extract_binaries"), function(new, "extract_binaries")
    need([arg.arg for arg in new_extract.args.args] == ["archive", "destination", "member_profile"], "explicit member_profile signature required")
    new.body[new.body.index(new_extract)] = old_extract
    old_collect = function(function(old, "Collector"), "collect")
    new_collect = function(function(new, "Collector"), "collect")
    def binding(node):
        return isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "binaries"
    old_bindings, new_bindings = [n for n in old_collect.body if binding(n)], [n for n in new_collect.body if binding(n)]
    need(len(old_bindings) == len(new_bindings) == 1, "single production extractor binding")
    expected = ast.parse('binaries = extract_binaries(archive, self.base / "bin", member_profile=read(self.task / "BINARY_MEMBER_LOCK.json"))').body[0]
    need(ast_text(new_bindings[0]) == ast_text(expected), "production profile must be fixed task lock")
    new_collect.body[new_collect.body.index(new_bindings[0])] = old_bindings[0]
    need(ast_text(new) == ast_text(old), "WORKLOAD change outside extractor/binding")
    old_tests = function(ast.parse((OLD / "TASK_TESTS.py").read_text(encoding="utf-8")), "GuardTests")
    new_tests = function(ast.parse((P / "TASK_TESTS.py").read_text(encoding="utf-8")), "GuardTests")
    before = {n.name: n for n in old_tests.body if isinstance(n, ast.FunctionDef)}
    after = {n.name: n for n in new_tests.body if isinstance(n, ast.FunctionDef)}
    need(set(before).issubset(after), "original task guards removed")
    allowed = {"make_archive", "test_archive_member_to_file_digest_binding", "test_archive_traversal_link_and_duplicate_denied"}
    for name in set(before) - allowed:
        need(ast_text(before[name]) == ast_text(after[name]), "original non-archive guard changed")
    helper = ast.parse((P / "ASSET_PREFLIGHT.py").read_text(encoding="utf-8"))
    for node in ast.walk(helper):
        if isinstance(node, ast.Import):
            need(not any(alias.name.split(".")[0] in {"subprocess", "socket", "requests", "urllib", "http", "ctypes"} for alias in node.names), "preflight forbidden import")
        if isinstance(node, ast.ImportFrom):
            need((node.module or "").split(".")[0] not in {"subprocess", "socket", "requests", "urllib", "http", "ctypes"}, "preflight forbidden import")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            need(node.func.attr not in {"system", "popen", "execv", "execve", "execl", "spawnv", "spawnve", "posix_spawn", "Popen"}, "preflight must not execute binaries")
    return {"production_scope": "extractor_and_fixed_profile_call_only", "original_task_guards_retained": sum(name.startswith("test_") for name in before)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("executor", "evaluator"), required=True)
    phase = parser.parse_args().phase
    CHECK.preservation()
    import yaml
    route = yaml.safe_load((ROOT / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0])
    need(route["task_id"] == P.name, "route")
    need((route["current_role"], route["state"]) in ({("Executor", "EXECUTING"), ("Executor", "CONTRACT_FROZEN")} if phase == "executor" else {("Evaluator", "READY_FOR_REVIEW")}), "phase authority")
    if phase == "evaluator":
        for rel, digest in read(P / "evidence/ACCEPTED.json")["files"].items():
            need(sha(ROOT / rel) == digest, "accepted drift")
    print(json.dumps(scope()), flush=True)
    completed = subprocess.run([sys.executable, "-B", str(P / "TASK_TESTS.py")], cwd=ROOT, check=False, timeout=180)
    need(completed.returncode == 0, "task guards failed before asset access")
    SEAM_CHECK.main()
    parent = P / "evidence/asset_preflight"
    need(parent.resolve() == parent.absolute() and not parent.is_symlink(), "preflight directory escape")
    parent.mkdir(parents=True, exist_ok=True)
    prior = sorted(parent.glob(phase + "_*"))
    need(len(prior) < (2 if phase == "executor" else 1), "asset-preflight attempt ceiling")
    out = parent / (phase + "_" + str(len(prior) + 1).zfill(2))
    out.mkdir(exist_ok=False)
    (out / "START.json").write_text(json.dumps({"phase": phase, "at_utc": datetime.now(timezone.utc).isoformat(), "budget_consumed": 1}) + "\n", encoding="utf-8")
    command = ["wsl.exe", "--distribution", "Ubuntu", "--exec", "/usr/bin/python3", "-B", RUN.wsl_path(P / "ASSET_PREFLIGHT.py"), "--phase", phase, "--out", RUN.wsl_path(out)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, check=False, timeout=180)
    (out / "stdout.log").write_bytes(result.stdout)
    (out / "stderr.log").write_bytes(result.stderr)
    (out / "COMMAND.json").write_text(json.dumps({"argv": command, "exit_code": result.returncode, "finished_utc": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    need(result.returncode == 0, "real-asset qualification failed; no issuer permitted")
    data, lock = read(out / "RESULT.json"), read(P / "BINARY_MEMBER_LOCK.json")
    need(data["schema"] == "h77r2-real-asset-preflight/v1" and data["phase"] == phase, "preflight identity")
    need(data["archive_sha256"] == lock["archive_sha256"] and data["archive_size"] == lock["archive_size"] and data["extractor_sha256"] == sha(P / "WORKLOAD.py"), "asset/extractor provenance")
    need(set(data["binaries"]) == set(lock["binaries"]), "two members only")
    for name, expected in lock["binaries"].items():
        actual = data["binaries"][name]
        need(actual["archive_member"] == expected["archive_member"] and actual["size"] == expected["size"] and actual["archive_member_sha256"] == actual["extracted_sha256"] == expected["sha256"], "real member mismatch")
    need(data["extracted_bytes"] == lock["total_binary_bytes"] and data["scratch_removed"] is True and all(data[k] == 0 for k in ("binary_executions", "spire_service_starts", "new_downloads")), "preflight effects/cleanup")
    print(json.dumps({"real_asset_preflight": "PASS", "phase": phase, "binary_bytes": data["extracted_bytes"], "output": out.relative_to(ROOT).as_posix(), "new_issuer_starts": 0}), flush=True)
    if phase == "evaluator":
        print(json.dumps(CHECK.live(), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

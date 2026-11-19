"""Frozen offline response qualification; never invokes the issuer or WSL."""
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
OLD = P.parent / "H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1"


def need(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scope():
    before = ast.parse((OLD / "WORKLOAD.py").read_text(encoding="utf-8"))
    after = ast.parse((P / "WORKLOAD.py").read_text(encoding="utf-8"))
    old = next(n for n in before.body if isinstance(n, ast.FunctionDef) and n.name == "one_entry")
    new = next(n for n in after.body if isinstance(n, ast.FunctionDef) and n.name == "one_entry")
    need(ast.dump(new.args) == ast.dump(old.args), "parser signature drift")
    after.body[after.body.index(new)] = old
    need(ast.dump(before, include_attributes=False) == ast.dump(after, include_attributes=False), "change outside one_entry")
    need(sha(P / "TASK_TESTS.py") == sha(OLD / "TASK_TESTS.py"), "original guards changed")
    return {"scope": "one_entry_only", "original_guard_file_unchanged": True}


def preservation():
    baseline = read(P / "BASELINE.json")
    need(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == baseline["head"], "HEAD drift")
    for rel, digest in baseline["files"].items():
        need((ROOT / rel).is_file() and sha(ROOT / rel) == digest, "protected drift: " + rel)
    for rel, digest in baseline["common_protected"].items():
        need(sha(ROOT.parent / "localagent-common" / rel) == digest, "common drift: " + rel)
    for rel, digest in read(P / "FREEZE.json")["files"].items():
        need(sha(P / rel) == digest, "frozen drift: " + rel)
    accepted = P / "evidence/ACCEPTED.json"
    if accepted.exists():
        for rel, digest in read(accepted)["files"].items():
            need(sha(ROOT / rel) == digest, "accepted drift: " + rel)
    return {"protected_files": len(baseline["files"]), **scope(), "new_issuer_runs": 0}


def fixtures():
    source = read(P / "SOURCE_LOCK.json")
    for name, record in source["fixtures"].items():
        need(sha(P / "fixtures" / name) == record["sha256"] == sha(ROOT / record["source"]), "actual fixture provenance")
    response = read(P / "fixtures/entry_create.redacted.json")
    agents = read(P / "fixtures/agent_list.redacted.json")
    need(response["results"][0]["status"] == {"code": 0, "message": "OK"}, "fixed actual status")
    return response, agents


def baseline():
    response, agents = fixtures()
    old = load(OLD / "WORKLOAD.py", "frozen_parent_workload")
    try:
        old.entry_identity(response)
    except ValueError as exc:
        need(str(exc) == "entry object schema", "unexpected parent baseline")
    else:
        raise ValueError("parent baseline unexpectedly accepts actual response")
    entry = response["results"][0]["entry"]
    old.validate_entry(entry, old.parent_from_management(agents), entry["id"])
    return {"actual_parent_failure_reproduced": True, "actual_inner_entry_valid": True, "new_issuer_runs": 0}


def protocol():
    response, agents = fixtures()
    w = load(P / "WORKLOAD.py", "candidate_workload")
    parent = w.parent_from_management(agents)
    entry = response["results"][0]["entry"]
    entry_id = entry["id"]
    def consume(obj):
        w.one_entry(obj)
        need(w.entry_identity(obj) == entry_id, "actual registration ID drift")
        w.validate_entry(obj, parent, entry_id)
    positive = [response, {"entry": entry}, {"entries": [entry]}, entry]
    for obj in positive:
        saved = copy.deepcopy(obj)
        consume(obj)
        need(obj == saved, "parser mutated input")
    cases = {}
    def batch(item):
        return {"results": [item]}
    for name, status in (("failed_status", {"code": 13, "message": "DENIED"}), ("missing_code", {}), ("bool_code", {"code": False}), ("float_code", {"code": 0.0}), ("string_code", {"code": "0"}), ("status_not_object", [])):
        cases[name] = batch({"status": status, "entry": entry})
    cases["missing_status"] = batch({"entry": entry})
    cases["missing_entry"] = batch({"status": {"code": 0}})
    cases["entry_not_object"] = batch({"status": {"code": 0}, "entry": []})
    cases["empty_results"] = {"results": []}
    cases["two_results"] = {"results": response["results"] * 2}
    cases["results_not_array"] = {"results": response["results"][0]}
    for key, value in (("entry", entry), ("entries", [entry]), ("id", entry_id)):
        cases["ambiguous_" + key] = {**response, key: value}
    for name, key, value in (("wrong_parent", "parent_id", "spiffe://h76.test/spire/agent/join_token/wrong-parent"), ("wrong_target", "spiffe_id", w.TARGET + "/wrong"), ("wrong_uid", "selectors", [{"type": "unix", "value": "uid:1002"}]), ("duplicate_selector", "selectors", entry["selectors"] * 2), ("missing_selector", "selectors", []), ("wrong_id", "id", "different-entry-001")):
        changed = copy.deepcopy(response)
        changed["results"][0]["entry"][key] = value
        cases[name] = changed
    outcomes = {}
    for name, obj in cases.items():
        try:
            consume(obj)
        except ValueError as exc:
            outcomes[name] = str(exc)
        else:
            raise ValueError("unsafe response accepted: " + name)
    return {"actual_and_legacy_positive": len(positive), "negative_cases": outcomes, "negative_count": len(outcomes), "negative_accepted": 0, "historical_offline_only": True, "new_issuer_runs": 0}


def guards():
    subprocess.run([sys.executable, "-B", str(P / "TASK_TESTS.py")], cwd=ROOT, check=True, timeout=180)
    return {"original_task_tests": 16, "new_issuer_runs": 0}


def regressions():
    env = os.environ.copy()
    base = P / "runtime/userbase"
    shim = base / ("Python" + str(sys.version_info.major) + str(sys.version_info.minor)) / "site-packages/tests"
    shim.mkdir(parents=True, exist_ok=True)
    (shim / "__init__.py").write_text("__path__ = [" + repr(str(ROOT / "tests")) + "]\n", encoding="utf-8")
    env.update(PYTHONUSERBASE=str(base), PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
    commands = [[sys.executable, "-B", "-m", "unittest", "tests.trusted_execution.test_credential_possession", "tests.trusted_execution.test_identity_assurance", "tests.test_stripe_authority_context"], [sys.executable, "-B", "docs/05_任务交接/H74_DURABLE_AUTHORITY_CONTEXT_V1/CHECK.py", "regressions"]]
    for command in commands:
        subprocess.run(command, cwd=ROOT, env=env, check=True, timeout=240)
    return {"original_tests": "PASS", "expected_identity_context": 28, "expected_stripe_security_business": [19, 9, 74]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("check", choices=("preservation", "baseline", "protocol", "guards", "regressions"))
    args = parser.parse_args()
    print(json.dumps({"check": args.check, "result": globals()[args.check]()}, ensure_ascii=False))

"""H50 frozen scope, source-locality and artifact checks. No guard implementation."""
from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import yaml

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
PARENT = TASK.parent / "H47_UCP_COMMERCE_APPLICABILITY_V1"
TASK_ID = TASK.name
MUTABLE = {"REPORT.md", "DESIGN.md", "RESULT.json", "ATTEMPT_LEDGER.json"}
EDITABLE_COPY = {"db.py", "services/checkout_service.py"}
NEW_COPY = {"services/execution_control.py"}
METHODS = {"__init__", "complete_checkout", "update_checkout", "cancel_checkout", "_process_payment"}
EXPECTED_CASES = ["G01_NORMAL", "G02_CHANGED", "G03_MISSING", "G04_FORGED", "G05_EXPIRED", "G06_REVOKED",
    "G07_REPLAY", "G08_UPDATE_WINS", "G09_CLAIM_WINS", "G10_CONCURRENT", "G11_CRASH_AFTER_PAYMENT",
    "G12_PRECOMMIT_FAILURE", "G13_ORDER_COMMIT_FAILURE", "G14_NO_CONTROL", "G15_CRASH_BEFORE_PAYMENT"]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(name):
    return json.loads((TASK / name).read_text(encoding="utf-8"))

def workspace():
    raw = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT)
    return {x.decode("utf-8") for x in raw.split(b"\0") if x}

def ast_definitions(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = {}
    def visit(parent, ancestors):
        for node in ast.iter_child_nodes(parent):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qualified = ".".join(ancestors + [node.name])
                if isinstance(node, ast.ClassDef):
                    found["class-header:"+qualified] = ast.dump(ast.ClassDef(name=node.name, bases=node.bases,
                        keywords=node.keywords, body=[], decorator_list=node.decorator_list), include_attributes=False)
                else:
                    found[qualified] = ast.dump(node, include_attributes=False)
                visit(node, ancestors + [node.name])
            else:
                visit(node, ancestors)
    visit(tree, [])
    return tree, found

def source_locality():
    manifest = read("SOURCE_COPY.json")
    for name, expected in manifest["files"].items():
        target = TASK / "merchant" / name
        assert target.is_file(), "missing source copy: " + name
        if name not in EDITABLE_COPY:
            assert sha(target) == expected, "unapproved copy change: " + name
    existing = {p.relative_to(TASK / "merchant").as_posix() for p in (TASK / "merchant").rglob("*")
                if p.is_file() and "__pycache__" not in p.parts}
    assert existing <= set(manifest["files"]) | NEW_COPY, "unlisted merchant file"
    for name in EDITABLE_COPY:
        _, original = ast_definitions(PARENT / "sources/ucp/rest/python/server" / name)
        _, modified = ast_definitions(TASK / "merchant" / name)
        for symbol, expected in original.items():
            if name == "services/checkout_service.py" and symbol in {"CheckoutService." + x for x in METHODS}:
                assert symbol in modified, "removed native method"
            else:
                assert modified.get(symbol) == expected, "rewritten unrelated definition: " + name + "#" + symbol
    service = ast.parse((TASK / "merchant/services/checkout_service.py").read_text(encoding="utf-8"))
    cls = next(n for n in service.body if isinstance(n, ast.ClassDef) and n.name == "CheckoutService")
    method = next(n for n in cls.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "complete_checkout")
    calls = {n.func.attr for n in ast.walk(method) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert {"_process_payment", "reserve_stock", "save_order", "save_checkout", "save_idempotency_record"} <= calls, "native completion business flow must remain in place"

def baseline():
    lock = read("BASELINE.json")
    current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    route = yaml.safe_load(current.split("```yaml", 1)[1].split("```", 1)[0])
    assert route["task_id"] == TASK_ID and route["task_kind"] == "one_off"
    assert route["project_map_revision"] == "2026-10-20-r79" and route["active_bottleneck_id"] == "B-17"
    assert route["hypothesis_id"] == "H-50"
    assert (route["state"], route["current_role"]) in {("CONTRACT_FROZEN", "Executor"), ("EXECUTING", "Executor"), ("READY_FOR_REVIEW", "Evaluator")}
    assert all(route["authorization_"+key] is False for key in ("api_call", "commit", "push", "history_rewrite"))
    assert hashlib.sha256(current.split("## Global position", 1)[1].encode()).hexdigest() == lock["current_history_sha256"]
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == lock["head"]
    for name, expected in lock["protected_files"].items():
        assert (ROOT / name).is_file() and sha(ROOT / name) == expected, "protected drift: " + name
    for name, expected in lock["frozen_files"].items():
        assert sha(TASK / name) == expected, "frozen drift: " + name
    prefix = TASK.relative_to(ROOT).as_posix() + "/"
    assert all(name.startswith(prefix) for name in workspace() - set(lock["workspace_files"])), "new file outside task"
    for p in TASK.rglob("*"):
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        name = p.relative_to(TASK).as_posix()
        assert name in lock["frozen_files"] or name in MUTABLE or name == "BASELINE.json" or name.startswith(("evidence/", "merchant/")), "unlisted task file: " + name
    env = json.loads((PARENT / "ENVIRONMENT.json").read_text(encoding="utf-8"))
    assert sys.version_info[:2] == (3, 12) and sys.prefix != sys.base_prefix
    for name, version in env["packages"].items():
        assert importlib.metadata.version(name) == version, "dependency drift: " + name
    source_locality()
    print(json.dumps({"baseline": "PASS", "protected_files": len(lock["protected_files"]), "frozen_files": len(lock["frozen_files"]), "source_locality": "PASS"}))

def validate_observations(value):
    assert value["schema"] == "h50-observations/v1" and value["mode"] == "guarded"
    cases = value["cases"]
    assert len(cases) == 15 and sorted(x["case"] for x in cases) == sorted(EXPECTED_CASES)
    assert all(x.get("passed") is True for x in cases)
    by_id = {x["case"]: x for x in cases}
    for name in ("G01_NORMAL", "G07_REPLAY", "G09_CLAIM_WINS", "G10_CONCURRENT", "G11_CRASH_AFTER_PAYMENT", "G13_ORDER_COMMIT_FAILURE"):
        assert len(by_id[name]["psp_calls"]) == 1, name
    for name in set(EXPECTED_CASES) - {"G01_NORMAL", "G07_REPLAY", "G09_CLAIM_WINS", "G10_CONCURRENT", "G11_CRASH_AFTER_PAYMENT", "G13_ORDER_COMMIT_FAILURE"}:
        assert len(by_id[name]["psp_calls"]) == 0, name
    for name in ("G01_NORMAL", "G07_REPLAY", "G09_CLAIM_WINS", "G10_CONCURRENT"):
        assert len(by_id[name]["state"]["orders"]) == 1, name
    for name in ("G08_UPDATE_WINS", "G09_CLAIM_WINS", "G10_CONCURRENT"):
        sessions = by_id[name]["sessions"]
        assert len({x["session_id"] for x in sessions}) >= 2
        assert len({x["connection_id"] for x in sessions}) >= 2, "independent database connections required"

def validate_result(value):
    assert value["schema"] == "h50-result/v1" and value["classification"] == "LOCAL_SERVICE_PROTOTYPE_ONLY"
    assert value["measurement_boundary"] == "LOCAL_NATIVE_SERVICE_METHODS_SYNTHETIC_TRUST_FAKE_PSP_NO_HTTP"
    assert value["local_guard_implemented"] is True
    assert all(value[key] is False for key in ("product_core_changed", "production_ready", "real_identity_verified",
        "cross_system_revocation_verified", "provider_verified", "customer_validated", "global_race_closed"))
    assert value["customer_demand"] == "UNKNOWN" and value["native_amount_binding_baseline"] == "NOT_OBSERVABLE"

def materials(native_path, guarded_path):
    validate_observations(json.loads((ROOT / guarded_path).read_text(encoding="utf-8")))
    native = json.loads((ROOT / native_path).read_text(encoding="utf-8"))
    assert native["mode"] == "native" and len(native["cases"]) == 2
    assert [x["stock"] for x in native["cases"]] == [4, 3]
    assert all(x["binding_observed"] is False for x in native["cases"])
    validate_result(read("RESULT.json"))
    ledger = read("ATTEMPT_LEDGER.json")
    assert 1 <= ledger["formal_l2_attempts"] <= 2 and 0 <= ledger["active_work_minutes"] <= 360
    assert all(ledger[x] == 0 for x in ("asgi_requests", "network_calls", "model_calls", "provider_calls", "external_runtime_calls"))
    for name in ("REPORT.md", "DESIGN.md"):
        assert len((TASK / name).read_text(encoding="utf-8").strip()) >= 250
    assert "SUBMITTED_FOR_REVIEW" in (TASK / "REPORT.md").read_text(encoding="utf-8")
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
    baseline()
    print("H50 native/guarded observations, declared scope, budget and source locality PASS; manual L3 source review remains required.")

def selftest():
    good = {"schema": "h50-result/v1", "classification": "LOCAL_SERVICE_PROTOTYPE_ONLY",
        "measurement_boundary": "LOCAL_NATIVE_SERVICE_METHODS_SYNTHETIC_TRUST_FAKE_PSP_NO_HTTP",
        "local_guard_implemented": True, "customer_demand": "UNKNOWN", "native_amount_binding_baseline": "NOT_OBSERVABLE",
        **{key: False for key in ("product_core_changed", "production_ready", "real_identity_verified",
            "cross_system_revocation_verified", "provider_verified", "customer_validated", "global_race_closed")}}
    validate_result(good)
    variants = []
    for key in ("production_ready", "provider_verified", "cross_system_revocation_verified", "global_race_closed"):
        bad = copy.deepcopy(good); bad[key] = True; variants.append(bad)
    bad = copy.deepcopy(good); bad["native_amount_binding_baseline"] = "VERIFIED"; variants.append(bad)
    rejected = 0
    for value in variants:
        try:
            validate_result(value)
        except AssertionError:
            rejected += 1
    assert rejected == 5
    paid = {"G01_NORMAL", "G07_REPLAY", "G09_CLAIM_WINS", "G10_CONCURRENT", "G11_CRASH_AFTER_PAYMENT", "G13_ORDER_COMMIT_FAILURE"}
    ordered = {"G01_NORMAL", "G07_REPLAY", "G09_CLAIM_WINS", "G10_CONCURRENT"}
    fixture = {"schema": "h50-observations/v1", "mode": "guarded", "cases": [
        {"case": name, "passed": True, "psp_calls": [{}] if name in paid else [],
         "state": {"orders": [{}] if name in ordered else []},
         "sessions": [{"session_id": 1, "connection_id": 1}, {"session_id": 2, "connection_id": 2}]}
        for name in EXPECTED_CASES]}
    validate_observations(fixture)
    broken = []
    value = copy.deepcopy(fixture); value["cases"].pop(); broken.append(value)
    value = copy.deepcopy(fixture); value["cases"][0]["passed"] = False; broken.append(value)
    value = copy.deepcopy(fixture); value["cases"][0]["psp_calls"] = []; broken.append(value)
    value = copy.deepcopy(fixture); value["cases"][0]["psp_calls"].append({}); broken.append(value)
    value = copy.deepcopy(fixture); value["cases"][9]["sessions"][1]["connection_id"] = 1; broken.append(value)
    observation_rejected = 0
    for value in broken:
        try:
            validate_observations(value)
        except AssertionError:
            observation_rejected += 1
    assert observation_rejected == 5
    print(json.dumps({"result_checker_positive": True, "overclaim_mutations_rejected": rejected,
        "observation_mutations_rejected": observation_rejected, "boundary": "CHECKER_SELFTEST_NOT_RUNTIME"}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["baseline", "materials", "selftest"])
    parser.add_argument("--native")
    parser.add_argument("--guarded")
    args = parser.parse_args()
    {"baseline": baseline, "selftest": selftest,
     "materials": lambda: materials(args.native, args.guarded)}[args.mode]()

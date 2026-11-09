"""Frozen packet protection and independently recomputed observation checks."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import yaml
from RUNTIME import TASK, ROOT, PARENT, bootstrap, preflight
bootstrap()
from FROZEN_TESTS import CASES, POSITIVE, check
from FIXTURES import keys, public, envelope, independent_materials, PAYEE

MUTABLE = {"merchant/services/checkout_service.py", "merchant/services/execution_control.py",
           "merchant/services/ap2_authorization.py", "REPORT.md", "RESULT.json", "ATTEMPT_LEDGER.json"}
FALSE_FLAGS = ["product_core_changed", "full_ucp_ap2_conformance", "jcs_conformance",
               "http_integration_verified", "real_identity_verified", "provider_verified",
               "production_ready", "customer_validated", "global_race_closed"]

def read(name):
    return json.loads((TASK / name).read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def workspace():
    return {x.decode("utf-8") for x in subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT).split(b"\0") if x}

def baseline():
    lock = read("BASELINE.json")
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == lock["head"]
    router = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    route = yaml.safe_load(router.split("```yaml", 1)[1].split("```", 1)[0])
    assert route["task_id"] == TASK.name and route["task_kind"] == "one_off"
    assert route["project_map_revision"] == "2026-10-31-r86" and route["active_bottleneck_id"] == "B-17"
    assert route["hypothesis_id"] == "H-53"
    assert (route["state"], route["current_role"]) in {("CONTRACT_FROZEN", "Executor"), ("EXECUTING", "Executor"), ("READY_FOR_REVIEW", "Evaluator")}
    assert all(route["authorization_" + k] is False for k in ("commit", "push", "history_rewrite", "api_call"))
    assert hashlib.sha256(router.split("## Global position", 1)[1].encode()).hexdigest() == lock["current_history_sha256"]
    for name, expected in lock["protected_files"].items(): assert sha(ROOT / name) == expected, name
    for name, expected in lock["frozen_files"].items(): assert sha(TASK / name) == expected, name
    assert all(x.startswith(TASK.relative_to(ROOT).as_posix() + "/") for x in workspace() - set(lock["workspace_files"]))
    for path in TASK.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            name = path.relative_to(TASK).as_posix()
            assert name in lock["frozen_files"] or name in MUTABLE or name == "BASELINE.json" or name.startswith("evidence/"), name
    preflight()
    print(json.dumps({"protected_files": len(lock["protected_files"]), "frozen_files": len(lock["frozen_files"])}))

def fixture():
    checkout = read("SAMPLE_CHECKOUT.json")
    registry = keys()
    value = envelope(checkout, "h53-fixture-only", registry)
    raw, payloads = independent_materials(value, public(registry), "h53-fixture-only")
    assert raw == checkout and len(payloads) == 2
    verified = payloads_by_type(payloads)
    assert value["projection"]["open_payment_mandate"] == verified["mandate.payment.open.1"]
    assert value["projection"]["payment_mandate"] == verified["mandate.payment.1"]
    assert {"id", "ucp", "currency", "line_items", "totals", "fulfillment"} <= set(raw)
    assert len([t for t in raw["totals"] if t["type"] == "total"]) == 1
    assert len(CASES) == 28 and len(set(CASES)) == 28 and len(POSITIVE) == 4
    assert all("d" not in key for key in public(registry).values())
    print(json.dumps({"preparation_only": True, "full_checkout_signature_smoke": "PASS", "future_cases": len(CASES), "merchant_execution": "NOT_RUN"}))

def implementation_scope():
    inherited = read("INHERITED_COPY.json")["files"]
    assert len(inherited) == 36
    for name, expected in inherited.items():
        if name not in MUTABLE: assert sha(TASK / name) == expected, name
    relative = "merchant/services/checkout_service.py"
    original = (PARENT / relative).read_text(encoding="utf-8")
    old = 'checkout_id, risk_signals.get("h50_confirmation_ref"), idempotency_key, request_hash\n'
    new = 'checkout_id, risk_signals.get("h50_confirmation_ref"), idempotency_key, request_hash,\n      authorization=risk_signals.get("h53_authorization")\n'
    assert original.count(old) == 1
    assert (TASK / relative).read_text(encoding="utf-8") == original.replace(old, new), "Only the frozen claim argument wiring may change"
    relative = "merchant/services/execution_control.py"
    a = ast.parse((PARENT / relative).read_text(encoding="utf-8"))
    b = ast.parse((TASK / relative).read_text(encoding="utf-8"))
    old_class = next(n for n in a.body if isinstance(n, ast.ClassDef) and n.name == "ExecutionControl")
    new_class = next(n for n in b.body if isinstance(n, ast.ClassDef) and n.name == "ExecutionControl")
    assert ast.dump(ast.Module(body=old_class.bases, type_ignores=[])) == ast.dump(ast.Module(body=new_class.bases, type_ignores=[]))
    allowed = {"__init__", "initialize", "claim"}
    assert {getattr(n, "name", None) for n in old_class.body} == {getattr(n, "name", None) for n in new_class.body}
    for old_node in old_class.body:
        if getattr(old_node, "name", None) not in allowed:
            new_node = next(n for n in new_class.body if getattr(n, "name", None) == getattr(old_node, "name", None))
            assert ast.dump(old_node) == ast.dump(new_node), getattr(old_node, "name", None)
    for old_node in a.body:
        if isinstance(old_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            new_node = next(n for n in b.body if getattr(n, "name", None) == old_node.name)
            assert ast.dump(old_node) == ast.dump(new_node), old_node.name
    ast.parse((TASK / "merchant/services/ap2_authorization.py").read_text(encoding="utf-8"))
    print("Implementation scope PASS; transactional authorization semantics require runtime and source review.")

def payloads_by_type(value):
    found = {}
    def walk(node):
        if isinstance(node, dict):
            if node.get("vct") in {"mandate.payment.open.1", "mandate.payment.1"}:
                assert node["vct"] not in found
                found[node["vct"]] = node
            for child in node.values(): walk(child)
        elif isinstance(node, list):
            for child in node: walk(child)
    walk(value)
    assert len(found) == 2
    return found

def observations(path):
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert value["schema"] == "h53-claim-consumer-observations/v1"
    assert value["boundary"] == "LOCAL_METHOD_EXACT_BYTES_SYNTHETIC_TRUST_FAKE_PSP"
    assert all(value[k] == 0 for k in ("network_calls", "asgi_requests", "real_payment_calls"))
    assert [row["case"] for row in value["cases"]] == CASES
    for row in value["cases"]:
        check(row)
        assert all("d" not in key for key in row["public_key_registry"].values())
        if row["case"] in POSITIVE:
            raw, verified = independent_materials(row["authorization"], row["public_key_registry"], row["confirmation_ref"])
            assert raw == row["raw_checkout_signed"]
            verified = payloads_by_type(verified)
            projection = row["authorization"]["projection"]
            assert projection["open_payment_mandate"] == verified["mandate.payment.open.1"]
            assert projection["payment_mandate"] == verified["mandate.payment.1"]
            terminal = verified["mandate.payment.1"]
            assert terminal["payee"]["id"] == PAYEE
            total = next(t["amount"] for t in raw["totals"] if t["type"] == "total")
            assert terminal["payment_amount"] == {"amount": total, "currency": raw["currency"]}
    print(json.dumps({"cases_checked": len(CASES), "merchant_payments": "SYNTHETIC_ONLY"}))

def result(value):
    assert value["schema"] == "h53-result/v1"
    assert value["classification"] == "LOCAL_AUTHORIZATION_CONSUMER_OBSERVED"
    assert all(value[k] is False for k in FALSE_FLAGS)
    assert value["customer_demand"] == "UNKNOWN" and value["remaining_gaps"]

def materials(path):
    baseline()
    implementation_scope()
    observations(path)
    result(read("RESULT.json"))
    ledger = read("ATTEMPT_LEDGER.json")
    assert 1 <= ledger["formal_l2_attempts"] <= 2 and 0 <= ledger["active_work_minutes"] <= 360
    assert 28 <= ledger["artifact_cases_run"] <= 280
    assert sum(run["cases_reserved"] for run in ledger["runs"]) == ledger["artifact_cases_run"]
    assert all(ledger[k] == 0 for k in ("network_calls", "asgi_requests", "model_calls", "provider_calls", "real_payment_calls", "packages_installed"))
    assert "SUBMITTED_FOR_REVIEW" in (TASK / "REPORT.md").read_text(encoding="utf-8")
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
    print("H53 materials PASS; task PASS remains Evaluator-only.")

def selftest():
    value = {"schema": "h53-result/v1", "classification": "LOCAL_AUTHORIZATION_CONSUMER_OBSERVED",
             "customer_demand": "UNKNOWN", "remaining_gaps": ["synthetic-only"], **{k: False for k in FALSE_FLAGS}}
    result(value)
    rejected = 0
    for key in FALSE_FLAGS:
        bad = copy.deepcopy(value)
        bad[key] = True
        try: result(bad)
        except AssertionError: rejected += 1
    assert rejected == len(FALSE_FLAGS)
    print(json.dumps({"overclaims_rejected": rejected, "purpose": "CHECKER_SELFTEST_ONLY"}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["baseline", "fixture", "scope", "observations", "materials", "selftest"])
    parser.add_argument("--observations")
    args = parser.parse_args()
    if args.mode in {"observations", "materials"}:
        assert args.observations
        (observations if args.mode == "observations" else materials)(args.observations)
    else:
        {"baseline": baseline, "fixture": fixture, "scope": implementation_scope, "selftest": selftest}[args.mode]()

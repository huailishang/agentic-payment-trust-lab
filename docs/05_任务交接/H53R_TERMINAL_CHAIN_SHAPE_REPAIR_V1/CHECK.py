"""Frozen single-file repair protection plus original and terminal-case oracles."""
import argparse
import ast
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import yaml
from RUNTIME import TASK, ROOT, bootstrap, preflight
bootstrap()
from FIXTURES import NOW, AUDIENCE
from jwcrypto.jwk import JWK
from ap2.sdk.mandate import MandateClient

PARENT = TASK.parent / "H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1"
spec = importlib.util.spec_from_file_location("h53r_original_material_checker", TASK / "sources/H53_CHECK.py")
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
CASES = ["S01_NORMAL_CONTROL", "S02_MISSING_TRUST_CONTEXT", "S03_CLAIM_COMMIT_ROLLBACK",
         "S04_REVERSED_MANDATE_TYPES", "S05_INTERMEDIATE_TAIL_WRONG_AUD", "S06_INTERMEDIATE_TAIL_WRONG_NONCE"]
MUTABLE = {"merchant/services/ap2_authorization.py", "REPORT.md", "RESULT.json", "ATTEMPT_LEDGER.json"}

def read(name): return json.loads((TASK / name).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def workspace():
    return {x.decode("utf-8") for x in subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT).split(b"\0") if x}

def baseline():
    lock = read("BASELINE.json")
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == lock["head"]
    text = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    route = yaml.safe_load(text.split("```yaml", 1)[1].split("```", 1)[0])
    assert route["task_id"] == TASK.name and route["task_kind"] == "repair"
    assert route["project_map_revision"] == "2026-10-31-r87" and route["hypothesis_id"] == "H-53R" and route["active_bottleneck_id"] == "B-17"
    assert (route["state"], route["current_role"]) in {("CONTRACT_FROZEN", "Executor"), ("EXECUTING", "Executor"), ("READY_FOR_REVIEW", "Evaluator")}
    assert all(route["authorization_" + k] is False for k in ("commit", "push", "history_rewrite", "api_call"))
    assert hashlib.sha256(text.split("## Global position", 1)[1].encode()).hexdigest() == lock["current_history_sha256"]
    for name, expected in lock["protected_files"].items(): assert sha(ROOT / name) == expected, name
    for name, expected in lock["frozen_files"].items(): assert sha(TASK / name) == expected, name
    prefix = TASK.relative_to(ROOT).as_posix() + "/"
    assert all(x.startswith(prefix) for x in workspace() - set(lock["workspace_files"]))
    for path in TASK.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            name = path.relative_to(TASK).as_posix()
            assert name in lock["frozen_files"] or name in MUTABLE or name == "BASELINE.json" or name.startswith("evidence/"), name
    preflight()
    print(json.dumps({"protected_files": len(lock["protected_files"]), "frozen_files": len(lock["frozen_files"])}))

def scope():
    manifest = read("SOURCE_COPY.json")["files"]
    names = [name for name in manifest if name.startswith("merchant/")]
    assert len(names) == 37
    for name in names:
        if name not in MUTABLE: assert sha(TASK / name) == manifest[name]["copy_sha256"], name
    ast.parse((TASK / "merchant/services/ap2_authorization.py").read_text(encoding="utf-8"))
    print(json.dumps({"immutable_merchant_files": 36, "mutable_implementation_files": 1}))

def tail_row(row):
    name = row["case"]
    assert name in CASES
    keys = row["public_key_registry"]
    assert all("d" not in key for key in keys.values())
    verified = MandateClient().verify(row["authorization"]["payment_token"], lambda _: JWK(**keys["user"]),
        expected_aud=AUDIENCE, expected_nonce="h53:" + row["confirmation_ref"], current_time=NOW, clock_skew_seconds=0)
    assert row["sdk"]["status"] == "VALID" and verified == row["sdk"]["verified_payloads"]
    expected = 1 if name == "S01_NORMAL_CONTROL" else 0
    state = row["state"]
    assert state["payment_calls"] == len(row["psp_calls"]) == len(state["orders"]) == expected, name
    assert len(state["attempts"]) == len(row["authorization_records"]) == expected, name
    if expected:
        assert row["result"]["ok"] and row["contract_satisfied"]
        token = row["authorization"]["payment_token"]
        assert row["authorization_records"][0]["token_sha256"] == hashlib.sha256(token.encode()).hexdigest()
    else:
        assert not row["result"]["ok"] and row["contract_satisfied"]
        assert state["inventory"][0]["quantity"] == 5
        if name != "S03_CLAIM_COMMIT_ROLLBACK": assert row["result"]["status"] in {400, 403, 409}
    if name == "S04_REVERSED_MANDATE_TYPES":
        assert [x.get("vct") for x in verified] == ["mandate.payment.1", "mandate.payment.open.1"]
    if name in {"S05_INTERMEDIATE_TAIL_WRONG_AUD", "S06_INTERMEDIATE_TAIL_WRONG_NONCE"}:
        piece = row["authorization"]["payment_token"].split("~~")[-1].split(".")[0]
        header = json.loads(base64.urlsafe_b64decode(piece + "=" * (-len(piece) % 4)))
        assert header["typ"] == "kb+sd-jwt+kb"
        assert "cnf" in verified[-1]
        if name.endswith("WRONG_AUD"): assert row["audience_supplied"] != AUDIENCE
        else: assert row["nonce_supplied"] != "h53:" + row["confirmation_ref"]

def tail(path):
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert value["schema"] == "h53r-terminal-cases/v1"
    assert all(value[k] == 0 for k in ("network_calls", "asgi_requests", "real_payment_calls"))
    assert [x["case"] for x in value["cases"]] == CASES
    for row in value["cases"]: tail_row(row)
    print(json.dumps({"terminal_cases_checked": 6, "independent_sdk_recomputed": 6}))

def checker_baseline():
    original = json.loads((PARENT / "evidence/review_20261031/INDEPENDENT_OBSERVATIONS.json").read_text(encoding="utf-8"))
    failures = []
    for row in original["cases"]:
        try: tail_row(row)
        except AssertionError: failures.append(row["case"])
    assert failures == CASES[3:]
    print(json.dumps({"parent_counterexamples_correctly_rejected": failures,
        "preparation_only": True, "repair_implementation_run": False}))

def result(value):
    assert value["schema"] == "h53r-result/v1" and value["classification"] == "LOCAL_TERMINAL_CHAIN_REPAIR_OBSERVED"
    assert all(value[k] is False for k in old.FALSE_FLAGS)
    assert value["customer_demand"] == "UNKNOWN" and value["remaining_gaps"]

def materials(original, terminal):
    baseline()
    scope()
    old.observations(original)
    tail(terminal)
    result(read("RESULT.json"))
    ledger = read("ATTEMPT_LEDGER.json")
    assert 1 <= ledger["formal_l2_attempts"] <= 2 and 0 <= ledger["active_work_minutes"] <= 120
    assert 34 <= ledger["artifact_cases_run"] <= 272
    assert sum(x["cases_reserved"] for x in ledger["runs"]) == ledger["artifact_cases_run"]
    assert all(ledger[k] == 0 for k in ("network_calls", "asgi_requests", "model_calls", "provider_calls", "real_payment_calls", "packages_installed"))
    assert "SUBMITTED_FOR_REVIEW" in (TASK / "REPORT.md").read_text(encoding="utf-8")
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
    print("Repair materials PASS; final acceptance remains Evaluator-only.")

def selftest():
    good = {"schema": "h53r-result/v1", "classification": "LOCAL_TERMINAL_CHAIN_REPAIR_OBSERVED",
            "customer_demand": "UNKNOWN", "remaining_gaps": ["synthetic-only"], **{k: False for k in old.FALSE_FLAGS}}
    result(good)
    count = 0
    for key in old.FALSE_FLAGS:
        bad = copy.deepcopy(good)
        bad[key] = True
        try: result(bad)
        except AssertionError: count += 1
    assert count == len(old.FALSE_FLAGS)
    checker_baseline()
    print(json.dumps({"overclaim_mutations_rejected": count}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["baseline", "scope", "fixture", "original", "tail", "observations", "materials", "selftest", "checker-baseline"])
    parser.add_argument("--observations")
    parser.add_argument("--tail")
    args = parser.parse_args()
    if args.mode == "original": old.observations(args.observations)
    elif args.mode == "tail": tail(args.tail)
    elif args.mode == "observations":
        old.observations(args.observations)
        tail(args.tail)
    elif args.mode == "materials": materials(args.observations, args.tail)
    else: {"baseline": baseline, "scope": scope, "fixture": old.fixture,
           "selftest": selftest, "checker-baseline": checker_baseline}[args.mode]()

"""Frozen independent observation/material/scope assertions, not a product guard."""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import yaml
from RUNTIME import TASK, ROOT, bootstrap, preflight
from REFERENCE import recompute

CASES = [
    "Q01_NORMAL", "Q02_CHECKOUT_TAMPERED", "Q03_CHECKOUT_REBOUND_PAYMENT_STALE",
    "Q04_PROJECTED_AMOUNT_CHANGED", "Q05_PROJECTED_PAYEE_CHANGED", "Q06_PROJECTED_CURRENCY_CHANGED",
    "Q07_SELF_ROOT_SUBSTITUTION", "Q08_CONSENT_ABSENT", "Q09_EXPIRED_TOKEN",
    "Q10_WRONG_AUDIENCE", "Q11_REPLAY_WITH_SEEN_ID", "Q12_MISSING_CONTEXT"]
REQUIREMENTS = [
    "VERSION_SCHEMA", "CAPABILITY_NEGOTIATION", "MERCHANT_SIGNATURE", "FULL_CHECKOUT_JCS",
    "TRUSTED_CONSENT_ISSUER", "DELEGATION_KEY_BINDING", "AMOUNT_CURRENCY_PAYEE",
    "VERIFIED_PAYLOAD_LINEAGE", "REPLAY_REVOCATION_ORDER", "EXECUTION_SNAPSHOT_CLAIM",
    "PROVIDER_REFERENCE_QUERY", "TRACE_CONSUMPTION"]
FALSE_FLAGS = ["product_core_changed", "native_ap2_ready", "full_ucp_ap2_conformance",
               "production_ready", "real_identity_verified", "provider_verified",
               "customer_validated", "global_race_closed", "end_to_end_authorization_verified"]
MUTABLE = {"PROBES.py", "SOURCE_AUDIT.md", "COMPATIBILITY.json", "TRUST_BOUNDARY.md",
           "READINESS_MATRIX.json", "NEXT_BOUNDARY.md", "RESULT.json", "REPORT.md", "ATTEMPT_LEDGER.json"}
def read(name):
    return json.loads((TASK / name).read_text(encoding="utf-8"))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def baseline():
    lock = read("BASELINE.json")
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == lock["head"]
    route_text = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    route = yaml.safe_load(route_text.split("```yaml", 1)[1].split("```", 1)[0])
    assert route["task_id"] == TASK.name and route["task_kind"] == "one_off"
    assert route["project_map_revision"] == "2026-10-30-r84" and route["active_bottleneck_id"] == "B-17"
    assert route["hypothesis_id"] == "H-52"
    assert (route["state"], route["current_role"]) in {
        ("CONTRACT_FROZEN", "Executor"), ("EXECUTING", "Executor"), ("READY_FOR_REVIEW", "Evaluator")}
    assert all(route["authorization_" + k] is False for k in ("commit", "push", "history_rewrite", "api_call"))
    assert hashlib.sha256(route_text.split("## Global position", 1)[1].encode()).hexdigest() == lock["current_history_sha256"]
    for name, expected in lock["protected_files"].items():
        assert sha(ROOT / name) == expected, name
    for name, expected in lock["frozen_files"].items():
        assert sha(TASK / name) == expected, name
    current_files = set(subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT).decode("utf-8").split("\0")) - {""}
    prefix = TASK.relative_to(ROOT).as_posix() + "/"
    assert all(name.startswith(prefix) for name in current_files - set(lock["workspace_files"]))
    for path in TASK.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            name = path.relative_to(TASK).as_posix()
            assert name in lock["frozen_files"] or name in MUTABLE or name == "BASELINE.json" or name.startswith("evidence/"), name
    preflight()
    print(json.dumps({"protected_files": len(lock["protected_files"]), "frozen_files": len(lock["frozen_files"])}))

def result(value):
    assert value["schema"] == "h52-readiness-result/v1"
    assert value["classification"] in {"READY_FOR_BOUNDED_IMPLEMENTATION", "MERCHANT_CONTRACT_CHANGE_REQUIRED", "STOP_NO_JUSTIFIED_INTEGRATION"}
    assert all(value[k] is False for k in FALSE_FLAGS)
    assert value["customer_demand"] == "UNKNOWN"
    assert value["evidence_boundary"] == "OFFLINE_SYNTHETIC_SIGNED_ARTIFACTS_NO_MERCHANT_EXECUTION"
    assert value["remaining_gaps"] and value["one_next_action"]

def observations(value):
    assert value["schema"] == "h52-signed-artifact-observations/v1"
    assert value["boundary"] == "OFFLINE_SYNTHETIC_SIGNED_ARTIFACTS_NO_MERCHANT_EXECUTION"
    assert value["encoding_scope"] == "FIXED_ASCII_INTEGER_FIXTURE_NOT_GENERAL_JCS"
    assert all(value[k] == 0 for k in ("network_calls", "asgi_requests", "payment_calls"))
    registry = value["public_key_registry"]
    assert set(registry) == {"trusted_user", "delegate_agent", "merchant", "attacker"}
    for role, key in registry.items():
        assert key["kty"] == "EC" and key["crv"] == "P-256" and "d" not in key
        assert key["kid"] == "h52-" + role
    assert len({(key["x"], key["y"]) for key in registry.values()}) == 4
    cases = value["cases"]
    assert [c["case"] for c in cases] == CASES
    by_id = {c["case"]: c for c in cases}
    normal = by_id["Q01_NORMAL"]
    for case in cases:
        assert case["crypto_inputs"]["expected_nonce"] == "h52-checkout-once"
        assert case["crypto_inputs"]["trusted_root_role"] == "trusted_user"
        assert case["crypto_inputs"]["current_time"] == (1800007200 if case["case"] == "Q09_EXPIRED_TOKEN" else 1800000000)
        assert case["crypto_inputs"]["expected_aud"] == ("h52-wrong-merchant" if case["case"] == "Q10_WRONG_AUDIENCE" else "h52-merchant")
        actual = recompute(case, registry)
        assert case["observed"] == actual, case["case"]
        assert not case["observed"]["user_consent_assessed_by_these_functions"]
        assert not case["observed"]["merchant_execution_assessed"]
    assert normal["observed"]["crypto_status"] == "VALID"
    assert normal["observed"]["merchant_signature_status"] == "VALID"
    assert normal["observed"]["boundary_status"] == "VALID" and normal["observed"]["canonical_decision"] == "ALLOW"
    assert normal["observed"]["projection_matches_verified_payload"] is True
    payment = normal["boundary_input"]["payment_mandate"]
    assert payment["payment_amount"] == {"amount": 1000, "currency": "USD"}
    assert payment["payee"]["id"] == "h52-merchant" and normal["consent_present"] is True
    assert normal["seen_request_ids"] == []
    for ident in CASES[1:]:
        c = by_id[ident]
        if ident != "Q07_SELF_ROOT_SUBSTITUTION":
            assert c["crypto_inputs"]["token"] == normal["crypto_inputs"]["token"]
        assert c["consent_present"] is (ident != "Q08_CONSENT_ABSENT")
        expected_seen = [payment["transaction_id"]] if ident == "Q11_REPLAY_WITH_SEEN_ID" else []
        assert c["seen_request_ids"] == expected_seen
        expected_snapshot = copy.deepcopy(normal["boundary_input"])
        if ident == "Q02_CHECKOUT_TAMPERED":
            jwt = c["boundary_input"]["checkout_mandate"]["checkout_jwt"]
            assert jwt != expected_snapshot["checkout_mandate"]["checkout_jwt"]
            expected_snapshot["checkout_mandate"]["checkout_jwt"] = jwt
            assert c["observed"]["merchant_signature_status"] == "INVALID"
        elif ident == "Q03_CHECKOUT_REBOUND_PAYMENT_STALE":
            checkout = c["boundary_input"]["checkout_mandate"]
            assert checkout["checkout_jwt"] != expected_snapshot["checkout_mandate"]["checkout_jwt"]
            assert checkout["checkout_hash"] == base64.urlsafe_b64encode(hashlib.sha256(checkout["checkout_jwt"].encode()).digest()).decode().rstrip("=")
            expected_snapshot["checkout_mandate"] = checkout
            assert c["observed"]["merchant_signature_status"] == "VALID"
        elif ident == "Q04_PROJECTED_AMOUNT_CHANGED":
            expected_snapshot["payment_mandate"]["payment_amount"]["amount"] = 1500
        elif ident == "Q05_PROJECTED_PAYEE_CHANGED":
            expected_snapshot["payment_mandate"]["payee"]["id"] = "h52-other-merchant"
        elif ident == "Q06_PROJECTED_CURRENCY_CHANGED":
            expected_snapshot["payment_mandate"]["payment_amount"]["currency"] = "EUR"
        elif ident == "Q12_MISSING_CONTEXT":
            expected_snapshot["experiment_context"] = {}
        assert c["boundary_input"] == expected_snapshot, ident
    attacker = by_id["Q07_SELF_ROOT_SUBSTITUTION"]
    assert attacker["observed"]["crypto_status"] == "INVALID"
    diag = copy.deepcopy(attacker)
    diag["crypto_inputs"]["trusted_root_role"] = "attacker"
    assert attacker["self_root_diagnostic"] == recompute(diag, registry)
    assert attacker["self_root_diagnostic"]["crypto_status"] == "VALID"
    print(json.dumps({"signed_artifact_cases_recomputed": len(cases), "merchant_execution": "NOT_MEASURED"}))

def mappings():
    source = read("SOURCE_MANIFEST.json")
    for item in source["sources"]:
        assert sha(ROOT / item["html"]) == item["html_sha256"]
        assert sha(ROOT / item["text"]) == item["text_sha256"]
    compatibility = read("COMPATIBILITY.json")
    assert compatibility["schema"] == "h52-compatibility/v1"
    assert compatibility["merchant_ucp_version"] == "2026-04-08"
    assert compatibility["reference_ucp_version"] == "2026-08-25"
    assert compatibility["merchant_ap2_advertised"] is False
    assert compatibility["auto_upgrade_performed"] is False
    matrix = read("READINESS_MATRIX.json")
    assert matrix["schema"] == "h52-readiness-matrix/v1"
    assert {r["id"] for r in matrix["rows"]} == set(REQUIREMENTS) and len(matrix["rows"]) == 12
    for row in matrix["rows"]:
        assert row["status"] in {"MEASURED_LOCAL", "SOURCE_ONLY", "GAP", "NOT_OBSERVABLE"}
        assert row["next_action"] in {"REUSE", "BRIDGE", "MERCHANT_CHANGE", "DEFER"}
        assert len(row["claim"].strip()) >= 15 and row["references"]
        assert row["owner"] and row["evidence_origin"] in {"PRODUCT_RUNTIME", "SDK_RUNTIME", "MERCHANT_SOURCE", "SPECIFICATION", "MIXED"}
        for ref in row["references"]:
            path = (ROOT / ref["path"]).resolve()
            assert path.is_relative_to(ROOT) and path.is_file()
            lines = path.read_text(encoding="utf-8").splitlines()
            start, end = ref["start"], ref["end"]
            assert 1 <= start <= end <= len(lines)
            assert ref["anchor"] in "\n".join(lines[start-1:end])
    for name in ("SOURCE_AUDIT.md", "TRUST_BOUNDARY.md", "NEXT_BOUNDARY.md"):
        assert len((TASK / name).read_text(encoding="utf-8").strip()) >= 500
    print("Source/compatibility/12 obligation rows structurally valid; truth requires Evaluator source review.")

def materials(observation_path):
    baseline()
    mappings()
    observations(json.loads((ROOT / observation_path).read_text(encoding="utf-8")))
    result(read("RESULT.json"))
    ledger = read("ATTEMPT_LEDGER.json")
    assert 1 <= ledger["formal_l2_attempts"] <= 3 and 0 <= ledger["active_work_minutes"] <= 360
    assert 12 <= ledger["artifact_cases_run"] <= 144
    assert all(ledger[k] == 0 for k in ("network_calls", "model_calls", "provider_calls", "asgi_requests", "payment_calls"))
    assert "SUBMITTED_FOR_REVIEW" in (TASK / "REPORT.md").read_text(encoding="utf-8")
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
    print("H52 materials PASS; no end-to-end capability verdict implied")

def selftest():
    good = {"schema": "h52-readiness-result/v1", "classification": "MERCHANT_CONTRACT_CHANGE_REQUIRED",
        "customer_demand": "UNKNOWN", "evidence_boundary": "OFFLINE_SYNTHETIC_SIGNED_ARTIFACTS_NO_MERCHANT_EXECUTION",
        "remaining_gaps": ["synthetic-selftest"], "one_next_action": "synthetic-selftest",
        **{k: False for k in FALSE_FLAGS}}
    result(good)
    count = 0
    for key in FALSE_FLAGS:
        bad = copy.deepcopy(good)
        bad[key] = True
        try:
            result(bad)
        except AssertionError:
            count += 1
    assert count == len(FALSE_FLAGS)
    for bad in ({}, {"schema": "h52-signed-artifact-observations/v1"}):
        try:
            observations(bad)
        except (AssertionError, KeyError):
            count += 1
    assert count == len(FALSE_FLAGS) + 2
    print(json.dumps({"boundary": "CHECKER_SELFTEST_NOT_EXECUTOR_MEASUREMENT", "mutations_rejected": count}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["baseline", "mappings", "observations", "materials", "selftest"])
    parser.add_argument("--observations")
    args = parser.parse_args()
    bootstrap()
    if args.mode in ("materials", "observations"):
        assert args.observations
        materials(args.observations) if args.mode == "materials" else observations(json.loads((ROOT / args.observations).read_text(encoding="utf-8")))
    else:
        globals()[args.mode]()

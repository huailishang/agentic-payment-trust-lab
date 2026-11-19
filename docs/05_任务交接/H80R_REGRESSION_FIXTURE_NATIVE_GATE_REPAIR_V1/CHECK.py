"""Evaluator-frozen offline repair oracles; no product implementation here."""
import argparse
import ast
import base64
from dataclasses import asdict, replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType, SimpleNamespace
import unittest

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
sys.path.insert(0, str(ROOT / "src"))
FIELDS = ("verified_agent_ref", "verified_provider_ref", "verified_executor_instance_ref")
CONTEXT = ("h76-agent", "h76-provider", "h76-executor")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def route():
    import yaml
    data = yaml.safe_load((ROOT / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0])
    need(data["task_id"] == P.name and data["active_bottleneck_id"] == "B-23" and data["hypothesis_id"] == "H-80", "wrong task/strategy")
    need((data["current_role"], data["state"]) in {("Executor", "CONTRACT_FROZEN"), ("Executor", "EXECUTING"), ("Evaluator", "READY_FOR_REVIEW")}, "wrong role/state")
    for key, value in data.items():
        if key.startswith("authorization_"):
            need(value is (key == "authorization_reference_read"), "authority expanded: " + key)
    return data


def fixture_ast():
    rel = "tests/trusted_execution/test_payment_binding.py"
    before = ast.parse((P / "references/before_h80" / rel).read_text(encoding="utf-8"))
    after = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
    added = []
    for node in ast.walk(after):
        if isinstance(node, ast.FunctionDef) and node.name == "test_verified_identity_uses_same_payment_policy_as_bound_identity":
            for call in ast.walk(node):
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "CredentialPossessionVerificationFact":
                    for item in list(call.keywords):
                        if item.arg in FIELDS:
                            expected = {FIELDS[0]: "agent-1", FIELDS[1]: "offline-provider-1", FIELDS[2]: "executor-1"}[item.arg]
                            need(isinstance(item.value, ast.Constant) and item.value.value == expected, "fixture context must match original binding")
                            added.append(item.arg)
                            call.keywords.remove(item)
    need(len(added) in (0, 3) and len(added) == len(set(added)), "partial/duplicate fixture change")
    need(ast.dump(before, include_attributes=False) == ast.dump(after, include_attributes=False), "original payment test changed beyond three context kwargs")


def product_scope():
    for rel, allowed in {
        "src/agentic_payment_experiment/trusted_execution/credential_possession.py": {"CredentialPossessionVerificationFact", "verify_x509_svid_credential_possession", "_fact"},
        "src/agentic_payment_experiment/trusted_execution/execution_facts.py": {"_CredentialPossessionFactLike", "verify_agent_executor_identity"},
    }.items():
        before = ast.parse((P / "references/before_h80" / rel).read_text(encoding="utf-8"))
        after = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        old_nodes = {node.name: node for node in before.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in allowed}
        need(set(old_nodes) == allowed, "frozen scope symbols missing")
        replaced = []
        for index, node in enumerate(after.body):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in allowed:
                replaced.append(node.name)
                if node.name == "CredentialPossessionVerificationFact":
                    original = old_nodes[node.name]
                    existing = [item for item in node.body if not (isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id in FIELDS)]
                    need(ast.dump(ast.Module(body=existing, type_ignores=[]), include_attributes=False) == ast.dump(ast.Module(body=original.body, type_ignores=[]), include_attributes=False), "old dataclass fields changed")
                after.body[index] = old_nodes[node.name]
        need(sorted(replaced) == sorted(allowed), "scope symbol deleted/duplicated")
        need(ast.dump(before, include_attributes=False) == ast.dump(after, include_attributes=False), "product changed outside frozen context seam: " + rel)


def new_test_scope():
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


def preservation():
    route()
    baseline = read(P / "BASELINE.json")
    need(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == baseline["head"], "HEAD drift")
    for rel, digest in baseline["files"].items():
        need(sha(ROOT / rel) == digest, "protected drift: " + rel)
    for rel, digest in baseline["common_protected"].items():
        need(sha(ROOT.parent / "localagent-common" / rel) == digest, "common tool drift")
    for rel, digest in read(P / "FREEZE.json")["files"].items():
        need(sha(P / rel) == digest, "frozen repair oracle drift: " + rel)
    inventory = set(filter(None, subprocess.check_output(["git", "ls-files", "-c", "-o", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0")))
    prefix = P.relative_to(ROOT).as_posix() + "/"
    for rel in inventory - set(baseline["existing_inventory"]):
        need(rel in baseline["mutable"] or rel.startswith(prefix), "new file outside repair: " + rel)
    fixture_ast()
    product_scope()
    new_test_scope()
    accepted = P / "evidence/ACCEPTED.json"
    if accepted.exists():
        for rel, digest in read(accepted)["files"].items():
            need(sha(ROOT / rel) == digest, "accepted snapshot drift: " + rel)
    return {"protected_files": len(baseline["files"]), "historical_aliases": baseline["historical_aliases"], "fixture_assertions_unchanged": True}


def load_fixture():
    path = ROOT / "tests/trusted_execution/test_payment_binding.py"
    spec = importlib.util.spec_from_file_location("h80_original_payment_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PaymentExecutionBindingTests


def proof_values():
    lock = read(P / "SOURCE.json")
    source = ROOT / lock["source_directory"]
    for rel, digest in lock["public_inputs"].items():
        need(sha(source / rel) == digest, "H78 public proof drift")
    data = read(source / "RESULT.json")
    payload = (source / "payload.bin").read_bytes()
    context = dict(line.split("=", 1) for line in payload.decode("utf-8").splitlines()[1:])
    need(tuple(context[key] for key in ("agent", "provider", "executor")) == CONTEXT, "source signed context")
    return source, data, dict(leaf_svid_pem=(source / "leaf.pem").read_bytes(), trusted_ca_pem=(source / "root.pem").read_bytes(), expected_trust_domain="h76.test", expected_agent_ref=CONTEXT[0], expected_provider_ref=CONTEXT[1], expected_executor_instance_ref=CONTEXT[2], credential_ref="h79:captured-h78:" + data["run_id"], challenge_payload=payload, challenge_signature=base64.b64decode((source / "signature.b64").read_bytes().strip(), validate=True), nonce_ref=data["nonce"], issued_at_epoch=data["issued_at_epoch"], observed_at_epoch=data["observed_at_epoch"], max_age_seconds=300)


def behavior():
    route()
    from cryptography import x509
    from agentic_payment_experiment.trusted_execution.credential_possession import CredentialPossessionVerificationFact, verify_x509_svid_credential_possession
    from agentic_payment_experiment.trusted_execution.execution_facts import VerificationStatus
    source, data, values = proof_values()
    fact = verify_x509_svid_credential_possession(**values)
    need(fact.status.name == "VALID" and all((fact.credential_valid, fact.subject_binding_valid, fact.proof_of_possession_valid, fact.freshness_valid)) and not fact.replay_detected, "actual historical positive")
    need(tuple(getattr(fact, key, None) for key in FIELDS) == CONTEXT, "verified signed context missing or fabricated")
    print(json.dumps({"source_run": data["run_id"], "time_mode": "CAPTURED_OBSERVATION_REPLAY_NOT_CURRENT_AUTHENTICATION", "source_subject": fact.subject_ref, "verified_context": CONTEXT}), flush=True)
    fixture = load_fixture()
    rows = []

    def observe(case_id, proof, *, agent=CONTEXT[0], provider=CONTEXT[1], executor=CONTEXT[2], credential=None, status="active", request_agent=None, assurance="BOUND", identity_status="VALID", callbacks=1, reason=None, require_binding=True):
        case = fixture()
        case.setUp()
        ref = credential or values["credential_ref"]
        case.mandate = replace(case.mandate, expected_agent_id=agent)
        case.request = replace(case.request, agent_id=request_agent or agent)
        case.payment = replace(case.payment, agent_ref=agent)
        case.identity = replace(case.identity, agent_id=agent, provider=provider, executor_instance_id=executor, credential_ref=ref, status=status)
        outcome, calls = case.execute(identity=case.identity, provider_ref=provider, executor_ref=executor, credential_ref=ref, credential_possession_fact=proof)
        row = {"case_id": case_id, "consumer": {"agent": agent, "request_agent": request_agent or agent, "provider": provider, "executor": executor, "credential_ref": ref, "status": status}, "proof_status": getattr(getattr(proof, "status", None), "name", None), "proof_subject": getattr(proof, "subject_ref", None), "verified_context": {key: getattr(proof, key, None) for key in FIELDS}, "identity_status": outcome.identity_fact.status.name, "assurance": outcome.identity_fact.assurance_level.name, "identity_reasons": list(outcome.identity_fact.reason_codes), "decision": outcome.decision.name, "callbacks": len(calls), "binding": outcome.binding_fact.status.name, "context_policy": outcome.context_policy_fact.status.name, "gate_reasons": list(outcome.gate_reason_codes)}
        print(json.dumps(row), flush=True)
        rows.append(row)
        need(row["identity_status"] == identity_status and row["assurance"] == assurance and len(calls) == callbacks, "consumer oracle: " + case_id)
        if require_binding:
            need(row["binding"] == row["context_policy"] == "VALID", "confounded consumer: " + case_id)
        if callbacks == 1:
            need(row["decision"] == "ALLOW", "existing BOUND/VERIFIED payment policy changed")
        if reason:
            need(reason in row["identity_reasons"], "missing diagnostic: " + case_id)

    observe("M01", fact, assurance="VERIFIED")
    observe("M02", fact, agent="h79-other-agent", reason="credential_possession_context_mismatch")
    observe("M03", fact, provider="h79-other-provider", reason="credential_possession_context_mismatch")
    observe("M04", fact, executor="h79-other-executor", reason="credential_possession_context_mismatch")
    observe("M05", fact, credential=values["credential_ref"] + ":different", reason="credential_possession_ref_mismatch")
    observe("M06", fact, status="revoked", assurance="DECLARED", identity_status="INVALID", callbacks=0)

    legacy_values = {key: value for key, value in asdict(fact).items() if key not in FIELDS}
    legacy = CredentialPossessionVerificationFact(**legacy_values)
    need(all(getattr(legacy, key) is None for key in FIELDS), "legacy constructor defaults")
    observe("LEGACY_DATACLASS", legacy, reason="credential_possession_context_missing")
    observe("LEGACY_DUCK", SimpleNamespace(**legacy_values), reason="credential_possession_context_missing")
    for key in FIELDS:
        for value in (None, " "):
            observe("MISSING_" + key + ("_NONE" if value is None else "_BLANK"), replace(fact, **{key: value}), reason="credential_possession_context_missing")
    observe("NO_PROOF", None)
    observe("INACTIVE", fact, status="inactive", assurance="DECLARED", identity_status="INVALID", callbacks=0)
    observe("INVALID_BASE_REQUEST", fact, request_agent="different-request-agent", assurance="DECLARED", identity_status="INVALID", callbacks=0, require_binding=False)

    leaf = x509.load_pem_x509_certificate(values["leaf_svid_pem"])
    root = x509.load_pem_x509_certificate(values["trusted_ca_pem"])
    expiry = int(leaf.not_valid_after_utc.timestamp()) + 1
    stale = data["issued_at_epoch"] + 301
    need(leaf.not_valid_before_utc.timestamp() <= stale <= leaf.not_valid_after_utc.timestamp() and root.not_valid_before_utc.timestamp() <= expiry <= root.not_valid_after_utc.timestamp(), "negative temporal isolation")
    vector = read(ROOT / "docs/05_任务交接/P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1/evaluator_fixtures/X509_SVID_POSSESSION_VECTOR.json")
    oracles = read(ROOT / "docs/05_任务交接/H76_SPIRE_ISSUED_WORKLOAD_POSSESSION_MEASUREMENT_V1/NEGATIVE_ORACLES.json")["cases"]
    variants = {"wrong_root": {"trusted_ca_pem": vector["untrusted_ca_pem"]}, "wrong_trust_domain": {"expected_trust_domain": "wrong.h76.test"}, "wrong_agent": {"expected_agent_ref": "wrong-agent"}, "wrong_executor": {"expected_executor_instance_ref": "wrong-executor"}, "wrong_provider": {"expected_provider_ref": "wrong-provider"}, "wrong_nonce_binding": {"nonce_ref": "different-nonce"}, "damaged_signature": {"challenge_signature": b"damaged-signature"}, "nonce_replay": {"consumed_nonce_refs": (data["nonce"],)}, "stale_challenge": {"observed_at_epoch": stale}, "expired_leaf_observation": {"observed_at_epoch": expiry}}
    for name, override in variants.items():
        invalid = verify_x509_svid_credential_possession(**{**values, **override})
        need(invalid.status.name != "VALID" and oracles[name] in invalid.reason_codes, "original crypto negative: " + name)
        need(all(getattr(invalid, key, None) is None for key in FIELDS), "unverified context exported as verified: " + name)
        observe("CRYPTO_" + name, invalid, reason=oracles[name])
    # Synthetic consumer guards isolate each pre-existing promotion prerequisite.
    for key, value in {"status": VerificationStatus.INVALID, "credential_valid": False, "subject_binding_valid": False, "proof_of_possession_valid": False, "freshness_valid": False, "replay_detected": True}.items():
        observe("SYNTHETIC_GUARD_" + key, replace(fact, **{key: value}))
    return {"consumer_observations": len(rows), "original_crypto_negatives": 10, "actual_payment_calls": 0, "new_issuer_runs": 0, "source_is_current_authentication": False}


def regressions():
    route()
    need(sys.platform == "win32" and os.name == "nt", "native Windows only")
    os.environ.update(PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
    print(json.dumps({"execution_platform": sys.platform, "native_environment_set_before_first_suite": True}), flush=True)
    need((ROOT / "tests/trusted_execution/test_credential_context_consumption.py").is_file(), "durable regression file missing")
    tests_package = ModuleType("tests")
    tests_package.__path__ = [str(ROOT / "tests")]
    sys.modules["tests"] = tests_package

    def suite(names, count=None):
        tests = unittest.defaultTestLoader.loadTestsFromNames(names)
        actual = tests.countTestCases()
        if count is not None:
            need(actual == count, "original test count changed")
        result = unittest.TextTestRunner(verbosity=1).run(tests)
        need(result.wasSuccessful() and not result.skipped and not result.expectedFailures and not result.unexpectedSuccesses, "regression failure/skip")
        return actual

    suite(["tests.trusted_execution.test_credential_possession", "tests.trusted_execution.test_identity_assurance", "tests.test_stripe_authority_context"], 28)
    suite(["tests.trusted_execution.test_payment_binding"], 18)
    added = suite(["tests.trusted_execution.test_credential_context_consumption"])
    need(added == 6, "all original six new regressions required")
    env = os.environ.copy()
    base = P / "runtime/userbase"
    shim = base / ("Python" + str(sys.version_info.major) + str(sys.version_info.minor)) / "site-packages/tests"
    shim.mkdir(parents=True, exist_ok=True)
    (shim / "__init__.py").write_text("__path__ = [" + repr(str(ROOT / "tests")) + "]\n", encoding="utf-8")
    env.update(PYTHONUSERBASE=str(base), PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([sys.executable, "-B", "docs/05_任务交接/H74_DURABLE_AUTHORITY_CONTEXT_V1/CHECK.py", "regressions"], cwd=ROOT, env=env, check=True, timeout=240)
    parent = P.parent / "H78_FRESH_SPIRE_UID_POSSESSION_CLOSURE_V1"
    for name, extra in (("TASK_TESTS.py", []), ("PROTOCOL_CHECK.py", ["protocol"]), ("OFFLINE_TESTS.py", [])):
        subprocess.run([sys.executable, "-B", str(parent / name), *extra], cwd=ROOT, env=env, check=True, timeout=240)
    return {"original_regressions": 130, "original_payment_binding": 18, "new_tests": added, "original_source_guards": 16, "protocol_positive": 4, "protocol_negative": 21, "original_offline_gates": 8, "parent_physical_source_runs": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("check", choices=("preservation", "behavior", "regressions"))
    print(json.dumps(globals()[parser.parse_args().check](), ensure_ascii=False))

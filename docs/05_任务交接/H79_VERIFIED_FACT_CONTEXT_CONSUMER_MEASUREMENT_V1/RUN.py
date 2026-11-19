"""Frozen offline consumer measurement using captured H78 public proof only."""
import argparse
import base64
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
sys.path.insert(0, str(ROOT / "src"))


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


def authority(phase):
    import yaml
    route = yaml.safe_load((ROOT / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0])
    states = {("Executor", "CONTRACT_FROZEN"), ("Executor", "EXECUTING")} if phase == "executor" else {("Evaluator", "READY_FOR_REVIEW")}
    need(route["task_id"] == P.name and (route["current_role"], route["state"]) in states, "measurement route mismatch")
    for key in ("authorization_existing_wsl", "authorization_local_service", "authorization_ephemeral_test_credentials", "authorization_api_call", "authorization_install", "authorization_test_payments", "authorization_commit", "authorization_push"):
        need(route.get(key) is False, "offline measurement authority expanded")
    if phase == "evaluator":
        for rel, digest in read(P / "evidence/ACCEPTED.json")["files"].items():
            need(sha(ROOT / rel) == digest, "accepted input drift")


def measurement(phase):
    from agentic_payment_experiment.trusted_execution.credential_possession import verify_x509_svid_credential_possession
    matrix = read(P / "SCENARIOS.json")
    source_lock = read(P / "SOURCE.json")
    source = ROOT / source_lock["source_directory"]
    for rel, digest in source_lock["public_inputs"].items():
        need(sha(source / rel) == digest, "captured H78 source drift")
    data = read(source / "RESULT.json")
    context = dict(line.split("=", 1) for line in (source / "payload.bin").read_text(encoding="utf-8").splitlines()[1:])
    need(context["agent"] == "h76-agent" and context["provider"] == "h76-provider" and context["executor"] == "h76-executor", "fixed H78 context mismatch")
    credential_ref = "h79:captured-h78:" + data["run_id"]
    fact = verify_x509_svid_credential_possession(leaf_svid_pem=(source / "leaf.pem").read_bytes(), trusted_ca_pem=(source / "root.pem").read_bytes(), expected_trust_domain="h76.test", expected_agent_ref=context["agent"], expected_provider_ref=context["provider"], expected_executor_instance_ref=context["executor"], credential_ref=credential_ref, challenge_payload=(source / "payload.bin").read_bytes(), challenge_signature=base64.b64decode((source / "signature.b64").read_bytes().strip(), validate=True), nonce_ref=data["nonce"], issued_at_epoch=data["issued_at_epoch"], observed_at_epoch=data["observed_at_epoch"], max_age_seconds=300)
    need(fact.status.name == "VALID" and all((fact.credential_valid, fact.subject_binding_valid, fact.proof_of_possession_valid, fact.freshness_valid)) and not fact.replay_detected, "captured historical fact not valid at recorded observation")
    fixture_module = load(ROOT / "tests/trusted_execution/test_payment_binding.py", "h79_payment_fixture")
    results = []
    stop = False
    for item in matrix["cases"]:
        if stop:
            results.append({"case_id": item["id"], "status": "NOT_RUN_AFTER_COUNTEREXAMPLE"})
            continue
        case = fixture_module.PaymentExecutionBindingTests()
        case.setUp()
        agent, provider, executor = item["agent"], item["provider"], item["executor"]
        reference = credential_ref if item["credential_ref"] == "SOURCE" else credential_ref + ":different"
        case.mandate = replace(case.mandate, expected_agent_id=agent)
        case.request = replace(case.request, agent_id=agent)
        case.payment = replace(case.payment, agent_ref=agent)
        case.identity = replace(case.identity, agent_id=agent, provider=provider, executor_instance_id=executor, credential_ref=reference, status=item["identity_status"])
        outcome, calls = case.execute(identity=case.identity, provider_ref=provider, executor_ref=executor, credential_ref=reference, credential_possession_fact=fact)
        context_match = (agent, provider, executor) == (context["agent"], context["provider"], context["executor"])
        contradiction = not context_match and outcome.identity_fact.assurance_level.name == "VERIFIED"
        revoked_violation = item["identity_status"] == "revoked" and (outcome.identity_fact.status.name != "INVALID" or bool(calls))
        if item["id"] == "M01":
            need(outcome.identity_fact.assurance_level.name == "VERIFIED" and len(calls) == 1, "coherent-source positive control failed")
        need(outcome.binding_fact.status.name == "VALID" and outcome.context_policy_fact.status.name == "VALID", "measurement confounded by payment/context binding")
        results.append({"case_id": item["id"], "status": "OBSERVED", "consumer_input": item, "source_context": {key: context[key] for key in ("agent", "provider", "executor")}, "source_context_matches_consumer": context_match, "credential_ref_matches": reference == fact.credential_ref, "proof_status": fact.status.name, "proof_subject_ref": fact.subject_ref, "proof_credential_ref": fact.credential_ref, "identity_status": outcome.identity_fact.status.name, "assurance": outcome.identity_fact.assurance_level.name, "decision": outcome.decision.name, "callback_count": len(calls), "binding_status": outcome.binding_fact.status.name, "context_policy_status": outcome.context_policy_fact.status.name, "identity_reasons": list(outcome.identity_fact.reason_codes), "gate_reasons": list(outcome.gate_reason_codes), "context_counterexample": contradiction, "revoked_guard_counterexample": revoked_violation})
        stop = contradiction or revoked_violation
    return {"schema": "h79-captured-fact-consumer-measurement/v1", "phase": phase, "source_run_id": data["run_id"], "source_observed_at_epoch": data["observed_at_epoch"], "time_mode": "CAPTURED_OBSERVATION_REPLAY_NOT_CURRENT_AUTHENTICATION", "matrix_sha256": sha(P / "SCENARIOS.json"), "source_lock_sha256": sha(P / "SOURCE.json"), "source_fact_status": fact.status.name, "cases": results, "stopped_on_counterexample": stop, "actual_payment_calls": 0, "new_credentials": 0, "new_issuer_runs": 0, "network_calls": 0, "callback_meaning": "isolated list append from original test fixture; no provider API"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("executor", "evaluator"), required=True)
    phase = parser.parse_args().phase
    authority(phase)
    import CHECK
    CHECK.preservation()
    out = P / "evidence" / (phase + "_measurement")
    if out.exists():
        result = read(out / "RESULT.json")
        need(result["matrix_sha256"] == sha(P / "SCENARIOS.json") and result["source_lock_sha256"] == sha(P / "SOURCE.json"), "cannot reuse drifted measurement")
        print(json.dumps({"reused_immutable_measurement": True, "result": result}, ensure_ascii=False))
        return
    out.mkdir(parents=True, exist_ok=False)
    result = measurement(phase)
    with (out / "RESULT.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

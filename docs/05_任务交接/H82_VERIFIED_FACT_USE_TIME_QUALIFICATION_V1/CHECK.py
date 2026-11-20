#!/usr/bin/env python
"""H82 frozen offline, read-only evidence qualification checker.

All observations are local/synthetic. Never claims a current issuer/status lookup,
a real certificate revocation event, production payment, or live authentication.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import replace
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys

TASK_DIR = Path(__file__).resolve().parent
REPO = TASK_DIR.parents[2]
LOCK = json.loads((TASK_DIR / "SOURCE_LOCK.json").read_text(encoding="utf-8"))
SRC = REPO / "src"


def emit(kind, data):
    print(json.dumps({"task_id": LOCK["task_id"], "check": kind, "result": "PASS", **data},
                     ensure_ascii=False, sort_keys=True))


def fail(message):
    raise AssertionError(message)


def check_runtime():
    # H82 A1 2026-11-20: runtime platform is not a trust assertion.
    # Preserve all original data, behavioral, and regression checks.
    if sys.version_info < (3, 11):
        fail("H82 requires Python >= 3.11 in an existing local environment")


def preservation():
    issues = []
    digests = {}
    for rel, expected in LOCK["entries"].items():
        path = REPO / rel
        if not path.is_file():
            issues.append({"file": rel, "problem": "missing"})
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        digests[rel] = digest
        if digest != expected:
            issues.append({"file": rel, "problem": "hash_mismatch", "expected": expected,
                           "actual": digest})
    if issues:
        fail(json.dumps({"preservation_errors": issues}, ensure_ascii=False))
    emit("preservation", {"locked_file_count": len(digests),
                          "locked_sha256": digests,
                          "previous_h81_submission_sha256": LOCK["previous_h81_submission_sha256"]})


def function_parameters(file, name):
    tree = ast.parse((SRC / file).read_text(encoding="utf-8"))
    funcs = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
             and node.name == name]
    if len(funcs) != 1:
        fail("unexpected function count: " + file + ":" + name)
    return tuple(arg.arg for arg in (*funcs[0].args.posonlyargs, *funcs[0].args.args,
                                     *funcs[0].args.kwonlyargs))


def inventory():
    verifier = "agentic_payment_experiment/trusted_execution/credential_possession.py"
    consumer = "agentic_payment_experiment/trusted_execution/execution_facts.py"
    gate = "agentic_payment_experiment/payment_execution.py"
    signed = "agentic_payment_experiment/trusted_execution/signed_instruction.py"
    verified = function_parameters(verifier, "verify_x509_svid_credential_possession")
    consumed = function_parameters(consumer, "verify_agent_executor_identity")
    payment = function_parameters(gate, "execute_with_payment_binding_gate")
    signed_args = function_parameters(signed, "verify_es256_compact_jws_signed_instruction")
    assert "observed_at_epoch" in verified
    assert "max_age_seconds" in verified
    assert "consumed_nonce_refs" in verified
    assert "credential_possession_fact" in consumed and "credential_possession_fact" in payment
    assert "current_credential_ref" in consumed and "current_credential_ref" in payment
    assert "observed_at_epoch" in signed_args and "expires_at_epoch" in signed_args
    assert "use_time_epoch" not in consumed and "use_time_epoch" not in payment
    assert "observed_at_epoch" not in consumed and "observed_at_epoch" not in payment
    credential_source = (SRC / verifier).read_text(encoding="utf-8")
    consumer_source = (SRC / consumer).read_text(encoding="utf-8")
    payment_source = (SRC / gate).read_text(encoding="utf-8")
    for label, passed in (
        ("x509_cert_validity_at_observed", "_certificate_valid_at(" in credential_source),
        ("challenge_freshness", "credential_possession_challenge_stale" in credential_source),
        ("nonce_replay", "credential_possession_replay_detected" in credential_source),
        ("revoked_status", "identity_status_revoked" in consumer_source),
        ("verified_context", "credential_possession_context_mismatch" in consumer_source),
        ("bound_payment_allowed", "IdentityAssuranceLevel.BOUND" in payment_source),
        ("verified_payment_allowed", "IdentityAssuranceLevel.VERIFIED" in payment_source),
    ):
        if not passed:
            fail("expected existing capability disappeared: " + label)
    emit("inventory", {"capture_time": "OBSERVED_AT_PARAMETER_VERIFIED",
                        "consumer_use_time_input": "NOT_EXPOSED_IN_SCOPED_INTERFACE",
                        "payment_use_time_input": "NOT_EXPOSED_IN_SCOPED_INTERFACE",
                        "identity_status": "SUPPLIED_BY_CALLER",
                        "revocation_authority": "UNKNOWN_NO_LOOKUP_PROVEN",
                        "rotation_authority": "UNKNOWN_NO_LOOKUP_PROVEN",
                        "upstream_refresh": "UNKNOWN_OUTSIDE_SCOPED_FUNCTIONS",
                        "existing_controls": ["cert_validity", "challenge_freshness",
                                              "nonce_replay", "revoked_identity_flag",
                                              "credential_ref_mismatch", "agent_provider_executor_context",
                                              "signed_instruction_expiry"],
                        "note": "Interface inspection only; no production system claim."})


def probe(phase):
    sys.path.insert(0, str(SRC))
    from agentic_payment_experiment.models import AgentIdentity
    from agentic_payment_experiment.trusted_execution.credential_possession import (
        CredentialPossessionVerificationFact)
    from agentic_payment_experiment.trusted_execution.execution_facts import (
        VerificationStatus, IdentityAssuranceLevel, verify_agent_executor_identity)

    at = 1_760_000_000
    # Intentionally synthetically populated fact, NEVER a cryptographically
    # validated new credential. Tests only consumer interface responsibilities.
    credential = CredentialPossessionVerificationFact(
        status=VerificationStatus.VALID,
        reason_codes=("credential_possession_verified",),
        credential_format="X509-SVID",
        credential_ref="credential-h82-offline",
        subject_ref="spiffe://offline.test/agent/agent-h82/executor/executor-h82",
        trust_domain_ref="offline.test",
        leaf_certificate_sha256="synthetic-not-an-authenticated-certificate",
        credential_valid=True, subject_binding_valid=True,
        proof_of_possession_valid=True, freshness_valid=True,
        replay_detected=False, nonce_ref="nonce-h82-synthetic",
        challenge_payload_sha256="synthetic", issued_at_epoch=at - 1,
        observed_at_epoch=at, max_age_seconds=300,
        verified_agent_ref="agent-h82",
        verified_provider_ref="provider-h82",
        verified_executor_instance_ref="executor-h82")
    identity = AgentIdentity(agent_id="agent-h82", provider="provider-h82",
                             executor_instance_id="executor-h82",
                             status="active", credential_ref="credential-h82-offline")
    def consume(*, proof=credential, agent_identity=identity, current_ref="credential-h82-offline"):
        return verify_agent_executor_identity(
            authorized_agent_ref="agent-h82", request_agent_ref="agent-h82",
            execution_agent_ref="agent-h82", identity=agent_identity,
            current_provider_ref="provider-h82",
            current_executor_instance_ref="executor-h82",
            current_credential_ref=current_ref, credential_possession_fact=proof)
    baseline = consume()
    assert baseline.status is VerificationStatus.VALID
    assert baseline.assurance_level is IdentityAssuranceLevel.VERIFIED

    # use_time is external test metadata; NOT injected into the function.
    # This establishes an interface limitation, NOT a demonstrated live exploit.
    proposed_use_time = at + (86_400 if phase == "executor" else 172_800)
    same_inputs = consume()
    assert same_inputs.assurance_level is IdentityAssuranceLevel.VERIFIED
    assert same_inputs == baseline

    controls = {
        "identity_revoked": consume(agent_identity=replace(identity, status="revoked")),
        "credential_ref_rotated": consume(
            agent_identity=replace(identity, credential_ref="credential-h82-rotated"),
            current_ref="credential-h82-rotated"),
        "fact_freshness_false": consume(proof=replace(credential, freshness_valid=False)),
        "cross_agent_context": consume(proof=replace(credential, verified_agent_ref="other-agent")),
    }
    assert controls["identity_revoked"].status is VerificationStatus.INVALID
    assert controls["identity_revoked"].assurance_level is IdentityAssuranceLevel.DECLARED
    for name in ("credential_ref_rotated", "fact_freshness_false", "cross_agent_context"):
        assert controls[name].assurance_level is IdentityAssuranceLevel.BOUND, name

    emit("probe", {"phase": phase, "synthetic_fact": True,
                   "cryptographically_authenticated": False,
                   "observed_at_epoch": at, "hypothetical_use_time_epoch": proposed_use_time,
                   "time_shift_injected_into_consumer": False,
                   "unchanged_consumed_fact": "VERIFIED_TO_VERIFIED",
                   "control_outcomes": {k: {"status": v.status.value,
                                             "assurance_level": v.assurance_level.value,
                                             "reason_codes": list(v.reason_codes)}
                                        for k, v in controls.items()},
                   "verified_at_current_time": "NOT_JUDGEABLE",
                   "actual_revocation_or_rotation_status": "UNKNOWN",
                   "payment_callback_executed": False,
                   "claim": "An external time label alone does not alter the current consumer input."})


def regressions():
    targets = [
        "test_credential_context_consumption.py",
        "test_credential_possession.py",
        "test_identity_assurance.py",
        "test_payment_binding.py",
        "test_signed_instruction_es256.py",
    ]
    results = []
    for target in targets:
        command = [sys.executable, "-B", "-m", "unittest", "discover",
                   "-s", str(REPO / "tests" / "trusted_execution"), "-p", target, "-v"]
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
        completed = subprocess.run(command, cwd=REPO, env=env,
                                   capture_output=True, text=True, timeout=100)
        item = {"module": target, "exit_code": completed.returncode,
                "stdout": completed.stdout[-20000:], "stderr": completed.stderr[-20000:]}
        results.append(item)
        if completed.returncode != 0:
            print(json.dumps({"regressions": results}, ensure_ascii=False))
            fail("frozen regression failed: " + target)
    emit("regressions", {"suites": results, "note": "Original tests only, no edit or skip."})


def qualification():
    # B-24 tests availability of current authority, not invented live status.
    inventory()
    emit("qualification", {"historical_credential_controls": "IMPLEMENTED_IN_SCOPED_CODE",
                           "static_consumer_use_time_recheck": "NOT_EXPOSED",
                           "current_revoke_rotate_authority": "UNKNOWN",
                           "trusted_use_time_source": "UNKNOWN",
                           "upstream_responsibility": "NOT_JUDGEABLE_FROM_SCOPED_CODE",
                           "real_world_security_conclusion": "NOT_JUDGEABLE",
                           "incremental_product_gain": "NONE_MEASURED",
                           "next_decision": "STOP_UNSUPPORTED_LIVE_CLAIMS_AND_RECORD_REQUIRED_INPUTS",
                           "minimum_additional_evidence": [
                               "documented owner of fresh identity fact at payment gate",
                               "trustworthy use-time or fresh re-verification invocation",
                               "issuer revocation/rotation state source with validity semantics",
                               "policy required assurance level at payment boundary"
                           ]})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preservation", "inventory", "probe",
                                         "regressions", "qualification"))
    parser.add_argument("--phase", choices=("executor", "evaluator"), default="executor")
    options = parser.parse_args()
    check_runtime()
    if options.mode != "preservation":
        preservation()
    {"preservation": preservation, "inventory": inventory, "probe": lambda: probe(options.phase),
     "regressions": regressions, "qualification": qualification}[options.mode]()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"task_id": LOCK["task_id"], "result": "FAIL",
                          "exception": type(exc).__name__, "detail": str(exc)},
                         ensure_ascii=False))
        raise

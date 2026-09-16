from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agentic_payment_experiment.models import AgentIdentity
from agentic_payment_experiment.trusted_execution import (
    IdentityAssuranceLevel,
    verify_agent_executor_identity,
    verify_x509_svid_credential_possession,
)


SCHEMA = "p3-x509-svid-credential-possession-capability/v1"


def _digest(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _run_case(vector: dict, case: dict) -> dict:
    challenge = vector["challenge"]
    trusted_ca_pem = vector["trusted_ca_pem"]
    expected_executor = vector["expected_executor_instance_ref"]
    signature = base64.b64decode(challenge["signature_b64"])
    observed_at = challenge["observed_at_epoch"]
    consumed: set[str] = set()

    mutation = case["mutation"]
    if mutation == "USE_UNTRUSTED_CA":
        trusted_ca_pem = vector["untrusted_ca_pem"]
    elif mutation == "EXPECTED_EXECUTOR_OTHER":
        expected_executor = "executor-other"
    elif mutation == "REMOVE_SIGNATURE":
        signature = None
    elif mutation == "TAMPER_SIGNATURE":
        signature = signature[:-1] + bytes([signature[-1] ^ 0x01])
    elif mutation == "MARK_NONCE_CONSUMED":
        consumed.add(challenge["nonce_ref"])
    elif mutation == "OBSERVED_AFTER_TTL":
        observed_at = challenge["issued_at_epoch"] + challenge["max_age_seconds"] + 1
    elif mutation != "NONE":
        raise ValueError(f"unsupported mutation: {mutation}")

    credential_fact = verify_x509_svid_credential_possession(
        leaf_svid_pem=vector["leaf_svid_pem"],
        trusted_ca_pem=trusted_ca_pem,
        expected_trust_domain=vector["trust_domain"],
        expected_agent_ref=vector["expected_agent_ref"],
        expected_provider_ref=vector["expected_provider_ref"],
        expected_executor_instance_ref=expected_executor,
        credential_ref=vector["credential_ref"],
        challenge_payload=base64.b64decode(challenge["payload_b64"]),
        challenge_signature=signature,
        nonce_ref=challenge["nonce_ref"],
        issued_at_epoch=challenge["issued_at_epoch"],
        observed_at_epoch=observed_at,
        max_age_seconds=challenge["max_age_seconds"],
        consumed_nonce_refs=consumed,
    )

    identity = AgentIdentity(
        agent_id=vector["expected_agent_ref"],
        provider=vector["expected_provider_ref"],
        executor_instance_id=vector["expected_executor_instance_ref"],
        status="active",
        credential_ref=vector["credential_ref"],
    )
    identity_fact = verify_agent_executor_identity(
        authorized_agent_ref=vector["expected_agent_ref"],
        request_agent_ref=vector["expected_agent_ref"],
        execution_agent_ref=vector["expected_agent_ref"],
        identity=identity,
        current_provider_ref=vector["expected_provider_ref"],
        current_executor_instance_ref=vector["expected_executor_instance_ref"],
        current_credential_ref=vector["credential_ref"],
        credential_possession_fact=credential_fact,
    )

    return {
        "case_id": case["case_id"],
        "mutation": mutation,
        "credential_status": credential_fact.status.value,
        "identity_status": identity_fact.status.value,
        "assurance_level": identity_fact.assurance_level.value,
        "reason_codes": list(identity_fact.reason_codes),
        "credential_reason_codes": list(credential_fact.reason_codes),
        "four_condition_flags": {
            "credential_valid": credential_fact.credential_valid,
            "subject_binding_valid": credential_fact.subject_binding_valid,
            "proof_of_possession_valid": credential_fact.proof_of_possession_valid,
            "freshness_valid": credential_fact.freshness_valid,
            "replay_detected": credential_fact.replay_detected,
        },
        "credential_ref": credential_fact.credential_ref,
        "subject_ref": credential_fact.subject_ref,
        "trust_domain_ref": credential_fact.trust_domain_ref,
        "leaf_certificate_sha256": credential_fact.leaf_certificate_sha256,
        "nonce_ref": credential_fact.nonce_ref,
        "observed_at_epoch": credential_fact.observed_at_epoch,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vector", required=True)
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    vector = json.loads(Path(args.vector).read_text(encoding="utf-8"))
    matrix = json.loads(Path(args.matrix).read_text(encoding="utf-8"))
    if args.repeat <= 0:
        raise ValueError("repeat must be positive")

    repeat_results: list[list[dict]] = []
    repeat_digests: list[str] = []
    for _ in range(args.repeat):
        cases = [_run_case(vector, case) for case in matrix["cases"]]
        repeat_results.append(cases)
        repeat_digests.append(_digest(cases))

    if len(set(repeat_digests)) != 1:
        raise AssertionError(f"non-deterministic repeat digests: {repeat_digests}")
    cases = repeat_results[0]

    expected = {case["case_id"]: case for case in matrix["cases"]}
    for item in cases:
        frozen = expected[item["case_id"]]
        if item["credential_status"] != frozen["expected_status"]:
            raise AssertionError(
                f"{item['case_id']}: credential status {item['credential_status']} != {frozen['expected_status']}"
            )
        if item["assurance_level"] != frozen["expected_assurance"]:
            raise AssertionError(
                f"{item['case_id']}: assurance {item['assurance_level']} != {frozen['expected_assurance']}"
            )
        if frozen["expected_reason"] not in item["reason_codes"]:
            raise AssertionError(
                f"{item['case_id']}: missing expected reason {frozen['expected_reason']}"
            )

    legacy_identity = AgentIdentity(
        agent_id=vector["expected_agent_ref"],
        provider=vector["expected_provider_ref"],
        executor_instance_id=vector["expected_executor_instance_ref"],
        status="active",
        credential_ref=vector["credential_ref"],
    )
    legacy = verify_agent_executor_identity(
        authorized_agent_ref=vector["expected_agent_ref"],
        request_agent_ref=vector["expected_agent_ref"],
        execution_agent_ref=vector["expected_agent_ref"],
        identity=legacy_identity,
        current_provider_ref=vector["expected_provider_ref"],
        current_executor_instance_ref=vector["expected_executor_instance_ref"],
        current_credential_ref=vector["credential_ref"],
    )
    if legacy.assurance_level is not IdentityAssuranceLevel.BOUND:
        raise AssertionError("legacy credential-ref-only path must remain BOUND")

    verified_count = sum(item["assurance_level"] == "VERIFIED" for item in cases)
    if verified_count != 1:
        raise AssertionError(f"expected exactly one VERIFIED case, got {verified_count}")

    result = {
        "schema": SCHEMA,
        "vector_schema": vector.get("schema"),
        "matrix_schema": matrix.get("schema"),
        "repeat": args.repeat,
        "repeat_digests": repeat_digests,
        "deterministic": True,
        "verified_cases_before": 0,
        "verified_cases_after": verified_count,
        "legacy_credential_ref_only_assurance": legacy.assurance_level.value,
        "cases": cases,
        "guardrails": {
            "credential_ref_alone_never_verified": True,
            "signed_instruction_validity_not_identity_verification": True,
            "payment_allow_not_implied": True,
            "network_calls": 0,
            "real_payment": 0,
            "production_credentials": 0,
            "persisted_private_keys": 0,
        },
        "residual_risks": [
            "This is a bounded synthetic single-root/direct-leaf profile.",
            "It is not full RFC 5280 path validation or full SPIFFE/SPIRE conformance.",
            "It is not production authentication, legal identity proof, or regulatory compliance.",
            "No production credential, trust bundle, network service, or real transaction is used.",
        ],
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"PASS: {len(cases)}/{len(matrix['cases'])} frozen cases; "
        f"VERIFIED 0->{verified_count}; repeat={args.repeat}; digest={repeat_digests[0]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

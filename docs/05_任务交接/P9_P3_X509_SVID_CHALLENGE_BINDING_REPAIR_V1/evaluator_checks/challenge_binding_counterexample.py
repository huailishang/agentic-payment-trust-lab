from __future__ import annotations

import base64
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from agentic_payment_experiment.trusted_execution import (  # noqa: E402
    VerificationStatus,
    verify_x509_svid_credential_possession,
)

VECTOR = ROOT / "docs/05_任务交接/P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1/evaluator_fixtures/X509_SVID_POSSESSION_VECTOR.json"


def call(vector: dict, **overrides):
    c = vector["challenge"]
    values = {
        "leaf_svid_pem": vector["leaf_svid_pem"],
        "trusted_ca_pem": vector["trusted_ca_pem"],
        "expected_trust_domain": vector["trust_domain"],
        "expected_agent_ref": vector["expected_agent_ref"],
        "expected_executor_instance_ref": vector["expected_executor_instance_ref"],
        "expected_provider_ref": vector["expected_provider_ref"],
        "credential_ref": vector["credential_ref"],
        "challenge_payload": base64.b64decode(c["payload_b64"]),
        "challenge_signature": base64.b64decode(c["signature_b64"]),
        "nonce_ref": c["nonce_ref"],
        "issued_at_epoch": c["issued_at_epoch"],
        "observed_at_epoch": c["observed_at_epoch"],
        "max_age_seconds": c["max_age_seconds"],
        "consumed_nonce_refs": (),
    }
    values.update(overrides)
    return verify_x509_svid_credential_possession(**values)


def assert_rejected(name: str, fact) -> None:
    if fact.status is VerificationStatus.VALID and "credential_possession_verified" in fact.reason_codes:
        raise AssertionError(f"{name}: stale/relabelled signed challenge incorrectly VERIFIED")
    if "credential_possession_challenge_binding_mismatch" not in fact.reason_codes:
        raise AssertionError(f"{name}: expected challenge binding mismatch, got {fact.reason_codes!r}")


def main() -> int:
    vector = json.loads(VECTOR.read_text(encoding="utf-8"))
    c = vector["challenge"]

    # Original signed bytes/signature are retained, but trusted metadata is relabelled.
    assert_rejected(
        "nonce_and_time_relabel",
        call(
            vector,
            consumed_nonce_refs=(c["nonce_ref"],),
            nonce_ref="nonce-attacker-fresh-label",
            issued_at_epoch=c["issued_at_epoch"] + 120,
            observed_at_epoch=c["issued_at_epoch"] + 121,
        ),
    )
    assert_rejected("nonce_relabel", call(vector, nonce_ref="nonce-other"))
    assert_rejected("issued_at_relabel", call(vector, issued_at_epoch=c["issued_at_epoch"] + 1))
    assert_rejected("agent_context_relabel", call(vector, expected_agent_ref="agent-other"))
    assert_rejected("executor_context_relabel", call(vector, expected_executor_instance_ref="executor-other"))
    assert_rejected("provider_context_relabel", call(vector, expected_provider_ref="provider-other"))

    print("PASS: signed challenge cryptographically binds nonce/agent/provider/executor/issued_at; metadata relabel attacks fail closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

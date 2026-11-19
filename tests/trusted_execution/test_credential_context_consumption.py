"""H80 regression: verified possession must bind to the consuming identity context."""
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agentic_payment_experiment.models import AgentIdentity
from agentic_payment_experiment.trusted_execution.credential_possession import (
    CredentialPossessionVerificationFact,
)
from agentic_payment_experiment.trusted_execution.execution_facts import (
    IdentityAssuranceLevel,
    VerificationStatus,
    verify_agent_executor_identity,
)


class CredentialContextConsumptionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.identity = AgentIdentity(
            agent_id="agent-1",
            provider="provider-1",
            executor_instance_id="executor-1",
            status="active",
            credential_ref="credential-1",
        )
        self.possession = CredentialPossessionVerificationFact(
            status=VerificationStatus.VALID,
            reason_codes=("credential_possession_verified",),
            credential_format="X509-SVID",
            credential_ref="credential-1",
            subject_ref="spiffe://offline.test/agent/agent-1/executor/executor-1",
            trust_domain_ref="offline.test",
            leaf_certificate_sha256="offline-fixture",
            credential_valid=True,
            subject_binding_valid=True,
            proof_of_possession_valid=True,
            freshness_valid=True,
            replay_detected=False,
            nonce_ref="nonce-fixture",
            challenge_payload_sha256="digest-fixture",
            issued_at_epoch=1,
            observed_at_epoch=2,
            max_age_seconds=300,
            verified_agent_ref="agent-1",
            verified_provider_ref="provider-1",
            verified_executor_instance_ref="executor-1",
        )

    def consume(self, proof=None, **overrides):
        values = {
            "authorized_agent_ref": "agent-1",
            "request_agent_ref": "agent-1",
            "execution_agent_ref": "agent-1",
            "identity": self.identity,
            "current_provider_ref": "provider-1",
            "current_executor_instance_ref": "executor-1",
            "current_credential_ref": "credential-1",
            "credential_possession_fact": self.possession if proof is None else proof,
        }
        values.update(overrides)
        return verify_agent_executor_identity(**values)

    def test_exact_verified_context_promotes_and_keeps_existing_reason(self):
        result = self.consume()
        self.assertEqual(VerificationStatus.VALID, result.status)
        self.assertEqual(IdentityAssuranceLevel.VERIFIED, result.assurance_level)
        self.assertIn("credential_possession_verified", result.reason_codes)

    def test_cross_context_never_promotes_even_if_consumer_is_self_consistent(self):
        cases = (
            ("agent", "verified_agent_ref", "other-agent"),
            ("provider", "verified_provider_ref", "other-provider"),
            ("executor", "verified_executor_instance_ref", "other-executor"),
        )
        for name, field, other in cases:
            with self.subTest(name=name):
                proof = replace(self.possession, **{field: other})
                result = self.consume(proof=proof)
                self.assertEqual(VerificationStatus.VALID, result.status)
                self.assertEqual(IdentityAssuranceLevel.BOUND, result.assurance_level)
                self.assertIn("credential_possession_context_mismatch", result.reason_codes)

    def test_missing_blank_or_legacy_verified_context_cannot_promote(self):
        keys = ("verified_agent_ref", "verified_provider_ref", "verified_executor_instance_ref")
        for field in keys:
            for missing in (None, " "):
                with self.subTest(field=field, missing=missing):
                    result = self.consume(proof=replace(self.possession, **{field: missing}))
                    self.assertEqual(IdentityAssuranceLevel.BOUND, result.assurance_level)
                    self.assertIn("credential_possession_context_missing", result.reason_codes)

        old_fields = {
            key: value for key, value in vars(self.possession).items() if key not in keys
        }
        old_constructor = CredentialPossessionVerificationFact(**old_fields)
        self.assertTrue(all(getattr(old_constructor, key) is None for key in keys))
        legacy_duck = SimpleNamespace(**old_fields)
        for proof in (old_constructor, legacy_duck):
            with self.subTest(type=type(proof).__name__):
                result = self.consume(proof=proof)
                self.assertEqual(IdentityAssuranceLevel.BOUND, result.assurance_level)
                self.assertIn("credential_possession_context_missing", result.reason_codes)

    def test_existing_credential_reference_precedence_is_preserved(self):
        result = self.consume(current_credential_ref="different-credential", identity=replace(self.identity, credential_ref="different-credential"))
        self.assertEqual(IdentityAssuranceLevel.BOUND, result.assurance_level)
        self.assertIn("credential_possession_ref_mismatch", result.reason_codes)
        self.assertNotIn("credential_possession_context_mismatch", result.reason_codes)

    def test_unsatisfied_original_guards_do_not_promote(self):
        overrides = {
            "status": VerificationStatus.INVALID,
            "credential_valid": False,
            "subject_binding_valid": False,
            "proof_of_possession_valid": False,
            "freshness_valid": False,
            "replay_detected": True,
        }
        for field, value in overrides.items():
            with self.subTest(guard=field):
                result = self.consume(proof=replace(self.possession, **{field: value}))
                self.assertEqual(IdentityAssuranceLevel.BOUND, result.assurance_level)
                self.assertNotIn("credential_possession_context_mismatch", result.reason_codes)

    def test_base_identity_invalidity_precedes_any_promotion(self):
        for identity in (
            replace(self.identity, status="inactive"),
            replace(self.identity, status="revoked"),
        ):
            with self.subTest(status=identity.status):
                result = self.consume(identity=identity)
                self.assertEqual(VerificationStatus.INVALID, result.status)
                self.assertEqual(IdentityAssuranceLevel.DECLARED, result.assurance_level)
        conflicting = self.consume(request_agent_ref="another-agent")
        self.assertEqual(VerificationStatus.INVALID, conflicting.status)
        self.assertEqual(IdentityAssuranceLevel.DECLARED, conflicting.assurance_level)


if __name__ == "__main__":
    unittest.main()

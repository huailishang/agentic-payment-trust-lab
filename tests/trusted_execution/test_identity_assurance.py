import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agentic_payment_experiment.models import AgentIdentity
from agentic_payment_experiment.trusted_execution import (
    IdentityAssuranceLevel,
    VerificationStatus,
    verify_agent_executor_identity,
)


class IdentityAssuranceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.identity = AgentIdentity(
            agent_id="agent-1",
            provider="offline-provider-1",
            executor_instance_id="executor-1",
            status="active",
        )

    def verify(self, *, identity=None, **overrides):
        values = {
            "authorized_agent_ref": "agent-1",
            "request_agent_ref": "agent-1",
            "execution_agent_ref": "agent-1",
            "identity": self.identity if identity is None else identity,
            "current_provider_ref": "offline-provider-1",
            "current_executor_instance_ref": "executor-1",
            "current_credential_ref": None,
        }
        values.update(overrides)
        return verify_agent_executor_identity(**values)

    def test_assurance_levels_are_stable_serializable_values(self) -> None:
        self.assertEqual(
            ["DECLARED", "BOUND", "VERIFIED"],
            [level.value for level in IdentityAssuranceLevel],
        )

    def test_complete_offline_binding_is_valid_and_bound_only(self) -> None:
        fact = self.verify()

        self.assertEqual(VerificationStatus.VALID, fact.status)
        self.assertEqual(IdentityAssuranceLevel.BOUND, fact.assurance_level)
        self.assertEqual(("identity_executor_binding_match",), fact.reason_codes)
        self.assertEqual("agent-1", fact.authorized_agent_ref)
        self.assertEqual("agent-1", fact.request_agent_ref)
        self.assertEqual("agent-1", fact.execution_agent_ref)
        self.assertEqual("agent-1", fact.identity_agent_ref)
        self.assertEqual("offline-provider-1", fact.provider_ref)
        self.assertEqual("executor-1", fact.executor_instance_ref)
        self.assertFalse(fact.credential_available)

    def test_credential_reference_alone_never_upgrades_to_verified(self) -> None:
        identity = replace(self.identity, credential_ref="credential-ref-1")
        fact = self.verify(
            identity=identity,
            current_credential_ref="credential-ref-1",
        )

        self.assertEqual(VerificationStatus.VALID, fact.status)
        self.assertEqual(IdentityAssuranceLevel.BOUND, fact.assurance_level)
        self.assertNotEqual(IdentityAssuranceLevel.VERIFIED, fact.assurance_level)
        self.assertTrue(fact.credential_available)

    def test_missing_identity_and_executor_evidence_fails_closed(self) -> None:
        fact = self.verify(
            identity=AgentIdentity(
                agent_id="",
                provider="",
                executor_instance_id=None,
                status="",
            ),
            current_provider_ref=None,
            current_executor_instance_ref=None,
        )

        self.assertEqual(VerificationStatus.MISSING_EVIDENCE, fact.status)
        self.assertEqual(IdentityAssuranceLevel.DECLARED, fact.assurance_level)
        self.assertEqual(
            (
                "identity_object_agent_ref_missing",
                "identity_provider_ref_missing",
                "identity_expected_executor_ref_missing",
                "identity_status_missing",
                "identity_current_provider_ref_missing",
                "identity_current_executor_ref_missing",
            ),
            fact.reason_codes,
        )

    def test_same_layer_conflicts_are_aggregated_in_stable_order(self) -> None:
        identity = AgentIdentity(
            agent_id="agent-other",
            provider="offline-provider-expected",
            executor_instance_id="executor-expected",
            status="active",
            credential_ref="credential-expected",
        )
        fact = self.verify(
            identity=identity,
            request_agent_ref="agent-request-other",
            execution_agent_ref="agent-execution-other",
            current_provider_ref="offline-provider-current",
            current_executor_instance_ref="executor-current",
            current_credential_ref="credential-current",
        )

        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(IdentityAssuranceLevel.DECLARED, fact.assurance_level)
        self.assertEqual(
            (
                "identity_request_agent_ref_mismatch",
                "identity_execution_agent_ref_mismatch",
                "identity_object_agent_ref_mismatch",
                "identity_provider_ref_mismatch",
                "identity_executor_instance_ref_mismatch",
                "identity_credential_ref_mismatch",
            ),
            fact.reason_codes,
        )

    def test_inactive_revoked_and_unsupported_statuses_are_invalid(self) -> None:
        cases = (
            ("inactive", "identity_status_inactive"),
            ("revoked", "identity_status_revoked"),
            ("suspended", "identity_status_unsupported"),
        )
        for status, reason in cases:
            with self.subTest(status=status):
                fact = self.verify(identity=replace(self.identity, status=status))
                self.assertEqual(VerificationStatus.INVALID, fact.status)
                self.assertEqual((reason,), fact.reason_codes)
                self.assertEqual(
                    IdentityAssuranceLevel.DECLARED,
                    fact.assurance_level,
                )


if __name__ == "__main__":
    unittest.main()

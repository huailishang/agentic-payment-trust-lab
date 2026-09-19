from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
import unittest

from agentic_payment_experiment.adapters.ap2_official_verification import (
    AP2OfficialDelegationVerificationFact,
    AP2_V020_PROTOCOL_VERSION,
    verify_ap2_v020_official_two_hop_chain,
)
from agentic_payment_experiment.trusted_execution.execution_facts import VerificationStatus


class AP2OfficialVerificationTests(unittest.TestCase):
    def test_missing_evidence_is_optional_dependency_safe(self) -> None:
        result = verify_ap2_v020_official_two_hop_chain(
            token=None,
            root_public_jwk=None,
            expected_aud=None,
            expected_nonce=None,
            current_time=0,
        )
        self.assertEqual(VerificationStatus.MISSING_EVIDENCE, result.status)
        self.assertEqual(AP2_V020_PROTOCOL_VERSION, result.protocol_version)
        self.assertIsNone(result.token_sha256)
        self.assertEqual(0, result.verified_hop_count)
        self.assertFalse(result.official_verifier_completed)

    def test_fact_surface_is_minimal_and_frozen(self) -> None:
        self.assertEqual(
            [
                "status",
                "reason_codes",
                "protocol_version",
                "token_sha256",
                "verified_hop_count",
                "official_verifier_completed",
                "audience_check_requested",
                "nonce_check_requested",
            ],
            [item.name for item in fields(AP2OfficialDelegationVerificationFact)],
        )
        fact = AP2OfficialDelegationVerificationFact(
            status=VerificationStatus.VALID,
            reason_codes=("ap2_official_two_hop_verified",),
            protocol_version=AP2_V020_PROTOCOL_VERSION,
            token_sha256=None,
            verified_hop_count=2,
            official_verifier_completed=True,
            audience_check_requested=True,
            nonce_check_requested=True,
        )
        with self.assertRaises(FrozenInstanceError):
            fact.verified_hop_count = 3  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()

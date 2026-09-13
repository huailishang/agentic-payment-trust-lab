from __future__ import annotations

import hashlib
import hmac
import sys
import unittest
from dataclasses import fields
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agentic_payment_experiment.trusted_execution import (
    SignedInstructionVerificationFact,
    VerificationStatus,
    verify_hmac_sha256_signed_instruction,
)


class SignedInstructionVerificationTests(unittest.TestCase):
    SECRET = b"test-only-signed-instruction-secret"
    PAYLOAD = b'1700000000.{"event":"order.updated"}'

    @classmethod
    def signature(cls, *, secret: bytes | None = None, payload: bytes | None = None) -> str:
        return hmac.new(
            secret or cls.SECRET,
            payload or cls.PAYLOAD,
            hashlib.sha256,
        ).hexdigest()

    def verify(self, **overrides: object) -> SignedInstructionVerificationFact:
        values: dict[str, object] = {
            "signed_payload": self.PAYLOAD,
            "signature_hex": self.signature(),
            "secret": self.SECRET,
            "signer_ref": "signer-test-1",
            "key_ref": "key-test-1",
            "signed_at_epoch": 1_700_000_000,
            "observed_at_epoch": 1_700_000_100,
            "max_age_seconds": 300,
        }
        values.update(overrides)
        return verify_hmac_sha256_signed_instruction(**values)  # type: ignore[arg-type]

    def test_valid_signature_is_a_verification_fact_not_a_business_decision(self) -> None:
        fact = self.verify()

        self.assertEqual(VerificationStatus.VALID, fact.status)
        self.assertEqual(("signed_instruction_signature_valid",), fact.reason_codes)
        self.assertTrue(fact.cryptographic_signature_verified)
        self.assertEqual("HMAC-SHA256", fact.algorithm)
        self.assertEqual(hashlib.sha256(self.PAYLOAD).hexdigest(), fact.signed_payload_sha256)

        field_names = {item.name for item in fields(fact)}
        self.assertFalse(
            field_names
            & {
                "secret",
                "signature",
                "signature_hex",
                "signed_payload",
                "raw_body",
                "decision",
                "payment_decision",
                "allow",
            }
        )

    def test_inclusive_freshness_boundary_is_valid(self) -> None:
        fact = self.verify(observed_at_epoch=1_700_000_300)
        self.assertEqual(VerificationStatus.VALID, fact.status)
        self.assertTrue(fact.cryptographic_signature_verified)

    def test_future_timestamp_outside_absolute_window_is_invalid(self) -> None:
        fact = self.verify(
            signed_at_epoch=1_700_000_301,
            observed_at_epoch=1_700_000_000,
        )
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            ("signed_instruction_timestamp_outside_window",),
            fact.reason_codes,
        )
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_wrong_key_is_invalid(self) -> None:
        fact = self.verify(secret=b"different-test-only-secret")
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(("signed_instruction_signature_mismatch",), fact.reason_codes)
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_malformed_signature_is_invalid(self) -> None:
        fact = self.verify(signature_hex="not-a-sha256-signature")
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            ("signed_instruction_signature_format_invalid",),
            fact.reason_codes,
        )
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_missing_signature_is_missing_evidence(self) -> None:
        fact = self.verify(signature_hex=None)
        self.assertEqual(VerificationStatus.MISSING_EVIDENCE, fact.status)
        self.assertEqual(("signed_instruction_signature_missing",), fact.reason_codes)
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_negative_freshness_window_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.verify(max_age_seconds=-1)


if __name__ == "__main__":
    unittest.main()

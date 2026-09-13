from __future__ import annotations

import base64
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agentic_payment_experiment.adapters import verify_ap2_merchant_authorization_signature
from agentic_payment_experiment.trusted_execution import VerificationStatus


MATRIX_PATH = (
    PROJECT_ROOT
    / "docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evaluator_fixtures/AP2_ES256_JWS_MATRIX.json"
)


def b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * ((4 - len(value) % 4) % 4))


def b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def mutate_payload(token: str, **updates: object) -> str:
    header_segment, payload_segment, signature_segment = token.split(".")
    payload = json.loads(b64url_decode(payload_segment).decode("utf-8"))
    payload.update(updates)
    new_payload = b64url_encode(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return f"{header_segment}.{new_payload}.{signature_segment}"


class AP2SignedInstructionAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        cls.fixture = matrix["fixture"]

    def verify(self, **overrides: object):
        fixture = self.fixture
        values: dict[str, object] = {
            "merchant_authorization": fixture["valid_compact_jws"],
            "public_jwk": fixture["valid_public_jwk"],
            "expected_signer_ref": fixture["expected_signer_ref"],
            "expected_key_ref": fixture["expected_key_ref"],
            "observed_at_epoch": fixture["observed_at_epoch"],
        }
        values.update(overrides)
        return verify_ap2_merchant_authorization_signature(**values)  # type: ignore[arg-type]

    def test_valid_authorization_maps_signed_claims_and_delegates_crypto(self) -> None:
        fact = self.verify()
        self.assertEqual(VerificationStatus.VALID, fact.status)
        self.assertEqual(("signed_instruction_signature_valid",), fact.reason_codes)
        self.assertEqual("merchant-test", fact.signer_ref)
        self.assertEqual("ap2-merchant-test-key-v1", fact.key_ref)
        self.assertEqual(1_760_000_000, fact.signed_at_epoch)
        self.assertEqual(900, fact.max_age_seconds)
        self.assertEqual(
            self.fixture["expected_signing_input_sha256"], fact.signed_payload_sha256
        )
        self.assertTrue(fact.cryptographic_signature_verified)

    def test_tampered_payload_is_signature_mismatch(self) -> None:
        token = mutate_payload(
            self.fixture["valid_compact_jws"],
            jti="ap2-cart-auth-test-001-tampered",
        )
        fact = self.verify(merchant_authorization=token)
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(("signed_instruction_signature_mismatch",), fact.reason_codes)
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_wrong_public_key_is_signature_mismatch(self) -> None:
        fact = self.verify(public_jwk=self.fixture["wrong_public_jwk"])
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(("signed_instruction_signature_mismatch",), fact.reason_codes)
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_wrong_signer_binding_is_invalid(self) -> None:
        fact = self.verify(expected_signer_ref="other-merchant-test")
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(("signed_instruction_signer_mismatch",), fact.reason_codes)
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_missing_authorization_is_missing_evidence(self) -> None:
        fact = self.verify(merchant_authorization=None)
        self.assertEqual(VerificationStatus.MISSING_EVIDENCE, fact.status)
        self.assertEqual(("signed_instruction_signature_missing",), fact.reason_codes)
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_malformed_compact_jws_is_invalid(self) -> None:
        fact = self.verify(merchant_authorization="malformed.compact-jws")
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            ("signed_instruction_compact_jws_format_invalid",), fact.reason_codes
        )
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_missing_required_issuer_claim_is_format_invalid(self) -> None:
        token = mutate_payload(self.fixture["valid_compact_jws"], iss=None)
        fact = self.verify(merchant_authorization=token)
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            ("signed_instruction_compact_jws_format_invalid",), fact.reason_codes
        )
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_observation_before_iat_is_invalid(self) -> None:
        fact = self.verify(observed_at_epoch=1_759_999_999)
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            ("signed_instruction_timestamp_outside_window",), fact.reason_codes
        )
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_observation_after_exp_is_invalid(self) -> None:
        fact = self.verify(observed_at_epoch=1_760_000_901)
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            ("signed_instruction_timestamp_outside_window",), fact.reason_codes
        )
        self.assertFalse(fact.cryptographic_signature_verified)


if __name__ == "__main__":
    unittest.main()

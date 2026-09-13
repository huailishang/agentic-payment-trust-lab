from __future__ import annotations

import base64
import json
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
    verify_es256_compact_jws_signed_instruction,
)


MATRIX_PATH = (
    PROJECT_ROOT
    / "docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evaluator_fixtures/AP2_ES256_JWS_MATRIX.json"
)


def b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * ((4 - len(value) % 4) % 4))


def b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def mutate_header(token: str, **updates: object) -> str:
    header_segment, payload_segment, signature_segment = token.split(".")
    header = json.loads(b64url_decode(header_segment).decode("utf-8"))
    header.update(updates)
    new_header = b64url_encode(
        json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return f"{new_header}.{payload_segment}.{signature_segment}"


class ES256SignedInstructionVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        cls.fixture = matrix["fixture"]

    def verify(self, **overrides: object) -> SignedInstructionVerificationFact:
        fixture = self.fixture
        values: dict[str, object] = {
            "compact_jws": fixture["valid_compact_jws"],
            "public_jwk": fixture["valid_public_jwk"],
            "signer_ref": fixture["expected_signer_ref"],
            "expected_signer_ref": fixture["expected_signer_ref"],
            "expected_key_ref": fixture["expected_key_ref"],
            "signed_at_epoch": 1_760_000_000,
            "expires_at_epoch": 1_760_000_900,
            "observed_at_epoch": fixture["observed_at_epoch"],
        }
        values.update(overrides)
        return verify_es256_compact_jws_signed_instruction(**values)  # type: ignore[arg-type]

    def test_valid_es256_fact_uses_exact_signing_input_hash(self) -> None:
        fact = self.verify()

        self.assertEqual(VerificationStatus.VALID, fact.status)
        self.assertEqual(("signed_instruction_signature_valid",), fact.reason_codes)
        self.assertEqual("ES256", fact.algorithm)
        self.assertTrue(fact.cryptographic_signature_verified)
        self.assertEqual(
            self.fixture["expected_signing_input_sha256"],
            fact.signed_payload_sha256,
        )
        self.assertEqual(900, fact.max_age_seconds)

        field_names = {item.name for item in fields(fact)}
        self.assertFalse(
            field_names
            & {
                "compact_jws",
                "raw_token",
                "raw_signature",
                "public_jwk",
                "private_key",
                "decision",
                "payment_decision",
                "allow",
            }
        )

    def test_unsupported_algorithm_fails_closed_before_signature_acceptance(self) -> None:
        token = mutate_header(self.fixture["valid_compact_jws"], alg="ES384")
        fact = self.verify(compact_jws=token)
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(("signed_instruction_algorithm_unsupported",), fact.reason_codes)
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_wrong_kid_fails_closed(self) -> None:
        token = mutate_header(self.fixture["valid_compact_jws"], kid="other-key")
        fact = self.verify(compact_jws=token)
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(("signed_instruction_key_ref_mismatch",), fact.reason_codes)
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_future_iat_fails_closed(self) -> None:
        fact = self.verify(
            signed_at_epoch=1_760_000_301,
            expires_at_epoch=1_760_001_201,
            observed_at_epoch=1_760_000_300,
        )
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            ("signed_instruction_timestamp_outside_window",), fact.reason_codes
        )
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_expired_token_fails_closed(self) -> None:
        fact = self.verify(observed_at_epoch=1_760_000_901)
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            ("signed_instruction_timestamp_outside_window",), fact.reason_codes
        )
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_invalid_exp_before_iat_fails_closed(self) -> None:
        fact = self.verify(
            signed_at_epoch=1_760_000_500,
            expires_at_epoch=1_760_000_499,
            observed_at_epoch=1_760_000_500,
        )
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            ("signed_instruction_timestamp_outside_window",), fact.reason_codes
        )
        self.assertEqual(0, fact.max_age_seconds)
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_non_p256_jwk_fails_closed(self) -> None:
        jwk = dict(self.fixture["valid_public_jwk"])
        jwk["crv"] = "P-384"
        fact = self.verify(public_jwk=jwk)
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            ("signed_instruction_verification_key_invalid",), fact.reason_codes
        )
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_malformed_jwk_fails_closed(self) -> None:
        jwk = dict(self.fixture["valid_public_jwk"])
        jwk["x"] = "not+base64url"
        fact = self.verify(public_jwk=jwk)
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            ("signed_instruction_verification_key_invalid",), fact.reason_codes
        )
        self.assertFalse(fact.cryptographic_signature_verified)


if __name__ == "__main__":
    unittest.main()

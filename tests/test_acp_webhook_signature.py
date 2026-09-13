from __future__ import annotations

import hashlib
import hmac
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agentic_payment_experiment.adapters import verify_acp_webhook_signature
from agentic_payment_experiment.trusted_execution import VerificationStatus


class ACPWebhookSignatureTests(unittest.TestCase):
    SECRET = b"test-only-acp-webhook-secret"
    RAW_BODY = b'{"type":"order_update","data":{"id":"ord-test"}}'
    SIGNED_AT = 1_700_000_000

    @classmethod
    def header(
        cls,
        *,
        timestamp: int | None = None,
        body: bytes | None = None,
        secret: bytes | None = None,
    ) -> str:
        timestamp = cls.SIGNED_AT if timestamp is None else timestamp
        body = cls.RAW_BODY if body is None else body
        secret = cls.SECRET if secret is None else secret
        signed = str(timestamp).encode("ascii") + b"." + body
        signature = hmac.new(secret, signed, hashlib.sha256).hexdigest()
        return f"t={timestamp},v1={signature}"

    def verify(self, **overrides: object):
        values: dict[str, object] = {
            "raw_body": self.RAW_BODY,
            "merchant_signature": self.header(),
            "secret": self.SECRET,
            "observed_at_epoch": self.SIGNED_AT + 10,
            "signer_ref": "merchant-test",
            "key_ref": "merchant-key-test",
        }
        values.update(overrides)
        return verify_acp_webhook_signature(**values)  # type: ignore[arg-type]

    def test_valid_header_delegates_and_hashes_exact_signed_bytes(self) -> None:
        fact = self.verify()
        expected_signed = str(self.SIGNED_AT).encode("ascii") + b"." + self.RAW_BODY

        self.assertEqual(VerificationStatus.VALID, fact.status)
        self.assertEqual(("signed_instruction_signature_valid",), fact.reason_codes)
        self.assertTrue(fact.cryptographic_signature_verified)
        self.assertEqual(hashlib.sha256(expected_signed).hexdigest(), fact.signed_payload_sha256)
        self.assertEqual(self.SIGNED_AT, fact.signed_at_epoch)
        self.assertEqual(300, fact.max_age_seconds)

    def test_tampered_body_is_invalid(self) -> None:
        fact = self.verify(raw_body=self.RAW_BODY + b" ")
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(("signed_instruction_signature_mismatch",), fact.reason_codes)
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_missing_header_is_missing_evidence(self) -> None:
        fact = self.verify(merchant_signature=None)
        self.assertEqual(VerificationStatus.MISSING_EVIDENCE, fact.status)
        self.assertEqual(("signed_instruction_signature_missing",), fact.reason_codes)
        self.assertFalse(fact.cryptographic_signature_verified)

    def test_header_parser_rejects_extra_duplicate_reordered_and_whitespace_components(self) -> None:
        valid = self.header()
        timestamp, signature = valid.split(",", 1)
        malformed = (
            valid + ",v2=extra",
            f"{timestamp},{timestamp},{signature}",
            f"{signature},{timestamp}",
            valid.replace(",", ", "),
            "t=01700000000," + signature,
        )
        for header in malformed:
            with self.subTest(header=header):
                fact = self.verify(merchant_signature=header)
                self.assertEqual(VerificationStatus.INVALID, fact.status)
                self.assertEqual(
                    ("signed_instruction_signature_format_invalid",),
                    fact.reason_codes,
                )
                self.assertFalse(fact.cryptographic_signature_verified)

    def test_inclusive_timestamp_boundary_is_valid(self) -> None:
        fact = self.verify(observed_at_epoch=self.SIGNED_AT + 300)
        self.assertEqual(VerificationStatus.VALID, fact.status)
        self.assertTrue(fact.cryptographic_signature_verified)

    def test_future_timestamp_outside_window_is_invalid(self) -> None:
        future_timestamp = self.SIGNED_AT + 301
        fact = self.verify(
            merchant_signature=self.header(timestamp=future_timestamp),
            observed_at_epoch=self.SIGNED_AT,
        )
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            ("signed_instruction_timestamp_outside_window",),
            fact.reason_codes,
        )
        self.assertFalse(fact.cryptographic_signature_verified)


if __name__ == "__main__":
    unittest.main()

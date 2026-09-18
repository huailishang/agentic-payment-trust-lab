from __future__ import annotations

import base64
import copy
import hashlib
import unittest
from unittest.mock import patch

from agentic_payment_experiment.adapters import adapt_verified_ap2_v020_snapshot
from agentic_payment_experiment.trusted_execution import VerificationStatus


def checkout_hash(raw_checkout_jwt: str) -> str:
    digest = hashlib.sha256(raw_checkout_jwt.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def fixture() -> dict:
    raw_checkout_jwt = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.test-checkout.signature"
    verified_hash = checkout_hash(raw_checkout_jwt)
    return {
        "protocol_version": "AP2-v0.2.0-official-boundary",
        "open_payment_mandate": {
            "vct": "mandate.payment.open.1",
            "constraints": [
                {
                    "type": "payment.amount_range",
                    "currency": "CNY",
                    "max": 55000,
                },
                {
                    "type": "payment.allowed_payees",
                    "allowed": [{"id": "merchant-boundary"}],
                },
                {
                    "type": "payment.agent_recurrence",
                    "frequency": "ON_DEMAND",
                    "max_occurrences": 1,
                },
                {
                    "type": "payment.execution_date",
                    "not_after": "2026-12-31T23:59:59+08:00",
                },
            ],
        },
        "payment_mandate": {
            "vct": "mandate.payment.1",
            "transaction_id": verified_hash,
            "payee": {"id": "merchant-boundary"},
            "payment_amount": {"currency": "CNY", "value": 52000},
            "execution_date": "2026-09-18T10:00:00+08:00",
            "payment_instrument": {"id": "synthetic-instrument"},
        },
        "checkout_mandate": {
            "vct": "mandate.checkout.1",
            "checkout_jwt": raw_checkout_jwt,
            "checkout_hash": verified_hash,
        },
        "experiment_context": {
            "mandate_id": "mandate-ap2-boundary-test",
            "user_id": "synthetic-user",
            "category": "synthetic-category",
            "allowed_categories": ["synthetic-category"],
            "confirmation_above_minor": 60000,
            "agent_id": "synthetic-agent",
        },
    }


class AP2ProtocolBoundaryTests(unittest.TestCase):
    def assert_blocked(
        self,
        snapshot: dict,
        status: VerificationStatus,
        reason: str,
    ) -> None:
        result = adapt_verified_ap2_v020_snapshot(snapshot)
        self.assertIs(result.boundary_status, status)
        self.assertIn(reason, result.reason_codes)
        self.assertFalse(result.ready)
        self.assertIsNone(result.mandate)
        self.assertIsNone(result.request)

    def test_valid_boundary_adapts_only_after_verification(self) -> None:
        snapshot = fixture()
        result = adapt_verified_ap2_v020_snapshot(snapshot)

        self.assertIs(result.boundary_status, VerificationStatus.VALID)
        self.assertTrue(result.ready)
        self.assertEqual(
            result.reason_codes,
            ("ap2_v020_protocol_boundary_verified",),
        )
        self.assertEqual(
            result.verified_checkout_hash,
            snapshot["checkout_mandate"]["checkout_hash"],
        )
        self.assertIsNotNone(result.mandate)
        self.assertIsNotNone(result.request)

    def test_wrong_open_payment_vct_fails_closed_before_mapping(self) -> None:
        snapshot = fixture()
        snapshot["open_payment_mandate"]["vct"] = "mandate.payment.open.999"

        with patch(
            "agentic_payment_experiment.adapters.ap2_protocol_boundary.adapt_ap2_snapshot"
        ) as mapper:
            self.assert_blocked(
                snapshot,
                VerificationStatus.INVALID,
                "ap2_open_payment_vct_invalid",
            )
            mapper.assert_not_called()

    def test_wrong_payment_vct_fails_closed(self) -> None:
        snapshot = fixture()
        snapshot["payment_mandate"]["vct"] = "mandate.payment.2"
        self.assert_blocked(
            snapshot,
            VerificationStatus.INVALID,
            "ap2_payment_vct_invalid",
        )

    def test_wrong_checkout_vct_fails_closed(self) -> None:
        snapshot = fixture()
        snapshot["checkout_mandate"]["vct"] = "mandate.checkout.2"
        self.assert_blocked(
            snapshot,
            VerificationStatus.INVALID,
            "ap2_checkout_vct_invalid",
        )

    def test_missing_vct_is_invalid_and_reported_as_missing_field(self) -> None:
        snapshot = fixture()
        snapshot["checkout_mandate"].pop("vct")
        result = adapt_verified_ap2_v020_snapshot(snapshot)

        self.assertIs(result.boundary_status, VerificationStatus.INVALID)
        self.assertIn("ap2_checkout_vct_invalid", result.reason_codes)
        self.assertIn("checkout_mandate.vct", result.missing_fields)
        self.assertFalse(result.ready)

    def test_tampered_checkout_jwt_does_not_reach_mapping(self) -> None:
        snapshot = fixture()
        snapshot["checkout_mandate"]["checkout_jwt"] += ".tampered"

        with patch(
            "agentic_payment_experiment.adapters.ap2_protocol_boundary.adapt_ap2_snapshot"
        ) as mapper:
            self.assert_blocked(
                snapshot,
                VerificationStatus.INVALID,
                "ap2_checkout_hash_mismatch",
            )
            mapper.assert_not_called()

    def test_missing_checkout_hash_is_missing_evidence(self) -> None:
        snapshot = fixture()
        snapshot["checkout_mandate"].pop("checkout_hash")
        result = adapt_verified_ap2_v020_snapshot(snapshot)

        self.assertIs(result.boundary_status, VerificationStatus.MISSING_EVIDENCE)
        self.assertIn("ap2_checkout_evidence_missing", result.reason_codes)
        self.assertIn("checkout_mandate.checkout_hash", result.missing_fields)
        self.assertFalse(result.ready)

    def test_non_default_hash_algorithm_fails_closed(self) -> None:
        snapshot = fixture()
        snapshot["checkout_mandate"]["_sd_alg"] = "sha-512"
        self.assert_blocked(
            snapshot,
            VerificationStatus.MISSING_EVIDENCE,
            "ap2_checkout_hash_algorithm_unsupported",
        )

    def test_payment_transaction_id_must_match_verified_checkout_hash(self) -> None:
        snapshot = fixture()
        snapshot["payment_mandate"]["transaction_id"] = "wrong-transaction"

        with patch(
            "agentic_payment_experiment.adapters.ap2_protocol_boundary.adapt_ap2_snapshot"
        ) as mapper:
            result = adapt_verified_ap2_v020_snapshot(snapshot)
            self.assertIs(result.boundary_status, VerificationStatus.INVALID)
            self.assertIn(
                "ap2_payment_checkout_binding_mismatch",
                result.reason_codes,
            )
            self.assertEqual(
                result.verified_checkout_hash,
                snapshot["checkout_mandate"]["checkout_hash"],
            )
            self.assertFalse(result.ready)
            mapper.assert_not_called()

    def test_missing_payment_transaction_id_is_missing_evidence(self) -> None:
        snapshot = fixture()
        snapshot["payment_mandate"].pop("transaction_id")
        result = adapt_verified_ap2_v020_snapshot(snapshot)

        self.assertIs(result.boundary_status, VerificationStatus.MISSING_EVIDENCE)
        self.assertIn(
            "ap2_payment_checkout_binding_missing",
            result.reason_codes,
        )
        self.assertIn("payment_mandate.transaction_id", result.missing_fields)
        self.assertFalse(result.ready)


    def test_non_string_checkout_jwt_is_invalid_without_mapping(self) -> None:
        snapshot = fixture()
        snapshot["checkout_mandate"]["checkout_jwt"] = 123
        coerced_hash = checkout_hash("123")
        snapshot["checkout_mandate"]["checkout_hash"] = coerced_hash
        snapshot["payment_mandate"]["transaction_id"] = coerced_hash

        with patch(
            "agentic_payment_experiment.adapters.ap2_protocol_boundary.adapt_ap2_snapshot"
        ) as mapper:
            self.assert_blocked(
                snapshot,
                VerificationStatus.INVALID,
                "ap2_checkout_evidence_type_invalid",
            )
            mapper.assert_not_called()

    def test_non_string_checkout_hash_is_invalid_without_mapping(self) -> None:
        snapshot = fixture()
        snapshot["checkout_mandate"]["checkout_hash"] = 123

        with patch(
            "agentic_payment_experiment.adapters.ap2_protocol_boundary.adapt_ap2_snapshot"
        ) as mapper:
            self.assert_blocked(
                snapshot,
                VerificationStatus.INVALID,
                "ap2_checkout_evidence_type_invalid",
            )
            mapper.assert_not_called()

    def test_non_string_transaction_id_is_invalid_without_mapping(self) -> None:
        snapshot = fixture()
        snapshot["payment_mandate"]["transaction_id"] = 123

        with patch(
            "agentic_payment_experiment.adapters.ap2_protocol_boundary.adapt_ap2_snapshot"
        ) as mapper:
            self.assert_blocked(
                snapshot,
                VerificationStatus.INVALID,
                "ap2_payment_checkout_binding_type_invalid",
            )
            mapper.assert_not_called()


if __name__ == "__main__":
    unittest.main()

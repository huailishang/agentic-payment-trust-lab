from __future__ import annotations

import copy
import json
import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment.adapters.x402 import (
    X402AdaptationStatus,
    adapt_x402_fixture,
    compute_requirement_digest,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "samples" / "protocols" / "x402" / "x402_offline_cases_v1.json"


def load_document() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def case(case_id: str) -> dict[str, object]:
    document = load_document()
    return copy.deepcopy(next(item for item in document["cases"] if item["case_id"] == case_id))


class X402AdapterTest(unittest.TestCase):
    def assert_invalid_text_field(self, fixture: dict[str, object], path: str) -> None:
        adapted = adapt_x402_fixture(fixture)

        self.assertEqual(X402AdaptationStatus.INVALID, adapted.status)
        self.assertIn(f"x402_string_invalid:{path}", adapted.reason_codes)
        self.assertIsNone(adapted.mandate)
        self.assertIsNone(adapted.order)
        self.assertIsNone(adapted.request)
        self.assertIsNone(adapted.payment)
        self.assertIsNone(adapted.settlement_observation)
        self.assertIsNone(adapted.async_observation)
        self.assertIsNone(adapted.resource_delivery)
        self.assertEqual((), adapted.delivery_attempts)

    def test_fixture_inventory_is_versioned_synthetic_and_bounded(self) -> None:
        document = load_document()

        self.assertEqual("x402-offline-fixture-v1", document["fixture_version"])
        self.assertTrue(document["synthetic"])
        self.assertEqual(
            [
                "X402-C01-BINDING-MATCH",
                "X402-C02-PAYEE-CHANGED",
                "X402-C03-VALUE-RAIL-CHANGED",
                "X402-C04-CROSS-RESOURCE-REUSE",
                "X402-C05-DUPLICATE-CONCURRENT-REUSE",
                "X402-C06-SETTLEMENT-DELIVERY-CONFLICT",
            ],
            [item["case_id"] for item in document["cases"]],
        )
        serialized = json.dumps(document, ensure_ascii=False).lower()
        for forbidden in ("private_key", "secret_key", "seed_phrase", "customer_name", "card_number"):
            self.assertNotIn(forbidden, serialized)

    def test_normal_fixture_maps_to_existing_protocol_neutral_models(self) -> None:
        fixture = case("X402-C01-BINDING-MATCH")
        adapted = adapt_x402_fixture(fixture)

        self.assertEqual(X402AdaptationStatus.READY, adapted.status)
        self.assertEqual((), adapted.reason_codes)
        self.assertIsNotNone(adapted.mandate)
        self.assertIsNotNone(adapted.order)
        self.assertIsNotNone(adapted.request)
        self.assertIsNotNone(adapted.payment)
        self.assertEqual("/weather/tokyo", adapted.order.service_id)
        self.assertEqual(("exact", "base-sepolia"), adapted.order.candidate_rails)
        self.assertEqual("USDC", adapted.order.currency)
        self.assertEqual("USDC", adapted.request.currency)
        self.assertEqual("synthetic-payee-001", adapted.request.payee)
        self.assertEqual("proof-synthetic-001", adapted.payment.payment_id)
        self.assertEqual(
            fixture["payment_requirement"]["requirement_digest"],
            compute_requirement_digest(fixture["http_request"], fixture["payment_requirement"]),
        )
        self.assertIn("offline_fixture_only", adapted.limitations)
        self.assertIn("does_not_verify_cryptographic_signature", adapted.limitations)

    def test_missing_reference_malformed_type_and_unknown_enum_fail_closed(self) -> None:
        missing = case("X402-C01-BINDING-MATCH")
        missing["payment_proof"]["proof_ref"] = ""
        self.assertEqual(X402AdaptationStatus.INVALID, adapt_x402_fixture(missing).status)
        self.assertIn("x402_required_field_missing:payment_proof.proof_ref", adapt_x402_fixture(missing).reason_codes)

        malformed = case("X402-C01-BINDING-MATCH")
        malformed["payment_proof"]["amount"] = ["0.01"]
        self.assertEqual(X402AdaptationStatus.INVALID, adapt_x402_fixture(malformed).status)
        self.assertIn("x402_decimal_invalid:payment_proof.amount", adapt_x402_fixture(malformed).reason_codes)

        unknown = case("X402-C01-BINDING-MATCH")
        unknown["facilitator_verification"]["status"] = "MAYBE"
        self.assertEqual(X402AdaptationStatus.INVALID, adapt_x402_fixture(unknown).status)
        self.assertIn("x402_verification_status_invalid", adapt_x402_fixture(unknown).reason_codes)

    def test_unsupported_scheme_or_network_is_not_silently_coerced(self) -> None:
        unsupported_scheme = case("X402-C01-BINDING-MATCH")
        unsupported_scheme["payment_requirement"]["scheme"] = "future-scheme"
        unsupported_scheme["payment_proof"]["scheme"] = "future-scheme"
        self.assertEqual(
            X402AdaptationStatus.UNSUPPORTED,
            adapt_x402_fixture(unsupported_scheme).status,
        )
        self.assertIn("x402_scheme_unsupported:future-scheme", adapt_x402_fixture(unsupported_scheme).reason_codes)

        unsupported_network = case("X402-C01-BINDING-MATCH")
        unsupported_network["payment_requirement"]["network"] = "mainnet-unknown"
        unsupported_network["payment_proof"]["network"] = "mainnet-unknown"
        self.assertEqual(
            X402AdaptationStatus.UNSUPPORTED,
            adapt_x402_fixture(unsupported_network).status,
        )
        self.assertIn("x402_network_unsupported:mainnet-unknown", adapt_x402_fixture(unsupported_network).reason_codes)

    def test_contradictory_identifiers_and_digest_are_invalid(self) -> None:
        fixture = case("X402-C01-BINDING-MATCH")
        fixture["payment_proof"]["requirement_ref"] = "requirement-other"
        adapted = adapt_x402_fixture(fixture)
        self.assertEqual(X402AdaptationStatus.INVALID, adapted.status)
        self.assertIn("x402_requirement_ref_mismatch", adapted.reason_codes)

        digest_changed = case("X402-C01-BINDING-MATCH")
        digest_changed["payment_proof"]["requirement_digest"] = "digest-other"
        adapted = adapt_x402_fixture(digest_changed)
        self.assertEqual(X402AdaptationStatus.INVALID, adapted.status)
        self.assertIn("x402_proof_requirement_digest_mismatch", adapted.reason_codes)

    def test_linked_list_valued_proof_reference_is_rejected_before_mapping(self) -> None:
        fixture = case("X402-C01-BINDING-MATCH")
        malformed = ["proof-as-list"]
        fixture["payment_proof"]["proof_ref"] = malformed
        fixture["facilitator_verification"]["proof_ref"] = malformed
        fixture["facilitator_settlement"]["proof_ref"] = malformed
        fixture["facilitator_settlement"]["payment_ref"] = malformed
        fixture["facilitator_async_observation"]["payment_ref"] = malformed
        fixture["resource_delivery"]["proof_ref"] = malformed

        self.assert_invalid_text_field(fixture, "payment_proof.proof_ref")

    def test_mapping_payee_and_numeric_requirement_id_are_rejected(self) -> None:
        payee = case("X402-C01-BINDING-MATCH")
        malformed_payee = {"address": "synthetic-payee"}
        payee["payment_requirement"]["payee"] = malformed_payee
        payee["payment_proof"]["payee"] = malformed_payee
        self.assert_invalid_text_field(payee, "payment_requirement.payee")

        for malformed_id in (True, 402):
            with self.subTest(malformed_id=malformed_id):
                requirement = case("X402-C01-BINDING-MATCH")
                requirement["payment_requirement"]["requirement_id"] = malformed_id
                requirement["payment_proof"]["requirement_ref"] = malformed_id
                requirement["payment_proof"]["original_transaction_ref"] = malformed_id
                requirement["facilitator_verification"]["requirement_ref"] = malformed_id
                requirement["facilitator_settlement"]["original_transaction_ref"] = malformed_id
                requirement["facilitator_async_observation"]["original_transaction_ref"] = malformed_id
                self.assert_invalid_text_field(
                    requirement,
                    "payment_requirement.requirement_id",
                )

    def test_project_context_and_delivery_attempt_references_are_strict_strings(self) -> None:
        identity = case("X402-C01-BINDING-MATCH")
        identity["project_context"]["agent_ref"] = ["agent-as-list"]
        self.assert_invalid_text_field(identity, "project_context.agent_ref")

        authority = case("X402-C01-BINDING-MATCH")
        authority["project_context"]["authority_ref"] = {"id": "authority-as-map"}
        self.assert_invalid_text_field(authority, "project_context.authority_ref")

        attempt = case("X402-C05-DUPLICATE-CONCURRENT-REUSE")
        attempt["delivery_attempts"][0]["proof_ref"] = {"proof": "not-text"}
        self.assert_invalid_text_field(
            attempt,
            "delivery_attempts[0].proof_ref",
        )

    def test_protocol_text_fields_and_optional_failure_code_are_strict_strings(self) -> None:
        for section, field, malformed, path in (
            ("http_request", "method", ["GET"], "http_request.method"),
            ("payment_requirement", "scheme", {"name": "exact"}, "payment_requirement.scheme"),
            ("payment_requirement", "network", 1, "payment_requirement.network"),
        ):
            with self.subTest(path=path):
                fixture = case("X402-C01-BINDING-MATCH")
                fixture[section][field] = malformed
                self.assert_invalid_text_field(fixture, path)

        failure = case("X402-C06-SETTLEMENT-DELIVERY-CONFLICT")
        failure["resource_delivery"]["failure_code"] = ["delivery-failed"]
        self.assert_invalid_text_field(failure, "resource_delivery.failure_code")

    def test_all_six_valid_fixtures_keep_their_adapter_status(self) -> None:
        document = load_document()
        statuses = [adapt_x402_fixture(item).status for item in document["cases"]]

        self.assertEqual([X402AdaptationStatus.READY] * 6, statuses)

    def test_adapter_performs_no_network_wallet_signing_or_payment_action(self) -> None:
        fixture = case("X402-C01-BINDING-MATCH")
        with (
            patch.object(socket, "socket", side_effect=AssertionError("network forbidden")) as socket_mock,
            patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")) as urlopen_mock,
        ):
            adapted = adapt_x402_fixture(fixture)

        self.assertEqual(X402AdaptationStatus.READY, adapted.status)
        socket_mock.assert_not_called()
        urlopen_mock.assert_not_called()
        self.assertFalse(adapted.side_effects.network_called)
        self.assertFalse(adapted.side_effects.wallet_created)
        self.assertFalse(adapted.side_effects.signature_created)
        self.assertFalse(adapted.side_effects.payment_executed)


if __name__ == "__main__":
    unittest.main()

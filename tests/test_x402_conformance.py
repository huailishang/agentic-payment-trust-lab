from __future__ import annotations

import copy
import json
import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment.x402_conformance import (
    ConformanceOutcome,
    ConformanceStatus,
    evaluate_x402_case,
    load_x402_fixture_document,
    run_x402_conformance,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "samples" / "protocols" / "x402" / "x402_offline_cases_v1.json"


class X402ConformanceTest(unittest.TestCase):
    def test_six_required_cases_are_derived_and_pass(self) -> None:
        report = run_x402_conformance(FIXTURE_PATH)
        by_id = {result.case_id: result for result in report.results}

        self.assertEqual(6, len(report.results))
        self.assertTrue(report.synthetic_fixtures_only)
        self.assertTrue(all(result.status is ConformanceStatus.PASS for result in report.results))
        self.assertEqual(ConformanceOutcome.ALLOW, by_id["X402-C01-BINDING-MATCH"].actual_outcome)
        self.assertEqual(ConformanceOutcome.BLOCK, by_id["X402-C02-PAYEE-CHANGED"].actual_outcome)
        self.assertEqual(ConformanceOutcome.BLOCK, by_id["X402-C03-VALUE-RAIL-CHANGED"].actual_outcome)
        self.assertEqual(ConformanceOutcome.BLOCK, by_id["X402-C04-CROSS-RESOURCE-REUSE"].actual_outcome)
        self.assertEqual(ConformanceOutcome.BLOCK, by_id["X402-C05-DUPLICATE-CONCURRENT-REUSE"].actual_outcome)
        self.assertEqual(ConformanceOutcome.CONFLICT, by_id["X402-C06-SETTLEMENT-DELIVERY-CONFLICT"].actual_outcome)

    def test_changed_payee_value_rail_and_resource_expose_reason_codes(self) -> None:
        report = run_x402_conformance(FIXTURE_PATH)
        by_id = {result.case_id: result for result in report.results}

        self.assertIn("payment_request_payee_mismatch", by_id["X402-C02-PAYEE-CHANGED"].reason_codes)
        changed = by_id["X402-C03-VALUE-RAIL-CHANGED"].reason_codes
        self.assertIn("payment_request_amount_mismatch", changed)
        self.assertIn("payment_request_currency_mismatch", changed)
        self.assertIn("x402_network_mismatch", changed)
        self.assertIn("x402_scheme_or_network_binding_invalid", changed)
        reused = by_id["X402-C04-CROSS-RESOURCE-REUSE"].reason_codes
        self.assertIn("x402_proof_resource_mismatch", reused)
        self.assertIn("x402_cross_resource_reuse", reused)

    def test_duplicate_proof_has_one_successful_delivery_and_explicit_idempotency_fact(self) -> None:
        result = next(
            result
            for result in run_x402_conformance(FIXTURE_PATH).results
            if result.case_id == "X402-C05-DUPLICATE-CONCURRENT-REUSE"
        )

        self.assertTrue(result.duplicate_or_concurrent_reuse)
        self.assertEqual(1, result.successful_delivery_count)
        self.assertIn("x402_duplicate_proof_reuse_blocked", result.reason_codes)
        self.assertEqual("VALID", result.evidence["idempotency"]["status"])
        self.assertEqual(
            ["delivery-attempt-synthetic-005-b"],
            result.evidence["idempotency"]["same_key_execution_ids"],
        )
        self.assertFalse(result.business_success_confirmed)

    def test_settlement_delivery_and_terminal_conflict_remain_separate(self) -> None:
        result = next(
            result
            for result in run_x402_conformance(FIXTURE_PATH).results
            if result.case_id == "X402-C06-SETTLEMENT-DELIVERY-CONFLICT"
        )

        self.assertEqual(ConformanceOutcome.CONFLICT, result.actual_outcome)
        self.assertEqual("CONFLICT", result.evidence["payment_status_conflict"]["resolution"])
        self.assertEqual("SUCCEEDED", result.evidence["facilitator_settlement"]["status"])
        self.assertEqual("FAILED", result.evidence["facilitator_async_observation"]["status"])
        self.assertEqual("FAILED", result.evidence["resource_delivery"]["status"])
        self.assertIn("payment_status_opposite_terminal_claims", result.reason_codes)
        self.assertIn("x402_settlement_succeeded_delivery_failed", result.reason_codes)
        self.assertFalse(result.business_success_confirmed)
        self.assertFalse(result.evidence["payment_status_conflict"]["business_success_confirmed"])
        self.assertFalse(result.evidence["payment_status_conflict"]["fulfillment_confirmed"])

    def test_evidence_answers_the_required_business_questions(self) -> None:
        result = run_x402_conformance(FIXTURE_PATH).results[0]

        self.assertEqual("/weather/tokyo", result.evidence["resource"]["resource_ref"])
        self.assertEqual("GET", result.evidence["resource"]["http_method"])
        self.assertEqual("0.01", result.evidence["payment_requirement"]["amount"])
        self.assertEqual("USDC", result.evidence["payment_requirement"]["asset"])
        self.assertEqual("base-sepolia", result.evidence["payment_requirement"]["network"])
        self.assertEqual("synthetic-payee-001", result.evidence["payment_requirement"]["payee"])
        self.assertEqual("proof-synthetic-001", result.evidence["payment_proof"]["proof_ref"])
        self.assertEqual("VERIFIED", result.evidence["facilitator_verification"]["status"])
        self.assertEqual("SUCCEEDED", result.evidence["resource_delivery"]["status"])
        self.assertEqual("VALID", result.evidence["replay"]["status"])
        self.assertIn("x402_conformance_allow", result.reason_codes)

    def test_pass_status_is_not_hard_coded_presentation_metadata(self) -> None:
        document = load_x402_fixture_document(FIXTURE_PATH)
        fixture = copy.deepcopy(document["cases"][0])
        fixture["expected"]["outcome"] = "BLOCK"

        result = evaluate_x402_case(fixture)

        self.assertEqual(ConformanceOutcome.ALLOW, result.actual_outcome)
        self.assertEqual(ConformanceStatus.FAIL, result.status)
        self.assertIn("x402_expected_outcome_mismatch", result.reason_codes)

    def test_report_is_deterministic_closed_and_has_explicit_limitations(self) -> None:
        first = run_x402_conformance(FIXTURE_PATH).to_dict()
        second = run_x402_conformance(FIXTURE_PATH).to_dict()

        self.assertEqual(first, second)
        self.assertEqual({"PASS"}, {result["status"] for result in first["results"]})
        self.assertIn("offline_fixture_pass_does_not_prove_official_sdk_security", first["limitations"])
        self.assertIn("offline_fixture_pass_does_not_prove_facilitator_production_safety", first["limitations"])
        self.assertIn("offline_fixture_pass_does_not_prove_regulatory_compliance", first["limitations"])
        self.assertIn("offline_fixture_pass_does_not_prove_mainnet_readiness", first["limitations"])
        self.assertFalse(first["side_effects"]["network_called"])
        self.assertFalse(first["side_effects"]["wallet_created"])
        self.assertFalse(first["side_effects"]["signature_created"])
        self.assertFalse(first["side_effects"]["payment_executed"])

    def test_harness_performs_no_network_or_payment_action(self) -> None:
        with (
            patch.object(socket, "socket", side_effect=AssertionError("network forbidden")) as socket_mock,
            patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")) as urlopen_mock,
        ):
            report = run_x402_conformance(FIXTURE_PATH)

        socket_mock.assert_not_called()
        urlopen_mock.assert_not_called()
        self.assertEqual(6, len(report.results))
        self.assertTrue(all(result.status is ConformanceStatus.PASS for result in report.results))


if __name__ == "__main__":
    unittest.main()

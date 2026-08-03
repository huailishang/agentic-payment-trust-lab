import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment import (
    PaymentQueryEvidenceStage,
    PaymentStatus,
    assess_payment_recovery,
    derive_payment_query_finality,
)
from agentic_payment_experiment.scenario_loader import load_scenario


class PaymentQueryFinalityTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        scenario = load_scenario(root / "samples" / "scenarios" / "S12_unknown_payment_state_recovery.json")
        self.payment = scenario.payment_recovery_initial
        self.observation = scenario.payment_status_observation
        self.mandate = scenario.mandate
        self.request = scenario.request
        self.order = scenario.final_order

    def derive(self, payment=None, observation=None):
        payment = payment or self.payment
        observation = observation or self.observation
        recovery = assess_payment_recovery(
            payment,
            observation,
            mandate=self.mandate,
            request=self.request,
            order=self.order,
        )
        return derive_payment_query_finality(payment, observation, recovery)

    def test_s12_query_confirmed_is_payment_terminal_only(self) -> None:
        fact = self.derive()
        self.assertEqual(PaymentQueryEvidenceStage.QUERY_CONFIRMED, fact.evidence_stage)
        self.assertTrue(fact.effective_status_terminal)
        self.assertFalse(fact.business_success_confirmed)
        self.assertFalse(fact.fulfillment_confirmed)
        self.assertFalse(fact.user_task_success_confirmed)
        self.assertFalse(fact.reconciliation_confirmed)
        self.assertFalse(fact.settlement_confirmed)
        self.assertFalse(fact.legal_finality_confirmed)

    def test_trusted_failed_query_is_payment_terminal_only(self) -> None:
        fact = self.derive(observation=replace(self.observation, status=PaymentStatus.FAILED))
        self.assertEqual(PaymentQueryEvidenceStage.QUERY_CONFIRMED, fact.evidence_stage)
        self.assertEqual(PaymentStatus.FAILED, fact.effective_status)
        self.assertTrue(fact.effective_status_terminal)
        self.assertFalse(fact.business_success_confirmed)
        self.assertFalse(fact.fulfillment_confirmed)
        self.assertFalse(fact.user_task_success_confirmed)
        self.assertFalse(fact.reconciliation_confirmed)
        self.assertFalse(fact.settlement_confirmed)
        self.assertFalse(fact.legal_finality_confirmed)

    def test_unknown_and_pending_queries_are_non_final(self) -> None:
        for status in (PaymentStatus.UNKNOWN, PaymentStatus.PENDING):
            with self.subTest(status=status):
                fact = self.derive(observation=replace(self.observation, status=status))
                self.assertEqual(PaymentQueryEvidenceStage.QUERY_UNRESOLVED, fact.evidence_stage)
                self.assertFalse(fact.effective_status_terminal)

    def test_conflicting_observation_is_blocked_and_non_terminal(self) -> None:
        payment = replace(self.payment, status=PaymentStatus.SUCCEEDED)
        fact = self.derive(payment=payment, observation=replace(self.observation, status=PaymentStatus.FAILED))
        self.assertEqual(PaymentQueryEvidenceStage.QUERY_BLOCKED, fact.evidence_stage)
        self.assertFalse(fact.effective_status_terminal)

    def test_invalid_binding_is_blocked_and_non_terminal(self) -> None:
        fact = self.derive(observation=replace(self.observation, payment_id="other-payment"))
        self.assertEqual(PaymentQueryEvidenceStage.QUERY_BLOCKED, fact.evidence_stage)
        self.assertFalse(fact.effective_status_terminal)

    def test_unknown_input_fails_closed(self) -> None:
        recovery = assess_payment_recovery(
            self.payment, self.observation, mandate=self.mandate, request=self.request, order=self.order
        )
        with self.assertRaisesRegex(ValueError, "PaymentStatus"):
            derive_payment_query_finality(
                replace(self.payment, status="NOT_A_STATUS"), self.observation, recovery
            )

    def test_serialization_is_deterministic(self) -> None:
        fact = self.derive()
        expected = {
            "evidence_stage": "QUERY_CONFIRMED",
            "initial_status": "UNKNOWN",
            "queried_status": "SUCCEEDED",
            "effective_status": "SUCCEEDED",
            "effective_status_terminal": True,
            "business_success_confirmed": False,
            "fulfillment_confirmed": False,
            "user_task_success_confirmed": False,
            "reconciliation_confirmed": False,
            "settlement_confirmed": False,
            "legal_finality_confirmed": False,
        }
        self.assertEqual(expected, fact.to_dict())
        self.assertEqual(expected, fact.to_dict())


if __name__ == "__main__":
    unittest.main()

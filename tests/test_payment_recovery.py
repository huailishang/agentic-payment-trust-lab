import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment import (
    PaymentRecoveryStatus,
    PaymentStatus,
    assess_payment_recovery,
)
from agentic_payment_experiment.scenario_loader import load_scenario


class PaymentRecoveryTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.scenario = load_scenario(
            root / "samples" / "scenarios" / "S12_unknown_payment_state_recovery.json"
        )
        self.assertIsNotNone(self.scenario.payment_recovery_initial)
        self.assertIsNotNone(self.scenario.payment_status_observation)
        self.payment = self.scenario.payment_recovery_initial
        self.observation = self.scenario.payment_status_observation

    def assess(self, *, payment=None, observation=None, attempts=()):
        return assess_payment_recovery(
            payment or self.payment,
            observation or self.observation,
            known_attempts=tuple(attempts),
            mandate=self.scenario.mandate,
            request=self.scenario.request,
            order=self.scenario.final_order,
        )

    def test_unknown_to_succeeded_recovers_original_payment_and_forbids_retry(self) -> None:
        result = self.assess()
        self.assertEqual(PaymentStatus.UNKNOWN, result.initial_status)
        self.assertEqual(PaymentStatus.SUCCEEDED, result.observed_status)
        self.assertEqual(PaymentStatus.SUCCEEDED, result.effective_status)
        self.assertEqual(PaymentRecoveryStatus.RECOVERED, result.recovery_status)
        self.assertFalse(result.retry_allowed)
        self.assertEqual("continue_with_original_payment", result.next_action)
        self.assertIn(
            "payment_state_recovered_as_succeeded",
            {item.code for item in result.issues},
        )
        evidence = {item.code: item for item in result.evidence}
        self.assertEqual("request-s12", evidence["recovery_request_ref"].observed)
        self.assertEqual("order-s12", evidence["recovery_order_ref"].observed)
        self.assertEqual("payment-s12", evidence["recovery_payment_ref"].observed)
        self.assertEqual("provider-payment-s12", evidence["recovery_provider_ref"].observed)
        self.assertEqual("idem-request-s12", evidence["recovery_idempotency_key"].observed)
        self.assertEqual("UNKNOWN", evidence["initial_payment_status"].observed)
        self.assertEqual("SUCCEEDED", evidence["queried_payment_status"].observed)
        self.assertEqual("VALID", evidence["status_observation_verification_status"].observed)
        self.assertEqual(
            "VALID",
            evidence["payment_execution_binding_status"].observed,
        )
        self.assertEqual(
            "original_transaction_binding_match",
            evidence["status_observation_verification_reasons"].observed,
        )
        self.assertEqual("payment-recovery-rules-v0.2", result.rule_version)

    def test_invalid_p2_binding_blocks_status_recovery(self) -> None:
        payment = replace(self.payment, transaction_object_ref="request-other")
        result = self.assess(payment=payment)

        self.assertEqual(PaymentRecoveryStatus.BLOCKED, result.recovery_status)
        self.assertFalse(result.retry_allowed)
        self.assertEqual(
            "investigate_payment_execution_binding",
            result.next_action,
        )
        self.assertIn(
            "payment_request_binding_mismatch",
            {item.code for item in result.issues},
        )

    def test_missing_provider_or_order_blocks_original_transaction_recovery(self) -> None:
        for observation in (
            replace(self.observation, provider_ref=None),
            replace(self.observation, order_id=None),
        ):
            with self.subTest(observation=observation):
                result = self.assess(observation=observation)
                self.assertEqual(PaymentRecoveryStatus.BLOCKED, result.recovery_status)
                self.assertFalse(result.retry_allowed)
                self.assertEqual("investigate_status_observation_binding", result.next_action)
                evidence = {item.code: item for item in result.evidence}
                self.assertNotEqual("VALID", evidence["status_observation_verification_status"].observed)

    def test_unknown_to_unknown_forbids_retry_and_remains_unresolved(self) -> None:
        observation = replace(self.observation, status=PaymentStatus.UNKNOWN)
        result = self.assess(observation=observation)
        self.assertEqual(PaymentStatus.UNKNOWN, result.effective_status)
        self.assertEqual(PaymentRecoveryStatus.UNRESOLVED, result.recovery_status)
        self.assertFalse(result.retry_allowed)
        self.assertEqual("query_again_or_manual_review", result.next_action)
        self.assertIn("payment_state_still_unknown", {item.code for item in result.issues})

    def test_pending_to_pending_forbids_retry(self) -> None:
        payment = replace(self.payment, status=PaymentStatus.PENDING)
        observation = replace(self.observation, status=PaymentStatus.PENDING)
        result = self.assess(payment=payment, observation=observation)
        self.assertEqual(PaymentStatus.PENDING, result.effective_status)
        self.assertEqual(PaymentRecoveryStatus.UNRESOLVED, result.recovery_status)
        self.assertFalse(result.retry_allowed)
        self.assertEqual("wait_and_query_again", result.next_action)
        self.assertIn("payment_still_pending", {item.code for item in result.issues})

    def test_unknown_to_failed_is_only_a_safe_retry_candidate(self) -> None:
        observation = replace(self.observation, status=PaymentStatus.FAILED)
        result = self.assess(observation=observation)
        self.assertEqual(PaymentStatus.FAILED, result.effective_status)
        self.assertEqual(PaymentRecoveryStatus.RETRY_CANDIDATE, result.recovery_status)
        self.assertTrue(result.retry_allowed)
        self.assertEqual(
            "safe_retry_candidate_with_same_idempotency_boundary",
            result.next_action,
        )
        self.assertIn(
            "payment_confirmed_failed_retry_candidate",
            {item.code for item in result.issues},
        )
        evidence = {item.code: item for item in result.evidence}
        self.assertEqual("VALID", evidence["idempotency_verification_status"].observed)
        self.assertEqual(
            "idempotency_boundary_present",
            evidence["idempotency_verification_reason"].observed,
        )
        self.assertEqual("0", evidence["idempotency_related_attempt_count"].observed)

    def test_status_observation_binding_errors_are_blocked(self) -> None:
        cases = {
            "payment": (
                replace(self.observation, payment_id="payment-other"),
                "payment_status_observation_payment_mismatch",
            ),
            "order": (
                replace(self.observation, order_id="order-other"),
                "payment_status_observation_order_mismatch",
            ),
            "provider": (
                replace(self.observation, provider_ref="provider-other"),
                "payment_status_observation_provider_mismatch",
            ),
        }
        for name, (observation, reason_code) in cases.items():
            with self.subTest(name=name):
                result = self.assess(observation=observation)
                self.assertEqual(PaymentRecoveryStatus.BLOCKED, result.recovery_status)
                self.assertEqual(PaymentStatus.UNKNOWN, result.effective_status)
                self.assertFalse(result.retry_allowed)
                self.assertEqual("investigate_status_observation_binding", result.next_action)
                self.assertIn(reason_code, {item.code for item in result.issues})

    def test_existing_successful_attempt_for_same_request_blocks_retry(self) -> None:
        observation = replace(self.observation, status=PaymentStatus.FAILED)
        successful_attempt = replace(
            self.payment,
            payment_id="payment-s12-success-existing",
            provider_ref="provider-payment-s12-success-existing",
            status=PaymentStatus.SUCCEEDED,
        )
        result = self.assess(observation=observation, attempts=(successful_attempt,))
        self.assertEqual(PaymentRecoveryStatus.BLOCKED, result.recovery_status)
        self.assertFalse(result.retry_allowed)
        self.assertEqual("use_existing_successful_attempt", result.next_action)
        self.assertIn(
            "existing_successful_payment_attempt",
            {item.code for item in result.issues},
        )
        evidence = {item.code: item for item in result.evidence}
        self.assertEqual("VALID", evidence["idempotency_verification_status"].observed)
        self.assertEqual("1", evidence["idempotency_related_attempt_count"].observed)

    def test_existing_unknown_or_pending_attempt_for_same_request_blocks_retry(self) -> None:
        observation = replace(self.observation, status=PaymentStatus.FAILED)
        for status in (PaymentStatus.UNKNOWN, PaymentStatus.PENDING):
            attempt = replace(
                self.payment,
                payment_id=f"payment-s12-{status.value.lower()}-existing",
                provider_ref=f"provider-payment-s12-{status.value.lower()}-existing",
                status=status,
            )
            with self.subTest(status=status.value):
                result = self.assess(observation=observation, attempts=(attempt,))
                self.assertEqual(PaymentRecoveryStatus.BLOCKED, result.recovery_status)
                self.assertFalse(result.retry_allowed)
                self.assertEqual("query_existing_attempts_before_retry", result.next_action)
                self.assertIn(
                    "unresolved_payment_attempt_exists",
                    {item.code for item in result.issues},
                )

    def test_failed_observation_without_idempotency_boundary_is_blocked(self) -> None:
        payment = replace(self.payment, idempotency_key=None)
        observation = replace(self.observation, status=PaymentStatus.FAILED)
        result = self.assess(payment=payment, observation=observation)
        self.assertEqual(PaymentRecoveryStatus.BLOCKED, result.recovery_status)
        self.assertFalse(result.retry_allowed)
        self.assertEqual("establish_idempotency_boundary_before_retry", result.next_action)
        self.assertIn("idempotency_boundary_missing", {item.code for item in result.issues})

    def test_conflicting_failed_observation_cannot_override_known_success(self) -> None:
        payment = replace(self.payment, status=PaymentStatus.SUCCEEDED)
        observation = replace(self.observation, status=PaymentStatus.FAILED)
        result = self.assess(payment=payment, observation=observation)
        self.assertEqual(PaymentStatus.SUCCEEDED, result.effective_status)
        self.assertEqual(PaymentRecoveryStatus.BLOCKED, result.recovery_status)
        self.assertFalse(result.retry_allowed)
        self.assertIn(
            "payment_status_observation_conflicts_with_known_success",
            {item.code for item in result.issues},
        )


if __name__ == "__main__":
    unittest.main()

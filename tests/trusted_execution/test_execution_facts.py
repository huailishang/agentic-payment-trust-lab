from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agentic_payment_experiment.trusted_execution import (
    ExecutionAttemptFact,
    VerificationStatus,
    check_idempotency,
    validate_status_observation,
    verify_declared_identity_binding,
    verify_execution_identity,
)


class ExecutionFactsTests(unittest.TestCase):
    def test_declared_identity_reference_match_is_valid_but_not_authentication(self) -> None:
        result = verify_declared_identity_binding(
            expected_identity_id="agent-shop-001",
            actual_identity_id="agent-shop-001",
        )
        self.assertEqual(VerificationStatus.VALID, result.status)
        self.assertEqual(("declared_identity_reference_match",), result.reason_codes)
        self.assertFalse(hasattr(result, "authenticated"))

    def test_declared_identity_reference_mismatch_is_invalid(self) -> None:
        result = verify_declared_identity_binding(
            expected_identity_id="agent-shop-001",
            actual_identity_id="agent-other",
        )
        self.assertEqual(VerificationStatus.INVALID, result.status)
        self.assertEqual(("declared_identity_reference_mismatch",), result.reason_codes)

    def test_declared_identity_reference_missing_is_missing_evidence(self) -> None:
        for expected, actual in ((None, "agent-1"), ("agent-1", None), ("", "agent-1")):
            with self.subTest(expected=expected, actual=actual):
                result = verify_declared_identity_binding(
                    expected_identity_id=expected,
                    actual_identity_id=actual,
                )
                self.assertEqual(VerificationStatus.MISSING_EVIDENCE, result.status)
                self.assertEqual(
                    ("declared_identity_reference_missing",),
                    result.reason_codes,
                )

    def test_execution_identity_match_is_valid(self) -> None:
        result = verify_execution_identity(
            expected_execution_id="payment-1",
            actual_execution_id="payment-1",
            expected_object_id="order-1",
            actual_object_id="order-1",
            expected_provider_ref="provider-1",
            actual_provider_ref="provider-1",
        )
        self.assertEqual(VerificationStatus.VALID, result.status)
        self.assertEqual(("execution_identity_match",), result.reason_codes)

    def test_execution_and_object_mismatches_are_reported_together(self) -> None:
        result = verify_execution_identity(
            expected_execution_id="payment-1",
            actual_execution_id="payment-2",
            expected_object_id="order-1",
            actual_object_id="order-2",
        )
        self.assertEqual(VerificationStatus.INVALID, result.status)
        self.assertEqual(
            ("execution_reference_mismatch", "object_reference_mismatch"),
            result.reason_codes,
        )

    def test_provider_mismatch_is_invalid_when_both_refs_exist(self) -> None:
        result = verify_execution_identity(
            expected_execution_id="payment-1",
            actual_execution_id="payment-1",
            expected_object_id="order-1",
            actual_object_id="order-1",
            expected_provider_ref="provider-1",
            actual_provider_ref="provider-2",
        )
        self.assertEqual(VerificationStatus.INVALID, result.status)
        self.assertEqual(("provider_reference_mismatch",), result.reason_codes)

    def test_missing_optional_provider_ref_does_not_invent_a_mismatch(self) -> None:
        for expected_provider_ref, actual_provider_ref in (
            ("provider-1", None),
            (None, "provider-1"),
            (None, None),
        ):
            with self.subTest(
                expected_provider_ref=expected_provider_ref,
                actual_provider_ref=actual_provider_ref,
            ):
                result = verify_execution_identity(
                    expected_execution_id="payment-1",
                    actual_execution_id="payment-1",
                    expected_object_id="order-1",
                    actual_object_id="order-1",
                    expected_provider_ref=expected_provider_ref,
                    actual_provider_ref=actual_provider_ref,
                )
                self.assertEqual(VerificationStatus.VALID, result.status)

    def test_missing_required_reference_is_missing_evidence(self) -> None:
        result = verify_execution_identity(
            expected_execution_id="payment-1",
            actual_execution_id="",
            expected_object_id="order-1",
            actual_object_id="order-1",
        )
        self.assertEqual(VerificationStatus.MISSING_EVIDENCE, result.status)
        self.assertEqual(("required_execution_reference_missing",), result.reason_codes)

    def test_status_observation_reuses_reference_verification(self) -> None:
        result = validate_status_observation(
            expected_execution_id="payment-1",
            observed_execution_id="payment-other",
            expected_object_id="order-1",
            observed_object_id="order-other",
            expected_provider_ref="provider-1",
            observed_provider_ref="provider-other",
        )
        self.assertEqual(VerificationStatus.INVALID, result.status)
        self.assertEqual(
            (
                "execution_reference_mismatch",
                "object_reference_mismatch",
                "provider_reference_mismatch",
            ),
            result.reason_codes,
        )

    def test_missing_idempotency_key_still_inventories_related_attempts(self) -> None:
        attempts = (
            ExecutionAttemptFact("payment-2", "request-1", "SUCCEEDED", "key-2"),
            ExecutionAttemptFact("payment-3", "request-2", "PENDING", "key-3"),
        )
        result = check_idempotency(
            idempotency_key=None,
            request_id="request-1",
            current_execution_id="payment-1",
            known_attempts=attempts,
        )
        self.assertEqual(VerificationStatus.MISSING_EVIDENCE, result.status)
        self.assertEqual("idempotency_key_missing", result.reason_code)
        self.assertEqual((attempts[0],), result.related_attempts)
        self.assertEqual((), result.same_key_execution_ids)
        self.assertEqual(("payment-2",), result.different_key_execution_ids)

    def test_present_idempotency_key_classifies_same_request_attempts(self) -> None:
        attempts = (
            ExecutionAttemptFact("payment-1", "request-1", "FAILED", "key-1"),
            ExecutionAttemptFact("payment-2", "request-1", "FAILED", "key-1"),
            ExecutionAttemptFact("payment-3", "request-1", "PENDING", "key-2"),
            ExecutionAttemptFact("payment-4", "request-1", "UNKNOWN", None),
            ExecutionAttemptFact("payment-5", "request-2", "SUCCEEDED", "key-1"),
        )
        result = check_idempotency(
            idempotency_key="key-1",
            request_id="request-1",
            current_execution_id="payment-1",
            known_attempts=attempts,
        )
        self.assertEqual(VerificationStatus.VALID, result.status)
        self.assertEqual("idempotency_boundary_present", result.reason_code)
        self.assertEqual((attempts[1], attempts[2], attempts[3]), result.related_attempts)
        self.assertEqual(("payment-2",), result.same_key_execution_ids)
        self.assertEqual(("payment-3", "payment-4"), result.different_key_execution_ids)

    def test_valid_idempotency_fact_does_not_claim_retry_is_safe(self) -> None:
        successful_parallel_attempt = ExecutionAttemptFact(
            "payment-2",
            "request-1",
            "SUCCEEDED",
            "key-1",
        )
        result = check_idempotency(
            idempotency_key="key-1",
            request_id="request-1",
            current_execution_id="payment-1",
            known_attempts=(successful_parallel_attempt,),
        )
        self.assertEqual(VerificationStatus.VALID, result.status)
        self.assertEqual((successful_parallel_attempt,), result.related_attempts)
        self.assertFalse(hasattr(result, "retry_allowed"))


if __name__ == "__main__":
    unittest.main()

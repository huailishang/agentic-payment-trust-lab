from __future__ import annotations

import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment import (
    PaymentExecutionRecord,
    PaymentStatus,
    PaymentStatusConflictResolution,
    PaymentStatusObservation,
    derive_payment_status_conflict,
)
from agentic_payment_experiment.trusted_execution import (
    FollowUpAction,
    verify_original_transaction,
)


class PaymentStatusConflictFactTest(unittest.TestCase):
    def setUp(self) -> None:
        self.t0 = datetime(2026, 7, 11, tzinfo=timezone.utc)
        self.payment = PaymentExecutionRecord(
            payment_id="pay-1",
            request_id="req-1",
            order_id="order-1",
            status=PaymentStatus.UNKNOWN,
            amount=Decimal("10.00"),
            currency="CNY",
            occurred_at=self.t0,
            provider_ref="provider-1",
        )

    def observation(
        self,
        status: PaymentStatus,
        *,
        minutes: int,
        source: str,
        payment_id: str = "pay-1",
        order_id: str = "order-1",
        provider_ref: str | None = "provider-1",
    ) -> PaymentStatusObservation:
        return PaymentStatusObservation(
            payment_id=payment_id,
            order_id=order_id,
            status=status,
            observed_at=self.t0 + timedelta(minutes=minutes),
            source=source,
            provider_ref=provider_ref,
        )

    def derive(
        self,
        query: PaymentStatusObservation,
        async_observation: PaymentStatusObservation,
        *,
        payment: PaymentExecutionRecord | None = None,
    ):
        payment = payment or self.payment
        query_binding = verify_original_transaction(
            FollowUpAction.STATUS_QUERY, payment, query
        )
        async_binding = verify_original_transaction(
            FollowUpAction.ASYNC_STATUS_NOTIFICATION, payment, async_observation
        )
        return derive_payment_status_conflict(
            payment,
            query,
            async_observation,
            query_binding,
            async_binding,
        )

    def test_pending_to_succeeded_is_monotonic_terminal_confirmation(self) -> None:
        fact = self.derive(
            self.observation(PaymentStatus.PENDING, minutes=1, source="query"),
            self.observation(PaymentStatus.SUCCEEDED, minutes=2, source="async"),
        )
        self.assertEqual(
            PaymentStatusConflictResolution.MONOTONIC_CONFIRMATION,
            fact.resolution,
        )
        self.assertEqual(PaymentStatus.SUCCEEDED, fact.effective_status)
        self.assertTrue(fact.effective_status_terminal)
        self.assertEqual(
            ("payment_status_monotonic_terminal_confirmation",),
            fact.reason_codes,
        )

    def test_unknown_to_failed_is_monotonic_terminal_confirmation(self) -> None:
        fact = self.derive(
            self.observation(PaymentStatus.UNKNOWN, minutes=1, source="query"),
            self.observation(PaymentStatus.FAILED, minutes=2, source="async"),
        )
        self.assertEqual(
            PaymentStatusConflictResolution.MONOTONIC_CONFIRMATION,
            fact.resolution,
        )
        self.assertEqual(PaymentStatus.FAILED, fact.effective_status)
        self.assertTrue(fact.effective_status_terminal)

    def test_matching_terminal_observations_are_consistent_and_terminal(self) -> None:
        payment = replace(self.payment, status=PaymentStatus.SUCCEEDED)
        fact = self.derive(
            self.observation(PaymentStatus.SUCCEEDED, minutes=1, source="query"),
            self.observation(PaymentStatus.SUCCEEDED, minutes=2, source="async"),
            payment=payment,
        )
        self.assertEqual(PaymentStatusConflictResolution.CONSISTENT, fact.resolution)
        self.assertEqual(PaymentStatus.SUCCEEDED, fact.effective_status)
        self.assertTrue(fact.effective_status_terminal)
        self.assertEqual(
            ("payment_status_matching_terminal_observations",),
            fact.reason_codes,
        )

    def test_opposite_terminal_claims_conflict_in_both_channel_orders(self) -> None:
        cases = (
            (
                self.observation(PaymentStatus.SUCCEEDED, minutes=1, source="query"),
                self.observation(PaymentStatus.FAILED, minutes=2, source="async"),
            ),
            (
                self.observation(PaymentStatus.FAILED, minutes=2, source="query"),
                self.observation(PaymentStatus.SUCCEEDED, minutes=1, source="async"),
            ),
        )
        for query, async_observation in cases:
            with self.subTest(query=query.status, async_status=async_observation.status):
                fact = self.derive(query, async_observation)
                self.assertEqual(PaymentStatusConflictResolution.CONFLICT, fact.resolution)
                self.assertEqual(PaymentStatus.UNKNOWN, fact.effective_status)
                self.assertFalse(fact.effective_status_terminal)
                self.assertEqual(
                    ("payment_status_opposite_terminal_claims",),
                    fact.reason_codes,
                )

    def test_terminal_to_unresolved_regression_is_conflict(self) -> None:
        fact = self.derive(
            self.observation(PaymentStatus.SUCCEEDED, minutes=1, source="query"),
            self.observation(PaymentStatus.PENDING, minutes=2, source="async"),
        )
        self.assertEqual(PaymentStatusConflictResolution.CONFLICT, fact.resolution)
        self.assertFalse(fact.effective_status_terminal)
        self.assertEqual(
            ("payment_status_terminal_to_unresolved_regression",),
            fact.reason_codes,
        )

    def test_equal_time_disagreement_is_conflict(self) -> None:
        fact = self.derive(
            self.observation(PaymentStatus.PENDING, minutes=1, source="query"),
            self.observation(PaymentStatus.SUCCEEDED, minutes=1, source="async"),
        )
        self.assertEqual(PaymentStatusConflictResolution.CONFLICT, fact.resolution)
        self.assertEqual(
            ("payment_status_equal_time_disagreement",),
            fact.reason_codes,
        )

    def test_unresolved_observations_remain_non_terminal(self) -> None:
        fact = self.derive(
            self.observation(PaymentStatus.PENDING, minutes=1, source="query"),
            self.observation(PaymentStatus.UNKNOWN, minutes=2, source="async"),
        )
        self.assertEqual(PaymentStatusConflictResolution.UNRESOLVED, fact.resolution)
        self.assertEqual(PaymentStatus.UNKNOWN, fact.effective_status)
        self.assertFalse(fact.effective_status_terminal)
        self.assertEqual(("payment_status_unresolved",), fact.reason_codes)

    def test_invalid_binding_and_reference_fail_closed(self) -> None:
        async_observation = self.observation(
            PaymentStatus.SUCCEEDED,
            minutes=2,
            source="async",
            provider_ref=None,
        )
        fact = self.derive(
            self.observation(PaymentStatus.PENDING, minutes=1, source="query"),
            async_observation,
        )
        self.assertEqual(PaymentStatusConflictResolution.BLOCKED, fact.resolution)
        self.assertEqual(PaymentStatus.UNKNOWN, fact.effective_status)
        self.assertFalse(fact.effective_status_terminal)
        self.assertEqual(
            ("payment_status_async_binding_invalid",),
            fact.reason_codes,
        )

    def test_observation_before_execution_is_blocked(self) -> None:
        fact = self.derive(
            self.observation(PaymentStatus.PENDING, minutes=-1, source="query"),
            self.observation(PaymentStatus.SUCCEEDED, minutes=2, source="async"),
        )
        self.assertEqual(PaymentStatusConflictResolution.BLOCKED, fact.resolution)
        self.assertEqual(
            ("payment_status_query_before_execution",),
            fact.reason_codes,
        )

    def test_invalid_enum_is_blocked_instead_of_coerced(self) -> None:
        query = replace(
            self.observation(PaymentStatus.PENDING, minutes=1, source="query"),
            status="NOT_A_PAYMENT_STATUS",
        )
        fact = self.derive(
            query,
            self.observation(PaymentStatus.SUCCEEDED, minutes=2, source="async"),
        )
        self.assertEqual(PaymentStatusConflictResolution.BLOCKED, fact.resolution)
        self.assertEqual(
            ("payment_status_query_status_invalid",),
            fact.reason_codes,
        )

    def test_serialization_is_deterministic_primitive_only_and_narrow(self) -> None:
        fact = self.derive(
            self.observation(PaymentStatus.PENDING, minutes=1, source="query"),
            self.observation(PaymentStatus.SUCCEEDED, minutes=2, source="async"),
        )
        expected = {
            "resolution": "MONOTONIC_CONFIRMATION",
            "initial_status": "UNKNOWN",
            "query_status": "PENDING",
            "query_observed_at": "2026-07-11T00:01:00+00:00",
            "async_status": "SUCCEEDED",
            "async_observed_at": "2026-07-11T00:02:00+00:00",
            "effective_status": "SUCCEEDED",
            "effective_status_terminal": True,
            "reason_codes": ["payment_status_monotonic_terminal_confirmation"],
            "business_success_confirmed": False,
            "fulfillment_confirmed": False,
            "user_task_success_confirmed": False,
            "reconciliation_confirmed": False,
            "settlement_confirmed": False,
            "legal_finality_confirmed": False,
        }
        self.assertEqual(expected, fact.to_dict())
        self.assertEqual(expected, fact.to_dict())
        self.assertTrue(all(not isinstance(value, PaymentStatus) for value in fact.to_dict().values()))
        with self.assertRaises(FrozenInstanceError):
            fact.effective_status = PaymentStatus.FAILED


if __name__ == "__main__":
    unittest.main()

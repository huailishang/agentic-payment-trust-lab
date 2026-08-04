from __future__ import annotations

import json
import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agentic_payment_experiment.models import (
    IntentMandate,
    Order,
    OrderItem,
    PaymentExecutionRecord,
    PaymentStatus,
    TransactionRequest,
)
from agentic_payment_experiment.trusted_execution import (
    KnownPaymentAttemptPreflightStatus,
    derive_known_payment_attempt_preflight,
    verify_payment_execution_binding,
)


class KnownPaymentAttemptPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        now = datetime(2026, 8, 4, 0, 0, tzinfo=timezone.utc)
        self.mandate = IntentMandate(
            mandate_id="mandate-1",
            user_id="user-1",
            max_amount=Decimal("500.00"),
            allowed_merchants=frozenset({"merchant-1"}),
            allowed_categories=frozenset({"shoes"}),
            expires_at=now + timedelta(hours=1),
            expected_agent_id="agent-1",
            authority_version="v1",
        )
        self.order = Order(
            order_id="order-1",
            order_version="v1",
            merchant="merchant-1",
            payee="payee-1",
            items=(
                OrderItem(
                    item_id="item-1",
                    name="Running Shoe",
                    category="shoes",
                    quantity=1,
                    unit_amount=Decimal("480.00"),
                ),
            ),
            total_amount=Decimal("480.00"),
            currency="CNY",
            quote_expires_at=now + timedelta(minutes=30),
            fulfilment_terms="standard delivery",
            mandate_ref="mandate-1",
            authority_version_ref="v1",
        )
        self.request = TransactionRequest(
            request_id="request-1",
            amount=Decimal("480.00"),
            merchant="merchant-1",
            category="shoes",
            occurred_at=now,
            agent_id="agent-1",
            currency="CNY",
            order_ref="order-1",
            authority_ref="mandate-1",
            authority_version_ref="v1",
            payee="payee-1",
        )
        self.succeeded = PaymentExecutionRecord(
            payment_id="payment-existing-1",
            request_id="request-1",
            order_id="order-1",
            status=PaymentStatus.SUCCEEDED,
            amount=Decimal("480.00"),
            currency="CNY",
            occurred_at=now + timedelta(seconds=1),
            provider_ref="provider-1",
            idempotency_key="idempotency-1",
            authority_ref="mandate-1",
            agent_ref="agent-1",
            transaction_object_ref="request-1",
            payee="payee-1",
        )

    def derive(self, attempts=()):
        return derive_known_payment_attempt_preflight(
            self.mandate,
            self.order,
            self.request,
            attempts,
        )

    def test_bound_succeeded_attempt_blocks_and_reuses_p2_verifier(self) -> None:
        with patch(
            "agentic_payment_experiment.trusted_execution.known_payment_attempt."
            "verify_payment_execution_binding",
            wraps=verify_payment_execution_binding,
        ) as verifier:
            fact = self.derive((self.succeeded,))

        verifier.assert_called_once_with(
            self.mandate,
            self.order,
            self.request,
            self.succeeded,
        )
        self.assertEqual(KnownPaymentAttemptPreflightStatus.BLOCKED, fact.status)
        self.assertEqual(
            ("known_payment_attempt_duplicate_succeeded",),
            fact.reason_codes,
        )
        self.assertEqual(("payment-existing-1",), fact.related_attempt_refs)
        self.assertEqual(("request-1",), fact.blocking_request_refs)
        serialized = fact.to_dict()
        self.assertEqual("BLOCKED", serialized["status"])
        json.dumps(serialized, allow_nan=False, sort_keys=True)
        with self.assertRaises(FrozenInstanceError):
            fact.status = KnownPaymentAttemptPreflightStatus.CLEAR  # type: ignore[misc]

    def test_empty_inventory_is_clear_and_primitive_serializable(self) -> None:
        fact = self.derive(())
        self.assertEqual(KnownPaymentAttemptPreflightStatus.CLEAR, fact.status)
        self.assertEqual((), fact.related_attempt_refs)
        self.assertEqual((), fact.blocking_request_refs)
        self.assertIn(
            "pending_or_unknown_attempt_policy_not_defined",
            fact.limitations,
        )
        json.dumps(fact.to_dict(), allow_nan=False, sort_keys=True)

    def test_unrelated_succeeded_attempt_does_not_block_or_call_binding(self) -> None:
        unrelated = replace(
            self.succeeded,
            payment_id="payment-other",
            request_id="request-other",
            transaction_object_ref="request-other",
        )
        with patch(
            "agentic_payment_experiment.trusted_execution.known_payment_attempt."
            "verify_payment_execution_binding"
        ) as verifier:
            fact = self.derive((unrelated,))

        verifier.assert_not_called()
        self.assertEqual(KnownPaymentAttemptPreflightStatus.CLEAR, fact.status)
        self.assertEqual((), fact.related_attempt_refs)
        self.assertEqual((), fact.blocking_request_refs)

    def test_unrelated_malformed_attempts_are_ignored_before_other_field_validation(self) -> None:
        cases = (
            replace(
                self.succeeded,
                request_id="request-other-a",
                payment_id="",
                status="INVALID_STATUS",  # type: ignore[arg-type]
                amount=Decimal("999999.00"),
                currency="INVALID",
                order_id="",
                authority_ref=None,
                agent_ref=None,
                transaction_object_ref=None,
                payee=None,
            ),
            replace(
                self.succeeded,
                request_id="request-other-b",
                payment_id=None,  # type: ignore[arg-type]
                status=None,  # type: ignore[arg-type]
            ),
        )
        for unrelated in cases:
            with self.subTest(request_id=unrelated.request_id):
                with patch(
                    "agentic_payment_experiment.trusted_execution.known_payment_attempt."
                    "verify_payment_execution_binding"
                ) as verifier:
                    fact = self.derive((unrelated,))

                verifier.assert_not_called()
                self.assertEqual(KnownPaymentAttemptPreflightStatus.CLEAR, fact.status)
                self.assertEqual(
                    ("known_payment_attempt_preflight_clear",),
                    fact.reason_codes,
                )
                self.assertEqual((), fact.related_attempt_refs)
                self.assertEqual((), fact.blocking_request_refs)

    def test_unknown_request_ownership_fails_closed_without_calling_binding(self) -> None:
        for request_id in (None, "", "   ", 123):
            with self.subTest(request_id=request_id):
                unknown = replace(
                    self.succeeded,
                    request_id=request_id,  # type: ignore[arg-type]
                )
                with patch(
                    "agentic_payment_experiment.trusted_execution.known_payment_attempt."
                    "verify_payment_execution_binding"
                ) as verifier:
                    fact = self.derive((unknown,))

                verifier.assert_not_called()
                self.assertEqual(
                    KnownPaymentAttemptPreflightStatus.INDETERMINATE,
                    fact.status,
                )
                self.assertEqual(
                    ("known_payment_attempt_request_ref_missing",),
                    fact.reason_codes,
                )
                self.assertEqual((), fact.related_attempt_refs)
                self.assertEqual((), fact.blocking_request_refs)

    def test_mixed_inventories_are_order_independent_and_refs_are_sorted(self) -> None:
        unrelated_malformed = replace(
            self.succeeded,
            request_id="request-other-malformed",
            payment_id="",
            status="INVALID_STATUS",  # type: ignore[arg-type]
        )
        unrelated_valid = replace(
            self.succeeded,
            request_id="request-other-valid",
            payment_id="payment-other-valid",
            transaction_object_ref="request-other-valid",
        )
        same_request_malformed = replace(self.succeeded, payment_id="")
        same_request_valid = self.succeeded

        blocked_results = tuple(
            self.derive(inventory).to_dict()
            for inventory in (
                (unrelated_malformed, same_request_valid),
                (same_request_valid, unrelated_malformed),
            )
        )
        self.assertEqual(blocked_results[0], blocked_results[1])
        self.assertEqual("BLOCKED", blocked_results[0]["status"])
        self.assertEqual(
            ["payment-existing-1"],
            blocked_results[0]["related_attempt_refs"],
        )

        indeterminate_results = tuple(
            self.derive(inventory).to_dict()
            for inventory in (
                (unrelated_valid, same_request_malformed),
                (same_request_malformed, unrelated_valid),
            )
        )
        self.assertEqual(indeterminate_results[0], indeterminate_results[1])
        self.assertEqual("INDETERMINATE", indeterminate_results[0]["status"])
        self.assertEqual(
            ["known_payment_attempt_ref_missing"],
            indeterminate_results[0]["reason_codes"],
        )

        second_unrelated_malformed = replace(
            unrelated_malformed,
            request_id="request-other-malformed-2",
            payment_id=None,  # type: ignore[arg-type]
            status=None,  # type: ignore[arg-type]
        )
        clear_results = tuple(
            self.derive(inventory).to_dict()
            for inventory in (
                (unrelated_malformed, second_unrelated_malformed),
                (second_unrelated_malformed, unrelated_malformed),
            )
        )
        self.assertEqual(clear_results[0], clear_results[1])
        self.assertEqual("CLEAR", clear_results[0]["status"])
        self.assertEqual([], clear_results[0]["related_attempt_refs"])

        pending_z = replace(
            self.succeeded,
            payment_id="payment-z",
            status=PaymentStatus.PENDING,
        )
        pending_a = replace(
            self.succeeded,
            payment_id="payment-a",
            status=PaymentStatus.UNKNOWN,
        )
        sorted_results = tuple(
            self.derive(inventory).to_dict()
            for inventory in ((pending_z, pending_a), (pending_a, pending_z))
        )
        self.assertEqual(sorted_results[0], sorted_results[1])
        self.assertEqual(
            ["payment-a", "payment-z"],
            sorted_results[0]["related_attempt_refs"],
        )

    def test_same_request_pending_and_unknown_do_not_block(self) -> None:
        for status in (PaymentStatus.PENDING, PaymentStatus.UNKNOWN):
            with self.subTest(status=status):
                attempt = replace(self.succeeded, status=status)
                fact = self.derive((attempt,))
                self.assertEqual(KnownPaymentAttemptPreflightStatus.CLEAR, fact.status)
                self.assertEqual(
                    ("known_payment_attempt_no_succeeded_match",),
                    fact.reason_codes,
                )
                self.assertEqual((attempt.payment_id,), fact.related_attempt_refs)
                self.assertEqual((), fact.blocking_request_refs)

    def test_invalid_succeeded_binding_is_indeterminate(self) -> None:
        invalid = replace(
            self.succeeded,
            amount=self.succeeded.amount + Decimal("1.00"),
        )
        fact = self.derive((invalid,))
        self.assertEqual(
            KnownPaymentAttemptPreflightStatus.INDETERMINATE,
            fact.status,
        )
        self.assertIn(
            "known_payment_attempt_binding:payment_execution_amount_mismatch",
            fact.reason_codes,
        )
        self.assertEqual((), fact.blocking_request_refs)

    def test_missing_succeeded_binding_is_indeterminate(self) -> None:
        missing = replace(self.succeeded, transaction_object_ref=None)
        fact = self.derive((missing,))
        self.assertEqual(
            KnownPaymentAttemptPreflightStatus.INDETERMINATE,
            fact.status,
        )
        self.assertIn(
            "known_payment_attempt_binding:payment_execution_transaction_object_ref_missing",
            fact.reason_codes,
        )
        self.assertEqual((), fact.blocking_request_refs)

    def test_non_tuple_containers_fail_closed_without_reading_items(self) -> None:
        class ExplodingProxy:
            def __getattribute__(self, name):
                raise AssertionError(f"unexpected attribute read: {name}")

        for attempts in ([ExplodingProxy()], {"attempt": ExplodingProxy()}):
            with self.subTest(container=type(attempts).__name__):
                fact = self.derive(attempts)
                self.assertEqual(
                    KnownPaymentAttemptPreflightStatus.INDETERMINATE,
                    fact.status,
                )
                self.assertEqual(
                    ("known_payment_attempts_invalid_container",),
                    fact.reason_codes,
                )

    def test_invalid_tuple_members_fail_closed_without_attribute_reads(self) -> None:
        class PaymentSubclass(PaymentExecutionRecord):
            pass

        class ExplodingProxy:
            def __getattribute__(self, name):
                raise AssertionError(f"unexpected attribute read: {name}")

        invalid_members = (
            None,
            {},
            [],
            ExplodingProxy(),
            PaymentSubclass(**self.succeeded.__dict__),
        )
        for member in invalid_members:
            with self.subTest(member=type(member).__name__):
                fact = self.derive((member,))
                self.assertEqual(
                    KnownPaymentAttemptPreflightStatus.INDETERMINATE,
                    fact.status,
                )
                self.assertEqual(
                    ("known_payment_attempt_invalid_type",),
                    fact.reason_codes,
                )

    def test_invalid_context_outer_types_fail_closed_before_attribute_reads(self) -> None:
        class ExplodingProxy:
            def __getattribute__(self, name):
                raise AssertionError(f"unexpected attribute read: {name}")

        cases = (
            (ExplodingProxy(), self.order, self.request, "mandate"),
            (self.mandate, ExplodingProxy(), self.request, "order"),
            (self.mandate, self.order, ExplodingProxy(), "request"),
        )
        for mandate, order, request, name in cases:
            with self.subTest(name=name):
                fact = derive_known_payment_attempt_preflight(
                    mandate,
                    order,
                    request,
                    (self.succeeded,),
                )
                self.assertEqual(
                    KnownPaymentAttemptPreflightStatus.INDETERMINATE,
                    fact.status,
                )
                self.assertEqual(
                    (f"known_payment_attempt_{name}_invalid_type",),
                    fact.reason_codes,
                )


if __name__ == "__main__":
    unittest.main()

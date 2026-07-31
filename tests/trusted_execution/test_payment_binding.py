import sys
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agentic_payment_experiment.models import (
    AgentIdentity,
    Decision,
    IntentMandate,
    Order,
    OrderItem,
    PaymentExecutionRecord,
    PaymentStatus,
    TransactionRequest,
)
from agentic_payment_experiment.payment_execution import (
    execute_with_payment_binding_gate,
)
from agentic_payment_experiment.trusted_execution import (
    IdentityAssuranceLevel,
    VerificationStatus,
    verify_payment_execution_binding,
)


class PaymentExecutionBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 7, 11, 12, 0, tzinfo=timezone.utc)
        self.mandate = IntentMandate(
            mandate_id="mandate-1",
            user_id="user-1",
            max_amount=Decimal("500.00"),
            allowed_merchants=frozenset({"merchant-1"}),
            allowed_categories=frozenset({"shoes"}),
            expires_at=self.now + timedelta(hours=1),
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
            quote_expires_at=self.now + timedelta(minutes=30),
            fulfilment_terms="standard delivery",
            mandate_ref="mandate-1",
            authority_version_ref="v1",
        )
        self.request = TransactionRequest(
            request_id="request-1",
            amount=Decimal("480.00"),
            merchant="merchant-1",
            category="shoes",
            occurred_at=self.now,
            agent_id="agent-1",
            currency="CNY",
            order_ref="order-1",
            authority_ref="mandate-1",
            authority_version_ref="v1",
            payee="payee-1",
        )
        self.payment = PaymentExecutionRecord(
            payment_id="payment-1",
            request_id="request-1",
            order_id="order-1",
            status=PaymentStatus.PENDING,
            amount=Decimal("480.00"),
            currency="CNY",
            occurred_at=self.now + timedelta(seconds=1),
            authority_ref="mandate-1",
            agent_ref="agent-1",
            transaction_object_ref="request-1",
            payee="payee-1",
        )
        self.identity = AgentIdentity(
            agent_id="agent-1",
            provider="offline-provider-1",
            executor_instance_id="executor-1",
            status="active",
        )

    def verify(self, *, mandate=None, order=None, request=None, payment=None):
        return verify_payment_execution_binding(
            mandate if mandate is not None else self.mandate,
            order if order is not None else self.order,
            request if request is not None else self.request,
            payment if payment is not None else self.payment,
        )

    def execute(
        self,
        *,
        decision=Decision.ALLOW,
        mandate=None,
        order=None,
        request=None,
        payment=None,
        identity=None,
        provider_ref="offline-provider-1",
        executor_ref="executor-1",
        credential_ref=None,
    ):
        calls: list[str] = []
        outcome = execute_with_payment_binding_gate(
            decision,
            mandate if mandate is not None else self.mandate,
            order if order is not None else self.order,
            request if request is not None else self.request,
            payment if payment is not None else self.payment,
            lambda: calls.append("paid") or "provider-payment-1",
            agent_identity=self.identity if identity is None else identity,
            current_provider_ref=provider_ref,
            current_executor_instance_ref=executor_ref,
            current_credential_ref=credential_ref,
        )
        return outcome, calls

    def test_valid_continuous_binding_is_the_only_path_that_executes(self) -> None:
        fact = self.verify()
        outcome, calls = self.execute()

        self.assertEqual(VerificationStatus.VALID, fact.status)
        self.assertEqual(("payment_execution_binding_match",), fact.reason_codes)
        self.assertEqual(Decision.ALLOW, outcome.decision)
        self.assertEqual(VerificationStatus.VALID, outcome.identity_fact.status)
        self.assertEqual(
            IdentityAssuranceLevel.BOUND,
            outcome.identity_fact.assurance_level,
        )
        self.assertTrue(outcome.executed)
        self.assertEqual("provider-payment-1", outcome.execution_result)
        self.assertEqual(["paid"], calls)

    def test_request_must_bind_the_current_order_and_authority_version(self) -> None:
        request = replace(
            self.request,
            order_ref="order-other",
            authority_version_ref="v2",
        )
        fact = self.verify(request=request)
        outcome, calls = self.execute(request=request)

        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            (
                "payment_request_order_ref_mismatch",
                "payment_request_authority_version_ref_mismatch",
                "payment_execution_order_ref_mismatch",
            ),
            fact.reason_codes,
        )
        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)

    def test_execution_must_bind_the_validated_request_and_order(self) -> None:
        payment = replace(
            self.payment,
            request_id="request-other",
            order_id="order-other",
            transaction_object_ref="request-other",
        )
        fact = self.verify(payment=payment)
        outcome, calls = self.execute(payment=payment)

        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            (
                "payment_execution_request_ref_mismatch",
                "payment_execution_transaction_object_ref_mismatch",
                "payment_execution_order_ref_mismatch",
            ),
            fact.reason_codes,
        )
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)

    def test_critical_payment_fields_cannot_change_silently(self) -> None:
        payment = replace(
            self.payment,
            amount=Decimal("490.00"),
            currency="USD",
            payee="payee-other",
        )
        fact = self.verify(payment=payment)
        outcome, calls = self.execute(payment=payment)

        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            (
                "payment_execution_payee_mismatch",
                "payment_execution_amount_mismatch",
                "payment_execution_currency_mismatch",
            ),
            fact.reason_codes,
        )
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)

    def test_authority_and_agent_cannot_be_swapped_at_execution(self) -> None:
        payment = replace(
            self.payment,
            authority_ref="mandate-other",
            agent_ref="agent-other",
        )
        fact = self.verify(payment=payment)
        outcome, calls = self.execute(payment=payment)

        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            (
                "payment_execution_authority_ref_mismatch",
                "payment_execution_agent_ref_mismatch",
            ),
            fact.reason_codes,
        )
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)

    def test_missing_continuous_references_fail_closed(self) -> None:
        request = replace(
            self.request,
            order_ref=None,
            authority_ref=None,
            authority_version_ref=None,
            payee=None,
        )
        payment = replace(
            self.payment,
            authority_ref=None,
            agent_ref=None,
            transaction_object_ref=None,
            payee=None,
        )
        fact = self.verify(request=request, payment=payment)
        outcome, calls = self.execute(request=request, payment=payment)

        self.assertEqual(VerificationStatus.MISSING_EVIDENCE, fact.status)
        self.assertIn("payment_request_order_ref_missing", fact.reason_codes)
        self.assertIn(
            "payment_execution_transaction_object_ref_missing",
            fact.reason_codes,
        )
        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)

    def test_reference_collision_or_execution_before_request_is_invalid(self) -> None:
        payment = replace(
            self.payment,
            payment_id="request-1",
            occurred_at=self.now - timedelta(seconds=1),
        )
        fact = self.verify(payment=payment)

        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            (
                "payment_execution_reference_collision",
                "payment_execution_before_request",
            ),
            fact.reason_codes,
        )

    def test_upstream_non_allow_decision_blocks_even_a_valid_payment_binding(self) -> None:
        for decision in (
            Decision.DENY,
            Decision.CONFIRMATION_REQUIRED,
            Decision.INDETERMINATE,
        ):
            with self.subTest(decision=decision):
                outcome, calls = self.execute(decision=decision)
                self.assertEqual(decision, outcome.decision)
                self.assertEqual(VerificationStatus.VALID, outcome.binding_fact.status)
                self.assertFalse(outcome.executed)
                self.assertEqual([], calls)

    def test_missing_p3_executor_evidence_is_indeterminate_before_callback(self) -> None:
        identity = replace(self.identity, executor_instance_id=None)
        outcome, calls = self.execute(
            identity=identity,
            executor_ref=None,
        )

        self.assertEqual(VerificationStatus.VALID, outcome.binding_fact.status)
        self.assertEqual(
            VerificationStatus.MISSING_EVIDENCE,
            outcome.identity_fact.status,
        )
        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)

    def test_invalid_p3_identity_is_denied_before_callback(self) -> None:
        identity = replace(self.identity, agent_id="agent-other")
        outcome, calls = self.execute(identity=identity)

        self.assertEqual(VerificationStatus.VALID, outcome.binding_fact.status)
        self.assertEqual(VerificationStatus.INVALID, outcome.identity_fact.status)
        self.assertEqual(
            ("identity_object_agent_ref_mismatch",),
            outcome.identity_fact.reason_codes,
        )
        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)


if __name__ == "__main__":
    unittest.main()

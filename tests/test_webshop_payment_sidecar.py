from __future__ import annotations

import ast
import builtins
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment import (
    Decision,
    FulfillmentRecord,
    FulfillmentStatus,
    IntentMandate,
    PaymentExecutionRecord,
    PaymentRecoveryStatus,
    PaymentStatus,
    PaymentStatusConflictResolution,
    PaymentStatusObservation,
    RemediationStatus,
    TaskStatus,
    WebShopBuyNowGateOutcome,
    WebShopPaymentFulfilmentOutcome,
    assess_webshop_payment_fulfilment,
)
from agentic_payment_experiment.adapters.webshop import adapt_webshop_purchase_candidate
from agentic_payment_experiment.trusted_execution import RuntimeGateRecord


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "samples/external/webshop/pre_buy_now_candidate_v1.json"
SIDECAR_PATH = ROOT / "src/agentic_payment_experiment/webshop_payment_sidecar.py"
REQUIRED_LIMITATIONS = {
    "offline_sidecar_only",
    "no_real_payment_execution",
    "no_real_status_query_or_async_callback",
    "no_real_fulfilment",
    "no_automatic_payment_retry",
    "no_real_refund_or_dispute",
    "webshop_reward_not_used_as_payment_or_task_success",
}


class WebShopPaymentSidecarTest(unittest.TestCase):
    def setUp(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.adaptation = adapt_webshop_purchase_candidate(fixture)
        self.assertTrue(self.adaptation.ready)
        self.assertIsNotNone(self.adaptation.order)
        self.assertIsNotNone(self.adaptation.payment_request)
        assert self.adaptation.order is not None
        assert self.adaptation.payment_request is not None

        self.agent_id = "webshop-agent-1"
        self.request = replace(
            self.adaptation.payment_request,
            agent_id=self.agent_id,
        )
        self.mandate = IntentMandate(
            mandate_id=self.adaptation.order.mandate_ref,
            user_id="webshop-user-1",
            max_amount=Decimal("1000.00"),
            allowed_merchants=frozenset({self.adaptation.order.merchant}),
            allowed_categories=frozenset({self.request.category}),
            expires_at=self.request.occurred_at + timedelta(hours=2),
            max_count=1,
            expected_agent_id=self.agent_id,
            currency=self.request.currency,
            authority_version=self.adaptation.order.authority_version_ref or "",
        )
        runtime_record = RuntimeGateRecord(
            preliminary_decision=Decision.ALLOW,
            final_decision=Decision.ALLOW,
            binding_status="VALID",
            binding_reason_codes=("payment_execution_binding_match",),
            identity_status="VALID",
            identity_reason_codes=("identity_executor_binding_match",),
            context_policy_status="VALID",
            context_policy_reason_codes=("context_policy_valid",),
            callback_executed=True,
            callback_count=1,
            callback_result_ref="simulated-webshop-checkout",
            reason_codes=("runtime:allow",),
        )
        self.gate = WebShopBuyNowGateOutcome(
            decision=Decision.ALLOW,
            checkout_executed=True,
            callback_count=1,
            callback_result_ref="simulated-webshop-checkout",
            bound_request=self.request,
            prepayment_result=None,
            runtime_gate_record=runtime_record,
            reason_codes=("runtime:allow",),
        )
        self.payment = PaymentExecutionRecord(
            payment_id="webshop-payment-1",
            request_id=self.request.request_id,
            order_id=self.adaptation.order.order_id,
            status=PaymentStatus.UNKNOWN,
            amount=self.request.amount,
            currency=self.request.currency,
            occurred_at=self.request.occurred_at + timedelta(seconds=1),
            receipt_ref="offline-receipt-1",
            provider_ref="offline-provider-payment-1",
            idempotency_key="idem-webshop-request-1",
            authority_ref=self.mandate.mandate_id,
            agent_ref=self.agent_id,
            transaction_object_ref=self.request.request_id,
            payee=self.adaptation.order.payee,
        )
        self.fulfillment = FulfillmentRecord(
            fulfillment_id="webshop-fulfillment-1",
            order_id=self.adaptation.order.order_id,
            status=FulfillmentStatus.PENDING,
            occurred_at=self.payment.occurred_at + timedelta(minutes=3),
            evidence_ref="offline-fulfillment-evidence-1",
        )

    def observation(
        self,
        status: PaymentStatus,
        *,
        minutes: int,
        source: str,
        payment_id: str | None = None,
        order_id: str | None = None,
        provider_ref: str | None = "_default",
    ) -> PaymentStatusObservation:
        return PaymentStatusObservation(
            payment_id=payment_id or self.payment.payment_id,
            order_id=order_id or self.payment.order_id,
            status=status,
            observed_at=self.payment.occurred_at + timedelta(minutes=minutes),
            source=source,
            provider_ref=(
                self.payment.provider_ref
                if provider_ref == "_default"
                else provider_ref
            ),
        )

    def assess(self, **overrides):
        values = {
            "gate_outcome": self.gate,
            "adaptation": self.adaptation,
            "mandate": self.mandate,
            "payment": self.payment,
            "fulfillment": self.fulfillment,
            "query_observation": None,
            "async_observation": None,
            "known_attempts": (),
        }
        values.update(overrides)
        return assess_webshop_payment_fulfilment(**values)

    def test_gate_and_explicit_input_prerequisite_matrix_fails_closed(self) -> None:
        cases = (
            ("gate_missing", {"gate_outcome": None}, "prerequisite:gate_outcome_missing"),
            (
                "gate_deny",
                {"gate_outcome": replace(self.gate, decision=Decision.DENY)},
                "prerequisite:gate_decision_not_allow",
            ),
            (
                "checkout_false",
                {"gate_outcome": replace(self.gate, checkout_executed=False)},
                "prerequisite:checkout_not_executed",
            ),
            (
                "callback_count",
                {"gate_outcome": replace(self.gate, callback_count=0)},
                "prerequisite:callback_count_not_one",
            ),
            (
                "runtime_missing",
                {"gate_outcome": replace(self.gate, runtime_gate_record=None)},
                "prerequisite:runtime_gate_record_missing",
            ),
            (
                "adaptation_not_ready",
                {"adaptation": replace(self.adaptation, order=None)},
                "prerequisite:adaptation_not_ready",
            ),
            ("mandate_missing", {"mandate": None}, "prerequisite:mandate_missing"),
            ("payment_missing", {"payment": None}, "prerequisite:payment_missing"),
            (
                "fulfillment_missing",
                {"fulfillment": None},
                "prerequisite:fulfillment_missing",
            ),
        )
        for name, overrides, reason in cases:
            with self.subTest(name=name):
                outcome = self.assess(**overrides)
                self.assertFalse(outcome.ready)
                self.assertIsNone(outcome.effective_payment)
                self.assertIsNone(outcome.lifecycle)
                self.assertFalse(outcome.retry_allowed)
                self.assertIn(reason, outcome.reason_codes)

    def test_adapter_request_id_mismatch_fails_closed(self) -> None:
        adaptation = replace(
            self.adaptation,
            payment_request=replace(
                self.adaptation.payment_request,
                request_id="cross-composed-request",
            ),
        )
        outcome = self.assess(adaptation=adaptation)

        self.assertFalse(outcome.ready)
        self.assertIsNone(outcome.effective_payment)
        self.assertIsNone(outcome.lifecycle)
        self.assertFalse(outcome.retry_allowed)
        self.assertFalse(outcome.duplicate_payment_blocked)
        self.assertIn(
            "prerequisite:adapter_gate_request_mismatch",
            outcome.reason_codes,
        )

    def test_adapter_amount_mismatch_fails_closed(self) -> None:
        adaptation = replace(
            self.adaptation,
            payment_request=replace(
                self.adaptation.payment_request,
                amount=self.adaptation.payment_request.amount + Decimal("0.01"),
            ),
        )
        outcome = self.assess(adaptation=adaptation)

        self.assertFalse(outcome.ready)
        self.assertIsNone(outcome.effective_payment)
        self.assertIsNone(outcome.lifecycle)
        self.assertFalse(outcome.retry_allowed)
        self.assertFalse(outcome.duplicate_payment_blocked)
        self.assertIn(
            "prerequisite:adapter_gate_request_mismatch",
            outcome.reason_codes,
        )

    def test_adapter_currency_mismatch_fails_closed(self) -> None:
        adaptation = replace(
            self.adaptation,
            payment_request=replace(
                self.adaptation.payment_request,
                currency="EUR",
            ),
        )
        outcome = self.assess(adaptation=adaptation)

        self.assertFalse(outcome.ready)
        self.assertIsNone(outcome.effective_payment)
        self.assertIsNone(outcome.lifecycle)
        self.assertFalse(outcome.retry_allowed)
        self.assertFalse(outcome.duplicate_payment_blocked)
        self.assertIn(
            "prerequisite:adapter_gate_request_mismatch",
            outcome.reason_codes,
        )

    def test_full_canonical_adapter_gate_projection_passes(self) -> None:
        self.assertEqual(
            self.gate.bound_request,
            replace(
                self.adaptation.payment_request,
                agent_id=self.gate.bound_request.agent_id,
            ),
        )
        outcome = self.assess()
        self.assertTrue(outcome.ready)
        self.assertNotIn(
            "prerequisite:adapter_gate_request_mismatch",
            outcome.reason_codes,
        )

    def test_no_query_related_successful_attempt_blocks_duplicate_payment(self) -> None:
        existing = replace(
            self.payment,
            payment_id="webshop-payment-success-existing-no-query",
            status=PaymentStatus.SUCCEEDED,
            provider_ref="provider-success-existing-no-query",
        )
        outcome = self.assess(known_attempts=(existing,))

        self.assertTrue(outcome.ready)
        self.assertIsNone(outcome.query_recovery)
        self.assertTrue(outcome.duplicate_payment_blocked)
        self.assertFalse(outcome.retry_allowed)
        self.assertIn("duplicate:known_successful_attempt", outcome.reason_codes)
        self.assertIn("duplicate:payment_blocked", outcome.reason_codes)

    def test_no_query_related_unknown_and_pending_attempts_block_duplicate_payment(self) -> None:
        for status in (PaymentStatus.UNKNOWN, PaymentStatus.PENDING):
            existing = replace(
                self.payment,
                payment_id=f"webshop-payment-{status.value.lower()}-existing-no-query",
                status=status,
                provider_ref=f"provider-{status.value.lower()}-existing-no-query",
            )
            with self.subTest(status=status.value):
                outcome = self.assess(known_attempts=(existing,))
                self.assertTrue(outcome.ready)
                self.assertIsNone(outcome.query_recovery)
                self.assertTrue(outcome.duplicate_payment_blocked)
                self.assertFalse(outcome.retry_allowed)
                self.assertIn(
                    "duplicate:known_unresolved_attempt",
                    outcome.reason_codes,
                )
                self.assertIn("duplicate:payment_blocked", outcome.reason_codes)

    def test_no_query_unrelated_attempt_does_not_set_duplicate_block(self) -> None:
        unrelated = replace(
            self.payment,
            payment_id="webshop-payment-unrelated-no-query",
            request_id="different-business-request",
            status=PaymentStatus.SUCCEEDED,
            provider_ref="provider-unrelated-no-query",
        )
        outcome = self.assess(known_attempts=(unrelated,))

        self.assertTrue(outcome.ready)
        self.assertIsNone(outcome.query_recovery)
        self.assertFalse(outcome.duplicate_payment_blocked)
        self.assertFalse(outcome.retry_allowed)
        self.assertNotIn("duplicate:payment_blocked", outcome.reason_codes)

    def test_no_query_known_attempts_never_create_retry_candidate(self) -> None:
        failed = replace(
            self.payment,
            payment_id="webshop-payment-failed-existing-no-query",
            status=PaymentStatus.FAILED,
            provider_ref="provider-failed-existing-no-query",
        )
        outcome = self.assess(known_attempts=(failed,))

        self.assertTrue(outcome.ready)
        self.assertIsNone(outcome.query_recovery)
        self.assertFalse(outcome.duplicate_payment_blocked)
        self.assertFalse(outcome.retry_allowed)
        self.assertIn("retry:not_allowed", outcome.reason_codes)

    def test_payment_success_and_fulfillment_success_complete_user_task(self) -> None:
        payment = replace(self.payment, status=PaymentStatus.SUCCEEDED)
        fulfillment = replace(self.fulfillment, status=FulfillmentStatus.SUCCEEDED)
        outcome = self.assess(payment=payment, fulfillment=fulfillment)

        self.assertTrue(outcome.ready)
        self.assertEqual(PaymentStatus.SUCCEEDED, outcome.effective_payment.status)
        self.assertEqual(TaskStatus.SUCCEEDED, outcome.lifecycle.task_status)
        self.assertEqual(RemediationStatus.NOT_REQUIRED, outcome.lifecycle.remediation.status)
        self.assertFalse(outcome.retry_allowed)
        self.assertFalse(outcome.duplicate_payment_blocked)

    def test_payment_success_and_fulfillment_failure_require_remediation(self) -> None:
        payment = replace(self.payment, status=PaymentStatus.SUCCEEDED)
        fulfillment = replace(
            self.fulfillment,
            status=FulfillmentStatus.FAILED,
            failure_code="merchant_did_not_fulfil",
        )
        outcome = self.assess(payment=payment, fulfillment=fulfillment)

        self.assertTrue(outcome.ready)
        self.assertEqual(TaskStatus.FAILED, outcome.lifecycle.task_status)
        self.assertEqual(RemediationStatus.REQUIRED, outcome.lifecycle.remediation.status)
        self.assertIn("lifecycle:fulfillment_failed_after_payment", outcome.reason_codes)

    def test_payment_success_and_pending_fulfillment_remain_pending(self) -> None:
        payment = replace(self.payment, status=PaymentStatus.SUCCEEDED)
        outcome = self.assess(payment=payment)
        self.assertTrue(outcome.ready)
        self.assertEqual(TaskStatus.PENDING, outcome.lifecycle.task_status)
        self.assertEqual(FulfillmentStatus.PENDING, outcome.lifecycle.fulfillment_status)

    def test_failed_payment_never_becomes_task_success(self) -> None:
        payment = replace(self.payment, status=PaymentStatus.FAILED)
        fulfillment = replace(self.fulfillment, status=FulfillmentStatus.SUCCEEDED)
        outcome = self.assess(payment=payment, fulfillment=fulfillment)
        self.assertTrue(outcome.ready)
        self.assertEqual(TaskStatus.FAILED, outcome.lifecycle.task_status)
        self.assertNotEqual(TaskStatus.SUCCEEDED, outcome.lifecycle.task_status)

    def test_trusted_query_recovers_unknown_payment_to_succeeded(self) -> None:
        query = self.observation(PaymentStatus.SUCCEEDED, minutes=1, source="query")
        fulfillment = replace(self.fulfillment, status=FulfillmentStatus.SUCCEEDED)
        outcome = self.assess(query_observation=query, fulfillment=fulfillment)

        self.assertTrue(outcome.ready)
        self.assertEqual(PaymentRecoveryStatus.RECOVERED, outcome.query_recovery.recovery_status)
        self.assertEqual(PaymentStatus.SUCCEEDED, outcome.effective_payment.status)
        self.assertEqual(TaskStatus.SUCCEEDED, outcome.lifecycle.task_status)
        self.assertFalse(outcome.retry_allowed)

    def test_pending_query_remains_unresolved_and_never_retries(self) -> None:
        payment = replace(self.payment, status=PaymentStatus.PENDING)
        query = replace(
            self.observation(PaymentStatus.PENDING, minutes=1, source="query"),
            payment_id=payment.payment_id,
            order_id=payment.order_id,
            provider_ref=payment.provider_ref,
        )
        outcome = self.assess(payment=payment, query_observation=query)

        self.assertTrue(outcome.ready)
        self.assertEqual(PaymentRecoveryStatus.UNRESOLVED, outcome.query_recovery.recovery_status)
        self.assertEqual(PaymentStatus.PENDING, outcome.effective_payment.status)
        self.assertEqual(TaskStatus.PENDING, outcome.lifecycle.task_status)
        self.assertFalse(outcome.retry_allowed)

    def test_query_async_terminal_conflict_never_implies_success(self) -> None:
        query = self.observation(PaymentStatus.SUCCEEDED, minutes=1, source="query")
        async_observation = self.observation(
            PaymentStatus.FAILED,
            minutes=2,
            source="async",
        )
        fulfillment = replace(self.fulfillment, status=FulfillmentStatus.SUCCEEDED)
        outcome = self.assess(
            query_observation=query,
            async_observation=async_observation,
            fulfillment=fulfillment,
        )

        self.assertTrue(outcome.ready)
        self.assertEqual(PaymentStatusConflictResolution.CONFLICT, outcome.status_conflict.resolution)
        self.assertEqual(PaymentStatus.UNKNOWN, outcome.effective_payment.status)
        self.assertEqual(TaskStatus.UNKNOWN, outcome.lifecycle.task_status)
        self.assertFalse(outcome.retry_allowed)
        self.assertIn("sidecar:status_evidence_conflict", outcome.reason_codes)

    def test_query_async_monotonic_confirmation_can_drive_lifecycle(self) -> None:
        query = self.observation(PaymentStatus.PENDING, minutes=1, source="query")
        async_observation = self.observation(
            PaymentStatus.SUCCEEDED,
            minutes=2,
            source="async",
        )
        fulfillment = replace(self.fulfillment, status=FulfillmentStatus.SUCCEEDED)
        outcome = self.assess(
            query_observation=query,
            async_observation=async_observation,
            fulfillment=fulfillment,
        )

        self.assertTrue(outcome.ready)
        self.assertEqual(
            PaymentStatusConflictResolution.MONOTONIC_CONFIRMATION,
            outcome.status_conflict.resolution,
        )
        self.assertEqual(PaymentStatus.SUCCEEDED, outcome.effective_payment.status)
        self.assertEqual(TaskStatus.SUCCEEDED, outcome.lifecycle.task_status)

    def test_async_only_bound_observation_is_supported_without_retry(self) -> None:
        async_observation = self.observation(
            PaymentStatus.SUCCEEDED,
            minutes=2,
            source="async",
        )
        fulfillment = replace(self.fulfillment, status=FulfillmentStatus.SUCCEEDED)
        outcome = self.assess(
            async_observation=async_observation,
            fulfillment=fulfillment,
        )
        self.assertTrue(outcome.ready)
        self.assertEqual(PaymentStatus.SUCCEEDED, outcome.effective_payment.status)
        self.assertEqual(TaskStatus.SUCCEEDED, outcome.lifecycle.task_status)
        self.assertFalse(outcome.retry_allowed)
        self.assertIn("async:original_transaction_binding_match", outcome.reason_codes)

    def test_duplicate_successful_attempt_blocks_retry(self) -> None:
        query = self.observation(PaymentStatus.FAILED, minutes=1, source="query")
        existing = replace(
            self.payment,
            payment_id="webshop-payment-success-existing",
            status=PaymentStatus.SUCCEEDED,
            provider_ref="provider-success-existing",
        )
        outcome = self.assess(query_observation=query, known_attempts=(existing,))

        self.assertTrue(outcome.ready)
        self.assertTrue(outcome.duplicate_payment_blocked)
        self.assertFalse(outcome.retry_allowed)
        self.assertEqual(PaymentRecoveryStatus.BLOCKED, outcome.query_recovery.recovery_status)
        self.assertIn("duplicate:payment_blocked", outcome.reason_codes)

    def test_unresolved_parallel_attempt_blocks_retry(self) -> None:
        query = self.observation(PaymentStatus.FAILED, minutes=1, source="query")
        for status in (PaymentStatus.UNKNOWN, PaymentStatus.PENDING):
            attempt = replace(
                self.payment,
                payment_id=f"webshop-payment-{status.value.lower()}-existing",
                status=status,
                provider_ref=f"provider-{status.value.lower()}-existing",
            )
            with self.subTest(status=status.value):
                outcome = self.assess(
                    query_observation=query,
                    known_attempts=(attempt,),
                )
                self.assertTrue(outcome.ready)
                self.assertTrue(outcome.duplicate_payment_blocked)
                self.assertFalse(outcome.retry_allowed)

    def test_terminal_failed_can_be_offline_retry_candidate_without_execution(self) -> None:
        query = self.observation(PaymentStatus.FAILED, minutes=1, source="query")
        before = self.payment
        outcome = self.assess(query_observation=query)

        self.assertTrue(outcome.ready)
        self.assertEqual(PaymentRecoveryStatus.RETRY_CANDIDATE, outcome.query_recovery.recovery_status)
        self.assertTrue(outcome.retry_allowed)
        self.assertFalse(outcome.duplicate_payment_blocked)
        self.assertEqual(PaymentStatus.FAILED, outcome.effective_payment.status)
        self.assertEqual(before, self.payment)
        self.assertIn("retry:offline_candidate_only", outcome.reason_codes)

    def test_missing_idempotency_boundary_never_allows_retry(self) -> None:
        payment = replace(self.payment, idempotency_key=None)
        query = replace(
            self.observation(PaymentStatus.FAILED, minutes=1, source="query"),
            payment_id=payment.payment_id,
            order_id=payment.order_id,
            provider_ref=payment.provider_ref,
        )
        outcome = self.assess(payment=payment, query_observation=query)
        self.assertTrue(outcome.ready)
        self.assertFalse(outcome.retry_allowed)
        self.assertFalse(outcome.duplicate_payment_blocked)
        self.assertIn("recovery:idempotency_boundary_missing", outcome.reason_codes)

    def test_payment_binding_mismatch_fails_closed(self) -> None:
        payment = replace(self.payment, transaction_object_ref="request-other")
        outcome = self.assess(payment=payment)
        self.assertFalse(outcome.ready)
        self.assertEqual(TaskStatus.UNKNOWN, outcome.lifecycle.task_status)
        self.assertFalse(outcome.retry_allowed)
        self.assertIn("sidecar:lifecycle_binding_invalid", outcome.reason_codes)

    def test_fulfillment_binding_mismatch_fails_closed(self) -> None:
        fulfillment = replace(self.fulfillment, order_id="order-other")
        outcome = self.assess(fulfillment=fulfillment)
        self.assertFalse(outcome.ready)
        self.assertEqual(TaskStatus.UNKNOWN, outcome.lifecycle.task_status)
        self.assertIn("lifecycle:fulfillment_order_binding_mismatch", outcome.reason_codes)

    def test_query_binding_mismatch_blocks_recovery_and_success(self) -> None:
        query = self.observation(
            PaymentStatus.SUCCEEDED,
            minutes=1,
            source="query",
            payment_id="payment-other",
        )
        fulfillment = replace(self.fulfillment, status=FulfillmentStatus.SUCCEEDED)
        outcome = self.assess(query_observation=query, fulfillment=fulfillment)

        self.assertFalse(outcome.ready)
        self.assertEqual(PaymentStatus.UNKNOWN, outcome.effective_payment.status)
        self.assertEqual(TaskStatus.UNKNOWN, outcome.lifecycle.task_status)
        self.assertFalse(outcome.retry_allowed)
        self.assertIn("sidecar:recovery_binding_invalid", outcome.reason_codes)

    def test_inputs_are_immutable_and_effective_status_uses_a_copy(self) -> None:
        query = self.observation(PaymentStatus.SUCCEEDED, minutes=1, source="query")
        payment_before = self.payment
        fulfillment_before = self.fulfillment
        adaptation_before = self.adaptation
        gate_before = self.gate
        outcome = self.assess(query_observation=query)

        self.assertEqual(payment_before, self.payment)
        self.assertEqual(fulfillment_before, self.fulfillment)
        self.assertEqual(adaptation_before, self.adaptation)
        self.assertEqual(gate_before, self.gate)
        self.assertIsNot(outcome.initial_payment, outcome.effective_payment)
        self.assertEqual(PaymentStatus.UNKNOWN, outcome.initial_payment.status)
        self.assertEqual(PaymentStatus.SUCCEEDED, outcome.effective_payment.status)
        with self.assertRaises(FrozenInstanceError):
            outcome.ready = False  # type: ignore[misc]

    def test_to_dict_is_deterministic_and_primitive_only(self) -> None:
        query = self.observation(PaymentStatus.PENDING, minutes=1, source="query")
        async_observation = self.observation(
            PaymentStatus.SUCCEEDED,
            minutes=2,
            source="async",
        )
        outcome = self.assess(
            query_observation=query,
            async_observation=async_observation,
        )
        first = outcome.to_dict()
        second = outcome.to_dict()
        self.assertEqual(first, second)
        self.assertEqual("UNKNOWN", first["initial_payment"]["status"])
        self.assertEqual("SUCCEEDED", first["effective_payment"]["status"])
        self.assertEqual("MONOTONIC_CONFIRMATION", first["status_conflict"]["resolution"])
        self.assertTrue(REQUIRED_LIMITATIONS.issubset(set(first["limitations"])))
        json.dumps(first, ensure_ascii=False, sort_keys=True)

    def test_production_sidecar_has_no_file_network_process_environment_or_callback_action(self) -> None:
        source = SIDECAR_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports: set[str] = set()
        called: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module or "")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called.add(node.func.attr)
        for forbidden in (
            "gym",
            "web_agent_site",
            "pyserini",
            "flask",
            "selenium",
            "playwright",
            "requests",
            "urllib",
            "socket",
            "subprocess",
            "os",
            "pathlib",
        ):
            self.assertFalse(
                any(name == forbidden or name.startswith(forbidden + ".") for name in imports),
                imports,
            )
        self.assertTrue(
            called.isdisjoint(
                {
                    "open",
                    "read_text",
                    "write_text",
                    "getenv",
                    "run",
                    "Popen",
                    "urlopen",
                    "socket",
                    "checkout_callback",
                    "execute_payment",
                }
            ),
            called,
        )
        self.assertNotIn("click[buy now]", source.lower())
        self.assertNotIn("SimServer", source)

        with (
            patch.object(builtins, "open", side_effect=AssertionError("file forbidden")) as open_mock,
            patch.object(socket, "socket", side_effect=AssertionError("network forbidden")) as socket_mock,
            patch.object(subprocess, "run", side_effect=AssertionError("process forbidden")) as run_mock,
            patch.object(os, "getenv", side_effect=AssertionError("environment forbidden")) as getenv_mock,
            patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")) as urlopen_mock,
        ):
            outcome = self.assess()
        self.assertTrue(outcome.ready)
        open_mock.assert_not_called()
        socket_mock.assert_not_called()
        run_mock.assert_not_called()
        getenv_mock.assert_not_called()
        urlopen_mock.assert_not_called()

    def test_public_api_is_exported(self) -> None:
        self.assertTrue(callable(assess_webshop_payment_fulfilment))
        self.assertTrue(hasattr(WebShopPaymentFulfilmentOutcome, "__dataclass_fields__"))


if __name__ == "__main__":
    unittest.main()

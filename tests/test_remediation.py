import sys
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment import (
    DisputeRecord,
    DisputeStatus,
    RefundStatus,
    RemediationStatus,
    TaskStatus,
    assess_lifecycle,
    assess_remediation,
)
from agentic_payment_experiment.scenario_loader import load_scenario


class RemediationTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.scenario = load_scenario(
            root / "samples" / "scenarios" / "S11_full_refund_after_fulfillment_failure.json"
        )
        self.assertIsNotNone(self.scenario.final_order)
        self.assertIsNotNone(self.scenario.payment_execution)
        self.assertIsNotNone(self.scenario.fulfillment)
        self.assertIsNotNone(self.scenario.refund)
        self.base_lifecycle = assess_lifecycle(
            self.scenario.request,
            self.scenario.final_order,
            self.scenario.payment_execution,
            self.scenario.fulfillment,
        )

    def assess(self, *, refund=None, dispute=None):
        return assess_remediation(
            self.scenario.final_order,
            self.scenario.payment_execution,
            self.base_lifecycle,
            refund=self.scenario.refund if refund is None and dispute is None else refund,
            dispute=dispute,
        )

    def test_full_refund_resolves_economic_remediation_but_not_original_task(self) -> None:
        result = self.assess()
        self.assertEqual(RefundStatus.SUCCEEDED, result.refund_status)
        self.assertEqual(RemediationStatus.RESOLVED, result.remediation.status)
        self.assertEqual(TaskStatus.FAILED, result.task_status)
        self.assertEqual(
            "economic_remediation_completed_by_full_refund",
            result.remediation.next_action,
        )
        self.assertIn(
            "fulfillment_failed_after_payment",
            {item.code for item in result.issues},
        )
        evidence = {item.code: item for item in result.evidence}
        self.assertEqual("refund-s11", evidence["refund_record_ref"].observed)
        self.assertEqual("payment-s11", evidence["refund_payment_ref"].observed)
        self.assertEqual("order-s11", evidence["refund_order_ref"].observed)
        self.assertEqual("480.00", evidence["refund_amount_ref"].observed)
        self.assertEqual("SUCCEEDED", evidence["refund_status_ref"].observed)

    def test_successful_partial_refund_does_not_resolve_remediation(self) -> None:
        partial = replace(self.scenario.refund, amount=Decimal("200.00"))
        result = self.assess(refund=partial)
        self.assertEqual(RefundStatus.SUCCEEDED, result.refund_status)
        self.assertEqual(RemediationStatus.IN_PROGRESS, result.remediation.status)
        self.assertEqual(TaskStatus.FAILED, result.task_status)
        self.assertIn(
            "partial_refund_requires_further_remediation",
            {item.code for item in result.issues},
        )

    def test_refund_binding_errors_never_resolve_remediation(self) -> None:
        cases = {
            "payment": replace(self.scenario.refund, payment_id="payment-other"),
            "order": replace(self.scenario.refund, order_id="order-other"),
            "currency": replace(self.scenario.refund, currency="USD"),
            "amount": replace(self.scenario.refund, amount=Decimal("481.00")),
        }
        expected_codes = {
            "payment": "refund_payment_binding_mismatch",
            "order": "refund_order_binding_mismatch",
            "currency": "refund_currency_binding_mismatch",
            "amount": "refund_amount_exceeds_payment",
        }
        for name, refund in cases.items():
            with self.subTest(name=name):
                result = self.assess(refund=refund)
                self.assertNotEqual(RemediationStatus.RESOLVED, result.remediation.status)
                self.assertEqual(RemediationStatus.REQUIRED, result.remediation.status)
                self.assertEqual(TaskStatus.FAILED, result.task_status)
                self.assertIn(expected_codes[name], {item.code for item in result.issues})

    def test_dispute_binding_errors_never_resolve_remediation(self) -> None:
        base = DisputeRecord(
            dispute_id="dispute-s11",
            payment_id=self.scenario.payment_execution.payment_id,
            order_id=self.scenario.final_order.order_id,
            status=DisputeStatus.OPEN,
            opened_at=self.scenario.fulfillment.occurred_at,
            reason_code="fulfillment_failed",
            evidence_ref="dispute-evidence-s11",
        )
        cases = {
            "payment": replace(base, payment_id="payment-other"),
            "order": replace(base, order_id="order-other"),
        }
        expected_codes = {
            "payment": "dispute_payment_binding_mismatch",
            "order": "dispute_order_binding_mismatch",
        }
        for name, dispute in cases.items():
            with self.subTest(name=name):
                result = self.assess(refund=None, dispute=dispute)
                self.assertEqual(RemediationStatus.REQUIRED, result.remediation.status)
                self.assertNotEqual(RemediationStatus.RESOLVED, result.remediation.status)
                self.assertEqual(TaskStatus.FAILED, result.task_status)
                self.assertIn(expected_codes[name], {item.code for item in result.issues})

    def test_open_or_under_review_dispute_stays_in_progress(self) -> None:
        for status in (DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW):
            dispute = DisputeRecord(
                dispute_id=f"dispute-{status.value.lower()}",
                payment_id=self.scenario.payment_execution.payment_id,
                order_id=self.scenario.final_order.order_id,
                status=status,
                opened_at=self.scenario.fulfillment.occurred_at,
                reason_code="fulfillment_failed",
                evidence_ref="dispute-evidence-s11",
            )
            with self.subTest(status=status.value):
                result = self.assess(refund=None, dispute=dispute)
                self.assertEqual(status, result.dispute_status)
                self.assertEqual(RemediationStatus.IN_PROGRESS, result.remediation.status)
                self.assertNotEqual(RemediationStatus.RESOLVED, result.remediation.status)
                self.assertEqual(TaskStatus.FAILED, result.task_status)
                self.assertIn("dispute_requires_review", {item.code for item in result.issues})

    def test_resolved_dispute_without_outcome_does_not_resolve_economic_remediation(self) -> None:
        dispute = DisputeRecord(
            dispute_id="dispute-resolved",
            payment_id=self.scenario.payment_execution.payment_id,
            order_id=self.scenario.final_order.order_id,
            status=DisputeStatus.RESOLVED,
            opened_at=self.scenario.fulfillment.occurred_at,
            reason_code="fulfillment_failed",
            evidence_ref="dispute-evidence-s11",
        )
        result = self.assess(refund=None, dispute=dispute)
        self.assertEqual(DisputeStatus.RESOLVED, result.dispute_status)
        self.assertEqual(RemediationStatus.REQUIRED, result.remediation.status)
        self.assertNotEqual(RemediationStatus.RESOLVED, result.remediation.status)
        self.assertEqual("verify_dispute_resolution_outcome", result.remediation.next_action)
        self.assertEqual(TaskStatus.FAILED, result.task_status)
        self.assertIn(
            "dispute_resolution_outcome_unverified",
            {item.code for item in result.issues},
        )


if __name__ == "__main__":
    unittest.main()

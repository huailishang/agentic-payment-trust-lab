import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment import (
    FulfillmentStatus,
    PaymentStatus,
    RemediationStatus,
    TaskStatus,
    assess_lifecycle,
    validate_request,
)
from agentic_payment_experiment.scenario_loader import load_scenario


class LifecycleTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.scenario = load_scenario(
            root / "samples" / "scenarios" / "S10_fulfillment_failed_after_payment.json"
        )
        self.assertIsNotNone(self.scenario.final_order)
        self.assertIsNotNone(self.scenario.payment_execution)
        self.assertIsNotNone(self.scenario.fulfillment)

    def assess(self, *, payment=None, fulfillment=None):
        return assess_lifecycle(
            self.scenario.request,
            self.scenario.final_order,
            payment or self.scenario.payment_execution,
            fulfillment or self.scenario.fulfillment,
        )

    def test_s10_separates_prepayment_allow_from_failed_user_task(self) -> None:
        validation = validate_request(
            self.scenario.mandate,
            self.scenario.request,
            authorized_order=self.scenario.authorized_order,
            final_order=self.scenario.final_order,
        )
        lifecycle = self.assess()

        self.assertEqual("ALLOW", validation.decision.value)
        self.assertEqual(PaymentStatus.SUCCEEDED, lifecycle.payment_status)
        self.assertEqual(FulfillmentStatus.FAILED, lifecycle.fulfillment_status)
        self.assertEqual(RemediationStatus.REQUIRED, lifecycle.remediation.status)
        self.assertEqual(TaskStatus.FAILED, lifecycle.task_status)
        self.assertEqual(
            {"fulfillment_failed_after_payment"},
            {item.code for item in lifecycle.issues},
        )

    def test_s10_preserves_linked_evidence_for_later_remediation(self) -> None:
        lifecycle = self.assess()
        evidence = {item.code: item for item in lifecycle.evidence}

        self.assertEqual("request-s10", evidence["lifecycle_request_ref"].observed)
        self.assertEqual("order-s10", evidence["lifecycle_order_ref"].observed)
        self.assertEqual("payment-s10", evidence["payment_execution_ref"].observed)
        self.assertEqual("receipt-s10", evidence["payment_receipt_ref"].observed)
        self.assertEqual("fulfillment-s10", evidence["fulfillment_ref"].observed)
        self.assertEqual(
            "merchant-delivery-failure-s10",
            evidence["fulfillment_evidence_ref"].observed,
        )
        self.assertEqual("delivery_failed", evidence["fulfillment_failure_code"].observed)
        self.assertEqual(
            "preserve_evidence_and_start_remediation",
            lifecycle.remediation.next_action,
        )

    def test_successful_payment_and_successful_fulfillment_complete_task(self) -> None:
        fulfillment = replace(
            self.scenario.fulfillment,
            status=FulfillmentStatus.SUCCEEDED,
            failure_code=None,
        )
        lifecycle = self.assess(fulfillment=fulfillment)

        self.assertEqual(TaskStatus.SUCCEEDED, lifecycle.task_status)
        self.assertEqual(RemediationStatus.NOT_REQUIRED, lifecycle.remediation.status)
        self.assertEqual((), lifecycle.issues)

    def test_binding_mismatch_is_unknown_not_success(self) -> None:
        payment = replace(self.scenario.payment_execution, order_id="order-other")
        lifecycle = self.assess(payment=payment)

        self.assertEqual(TaskStatus.UNKNOWN, lifecycle.task_status)
        self.assertEqual(RemediationStatus.REQUIRED, lifecycle.remediation.status)
        self.assertIn(
            "payment_order_binding_mismatch",
            {item.code for item in lifecycle.issues},
        )

    def test_payment_failed_does_not_mark_task_successful(self) -> None:
        payment = replace(self.scenario.payment_execution, status=PaymentStatus.FAILED)
        lifecycle = self.assess(payment=payment)

        self.assertEqual(TaskStatus.FAILED, lifecycle.task_status)
        self.assertEqual(RemediationStatus.NOT_REQUIRED, lifecycle.remediation.status)
        self.assertEqual(
            {"payment_execution_failed"},
            {item.code for item in lifecycle.issues},
        )


if __name__ == "__main__":
    unittest.main()

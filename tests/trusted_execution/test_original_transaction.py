from __future__ import annotations
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from agentic_payment_experiment.models import DisputeRecord, DisputeStatus, PaymentExecutionRecord, PaymentStatus, PaymentStatusObservation, RefundRecord, RefundStatus
from agentic_payment_experiment.trusted_execution import FollowUpAction, VerificationStatus, verify_original_transaction

class OriginalTransactionTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,7,11,tzinfo=timezone.utc)
        self.payment=PaymentExecutionRecord("pay-1","req-1","order-1",PaymentStatus.SUCCEEDED,Decimal("10"),"CNY",self.now,provider_ref="provider-1")
    def test_all_actions_bind_original_transaction(self):
        cases=(
          (FollowUpAction.STATUS_QUERY,PaymentStatusObservation("pay-1","order-1",PaymentStatus.SUCCEEDED,self.now,"offline",provider_ref="provider-1")),
          (FollowUpAction.ASYNC_STATUS_NOTIFICATION,PaymentStatusObservation("pay-1","order-1",PaymentStatus.SUCCEEDED,self.now,"offline-async",provider_ref="provider-1")),
          (FollowUpAction.REFUND,RefundRecord("refund-1","pay-1","order-1",RefundStatus.SUCCEEDED,Decimal("10"),"CNY",self.now)),
          (FollowUpAction.DISPUTE,DisputeRecord("dispute-1","pay-1","order-1",DisputeStatus.OPEN,self.now)),)
        for action, follow_up in cases:
            with self.subTest(action=action):
                fact=verify_original_transaction(action,self.payment,follow_up)
                self.assertEqual(VerificationStatus.VALID,fact.status)
                self.assertEqual(("original_transaction_binding_match",),fact.reason_codes)
    def test_mismatches_missing_provider_and_unknown_action_fail_closed(self):
        wrong=PaymentStatusObservation("pay-x","order-x",PaymentStatus.SUCCEEDED,self.now,"offline",provider_ref="provider-x")
        fact=verify_original_transaction(FollowUpAction.STATUS_QUERY,self.payment,wrong)
        self.assertEqual(VerificationStatus.INVALID,fact.status)
        self.assertIn("original_transaction_payment_ref_mismatch",fact.reason_codes)
        self.assertIn("original_transaction_order_ref_mismatch",fact.reason_codes)
        self.assertIn("original_transaction_provider_ref_mismatch",fact.reason_codes)
        missing=PaymentStatusObservation("pay-1","order-1",PaymentStatus.SUCCEEDED,self.now,"offline")
        self.assertEqual(VerificationStatus.INVALID,verify_original_transaction(FollowUpAction.STATUS_QUERY,self.payment,missing).status)
        async_missing=verify_original_transaction(FollowUpAction.ASYNC_STATUS_NOTIFICATION,self.payment,missing)
        self.assertEqual(VerificationStatus.INVALID,async_missing.status)
        self.assertEqual(("original_transaction_provider_ref_missing",),async_missing.reason_codes)
        async_wrong=verify_original_transaction(FollowUpAction.ASYNC_STATUS_NOTIFICATION,self.payment,wrong)
        self.assertEqual(VerificationStatus.INVALID,async_wrong.status)
        self.assertIn("original_transaction_payment_ref_mismatch",async_wrong.reason_codes)
        self.assertIn("original_transaction_order_ref_mismatch",async_wrong.reason_codes)
        self.assertIn("original_transaction_provider_ref_mismatch",async_wrong.reason_codes)
        self.assertEqual(VerificationStatus.INVALID,verify_original_transaction("REVERSAL",self.payment,missing).status)

if __name__ == "__main__": unittest.main()

"""H68 local SQLite recovery and delivery tests; provider fixtures are synthetic."""
import hashlib
import hmac
import json
import secrets
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from agentic_payment_experiment.stripe_checkout_lab import StripeLabLedger
from agentic_payment_experiment.adapters.stripe_checkout import StripeCheckoutError
from agentic_payment_experiment.models import PaymentStatus, PaymentStatusObservation
from tests.test_stripe_checkout_adapter import NOW, valid_context

RESOURCE = b"synthetic client resource"
SHA = hashlib.sha256(RESOURCE).hexdigest()


class StripeLabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "h68-private.sqlite3"
        self.store = StripeLabLedger(self.database)
        self.context = valid_context()
        self.op = "operation-001"
        self.sid = "cs_test_original_one"
        self.store.register(
            operation_id=self.op, run_id="run-001", case_id="N01",
            order_id="order-h68", request_id="request-h68",
            payment_id="payment-h68", resource_sha256=SHA,
        )

    def session(self):
        return {
            "id": self.sid, "livemode": False,
            "mode": "payment", "currency": "usd", "amount_total": 100,
            "client_reference_id": "order-h68",
            "payment_status": "unpaid", "status": "open",
            "metadata": {
                "h68_run_id": "run-001",
                "h68_operation_id": self.op,
                "h68_resource_sha256": SHA,
            },
        }

    def paid(self):
        session = dict(self.session(), payment_status="paid", status="complete",
                       payment_intent="pi_test_original_one")
        intent = {
            "id": "pi_test_original_one", "livemode": False, "status": "succeeded",
            "latest_charge": "ch_test_original_one", "amount": 100, "currency": "usd",
        }
        charge = {
            "id": "ch_test_original_one", "livemode": False, "status": "succeeded",
            "paid": True, "captured": True, "amount": 100, "currency": "usd",
            "payment_intent": "pi_test_original_one",
        }
        return session, intent, charge

    def test_persisted_session_cannot_be_replaced_after_restart(self):
        self.store.bind_session(self.op, self.session())
        reopened = StripeLabLedger(self.database)
        self.assertEqual(self.sid, reopened.get(self.op)["session_id"])
        with self.assertRaisesRegex(StripeCheckoutError, "second_session"):
            reopened.bind_session(self.op, dict(self.session(), id="cs_test_replacement"))
        self.assertEqual(self.sid, reopened.get(self.op)["session_id"])

    def test_paid_query_required_for_delivery_and_unique_receipt(self):
        self.store.bind_session(self.op, self.session())
        with self.assertRaisesRegex(StripeCheckoutError, "unpaid_order_cannot_deliver"):
            self.store.record_client_delivery(self.op, RESOURCE)
        session, intent, charge = self.paid()
        self.assertEqual("PAID_CONFIRMED", self.store.observe(self.op, session, intent, charge))
        receipt = self.store.record_client_delivery(self.op, RESOURCE)
        self.assertTrue(receipt.startswith("delivery-"))
        after_restart = StripeLabLedger(self.database)
        self.assertEqual(receipt, after_restart.record_client_delivery(self.op, RESOURCE))
        self.assertEqual(1, len(after_restart.delivery_history(self.op)))

    def test_cancel_query_and_no_client_delivery(self):
        self.store.bind_session(self.op, self.session())
        cancelled = dict(self.session(), status="expired", payment_status="unpaid")
        self.assertEqual("CANCELLED", self.store.observe(self.op, cancelled, None, None))
        with self.assertRaisesRegex(StripeCheckoutError, "unpaid_order_cannot_deliver"):
            self.store.record_client_delivery(self.op, RESOURCE)
        self.assertEqual([], self.store.delivery_history(self.op))

    def test_unknown_recovery_reuses_original_session(self):
        self.store.bind_session(self.op, self.session())
        self.store.mark_unknown(self.op)
        restarted = StripeLabLedger(self.database)
        self.assertEqual("UNKNOWN", restarted.get(self.op)["state"])
        session, intent, charge = self.paid()
        restarted.observe(self.op, session, intent, charge)
        unknown = replace(self.context.execution, status=PaymentStatus.UNKNOWN,
                          provider_ref=self.sid)
        observed = PaymentStatusObservation(
            payment_id=unknown.payment_id, order_id=unknown.order_id,
            status=PaymentStatus.SUCCEEDED, observed_at=NOW+timedelta(minutes=1),
            source="stripe_api", provider_ref=self.sid,
        )
        outcome = restarted.recover_original(self.op, unknown, observed)
        self.assertFalse(outcome.retry_allowed)
        self.assertEqual("RECOVERED", outcome.recovery_status.value)
        self.assertEqual(self.sid, restarted.get(self.op)["session_id"])

    def test_delivery_failure_then_unique_recovery(self):
        self.store.bind_session(self.op, self.session())
        self.store.observe(self.op, *self.paid())
        self.assertIsNone(self.store.record_client_delivery(
            self.op, RESOURCE, inject_failure=True))
        receipt = self.store.record_client_delivery(self.op, RESOURCE)
        self.assertEqual(receipt, self.store.record_client_delivery(self.op, RESOURCE))
        self.assertEqual(["FAILED", "SUCCEEDED"], [
            row["state"] for row in self.store.delivery_history(self.op)
        ])

    def test_webhook_is_recorded_once_without_automatic_paid_transition(self):
        self.store.bind_session(self.op, self.session())
        secret = "whsec_" + secrets.token_hex(16)
        ts = int(NOW.timestamp())
        raw = json.dumps({
            "id": "evt_synthetic_1", "livemode": False,
            "type": "checkout.session.completed",
            "data": {"object": {"id": self.sid}},
        }, separators=(",", ":")).encode()
        mac = hmac.new(secret.encode(), str(ts).encode()+b"."+raw,
                       hashlib.sha256).hexdigest()
        sig = f"t={ts},v1={mac}"
        self.assertTrue(self.store.ingest_webhook(
            operation_id=self.op, body=raw, signature=sig,
            test_secret=secret, received_at=NOW))
        self.assertFalse(self.store.ingest_webhook(
            operation_id=self.op, body=raw, signature=sig,
            test_secret=secret, received_at=NOW))
        self.assertEqual("SESSION_OPEN", self.store.get(self.op)["state"])


if __name__ == "__main__":
    unittest.main()

"""H68 dry-run tests; no live Stripe requests, no embedded keys."""
import hashlib
import hmac
import json
import secrets
import sys
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment.adapters.stripe_checkout import (
    CheckoutReceipt, GateContext, StripeCheckoutAdapter,
    StripeCheckoutError, StripeTestAPI, verify_webhook,
)
from agentic_payment_experiment.models import (
    AgentIdentity, Decision, IntentMandate, Order, OrderItem,
    PaymentExecutionRecord, PaymentStatus, TransactionRequest,
)
from agentic_payment_experiment.payment_execution import (
    PAYMENT_CONTEXT_ACTION, PAYMENT_REQUIRED_SOURCE_PATHS,
)
from agentic_payment_experiment.trusted_execution import SourceType, evaluate_context_policy
from agentic_payment_experiment.trusted_execution.confirmation import create_confirmation_record

NOW = datetime(2026, 11, 12, 1, 0, tzinfo=timezone.utc)
SHA = hashlib.sha256(b"synthetic H68 resource").hexdigest()


class FakeStripe:
    def __init__(self):
        self.created, self.queries = [], []
        self.session = {
            "id": "cs_test_fixture", "livemode": False,
            "url": "https://checkout.stripe.com/c/pay/synthetic",
            "mode": "payment", "currency": "usd", "amount_total": 100,
            "client_reference_id": "order-h68", "payment_status": "unpaid",
            "status": "open", "metadata": {"h68_resource_sha256": SHA,
                                            "h68_run_id": "run-h68",
                                            "h68_operation_id": "operation-h68"},
        }

    def create_session(self, payload, *, idempotency_key):
        self.created.append((payload, idempotency_key))
        return self.session.copy()

    def get_session(self, session_id):
        self.queries.append(session_id)
        return self.session.copy()


def valid_context():
    mandate = IntentMandate(
        "mandate-h68", "synthetic-user", Decimal("1.00"),
        frozenset({"synthetic-merchant"}), frozenset({"digital"}),
        NOW + timedelta(hours=1), expected_agent_id="agent-h68", currency="usd",
    )
    order = Order(
        "order-h68", "v1", "synthetic-merchant", "synthetic-payee",
        (OrderItem("resource", "Synthetic digital resource", "digital", 1, Decimal("1.00")),),
        Decimal("1.00"), "usd", NOW + timedelta(minutes=30), "download once",
        mandate.mandate_id, authority_version_ref=mandate.authority_version,
    )
    req = TransactionRequest(
        "request-h68", Decimal("1.00"), order.merchant, "digital",
        NOW - timedelta(seconds=1), agent_id="agent-h68", currency="usd",
        order_ref=order.order_id, authority_ref=mandate.mandate_id,
        authority_version_ref=mandate.authority_version, payee=order.payee,
    )
    payment = PaymentExecutionRecord(
        "payment-h68", req.request_id, order.order_id, PaymentStatus.PENDING,
        Decimal("1.00"), "usd", NOW, authority_ref=mandate.mandate_id,
        agent_ref="agent-h68", transaction_object_ref=req.request_id, payee=order.payee,
    )
    identity = AgentIdentity("agent-h68", "local-test", "h68-executor")
    sources = {
        "mandate.mandate_id": SourceType.USER_CONFIRMED,
        "final_order.order_id": SourceType.USER_CONFIRMED,
        "request.request_id": SourceType.PROTOCOL_VERIFIED,
        "request.agent_id": SourceType.USER_CONFIRMED,
        "request.amount": SourceType.USER_CONFIRMED,
        "request.payee": SourceType.USER_CONFIRMED,
        "request.currency": SourceType.USER_CONFIRMED,
    }
    fact = evaluate_context_policy({
        "mandate": {"mandate_id": mandate.mandate_id},
        "final_order": {"order_id": order.order_id},
        "request": {"request_id": req.request_id, "agent_id": req.agent_id,
                    "amount": req.amount, "payee": req.payee, "currency": req.currency},
    }, trusted_sources=sources, required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
       current_action=PAYMENT_CONTEXT_ACTION).fact
    confirmation = create_confirmation_record(
        confirmation_id="confirm-h68", authority_id=mandate.mandate_id,
        authority_version=mandate.authority_version, order=order,
        confirmed_at=NOW - timedelta(seconds=2),
        expires_at=NOW + timedelta(minutes=30),
    )
    return GateContext(mandate, order, req, payment, identity, fact,
                       identity.provider, identity.executor_instance_id,
                       Decision.ALLOW, confirmation)


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeStripe()
        self.adapter = StripeCheckoutAdapter(self.client)
        self.ctx = valid_context()

    def create(self, ctx=None, **changes):
        kwargs = dict(run_id="run-h68", operation_id="operation-h68",
                      resource_sha256=SHA, success_url="http://127.0.0.1:8768/success",
                      cancel_url="http://127.0.0.1:8768/cancel", now=NOW)
        kwargs.update(changes)
        return self.adapter.create_session(ctx or self.ctx, **kwargs)

    def test_valid_gate_creates_one_session_and_redacts_url_from_repr(self):
        out = self.create()
        self.assertIsInstance(out, CheckoutReceipt)
        self.assertEqual(1, len(self.client.created))
        self.assertEqual("ALLOW", out.gate.final_decision.value)
        self.assertEqual(1, out.gate.callback_count)
        self.assertEqual(out.session_id, out.gate.callback_result_ref)
        self.assertNotIn("checkout.stripe.com", repr(out))
        self.assertEqual("100", self.client.created[0][0]["line_items[0][price_data][unit_amount]"])

    def test_nonallow_wrong_binding_and_wrong_amount_create_no_session(self):
        for ctx in (
            replace(self.ctx, prepayment_decision=Decision.DENY),
            replace(self.ctx, prepayment_decision=Decision.INDETERMINATE),
            replace(self.ctx, execution=replace(self.ctx.execution, request_id="wrong")),
            replace(self.ctx, order=replace(self.ctx.order, total_amount=Decimal("2.00"))),
        ):
            with self.subTest(ctx=ctx.prepayment_decision):
                self.assertFalse(self.create(ctx).callback_executed)
        self.assertEqual([], self.client.created)

    def test_browser_gate_rechecks_native_amount_and_nonallow(self):
        clicked = []
        gate = self.adapter.authorize_browser_payment(
            self.ctx, session_id="cs_test_fixture", now=NOW, resource_sha256=SHA,
            browser_payment=clicked.append, run_id="run-h68", operation_id="operation-h68")
        self.assertTrue(gate.callback_executed)
        self.assertEqual(1, len(clicked))
        clicked.clear()
        self.client.session["amount_total"] = 101
        with self.assertRaisesRegex(StripeCheckoutError, "prepay_native_state_mismatch"):
            self.adapter.authorize_browser_payment(
                self.ctx, session_id="cs_test_fixture", now=NOW, resource_sha256=SHA,
                browser_payment=clicked.append, run_id="run-h68", operation_id="operation-h68")
        self.assertEqual([], clicked)
        self.client.queries.clear()
        blocked = self.adapter.authorize_browser_payment(
            replace(self.ctx, prepayment_decision=Decision.DENY),
            session_id="cs_test_fixture", now=NOW, resource_sha256=SHA,
            browser_payment=clicked.append, run_id="run-h68", operation_id="operation-h68")
        self.assertFalse(blocked.callback_executed)
        self.assertEqual([], self.client.queries)

    def test_rejects_unsafe_return_url_or_live_session(self):
        with self.assertRaisesRegex(StripeCheckoutError, "unsafe_return_url"):
            self.create(success_url="https://example.org/success")
        self.assertEqual([], self.client.created)
        self.client.session["livemode"] = True
        with self.assertRaisesRegex(StripeCheckoutError, "unexpected_session_response"):
            self.create()

    def test_browser_refuses_foreign_run_and_operation_without_click(self):
        clicked = []
        for key, replacement in (("h68_run_id", "other-run"),
                                 ("h68_operation_id", "other-operation")):
            with self.subTest(key=key):
                original = self.client.session["metadata"][key]
                self.client.session["metadata"][key] = replacement
                try:
                    with self.assertRaisesRegex(StripeCheckoutError, "prepay_native_state_mismatch"):
                        self.adapter.authorize_browser_payment(
                            self.ctx, session_id="cs_test_fixture", now=NOW,
                            resource_sha256=SHA, run_id="run-h68",
                            operation_id="operation-h68", browser_payment=clicked.append)
                finally:
                    self.client.session["metadata"][key] = original
        self.assertEqual([], clicked)

    def test_direct_payment_post_is_outside_transport(self):
        api = StripeTestAPI.__new__(StripeTestAPI)
        with self.assertRaisesRegex(StripeCheckoutError, "post_path_not_allowed"):
            api._request("POST", "/v1/payment_intents", {}, "test")
        with self.assertRaisesRegex(StripeCheckoutError, "non_test_key_rejected"):
            StripeTestAPI("not-a-test-key")


class WebhookTests(unittest.TestCase):
    def setUp(self):
        self.secret = "whsec_" + secrets.token_hex(16)
        self.received = NOW

    def signed(self, *, old=0, live=False):
        ts = int(NOW.timestamp()) - old
        raw = json.dumps({"id": "evt_synthetic", "livemode": live,
                          "type": "checkout.session.completed",
                          "data": {"object": {"id": "cs_test_fixture"}}},
                         separators=(",", ":")).encode()
        mac = hmac.new(self.secret.encode(), str(ts).encode() + b"." + raw,
                       hashlib.sha256).hexdigest()
        return raw, f"t={ts},v1={mac}"

    def test_verifies_bytes_and_rejects_alterations_staleness_and_live(self):
        raw, header = self.signed()
        self.assertEqual("checkout.session.completed",
                         verify_webhook(raw, header, self.secret, self.received)["type"])
        invalid = [
            (raw+b" ", header, self.secret),
            (raw, header, "whsec_" + secrets.token_hex(16)),
            (*self.signed(old=301), self.secret),
            (*self.signed(live=True), self.secret),
        ]
        for body, sig, secret in invalid:
            with self.subTest(reason=sig[:2]):
                with self.assertRaises(StripeCheckoutError):
                    verify_webhook(body, sig, secret, self.received)


if __name__ == "__main__":
    unittest.main()

"""H74: synthetic-only, native Windows agent durable authority checks."""
from __future__ import annotations

import hashlib
from contextlib import closing
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from agentic_payment_experiment.adapters.stripe_checkout import (
    CheckoutReceipt, StripeCheckoutAdapter, StripeCheckoutError,
)
from agentic_payment_experiment.models import PaymentStatus, PaymentStatusObservation
from agentic_payment_experiment.stripe_checkout_lab import StripeLabLedger
from agentic_payment_experiment.stripe_authority_context import _encode
from tests.test_stripe_checkout_adapter import NOW, SHA, FakeStripe, valid_context

ROOT = Path(__file__).resolve().parents[1]
OP = "operation-h68"
RUN = "run-h68"
RESOURCE = b"synthetic H68 resource"
SUCCESS = "http://127.0.0.1:8768/success"
CANCEL = "http://127.0.0.1:8768/cancel"


def graph_sha(ctx):
    return hashlib.sha256(json.dumps(
        _encode(ctx), ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()


class _Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "synthetic.sqlite3"
        self.store = StripeLabLedger(self.db)
        self.ctx = valid_context()
        self.store.register(operation_id=OP, run_id=RUN, case_id="N01",
            order_id=self.ctx.order.order_id, request_id=self.ctx.request.request_id,
            payment_id=self.ctx.execution.payment_id, resource_sha256=SHA)
        self.client = FakeStripe()
        self.adapter = StripeCheckoutAdapter(self.client)

    def recorded(self, ctx=None):
        return self.store.record_authority(
            OP, ctx or self.ctx, resource_sha256=SHA, recorded_at=NOW)

    def reopened(self):
        return StripeLabLedger(self.db)

    def stored_create(self, store=None, sha=None, now=NOW):
        return self.adapter.create_stored_session(
            store or self.store, operation_id=OP,
            expected_authority_sha256=sha or self.ref,
            success_url=SUCCESS, cancel_url=CANCEL, now=now)

    def stored_pay(self, store=None, sha=None, now=NOW, clicked=None):
        return self.adapter.authorize_stored_browser_payment(
            store or self.store, operation_id=OP,
            expected_authority_sha256=sha or self.ref, now=now,
            browser_payment=(clicked if clicked is not None else []).append)

    def session(self):
        return self.client.session.copy()


class AuthorityStoreCases(_Fixture):
    def test_original_roundtrip_all_types_and_confirmation_provenance(self):
        self.ref = self.recorded()
        reloaded = self.reopened().load_authority(OP, expected_sha256=self.ref)
        self.assertEqual(self.ctx, reloaded)
        self.assertEqual(graph_sha(self.ctx), graph_sha(reloaded))
        self.assertEqual(self.ctx.confirmation_record.authorized_order_content,
                         reloaded.confirmation_record.authorized_order_content)
        self.assertEqual(self.ctx.confirmation_record.confirmed_at,
                         reloaded.confirmation_record.confirmed_at)
        with closing(sqlite3.connect(self.db)) as con:
            row = con.execute("SELECT snapshot_sha256,payload_json FROM authority_contexts").fetchone()
        self.assertEqual(self.ref, row[0])
        self.assertEqual(self.ref, hashlib.sha256(row[1].encode("utf-8")).hexdigest())

    def test_cold_child_process_deserializes_original_graph(self):
        self.ref = self.recorded()
        script = (
            "import sys,json,hashlib;"
            "from agentic_payment_experiment.stripe_checkout_lab import StripeLabLedger;"
            "from agentic_payment_experiment.stripe_authority_context import _encode;"
            "c=StripeLabLedger(sys.argv[1]).load_authority(sys.argv[2],expected_sha256=sys.argv[3]);"
            "raw=json.dumps(_encode(c),sort_keys=True,ensure_ascii=False,separators=(',',':'));"
            "print(json.dumps({'graph':hashlib.sha256(raw.encode('utf-8')).hexdigest(),"
            "'confirmed_at':c.confirmation_record.confirmed_at.isoformat(),"
            "'authority_version':c.mandate.authority_version}))"
        )
        child = subprocess.run([sys.executable, "-B", "-c", script,
            str(self.db), OP, self.ref], cwd=ROOT, capture_output=True,
            text=True, env=os.environ.copy(), timeout=20)
        self.assertEqual(child.returncode, 0, child.stderr)
        observed = json.loads(child.stdout)
        self.assertEqual(graph_sha(self.ctx), observed["graph"])
        self.assertEqual(self.ctx.confirmation_record.confirmed_at.isoformat(),
                         observed["confirmed_at"])
        self.assertEqual(self.ctx.mandate.authority_version, observed["authority_version"])

    def test_idempotent_original_and_conflicting_replacement_denied(self):
        self.ref = self.recorded()
        self.assertEqual(self.ref, self.recorded())
        with self.assertRaises(StripeCheckoutError):
            self.recorded(replace(self.ctx, order=replace(self.ctx.order, order_version="v2")))
        with closing(sqlite3.connect(self.db)) as con:
            self.assertEqual(1, con.execute("SELECT count(*) FROM authority_contexts").fetchone()[0])
        self.assertEqual(self.ctx, self.reopened().load_authority(OP, expected_sha256=self.ref))


class StoredAdapterCases(_Fixture):
    def test_stored_create_and_pay_use_db_graph_before_callback(self):
        self.ref = self.recorded()
        self.ctx = replace(self.ctx, prepayment_decision=self.ctx.prepayment_decision)
        observations = []
        client = self.client
        store = self.reopened()

        def checked_create(payload, *, idempotency_key):
            observations.append(("create", graph_sha(store.load_authority(OP, expected_sha256=self.ref))))
            return FakeStripe.create_session(client, payload, idempotency_key=idempotency_key)

        def checked_get(sid):
            observations.append(("get", graph_sha(store.load_authority(OP, expected_sha256=self.ref))))
            return FakeStripe.get_session(client, sid)

        client.create_session = checked_create
        client.get_session = checked_get
        receipt = self.stored_create(store)
        self.assertIsInstance(receipt, CheckoutReceipt)
        self.assertEqual(1, len(client.created))
        store.bind_session(OP, self.session())
        clicked = []
        result = self.stored_pay(store=store, clicked=clicked)
        self.assertTrue(result.callback_executed)
        self.assertEqual(1, len(clicked))
        self.assertEqual(1, len(client.queries))
        self.assertEqual([("create", graph_sha(self.ctx)), ("get", graph_sha(self.ctx))], observations)

    def test_cancel_C01_never_calls_browser_or_create_again(self):
        self.ref = self.recorded()
        self.stored_create()
        self.store.bind_session(OP, self.session())
        cancelled = dict(self.session(), status="expired", payment_status="unpaid")
        self.assertEqual("CANCELLED", self.store.observe(OP, cancelled, None, None))
        clicked = []
        before = (len(self.client.created), len(self.client.queries))
        with self.assertRaises(StripeCheckoutError):
            self.stored_pay(self.reopened(), clicked=clicked)
        with self.assertRaises(StripeCheckoutError):
            self.stored_create(self.reopened())
        self.assertEqual([], clicked)
        self.assertEqual(before, (len(self.client.created), len(self.client.queries)))

    def test_R01_paid_unknown_recovers_read_only_after_confirmation_expiry(self):
        self.ref = self.recorded()
        self.stored_create()
        self.store.bind_session(OP, self.session())
        self.store.mark_unknown(OP)
        self.assertEqual(self.ctx, self.reopened().load_authority(OP, expected_sha256=self.ref))
        session = dict(self.session(), status="complete", payment_status="paid",
                       payment_intent="pi_test_h74")
        intent = dict(id="pi_test_h74", livemode=False, status="succeeded",
                      latest_charge="ch_test_h74", amount=100, currency="usd")
        charge = dict(id="ch_test_h74", livemode=False, status="succeeded",
                      paid=True, captured=True, amount=100, currency="usd",
                      payment_intent="pi_test_h74")
        self.store.observe(OP, session, intent, charge)
        payment = replace(self.ctx.execution, status=PaymentStatus.UNKNOWN,
                          provider_ref=self.client.session["id"])
        observation = PaymentStatusObservation(
            payment.payment_id, payment.order_id, PaymentStatus.SUCCEEDED,
            NOW+timedelta(hours=3), "stripe_api", provider_ref=payment.provider_ref)
        outcome = self.reopened().recover_original(OP, payment, observation)
        self.assertFalse(outcome.retry_allowed)
        self.assertEqual("RECOVERED", outcome.recovery_status.value)
        self.assertEqual(1, len(self.client.created))
        self.assertEqual(0, len(self.client.queries))
        with self.assertRaises(StripeCheckoutError):
            self.stored_pay(self.reopened(), now=NOW+timedelta(hours=3))
        self.assertEqual(0, len(self.client.queries))

    def test_D01_delivery_receipt_replay_is_not_second_payment(self):
        self.ref = self.recorded()
        self.stored_create()
        self.store.bind_session(OP, self.session())
        session = dict(self.session(), status="complete", payment_status="paid",
                       payment_intent="pi_test_h74")
        intent = dict(id="pi_test_h74", livemode=False, status="succeeded",
                      latest_charge="ch_test_h74", amount=100, currency="usd")
        charge = dict(id="ch_test_h74", livemode=False, status="succeeded",
                      paid=True, captured=True, amount=100, currency="usd",
                      payment_intent="pi_test_h74")
        self.store.observe(OP, session, intent, charge)
        self.assertIsNone(self.store.record_client_delivery(OP, RESOURCE, inject_failure=True))
        old = self.reopened()
        self.assertEqual(self.ctx, old.load_authority(OP, expected_sha256=self.ref))
        receipt = old.record_client_delivery(OP, RESOURCE)
        self.assertEqual(receipt, old.record_client_delivery(OP, RESOURCE))
        self.assertEqual(["FAILED", "SUCCEEDED"], [
            x["state"] for x in old.delivery_history(OP)])
        self.assertEqual(1, len(self.client.created))
        self.assertEqual(0, len(self.client.queries))


class AuthorityDenialCases(_Fixture):
    def test_missing_wrong_reference_and_cross_operation_are_pre_effect_denials(self):
        calls = []
        with self.assertRaises(StripeCheckoutError):
            self.adapter.create_stored_session(self.store, operation_id=OP,
                expected_authority_sha256="a"*64, success_url=SUCCESS,
                cancel_url=CANCEL, now=NOW)
        self.ref = self.recorded()
        for op, digest in ((OP, "a"*64), ("nonexistent", self.ref)):
            with self.subTest(op=op):
                with self.assertRaises(StripeCheckoutError):
                    self.adapter.create_stored_session(self.store, operation_id=op,
                        expected_authority_sha256=digest, success_url=SUCCESS,
                        cancel_url=CANCEL, now=NOW)
        self.assertEqual([], self.client.created)
        self.assertEqual([], calls)

    def test_payload_tamper_is_denied_for_both_stored_entries(self):
        self.ref = self.recorded()
        with closing(sqlite3.connect(self.db)) as con:
            con.execute("UPDATE authority_contexts SET payload_json=? WHERE operation_id=?",
                        ('{"schema":"tampered"}', OP))
            con.commit()
        with self.assertRaises(StripeCheckoutError):
            self.stored_create()
        self.assertEqual([], self.client.created)
        self.store.bind_session(OP, self.session())
        with self.assertRaises(StripeCheckoutError):
            self.stored_pay(clicked=[])
        self.assertEqual([], self.client.queries)

    def test_original_confirmation_reused_after_order_change_denied(self):
        for changed in (
            replace(self.ctx.order, order_version="v2"),
            replace(self.ctx.order, total_amount=Decimal("2.00")),
            replace(self.ctx.order, payee="other-payee"),
            replace(self.ctx.order, items=(replace(self.ctx.order.items[0], unit_amount=Decimal("2.00")),)),
        ):
            with self.subTest(changed=changed):
                with self.assertRaises(StripeCheckoutError):
                    self.recorded(replace(self.ctx, order=changed))
        with closing(sqlite3.connect(self.db)) as con:
            self.assertEqual(0, con.execute("SELECT count(*) FROM authority_contexts").fetchone()[0])
        self.assertEqual([], self.client.created)

    def test_resource_mismatch_and_operation_cross_reference_denied(self):
        with self.assertRaises(StripeCheckoutError):
            self.store.record_authority(OP, self.ctx,
                resource_sha256="f"*64, recorded_at=NOW)
        altered = replace(self.ctx, execution=replace(self.ctx.execution, order_id="wrong"))
        with self.assertRaises(StripeCheckoutError):
            self.recorded(altered)
        self.assertEqual([], self.client.created)

    def test_future_expired_revoked_confirmations_and_no_clock_refresh(self):
        for changed in (
            replace(self.ctx.confirmation_record, confirmed_at=NOW+timedelta(minutes=1)),
            replace(self.ctx.confirmation_record, expires_at=NOW-timedelta(seconds=1)),
            replace(self.ctx.confirmation_record,
                    status=self.ctx.confirmation_record.status.__class__.REVOKED),
        ):
            with self.subTest(changed=changed):
                with self.assertRaises(StripeCheckoutError):
                    self.recorded(replace(self.ctx, confirmation_record=changed))
        self.ref = self.recorded()
        # Moving the action clock forward can never make original confirmation valid.
        with self.assertRaises(StripeCheckoutError):
            self.recorded(replace(self.ctx, confirmation_record=replace(
                self.ctx.confirmation_record, confirmed_at=NOW+timedelta(seconds=1))))
        denied = self.stored_create(now=NOW+timedelta(hours=2))
        self.assertFalse(denied.callback_executed)
        self.assertEqual([], self.client.created)
        self.assertEqual(self.ctx, self.reopened().load_authority(OP, expected_sha256=self.ref))

    def test_original_expired_at_pay_gate_prevents_provider_get(self):
        self.ref = self.recorded()
        self.stored_create()
        self.store.bind_session(OP, self.session())
        clicked = []
        denied = self.stored_pay(now=NOW+timedelta(hours=2), clicked=clicked)
        self.assertFalse(denied.callback_executed)
        self.assertEqual([], clicked)
        self.assertEqual([], self.client.queries)


class H74RRegressionCases(_Fixture):
    """New tests only; all frozen H74 test method bodies remain unchanged."""

    def test_retry_same_context_new_valid_record_time_preserves_first_snapshot(self):
        with closing(sqlite3.connect(self.db)) as con:
            self.assertEqual(0, con.execute("SELECT count(*) FROM authority_contexts").fetchone()[0])
        first = self.recorded()
        with closing(sqlite3.connect(self.db)) as con:
            initial = con.execute(
                "SELECT snapshot_sha256,payload_json FROM authority_contexts WHERE operation_id=?",
                (OP,),
            ).fetchone()
        self.assertEqual(first, self.store.record_authority(
            OP, self.ctx, resource_sha256=SHA,
            recorded_at=NOW + timedelta(seconds=1),
        ))
        with closing(sqlite3.connect(self.db)) as con:
            after = con.execute(
                "SELECT snapshot_sha256,payload_json FROM authority_contexts WHERE operation_id=?",
                (OP,),
            ).fetchone()
        self.assertEqual(initial, after)
        self.assertEqual(NOW.isoformat(), json.loads(after[1])["recorded_at"]["value"])
        loaded = self.reopened().load_authority(OP, expected_sha256=first)
        self.assertEqual(loaded.confirmation_record, self.ctx.confirmation_record)
        self.assertEqual(loaded.order.order_version, self.ctx.order.order_version)

    def test_retry_after_original_expiry_does_not_resurrect_authority(self):
        first = self.recorded()
        with self.assertRaises(StripeCheckoutError):
            self.store.record_authority(
                OP, self.ctx, resource_sha256=SHA,
                recorded_at=NOW + timedelta(hours=2),
            )
        with closing(sqlite3.connect(self.db)) as con:
            self.assertEqual(1, con.execute(
                "SELECT count(*) FROM authority_contexts").fetchone()[0])
        self.assertEqual(self.ctx, self.reopened().load_authority(
            OP, expected_sha256=first))
        denied = self.adapter.create_stored_session(
            self.store, operation_id=OP, expected_authority_sha256=first,
            success_url=SUCCESS, cancel_url=CANCEL, now=NOW+timedelta(hours=2))
        self.assertFalse(denied.callback_executed)
        self.assertEqual([], self.client.created)

    def test_foreign_same_name_enums_rejected_before_any_persistence(self):
        from enum import Enum
        from agentic_payment_experiment.stripe_authority_context import serialize_authority
        from agentic_payment_experiment.models import Decision, PaymentStatus
        foreign_status = Enum("PaymentStatus", {"PENDING": PaymentStatus.PENDING.value})
        foreign_decision = Enum("Decision", {"ALLOW": Decision.ALLOW.value})
        variants = (
            replace(self.ctx, execution=replace(
                self.ctx.execution, status=foreign_status.PENDING)),
            replace(self.ctx, prepayment_decision=foreign_decision.ALLOW),
        )
        for context in variants:
            with self.subTest(name=type(context.prepayment_decision).__name__):
                with self.assertRaises(StripeCheckoutError):
                    serialize_authority(OP, context, resource_sha256=SHA,
                        recorded_at=NOW, run_id=RUN)
                with self.assertRaises(StripeCheckoutError):
                    self.store.record_authority(OP, context,
                        resource_sha256=SHA, recorded_at=NOW)
        with closing(sqlite3.connect(self.db)) as con:
            self.assertEqual(0, con.execute(
                "SELECT count(*) FROM authority_contexts").fetchone()[0])
        self.assertEqual([], self.client.created)
        self.assertEqual([], self.client.queries)


if __name__ == "__main__":
    unittest.main()

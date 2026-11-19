"""Frozen, offline H68R checks. No provider requests or browser operations."""
from __future__ import annotations

import gc
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
TASK = PACK.name
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(PACK))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_files(*args):
    raw = subprocess.run(["git", "ls-files", "-z", *args], cwd=ROOT,
                         capture_output=True, check=True).stdout
    return sorted(x.decode("utf-8") for x in raw.split(b"\0") if x)


def integrity():
    baseline = json.loads((PACK / "BASELINE.json").read_text(encoding="utf-8"))
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout.strip()
    assert head == baseline["head"], "HEAD changed"
    exempt = set(baseline["allowed_product"]) | set(baseline["governance"])
    tracked = set(git_files()) - exempt
    assert tracked == set(baseline["tracked_files"]), "tracked file set changed"
    parent_pack = PACK.parent / "H68_STRIPE_CHECKOUT_SANDBOX_JOURNEY_V1"
    parent_files = sorted(p.relative_to(ROOT).as_posix() for p in parent_pack.rglob("*")
                          if p.is_file() and "__pycache__" not in p.parts)
    assert parent_files == baseline["parent_files"], "H68 artifact file set changed"
    for rel, expected in baseline["protected"].items():
        assert (ROOT / rel).is_file() and sha(ROOT / rel) == expected, "protected input changed: " + rel
    for rel, expected in baseline["package_files"].items():
        assert sha(PACK / rel) == expected, "frozen package changed: " + rel
    for rel, expected in baseline["shared_tools"].items():
        assert sha(ROOT / rel) == expected, "shared workflow changed"
    prefix = PACK.relative_to(ROOT).as_posix() + "/"
    allowed = set(baseline["inherited_untracked"]) | set(baseline["allowed_product"])
    for rel in git_files("--others", "--exclude-standard"):
        if rel in allowed:
            continue
        assert rel.startswith(prefix), "new file outside repair package: " + rel
        child = rel[len(prefix):]
        assert child in set(baseline["package_files"]) | {"BASELINE.json", "REPORT.md", "RESULT.json", "RUN.py", "ATTEMPT_LEDGER.jsonl", "REVIEW.md"} or child.startswith(("evidence/", "versions/")), "unexpected task output"
    current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    assert "task_id: " + TASK in current
    assert all("authorization_" + action + ": false" in current for action in
               ("api_call", "commit", "push", "history_rewrite")), "authority expanded"
    ledger = PACK / "ATTEMPT_LEDGER.jsonl"
    if ledger.is_file():
        rows = [json.loads(x) for x in ledger.read_text(encoding="utf-8").splitlines() if x.strip()]
        assert [r["seq"] for r in rows] == list(range(1, len(rows) + 1))
        starts, ends = {}, {}
        for row in rows:
            table = starts if row["event"] == "BEGIN" else ends
            assert row["event"] in {"BEGIN", "END"} and row["attempt_id"] not in table
            table[row["attempt_id"]] = row
        assert set(ends) <= set(starts)
        limits = {"implementation": 2, "l2": 2, "l3": 1, "active_work": None}
        counts = {}
        intervals = []
        now = datetime.now(timezone.utc)
        for key, start in starts.items():
            kind = start["kind"]
            assert kind in limits, "external or unknown attempt kind"
            counts[kind] = counts.get(kind, 0) + 1
            if limits[kind] is not None:
                assert counts[kind] <= limits[kind]
            begin = datetime.fromisoformat(start["at"].replace("Z", "+00:00"))
            end = ends.get(key)
            finish = datetime.fromisoformat(end["at"].replace("Z", "+00:00")) if end else now
            assert begin.tzinfo and finish.tzinfo and finish >= begin
            if end:
                assert end["kind"] == kind and end["status"] in {"SUCCEEDED", "FAILED", "INPUT_LIMIT"}
            if kind == "active_work":
                intervals.append((begin, finish))
        intervals.sort()
        assert all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:]))
        assert sum((end - begin).total_seconds() for begin, end in intervals) <= 90 * 60
        if starts:
            assert intervals, "active work envelope missing"
            first = min(datetime.fromisoformat(r["at"].replace("Z", "+00:00")) for r in starts.values())
            assert (now - first).total_seconds() <= 4 * 3600
    print("H68R frozen inputs, scope and reported budget OK; offline only")


class SafetyChecks(unittest.TestCase):
    def setUp(self):
        from FIXTURES import valid_context, FakeStripe, NOW, SHA
        from agentic_payment_experiment.adapters.stripe_checkout import StripeCheckoutAdapter
        self.ctx, self.client = valid_context(), FakeStripe()
        self.adapter = StripeCheckoutAdapter(self.client)
        self.now, self.sha = NOW, SHA

    def action(self, phase, ctx, now):
        callbacks = []
        if phase == "create":
            value = self.adapter.create_session(ctx, run_id="run-h68", operation_id="operation-h68",
                resource_sha256=self.sha, success_url="http://127.0.0.1:8768/success",
                cancel_url="http://127.0.0.1:8768/cancel", now=now)
            count = len(self.client.created)
        else:
            value = self.adapter.authorize_browser_payment(ctx, session_id="cs_test_fixture",
                now=now, browser_payment=callbacks.append, resource_sha256=self.sha,
                run_id="run-h68", operation_id="operation-h68")
            count = len(callbacks)
        return value, count

    def test_valid_confirmation_controls(self):
        for phase in ("create", "pay"):
            with self.subTest(phase=phase):
                value, count = self.action(phase, self.ctx, self.now)
                self.assertEqual(1, count)

    def test_expired_confirmation_at_actual_action(self):
        ctx = replace(self.ctx, confirmation_record=replace(self.ctx.confirmation_record,
                      expires_at=self.now + timedelta(minutes=1)))
        for phase in ("create", "pay"):
            with self.subTest(phase=phase):
                _, count = self.action(phase, ctx, self.now + timedelta(minutes=2))
                self.assertEqual(0, count)

    def test_missing_or_future_confirmation(self):
        for record in (None, replace(self.ctx.confirmation_record,
                                    confirmed_at=self.now + timedelta(minutes=1))):
            for phase in ("create", "pay"):
                with self.subTest(phase=phase, missing=record is None):
                    self.client.created.clear()
                    _, count = self.action(phase, replace(self.ctx, confirmation_record=record), self.now)
                    self.assertEqual(0, count)

    def store(self, tmp):
        from agentic_payment_experiment.stripe_checkout_lab import StripeLabLedger
        store = StripeLabLedger(Path(tmp) / "ledger.sqlite3")
        store.register(operation_id="op", run_id="run", case_id="R01",
                       order_id=self.ctx.order.order_id, request_id=self.ctx.request.request_id,
                       payment_id=self.ctx.execution.payment_id, resource_sha256=self.sha)
        session = {"id": "cs_test_original", "livemode": False, "mode": "payment",
                   "currency": "usd", "amount_total": 100,
                   "client_reference_id": self.ctx.order.order_id,
                   "status": "open", "payment_status": "unpaid",
                   "metadata": {"h68_run_id": "run", "h68_operation_id": "op",
                                "h68_resource_sha256": self.sha}}
        store.bind_session("op", session)
        return store, session

    def recovery(self, store, ref):
        from agentic_payment_experiment.models import PaymentStatus, PaymentStatusObservation
        payment = replace(self.ctx.execution, status=PaymentStatus.UNKNOWN, provider_ref=ref)
        observed = PaymentStatusObservation(payment_id=payment.payment_id, order_id=payment.order_id,
            status=PaymentStatus.SUCCEEDED, observed_at=self.now + timedelta(minutes=1),
            source="stripe_api", provider_ref=ref)
        return store.recover_original("op", payment, observed)

    def test_recovery_rejects_different_persisted_session(self):
        from agentic_payment_experiment.adapters.stripe_checkout import StripeCheckoutError
        with tempfile.TemporaryDirectory() as tmp:
            try:
                store, _ = self.store(tmp)
                store.mark_unknown("op")
                try:
                    result = self.recovery(store, "cs_test_foreign")
                except StripeCheckoutError:
                    pass
                else:
                    self.assertEqual("BLOCKED", result.recovery_status.value)
                self.assertEqual("UNKNOWN", store.get("op")["state"])
            finally:
                gc.collect()  # harness cleanup only; explicit closure checked below

    def test_original_session_recovery_control(self):
        with tempfile.TemporaryDirectory() as tmp:
            try:
                store, _ = self.store(tmp)
                store.mark_unknown("op")
                result = self.recovery(store, "cs_test_original")
                self.assertEqual("RECOVERED", result.recovery_status.value)
                self.assertFalse(result.retry_allowed)
            finally:
                gc.collect()

    def test_recovery_rejects_execution_request_mismatch(self):
        from agentic_payment_experiment.models import PaymentStatus, PaymentStatusObservation
        from agentic_payment_experiment.adapters.stripe_checkout import StripeCheckoutError
        with tempfile.TemporaryDirectory() as tmp:
            try:
                store, _ = self.store(tmp)
                store.mark_unknown("op")
                payment = replace(self.ctx.execution, status=PaymentStatus.UNKNOWN,
                                  request_id="request-foreign", provider_ref="cs_test_original")
                observed = PaymentStatusObservation(payment_id=payment.payment_id,
                    order_id=payment.order_id, status=PaymentStatus.SUCCEEDED,
                    observed_at=self.now + timedelta(minutes=1), source="stripe_api",
                    provider_ref="cs_test_original")
                try:
                    result = store.recover_original("op", payment, observed)
                except StripeCheckoutError:
                    pass
                else:
                    self.assertEqual("BLOCKED", result.recovery_status.value)
            finally:
                gc.collect()

    def event(self, store, intent):
        secret = "whsec_synthetic_repair_fixture"
        stamp = str(int(self.now.timestamp()))
        body = json.dumps({"id": "evt_fixture_" + intent, "livemode": False,
            "type": "payment_intent.succeeded", "data": {"object": {"id": intent}}},
            separators=(",", ":")).encode()
        mac = hmac.new(secret.encode(), stamp.encode() + b"." + body, hashlib.sha256).hexdigest()
        return store.ingest_webhook(operation_id="op", body=body, signature="t="+stamp+",v1="+mac,
                                    test_secret=secret, received_at=self.now)

    def test_foreign_or_unknown_intent_event_not_accepted(self):
        from agentic_payment_experiment.adapters.stripe_checkout import StripeCheckoutError
        with tempfile.TemporaryDirectory() as tmp:
            try:
                store, _ = self.store(tmp)
                try:
                    accepted = self.event(store, "pi_foreign")
                except StripeCheckoutError:
                    accepted = False
                self.assertFalse(accepted)
                self.assertEqual("SESSION_OPEN", store.get("op")["state"])
            finally:
                gc.collect()

    def test_known_intent_event_and_replay_control(self):
        with tempfile.TemporaryDirectory() as tmp:
            try:
                store, session = self.store(tmp)
                session.update(status="complete", payment_status="paid", payment_intent="pi_original")
                intent = {"id":"pi_original", "livemode":False, "status":"succeeded",
                          "latest_charge":"ch_original", "amount":100, "currency":"usd"}
                charge = {"id":"ch_original", "livemode":False, "status":"succeeded", "paid":True,
                          "captured":True, "amount":100, "currency":"usd", "payment_intent":"pi_original"}
                store.observe("op", session, intent, charge)
                self.assertTrue(self.event(store, "pi_original"))
                self.assertFalse(self.event(store, "pi_original"))
            finally:
                gc.collect()

    def test_real_connections_closed_on_success_and_error(self):
        import agentic_payment_experiment.stripe_checkout_lab as module
        from agentic_payment_experiment.adapters.stripe_checkout import StripeCheckoutError
        native_connect = sqlite3.connect
        connections = []
        def connect(*args, **kwargs):
            con = native_connect(*args, **kwargs)
            connections.append(con)  # retain handles: no refcount/GC shortcut
            return con
        with tempfile.TemporaryDirectory() as tmp:
            try:
                with patch.object(module.sqlite3, "connect", side_effect=connect):
                    store, _ = self.store(tmp)
                    store.get("op")
                    with self.assertRaises(StripeCheckoutError):
                        store.record_client_delivery("op", b"not-paid")
                for con in connections:
                    with self.assertRaises(sqlite3.ProgrammingError):
                        con.execute("SELECT 1")
            finally:
                for con in connections:
                    con.close()  # cleanup after assertions, never used to make them pass


def regressions():
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    modules = ["tests.test_stripe_checkout_adapter", "tests.test_stripe_checkout_lab",
               "tests.test_order_validation", "tests.test_payment_recovery", "tests.test_lifecycle",
               "tests.trusted_execution.test_governed_action", "tests.trusted_execution.test_context_policy"]
    raise SystemExit(subprocess.run([sys.executable, "-m", "unittest", *modules],
                                   cwd=ROOT, env=env, timeout=180).returncode)


if __name__ == "__main__":
    if sys.argv[1:] == ["integrity"]:
        integrity()
    elif sys.argv[1:] == ["safety"]:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SafetyChecks))
        raise SystemExit(not result.wasSuccessful())
    elif sys.argv[1:] == ["regressions"]:
        regressions()
    else:
        raise SystemExit("integrity | safety | regressions")

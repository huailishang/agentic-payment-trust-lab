"""Evaluator-owned service-level integration tests. Local SQLite, synthetic grants.

The merchant's actual CheckoutService creates, updates and completes checkouts.
Only the payment port, clock and scheduling/fault hooks belong to this harness.
No implementation of the execution guard is supplied here.
"""
from __future__ import annotations
import argparse
import asyncio
from contextlib import closing
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
from unittest.mock import patch

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
PARENT = TASK.parent / "H47_UCP_COMMERCE_APPLICABILITY_V1"
NOW = 1800000000
MERCHANT = "h50-synthetic-merchant"
PAYEE = "h50-synthetic-payee"
_CONNECT = socket.socket.connect

def deny_socket(*args, **kwargs):
    caller = sys._getframe(1)
    if caller.f_code.co_name == "socketpair" and Path(caller.f_code.co_filename).resolve() == Path(socket.__file__).resolve():
        return _CONNECT(*args, **kwargs)
    raise AssertionError("H50 external network budget is zero")

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def snapshot(checkout):
    raw = checkout.model_dump(mode="json", by_alias=True, exclude_none=True) if hasattr(checkout, "model_dump") else checkout
    return {"checkout_id": raw["id"], "merchant": MERCHANT, "payee": PAYEE,
            "currency": raw["currency"], "line_items": raw["line_items"],
            "totals": raw["totals"], "fulfillment": raw.get("fulfillment")}

def payload(quantity=1):
    return {"line_items": [{"item": {"id": "rose"}, "quantity": quantity}],
        "payment": {"instruments": []}, "fulfillment": {"methods": [{"id": "method_1", "type": "shipping",
        "line_item_ids": ["rose"], "destinations": [{"id": "dest_1", "address_country": "US"}],
        "selected_destination_id": "dest_1", "groups": [{"id": "group_1", "line_item_ids": ["rose"],
        "selected_option_id": "std-ship"}]}]}}

def payment():
    return {"instruments": [{"id": "instr_1", "handler_id": "mock_payment_handler", "type": "card",
        "display": {"brand": "Visa", "last_digits": "1234"},
        "credential": {"type": "token", "token": "success_token"}}]}

def denied(result):
    assert not result["ok"] and result.get("status") in {202, 400, 403, 409}, result
    return True

def rows(path, table):
    with closing(sqlite3.connect(path, timeout=10)) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute("SELECT * FROM " + table)]

class PaymentPort:
    """Independent, durable fake PSP ledger; every charge invocation is counted."""
    def __init__(self, path):
        self.path = Path(path)
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS calls (id INTEGER PRIMARY KEY, payment_ref TEXT, snapshot_json TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS receipts (payment_ref TEXT PRIMARY KEY, snapshot_json TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS queries (id INTEGER PRIMARY KEY, payment_ref TEXT)")
            conn.commit()

    async def charge(self, payment_ref, frozen_snapshot):
        assert isinstance(payment_ref, str) and payment_ref
        encoded = canonical(frozen_snapshot)
        with closing(sqlite3.connect(self.path, timeout=10)) as conn:
            conn.execute("INSERT INTO calls(payment_ref,snapshot_json) VALUES (?,?)", (payment_ref, encoded))
            old = conn.execute("SELECT snapshot_json FROM receipts WHERE payment_ref=?", (payment_ref,)).fetchone()
            assert old is None or old[0] == encoded, "PSP reference reused for different snapshot"
            conn.execute("INSERT OR IGNORE INTO receipts VALUES (?,?)", (payment_ref, encoded))
            conn.commit()
        return {"payment_ref": payment_ref, "state": "SUCCEEDED", "source": "H50_FAKE_PSP"}

    async def query(self, payment_ref):
        with closing(sqlite3.connect(self.path, timeout=10)) as conn:
            conn.execute("INSERT INTO queries(payment_ref) VALUES (?)", (payment_ref,))
            row = conn.execute("SELECT snapshot_json FROM receipts WHERE payment_ref=?", (payment_ref,)).fetchone()
            conn.commit()
        return {"payment_ref": payment_ref, "state": "SUCCEEDED" if row else "NOT_FOUND",
                "snapshot": json.loads(row[0]) if row else None, "source": "H50_FAKE_PSP"}

    def calls(self):
        return rows(self.path, "calls")

class Env:
    def __init__(self, directory, native=False, hook=None):
        self.directory = Path(directory)
        self.native = native
        self.hook_fn = hook
        self.psp = PaymentPort(self.directory / "psp.db")
        self.native_calls = []
        self.events = []
        self.sessions = []

    async def open(self, seed=True):
        self.db = importlib.import_module("db")
        self.models = importlib.import_module("models")
        self.service_cls = importlib.import_module("services.checkout_service").CheckoutService
        self.fulfillment = importlib.import_module("services.fulfillment_service").FulfillmentService
        self.payment_cls = importlib.import_module("ucp_sdk.models.schemas.shopping.payment_create_request").PaymentCreateRequest
        self.manager = self.db.DatabaseManager()
        await self.manager.init_dbs(str(self.directory / "products.db"), str(self.directory / "transactions.db"))
        if seed:
            async with self.manager.products_session_factory() as s:
                s.add(self.db.Product(id="rose", title="Red Rose", price=1000, image_url="https://image.example/rose"))
                await s.commit()
            async with self.manager.transactions_session_factory() as s:
                s.add(self.db.Inventory(product_id="rose", quantity=5))
                await s.commit()
        self.control = None
        if not self.native:
            cls = importlib.import_module("services.execution_control").ExecutionControl
            self.control = cls(str(self.directory / "transactions.db"), self.psp,
                               now=lambda: NOW, hook=self.hook, merchant=MERCHANT, payee=PAYEE)
            await self.control.initialize()
        return self

    async def hook(self, event, checkout_id):
        self.events.append({"event": event, "checkout_id": checkout_id})
        if event == "after_claim_commit":
            attempts = rows(self.directory / "transactions.db", "h50_attempts")
            assert any(x["checkout_id"] == checkout_id and x["state"] == "IN_FLIGHT"
                       and x["payment_ref"] and x["snapshot_json"] for x in attempts), "claim must be independently committed before payment"
        if self.hook_fn:
            await self.hook_fn(event, checkout_id)

    async def service_call(self, method, *args, no_control=False, **kwargs):
        async with self.manager.products_session_factory() as p, self.manager.transactions_session_factory() as t:
            connection = await t.connection()
            self.sessions.append({"method": method, "session_id": id(t),
                "connection_id": id(connection.sync_connection.connection.dbapi_connection)})
            extra = {} if self.native else {"execution_control": None if no_control else self.control}
            service = self.service_cls(self.fulfillment(), p, t, "https://h50-merchant.example", **extra)
            # Native-only observer: a count is explicitly NOT amount/payee binding.
            if self.native:
                original = service._process_payment
                async def observed(pay):
                    self.native_calls.append({"checkout_method": method, "snapshot_binding": "NOT_AVAILABLE"})
                    return await original(pay)
                service._process_payment = observed
            elif not no_control:
                original = service._process_payment
                async def observed(pay, *, execution=None):
                    assert isinstance(execution, dict) and execution.get("payment_ref")
                    assert isinstance(execution.get("snapshot"), dict)
                    self.native_calls.append(copy.deepcopy(execution))
                    return await original(pay, execution=execution)
                service._process_payment = observed
            try:
                value = await getattr(service, method)(*args, **kwargs)
                return {"ok": True, "value": value}
            except Exception as exc:
                await t.rollback()
                return {"ok": False, "error": type(exc).__name__, "status": getattr(exc, "status_code", None),
                        "code": getattr(exc, "code", None), "message": str(exc)}

    async def create(self):
        result = await self.service_call("create_checkout", self.models.UnifiedCheckoutCreateRequest(**payload()), "create-key")
        assert result["ok"], result
        self.checkout = result["value"]
        self.cid = str(self.checkout.id).split("/")[-1]
        self.confirmed = snapshot(self.checkout)
        if self.control:
            self.ref = await self.control.issue(self.confirmed, expires_at=NOW+100)
        return self

    async def complete(self, key="pay-key", ref="default", token="success_token", no_control=False):
        body = payment()
        body["instruments"][0]["credential"]["token"] = token
        signals = {} if ref is None else {"h50_confirmation_ref": self.ref if ref == "default" else ref}
        return await self.service_call("complete_checkout", self.cid, self.payment_cls(**body), signals, key, no_control=no_control)

    async def update(self, quantity=2):
        body = payload(quantity)
        body["line_items"][0]["id"] = self.checkout.line_items[0].id
        return await self.service_call("update_checkout", self.cid, self.models.UnifiedCheckoutUpdateRequest(**body), "update-key")

    async def cancel(self):
        return await self.service_call("cancel_checkout", self.cid, "cancel-key")

    def state(self):
        path = self.directory / "transactions.db"
        return {"orders": rows(path, "orders"), "inventory": rows(path, "inventory"), "checkouts": rows(path, "checkouts"),
                "attempts": [] if self.native else rows(path, "h50_attempts"), "payment_calls": len(self.psp.calls())}

    async def close(self):
        await self.manager.close()

async def scenario(case, directory, native=False):
    env = await Env(directory, native=native).open()
    try:
        await env.create()
        if native:
            if case == "N02_CHANGED_BEFORE":
                assert (await env.update())["ok"]
            assert (await env.complete(ref=None))["ok"]
            assert len(env.native_calls) == 1 and len(env.state()["orders"]) == 1
            expected_stock = 3 if case == "N02_CHANGED_BEFORE" else 4
            assert env.state()["inventory"][0]["quantity"] == expected_stock
            return {"case": case, "native_payment_calls": 1, "stock": expected_stock, "binding_observed": False}

        if case in {"G01_NORMAL", "G07_REPLAY"}:
            first = await env.complete()
            assert first["ok"], first
            assert len(env.psp.calls()) == 1 and len(env.state()["orders"]) == 1
            assert json.loads(env.psp.calls()[0]["snapshot_json"]) == env.confirmed
            if case == "G07_REPLAY":
                assert (await env.complete())["ok"]
                denied(await env.complete(token="different-token"))
                denied(await env.complete(key="new-key"))
                await env.control.revoke(env.ref)
                assert (await env.complete())["ok"], "historical result is not new authorization"
                assert len(env.psp.calls()) == 1 and len(env.state()["orders"]) == 1
        elif case in {"G02_CHANGED", "G03_MISSING", "G04_FORGED", "G05_EXPIRED", "G06_REVOKED", "G14_NO_CONTROL"}:
            ref = "default"
            if case == "G02_CHANGED":
                assert (await env.update())["ok"]
            elif case == "G03_MISSING":
                ref = None
            elif case == "G04_FORGED":
                ref = "untrusted-reference"
            elif case == "G05_EXPIRED":
                ref = await env.control.issue(env.confirmed, expires_at=NOW-1)
            elif case == "G06_REVOKED":
                await env.control.revoke(env.ref)
            result = await env.complete(ref=ref, no_control=case == "G14_NO_CONTROL")
            denied(result)
            assert not env.psp.calls() and not env.state()["orders"]
        elif case == "G08_UPDATE_WINS":
            arrived, release = asyncio.Event(), asyncio.Event()
            async def hook(event, cid):
                if event == "before_claim":
                    arrived.set()
                    await asyncio.wait_for(release.wait(), 10)
            env.hook_fn = hook
            task = asyncio.create_task(env.complete())
            await asyncio.wait_for(arrived.wait(), 10)
            assert (await env.update())["ok"]
            release.set()
            denied(await asyncio.wait_for(task, 15))
            assert not env.psp.calls() and not env.state()["orders"]
        elif case == "G09_CLAIM_WINS":
            arrived, release = asyncio.Event(), asyncio.Event()
            async def hook(event, cid):
                if event == "after_claim_commit":
                    arrived.set()
                    await asyncio.wait_for(release.wait(), 10)
            env.hook_fn = hook
            task = asyncio.create_task(env.complete())
            await asyncio.wait_for(arrived.wait(), 10)
            denied(await env.update())
            denied(await env.cancel())
            await env.control.revoke(env.ref)
            release.set()
            assert (await asyncio.wait_for(task, 15))["ok"]
            assert len(env.psp.calls()) == 1
            assert json.loads(env.psp.calls()[0]["snapshot_json"]) == env.confirmed
        elif case == "G10_CONCURRENT":
            arrived, release = 0, asyncio.Event()
            async def hook(event, cid):
                nonlocal arrived
                if event == "before_claim":
                    arrived += 1
                    if arrived == 2:
                        release.set()
                    await asyncio.wait_for(release.wait(), 10)
            env.hook_fn = hook
            results = await asyncio.wait_for(asyncio.gather(env.complete(key="key-A"), env.complete(key="key-B")), 20)
            assert arrived == 2 and sum(x["ok"] for x in results) == 1, results
            denied(next(x for x in results if not x["ok"]))
            assert len(env.psp.calls()) == 1 and len(env.state()["orders"]) == 1
        elif case in {"G12_PRECOMMIT_FAILURE", "G13_ORDER_COMMIT_FAILURE"}:
            point = "before_claim_commit" if case.startswith("G12") else "before_order_commit"
            async def hook(event, cid):
                if event == point:
                    raise RuntimeError("frozen fault at " + point)
            env.hook_fn = hook
            assert not (await env.complete())["ok"]
            assert not env.state()["orders"]
            assert env.state()["inventory"][0]["quantity"] == 5
            if case.startswith("G12"):
                assert not env.psp.calls() and not env.state()["attempts"]
            else:
                await assert_recovery(env, expected_calls=1)
        elif case in {"G11_CRASH_AFTER_PAYMENT", "G15_CRASH_BEFORE_PAYMENT"}:
            await env.manager.close()
            result = await asyncio.to_thread(subprocess.run, [sys.executable, "-B", str(__file__), "worker",
                "--directory", str(directory), "--checkout", env.cid, "--confirmation", env.ref,
                "--crash-point", "after_payment" if case.startswith("G11") else "after_claim_commit"],
                capture_output=True, timeout=30)
            assert result.returncode == 71, (result.returncode, result.stdout.decode(errors="replace"), result.stderr.decode(errors="replace"))
            await env.manager.init_dbs(str(env.directory / "products.db"), str(env.directory / "transactions.db"))
            await assert_recovery(env, expected_calls=1 if case.startswith("G11") else 0)
        else:
            raise AssertionError("unlisted frozen case")
        return {"case": case, "state": env.state(), "events": env.events, "sessions": env.sessions,
                "native_payment_method_calls": env.native_calls,
                "psp_calls": env.psp.calls(), "psp_queries": rows(env.psp.path, "queries"), "passed": True}
    finally:
        await env.close()

async def assert_recovery(env, expected_calls):
    state = env.state()
    assert len(state["attempts"]) == 1 and not state["orders"]
    record = state["attempts"][0]
    assert record["payment_ref"] and json.loads(record["snapshot_json"]) == env.confirmed
    outcome = await env.control.recover(env.cid)
    assert outcome["decision"] in {"WAIT", "QUERY"}
    queries = rows(env.psp.path, "queries")
    assert queries and queries[-1]["payment_ref"] == record["payment_ref"]
    assert len(env.psp.calls()) == expected_calls
    denied(await env.complete())
    denied(await env.complete(key="new-after-crash"))
    assert len(env.psp.calls()) == expected_calls

async def worker(args):
    async def hook(event, cid):
        if event == args.crash_point:
            os._exit(71)
    env = await Env(args.directory, hook=hook).open(seed=False)
    env.cid, env.ref = args.checkout, args.confirmation
    await env.complete()
    raise AssertionError("crash hook did not fire")

GUARDED_CASES = ["G01_NORMAL", "G02_CHANGED", "G03_MISSING", "G04_FORGED", "G05_EXPIRED", "G06_REVOKED",
    "G07_REPLAY", "G08_UPDATE_WINS", "G09_CLAIM_WINS", "G10_CONCURRENT", "G11_CRASH_AFTER_PAYMENT",
    "G12_PRECOMMIT_FAILURE", "G13_ORDER_COMMIT_FAILURE", "G14_NO_CONTROL", "G15_CRASH_BEFORE_PAYMENT"]

def setup_imports(native):
    server = PARENT / "sources/ucp/rest/python/server" if native else TASK / "merchant"
    sys.path.insert(0, str(server))
    from absl import flags
    import config
    if not flags.FLAGS.is_parsed():
        flags.FLAGS(["h50"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["native", "guarded", "worker", "port-selftest"])
    parser.add_argument("--out")
    parser.add_argument("--directory")
    parser.add_argument("--checkout")
    parser.add_argument("--confirmation")
    parser.add_argument("--crash-point")
    parser.add_argument("--case", choices=GUARDED_CASES)
    args = parser.parse_args()
    scratch = ROOT / ".task_envs/H50/runs"
    scratch.mkdir(parents=True, exist_ok=True)
    with patch("socket.socket.connect", deny_socket), patch("socket.create_connection", deny_socket):
        if args.mode == "port-selftest":
            with tempfile.TemporaryDirectory(dir=scratch) as tmp:
                p = PaymentPort(Path(tmp) / "port.db")
                asyncio.run(p.charge("ref", {"amount": 1000}))
                asyncio.run(p.charge("ref", {"amount": 1000}))
                assert len(p.calls()) == 2, "idempotent PSP receipts must not hide double invocation"
                assert asyncio.run(p.query("ref"))["state"] == "SUCCEEDED"
                assert asyncio.run(p.query("missing"))["state"] == "NOT_FOUND"
                print(json.dumps({"payment_port_selftest": "PASS", "invocations": 2, "receipts": 1}))
            return
        setup_imports(args.mode == "native")
        if args.mode == "worker":
            asyncio.run(worker(args))
            return
        cases = ["N01_NORMAL", "N02_CHANGED_BEFORE"] if args.mode == "native" else GUARDED_CASES
        if args.case:
            assert args.mode == "guarded", "--case is a guarded L1 diagnostic only"
            cases = [args.case]
        observations = []
        for case in cases:
            with tempfile.TemporaryDirectory(prefix="h50-", dir=scratch) as tmp:
                observations.append(asyncio.run(scenario(case, tmp, native=args.mode == "native")))
        result = {"schema": "h50-observations/v1", "mode": args.mode, "cases": observations,
                  "boundary": "LOCAL_NATIVE_SERVICE_METHODS_SYNTHETIC_TRUST_FAKE_PSP_NO_HTTP"}
        if args.out:
            target = ROOT / args.out
            assert target.resolve().is_relative_to((TASK / "evidence").resolve())
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
        print(json.dumps({"mode": args.mode, "case_count": len(observations), "all_passed": True,
                          "boundary": result["boundary"]}))

if __name__ == "__main__":
    main()

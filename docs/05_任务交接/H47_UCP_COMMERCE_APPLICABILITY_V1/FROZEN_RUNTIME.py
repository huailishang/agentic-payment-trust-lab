"""Evaluator-owned upstream ASGI harness. Synthetic state; no sockets or provider.

The complete pinned merchant app, routes, SDK, signature checker, service and DB
run unmodified. Only test setup, DNS/profile transport and call counters are ours.
This is a test transport and locally generated key, not production authentication.
"""
from __future__ import annotations
import asyncio
import copy
from contextlib import ExitStack, closing
import json
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
from unittest.mock import patch

TASK = Path(__file__).resolve().parent
SERVER = TASK / "sources/ucp/rest/python/server"
sys.path.insert(0, str(SERVER))
sys.path.insert(0, str(SERVER.parent))
from absl import flags
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
import httpx
import respx
import config
import db
import ucp_signing
import webhook_signer
from server.server import app
from services.checkout_service import CheckoutService

if not flags.FLAGS.is_parsed():
    flags.FLAGS(["h47"])

PROFILE = "https://h47-agent.example/profile"
BASE = "https://h47-merchant.example"
_CONNECT = socket.socket.connect


def deny_socket(*args, **kwargs):
    # Windows asyncio makes an internal socketpair for its event-loop wakeup.
    # Permit only that stdlib callsite, never an application network request.
    caller = sys._getframe(1)
    if caller.f_code.co_name == "socketpair" and Path(caller.f_code.co_filename).resolve() == Path(socket.__file__).resolve():
        return _CONNECT(*args, **kwargs)
    raise AssertionError("H47 has no runtime network authorization")


def synthetic_dns(host, port, *args, **kwargs):
    if host != "h47-agent.example":
        raise AssertionError("unlisted DNS request")
    # Fixture only: no DNS packet or connection is sent to this address.
    return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", port))]


def create_payload():
    # JSON shape follows the pinned integration test; the data is synthetic.
    return {"line_items": [{"item": {"id": "rose"}, "quantity": 1}],
            "payment": {"instruments": []},
            "fulfillment": {"methods": [{"id": "method_1", "type": "shipping",
                "line_item_ids": ["rose"], "destinations": [{"id": "dest_1", "address_country": "US"}],
                "selected_destination_id": "dest_1", "groups": [{"id": "group_1",
                    "line_item_ids": ["rose"], "selected_option_id": "std-ship"}]}]}}


def payment_payload(token="success_token"):
    return {"payment": {"instruments": [{"id": "instr_1", "handler_id": "mock_payment_handler",
        "type": "card", "display": {"brand": "Visa", "last_digits": "1234"},
        "credential": {"type": "token", "token": token}}]}, "risk_signals": {}}


class Merchant:
    def __init__(self):
        self.stack = ExitStack()
        scratch = TASK.parents[2] / ".task_envs/H47/runs"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = self.stack.enter_context(tempfile.TemporaryDirectory(prefix="h47-", dir=scratch))
        self.product_path = Path(self.tmp) / "products.db"
        self.transaction_path = Path(self.tmp) / "transactions.db"
        self.calls = []
        self.payment_calls = 0
        self.checkout_id = None
        self.latest = None
        self.confirmed = None
        self.key = ec.generate_private_key(ec.SECP256R1())

    def __enter__(self):
        try:
            return self._open()
        except BaseException:
            self.stack.__exit__(*sys.exc_info())
            raise

    def _open(self):
        config.FLAGS.products_db_path = str(self.product_path)
        config.FLAGS.transactions_db_path = str(self.transaction_path)
        config.FLAGS.require_signatures = True
        config.FLAGS.allow_insecure_profile_urls = False
        config.FLAGS.webhook_signing_key = None
        config.FLAGS.webhook_delivery_attempts = 1
        ucp_signing.clear_key_cache()
        webhook_signer.reset()
        self.stack.enter_context(patch("socket.socket.connect", deny_socket))
        self.stack.enter_context(patch("socket.create_connection", deny_socket))
        self.stack.enter_context(patch("socket.getaddrinfo", synthetic_dns))
        self.mock = self.stack.enter_context(respx.mock(assert_all_mocked=True, assert_all_called=False))
        self.profile_route = self.mock.get(PROFILE).mock(return_value=httpx.Response(200, json={
            "ucp": {"version": config.get_server_version(), "capabilities": {}},
            "signing_keys": [ucp_signing.jwk_from_public_key(self.key.public_key(), "h47-ephemeral")]}))
        original = CheckoutService._process_payment
        async def count_payment(service, payment):
            self.payment_calls += 1
            assert payment.instruments[0].handler_id == "mock_payment_handler"
            return await original(service, payment)
        self.stack.enter_context(patch.object(CheckoutService, "_process_payment", count_payment))
        self.client = self.stack.enter_context(TestClient(app, base_url=BASE))
        async def seed():
            async with db.manager.products_session_factory() as session:
                session.add(db.Product(id="rose", title="Red Rose", price=1000, image_url="https://image.example/rose"))
                await session.commit()
            async with db.manager.transactions_session_factory() as session:
                session.add(db.Inventory(product_id="rose", quantity=5))
                await session.commit()
        asyncio.run(seed())
        return self

    def __exit__(self, *args):
        return self.stack.__exit__(*args)

    def state(self):
        with closing(sqlite3.connect(self.transaction_path)) as conn:
            def rows(table):
                return [dict(zip([x[0] for x in cursor.description], row)) for cursor in [conn.execute("SELECT * FROM " + table)] for row in cursor.fetchall()]
            return {"orders": rows("orders"), "checkouts": rows("checkouts"),
                    "inventory": rows("inventory"), "idempotency_records": rows("idempotency_records"),
                    "payment_calls": self.payment_calls}

    def request(self, operation, *, key=None, token="success_token", quantity=None):
        before = self.state()
        signed = operation != "unsigned_create"
        tamper = operation == "tampered_create"
        if operation in {"create", "unsigned_create", "tampered_create"}:
            method, path, body = "POST", "/checkout-sessions", create_payload()
        elif operation == "update":
            method, path = "PUT", f"/checkout-sessions/{self.checkout_id}"
            # Build the writable request from explicit fixture fields and real IDs.
            body = create_payload()
            body["line_items"][0]["quantity"] = quantity
            if self.latest and self.latest.get("line_items"):
                body["line_items"][0]["id"] = self.latest["line_items"][0]["id"]
        elif operation in {"complete", "complete_drop_response"}:
            method, path, body = "POST", f"/checkout-sessions/{self.checkout_id}/complete", payment_payload(token)
        elif operation == "query":
            method, path, body = "GET", f"/checkout-sessions/{self.checkout_id}", None
        else:
            raise ValueError("operation outside frozen vocabulary")
        headers = {"UCP-Agent": f'profile="{PROFILE}"', "Content-Type": "application/json",
                   "Request-Id": f"h47-request-{len(self.calls)}"}
        if method != "GET":
            headers["Idempotency-Key"] = key or f"h47-{len(self.calls)}"
        content = json.dumps(body, separators=(",", ":")).encode() if body is not None else b""
        if signed:
            headers.update(ucp_signing.sign_request(self.key, "h47-ephemeral", method, BASE + path, headers, content))
        if tamper:
            body["line_items"][0]["quantity"] = 2
            content = json.dumps(body, separators=(",", ":")).encode()
        response = self.client.request(method, path, headers=headers, content=content)
        raw = response.json()
        if response.status_code < 300 and operation in {"create", "update", "query", "complete"}:
            self.latest = copy.deepcopy(raw)
            if operation == "create":
                self.checkout_id = raw["id"].split("/")[-1]
                self.confirmed = copy.deepcopy(raw)
        record = {"operation": operation, "key": headers.get("Idempotency-Key"),
                  "request_body": body, "response_status": response.status_code,
                  "merchant_response": raw, "client_observed_response": None if operation == "complete_drop_response" else raw,
                  "response_withheld": operation == "complete_drop_response", "before": before, "after": self.state()}
        self.calls.append(record)
        # Unknown to the simulated client; the independent observer retains it.
        return None if operation == "complete_drop_response" else copy.deepcopy(raw)


def canary():
    with Merchant() as merchant:
        merchant.request("unsigned_create")
        merchant.request("tampered_create")
        merchant.request("create", key="canary-create")
        assert [r["response_status"] for r in merchant.calls] == [401, 400, 201]
        assert merchant.state()["payment_calls"] == 0
        merchant.request("complete", key="canary-complete")
        merchant.request("complete", key="canary-complete")
        assert [r["response_status"] for r in merchant.calls][-2:] == [200, 200]
        state = merchant.state()
        assert len(state["orders"]) == 1 and state["payment_calls"] == 1
        assert state["inventory"][0]["quantity"] == 4
        print(json.dumps({"statuses": [r["response_status"] for r in merchant.calls],
            "order_count": len(state["orders"]), "stock": state["inventory"][0]["quantity"],
            "payment_calls": state["payment_calls"], "profile_fetches": merchant.profile_route.call_count,
            "runtime_boundary": "FULL_PINNED_ASGI_APP_OFFLINE_TRANSPORT"}, default=str))
    with Merchant() as merchant:
        merchant.request("create", key="canary-update-create")
        merchant.request("update", quantity=2, key="canary-update")
        assert [r["response_status"] for r in merchant.calls] == [201, 200]
        assert merchant.confirmed["line_items"][0]["quantity"] == 1
        assert merchant.latest["line_items"][0]["quantity"] == 2
        print(json.dumps({"update_ready": True, "fixed_confirmation_quantity": 1,
                          "updated_checkout_quantity": 2, "order_count": len(merchant.state()["orders"])}))


if __name__ == "__main__":
    canary()

"""Task-local offline transport around the full frozen merchant ASGI app.

Only get_checkout_service is overridden. Its original request-scoped dependencies
are retained; routes, signature validation, payment and control stay unmodified.
The key is ephemeral in memory. The profile and DNS are synthetic fixtures.
"""
import copy
from contextlib import AsyncExitStack
import json
from pathlib import Path
import socket
import sys
import tempfile
from typing import Annotated
from unittest.mock import patch

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
sys.path.insert(0, str(TASK / "merchant"))
from absl import flags
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import Depends, Request
import httpx
import respx
from sqlalchemy.ext.asyncio import AsyncSession
import config
import db
import dependencies
import server
import ucp_signing
import webhook_signer
from services.checkout_service import CheckoutService
from services.execution_control import ExecutionControl
from services.fulfillment_service import FulfillmentService
from FROZEN_TESTS import MERCHANT, PAYEE, NOW, PaymentPort, payload, payment, rows, snapshot

if not flags.FLAGS.is_parsed():
    flags.FLAGS(["h51"])

BASE = "https://h51-merchant.example"
PROFILE = "https://h51-agent.example/profile"
_CONNECT = socket.socket.connect


def deny_socket(*args, **kwargs):
    # Match H47: Windows may create an internal asyncio wakeup socketpair.
    caller = sys._getframe(1)
    if caller.f_code.co_name == "socketpair" and Path(caller.f_code.co_filename).resolve() == Path(socket.__file__).resolve():
        return _CONNECT(*args, **kwargs)
    raise AssertionError("H51 external network is forbidden")


def synthetic_dns(host, port, *args, **kwargs):
    assert host == "h51-agent.example", "Unlisted DNS lookup"
    return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", port))]


class Merchant:
    def __init__(self, injected=True, hook=None, on_request=None):
        self.injected = injected
        self.hook_fn = hook
        self.on_request = on_request
        self.calls = []
        self.events = []
        self.completion_sessions = []
        self.session_refs = []  # Prevent identity reuse in the observation.
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.confirmation = None
        self.ref = None
        self.latest = None
        self.cid = None

    async def __aenter__(self):
        self.stack = AsyncExitStack()
        await self.stack.__aenter__()
        try:
            scratch = ROOT / ".task_envs/H51/runs"
            scratch.mkdir(parents=True, exist_ok=True)
            directory = self.stack.enter_context(tempfile.TemporaryDirectory(prefix="http-", dir=scratch))
            self.directory = Path(directory)
            self.transactions = self.directory / "transactions.db"
            config.FLAGS.products_db_path = str(self.directory / "products.db")
            config.FLAGS.transactions_db_path = str(self.transactions)
            config.FLAGS.require_signatures = True
            config.FLAGS.allow_insecure_profile_urls = False
            config.FLAGS.webhook_signing_key = None
            config.FLAGS.webhook_delivery_attempts = 1
            ucp_signing.clear_key_cache()
            webhook_signer.reset()
            self.stack.enter_context(patch("socket.socket.connect", deny_socket))
            self.stack.enter_context(patch("socket.create_connection", deny_socket))
            self.stack.enter_context(patch("socket.getaddrinfo", synthetic_dns))
            mock = self.stack.enter_context(respx.mock(assert_all_mocked=True, assert_all_called=False))
            self.profile = mock.get(PROFILE).mock(return_value=httpx.Response(200, json={
                "ucp": {"version": config.get_server_version(), "capabilities": {}},
                "signing_keys": [ucp_signing.jwk_from_public_key(self.key.public_key(), "h51-ephemeral")]}))
            self.app = server.app
            assert not self.app.dependency_overrides, "Do not inherit a hidden dependency override"
            await self.stack.enter_async_context(self.app.router.lifespan_context(self.app))
            async with db.manager.products_session_factory() as s:
                s.add(db.Product(id="rose", title="Red Rose", price=1000, image_url="https://image.example/rose"))
                await s.commit()
            async with db.manager.transactions_session_factory() as s:
                s.add(db.Inventory(product_id="rose", quantity=5))
                await s.commit()
            self.psp = PaymentPort(self.directory / "psp.db")
            self.control = ExecutionControl(str(self.transactions), self.psp, now=lambda: NOW,
                hook=self.hook, merchant=MERCHANT, payee=PAYEE)
            await self.control.initialize()

            async def checkout_factory(
                request: Request,
                fulfillment_service: Annotated[FulfillmentService, Depends(dependencies.get_fulfillment_service)],
                products_session: Annotated[AsyncSession, Depends(dependencies.get_products_db)],
                transactions_session: Annotated[AsyncSession, Depends(dependencies.get_transactions_db)],
            ):
                if request.url.path.endswith("/complete"):
                    connection = await transactions_session.connection()
                    raw_connection = connection.sync_connection.connection.dbapi_connection
                    self.session_refs.append((transactions_session, connection, raw_connection))
                    self.completion_sessions.append({"request_id": request.headers["request-id"],
                        "session_id": id(transactions_session), "connection_id": id(raw_connection)})
                return CheckoutService(fulfillment_service, products_session, transactions_session,
                    str(request.base_url), execution_control=self.control)

            if self.injected:
                self.app.dependency_overrides[dependencies.get_checkout_service] = checkout_factory
                self.stack.callback(self.app.dependency_overrides.clear)
            self.client = await self.stack.enter_async_context(httpx.AsyncClient(
                transport=httpx.ASGITransport(app=self.app), base_url=BASE))
            return self
        except BaseException:
            await self.stack.__aexit__(*sys.exc_info())
            raise

    async def __aexit__(self, *args):
        return await self.stack.__aexit__(*args)

    async def hook(self, event, checkout_id):
        self.events.append({"event": event, "checkout_id": checkout_id})
        if event == "after_claim_commit":
            assert any(x["checkout_id"] == checkout_id and x["state"] == "IN_FLIGHT"
                for x in rows(self.transactions, "h50_attempts"))
        if self.hook_fn:
            await self.hook_fn(event, checkout_id)

    async def request(self, method, path, body, *, key, signed=True, tamper=False):
        # Reserve a unique ID and call position before concurrent requests yield.
        index = len(self.calls)
        headers = {"UCP-Agent": f'profile="{PROFILE}"', "Content-Type": "application/json",
            "Request-Id": f"h51-request-{index}", "Idempotency-Key": key}
        wire_body = copy.deepcopy(body)
        content = json.dumps(wire_body, separators=(",", ":")).encode()
        if signed:
            headers.update(ucp_signing.sign_request(self.key, "h51-ephemeral", method, BASE + path, headers, content))
        if tamper:
            wire_body["risk_signals"]["post_signature_mutation"] = True
            content = json.dumps(wire_body, separators=(",", ":")).encode()
        call = {"method": method, "path": path, "request_body": wire_body, "headers": headers,
            "wire_body_utf8": content.decode(), "response_status": None, "response_body": None}
        if self.on_request:
            self.on_request()
        self.calls.append(call)
        response = await self.client.request(method, path, headers=headers, content=content)
        call.update(response_status=response.status_code, response_body=response.json(),
            response_headers=dict(response.headers))
        return response

    async def create(self):
        response = await self.request("POST", "/checkout-sessions", payload(), key="create")
        assert response.status_code == 201, response.text
        self.latest = response.json()
        self.cid = self.latest["id"].split("/")[-1]

    async def confirm(self):
        # Local synthetic issuer, not a network endpoint or identity assertion.
        self.confirmation = snapshot(self.latest)
        self.ref = await self.control.issue(self.confirmation, expires_at=NOW + 100)

    async def update(self):
        body = payload(2)
        body["line_items"][0]["id"] = self.latest["line_items"][0]["id"]
        return await self.request("PUT", f"/checkout-sessions/{self.cid}", body, key="update")

    async def complete(self, key="complete", ref="default", **kwargs):
        signals = {} if ref is None else {"h50_confirmation_ref": self.ref if ref == "default" else ref}
        return await self.request("POST", f"/checkout-sessions/{self.cid}/complete",
            {"payment": payment(), "risk_signals": signals}, key=key, **kwargs)

    def observation(self, case, heartbeat_delays):
        return {"case": case, "calls": self.calls, "control_injected": self.injected,
            "confirmation": self.confirmation, "psp_calls": self.psp.calls(),
            "state": {name: rows(self.transactions, name) for name in
                ("orders", "inventory", "checkouts", "h50_attempts", "idempotency_records")},
            "completion_sessions": self.completion_sessions, "events": self.events,
            "heartbeat_delays": heartbeat_delays, "offline_profile_fetches": self.profile.call_count,
            "ephemeral_public_jwk": ucp_signing.jwk_from_public_key(self.key.public_key(), "h51-ephemeral")}

"""Native signed ASGI transport and durable evidence for H57.

No dependency overrides, no network access, and no production credentials.
L1 legacy ledger is preserved separately from new append-only requests.
"""
from contextlib import AsyncExitStack
import importlib.util
import json
import os
from pathlib import Path
import socket
import uuid
from unittest.mock import patch

from RUNTIME import TASK, ROOT, bootstrap
bootstrap()
from absl import flags
from cryptography.hazmat.primitives.asymmetric import ec
import httpx
import respx
import config
import db
import ucp_signing
import webhook_signer
from guarded_app import create_app
from services.execution_control import ExecutionControl

if not flags.FLAGS.is_parsed():
    flags.FLAGS(["h57"])

BASE = "https://h57-merchant.example"
PROFILE = "https://h57-agent.example/profile"


def fixture(name):
    spec = importlib.util.spec_from_file_location(
        "h57_" + name, TASK / "references" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_rows(path, table):
    from sqlite3 import connect, Row, OperationalError
    with connect(str(path), timeout=10) as connection:
        connection.row_factory = Row
        try:
            return [dict(row) for row in connection.execute("SELECT * FROM " + table)]
        except OperationalError as exc:
            if (table in ("h50_attempts", "h53_authorizations")
                    and "no such table" in str(exc)):
                # An unconfigured app must not create either guard table.
                return []
            raise


class NativeProbe:
    """An actual native merchant app, with request-scoped DB dependencies."""

    def __init__(self, directory, *, case, run, role="executor",
                 configured=True, seed=True, trusted_context=None, hook=None):
        self.directory = Path(directory)
        self.case = case
        self.run = run
        self.role = role
        self.configured = configured
        self.seed = seed
        self.trusted_context = trusted_context
        self.fault_hook = hook
        self.calls = []
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.fixture = fixture("H51_METHOD_FIXTURES")
        self.authorization_fixture = fixture("H53R_FIXTURES")

    async def __aenter__(self):
        self.stack = AsyncExitStack()
        await self.stack.__aenter__()
        try:
            config.FLAGS.products_db_path = str(self.directory / "products.db")
            config.FLAGS.transactions_db_path = str(self.directory / "transactions.db")
            config.FLAGS.require_signatures = True
            config.FLAGS.allow_insecure_profile_urls = False
            config.FLAGS.webhook_signing_key = None
            config.FLAGS.webhook_delivery_attempts = 1
            ucp_signing.clear_key_cache()
            webhook_signer.reset()

            def synthetic_dns(host, port, *args, **kwargs):
                assert host == "h57-agent.example", "Unlisted DNS lookup"
                return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP,
                         "", ("93.184.216.34", port))]

            self.stack.enter_context(patch("socket.getaddrinfo", synthetic_dns))
            mock = self.stack.enter_context(
                respx.mock(assert_all_mocked=True, assert_all_called=False)
            )
            mock.get(PROFILE).mock(return_value=httpx.Response(200, json={
                "ucp": {"version": config.get_server_version(), "capabilities": {}},
                "signing_keys": [
                    ucp_signing.jwk_from_public_key(
                        self.key.public_key(), "h57-ephemeral"
                    )
                ],
            }))
            self.payment_port = self.fixture.PaymentPort(
                self.directory / "psp.db"
            )
            self.keys = self.authorization_fixture.keys()
            self.control = ExecutionControl(
                str(self.directory / "transactions.db"),
                self.payment_port,
                now=lambda: self.authorization_fixture.NOW,
                hook=self.hook,
                merchant=self.authorization_fixture.MERCHANT,
                payee=self.authorization_fixture.PAYEE,
                authorization_context=(
                    self.trusted_context or
                    self.authorization_fixture.context(self.keys)
                ),
            )
            self.app = create_app(self.control if self.configured else None)
            assert not self.app.dependency_overrides
            await self.stack.enter_async_context(
                self.app.router.lifespan_context(self.app)
            )
            if self.seed:
                async with db.manager.products_session_factory() as session:
                    session.add(db.Product(
                        id="rose", title="Red Rose", price=1000,
                        image_url="https://image.example/rose"
                    ))
                    await session.commit()
                async with db.manager.transactions_session_factory() as session:
                    session.add(db.Inventory(product_id="rose", quantity=5))
                    await session.commit()
            self.client = await self.stack.enter_async_context(
                httpx.AsyncClient(
                    transport=httpx.ASGITransport(
                        app=self.app, raise_app_exceptions=False
                    ),
                    base_url=BASE,
                )
            )
            return self
        except BaseException:
            import sys
            await self.stack.__aexit__(*sys.exc_info())
            raise

    async def __aexit__(self, *args):
        return await self.stack.__aexit__(*args)

    async def hook(self, event, checkout_id):
        if self.fault_hook is not None:
            await self.fault_hook(event, checkout_id)

    async def request(self, method, path, body, *, key):
        # No invisible factory overrides. Capture exactly the transmitted bytes.
        assert not self.app.dependency_overrides
        wire = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode()
        request_id = "h57-" + uuid.uuid4().hex
        headers = {
            "UCP-Agent": 'profile="' + PROFILE + '"',
            "Content-Type": "application/json",
            "Request-Id": request_id,
            "Idempotency-Key": key,
        }
        headers.update(ucp_signing.sign_request(
            self.key, "h57-ephemeral", method, BASE + path, headers, wire
        ))
        role_dir = TASK / "evidence" / self.role
        role_dir.mkdir(parents=True, exist_ok=True)
        # Previous L1 file is an immutable malformed raw artifact. This
        # separate journal is for newly reserved requests, and NEVER
        # silently represents historical request IDs or attempts.
        new_ledger = role_dir / "HTTP_ATTEMPTS_AFTER_L1.jsonl"
        reservation = {
            "request_id": request_id,
            "case": self.case,
            "run": self.run,
            "phase": method + " " + path,
            "worker_pid": os.getpid(),
        }
        with new_ledger.open("a", encoding="utf-8") as output:
            print(json.dumps(reservation, ensure_ascii=False), file=output)
            output.flush()
            os.fsync(output.fileno())
        response = await self.client.request(
            method, path, headers=headers, content=wire
        )
        try:
            result = response.json()
        except ValueError:
            result = response.text
        call = {
            "method": method,
            "path": path,
            "request_id": request_id,
            "worker_pid": os.getpid(),
            "headers": headers,
            "request_body": body,
            "wire_body_utf8": wire.decode(),
            "response_status": response.status_code,
            "response_body": result,
        }
        self.calls.append(call)
        return response

    async def create(self):
        response = await self.request(
            "POST", "/checkout-sessions", self.fixture.payload(), key="create"
        )
        assert response.status_code == 201, (
            response.status_code, response.text[:600]
        )
        self.checkout = response.json()
        self.cid = self.checkout["id"].split("/")[-1]
        return self.checkout

    async def confirm(self):
        snapshot = self.fixture.snapshot(self.checkout)
        ref = await self.control.issue(
            snapshot, expires_at=self.authorization_fixture.NOW + 100
        )
        authorization = self.authorization_fixture.envelope(
            self.checkout, ref, self.keys
        )
        return ref, authorization, snapshot

    async def complete(self, ref, authorization, *, key="complete"):
        return await self.request(
            "POST", "/checkout-sessions/" + self.cid + "/complete",
            {
                "payment": self.fixture.payment(),
                "risk_signals": {
                    "h50_confirmation_ref": ref,
                    "h53_authorization": authorization,
                },
            },
            key=key,
        )

    def database_evidence(self):
        path = self.directory / "transactions.db"
        return {
            "orders": read_rows(path, "orders"),
            "inventory": read_rows(path, "inventory"),
            "checkouts": read_rows(path, "checkouts"),
            "attempts": read_rows(path, "h50_attempts"),
            "payment_calls": len(self.payment_port.calls()),
        }

    def public_keys(self):
        return self.authorization_fixture.public(self.keys)

    def psp_queries(self):
        return read_rows(self.directory / "psp.db", "queries")

    def authorization_records(self):
        return read_rows(
            self.directory / "transactions.db", "h53_authorizations"
        )

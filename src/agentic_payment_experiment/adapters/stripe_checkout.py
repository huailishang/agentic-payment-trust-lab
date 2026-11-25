"""H68 Stripe Checkout: one bounded external seam, no direct payment confirmation.

The adapter never reads a user's default Stripe configuration. All network and
browser actions are injected, and are invoked *inside* the existing P2/P3/P4
runtime payment gate. A callback returns only a session reference, not a URL.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from ..models import (
    AgentIdentity, Decision, IntentMandate, Order, PaymentExecutionRecord,
    TransactionRequest,
)
from ..order_validation import validate_order
from ..payment_execution import observe_payment_execution_gate
from ..trusted_execution import ContextPolicyFact, RuntimeGateRecord
from ..trusted_execution.confirmation import (
    ConfirmationRecord, ConfirmationStatus, verify_confirmation_binding,
)
from ..trusted_execution.binding import BindingStatus
from ..validator import validate_request


API_VERSION = "2026-10-28.endive"
AMOUNT_MINOR = 100
CURRENCY = "usd"
RESOURCE_NAME = "H68 digital resource"


class StripeCheckoutError(RuntimeError):
    """Only static diagnostic codes, never private credentials or HTTP bodies."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class GateContext:
    mandate: IntentMandate
    order: Order
    request: TransactionRequest
    execution: PaymentExecutionRecord
    agent_identity: AgentIdentity
    context_policy_fact: ContextPolicyFact
    current_provider_ref: str
    current_executor_instance_ref: str
    # Do not treat a test-only identity provider as the Stripe merchant.
    prepayment_decision: Decision
    confirmation_record: ConfirmationRecord | None = None


@dataclass(frozen=True)
class CheckoutReceipt:
    session_id: str
    gate: RuntimeGateRecord
    # The URL is private, must not appear in a gate callback_result_ref or report.
    checkout_url: str = field(repr=False)


def _safe_local_url(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme != "http" or parts.hostname != "127.0.0.1" or parts.port != 8768:
        raise StripeCheckoutError("unsafe_return_url")
    if parts.username or parts.password or parts.fragment:
        raise StripeCheckoutError("unsafe_return_url")


def _safe_checkout_url(url: str) -> None:
    """Accept actual Stripe-hosted URLs including their provider-signed fragment.

    Checkout commonly returns a long #... token (e.g. /g/pay/). It is an
    opaque part of the original hosted URL, not authority to redirect to a
    different origin. Never remove, decode, log, or synthesize this token.
    """
    if not isinstance(url, str) or not (15 <= len(url) <= 8192):
        raise StripeCheckoutError("invalid_hosted_checkout_url")
    if any(not 33 <= ord(char) <= 126 for char in url):
        raise StripeCheckoutError("invalid_hosted_checkout_url")
    try:
        parts = urlsplit(url)
        if (parts.scheme != "https"
                or parts.netloc != "checkout.stripe.com"
                or not parts.path.startswith(("/g/pay/", "/c/pay/"))
                or parts.username or parts.password
                or (parts.fragment and (
                    len(parts.fragment) > 2048
                    or not re.fullmatch(r"[A-Za-z0-9%_=.\-&/+~]+", parts.fragment)
                ))):
            raise StripeCheckoutError("invalid_hosted_checkout_url")
    except ValueError:
        raise StripeCheckoutError("invalid_hosted_checkout_url") from None


def _validate_operation(ctx: GateContext, resource_sha256: str, now: datetime) -> Decision:
    """Validate fixed one-dollar synthetic order before even constructing the callback."""
    if (
        not isinstance(resource_sha256, str)
        or len(resource_sha256) != 64
        or any(c not in "0123456789abcdef" for c in resource_sha256)
    ):
        return Decision.INDETERMINATE
    m, o, r, p = ctx.mandate, ctx.order, ctx.request, ctx.execution
    if not all((m, o, r, p, ctx.agent_identity, ctx.context_policy_fact)):
        return Decision.INDETERMINATE
    if (
        any(x != CURRENCY for x in (m.currency, o.currency, r.currency, p.currency))
        or any(x != Decimal("1.00") for x in (r.amount, o.total_amount, p.amount))
        or r.payee != o.payee
        or r.merchant != o.merchant
        or r.order_ref != o.order_id
        or p.order_id != o.order_id
        or p.request_id != r.request_id
        or m.mandate_id != o.mandate_ref
        or len(o.items) != 1
        or o.items[0].quantity != 1
        or o.items[0].unit_amount != Decimal("1.00")
        or r.occurred_at > now
        or now > o.quote_expires_at
        or now > m.expires_at
    ):
        return Decision.DENY
    # Existing validator checks the request timestamp. The real payment action can
    # happen later: recheck the same confirmation against *now* before callbacks.
    if ctx.confirmation_record is None:
        return Decision.INDETERMINATE
    confirmation_fact = verify_confirmation_binding(
        ctx.confirmation_record, o,
        authority_id=m.mandate_id, authority_version=m.authority_version,
        checked_at=now,
    )
    if confirmation_fact.status is BindingStatus.MISSING_EVIDENCE:
        return Decision.INDETERMINATE
    if confirmation_fact.status is not BindingStatus.VALID:
        return Decision.CONFIRMATION_REQUIRED
    if ctx.confirmation_record.confirmed_at > now:
        return Decision.CONFIRMATION_REQUIRED
    request_result = validate_request(
        m, r, authorized_order=o, final_order=o,
        confirmation_record=ctx.confirmation_record,
    )
    order_result = validate_order(m, r, o, o)
    if request_result.decision is not Decision.ALLOW:
        return request_result.decision
    if order_result is not None and order_result.decision is not None:
        return order_result.decision
    return ctx.prepayment_decision


def _gate(ctx: GateContext, decision: Decision, callback: Callable[[], str]) -> RuntimeGateRecord:
    return observe_payment_execution_gate(
        decision, ctx.mandate, ctx.order, ctx.request, ctx.execution, callback,
        agent_identity=ctx.agent_identity,
        current_provider_ref=ctx.current_provider_ref,
        current_executor_instance_ref=ctx.current_executor_instance_ref,
        context_policy_fact=ctx.context_policy_fact,
    )


class StripeCheckoutAdapter:
    """Thin, fixed-value adapter. API client is injected for test isolation."""

    def __init__(self, client):
        self._client = client

    def create_session(
        self, ctx: GateContext, *, run_id: str, operation_id: str,
        resource_sha256: str, success_url: str, cancel_url: str,
        now: datetime,
    ) -> CheckoutReceipt | RuntimeGateRecord:
        _safe_local_url(success_url)
        _safe_local_url(cancel_url)
        if not run_id or not operation_id:
            raise StripeCheckoutError("missing_operation_identity")
        decision = _validate_operation(ctx, resource_sha256, now)
        session_holder: list[dict] = []

        def invoke() -> str:
            payload = {
                "mode": "payment",
                "client_reference_id": ctx.order.order_id,
                "success_url": success_url,
                "cancel_url": cancel_url,
                "line_items[0][price_data][currency]": CURRENCY,
                "line_items[0][price_data][unit_amount]": str(AMOUNT_MINOR),
                "line_items[0][price_data][product_data][name]": RESOURCE_NAME,
                "line_items[0][quantity]": "1",
                "metadata[h68_run_id]": run_id,
                "metadata[h68_operation_id]": operation_id,
                "metadata[h68_resource_sha256]": resource_sha256,
                "payment_intent_data[metadata][h68_run_id]": run_id,
                "payment_intent_data[metadata][h68_operation_id]": operation_id,
            }
            response = self._client.create_session(
                payload, idempotency_key="h68-session-" + operation_id
            )
            if (
                not isinstance(response, dict)
                or not str(response.get("id", "")).startswith("cs_test_")
                or response.get("livemode") is not False
            ):
                raise StripeCheckoutError("unexpected_session_response")
            _safe_checkout_url(str(response.get("url", "")))
            session_holder.append(response)
            return response["id"]

        gate = _gate(ctx, decision, invoke)
        if not gate.callback_executed:
            return gate
        return CheckoutReceipt(
            session_id=session_holder[0]["id"],
            gate=gate,
            checkout_url=session_holder[0]["url"],
        )

    def authorize_browser_payment(
        self, ctx: GateContext, *, session_id: str,
        now: datetime, browser_payment: Callable[[str], None],
        resource_sha256: str, run_id: str, operation_id: str,
    ) -> RuntimeGateRecord:
        """Read original session before the actual browser action, never POST confirm."""
        if not session_id.startswith("cs_test_"):
            raise StripeCheckoutError("invalid_session_id")
        if not run_id or not operation_id:
            raise StripeCheckoutError("missing_operation_identity")
        decision = _validate_operation(ctx, resource_sha256, now)

        def invoke() -> str:
            native = self._client.get_session(session_id)
            if (
                native.get("id") != session_id
                or native.get("livemode") is not False
                or native.get("mode") != "payment"
                or native.get("currency") != CURRENCY
                or type(native.get("amount_total")) is not int
                or native["amount_total"] != AMOUNT_MINOR
                or native.get("client_reference_id") != ctx.order.order_id
                or native.get("payment_status") != "unpaid"
                or native.get("status") != "open"
                or native.get("metadata", {}).get("h68_resource_sha256") != resource_sha256
                or native.get("metadata", {}).get("h68_run_id") != run_id
                or native.get("metadata", {}).get("h68_operation_id") != operation_id
            ):
                raise StripeCheckoutError("prepay_native_state_mismatch")
            url = str(native.get("url", ""))
            _safe_checkout_url(url)
            browser_payment(url)
            return session_id

        return _gate(ctx, decision, invoke)

    @staticmethod
    def _effective_stored_authority(store, operation_id, expected_authority_sha256):
        ctx = store.load_authority(operation_id, expected_sha256=expected_authority_sha256)
        shutdown = store.get_mandate_shutdown(
            operation_id, expected_sha256=expected_authority_sha256
        )
        if shutdown is not None:
            return ctx, True
        fact = store.get_confirmation_withdrawal(
            operation_id, expected_sha256=expected_authority_sha256
        )
        if fact is not None:
            ctx = replace(ctx, confirmation_record=replace(
                ctx.confirmation_record, status=ConfirmationStatus.REVOKED
            ))
        return ctx, False

    @staticmethod
    def _shutdown_gate(ctx):
        def forbidden():
            raise StripeCheckoutError("mandate_shutdown_callback_forbidden")
        return _gate(ctx, Decision.DENY, forbidden)

    @staticmethod
    def _execute_stored_action(store, ctx, admission, invoke):
        decision = Decision(admission["decision"])
        if decision is Decision.DENY and admission["reason"] == "stored_action_original_state_invalid":
            # begin has already committed the native denial; retain the legacy
            # business-state error without calling the provider or bypassing control.
            raise StripeCheckoutError(
                "stored_create_original_operation_not_new"
                if admission["action"] == "CREATE_SESSION"
                else "stored_browser_original_session_not_open"
            )
        if decision is not Decision.ALLOW:
            def forbidden():
                raise StripeCheckoutError("stored_action_callback_forbidden")
            return _gate(ctx, decision, forbidden)
        # begin_stored_action has committed before this boundary. No SQLite
        # write lock is held during the existing gate or provider callback.
        ref = admission["admission_ref"]
        if not ref:
            raise StripeCheckoutError("stored_action_admission_missing")
        try:
            result = invoke()
        except BaseException:
            # If recording UNKNOWN itself fails, the committed ADMITTED fact
            # still prevents replay. Preserve the original exception.
            try:
                store.finish_stored_action(ref, outcome="UNKNOWN")
            except Exception:
                pass
            raise
        gate = result.gate if isinstance(result, CheckoutReceipt) else result
        store.finish_stored_action(
            ref, outcome="COMPLETED" if gate.callback_executed else "NO_EFFECT",
            result_ref=gate.callback_result_ref,
            gate_record={"decision": gate.final_decision.value,
                         "callback_count": gate.callback_count,
                         "reason": list(gate.reason_codes)},
        )
        return result

    def create_stored_session(
        self, store, *, operation_id: str, expected_authority_sha256: str,
        success_url: str, cancel_url: str, now: datetime,
    ) -> CheckoutReceipt | RuntimeGateRecord:
        """Only committed admission and the existing create gate can reach a provider."""
        ctx, _ = self._effective_stored_authority(
            store, operation_id, expected_authority_sha256
        )
        admission = store.begin_stored_action(
            operation_id, expected_sha256=expected_authority_sha256, action="CREATE_SESSION"
        )

        def invoke():
            operation = store.get(operation_id)
            if operation["state"] != "CREATED" or operation["session_id"] is not None:
                raise StripeCheckoutError("stored_create_original_operation_not_new")
            return self.create_session(
                ctx, run_id=operation["run_id"],
                operation_id=operation["operation_id"],
                resource_sha256=operation["resource_sha256"],
                success_url=success_url, cancel_url=cancel_url, now=now,
            )

        return self._execute_stored_action(store, ctx, admission, invoke)

    def authorize_stored_browser_payment(
        self, store, *, operation_id: str, expected_authority_sha256: str,
        now: datetime, browser_payment: Callable[[str], None],
    ) -> RuntimeGateRecord:
        """Use committed admission, original session and the existing browser gate."""
        ctx, _ = self._effective_stored_authority(
            store, operation_id, expected_authority_sha256
        )
        admission = store.begin_stored_action(
            operation_id, expected_sha256=expected_authority_sha256, action="BROWSER_PAYMENT"
        )

        def invoke():
            operation = store.get(operation_id)
            if operation["state"] != "SESSION_OPEN" or not operation["session_id"]:
                raise StripeCheckoutError("stored_browser_original_session_not_open")
            return self.authorize_browser_payment(
                ctx, session_id=operation["session_id"], now=now,
                browser_payment=browser_payment,
                resource_sha256=operation["resource_sha256"],
                run_id=operation["run_id"], operation_id=operation["operation_id"],
            )

        return self._execute_stored_action(store, ctx, admission, invoke)


class StripeTestAPI:
    """Explicit test-only Stripe client. No SDK, implicit accounts, or redirects."""

    def __init__(self, test_key: str, *, timeout: int = 30):
        if not test_key.startswith(("sk_test_", "rk_test_", "rkcs_test_")):
            raise StripeCheckoutError("non_test_key_rejected")
        self.__key = test_key
        self.timeout = min(30, max(1, timeout))
        self._opener = build_opener(_NoRedirect())

    def _request(self, method: str, path: str, params: Mapping[str, str] | None = None,
                 idempotency_key: str | None = None) -> dict:
        if method == "POST":
            if path != "/v1/checkout/sessions" and not (
                path.startswith("/v1/checkout/sessions/") and path.endswith("/expire")
            ):
                raise StripeCheckoutError("post_path_not_allowed")
            if not idempotency_key or len(idempotency_key) > 255:
                raise StripeCheckoutError("missing_idempotency_key")
        elif method == "GET":
            permitted = (
                path == "/v1/account"
                or re.fullmatch(r"/v1/checkout/sessions(?:/[A-Za-z0-9_]+(?:/line_items)?)?", path)
                or re.fullmatch(r"/v1/payment_intents(?:/[A-Za-z0-9_]+)?", path)
                or re.fullmatch(r"/v1/charges(?:/[A-Za-z0-9_]+)?", path)
                or re.fullmatch(r"/v1/events/[A-Za-z0-9_]+", path)
            )
            if not permitted:
                raise StripeCheckoutError("get_path_not_allowed")
        else:
            raise StripeCheckoutError("method_not_allowed")
        headers = {
            "Authorization": "Bearer " + self.__key,
            "Stripe-Version": API_VERSION,
        }
        raw = urlencode(params or {}).encode() if method == "POST" else None
        if method == "POST":
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            headers["Idempotency-Key"] = idempotency_key
        request = Request("https://api.stripe.com" + path, method=method,
                          data=raw, headers=headers)
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                data = response.read(2 * 1024 * 1024 + 1)
                if response.status != 200 or len(data) > 2 * 1024 * 1024:
                    raise StripeCheckoutError("stripe_response_status_or_size")
            result = json.loads(data)
            if not isinstance(result, dict) or result.get("livemode") is True:
                raise StripeCheckoutError("stripe_response_mode_invalid")
            return result
        except (HTTPError, URLError, TimeoutError, ValueError):
            raise StripeCheckoutError("stripe_transport_failure") from None

    def create_session(self, payload: Mapping[str, str], *, idempotency_key: str) -> dict:
        return self._request("POST", "/v1/checkout/sessions", payload, idempotency_key)

    def get_session(self, session_id: str) -> dict:
        if not session_id.startswith("cs_test_") or not all(
            c.isalnum() or c == "_" for c in session_id
        ):
            raise StripeCheckoutError("invalid_session_id")
        return self._request("GET", "/v1/checkout/sessions/" + session_id)


def verify_webhook(raw: bytes, header: str, secret: str, received_at: datetime,
                   *, tolerance: int = 300) -> dict:
    """Validate exact webhook bytes and original receipt timestamp (not replay clock)."""
    if len(raw) > 1024 * 1024 or not secret.startswith("whsec_"):
        raise StripeCheckoutError("webhook_input_invalid")
    if received_at.tzinfo is None:
        raise StripeCheckoutError("webhook_receipt_time_missing")
    pairs = [part.strip().split("=", 1) for part in header.split(",")]
    ts = [v for k, v in pairs if k == "t"]
    sigs = [v for k, v in pairs if k == "v1"]
    if len(ts) != 1 or not ts[0].isdigit() or not sigs:
        raise StripeCheckoutError("webhook_signature_fields")
    signed = ts[0].encode() + b"." + raw
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, s) for s in sigs):
        raise StripeCheckoutError("webhook_signature_mismatch")
    if abs(received_at.timestamp() - int(ts[0])) > tolerance:
        raise StripeCheckoutError("webhook_timestamp_stale")
    try:
        event = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise StripeCheckoutError("webhook_json_invalid") from None
    if event.get("livemode") is not False or event.get("type") not in {
        "checkout.session.completed", "checkout.session.expired",
        "payment_intent.succeeded",
    }:
        raise StripeCheckoutError("webhook_event_not_allowed")
    return event

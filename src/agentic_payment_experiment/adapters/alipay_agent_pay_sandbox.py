"""Bounded Alipay sandbox request signing and response verification.

No network, logging, credential storage or payment lifecycle transitions here.
"""
from __future__ import annotations

import base64
import hashlib
import json
from decimal import Decimal, InvalidOperation

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

GATEWAY = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
METHOD = "alipay.aipay.agent.payment.verify"
RESPONSE = "alipay_aipay_agent_payment_verify_response"
BINDINGS = ("trade_no", "out_trade_no", "resource_id", "amount")


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def signed_response_parts(raw: bytes):
    """Return parsed payload plus the exact signed JSON substring (not reserialized)."""
    if len(raw) > 1_000_000:
        raise ValueError("response too large")
    text = raw.decode("utf-8")
    decoder = json.JSONDecoder(object_pairs_hook=_unique,
                               parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
    envelope = decoder.decode(text)
    if type(envelope) is not dict or set(envelope) - {RESPONSE, "sign", "sign_type"}:
        raise ValueError("unexpected envelope")
    if envelope.get("sign_type", "RSA2") != "RSA2":
        raise ValueError("unexpected algorithm")
    if type(envelope.get(RESPONSE)) is not dict or type(envelope.get("sign")) is not str:
        raise ValueError("missing signed response")
    # Walk top-level JSON tokens so a key embedded in a string cannot select the payload.
    cursor = text.index("{") + 1
    while True:
        while text[cursor].isspace():
            cursor += 1
        key, cursor = decoder.raw_decode(text, cursor)
        while text[cursor].isspace():
            cursor += 1
        if text[cursor] != ":":
            raise ValueError("invalid JSON")
        cursor += 1
        while text[cursor].isspace():
            cursor += 1
        start = cursor
        _, cursor = decoder.raw_decode(text, cursor)
        if key == RESPONSE:
            return envelope[RESPONSE], text[start:cursor].encode("utf-8"), base64.b64decode(envelope["sign"], validate=True)
        while text[cursor].isspace():
            cursor += 1
        if text[cursor] != ",":
            raise ValueError("missing response")
        cursor += 1


def sign_request(*, app_id, private_key, trade_no, payment_proof, timestamp,
                 client_session=None, gateway=GATEWAY):
    if gateway != GATEWAY:
        raise ValueError("sandbox gateway required")
    if not isinstance(private_key, rsa.RSAPrivateKey) or private_key.key_size < 2048:
        raise ValueError("RSA 2048 or stronger required")
    for value, limit in ((app_id, 32), (trade_no, 32), (payment_proof, 64), (timestamp, 19)):
        if type(value) is not str or not value.strip() or len(value) > limit:
            raise ValueError("invalid request input")
    biz = {"trade_no": trade_no, "payment_proof": payment_proof}
    if client_session is not None:
        if type(client_session) is not str or not client_session or len(client_session) > 1024:
            raise ValueError("invalid session")
        biz["client_session"] = client_session
    params = dict(app_id=app_id, method=METHOD, format="JSON", charset="utf-8",
                  sign_type="RSA2", timestamp=timestamp, version="1.0",
                  biz_content=json.dumps(biz, ensure_ascii=False, separators=(",", ":")))
    canonical = "&".join(k + "=" + params[k] for k in sorted(params)).encode("utf-8")
    params["sign"] = base64.b64encode(private_key.sign(canonical, padding.PKCS1v15(), hashes.SHA256())).decode("ascii")
    return params


def _amount(value):
    if type(value) is not str or not value or len(value) > 32:
        raise ValueError("invalid amount")
    amount = Decimal(value)
    if not amount.is_finite() or amount <= 0:
        raise ValueError("invalid amount")
    return amount


def verify_response(raw: bytes, public_key, *, expected: dict):
    trade = expected.get("trade_no")
    fact = dict(status="MISSING_EVIDENCE", provider="ALIPAY_AGENT_PAY_SANDBOX", method=METHOD,
                trade_no_sha256=hashlib.sha256(trade.encode()).hexdigest() if type(trade) is str else None,
                active=None, binding_checks_requested=list(BINDINGS), binding_checks_passed=[],
                provider_response_signature_verified=False, reason_codes=["MISSING_EXPECTATION"])
    if any(type(expected.get(k)) is not str or not expected[k].strip() for k in BINDINGS):
        return fact
    try:
        _amount(expected["amount"])
    except (ValueError, InvalidOperation):
        return fact
    try:
        if not isinstance(public_key, rsa.RSAPublicKey) or public_key.key_size < 2048:
            raise ValueError("invalid public key")
        payload, signed, signature = signed_response_parts(raw)
        public_key.verify(signature, signed, padding.PKCS1v15(), hashes.SHA256())
    except Exception:
        fact.update(status="INVALID", reason_codes=["SIGNATURE_INVALID"])
        return fact
    fact["provider_response_signature_verified"] = True
    if payload.get("code") != "10000":
        # Unknown provider errors never masquerade as proof-specific rejection.
        fact.update(status="PROVIDER_ERROR", reason_codes=["PROVIDER_ERROR"])
        return fact
    if type(payload.get("active")) is not bool:
        fact["reason_codes"] = ["MISSING_ACTIVE"]
        return fact
    fact["active"] = payload["active"]
    missing = False
    mismatch = False
    for field in BINDINGS:
        value = payload.get(field)
        if type(value) is not str or not value.strip():
            missing = True
            continue
        try:
            equal = _amount(value) == _amount(expected[field]) if field == "amount" else value == expected[field]
        except (ValueError, InvalidOperation):
            missing = True
            continue
        if equal:
            fact["binding_checks_passed"].append(field)
        else:
            mismatch = True
    if missing:
        fact.update(status="MISSING_EVIDENCE", reason_codes=["MISSING_BINDING"])
    elif mismatch:
        fact.update(status="INVALID", reason_codes=["BINDING_MISMATCH"])
    elif not fact["active"]:
        fact.update(status="INVALID", reason_codes=["PROVIDER_INACTIVE"])
    else:
        fact.update(status="VALID", reason_codes=["VERIFIED"])
    return fact

"""Strict, offline, single-platform CheckoutMandate consumer (H54)."""
import base64
import copy
import hashlib
import json
import re

import rfc8785
from ap2.sdk.mandate import MandateClient
from ap2.sdk.sdjwt.sd_jwt import verify as verify_root
from jwcrypto.jwk import JWK
from jwcrypto.jws import JWS
from pydantic import BaseModel, ConfigDict


class Claims(BaseModel):
    model_config = ConfigDict(extra="allow")


class Reject(Exception):
    def __init__(self, code):
        self.code = code


def fail(code):
    raise Reject(code)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def b64decode(part):
    if not isinstance(part, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", part):
        fail("invalid_input")
    try:
        return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))
    except Exception:
        fail("invalid_input")


def unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            fail("invalid_input")
        obj[key] = value
    return obj


def forbidden_constant(value):
    fail("invalid_input")


def validate(value):
    if isinstance(value, str):
        if any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
            fail("invalid_input")
    elif isinstance(value, dict):
        for key, item in value.items():
            validate(key)
            validate(item)
    elif isinstance(value, list):
        for item in value:
            validate(item)
    elif isinstance(value, int) and not isinstance(value, bool):
        if abs(value) > 9007199254740991:
            fail("invalid_input")
    elif isinstance(value, float) and (value != value or abs(value) == float('inf')):
        fail("invalid_input")
    return value


def parse(raw):
    try:
        return validate(json.loads(raw, object_pairs_hook=unique_pairs,
                                   parse_constant=forbidden_constant))
    except Reject:
        raise
    except (ValueError, TypeError, UnicodeError, OverflowError):
        fail("invalid_input")


def jws_parts(compact):
    if not isinstance(compact, str):
        fail("invalid_input")
    parts = compact.split(".")
    if len(parts) != 3 or not all(parts):
        fail("invalid_input")
    header = parse(b64decode(parts[0]))
    payload_raw = b64decode(parts[1])
    payload = parse(payload_raw)
    if not isinstance(header, dict) or not isinstance(payload, dict):
        fail("invalid_input")
    if header.get("alg") != "ES256" or not isinstance(header.get("kid"), str):
        fail("unsupported_profile")
    if any(x in header for x in ("jwk", "jku", "x5u", "x5c", "crit")):
        fail("unsupported_profile")
    b64decode(parts[2])
    return parts, header, payload_raw, payload


def resolve(profile, kid):
    if not isinstance(profile, dict) or not isinstance(profile.get("keys"), list):
        fail("agent_missing_key")
    matches = [k for k in profile["keys"] if isinstance(k, dict) and k.get("kid") == kid]
    if len(matches) != 1:
        fail("agent_missing_key")
    key = matches[0]
    if key.get("kty") != "EC" or key.get("crv") != "P-256" or "d" in key:
        fail("unsupported_profile")
    try:
        return JWK(**key)
    except Exception:
        fail("agent_missing_key")


def consume(request_json: bytes, session_json: bytes, trust: dict, now: int) -> dict:
    try:
        if not isinstance(request_json, bytes) or not isinstance(session_json, bytes):
            fail("invalid_input")
        if not isinstance(now, int) or isinstance(now, bool):
            fail("invalid_input")
        request, session = parse(request_json), parse(session_json)
        if not isinstance(request, dict) or not isinstance(session, dict) or not isinstance(trust, dict):
            fail("invalid_input")
        if not trust or "platform_profile" not in trust or "merchant_profile" not in trust:
            fail("agent_missing_key")
        if trust.get("ap2_required") is not True or trust.get("protocol_version") != "2026-08-25":
            fail("unsupported_profile")
        ap2 = request.get("ap2")
        if not isinstance(ap2, dict) or not ap2.get("checkout_mandate"):
            fail("mandate_required")
        token = ap2["checkout_mandate"]
        if not isinstance(token, str):
            fail("invalid_input")
        sections = token.split("~")
        if len(sections) < 2 or sections[-1] != "" or not sections[0]:
            fail("unsupported_profile")
        # SD-JWT disclosures are JSON arrays; no key-binding JWT or extra hop.
        for disclosure in sections[1:-1]:
            item = parse(b64decode(disclosure))
            if not isinstance(item, list) or len(item) not in (2, 3):
                fail("unsupported_profile")
        jwt = sections[0]
        tparts, thead, _, _ = jws_parts(jwt)
        platform_key = resolve(trust["platform_profile"], thead["kid"])
        # The official AP2 SDK is the sole authority for platform issuance and time.
        try:
            claims = MandateClient().verify(token, platform_key, payload_type=Claims,
                current_time=now, clock_skew_seconds=0).mandate_payload.model_dump()
        except Exception as exc:
            msg = str(exc).lower()
            fail("mandate_expired" if any(s in msg for s in ("expired", "not yet", "iat", "future")) else "mandate_invalid_signature")
        if not isinstance(claims, dict) or claims.get("vct") != "mandate.checkout.1":
            fail("mandate_scope_mismatch")
        if not all(isinstance(claims.get(k), int) and not isinstance(claims[k], bool) for k in ("iat", "exp")):
            fail("mandate_scope_mismatch")
        if claims["iat"] > now or claims["exp"] <= now or claims["exp"] <= claims["iat"]:
            fail("mandate_expired")
        # Verify the *complete* signed SD-JWT root; the extracted checkout
        # claims may omit root-level delegation constraints (including disclosures).
        try:
            verified_root = verify_root(token, platform_key)
        except Exception:
            fail("mandate_invalid_signature")
        if not isinstance(verified_root, dict) or "cnf" in verified_root or "cnf" in claims:
            fail("unsupported_profile")
        compact = claims.get("checkout_jwt")
        expected_hash = claims.get("checkout_hash")
        if not isinstance(compact, str) or not isinstance(expected_hash, str):
            fail("mandate_scope_mismatch")
        actual_hash = base64.urlsafe_b64encode(hashlib.sha256(compact.encode("ascii")).digest()).decode().rstrip("=")
        if expected_hash != actual_hash:
            fail("mandate_scope_mismatch")
        parts, mhead, payload_raw, payload = jws_parts(compact)
        merchant_key = resolve(trust["merchant_profile"], mhead["kid"])
        try:
            signed = JWS()
            signed.deserialize(compact)
            signed.verify(merchant_key)
        except Exception:
            fail("merchant_authorization_invalid")
        try:
            if payload_raw != rfc8785.dumps(payload):
                fail("merchant_authorization_invalid")
        except (ValueError, TypeError, OverflowError):
            fail("invalid_input")
        session_ap2 = session.get("ap2")
        if not isinstance(session_ap2, dict) or "merchant_authorization" not in session_ap2:
            fail("merchant_authorization_missing")
        if set(session_ap2) != {"merchant_authorization"}:
            fail("unsupported_profile")
        if session_ap2["merchant_authorization"] != parts[0] + ".." + parts[2]:
            fail("merchant_authorization_invalid")
        checkout = {k:v for k,v in session.items() if k != "ap2"}
        try:
            if rfc8785.dumps(checkout) != payload_raw:
                fail("mandate_scope_mismatch")
        except (ValueError, TypeError, OverflowError):
            fail("invalid_input")
        return {"status":"VERIFIED", "checkout":copy.deepcopy(session),
            "checkout_jwt":compact, "checkout_hash":expected_hash,
            "mandate_sha256":digest(token.encode()), "request_sha256":digest(request_json),
            "session_sha256":digest(session_json), "platform_kid":thead["kid"],
            "merchant_kid":mhead["kid"], "protocol_version":trust["protocol_version"]}
    except Reject as exc:
        return {"status":"DENY", "code":exc.code}
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError):
        return {"status":"DENY", "code":"invalid_input"}

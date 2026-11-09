"""Frozen offline counterexamples for the H43 signed gateway-error boundary.

Uses ephemeral synthetic RSA keys only. Never reads a sandbox credential or network.
"""
import base64
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from agentic_payment_experiment.adapters.alipay_agent_pay_sandbox import (
    RESPONSE, signed_response_parts, verify_response,
)

EXPECTED = dict(trade_no="synthetic-trade", out_trade_no="synthetic-order",
                resource_id="synthetic-resource", amount="0.01")


def envelope(private, body, node="error_response", *, signed=True):
    signature = base64.b64encode(private.sign(body.encode(), padding.PKCS1v15(), hashes.SHA256())).decode()
    suffix = ',"sign":' + json.dumps(signature) if signed else ""
    return ('{"' + node + '":' + body + suffix + "}").encode()


def fact(raw, public):
    return verify_response(raw, public, expected=EXPECTED)


def main():
    mode = sys.argv[1] if len(sys.argv) == 2 else ""
    if mode not in {"before", "after"}:
        raise SystemExit("usage: EVALUATOR_CHECK.py before|after")
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    body = '{"code":"40002","msg":"synthetic-sensitive-marker"}'
    raw = envelope(private, body)
    result = fact(raw, private.public_key())
    if mode == "before":
        assert result["status"] == "INVALID" and not result["provider_response_signature_verified"]
        print("BASELINE: signed generic gateway error rejected; 0/1 recognized")
        return 0

    assert result["status"] == "PROVIDER_ERROR"
    assert result["provider_response_signature_verified"] is True
    assert result["reason_codes"] == ["SIGNED_GATEWAY_ERROR"]
    assert result["active"] is None and result["binding_checks_passed"] == []
    assert "synthetic-sensitive-marker" not in json.dumps(result)
    print("C01 signed generic gateway error is trusted only as an error")

    for label, bad in (
        ("wrong-key", fact(raw, other.public_key())),
        ("tamper", fact(raw.replace(b"40002", b"10000"), private.public_key())),
        ("unsigned", fact(envelope(private, body, signed=False), private.public_key())),
        ("duplicate", fact(envelope(private, '{"code":"40002","code":"10000"}'), private.public_key())),
        ("double-envelope", fact(raw.replace(b',"sign":', b',"' + RESPONSE.encode() + b'":{},"sign":'), private.public_key())),
    ):
        assert bad["status"] == "INVALID" and bad["provider_response_signature_verified"] is False, label
        assert bad["active"] is None and bad["binding_checks_passed"] == [], label
        print("C02 " + label + " fails closed")

    method_raw = envelope(private, '{"code":"40004","msg":"synthetic"}', node=RESPONSE)
    method_result = fact(method_raw, private.public_key())
    assert method_result["status"] == "PROVIDER_ERROR" and method_result["provider_response_signature_verified"]
    assert method_result["reason_codes"] == ["PROVIDER_ERROR"]
    print("C03 method-specific signed business error unchanged")

    anomalous = fact(envelope(private, '{"code":"10000","msg":"synthetic"}'), private.public_key())
    assert anomalous["status"] != "VALID" and anomalous["binding_checks_passed"] == []
    print("C04 generic success code never becomes valid payment")

    try:
        signed_response_parts(raw)
    except ValueError:
        print("C05 H41 method-specific parser remains narrow")
    else:
        raise AssertionError("H41 parser was broadened")
    print("AFTER: signed generic gateway error 1/1; all negative controls passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

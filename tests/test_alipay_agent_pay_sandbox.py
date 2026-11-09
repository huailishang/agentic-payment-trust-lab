import base64
import json
import unittest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from agentic_payment_experiment.adapters.alipay_agent_pay_sandbox import (
    RESPONSE, GATEWAY_ERROR, sign_request, signed_response_parts, verify_response,
)


class AlipayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.wrong = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.expected = dict(trade_no="test-trade", out_trade_no="test-order", resource_id="test-resource", amount="0.01")
        self.payload = dict(self.expected, code="10000", active=True)

    def envelope(self, payload=None):
        body = json.dumps(self.payload if payload is None else payload, ensure_ascii=False, indent=2)
        signature = base64.b64encode(self.key.sign(body.encode(), padding.PKCS1v15(), hashes.SHA256())).decode()
        return ('{"sign":' + json.dumps(signature) + ',"' + RESPONSE + '":' + body + '}').encode()

    def verify(self, raw=None, key=None):
        return verify_response(self.envelope() if raw is None else raw, key or self.key.public_key(), expected=self.expected)

    def gateway_error(self, body='{"code":"40002","msg":"synthetic-sensitive-content"}', *, signed=True):
        signature = base64.b64encode(self.key.sign(body.encode(), padding.PKCS1v15(), hashes.SHA256())).decode()
        suffix = ',"sign":' + json.dumps(signature) if signed else ""
        return ('{"' + GATEWAY_ERROR + '":' + body + suffix + '}').encode()

    def test_signed_gateway_error_only_proves_provider_error(self):
        raw = self.gateway_error()
        fact = self.verify(raw)
        self.assertEqual(fact["status"], "PROVIDER_ERROR")
        self.assertEqual(fact["reason_codes"], ["SIGNED_GATEWAY_ERROR"])
        self.assertTrue(fact["provider_response_signature_verified"])
        self.assertIsNone(fact["active"])
        self.assertEqual(fact["binding_checks_passed"], [])
        self.assertNotIn("synthetic-sensitive-content", json.dumps(fact))
        with self.assertRaises(ValueError):
            signed_response_parts(raw)

    def test_gateway_error_bad_envelopes_fail_closed(self):
        raw = self.gateway_error()
        for bad, key in (
            (raw, self.wrong.public_key()),
            (raw.replace(b"40002", b"40003"), self.key.public_key()),
            (self.gateway_error(signed=False), self.key.public_key()),
            (self.gateway_error('{"code":"40002","code":"40003"}'), self.key.public_key()),
            (raw.replace(b',"sign":', b',"' + RESPONSE.encode() + b'":{},"sign":'), self.key.public_key()),
        ):
            with self.subTest(raw=bad[:60]):
                fact = self.verify(bad, key)
                self.assertEqual(fact["status"], "INVALID")
                self.assertFalse(fact["provider_response_signature_verified"])
                self.assertEqual(fact["binding_checks_passed"], [])

    def test_gateway_success_code_is_not_payment_proof(self):
        fact = self.verify(self.gateway_error('{"code":"10000"}'))
        self.assertEqual(fact["status"], "INVALID")
        self.assertEqual(fact["reason_codes"], ["INVALID_GATEWAY_ERROR"])
        self.assertTrue(fact["provider_response_signature_verified"])
        self.assertEqual(fact["binding_checks_passed"], [])

    def test_valid_exact_signed_bytes(self):
        self.assertEqual(self.verify()["status"], "VALID")

    def test_wrong_key(self):
        self.assertFalse(self.verify(key=self.wrong.public_key())["provider_response_signature_verified"])

    def test_tampered_signed_amount(self):
        fact = self.verify(self.envelope().replace(b"0.01", b"9.99"))
        self.assertEqual(fact["reason_codes"], ["SIGNATURE_INVALID"])

    def test_missing_signature(self):
        self.assertEqual(self.verify(json.dumps({RESPONSE: self.payload}).encode())["status"], "INVALID")

    def test_duplicate_key(self):
        raw = self.envelope().replace(b'"active": true', b'"active": false, "active": true')
        self.assertFalse(self.verify(raw)["provider_response_signature_verified"])

    def test_all_binding_mismatches(self):
        for field in self.expected:
            payload = dict(self.payload)
            payload[field] = "0.02" if field == "amount" else "wrong"
            self.assertEqual(self.verify(self.envelope(payload))["reason_codes"], ["BINDING_MISMATCH"])

    def test_all_missing_fields(self):
        for field in self.expected:
            payload = dict(self.payload)
            del payload[field]
            self.assertEqual(self.verify(self.envelope(payload))["status"], "MISSING_EVIDENCE")

    def test_no_expected_backfill(self):
        del self.expected["resource_id"]
        self.assertEqual(self.verify()["status"], "MISSING_EVIDENCE")

    def test_exact_decimal(self):
        self.payload["amount"] = "0.010"
        self.assertEqual(self.verify()["status"], "VALID")
        self.payload["amount"] = "0.010000000000000001"
        self.assertEqual(self.verify()["status"], "INVALID")

    def test_invalid_amounts(self):
        for value in ["NaN", "Infinity", "-1", "0", 0.01, True]:
            self.payload["amount"] = value
            self.assertEqual(self.verify()["status"], "MISSING_EVIDENCE")

    def test_active_requires_boolean(self):
        self.payload["active"] = "true"
        self.assertEqual(self.verify()["status"], "MISSING_EVIDENCE")

    def test_inactive(self):
        self.payload["active"] = False
        self.assertEqual(self.verify()["reason_codes"], ["PROVIDER_INACTIVE"])

    def test_business_error_is_not_proof_rejection(self):
        self.payload["code"] = "40004"
        self.assertEqual(self.verify()["status"], "PROVIDER_ERROR")

    def test_no_response_text_leak(self):
        self.payload["msg"] = "synthetic-sensitive-content"
        self.assertNotIn("synthetic-sensitive-content", json.dumps(self.verify()))

    def test_sign_request(self):
        params = sign_request(app_id="test-app", private_key=self.key, trade_no="test-trade",
                              payment_proof="x" * 64, timestamp="2026-09-20 12:00:00")
        signature = base64.b64decode(params.pop("sign"))
        canonical = "&".join(k + "=" + params[k] for k in sorted(params)).encode()
        self.key.public_key().verify(signature, canonical, padding.PKCS1v15(), hashes.SHA256())
        self.assertEqual(params["method"], "alipay.aipay.agent.payment.verify")

    def test_production_gateway_refused(self):
        with self.assertRaises(ValueError):
            sign_request(app_id="test", private_key=self.key, trade_no="test", payment_proof="x",
                         timestamp="test", gateway="https://openapi.alipay.com/gateway.do")


if __name__ == "__main__":
    unittest.main()

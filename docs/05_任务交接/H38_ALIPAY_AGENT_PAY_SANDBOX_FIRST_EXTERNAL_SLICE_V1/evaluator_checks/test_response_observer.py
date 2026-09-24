import base64
import unittest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from response_observer import observe


class ObserverTests(unittest.TestCase):
    def test_signed_tampered_wrong_key(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        wrong = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        body = b'{"code":"10000"}'
        signature = base64.b64encode(key.sign(body, padding.PKCS1v15(), hashes.SHA256()))
        raw = b'{"alipay_aipay_agent_payment_verify_response":' + body + b',"sign":"' + signature + b'"}'
        self.assertTrue(observe(raw, key.public_key())["signature_verified"])
        self.assertFalse(observe(raw.replace(b"10000", b"40004"), key.public_key())["signature_verified"])
        self.assertFalse(observe(raw, wrong.public_key())["signature_verified"])

    def test_missing_signature(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.assertFalse(observe(b"{}", key.public_key())["signature_verified"])

"""Evaluator-owned cryptographic observation during the existing live call.

Shares only envelope extraction with the adapter; not independent provenance proof.
"""
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from agentic_payment_experiment.adapters.alipay_agent_pay_sandbox import signed_response_parts


def observe(raw, public_key):
    result = dict(response_sha256=hashlib.sha256(raw).hexdigest(),
                  signature_verified=False, network_replayed=False,
                  observation_scope="same_process_crypto_check_shared_parser")
    try:
        _, signed, signature = signed_response_parts(raw)
        public_key.verify(signature, signed, padding.PKCS1v15(), hashes.SHA256())
        result["signature_verified"] = True
    except Exception:
        pass
    return result

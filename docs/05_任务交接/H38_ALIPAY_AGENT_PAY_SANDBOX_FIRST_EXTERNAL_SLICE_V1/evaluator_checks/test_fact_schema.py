"""Synthetic adversarial tests; never live provider evidence."""
import copy
import json
import unittest
from fact_schema import BINDINGS, reject_duplicates, validate


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.fact = dict(status="VALID", provider="ALIPAY_AGENT_PAY_SANDBOX",
            method="alipay.aipay.agent.payment.verify", trade_no_sha256="a" * 64,
            active=True, binding_checks_requested=sorted(BINDINGS),
            binding_checks_passed=sorted(BINDINGS),
            provider_response_signature_verified=True, reason_codes=["VERIFIED"])

    def test_complete_synthetic_fact(self):
        self.assertIsNone(validate(self.fact, "valid"))

    def test_incomplete_binding_cannot_self_declare_success(self):
        for binding in BINDINGS:
            fact = copy.deepcopy(self.fact)
            fact["binding_checks_requested"].remove(binding)
            fact["binding_checks_passed"].remove(binding)
            self.assertIsNotNone(validate(fact, "valid"))

    def test_duplicate_binding(self):
        self.fact["binding_checks_requested"].append("amount")
        self.assertIsNotNone(validate(self.fact, "valid"))

    def test_unknown_nested_payload(self):
        self.fact["metadata"] = {"client_session": "synthetic"}
        self.assertIsNotNone(validate(self.fact, "valid"))

    def test_free_text_and_nested_reasons(self):
        for reason in [["synthetic-secret"], [{"raw_response": "synthetic"}], "VERIFIED"]:
            self.fact["reason_codes"] = reason
            self.assertIsNotNone(validate(self.fact, "valid"))

    def test_signature_requires_boolean_true(self):
        for value in [False, 1, "true", None]:
            self.fact["provider_response_signature_verified"] = value
            self.assertIsNotNone(validate(self.fact, "valid"))

    def test_digest_trailing_newline(self):
        self.fact["trade_no_sha256"] += "\n"
        self.assertIsNotNone(validate(self.fact, "valid"))

    def test_provider_negative(self):
        self.fact.update(status="INVALID", active=False,
                         binding_checks_passed=[], reason_codes=["PROVIDER_REJECTED_PROOF"])
        self.assertIsNone(validate(self.fact, "tampered-proof"))

    def test_failure_cannot_masquerade_as_security_rejection(self):
        self.fact.update(status="INVALID", active=False, binding_checks_passed=[])
        for reason in ["NETWORK_ERROR", "SIGNATURE_INVALID", "MISSING_BINDING", "BINDING_MISMATCH"]:
            self.fact["reason_codes"] = [reason]
            self.assertIsNotNone(validate(self.fact, "tampered-proof"))

    def test_active_negative_rejected(self):
        self.fact.update(status="INVALID", reason_codes=["PROVIDER_INACTIVE"])
        self.assertIsNotNone(validate(self.fact, "tampered-proof"))

    def test_malformed_shapes(self):
        for data in [None, [], "text", {}, {"status": "VALID"}]:
            self.assertIsNotNone(validate(data, "valid"))

    def test_duplicate_json_keys(self):
        with self.assertRaises(ValueError):
            json.loads('{"active": false, "active": true}', object_pairs_hook=reject_duplicates)


if __name__ == "__main__":
    unittest.main()

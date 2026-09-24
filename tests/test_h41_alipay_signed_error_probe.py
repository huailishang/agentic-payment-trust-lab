"""Offline entry-point and real RSA tests; never read configured user keys."""
import base64
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from urllib.parse import parse_qs
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import h41_alipay_signed_error_probe as probe
REAL_TRANSPORT = probe.transport
from agentic_payment_experiment.adapters.alipay_agent_pay_sandbox import RESPONSE
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

SECRET = "SYNTHETIC_SECRET_DO_NOT_EMIT_41"
FIELDS = {"schema", "task", "observed_at", "implementation_sha256", "gateway",
          "attempt_count", "http_status", "response_sha256", "signature_verified",
          "classification", "reason", "code", "sub_code", "observation_scope",
          "synthetic_input", "payment_success_proven", "binding_proven"}


def current(**updates):
    fields = dict(probe.EXPECTED, authorization_api_call="true")
    fields.update(updates)
    return "```yaml\n" + "\n".join(k + ": " + v for k, v in fields.items()) + "\n```\n"


class ProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.other = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / probe.PACKAGE_REL / "evidence"
        self.directory.mkdir(parents=True)
        self.state = self.root / "CURRENT.md"
        self.state.write_text(current(), encoding="utf-8")
        self.output = self.directory / "result.json"
        self.reservation = self.directory / "H41_DIAGNOSTIC.reserved"
        self.stdout, self.stderr = io.StringIO(), io.StringIO()
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(probe, "ROOT", self.root))
        self.stack.enter_context(patch.dict(os.environ, {"AIPAY_APP_ID": "123456", "H38_PAYMENT_PROOF": SECRET}))
        self.inspect = self.stack.enter_context(patch.object(probe, "inspect", return_value={
            "app_private": self.other, "alipay_public": self.private.public_key()}))
        self.signer = self.stack.enter_context(patch.object(probe, "sign_request", wraps=probe.sign_request))
        self.transport = self.stack.enter_context(patch.object(probe, "transport", return_value=(200, self.signed())))

    def signed(self, payload=None):
        if payload is None:
            payload = {"code": "40004", "sub_code": "TRADE_NOT_FOUND", "msg": SECRET,
                       "nested": {"secret": SECRET}}
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
        signature = self.private.sign(body, padding.PKCS1v15(), hashes.SHA256())
        return b'{"' + RESPONSE.encode() + b'": ' + body + b', "sign": "' + base64.b64encode(signature) + b'"}'

    def run_main(self, argv=None):
        if argv is None:
            argv = ["--execute", "--output", str(self.output), "--key-file", "synthetic-unused"]
        with contextlib.redirect_stdout(self.stdout), contextlib.redirect_stderr(self.stderr):
            code = probe.main(argv)
        self.assertNotIn(SECRET, self.stdout.getvalue() + self.stderr.getvalue())
        for path in self.directory.iterdir():
            if path.is_file():
                self.assertNotIn(SECRET, path.read_text())
        return code

    def fact(self):
        fact = json.loads(self.output.read_text())
        self.assertEqual(set(fact), FIELDS)
        self.assertFalse(fact["payment_success_proven"])
        self.assertFalse(fact["binding_proven"])
        self.assertTrue(fact["synthetic_input"])
        return fact

    def test_default_dry_run(self):
        self.assertEqual(self.run_main([]), 0)
        self.inspect.assert_not_called()
        self.signer.assert_not_called()
        self.transport.assert_not_called()
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_gate_mutations_before_all_side_effects(self):
        variants = [current(task_id="H38"), current(state="CONTRACT_FROZEN"),
                    current(current_role="Evaluator"), current(workflow="wrong"),
                    current(authorization_api_call="false"), current(authorization_api_call='"true"'),
                    current(execution_phase="H41_OFFLINE_PREPARATION"), current(contract_path="wrong"),
                    current() + current(), "<!--\n" + current() + "-->\n",
                    "````text\n" + current() + "````\n", current() + "```yaml\ntask_id: x",
                    current().replace("authorization_api_call: true", "authorization_api_call: true\nauthorization_api_call: true")]
        for value in variants:
            with self.subTest(value=value):
                self.state.write_text(value, encoding="utf-8")
                self.assertEqual(self.run_main(), 1)
                self.inspect.assert_not_called()
                self.signer.assert_not_called()
                self.transport.assert_not_called()
                self.assertFalse(self.reservation.exists())

    def test_actual_current_p0_blocked(self):
        real = Path(__file__).resolve().parents[1] / "CURRENT.md"
        self.state.write_bytes(real.read_bytes())
        self.assertEqual(self.run_main(), 1)
        self.inspect.assert_not_called()
        self.transport.assert_not_called()

    def test_successful_fake_attempt_and_fixed_request(self):
        self.assertEqual(self.run_main(), 0)
        self.transport.assert_called_once()
        request = self.transport.call_args.args[0]
        self.assertEqual(request.full_url, probe.GATEWAY)
        self.assertEqual(request.get_method(), "POST")
        params = parse_qs(request.data.decode())
        self.assertEqual(params["method"], ["alipay.aipay.agent.payment.verify"])
        self.assertEqual(json.loads(params["biz_content"][0]), {"trade_no": "0" * 32, "payment_proof": "0" * 64})
        fact = self.fact()
        self.assertEqual(fact["classification"], "SIGNED_BUSINESS_ERROR")
        self.assertEqual(fact["response_sha256"], hashlib.sha256(self.signed()).hexdigest())
        self.assertTrue(fact["signature_verified"])
        self.assertEqual(fact["attempt_count"], 1)
        self.assertTrue(self.reservation.exists())
        self.output = self.directory / "different.json"
        self.assertEqual(self.run_main(), 1)
        self.transport.assert_called_once()
        self.inspect.assert_called_once()

    def test_second_authorization_revocation(self):
        real_signer = probe.sign_request._mock_wraps
        def revoke(**kwargs):
            self.state.write_text(current(authorization_api_call="false"), encoding="utf-8")
            return real_signer(**kwargs)
        self.signer.side_effect = revoke
        self.assertEqual(self.run_main(), 1)
        self.transport.assert_not_called()
        self.assertFalse(self.reservation.exists())
        self.assertEqual(self.fact()["attempt_count"], 0)

    def test_local_output_rejections(self):
        self.output.write_text("existing")
        self.assertEqual(self.run_main(), 1)
        self.assertEqual(self.output.read_text(), "existing")
        self.output = self.root / "outside.json"
        self.assertEqual(self.run_main(), 1)
        self.output = self.reservation
        self.assertEqual(self.run_main(), 1)
        self.inspect.assert_not_called()
        self.transport.assert_not_called()

    def test_existing_reservation_without_output(self):
        self.reservation.write_text("retained")
        self.assertEqual(self.run_main(), 1)
        self.inspect.assert_not_called()
        self.transport.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_reservation_race_rejects_before_transport(self):
        real_signer = self.signer._mock_wraps
        def reserve_elsewhere(**kwargs):
            self.reservation.write_text("another synthetic runner reserved")
            return real_signer(**kwargs)
        self.signer.side_effect = reserve_elsewhere
        self.assertEqual(self.run_main(), 1)
        self.transport.assert_not_called()
        self.assertEqual(self.fact()["attempt_count"], 0)

    def test_evidence_write_failure_retains_reservation(self):
        with patch.object(probe.json, "dump", side_effect=OSError(SECRET)):
            self.assertEqual(self.run_main(), 1)
        self.assertTrue(self.reservation.exists())
        self.output = self.directory / "other.json"
        self.assertEqual(self.run_main(), 1)
        self.transport.assert_called_once()

    def test_crypto_negatives_through_main(self):
        variants = [self.signed().replace(b"40004", b"20000"), b'{}', b'not json',
                    self.signed().replace(b'"code": "40004"', b'"code": "40004", "code": "20000"'),
                    self.signed().replace(RESPONSE.encode(), b"unknown_response"),
                    self.signed({"msg": SECRET})]
        for index, raw in enumerate(variants):
            with self.subTest(index=index):
                self.transport.return_value = (200, raw)
                self.assertEqual(self.run_main(), 1)
                self.assertEqual(self.fact()["classification"], "UNVERIFIED_RESPONSE")
                self.transport.assert_called_once()
                # Reset only this test's temporary synthetic files for next independent case.
                self.output.unlink()
                self.reservation.unlink()
                self.transport.reset_mock()
        self.inspect.return_value["alipay_public"] = self.other.public_key()
        self.transport.return_value = (200, self.signed())
        self.assertEqual(self.run_main(), 1)
        self.assertFalse(self.fact()["signature_verified"])

    def test_key_and_signer_exceptions_are_quiet(self):
        self.inspect.side_effect = RuntimeError(SECRET)
        self.assertEqual(self.run_main(), 1)
        self.inspect.side_effect = None
        self.signer.side_effect = RuntimeError(SECRET)
        self.assertEqual(self.run_main(), 1)
        self.assertFalse(self.reservation.exists())
        self.transport.assert_not_called()

    def test_cli_cannot_override_frozen_inputs(self):
        for name in ["trade-no", "payment-proof", "gateway", "method", "session", "force", "current", "exec"]:
            self.assertEqual(self.run_main(["--" + name, SECRET]), 1)
        self.inspect.assert_not_called()
        self.transport.assert_not_called()

    def test_timeout_reservation_retained(self):
        self.transport.side_effect = TimeoutError(SECRET)
        self.assertEqual(self.run_main(), 1)
        self.assertEqual(self.fact()["classification"], "TRANSPORT_INCONCLUSIVE")
        self.assertTrue(self.reservation.exists())
        self.output = self.directory / "retry.json"
        self.assertEqual(self.run_main(), 1)
        self.transport.assert_called_once()

    def test_crypto_and_parser_negative_matrix(self):
        variants = [self.signed().replace(b"40004", b"20000"), b'{}', b'not json',
                    self.signed().replace(b'"code": "40004"', b'"code": "40004", "code": "20000"'),
                    self.signed().replace(RESPONSE.encode(), b"unknown_response"),
                    self.signed({"msg": SECRET}), b"x" * 1_000_001]
        for index, raw in enumerate(variants):
            with self.subTest(index=index):
                fact = probe.classify(raw, self.private.public_key())
                self.assertEqual(fact["classification"], "UNVERIFIED_RESPONSE")
                self.assertNotIn(SECRET, json.dumps(fact))
        self.assertFalse(probe.classify(self.signed(), self.other.public_key())["signature_verified"])

    def test_unexpected_success_stops(self):
        self.transport.return_value = (200, self.signed({"code": "10000"}))
        self.assertEqual(self.run_main(), 1)
        self.assertEqual(self.fact()["classification"], "SIGNED_UNEXPECTED_SUCCESS")
        self.transport.assert_called_once()

    def test_unknown_codes_and_nested_secrets_never_persist(self):
        self.transport.return_value = (200, self.signed({"code": SECRET, "sub_code": {"nested": SECRET},
                                                       "sub_msg": SECRET}))
        self.assertEqual(self.run_main(), 0)
        self.assertEqual(self.fact()["code"], "OTHER")
        self.assertEqual(self.fact()["sub_code"], "OTHER")

    def test_oversized_response_main(self):
        self.transport.return_value = (200, b"x" * 1_000_001)
        self.assertEqual(self.run_main(), 1)
        self.assertEqual(self.fact()["classification"], "UNVERIFIED_RESPONSE")

    def test_real_transport_redirect_and_read_limit(self):
        # Restore production transport, but replace only the urllib opener.
        import importlib.util
        spec = importlib.util.spec_from_file_location("h41_transport_test", probe.__file__)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        opener = Mock()
        with patch.object(module, "build_opener", return_value=opener):
            opener.open.side_effect = HTTPError(probe.GATEWAY, 302, SECRET, {}, None)
            with self.assertRaises(HTTPError):
                module.transport(Mock())
            self.assertEqual(opener.open.call_count, 1)
            self.assertEqual(opener.open.call_args.kwargs, {"timeout": 30})
            opener.open.side_effect = None
            response = Mock(status=200)
            opener.open.return_value = contextlib.nullcontext(response)
            module.transport(Mock())
            response.read.assert_called_once_with(1_000_001)
        self.assertIsNone(module.NoRedirect().redirect_request(None, None, 302, SECRET, {}, "https://elsewhere.invalid"))

    def test_redirect_main_no_retry(self):
        self.transport.side_effect = HTTPError(probe.GATEWAY, 302, SECRET, {}, None)
        self.assertEqual(self.run_main(), 1)
        self.assertEqual(self.fact()["classification"], "TRANSPORT_INCONCLUSIVE")
        self.assertTrue(self.reservation.exists())
        self.transport.assert_called_once()

    def exercise_http_error(self, status, raw, expected, *, read_error=None):
        stream = io.BytesIO(raw)
        error = HTTPError(probe.GATEWAY, status, SECRET, {}, stream)
        opener = Mock()
        opener.open.side_effect = error
        with patch.object(probe, "transport", REAL_TRANSPORT), \
                patch.object(probe, "build_opener", return_value=opener) as builder, \
                patch.object(stream, "read", wraps=stream.read, side_effect=read_error) as read:
            self.assertEqual(self.run_main(), 0 if expected == "SIGNED_BUSINESS_ERROR" else 1)
            fact = self.fact()
            self.assertEqual(fact["classification"], expected)
            self.assertEqual(fact["attempt_count"], 1)
            self.assertTrue(self.reservation.exists())
            self.assertTrue(stream.closed)
            opener.open.assert_called_once()
            self.assertEqual(opener.open.call_args.kwargs, {"timeout": 30})
            self.assertIsInstance(builder.call_args.args[0], probe.NoRedirect)
            if 300 <= status < 400:
                read.assert_not_called()
            else:
                read.assert_called_once_with(1_000_001)
            if expected == "TRANSPORT_INCONCLUSIVE":
                self.assertIsNone(fact["http_status"])
                self.assertIsNone(fact["response_sha256"])
            else:
                self.assertEqual(fact["http_status"], status)
                self.assertEqual(fact["response_sha256"], hashlib.sha256(raw[:1_000_001]).hexdigest())
            self.assertEqual(fact["signature_verified"], expected.startswith("SIGNED_"))
            self.output = self.directory / "retry.json"
            self.assertEqual(self.run_main(), 1)
            opener.open.assert_called_once()
            self.inspect.assert_called_once()
            self.signer.assert_called_once()

    def test_http_error_signed_400(self):
        self.exercise_http_error(400, self.signed(), "SIGNED_BUSINESS_ERROR")

    def test_http_error_signed_500(self):
        self.exercise_http_error(500, self.signed(), "SIGNED_BUSINESS_ERROR")

    def test_http_error_unsigned(self):
        self.exercise_http_error(400, json.dumps({"error": SECRET}).encode(), "UNVERIFIED_RESPONSE")

    def test_http_error_tampered(self):
        self.exercise_http_error(500, self.signed().replace(b"40004", b"20000"), "UNVERIFIED_RESPONSE")

    def test_http_error_unexpected_success(self):
        self.exercise_http_error(400, self.signed({"code": "10000"}), "SIGNED_UNEXPECTED_SUCCESS")

    def test_http_error_oversized(self):
        self.exercise_http_error(500, b"x" * 1_000_100, "UNVERIFIED_RESPONSE")

    def test_http_error_read_failure(self):
        self.exercise_http_error(500, self.signed(), "TRANSPORT_INCONCLUSIVE", read_error=OSError(SECRET))

    def test_http_error_read_timeout(self):
        self.exercise_http_error(400, self.signed(), "TRANSPORT_INCONCLUSIVE", read_error=TimeoutError(SECRET))

    def test_http_redirect_signed_body_is_not_consumed(self):
        self.exercise_http_error(302, self.signed(), "TRANSPORT_INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()

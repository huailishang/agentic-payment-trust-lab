import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import h38_alipay_sandbox_probe as probe


VALID_CURRENT = """# Evaluator ↔ Executor Current State

\x60\x60\x60yaml
workflow: evaluator-executor-workflow/v2.2
task_id: H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1
state: EXECUTING
current_role: Executor
authorization_api_call: true
contract_path: docs/05_任务交接/H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1/CONTRACT.md
\x60\x60\x60
"""


class _FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, _limit):
        return b"{}"


class H38AuthorizationGateTests(unittest.TestCase):
    def _run(
        self,
        current_text=VALID_CURRENT,
        *,
        execute=True,
        env_changes=None,
        missing_env=None,
        outside_output=False,
        mutate_after_sign=None,
        precreate_reservation=False,
    ):
        counters = {"inspect": 0, "sign": 0, "opener": 0, "network": 0}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            package = root / "h38-package"
            evidence = package / "evidence"
            evidence.mkdir(parents=True)
            if current_text is not None:
                (root / "CURRENT.md").write_text(current_text, encoding="utf-8")

            output = (root / "outside.json") if outside_output else (evidence / "fact.json")
            reservation = evidence / "H38_valid.reserved"
            if precreate_reservation:
                reservation.write_text("existing reservation\n", encoding="utf-8")

            env = {
                "AIPAY_APP_ID": "synthetic-app",
                "H38_TRADE_NO": "synthetic-trade",
                "H38_PAYMENT_PROOF": "x" * 64,
                "H38_EXPECTED_OUT_TRADE_NO": "synthetic-order",
                "H38_EXPECTED_AMOUNT": "0.01",
                "H38_EXPECTED_RESOURCE_ID": "synthetic-resource",
            }
            if env_changes:
                env.update(env_changes)
            if missing_env:
                env.pop(missing_env, None)

            def fake_inspect(_path, return_keys=False):
                counters["inspect"] += 1
                self.assertTrue(return_keys)
                return {"app_private": object(), "alipay_public": object()}

            def fake_sign_request(**_kwargs):
                counters["sign"] += 1
                if mutate_after_sign is not None:
                    (root / "CURRENT.md").write_text(mutate_after_sign, encoding="utf-8")
                return {"method": "synthetic"}

            def fake_verify(raw, _key, expected):
                self.assertEqual(set(expected), {"trade_no", "out_trade_no", "amount", "resource_id"})
                if raw == b"":
                    return {"reason_codes": []}
                return {"status": "VALID", "reason_codes": []}

            def fake_build_opener(*_args):
                counters["opener"] += 1

                class _FakeOpener:
                    def open(_self, _request, timeout):
                        self.assertEqual(timeout, 30)
                        counters["network"] += 1
                        return _FakeResponse()

                return _FakeOpener()

            argv = [
                "h38_alipay_sandbox_probe.py",
                "--case",
                "valid",
                "--output",
                str(output),
                "--key-file",
                str(root / "synthetic.keys"),
            ]
            if execute:
                argv.append("--execute")

            with (
                patch.object(probe, "ROOT", root),
                patch.object(probe, "PACKAGE", package),
                patch.object(probe, "inspect", fake_inspect),
                patch.object(probe, "sign_request", fake_sign_request),
                patch.object(probe, "verify_response", fake_verify),
                patch.object(probe, "observe", lambda _raw, _key: {"signature_verified": True}),
                patch.object(probe, "validate", lambda _fact, _case: None),
                patch.object(probe, "build_opener", fake_build_opener),
                patch.object(sys, "argv", argv),
                patch.dict(os.environ, env, clear=True),
            ):
                rc = probe.main()

            return {
                "rc": rc,
                **counters,
                "reservation": reservation.exists(),
                "output": output.exists(),
            }

    def assert_denied_before_side_effects(self, result):
        self.assertEqual(result["rc"], 1)
        self.assertEqual(result["inspect"], 0)
        self.assertEqual(result["sign"], 0)
        self.assertEqual(result["opener"], 0)
        self.assertEqual(result["network"], 0)
        self.assertFalse(result["reservation"])

    def test_allowed_execute_uses_fake_transport_once(self):
        result = self._run()
        self.assertEqual(result["rc"], 0)
        self.assertEqual(result["inspect"], 1)
        self.assertEqual(result["sign"], 1)
        self.assertEqual(result["opener"], 1)
        self.assertEqual(result["network"], 1)
        self.assertTrue(result["reservation"])
        self.assertTrue(result["output"])

    def test_quoted_expected_strings_are_allowed_but_boolean_stays_literal(self):
        quoted = (
            VALID_CURRENT
            .replace("workflow: evaluator-executor-workflow/v2.2", 'workflow: "evaluator-executor-workflow/v2.2"')
            .replace(
                "task_id: H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1",
                'task_id: "H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1"',
            )
            .replace("state: EXECUTING", "state: 'EXECUTING'")
            .replace("current_role: Executor", 'current_role: "Executor"')
            .replace(
                "contract_path: docs/05_任务交接/H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1/CONTRACT.md",
                'contract_path: "docs/05_任务交接/H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1/CONTRACT.md"',
            )
        )
        quoted = quoted.replace("authorization_api_call: true", 'metadata: "ordinary metadata"\nauthorization_api_call: true')
        self.assertEqual(self._run(quoted)["rc"], 0)

    def test_evaluator_discovered_parser_false_allows_are_denied(self):
        four = "`" * 4
        variants = {
            "commented-out-authorization": "<!--\n" + VALID_CURRENT + "-->\n",
            "outer-fence-example": four + "text\n" + VALID_CURRENT + four + "\n",
            "second-unclosed-state": VALID_CURRENT + "```yaml\nauthorization_api_call: false\n",
            "python-string-concatenation": VALID_CURRENT.replace(
                "state: EXECUTING", 'state: "EXEC" "UTING"'
            ),
            "malformed-metadata": VALID_CURRENT.replace(
                "state: EXECUTING", 'metadata: "unterminated\nstate: EXECUTING'
            ),
        }
        for name, current in variants.items():
            with self.subTest(name=name):
                self.assert_denied_before_side_effects(self._run(current))

    def test_indented_fence_variants_are_denied_before_side_effects(self):
        triple = "`" * 3
        four = "`" * 4
        for spaces in (1, 2, 3):
            indent = " " * spaces
            variants = {
                f"outer-example-indent-{spaces}": (
                    indent + four + "text\n" + VALID_CURRENT + indent + four + "\n"
                ),
                f"second-state-indent-{spaces}": (
                    VALID_CURRENT
                    + indent
                    + triple
                    + "yaml\nauthorization_api_call: false\n"
                    + indent
                    + triple
                    + "\n"
                ),
            }
            for name, current in variants.items():
                with self.subTest(name=name):
                    self.assert_denied_before_side_effects(self._run(current))

    def test_dry_run_never_uses_transport_or_reservation(self):
        result = self._run(execute=False)
        self.assertEqual(result["rc"], 0)
        self.assertEqual(result["network"], 0)
        self.assertEqual(result["opener"], 0)
        self.assertFalse(result["reservation"])
        self.assertFalse(result["output"])

    def test_invalid_current_variants_fail_before_keys_signing_or_network(self):
        variants = {
            "h39-task": VALID_CURRENT.replace(
                "H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1",
                "H39_ALIPAY_SANDBOX_FIXTURE_READINESS_V1",
                1,
            ),
            "h40-task": VALID_CURRENT.replace(
                "H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1",
                "H40_ALIPAY_LIVE_AUTHORIZATION_GATE_REPAIR_V1",
                1,
            ),
            "false-auth": VALID_CURRENT.replace("authorization_api_call: true", "authorization_api_call: false"),
            "missing-auth": VALID_CURRENT.replace("authorization_api_call: true\n", ""),
            "quoted-true": VALID_CURRENT.replace("authorization_api_call: true", 'authorization_api_call: "true"'),
            "wrong-role": VALID_CURRENT.replace("current_role: Executor", "current_role: Evaluator"),
            "wrong-state": VALID_CURRENT.replace("state: EXECUTING", "state: CONTRACT_FROZEN"),
            "wrong-contract": VALID_CURRENT.replace("CONTRACT.md", "OTHER.md"),
            "wrong-workflow": VALID_CURRENT.replace("evaluator-executor-workflow/v2.2", "evaluator-executor-workflow/v2.1"),
            "malformed": VALID_CURRENT.replace("state: EXECUTING", "state EXECUTING"),
            "duplicate-field": VALID_CURRENT.replace(
                "authorization_api_call: true",
                "authorization_api_call: true\nauthorization_api_call: true",
            ),
            "duplicate-block": VALID_CURRENT + "\n\x60\x60\x60yaml\nstate: EXECUTING\n\x60\x60\x60\n",
            "prose-spoof": (
                VALID_CURRENT.replace("authorization_api_call: true", "authorization_api_call: false")
                + "\nauthorization_api_call: true\n"
            ),
            "nested-spoof": VALID_CURRENT.replace(
                "authorization_api_call: true",
                "authorization_api_call: false\nmetadata: safe\n  authorization_api_call: true",
            ),
        }
        for name, current in variants.items():
            with self.subTest(name=name):
                self.assert_denied_before_side_effects(self._run(current))

    def test_missing_current_fails_closed_before_side_effects(self):
        self.assert_denied_before_side_effects(self._run(None))

    def test_mid_run_revocation_is_rechecked_before_reservation(self):
        revoked = VALID_CURRENT.replace("authorization_api_call: true", "authorization_api_call: false")
        result = self._run(mutate_after_sign=revoked)
        self.assertEqual(result["rc"], 1)
        self.assertEqual(result["inspect"], 1)
        self.assertEqual(result["sign"], 1)
        self.assertEqual(result["opener"], 0)
        self.assertEqual(result["network"], 0)
        self.assertFalse(result["reservation"])
        self.assertFalse(result["output"])

    def test_existing_reservation_prevents_replay_without_network(self):
        result = self._run(precreate_reservation=True)
        self.assertEqual(result["rc"], 1)
        self.assertEqual(result["network"], 0)
        self.assertEqual(result["opener"], 0)
        self.assertTrue(result["reservation"])
        self.assertFalse(result["output"])

    def test_non_sandbox_gateway_still_blocks_before_keys(self):
        result = self._run(env_changes={"AIPAY_GATEWAY": "https://openapi.alipay.com/gateway.do"})
        self.assert_denied_before_side_effects(result)

    def test_missing_fixture_still_blocks_before_keys(self):
        result = self._run(missing_env="H38_PAYMENT_PROOF")
        self.assert_denied_before_side_effects(result)

    def test_illegal_output_path_still_blocks_before_transport(self):
        result = self._run(outside_output=True)
        self.assertEqual(result["rc"], 1)
        self.assertEqual(result["network"], 0)
        self.assertEqual(result["opener"], 0)
        self.assertFalse(result["reservation"])


if __name__ == "__main__":
    unittest.main()

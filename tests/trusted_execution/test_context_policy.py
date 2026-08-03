from __future__ import annotations

import unittest
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agentic_payment_experiment.trusted_execution import (
    POLICY_VERSION,
    CandidateFactUpdate,
    FactDomain,
    SourceType,
    VerificationStatus,
    evaluate_context_policy,
)


class ContextPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = {
            "mandate": {"max_amount": "500.00"},
            "request": {
                "amount": "480.00",
                "payee": "payee-1",
                "agent_id": "agent-1",
            },
        }
        self.sources = {
            "mandate.max_amount": SourceType.USER_CONFIRMED,
            "request.amount": SourceType.USER_CONFIRMED,
            "request.payee": SourceType.USER_CONFIRMED,
            "request.agent_id": SourceType.USER_CONFIRMED,
        }

    def evaluate(self, *updates, **kwargs):
        return evaluate_context_policy(
            self.state,
            tuple(updates),
            trusted_sources=self.sources,
            policy_version=kwargs.pop("policy_version", POLICY_VERSION),
            current_action=kwargs.pop("current_action", "execute_payment"),
            **kwargs,
        )

    def update(self, source, domain, path, value, source_ref="fixture-source"):
        return CandidateFactUpdate(source, domain, path, value, source_ref=source_ref)

    def test_closed_models_contain_required_source_and_fact_domains(self) -> None:
        self.assertEqual(10, len(SourceType))
        self.assertEqual(6, len(FactDomain))
        self.assertIn(SourceType.PAYMENT_PROVIDER_OBSERVED, SourceType)
        self.assertIn(FactDomain.EXECUTOR_IDENTITY, FactDomain)

    def test_low_trust_sources_cannot_overwrite_critical_facts(self) -> None:
        cases = (
            (SourceType.WEB_UNTRUSTED, FactDomain.PAYMENT_REQUEST, "request.amount"),
            (SourceType.LLM_GENERATED, FactDomain.PAYMENT_REQUEST, "request.payee"),
            (
                SourceType.EXTERNAL_TOOL_UNTRUSTED,
                FactDomain.EXECUTOR_IDENTITY,
                "request.agent_id",
            ),
            (SourceType.AGENT_INFERRED, FactDomain.AUTHORITY, "mandate.max_amount"),
        )
        for source, domain, path in cases:
            with self.subTest(path=path):
                result = self.evaluate(self.update(source, domain, path, "evil"))
                self.assertEqual(VerificationStatus.VALID, result.fact.status)
                self.assertEqual((path,), result.fact.blocked_paths)
                self.assertFalse(result.fact.trusted_state_changed)
                self.assertEqual(self.state, result.trusted_state)

    def test_provider_status_update_is_allowed_but_authority_is_not(self) -> None:
        allowed = self.update(
            SourceType.PAYMENT_PROVIDER_OBSERVED,
            FactDomain.PAYMENT_STATUS,
            "payment_status_observation.status",
            "SUCCEEDED",
        )
        blocked = self.update(
            SourceType.PAYMENT_PROVIDER_OBSERVED,
            FactDomain.AUTHORITY,
            "mandate.max_amount",
            "9999.00",
        )
        result = self.evaluate(allowed, blocked)
        self.assertEqual(VerificationStatus.VALID, result.fact.status)
        self.assertEqual(
            ("payment_status_observation.status",), result.fact.applied_paths
        )
        self.assertEqual(("mandate.max_amount",), result.fact.blocked_paths)
        self.assertEqual(
            "SUCCEEDED", result.trusted_state["payment_status_observation"]["status"]
        )
        self.assertEqual("500.00", result.trusted_state["mandate"]["max_amount"])

    def test_merchant_cannot_overwrite_a_confirmed_order_fact(self) -> None:
        state = {"final_order": {"total_amount": "480.00"}}
        result = evaluate_context_policy(
            state,
            (
                self.update(
                    SourceType.MERCHANT_PROVIDED,
                    FactDomain.TRANSACTION_ORDER,
                    "final_order.total_amount",
                    "490.00",
                ),
            ),
            trusted_sources={
                "final_order.total_amount": SourceType.USER_CONFIRMED,
            },
            current_action="execute_payment",
        )
        self.assertEqual(("final_order.total_amount",), result.fact.blocked_paths)
        self.assertEqual(state, result.trusted_state)

    def test_missing_metadata_and_unknown_combinations_fail_closed(self) -> None:
        missing = self.evaluate(
            self.update(
                SourceType.PAYMENT_PROVIDER_OBSERVED,
                FactDomain.PAYMENT_STATUS,
                "payment_status_observation.status",
                "SUCCEEDED",
                source_ref=None,
            )
        )
        self.assertEqual(VerificationStatus.MISSING_EVIDENCE, missing.fact.status)
        self.assertEqual((), missing.fact.applied_paths)
        unknown = self.evaluate(
            CandidateFactUpdate(
                "UNKNOWN",
                "UNKNOWN",
                "request.amount",
                "1.00",
                source_ref="unknown-fixture",
            )
        )
        self.assertEqual(VerificationStatus.MISSING_EVIDENCE, unknown.fact.status)
        self.assertEqual(("request.amount",), unknown.fact.blocked_paths)

    def test_merge_is_copy_based_and_detects_actual_unauthorized_mutation(self) -> None:
        observed = {
            **self.state,
            "request": {**self.state["request"], "amount": "699.00"},
        }
        result = self.evaluate(observed_state_after=observed)
        self.assertEqual(VerificationStatus.INVALID, result.fact.status)
        self.assertTrue(result.fact.unauthorized_state_change_detected)
        self.assertEqual("480.00", self.state["request"]["amount"])
        result.trusted_state["request"]["amount"] = "changed-copy"
        self.assertEqual("480.00", self.state["request"]["amount"])

    def test_policy_and_current_action_are_required(self) -> None:
        result = self.evaluate(policy_version=None, current_action=None)
        self.assertEqual(VerificationStatus.MISSING_EVIDENCE, result.fact.status)
        self.assertIn("context_policy_version_missing", result.fact.reason_codes)
        self.assertIn("context_current_action_missing", result.fact.reason_codes)

    def test_unresolved_value_ref_is_blocked_without_writing_none(self) -> None:
        before = deepcopy(self.state)
        update = CandidateFactUpdate(
            SourceType.PAYMENT_PROVIDER_OBSERVED,
            FactDomain.PAYMENT_STATUS,
            "payment_status_observation.status",
            value_ref="provider://status/1",
            source_ref="offline-provider",
        )
        result = self.evaluate(update)
        self.assertEqual(VerificationStatus.MISSING_EVIDENCE, result.fact.status)
        self.assertEqual((), result.fact.applied_paths)
        self.assertEqual(
            ("payment_status_observation.status",), result.fact.blocked_paths
        )
        self.assertIn(
            "value_ref_unresolved:payment_status_observation.status",
            result.fact.reason_codes,
        )
        self.assertNotIn("payment_status_observation", result.trusted_state)
        self.assertEqual(before, self.state)

    def test_required_source_coverage_is_missing_partial_or_complete(self) -> None:
        required = (
            "mandate.max_amount",
            "request.agent_id",
            "request.amount",
        )
        cases = (
            ("empty", {}, VerificationStatus.MISSING_EVIDENCE, required),
            (
                "partial",
                {"mandate.max_amount": SourceType.USER_CONFIRMED},
                VerificationStatus.MISSING_EVIDENCE,
                ("request.agent_id", "request.amount"),
            ),
            (
                "complete",
                self.sources,
                VerificationStatus.VALID,
                (),
            ),
        )
        for name, sources, expected_status, missing in cases:
            with self.subTest(name=name):
                result = evaluate_context_policy(
                    self.state,
                    trusted_sources=sources,
                    required_source_paths=required,
                    current_action="execute_payment",
                )
                self.assertEqual(expected_status, result.fact.status)
                self.assertEqual(tuple(sorted(missing)), result.fact.missing_source_paths)
                self.assertEqual(
                    tuple(path for path in required if path not in missing),
                    result.fact.covered_source_paths,
                )

    def test_unknown_or_untrusted_source_does_not_count_as_coverage(self) -> None:
        for source in ("UNKNOWN", SourceType.WEB_UNTRUSTED):
            with self.subTest(source=source):
                result = evaluate_context_policy(
                    self.state,
                    trusted_sources={"request.amount": source},
                    required_source_paths=("request.amount",),
                    current_action="execute_payment",
                )
                self.assertEqual(VerificationStatus.MISSING_EVIDENCE, result.fact.status)
                self.assertEqual(
                    ("request.amount",), result.fact.missing_source_paths
                )


if __name__ == "__main__":
    unittest.main()

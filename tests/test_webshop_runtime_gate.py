from __future__ import annotations

import ast
import builtins
import importlib.util
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment import (
    ActionReversibility,
    AgentIdentity,
    Decision,
    GovernedActionType,
    GovernedPaymentAction,
    IntentMandate,
    PaymentExecutionRecord,
    PaymentStatus,
    SideEffectClass,
    WebShopBuyNowGateOutcome,
    gate_webshop_buy_now,
)
from agentic_payment_experiment.adapters.webshop import adapt_webshop_purchase_candidate
from agentic_payment_experiment.payment_execution import (
    PAYMENT_CONTEXT_ACTION,
    PAYMENT_REQUIRED_SOURCE_PATHS,
)
from agentic_payment_experiment.trusted_execution import (
    POLICY_VERSION,
    SourceType,
    VerificationStatus,
    create_confirmation_record,
    evaluate_context_policy,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "samples/external/webshop/pre_buy_now_candidate_v1.json"
GATE_PATH = ROOT / "src/agentic_payment_experiment/webshop_runtime_gate.py"
MATRIX_PATH = ROOT / "samples/external/webshop/checkout_snapshot_anomalies_v1.json"
MATRIX_RUNNER_PATH = ROOT / "scripts/validation/webshop/run_checkout_snapshot_anomalies.py"


def load_matrix_runner():
    spec = importlib.util.spec_from_file_location(
        "checkout_snapshot_anomaly_runner",
        MATRIX_RUNNER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
REQUIRED_LIMITATIONS = {
    "offline_interception_only",
    "no_webshop_runtime_execution",
    "no_real_buy_now_execution",
    "no_real_payment_or_fulfilment",
    "instruction_is_not_authorization_mandate",
    "checkout_callback_is_injected_test_seam",
}


def load_adaptation():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    adapted = adapt_webshop_purchase_candidate(fixture)
    assert adapted.ready and adapted.order is not None and adapted.payment_request is not None
    return adapted


def context_fact(mandate, order, request, *, state_overrides=None, sources_overrides=None, **kwargs):
    state = {
        "mandate": {"mandate_id": mandate.mandate_id},
        "final_order": {"order_id": order.order_id},
        "request": {
            "request_id": request.request_id,
            "agent_id": request.agent_id,
            "amount": request.amount,
            "payee": request.payee,
            "currency": request.currency,
        },
    }
    if state_overrides:
        for section, values in state_overrides.items():
            state.setdefault(section, {}).update(values)
    sources = {
        "mandate.mandate_id": SourceType.USER_CONFIRMED,
        "final_order.order_id": SourceType.USER_CONFIRMED,
        "request.request_id": SourceType.PROTOCOL_VERIFIED,
        "request.agent_id": SourceType.USER_CONFIRMED,
        "request.amount": SourceType.USER_CONFIRMED,
        "request.payee": SourceType.USER_CONFIRMED,
        "request.currency": SourceType.USER_CONFIRMED,
    }
    if sources_overrides:
        sources.update(sources_overrides)
    return evaluate_context_policy(
        state,
        trusted_sources=sources,
        required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
        current_action=kwargs.pop("current_action", PAYMENT_CONTEXT_ACTION),
        policy_version=kwargs.pop("policy_version", POLICY_VERSION),
        **kwargs,
    ).fact


class WebShopRuntimeGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.adaptation = load_adaptation()
        assert self.adaptation.order is not None
        assert self.adaptation.payment_request is not None
        self.agent_id = "webshop-agent-1"
        self.bound_request = replace(
            self.adaptation.payment_request,
            agent_id=self.agent_id,
        )
        self.mandate = IntentMandate(
            mandate_id=self.adaptation.order.mandate_ref,
            user_id="webshop-user-1",
            max_amount=Decimal("1000.00"),
            allowed_merchants=frozenset({self.adaptation.order.merchant}),
            allowed_categories=frozenset({self.bound_request.category}),
            expires_at=self.bound_request.occurred_at + timedelta(hours=2),
            max_count=1,
            expected_agent_id=self.agent_id,
            currency=self.bound_request.currency,
            authority_version=self.adaptation.order.authority_version_ref or "",
        )
        self.confirmation = create_confirmation_record(
            confirmation_id="webshop-confirmation-1",
            authority_id=self.mandate.mandate_id,
            authority_version=self.mandate.authority_version,
            order=self.adaptation.order,
            confirmed_at=self.bound_request.occurred_at - timedelta(minutes=1),
            expires_at=self.bound_request.occurred_at + timedelta(minutes=30),
        )
        self.execution = PaymentExecutionRecord(
            payment_id="webshop-payment-candidate-1",
            request_id=self.bound_request.request_id,
            order_id=self.adaptation.order.order_id,
            status=PaymentStatus.PENDING,
            amount=self.bound_request.amount,
            currency=self.bound_request.currency,
            occurred_at=self.bound_request.occurred_at + timedelta(seconds=1),
            authority_ref=self.mandate.mandate_id,
            agent_ref=self.agent_id,
            transaction_object_ref=self.bound_request.request_id,
            payee=self.adaptation.order.payee,
        )
        self.identity = AgentIdentity(
            agent_id=self.agent_id,
            provider="offline-webshop-provider",
            executor_instance_id="offline-webshop-executor",
            status="active",
        )
        self.context = context_fact(
            self.mandate,
            self.adaptation.order,
            self.bound_request,
        )
        self.governed_action = GovernedPaymentAction(
            action_id="webshop-action-1",
            action_type=GovernedActionType.EXECUTE_PAYMENT,
            subject_ref=self.mandate.user_id,
            agent_ref=self.agent_id,
            executor_ref="offline-webshop-executor",
            authority_ref=self.mandate.mandate_id,
            authority_version=self.mandate.authority_version,
            order_ref=self.adaptation.order.order_id,
            order_version=self.adaptation.order.order_version,
            request_ref=self.bound_request.request_id,
            payment_ref=self.execution.payment_id,
            source_refs=(
                "source:webshop-checkout-snapshot",
                "source:user-confirmation",
            ),
            side_effect_class=SideEffectClass.PAYMENT_EXECUTION,
            reversibility=ActionReversibility.COMPENSATABLE_NOT_REVERSIBLE,
            occurred_at=self.bound_request.occurred_at + timedelta(milliseconds=500),
        )

    def invoke(self, **overrides):
        calls: list[str] = []

        def callback():
            calls.append("checkout")
            return "simulated-webshop-checkout"

        values = {
            "adaptation": self.adaptation,
            "mandate": self.mandate,
            "declared_agent_id": self.agent_id,
            "execution_candidate": self.execution,
            "agent_identity": self.identity,
            "current_provider_ref": "offline-webshop-provider",
            "current_executor_instance_ref": "offline-webshop-executor",
            "context_policy_fact": self.context,
            "checkout_callback": callback,
            "confirmation_record": self.confirmation,
            "seen_request_ids": (),
        }
        values.update(overrides)
        return gate_webshop_buy_now(**values), calls

    def assert_blocked(self, outcome, calls, decision=None):
        self.assertEqual(decision or outcome.decision, outcome.decision)
        self.assertFalse(outcome.checkout_executed)
        self.assertEqual(0, outcome.callback_count)
        self.assertIsNone(outcome.callback_result_ref)
        self.assertEqual([], calls)

    def test_governed_action_api_is_keyword_only_and_optional(self) -> None:
        parameter = inspect.signature(gate_webshop_buy_now).parameters[
            "governed_action"
        ]
        self.assertEqual(inspect.Parameter.KEYWORD_ONLY, parameter.kind)
        self.assertIsNone(parameter.default)
        outcome, calls = self.invoke()
        self.assertEqual(Decision.ALLOW, outcome.decision)
        self.assertIsNone(outcome.governed_action_fact)
        self.assertEqual(["checkout"], calls)

    def test_valid_governed_action_continues_through_p2_p4_and_one_callback(self) -> None:
        outcome, calls = self.invoke(governed_action=self.governed_action)

        self.assertEqual(Decision.ALLOW, outcome.decision)
        self.assertTrue(outcome.checkout_executed)
        self.assertEqual(1, outcome.callback_count)
        self.assertEqual(["checkout"], calls)
        self.assertIsNotNone(outcome.governed_action_fact)
        self.assertEqual(
            VerificationStatus.VALID,
            outcome.governed_action_fact.status,
        )
        self.assertEqual(
            ("governed_action_binding_valid",),
            outcome.governed_action_fact.reason_codes,
        )
        self.assertIsNotNone(outcome.runtime_gate_record)
        self.assertIn("runtime:allow", outcome.reason_codes)

    def test_missing_governed_action_evidence_is_indeterminate_before_callback(self) -> None:
        missing = replace(self.governed_action, action_id="")
        outcome, calls = self.invoke(governed_action=missing)

        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assertEqual(("action:action_id_missing",), outcome.reason_codes)
        self.assertIsNotNone(outcome.governed_action_fact)
        self.assertEqual(
            VerificationStatus.MISSING_EVIDENCE,
            outcome.governed_action_fact.status,
        )
        self.assertIsNone(outcome.runtime_gate_record)
        self.assert_blocked(outcome, calls, Decision.INDETERMINATE)

    def test_invalid_governed_action_outer_types_are_denied_without_exception(self) -> None:
        class ActionSubclass(GovernedPaymentAction):
            pass

        class ExplodingProxy:
            def __getattribute__(self, name):
                raise AssertionError(f"invalid object attribute read: {name}")

        invalid_objects = (
            SimpleNamespace(**self.governed_action.__dict__),
            self.governed_action.to_dict(),
            [self.governed_action],
            "execute_payment",
            ActionSubclass(**self.governed_action.__dict__),
            ExplodingProxy(),
        )
        for invalid_action in invalid_objects:
            with self.subTest(object_type=type(invalid_action).__name__):
                outcome, calls = self.invoke(governed_action=invalid_action)
                self.assertEqual(Decision.DENY, outcome.decision)
                self.assertEqual(
                    ("action:governed_action_invalid_type",),
                    outcome.reason_codes,
                )
                self.assertIsNotNone(outcome.governed_action_fact)
                self.assertEqual(
                    VerificationStatus.INVALID,
                    outcome.governed_action_fact.status,
                )
                self.assertEqual(
                    ("governed_action_invalid_type",),
                    outcome.governed_action_fact.reason_codes,
                )
                self.assertIsNone(outcome.governed_action_fact.action_id)
                self.assertIsNone(outcome.runtime_gate_record)
                self.assert_blocked(outcome, calls, Decision.DENY)

    def test_invalid_governed_action_is_denied_and_never_reconstructed(self) -> None:
        invalid = replace(
            self.governed_action,
            subject_ref="different-user",
            payment_ref="different-payment",
        )
        outcome, calls = self.invoke(governed_action=invalid)

        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertEqual(
            (
                "action:subject_ref_mismatch",
                "action:payment_ref_mismatch",
            ),
            outcome.reason_codes,
        )
        self.assertIsNotNone(outcome.governed_action_fact)
        self.assertEqual(VerificationStatus.INVALID, outcome.governed_action_fact.status)
        self.assertEqual("different-payment", outcome.governed_action_fact.checked_payment_ref)
        self.assertIsNone(outcome.runtime_gate_record)
        self.assert_blocked(outcome, calls, Decision.DENY)

    def test_valid_governed_action_does_not_replace_p1_p2_p3_or_p4(self) -> None:
        p1_mandate = replace(self.mandate, max_amount=Decimal("1.00"))
        p1, calls = self.invoke(
            mandate=p1_mandate,
            governed_action=self.governed_action,
        )
        self.assertEqual(Decision.DENY, p1.decision)
        self.assertIn("p1:over_budget", p1.reason_codes)
        self.assertIsNone(p1.governed_action_fact)
        self.assert_blocked(p1, calls, Decision.DENY)

        p2_execution = replace(
            self.execution,
            amount=self.execution.amount + Decimal("1.00"),
        )
        p2, calls = self.invoke(
            execution_candidate=p2_execution,
            governed_action=self.governed_action,
        )
        self.assertEqual(Decision.DENY, p2.decision)
        self.assertEqual(VerificationStatus.VALID, p2.governed_action_fact.status)
        self.assertIn("p2:payment_execution_amount_mismatch", p2.reason_codes)
        self.assert_blocked(p2, calls, Decision.DENY)

        p3, calls = self.invoke(
            current_provider_ref="different-provider",
            governed_action=self.governed_action,
        )
        self.assertEqual(Decision.DENY, p3.decision)
        self.assertEqual(VerificationStatus.VALID, p3.governed_action_fact.status)
        self.assertIn("p3:identity_provider_ref_mismatch", p3.reason_codes)
        self.assert_blocked(p3, calls, Decision.DENY)

        p4_context = context_fact(
            self.mandate,
            self.adaptation.order,
            self.bound_request,
            state_overrides={"request": {"amount": Decimal("999.00")}},
        )
        p4, calls = self.invoke(
            context_policy_fact=p4_context,
            governed_action=self.governed_action,
        )
        self.assertEqual(Decision.INDETERMINATE, p4.decision)
        self.assertEqual(VerificationStatus.VALID, p4.governed_action_fact.status)
        self.assertIn("p4:source_coverage_value_mismatch", p4.reason_codes)
        self.assert_blocked(p4, calls, Decision.INDETERMINATE)

    def test_governed_action_context_action_mismatch_stops_before_p4(self) -> None:
        refund_context = context_fact(
            self.mandate,
            self.adaptation.order,
            self.bound_request,
            current_action="refund_payment",
        )
        outcome, calls = self.invoke(
            context_policy_fact=refund_context,
            governed_action=self.governed_action,
        )

        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertEqual(("action:context_action_mismatch",), outcome.reason_codes)
        self.assertEqual(VerificationStatus.INVALID, outcome.governed_action_fact.status)
        self.assertIsNone(outcome.runtime_gate_record)
        self.assert_blocked(outcome, calls, Decision.DENY)

    def test_governed_action_and_all_gate_inputs_remain_immutable(self) -> None:
        before = (
            self.governed_action,
            self.mandate,
            self.adaptation,
            self.execution,
            self.identity,
            self.context,
        )
        outcome, calls = self.invoke(governed_action=self.governed_action)
        self.assertEqual(Decision.ALLOW, outcome.decision)
        self.assertEqual(["checkout"], calls)
        self.assertEqual(
            before,
            (
                self.governed_action,
                self.mandate,
                self.adaptation,
                self.execution,
                self.identity,
                self.context,
            ),
        )

    def test_optional_authorized_snapshot_is_backward_compatible(self) -> None:
        omitted, omitted_calls = self.invoke()
        explicit, explicit_calls = self.invoke(authorized_adaptation=self.adaptation)

        self.assertEqual(omitted, explicit)
        self.assertEqual(Decision.ALLOW, explicit.decision)
        self.assertEqual(["checkout"], omitted_calls)
        self.assertEqual(["checkout"], explicit_calls)
        self.assertEqual(1, explicit.callback_count)

    def test_authorized_snapshot_api_is_keyword_only(self) -> None:
        parameter = inspect.signature(gate_webshop_buy_now).parameters[
            "authorized_adaptation"
        ]
        self.assertEqual(inspect.Parameter.KEYWORD_ONLY, parameter.kind)
        self.assertIsNone(parameter.default)

    def test_incomplete_authorized_snapshot_fails_closed(self) -> None:
        incomplete = replace(self.adaptation, order=None)
        outcome, calls = self.invoke(authorized_adaptation=incomplete)

        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assertEqual(
            ("authorized_commerce_adaptation_not_ready",),
            outcome.reason_codes,
        )
        self.assertIsNone(outcome.prepayment_result)
        self.assertIsNone(outcome.runtime_gate_record)
        self.assert_blocked(outcome, calls, Decision.INDETERMINATE)

    def test_snapshot_changes_reuse_order_validation_and_require_confirmation(self) -> None:
        runner = load_matrix_runner()
        mandate = replace(self.mandate, max_amount=Decimal("5000.00"))
        cases = {
            "price_up": {"order_total_changed", "order_item_unit_amount_changed"},
            "price_down": {"order_total_changed", "order_item_unit_amount_changed"},
            "option_changed": {"order_item_name_changed"},
            "quantity_changed": {"order_total_changed", "order_item_quantity_changed"},
            "content_changed": {"order_item_name_changed"},
            "fulfilment_changed": {"order_fulfilment_terms_changed"},
        }
        for mutation, expected_differences in cases.items():
            with self.subTest(mutation=mutation):
                current = runner._mutate(self.adaptation, mutation)
                outcome, calls = self.invoke(
                    adaptation=current,
                    authorized_adaptation=self.adaptation,
                    mandate=mandate,
                )
                self.assertEqual(Decision.CONFIRMATION_REQUIRED, outcome.decision)
                self.assertIsNotNone(outcome.prepayment_result)
                self.assertEqual(
                    expected_differences,
                    {
                        item.code
                        for item in outcome.prepayment_result.order_differences
                    },
                )
                self.assertIsNone(outcome.runtime_gate_record)
                self.assert_blocked(
                    outcome,
                    calls,
                    Decision.CONFIRMATION_REQUIRED,
                )

    def test_hard_snapshot_changes_preserve_existing_fail_closed_decisions(self) -> None:
        runner = load_matrix_runner()
        mandate = replace(
            self.mandate,
            max_amount=Decimal("5000.00"),
            allowed_merchants=frozenset(
                {self.adaptation.order.merchant, "webshop-other-merchant"}
            ),
        )
        cases = {
            "product_changed": (Decision.INDETERMINATE, "p1:order_id_mismatch"),
            "merchant_changed": (
                Decision.INDETERMINATE,
                "p1:authorized_order_merchant_mismatch",
            ),
            "payee_changed": (Decision.INDETERMINATE, "p1:order_payee_changed"),
            "currency_changed": (Decision.INDETERMINATE, "p1:currency_mismatch"),
            "category_out_of_scope": (Decision.DENY, "p1:category_out_of_scope"),
        }
        for mutation, (expected_decision, expected_reason) in cases.items():
            with self.subTest(mutation=mutation):
                current = runner._mutate(self.adaptation, mutation)
                outcome, calls = self.invoke(
                    adaptation=current,
                    authorized_adaptation=self.adaptation,
                    mandate=mandate,
                )
                self.assertEqual(expected_decision, outcome.decision)
                self.assertIn(expected_reason, outcome.reason_codes)
                self.assertIsNone(outcome.runtime_gate_record)
                self.assert_blocked(outcome, calls, expected_decision)

    def test_explicit_unchanged_snapshot_still_enforces_p2_p3_and_p4(self) -> None:
        cases = (
            (
                "p2",
                {"execution_candidate": replace(self.execution, amount=Decimal("1.00"))},
                Decision.DENY,
                "p2:payment_execution_amount_mismatch",
            ),
            (
                "p3",
                {
                    "agent_identity": replace(
                        self.identity,
                        executor_instance_id="executor-other",
                    )
                },
                Decision.DENY,
                "p3:identity_executor_instance_ref_mismatch",
            ),
            (
                "p4",
                {
                    "context_policy_fact": context_fact(
                        self.mandate,
                        self.adaptation.order,
                        self.bound_request,
                        current_action="refund_payment",
                    )
                },
                Decision.INDETERMINATE,
                "p4:current_action_mismatch",
            ),
        )
        for name, overrides, expected_decision, reason in cases:
            with self.subTest(name=name):
                outcome, calls = self.invoke(
                    authorized_adaptation=self.adaptation,
                    **overrides,
                )
                self.assertEqual(expected_decision, outcome.decision)
                self.assertIn(reason, outcome.reason_codes)
                self.assertIsNotNone(outcome.runtime_gate_record)
                self.assert_blocked(outcome, calls, expected_decision)

    def test_machine_readable_anomaly_matrix_matches_all_expected_decisions(self) -> None:
        runner = load_matrix_runner()
        result = runner.build_anomaly_matrix(MATRIX_PATH)

        self.assertEqual(12, result["summary"]["total"])
        self.assertEqual(12, result["summary"]["matched"])
        self.assertEqual(0, result["summary"]["failed"])
        self.assertIn("no_real_buy_now", result["limitations"])
        self.assertIn("no_real_payment", result["limitations"])
        by_id = {item["case_id"]: item for item in result["cases"]}
        self.assertEqual(1, by_id["unchanged"]["callback_count"])
        self.assertTrue(by_id["unchanged"]["checkout_executed"])
        for case_id, item in by_id.items():
            for field in (
                "baseline_order_ref",
                "baseline_order_version",
                "final_order_ref",
                "final_order_version",
                "expected_decision",
                "actual_decision",
                "callback_count",
                "reason_codes",
                "order_difference_codes",
            ):
                self.assertIn(field, item, (case_id, field))
            self.assertTrue(item["limitations"]["no_real_buy_now"])
            self.assertTrue(item["limitations"]["no_real_payment"])
            if case_id != "unchanged":
                self.assertEqual(0, item["callback_count"], case_id)
                self.assertEqual(0, item["callback_observations"], case_id)
                self.assertFalse(item["checkout_executed"], case_id)

    def test_gate_reuses_validate_request_without_duplicate_order_state_machine(self) -> None:
        source = GATE_PATH.read_text(encoding="utf-8")
        self.assertIn("authorized_order=authorized_snapshot.order", source)
        self.assertIn("final_order=adaptation.order", source)
        self.assertNotIn("from .order_validation import", source)
        self.assertNotIn("validate_order(", source)

    def test_authorized_and_current_snapshot_inputs_remain_immutable(self) -> None:
        runner = load_matrix_runner()
        authorized = self.adaptation
        current = runner._mutate(self.adaptation, "price_up")
        authorized_before = authorized
        current_before = current
        mandate = replace(self.mandate, max_amount=Decimal("5000.00"))

        outcome, calls = self.invoke(
            adaptation=current,
            authorized_adaptation=authorized,
            mandate=mandate,
        )

        self.assertEqual(Decision.CONFIRMATION_REQUIRED, outcome.decision)
        self.assertEqual(authorized_before, authorized)
        self.assertEqual(current_before, current)
        self.assert_blocked(outcome, calls, Decision.CONFIRMATION_REQUIRED)

    def test_permissive_explicit_mandate_allows_one_injected_callback(self) -> None:
        before = self.adaptation
        outcome, calls = self.invoke()

        self.assertEqual(Decision.ALLOW, outcome.decision)
        self.assertTrue(outcome.checkout_executed)
        self.assertEqual(1, outcome.callback_count)
        self.assertEqual("simulated-webshop-checkout", outcome.callback_result_ref)
        self.assertEqual(["checkout"], calls)
        self.assertIsNotNone(outcome.prepayment_result)
        self.assertEqual(Decision.ALLOW, outcome.prepayment_result.decision)
        self.assertIsNotNone(outcome.runtime_gate_record)
        self.assertEqual(Decision.ALLOW, outcome.runtime_gate_record.final_decision)
        self.assertEqual(VerificationStatus.VALID.value, outcome.runtime_gate_record.binding_status)
        self.assertEqual(VerificationStatus.VALID.value, outcome.runtime_gate_record.identity_status)
        self.assertEqual(VerificationStatus.VALID.value, outcome.runtime_gate_record.context_policy_status)
        self.assertEqual(before, self.adaptation)
        self.assertIsNone(self.adaptation.payment_request.agent_id)
        self.assertEqual(self.agent_id, outcome.bound_request.agent_id)
        self.assertTrue(REQUIRED_LIMITATIONS.issubset(set(outcome.limitations)))

    def test_restrictive_instruction_like_mandate_denies_console_table(self) -> None:
        mandate = replace(
            self.mandate,
            max_amount=Decimal("30.00"),
            allowed_categories=frozenset({"clothing"}),
        )
        outcome, calls = self.invoke(mandate=mandate)

        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertIn("p1:over_budget", outcome.reason_codes)
        self.assertIn("p1:category_out_of_scope", outcome.reason_codes)
        self.assert_blocked(outcome, calls, Decision.DENY)

    def test_pre_payment_amount_currency_merchant_category_expiry_and_count_fail_closed(self) -> None:
        cases = (
            ("amount", replace(self.mandate, max_amount=Decimal("1.00")), Decision.DENY),
            ("currency", replace(self.mandate, currency="CNY"), Decision.INDETERMINATE),
            ("merchant", replace(self.mandate, allowed_merchants=frozenset({"other"})), Decision.DENY),
            ("category", replace(self.mandate, allowed_categories=frozenset({"clothing"})), Decision.DENY),
            ("expiry", replace(self.mandate, expires_at=self.bound_request.occurred_at - timedelta(seconds=1)), Decision.DENY),
            ("count", replace(self.mandate, max_count=0), Decision.DENY),
        )
        for name, mandate, expected in cases:
            with self.subTest(name=name):
                outcome, calls = self.invoke(mandate=mandate)
                self.assertEqual(expected, outcome.decision)
                self.assert_blocked(outcome, calls, expected)

    def test_confirmation_required_and_indeterminate_preserve_zero_callbacks(self) -> None:
        stale = replace(
            self.confirmation,
            expires_at=self.bound_request.occurred_at - timedelta(seconds=1),
        )
        confirmation_required, calls = self.invoke(confirmation_record=stale)
        self.assertEqual(Decision.CONFIRMATION_REQUIRED, confirmation_required.decision)
        self.assert_blocked(confirmation_required, calls, Decision.CONFIRMATION_REQUIRED)

        indeterminate, calls = self.invoke(confirmation_record=None)
        self.assertEqual(Decision.INDETERMINATE, indeterminate.decision)
        self.assert_blocked(indeterminate, calls, Decision.INDETERMINATE)

    def test_duplicate_request_is_denied_before_runtime_gate(self) -> None:
        outcome, calls = self.invoke(seen_request_ids=(self.bound_request.request_id,))
        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertIn("p1:duplicate_request", outcome.reason_codes)
        self.assert_blocked(outcome, calls, Decision.DENY)

    def test_not_ready_adaptation_and_blank_declared_agent_fail_closed(self) -> None:
        not_ready = replace(self.adaptation, order=None)
        outcome, calls = self.invoke(adaptation=not_ready)
        self.assertEqual(("commerce_adaptation_not_ready",), outcome.reason_codes)
        self.assert_blocked(outcome, calls, Decision.INDETERMINATE)

        for value in (None, "", "   "):
            with self.subTest(value=value):
                outcome, calls = self.invoke(declared_agent_id=value)
                self.assertEqual(("declared_agent_id_missing",), outcome.reason_codes)
                self.assert_blocked(outcome, calls, Decision.INDETERMINATE)

    def test_every_mandatory_explicit_input_is_required(self) -> None:
        cases = (
            ("mandate", "intent_mandate_missing"),
            ("execution_candidate", "payment_execution_candidate_missing"),
            ("agent_identity", "agent_identity_missing"),
            ("current_provider_ref", "current_provider_ref_missing"),
            ("current_executor_instance_ref", "current_executor_instance_ref_missing"),
            ("context_policy_fact", "context_policy_fact_missing"),
            ("checkout_callback", "checkout_callback_missing"),
        )
        for field, reason in cases:
            with self.subTest(field=field):
                outcome, calls = self.invoke(**{field: None})
                self.assertIn(reason, outcome.reason_codes)
                self.assert_blocked(outcome, calls, Decision.INDETERMINATE)

    def test_p2_request_order_authority_agent_payee_amount_currency_mismatches_block(self) -> None:
        cases = {
            "request": replace(self.execution, request_id="request-other"),
            "transaction": replace(self.execution, transaction_object_ref="request-other"),
            "order": replace(self.execution, order_id="order-other"),
            "authority": replace(self.execution, authority_ref="authority-other"),
            "agent": replace(self.execution, agent_ref="agent-other"),
            "payee": replace(self.execution, payee="payee-other"),
            "amount": replace(self.execution, amount=self.execution.amount + Decimal("1.00")),
            "currency": replace(self.execution, currency="CNY"),
        }
        for name, execution in cases.items():
            with self.subTest(name=name):
                outcome, calls = self.invoke(execution_candidate=execution)
                self.assertEqual(Decision.DENY, outcome.decision)
                self.assertIsNotNone(outcome.runtime_gate_record)
                self.assertEqual(VerificationStatus.INVALID.value, outcome.runtime_gate_record.binding_status)
                self.assert_blocked(outcome, calls, Decision.DENY)

    def test_p3_missing_and_mismatched_executor_identity_block(self) -> None:
        missing_identity = AgentIdentity("", "", None, "")
        outcome, calls = self.invoke(
            agent_identity=missing_identity,
            current_provider_ref="provider-current",
            current_executor_instance_ref="executor-current",
        )
        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assertEqual(VerificationStatus.MISSING_EVIDENCE.value, outcome.runtime_gate_record.identity_status)
        self.assert_blocked(outcome, calls, Decision.INDETERMINATE)

        mismatch = replace(self.identity, executor_instance_id="executor-other")
        outcome, calls = self.invoke(agent_identity=mismatch)
        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertEqual(VerificationStatus.INVALID.value, outcome.runtime_gate_record.identity_status)
        self.assert_blocked(outcome, calls, Decision.DENY)

    def test_p4_missing_invalid_stale_and_value_mismatched_coverage_block(self) -> None:
        missing = evaluate_context_policy(
            {},
            required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
            current_action=PAYMENT_CONTEXT_ACTION,
        ).fact
        outcome, calls = self.invoke(context_policy_fact=missing)
        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assert_blocked(outcome, calls, Decision.INDETERMINATE)

        invalid = evaluate_context_policy(
            {},
            current_action=PAYMENT_CONTEXT_ACTION,
            observed_state_after={"request": {"amount": "999.00"}},
        ).fact
        outcome, calls = self.invoke(context_policy_fact=invalid)
        self.assertEqual(Decision.DENY, outcome.decision)
        self.assert_blocked(outcome, calls, Decision.DENY)

        stale = context_fact(
            self.mandate,
            self.adaptation.order,
            self.bound_request,
            current_action="refund_payment",
        )
        outcome, calls = self.invoke(context_policy_fact=stale)
        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assert_blocked(outcome, calls, Decision.INDETERMINATE)
        self.assertIsNotNone(outcome.runtime_gate_record)
        self.assertIn("p4:current_action_mismatch", outcome.reason_codes)
        self.assertEqual(
            outcome.runtime_gate_record.reason_codes,
            outcome.reason_codes,
        )

        mismatched = context_fact(
            self.mandate,
            self.adaptation.order,
            self.bound_request,
            state_overrides={"request": {"amount": Decimal("999.00")}},
        )
        self.assertEqual(VerificationStatus.VALID, mismatched.status)
        outcome, calls = self.invoke(context_policy_fact=mismatched)
        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assert_blocked(outcome, calls, Decision.INDETERMINATE)
        self.assertIsNotNone(outcome.runtime_gate_record)
        self.assertIn("p4:source_coverage_value_mismatch", outcome.reason_codes)
        self.assertEqual(
            outcome.runtime_gate_record.reason_codes,
            outcome.reason_codes,
        )

    def test_callback_exception_is_one_attempt_no_retry_and_no_false_success(self) -> None:
        calls: list[str] = []

        def failing_callback():
            calls.append("attempt")
            raise RuntimeError("offline checkout failed")

        outcome, _ = self.invoke(checkout_callback=failing_callback)

        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assertFalse(outcome.checkout_executed)
        self.assertEqual(1, outcome.callback_count)
        self.assertEqual(["attempt"], calls)
        self.assertIsNone(outcome.callback_result_ref)
        self.assertIn("checkout_callback_exception:RuntimeError", outcome.reason_codes)
        self.assertIsNotNone(outcome.runtime_gate_record)
        self.assertTrue(outcome.runtime_gate_record.callback_executed)
        self.assertEqual(1, outcome.runtime_gate_record.callback_count)
        self.assertEqual(Decision.INDETERMINATE, outcome.runtime_gate_record.final_decision)

    def test_same_inputs_are_deterministic_except_callback_observation(self) -> None:
        first, first_calls = self.invoke()
        second, second_calls = self.invoke()

        self.assertEqual(first, second)
        self.assertEqual(["checkout"], first_calls)
        self.assertEqual(["checkout"], second_calls)
        with self.assertRaises(FrozenInstanceError):
            first.callback_count = 2  # type: ignore[misc]

    def test_production_gate_has_no_file_network_process_environment_or_webshop_dependency(self) -> None:
        source = GATE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports: set[str] = set()
        called: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module or "")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called.add(node.func.attr)

        for forbidden in (
            "gym",
            "web_agent_site",
            "pyserini",
            "flask",
            "selenium",
            "playwright",
            "requests",
            "urllib",
            "socket",
            "subprocess",
            "os",
            "pathlib",
        ):
            self.assertFalse(any(name == forbidden or name.startswith(forbidden + ".") for name in imports), imports)
        self.assertTrue(called.isdisjoint({"open", "read_text", "write_text", "getenv", "run", "Popen", "urlopen", "socket"}), called)
        self.assertNotIn("click[buy now]", source.lower())
        self.assertNotIn("SimServer", source)

        with (
            patch.object(builtins, "open", side_effect=AssertionError("file forbidden")) as open_mock,
            patch.object(socket, "socket", side_effect=AssertionError("network forbidden")) as socket_mock,
            patch.object(subprocess, "run", side_effect=AssertionError("process forbidden")) as run_mock,
            patch.object(os, "getenv", side_effect=AssertionError("environment forbidden")) as getenv_mock,
            patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")) as urlopen_mock,
        ):
            outcome, calls = self.invoke()
        self.assertEqual(Decision.ALLOW, outcome.decision)
        self.assertEqual(["checkout"], calls)
        open_mock.assert_not_called()
        socket_mock.assert_not_called()
        run_mock.assert_not_called()
        getenv_mock.assert_not_called()
        urlopen_mock.assert_not_called()

    def test_public_api_is_exported_from_package_root(self) -> None:
        self.assertTrue(callable(gate_webshop_buy_now))
        self.assertTrue(hasattr(WebShopBuyNowGateOutcome, "__dataclass_fields__"))
        self.assertTrue(hasattr(GovernedPaymentAction, "__dataclass_fields__"))


if __name__ == "__main__":
    unittest.main()

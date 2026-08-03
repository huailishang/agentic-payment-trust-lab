from __future__ import annotations

import ast
import builtins
import importlib.util
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agentic_payment_experiment.models import (
    AgentIdentity,
    IntentMandate,
    Order,
    OrderItem,
    PaymentExecutionRecord,
    PaymentStatus,
    TransactionRequest,
)
from agentic_payment_experiment.payment_execution import (
    PAYMENT_CONTEXT_ACTION,
    PAYMENT_REQUIRED_SOURCE_PATHS,
)
from agentic_payment_experiment.trusted_execution import (
    ActionReversibility,
    GovernedActionBindingFact,
    GovernedActionType,
    GovernedPaymentAction,
    POLICY_VERSION,
    SideEffectClass,
    SourceType,
    VerificationStatus,
    evaluate_context_policy,
    verify_governed_payment_action,
)


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "src/agentic_payment_experiment/trusted_execution/governed_action.py"
MATRIX_PATH = ROOT / "samples/external/webshop/governed_payment_action_matrix_v1.json"
MATRIX_RUNNER_PATH = ROOT / "scripts/validation/webshop/run_governed_payment_action_matrix.py"


def _load_matrix_runner():
    spec = importlib.util.spec_from_file_location(
        "governed_payment_action_matrix_runner",
        MATRIX_RUNNER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _primitive_only(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_primitive_only(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _primitive_only(item) for key, item in value.items())
    return False


class GovernedActionTest(unittest.TestCase):
    def setUp(self) -> None:
        from datetime import datetime, timezone

        request_time = datetime(2026, 8, 3, 1, 0, 0, tzinfo=timezone.utc)
        self.agent_id = "agent-1"
        self.executor_id = "executor-1"
        self.mandate = IntentMandate(
            mandate_id="mandate-1",
            user_id="user-1",
            max_amount=Decimal("100.00"),
            allowed_merchants=frozenset({"merchant-1"}),
            allowed_categories=frozenset({"office"}),
            expires_at=request_time + timedelta(hours=1),
            expected_agent_id=self.agent_id,
            currency="USD",
            authority_version="authority-v1",
        )
        item = OrderItem(
            item_id="item-1",
            name="Desk lamp",
            category="office",
            quantity=1,
            unit_amount=Decimal("25.00"),
        )
        self.order = Order(
            order_id="order-1",
            order_version="order-v1",
            merchant="merchant-1",
            payee="payee-1",
            items=(item,),
            total_amount=Decimal("25.00"),
            currency="USD",
            quote_expires_at=request_time + timedelta(minutes=30),
            fulfilment_terms="standard",
            mandate_ref=self.mandate.mandate_id,
            authority_version_ref=self.mandate.authority_version,
        )
        self.request = TransactionRequest(
            request_id="request-1",
            amount=self.order.total_amount,
            merchant=self.order.merchant,
            category=item.category,
            occurred_at=request_time,
            agent_id=self.agent_id,
            currency=self.order.currency,
            order_ref=self.order.order_id,
            authority_ref=self.mandate.mandate_id,
            authority_version_ref=self.mandate.authority_version,
            payee=self.order.payee,
        )
        self.execution = PaymentExecutionRecord(
            payment_id="payment-1",
            request_id=self.request.request_id,
            order_id=self.order.order_id,
            status=PaymentStatus.PENDING,
            amount=self.request.amount,
            currency=self.request.currency,
            occurred_at=request_time + timedelta(seconds=2),
            authority_ref=self.mandate.mandate_id,
            agent_ref=self.agent_id,
            transaction_object_ref=self.request.request_id,
            payee=self.order.payee,
        )
        self.identity = AgentIdentity(
            agent_id=self.agent_id,
            provider="provider-1",
            executor_instance_id=self.executor_id,
            status="active",
        )
        state = {
            "mandate": {"mandate_id": self.mandate.mandate_id},
            "final_order": {"order_id": self.order.order_id},
            "request": {
                "request_id": self.request.request_id,
                "agent_id": self.request.agent_id,
                "amount": self.request.amount,
                "payee": self.request.payee,
                "currency": self.request.currency,
            },
        }
        sources = {
            "mandate.mandate_id": SourceType.USER_CONFIRMED,
            "final_order.order_id": SourceType.USER_CONFIRMED,
            "request.request_id": SourceType.PROTOCOL_VERIFIED,
            "request.agent_id": SourceType.USER_CONFIRMED,
            "request.amount": SourceType.USER_CONFIRMED,
            "request.payee": SourceType.USER_CONFIRMED,
            "request.currency": SourceType.USER_CONFIRMED,
        }
        self.context = evaluate_context_policy(
            state,
            trusted_sources=sources,
            required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
            current_action=PAYMENT_CONTEXT_ACTION,
            policy_version=POLICY_VERSION,
        ).fact
        self.action = GovernedPaymentAction(
            action_id="action-1",
            action_type=GovernedActionType.EXECUTE_PAYMENT,
            subject_ref=self.mandate.user_id,
            agent_ref=self.agent_id,
            executor_ref=self.executor_id,
            authority_ref=self.mandate.mandate_id,
            authority_version=self.mandate.authority_version,
            order_ref=self.order.order_id,
            order_version=self.order.order_version,
            request_ref=self.request.request_id,
            payment_ref=self.execution.payment_id,
            source_refs=("source:user-confirmation-1", "source:checkout-1"),
            side_effect_class=SideEffectClass.PAYMENT_EXECUTION,
            reversibility=ActionReversibility.COMPENSATABLE_NOT_REVERSIBLE,
            occurred_at=request_time + timedelta(seconds=1),
        )

    def verify(self, action=None, **overrides):
        values = {
            "mandate": self.mandate,
            "order": self.order,
            "request": self.request,
            "execution": self.execution,
            "agent_identity": self.identity,
            "current_executor_instance_ref": self.executor_id,
            "context_policy_fact": self.context,
        }
        values.update(overrides)
        return verify_governed_payment_action(
            self.action if action is None else action,
            **values,
        )

    def test_valid_action_is_immutable_and_serializes_to_primitives(self) -> None:
        fact = self.verify()
        self.assertEqual(VerificationStatus.VALID, fact.status)
        self.assertEqual(("governed_action_binding_valid",), fact.reason_codes)
        self.assertEqual("execute_payment", fact.checked_action_type)
        action_dict = self.action.to_dict()
        fact_dict = fact.to_dict()
        self.assertTrue(_primitive_only(action_dict))
        self.assertTrue(_primitive_only(fact_dict))
        self.assertIsInstance(action_dict["source_refs"], list)
        self.assertEqual(self.action.occurred_at.isoformat(), action_dict["occurred_at"])
        json.dumps(action_dict, sort_keys=True)
        json.dumps(fact_dict, sort_keys=True)
        with self.assertRaises(FrozenInstanceError):
            self.action.action_id = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            fact.status = VerificationStatus.INVALID  # type: ignore[misc]

    def test_public_types_are_closed_to_execute_payment_only(self) -> None:
        self.assertEqual([GovernedActionType.EXECUTE_PAYMENT], list(GovernedActionType))
        self.assertEqual([SideEffectClass.PAYMENT_EXECUTION], list(SideEffectClass))
        self.assertEqual(
            [ActionReversibility.COMPENSATABLE_NOT_REVERSIBLE],
            list(ActionReversibility),
        )
        self.assertTrue(hasattr(GovernedActionBindingFact, "__dataclass_fields__"))

    def test_only_exact_governed_payment_action_type_crosses_outer_boundary(self) -> None:
        class ActionSubclass(GovernedPaymentAction):
            pass

        class ExplodingProxy:
            def __getattribute__(self, name):
                raise AssertionError(f"invalid object attribute read: {name}")

        invalid_objects = (
            SimpleNamespace(**self.action.__dict__),
            self.action.to_dict(),
            [self.action],
            "execute_payment",
            ActionSubclass(**self.action.__dict__),
            ExplodingProxy(),
        )
        for invalid_action in invalid_objects:
            with self.subTest(object_type=type(invalid_action).__name__):
                fact = self.verify(invalid_action)
                self.assertEqual(VerificationStatus.INVALID, fact.status)
                self.assertIsNone(fact.action_id)
                self.assertEqual(
                    ("governed_action_invalid_type",),
                    fact.reason_codes,
                )
                self.assertIsNone(fact.checked_action_type)
                self.assertIsNone(fact.checked_order_ref)
                self.assertIsNone(fact.checked_request_ref)
                self.assertIsNone(fact.checked_payment_ref)

        exact = self.verify(self.action)
        self.assertEqual(VerificationStatus.VALID, exact.status)

    def test_missing_action_and_missing_mandatory_fields_are_missing_evidence(self) -> None:
        missing_action = verify_governed_payment_action(
            None,
            mandate=self.mandate,
            order=self.order,
            request=self.request,
            execution=self.execution,
            agent_identity=self.identity,
            current_executor_instance_ref=self.executor_id,
            context_policy_fact=self.context,
        )
        self.assertEqual(VerificationStatus.MISSING_EVIDENCE, missing_action.status)
        self.assertEqual(("governed_action_missing",), missing_action.reason_codes)

        cases = (
            (replace(self.action, action_id=""), "action_id_missing"),
            (replace(self.action, source_refs=()), "source_refs_missing"),
            (replace(self.action, occurred_at=None), "action_occurred_at_missing"),  # type: ignore[arg-type]
        )
        for action, reason in cases:
            with self.subTest(reason=reason):
                fact = self.verify(action)
                self.assertEqual(VerificationStatus.MISSING_EVIDENCE, fact.status)
                self.assertIn(reason, fact.reason_codes)

    def test_invalid_enum_and_container_types_are_not_coerced(self) -> None:
        cases = (
            (replace(self.action, action_type="execute_payment"), "action_type_invalid"),  # type: ignore[arg-type]
            (replace(self.action, side_effect_class="PAYMENT_EXECUTION"), "side_effect_class_invalid"),  # type: ignore[arg-type]
            (replace(self.action, reversibility="COMPENSATABLE_NOT_REVERSIBLE"), "reversibility_invalid"),  # type: ignore[arg-type]
            (replace(self.action, source_refs=["source-1"]), "source_refs_invalid_type"),  # type: ignore[arg-type]
            (replace(self.action, source_refs=("",)), "source_refs_blank"),
        )
        for action, reason in cases:
            with self.subTest(reason=reason):
                fact = self.verify(action)
                self.assertEqual(VerificationStatus.INVALID, fact.status)
                self.assertIn(reason, fact.reason_codes)

    def test_subject_authority_and_version_mismatches_are_independent(self) -> None:
        cases = (
            (replace(self.action, subject_ref="other-user"), "subject_ref_mismatch"),
            (replace(self.action, authority_ref="other-authority"), "authority_ref_mismatch"),
            (replace(self.action, authority_version="other-version"), "authority_version_mismatch"),
        )
        for action, reason in cases:
            with self.subTest(reason=reason):
                fact = self.verify(action)
                self.assertEqual(VerificationStatus.INVALID, fact.status)
                self.assertEqual((reason,), fact.reason_codes)

    def test_order_request_payment_and_existing_chain_mismatches_are_independent(self) -> None:
        cases = (
            (replace(self.action, order_ref="other-order"), {}, "order_ref_mismatch"),
            (replace(self.action, order_version="other-version"), {}, "order_version_mismatch"),
            (replace(self.action, request_ref="other-request"), {}, "request_ref_mismatch"),
            (replace(self.action, payment_ref="other-payment"), {}, "payment_ref_mismatch"),
            (
                self.action,
                {"execution": replace(self.execution, request_id="other-request")},
                "execution_request_chain_mismatch",
            ),
            (
                self.action,
                {"execution": replace(self.execution, order_id="other-order")},
                "execution_order_chain_mismatch",
            ),
        )
        for action, overrides, reason in cases:
            with self.subTest(reason=reason):
                fact = self.verify(action, **overrides)
                self.assertEqual(VerificationStatus.INVALID, fact.status)
                self.assertIn(reason, fact.reason_codes)

    def test_agent_executor_and_context_action_bindings(self) -> None:
        cases = (
            (replace(self.action, agent_ref="other-agent"), {}, "agent_ref_request_mismatch"),
            (replace(self.action, executor_ref="other-executor"), {}, "executor_ref_current_mismatch"),
            (
                self.action,
                {"current_executor_instance_ref": "other-executor"},
                "executor_ref_current_mismatch",
            ),
            (
                self.action,
                {"agent_identity": replace(self.identity, agent_id="other-agent")},
                "agent_ref_identity_mismatch",
            ),
            (
                self.action,
                {"agent_identity": replace(self.identity, executor_instance_id="other-executor")},
                "executor_ref_identity_mismatch",
            ),
            (
                self.action,
                {"context_policy_fact": replace(self.context, current_action="refund_payment")},
                "context_action_mismatch",
            ),
        )
        for action, overrides, reason in cases:
            with self.subTest(reason=reason):
                fact = self.verify(action, **overrides)
                self.assertEqual(VerificationStatus.INVALID, fact.status)
                self.assertIn(reason, fact.reason_codes)

    def test_missing_agent_executor_and_context_evidence_is_missing(self) -> None:
        cases = (
            ({"request": replace(self.request, agent_id=None)}, "request_agent_id_missing"),
            ({"agent_identity": replace(self.identity, agent_id="")}, "identity_agent_id_missing"),
            ({"agent_identity": replace(self.identity, executor_instance_id=None)}, "identity_executor_instance_ref_missing"),
            ({"current_executor_instance_ref": None}, "current_executor_instance_ref_missing"),
            ({"context_policy_fact": replace(self.context, current_action=None)}, "context_current_action_missing"),
        )
        for overrides, reason in cases:
            with self.subTest(reason=reason):
                fact = self.verify(**overrides)
                self.assertEqual(VerificationStatus.MISSING_EVIDENCE, fact.status)
                self.assertIn(reason, fact.reason_codes)

    def test_temporal_boundaries_and_identifier_collisions(self) -> None:
        cases = (
            (
                replace(self.action, occurred_at=self.request.occurred_at - timedelta(microseconds=1)),
                "action_before_request",
            ),
            (
                replace(self.action, occurred_at=self.execution.occurred_at + timedelta(microseconds=1)),
                "action_after_execution",
            ),
            (replace(self.action, action_id=self.order.order_id), "action_id_order_ref_collision"),
            (replace(self.action, action_id=self.request.request_id), "action_id_request_ref_collision"),
            (replace(self.action, action_id=self.execution.payment_id), "action_id_payment_ref_collision"),
        )
        for action, reason in cases:
            with self.subTest(reason=reason):
                fact = self.verify(action)
                self.assertEqual(VerificationStatus.INVALID, fact.status)
                self.assertEqual((reason,), fact.reason_codes)

        for occurred_at in (self.request.occurred_at, self.execution.occurred_at):
            with self.subTest(boundary=occurred_at.isoformat()):
                fact = self.verify(replace(self.action, occurred_at=occurred_at))
                self.assertEqual(VerificationStatus.VALID, fact.status)

    def test_machine_readable_action_matrix_matches_and_exposes_required_fields(self) -> None:
        runner = _load_matrix_runner()
        result = runner.build_action_matrix(MATRIX_PATH)

        self.assertEqual(18, result["summary"]["total"])
        self.assertEqual(18, result["summary"]["matched"])
        self.assertEqual(0, result["summary"]["failed"])
        self.assertIn("no_real_buy_now", result["limitations"])
        self.assertIn("no_real_payment", result["limitations"])
        self.assertTrue(_primitive_only(result["primitive_serialization_example"]))
        by_id = {item["case_id"]: item for item in result["cases"]}
        self.assertEqual("VALID", by_id["valid_execute_payment"]["actual_verification_status"])
        self.assertEqual("ALLOW", by_id["valid_execute_payment"]["actual_gate_decision"])
        self.assertEqual(1, by_id["valid_execute_payment"]["callback_count"])
        for case_id in (
            "mutable_lookalike_action_object",
            "serialized_dict_action_object",
        ):
            self.assertEqual("INVALID", by_id[case_id]["actual_verification_status"])
            self.assertEqual("DENY", by_id[case_id]["actual_gate_decision"])
            self.assertEqual(0, by_id[case_id]["callback_count"])
            self.assertEqual(
                ["governed_action_invalid_type"],
                by_id[case_id]["reason_codes"],
            )
        for case_id, item in by_id.items():
            for field in (
                "expected_verification_status",
                "actual_verification_status",
                "expected_gate_decision",
                "actual_gate_decision",
                "callback_count",
                "reason_codes",
                "references",
                "limitations",
            ):
                self.assertIn(field, item, (case_id, field))
            self.assertTrue(item["limitations"]["no_real_buy_now"])
            self.assertTrue(item["limitations"]["no_real_payment"])
            for ref in ("action_ref", "order_ref", "request_ref", "payment_ref"):
                self.assertIn(ref, item["references"], (case_id, ref))
            if case_id != "valid_execute_payment":
                self.assertEqual(0, item["callback_count"], case_id)
                self.assertEqual(0, item["callback_observations"], case_id)

    def test_verifier_is_deterministic_and_does_not_modify_inputs(self) -> None:
        before = (
            self.action,
            self.mandate,
            self.order,
            self.request,
            self.execution,
            self.identity,
            self.context,
        )
        first = self.verify()
        second = self.verify()
        self.assertEqual(first, second)
        self.assertEqual(
            before,
            (
                self.action,
                self.mandate,
                self.order,
                self.request,
                self.execution,
                self.identity,
                self.context,
            ),
        )

    def test_production_verifier_has_no_external_or_callback_side_effect(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports: set[str] = set()
        calls: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module or "")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
        for forbidden in (
            "requests",
            "urllib",
            "socket",
            "subprocess",
            "os",
            "pathlib",
            "flask",
            "selenium",
            "playwright",
            "web_agent_site",
        ):
            self.assertFalse(
                any(name == forbidden or name.startswith(forbidden + ".") for name in imports),
                imports,
            )
        self.assertTrue(
            calls.isdisjoint(
                {
                    "open",
                    "read_text",
                    "write_text",
                    "getenv",
                    "run",
                    "Popen",
                    "urlopen",
                    "socket",
                    "checkout_callback",
                    "execute_payment",
                }
            ),
            calls,
        )
        with (
            patch.object(builtins, "open", side_effect=AssertionError("file forbidden")) as open_mock,
            patch.object(socket, "socket", side_effect=AssertionError("network forbidden")) as socket_mock,
            patch.object(subprocess, "run", side_effect=AssertionError("process forbidden")) as run_mock,
            patch.object(os, "getenv", side_effect=AssertionError("environment forbidden")) as getenv_mock,
            patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")) as urlopen_mock,
        ):
            fact = self.verify()
        self.assertEqual(VerificationStatus.VALID, fact.status)
        open_mock.assert_not_called()
        socket_mock.assert_not_called()
        run_mock.assert_not_called()
        getenv_mock.assert_not_called()
        urlopen_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()

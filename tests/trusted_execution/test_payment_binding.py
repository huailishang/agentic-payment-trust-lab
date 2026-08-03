import sys
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agentic_payment_experiment.models import (
    AgentIdentity,
    Decision,
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
    execute_with_payment_binding_gate,
    observe_payment_execution_gate,
)
from agentic_payment_experiment.trusted_execution import (
    POLICY_VERSION,
    CandidateFactUpdate,
    FactDomain,
    IdentityAssuranceLevel,
    SourceType,
    ReplayEvent,
    ReplayEventType,
    ReplaySourceType,
    ReplayStatus,
    RuntimeGateRecord,
    VerificationStatus,
    evaluate_context_policy,
    replay_events,
    verify_payment_execution_binding,
)


class PaymentExecutionBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 7, 11, 12, 0, tzinfo=timezone.utc)
        self.mandate = IntentMandate(
            mandate_id="mandate-1",
            user_id="user-1",
            max_amount=Decimal("500.00"),
            allowed_merchants=frozenset({"merchant-1"}),
            allowed_categories=frozenset({"shoes"}),
            expires_at=self.now + timedelta(hours=1),
            expected_agent_id="agent-1",
            authority_version="v1",
        )
        self.order = Order(
            order_id="order-1",
            order_version="v1",
            merchant="merchant-1",
            payee="payee-1",
            items=(
                OrderItem(
                    item_id="item-1",
                    name="Running Shoe",
                    category="shoes",
                    quantity=1,
                    unit_amount=Decimal("480.00"),
                ),
            ),
            total_amount=Decimal("480.00"),
            currency="CNY",
            quote_expires_at=self.now + timedelta(minutes=30),
            fulfilment_terms="standard delivery",
            mandate_ref="mandate-1",
            authority_version_ref="v1",
        )
        self.request = TransactionRequest(
            request_id="request-1",
            amount=Decimal("480.00"),
            merchant="merchant-1",
            category="shoes",
            occurred_at=self.now,
            agent_id="agent-1",
            currency="CNY",
            order_ref="order-1",
            authority_ref="mandate-1",
            authority_version_ref="v1",
            payee="payee-1",
        )
        self.payment = PaymentExecutionRecord(
            payment_id="payment-1",
            request_id="request-1",
            order_id="order-1",
            status=PaymentStatus.PENDING,
            amount=Decimal("480.00"),
            currency="CNY",
            occurred_at=self.now + timedelta(seconds=1),
            authority_ref="mandate-1",
            agent_ref="agent-1",
            transaction_object_ref="request-1",
            payee="payee-1",
        )
        self.identity = AgentIdentity(
            agent_id="agent-1",
            provider="offline-provider-1",
            executor_instance_id="executor-1",
            status="active",
        )

    def verify(self, *, mandate=None, order=None, request=None, payment=None):
        return verify_payment_execution_binding(
            mandate if mandate is not None else self.mandate,
            order if order is not None else self.order,
            request if request is not None else self.request,
            payment if payment is not None else self.payment,
        )

    def execute(
        self,
        *,
        decision=Decision.ALLOW,
        mandate=None,
        order=None,
        request=None,
        payment=None,
        identity=None,
        provider_ref="offline-provider-1",
        executor_ref="executor-1",
        credential_ref=None,
        context_policy_fact=None,
    ):
        calls: list[str] = []
        if context_policy_fact is None:
            context_policy_fact = evaluate_context_policy(
                {
                    "mandate": {"mandate_id": self.mandate.mandate_id},
                    "final_order": {"order_id": self.order.order_id},
                    "request": {
                        "request_id": self.request.request_id,
                        "agent_id": self.request.agent_id,
                        "amount": self.request.amount,
                        "payee": self.request.payee,
                        "currency": self.request.currency,
                    },
                },
                trusted_sources={
                    "mandate.mandate_id": SourceType.USER_CONFIRMED,
                    "final_order.order_id": SourceType.USER_CONFIRMED,
                    "request.request_id": SourceType.PROTOCOL_VERIFIED,
                    "request.agent_id": SourceType.USER_CONFIRMED,
                    "request.amount": SourceType.USER_CONFIRMED,
                    "request.payee": SourceType.USER_CONFIRMED,
                    "request.currency": SourceType.USER_CONFIRMED,
                },
                required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
                current_action=PAYMENT_CONTEXT_ACTION,
                policy_version=POLICY_VERSION,
            ).fact
        outcome = execute_with_payment_binding_gate(
            decision,
            mandate if mandate is not None else self.mandate,
            order if order is not None else self.order,
            request if request is not None else self.request,
            payment if payment is not None else self.payment,
            lambda: calls.append("paid") or "provider-payment-1",
            agent_identity=self.identity if identity is None else identity,
            current_provider_ref=provider_ref,
            current_executor_instance_ref=executor_ref,
            current_credential_ref=credential_ref,
            context_policy_fact=context_policy_fact,
        )
        return outcome, calls

    def replay_gate_outcome(self, outcome) -> object:
        gate = RuntimeGateRecord(
            preliminary_decision=Decision.ALLOW,
            final_decision=outcome.decision,
            binding_status=outcome.binding_fact.status.value,
            binding_reason_codes=outcome.binding_fact.reason_codes,
            identity_status=outcome.identity_fact.status.value,
            identity_reason_codes=outcome.identity_fact.reason_codes,
            context_policy_status=outcome.context_policy_fact.status.value,
            context_policy_reason_codes=outcome.context_policy_fact.reason_codes,
            callback_executed=outcome.executed,
            callback_count=1 if outcome.executed else 0,
            callback_result_ref="provider-payment-1" if outcome.executed else None,
            reason_codes=("gate_outcome_recorded",),
        )
        event_types = (
            ReplayEventType.AUTHORITY_RECORDED,
            ReplayEventType.ORDER_RECORDED,
            ReplayEventType.REQUEST_RECORDED,
            ReplayEventType.RUNTIME_DECISION_RECORDED,
            ReplayEventType.PAYMENT_OUTCOME_RECORDED,
        )
        events = []
        for index, event_type in enumerate(event_types):
            events.append(
                ReplayEvent(
                    event_id=f"gate-{index}",
                    event_type=event_type,
                    occurred_at=self.now,
                    subject_ref=self.mandate.user_id,
                    agent_ref=self.request.agent_id or "agent-missing",
                    authority_ref=self.mandate.mandate_id,
                    transaction_object_ref=self.request.request_id,
                    payment_ref=self.payment.payment_id,
                    source_type=ReplaySourceType.SYSTEM_RUNTIME,
                    source_ref=f"gate-fixture:{index}",
                    decision=outcome.decision,
                    reason_codes=("gate_outcome_recorded",),
                    previous_event_ref=events[-1].event_id if events else None,
                    runtime_gate=gate if event_type is ReplayEventType.RUNTIME_DECISION_RECORDED else None,
                )
            )
        return replay_events(events)

    def test_valid_continuous_binding_is_the_only_path_that_executes(self) -> None:
        fact = self.verify()
        outcome, calls = self.execute()

        self.assertEqual(VerificationStatus.VALID, fact.status)
        self.assertEqual(("payment_execution_binding_match",), fact.reason_codes)
        self.assertEqual(Decision.ALLOW, outcome.decision)
        self.assertEqual(VerificationStatus.VALID, outcome.identity_fact.status)
        self.assertEqual(
            IdentityAssuranceLevel.BOUND,
            outcome.identity_fact.assurance_level,
        )
        self.assertTrue(outcome.executed)
        self.assertEqual("provider-payment-1", outcome.execution_result)
        self.assertEqual(["paid"], calls)

    def test_observation_is_captured_once_at_gate_without_replay_callback(self) -> None:
        callback_calls: list[str] = []
        context = evaluate_context_policy(
            {
                "mandate": {"mandate_id": self.mandate.mandate_id},
                "final_order": {"order_id": self.order.order_id},
                "request": {
                    "request_id": self.request.request_id,
                    "agent_id": self.request.agent_id,
                    "amount": self.request.amount,
                    "payee": self.request.payee,
                    "currency": self.request.currency,
                },
            },
            trusted_sources={
                "mandate.mandate_id": SourceType.USER_CONFIRMED,
                "final_order.order_id": SourceType.USER_CONFIRMED,
                "request.request_id": SourceType.PROTOCOL_VERIFIED,
                "request.agent_id": SourceType.USER_CONFIRMED,
                "request.amount": SourceType.USER_CONFIRMED,
                "request.payee": SourceType.USER_CONFIRMED,
                "request.currency": SourceType.USER_CONFIRMED,
            },
            required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
            current_action=PAYMENT_CONTEXT_ACTION,
        ).fact
        observed = observe_payment_execution_gate(
            Decision.ALLOW,
            self.mandate,
            self.order,
            self.request,
            self.payment,
            lambda: callback_calls.append("paid") or "provider-payment-1",
            agent_identity=self.identity,
            current_provider_ref="offline-provider-1",
            current_executor_instance_ref="executor-1",
            context_policy_fact=context,
        )
        self.assertEqual(["paid"], callback_calls)
        self.assertTrue(observed.callback_executed)
        self.assertEqual(1, observed.callback_count)
        self.assertEqual("provider-payment-1", observed.callback_result_ref)
        self.assertEqual(Decision.ALLOW, observed.final_decision)
        self.assertEqual(VerificationStatus.VALID.value, observed.binding_status)
        self.assertEqual(VerificationStatus.VALID.value, observed.identity_status)
        self.assertEqual(VerificationStatus.VALID.value, observed.context_policy_status)

    def test_shared_runtime_gate_emits_causal_reason_for_every_branch(self) -> None:
        allowed_outcome, allowed_calls = self.execute()
        self.assertEqual(["paid"], allowed_calls)
        valid_context = allowed_outcome.context_policy_fact
        valid_identity = allowed_outcome.identity_fact

        def observe(
            *,
            decision=Decision.ALLOW,
            payment=None,
            identity=None,
            provider_ref="offline-provider-1",
            executor_ref="executor-1",
            context_policy_fact=valid_context,
        ):
            calls: list[str] = []
            record = observe_payment_execution_gate(
                decision,
                self.mandate,
                self.order,
                self.request,
                self.payment if payment is None else payment,
                lambda: calls.append("paid") or "provider-payment-1",
                agent_identity=self.identity if identity is None else identity,
                current_provider_ref=provider_ref,
                current_executor_instance_ref=executor_ref,
                context_policy_fact=context_policy_fact,
            )
            return record, calls

        cases = (
            (
                "upstream",
                {"decision": Decision.DENY},
                Decision.DENY,
                "p1:upstream_prepayment_non_allow",
            ),
            (
                "p2_missing",
                {"payment": replace(self.payment, request_id="")},
                Decision.INDETERMINATE,
                "p2:binding_missing",
            ),
            (
                "p2_invalid",
                {"payment": replace(self.payment, request_id="request-other")},
                Decision.DENY,
                "p2:binding_invalid",
            ),
            (
                "p3_missing",
                {
                    "identity": AgentIdentity("", "", None, ""),
                    "provider_ref": "provider-current",
                    "executor_ref": "executor-current",
                },
                Decision.INDETERMINATE,
                "p3:identity_missing",
            ),
            (
                "p3_invalid",
                {"identity": replace(self.identity, executor_instance_id="executor-other")},
                Decision.DENY,
                "p3:identity_invalid",
            ),
            (
                "p4_missing",
                {
                    "context_policy_fact": replace(
                        valid_context,
                        status=VerificationStatus.MISSING_EVIDENCE,
                        reason_codes=("synthetic_context_missing",),
                    )
                },
                Decision.INDETERMINATE,
                "p4:context_missing",
            ),
            (
                "p4_invalid",
                {
                    "context_policy_fact": replace(
                        valid_context,
                        status=VerificationStatus.INVALID,
                        reason_codes=("synthetic_context_invalid",),
                    )
                },
                Decision.DENY,
                "p4:context_invalid",
            ),
            (
                "p4_policy_version",
                {"context_policy_fact": replace(valid_context, policy_version="unsupported")},
                Decision.INDETERMINATE,
                "p4:policy_version_mismatch",
            ),
            (
                "p4_current_action",
                {"context_policy_fact": replace(valid_context, current_action="refund_payment")},
                Decision.INDETERMINATE,
                "p4:current_action_mismatch",
            ),
            (
                "p4_required_paths",
                {"context_policy_fact": replace(valid_context, required_source_paths=("request.amount",))},
                Decision.INDETERMINATE,
                "p4:required_source_paths_mismatch",
            ),
            (
                "p4_covered_paths",
                {"context_policy_fact": replace(valid_context, covered_source_paths=("request.amount",))},
                Decision.INDETERMINATE,
                "p4:covered_source_paths_mismatch",
            ),
            (
                "p4_missing_paths",
                {"context_policy_fact": replace(valid_context, missing_source_paths=("request.amount",))},
                Decision.INDETERMINATE,
                "p4:missing_source_paths",
            ),
            (
                "p4_source_coverage",
                {"context_policy_fact": replace(valid_context, source_coverage=())},
                Decision.INDETERMINATE,
                "p4:source_coverage_value_mismatch",
            ),
            (
                "allow",
                {},
                Decision.ALLOW,
                "runtime:allow",
            ),
        )
        for name, kwargs, expected_decision, expected_reason in cases:
            with self.subTest(name=name):
                record, calls = observe(**kwargs)
                self.assertEqual(expected_decision, record.final_decision)
                self.assertIn(expected_reason, record.reason_codes)
                self.assertEqual(1 if expected_decision is Decision.ALLOW else 0, record.callback_count)
                self.assertEqual(["paid"] if expected_decision is Decision.ALLOW else [], calls)

        weak_identity = replace(
            valid_identity,
            assurance_level=IdentityAssuranceLevel.DECLARED,
        )
        with patch(
            "agentic_payment_experiment.payment_execution.verify_agent_executor_identity",
            return_value=weak_identity,
        ):
            record, calls = observe()
        self.assertEqual(Decision.INDETERMINATE, record.final_decision)
        self.assertIn("p3:assurance_insufficient", record.reason_codes)
        self.assertEqual(0, record.callback_count)
        self.assertEqual([], calls)

    def test_p4_missing_invalid_and_safely_blocked_paths_gate_callback(self) -> None:
        missing = evaluate_context_policy(
            {},
            required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
            current_action=None,
            policy_version=POLICY_VERSION,
        ).fact
        outcome, calls = self.execute(context_policy_fact=missing)
        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assertEqual([], calls)

        invalid = evaluate_context_policy(
            {},
            current_action=PAYMENT_CONTEXT_ACTION,
            observed_state_after={"request": {"amount": "699.00"}},
        ).fact
        outcome, calls = self.execute(context_policy_fact=invalid)
        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertEqual([], calls)

        blocked = evaluate_context_policy(
            {
                "mandate": {"mandate_id": self.mandate.mandate_id},
                "final_order": {"order_id": self.order.order_id},
                "request": {
                    "request_id": self.request.request_id,
                    "agent_id": self.request.agent_id,
                    "amount": self.request.amount,
                    "payee": self.request.payee,
                    "currency": self.request.currency,
                },
            },
            (
                CandidateFactUpdate(
                    SourceType.WEB_UNTRUSTED,
                    FactDomain.PAYMENT_REQUEST,
                    "request.amount",
                    "699.00",
                    source_ref="offline-web",
                ),
            ),
            trusted_sources={
                "mandate.mandate_id": SourceType.USER_CONFIRMED,
                "final_order.order_id": SourceType.USER_CONFIRMED,
                "request.request_id": SourceType.PROTOCOL_VERIFIED,
                "request.agent_id": SourceType.USER_CONFIRMED,
                "request.amount": SourceType.USER_CONFIRMED,
                "request.payee": SourceType.USER_CONFIRMED,
                "request.currency": SourceType.USER_CONFIRMED,
            },
            required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
            current_action=PAYMENT_CONTEXT_ACTION,
        ).fact
        outcome, calls = self.execute(context_policy_fact=blocked)
        self.assertEqual(Decision.ALLOW, outcome.decision)
        self.assertEqual(["paid"], calls)

    def test_p4_gate_rejects_empty_partial_action_and_policy_mismatch(self) -> None:
        base_state = {
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
        full_sources = {
            "mandate.mandate_id": SourceType.USER_CONFIRMED,
            "final_order.order_id": SourceType.USER_CONFIRMED,
            "request.request_id": SourceType.PROTOCOL_VERIFIED,
            "request.agent_id": SourceType.USER_CONFIRMED,
            "request.amount": SourceType.USER_CONFIRMED,
            "request.payee": SourceType.USER_CONFIRMED,
            "request.currency": SourceType.USER_CONFIRMED,
        }
        cases = (
            (
                "empty",
                evaluate_context_policy(
                    {},
                    trusted_sources={},
                    required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
                    current_action=PAYMENT_CONTEXT_ACTION,
                ).fact,
            ),
            (
                "partial",
                evaluate_context_policy(
                    base_state,
                    trusted_sources={
                        "mandate.mandate_id": SourceType.USER_CONFIRMED
                    },
                    required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
                    current_action=PAYMENT_CONTEXT_ACTION,
                ).fact,
            ),
            (
                "wrong_action",
                evaluate_context_policy(
                    base_state,
                    trusted_sources=full_sources,
                    required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
                    current_action="refund_payment",
                ).fact,
            ),
            (
                "wrong_policy",
                evaluate_context_policy(
                    base_state,
                    trusted_sources=full_sources,
                    required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
                    current_action=PAYMENT_CONTEXT_ACTION,
                    policy_version="unsupported-policy",
                ).fact,
            ),
        )
        for name, fact in cases:
            with self.subTest(name=name):
                outcome, calls = self.execute(context_policy_fact=fact)
                self.assertEqual(Decision.INDETERMINATE, outcome.decision)
                self.assertFalse(outcome.executed)
                self.assertEqual([], calls)

    def test_p4_gate_rejects_complete_coverage_bound_to_another_payment(self) -> None:
        fact = evaluate_context_policy(
            {
                "mandate": {"mandate_id": "mandate-other"},
                "final_order": {"order_id": "order-other"},
                "request": {
                    "request_id": "request-other",
                    "agent_id": "agent-other",
                    "amount": "490.00",
                    "payee": "payee-other",
                    "currency": "USD",
                },
            },
            trusted_sources={
                "mandate.mandate_id": SourceType.USER_CONFIRMED,
                "final_order.order_id": SourceType.USER_CONFIRMED,
                "request.request_id": SourceType.PROTOCOL_VERIFIED,
                "request.agent_id": SourceType.USER_CONFIRMED,
                "request.amount": SourceType.USER_CONFIRMED,
                "request.payee": SourceType.USER_CONFIRMED,
                "request.currency": SourceType.USER_CONFIRMED,
            },
            required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
            current_action=PAYMENT_CONTEXT_ACTION,
        ).fact
        self.assertEqual(VerificationStatus.VALID, fact.status)

        outcome, calls = self.execute(context_policy_fact=fact)
        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)

    def test_p4_gate_requires_each_payment_value_source_and_current_digest(self) -> None:
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
        for missing_path in ("request.amount", "request.payee", "request.currency"):
            with self.subTest(missing_path=missing_path):
                incomplete = {key: value for key, value in sources.items() if key != missing_path}
                fact = evaluate_context_policy(
                    state,
                    trusted_sources=incomplete,
                    required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
                    current_action=PAYMENT_CONTEXT_ACTION,
                ).fact
                outcome, calls = self.execute(context_policy_fact=fact)
                self.assertEqual(Decision.INDETERMINATE, outcome.decision)
                self.assertEqual([], calls)

        invalid_sources = dict(sources)
        invalid_sources["request.amount"] = SourceType.WEB_UNTRUSTED
        fact = evaluate_context_policy(
            state,
            trusted_sources=invalid_sources,
            required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
            current_action=PAYMENT_CONTEXT_ACTION,
        ).fact
        outcome, calls = self.execute(context_policy_fact=fact)
        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assertEqual([], calls)

        tampered = {**state, "request": {**state["request"], "amount": "490.00"}}
        fact = evaluate_context_policy(
            tampered,
            trusted_sources=sources,
            required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
            current_action=PAYMENT_CONTEXT_ACTION,
        ).fact
        self.assertEqual(VerificationStatus.VALID, fact.status)
        outcome, calls = self.execute(context_policy_fact=fact)
        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assertEqual([], calls)

    def test_request_must_bind_the_current_order_and_authority_version(self) -> None:
        request = replace(
            self.request,
            order_ref="order-other",
            authority_version_ref="v2",
        )
        fact = self.verify(request=request)
        outcome, calls = self.execute(request=request)

        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            (
                "payment_request_order_ref_mismatch",
                "payment_request_authority_version_ref_mismatch",
                "payment_execution_order_ref_mismatch",
            ),
            fact.reason_codes,
        )
        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)

    def test_execution_must_bind_the_validated_request_and_order(self) -> None:
        payment = replace(
            self.payment,
            request_id="request-other",
            order_id="order-other",
            transaction_object_ref="request-other",
        )
        fact = self.verify(payment=payment)
        outcome, calls = self.execute(payment=payment)

        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            (
                "payment_execution_request_ref_mismatch",
                "payment_execution_transaction_object_ref_mismatch",
                "payment_execution_order_ref_mismatch",
            ),
            fact.reason_codes,
        )
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)

    def test_critical_payment_fields_cannot_change_silently(self) -> None:
        payment = replace(
            self.payment,
            amount=Decimal("490.00"),
            currency="USD",
            payee="payee-other",
        )
        fact = self.verify(payment=payment)
        outcome, calls = self.execute(payment=payment)

        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            (
                "payment_execution_payee_mismatch",
                "payment_execution_amount_mismatch",
                "payment_execution_currency_mismatch",
            ),
            fact.reason_codes,
        )
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)

    def test_authority_and_agent_cannot_be_swapped_at_execution(self) -> None:
        payment = replace(
            self.payment,
            authority_ref="mandate-other",
            agent_ref="agent-other",
        )
        fact = self.verify(payment=payment)
        outcome, calls = self.execute(payment=payment)

        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            (
                "payment_execution_authority_ref_mismatch",
                "payment_execution_agent_ref_mismatch",
            ),
            fact.reason_codes,
        )
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)

    def test_missing_continuous_references_fail_closed(self) -> None:
        request = replace(
            self.request,
            order_ref=None,
            authority_ref=None,
            authority_version_ref=None,
            payee=None,
        )
        payment = replace(
            self.payment,
            authority_ref=None,
            agent_ref=None,
            transaction_object_ref=None,
            payee=None,
        )
        fact = self.verify(request=request, payment=payment)
        outcome, calls = self.execute(request=request, payment=payment)

        self.assertEqual(VerificationStatus.MISSING_EVIDENCE, fact.status)
        self.assertIn("payment_request_order_ref_missing", fact.reason_codes)
        self.assertIn(
            "payment_execution_transaction_object_ref_missing",
            fact.reason_codes,
        )
        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)

    def test_reference_collision_or_execution_before_request_is_invalid(self) -> None:
        payment = replace(
            self.payment,
            payment_id="request-1",
            occurred_at=self.now - timedelta(seconds=1),
        )
        fact = self.verify(payment=payment)

        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(
            (
                "payment_execution_reference_collision",
                "payment_execution_before_request",
            ),
            fact.reason_codes,
        )

    def test_upstream_non_allow_decision_blocks_even_a_valid_payment_binding(self) -> None:
        for decision in (
            Decision.DENY,
            Decision.CONFIRMATION_REQUIRED,
            Decision.INDETERMINATE,
        ):
            with self.subTest(decision=decision):
                outcome, calls = self.execute(decision=decision)
                self.assertEqual(decision, outcome.decision)
                self.assertEqual(VerificationStatus.VALID, outcome.binding_fact.status)
                self.assertFalse(outcome.executed)
                self.assertEqual([], calls)

    def test_missing_p3_executor_evidence_is_indeterminate_before_callback(self) -> None:
        identity = replace(self.identity, executor_instance_id=None)
        outcome, calls = self.execute(
            identity=identity,
            executor_ref=None,
        )

        self.assertEqual(VerificationStatus.VALID, outcome.binding_fact.status)
        self.assertEqual(
            VerificationStatus.MISSING_EVIDENCE,
            outcome.identity_fact.status,
        )
        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)

    def test_invalid_p3_identity_is_denied_before_callback(self) -> None:
        identity = replace(self.identity, agent_id="agent-other")
        outcome, calls = self.execute(identity=identity)

        self.assertEqual(VerificationStatus.VALID, outcome.binding_fact.status)
        self.assertEqual(VerificationStatus.INVALID, outcome.identity_fact.status)
        self.assertEqual(
            ("identity_object_agent_ref_mismatch",),
            outcome.identity_fact.reason_codes,
        )
        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)

    def test_p5_replay_preserves_final_p2_p3_and_p4_gate_blocks(self) -> None:
        missing_p2, calls = self.execute(
            payment=replace(self.payment, transaction_object_ref=None)
        )
        self.assertEqual([], calls)
        missing_p3, calls = self.execute(
            identity=replace(self.identity, executor_instance_id=None), executor_ref=None
        )
        self.assertEqual([], calls)
        base_state = {
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
        for missing_path in ("request.amount", "request.payee", "request.currency"):
            with self.subTest(missing_path=missing_path):
                fact = evaluate_context_policy(
                    base_state,
                    trusted_sources={key: value for key, value in sources.items() if key != missing_path},
                    required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
                    current_action=PAYMENT_CONTEXT_ACTION,
                ).fact
                missing_p4, calls = self.execute(context_policy_fact=fact)
                self.assertEqual([], calls)
                replay = self.replay_gate_outcome(missing_p4)
                self.assertEqual(ReplayStatus.INDETERMINATE, replay.status)
                self.assertNotEqual(Decision.ALLOW, missing_p4.decision)
                self.assertFalse(missing_p4.executed)

        for outcome in (missing_p2, missing_p3):
            replay = self.replay_gate_outcome(outcome)
            self.assertEqual(ReplayStatus.INDETERMINATE, replay.status)
            self.assertNotEqual(Decision.ALLOW, outcome.decision)
            self.assertFalse(outcome.executed)

        valid, calls = self.execute()
        self.assertEqual(["paid"], calls)
        replay = self.replay_gate_outcome(valid)
        self.assertEqual(ReplayStatus.VALID, replay.status)
        self.assertEqual(Decision.ALLOW, replay.decision)
        self.assertTrue(valid.executed)


if __name__ == "__main__":
    unittest.main()

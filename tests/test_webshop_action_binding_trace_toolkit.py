from __future__ import annotations

from dataclasses import replace
import unittest

from agentic_payment_experiment import Decision
from agentic_payment_experiment.authoritative_trace import (
    TraceValidationStatus,
    validate_product_authoritative_trace,
)
from agentic_payment_experiment.trusted_execution import VerificationStatus
from agentic_payment_experiment.webshop_action_binding_trace_toolkit import (
    build_action_binding_rejection_trace,
)
import tests.test_webshop_runtime_gate as runtime_gate_test


class WebShopActionBindingTraceToolkitTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = runtime_gate_test.WebShopRuntimeGateTest()
        self.fixture.setUp()
        assert self.fixture.adaptation.order is not None

    def _rebuild(self, action, outcome):
        assert outcome.bound_request is not None
        assert outcome.prepayment_result is not None
        assert outcome.governed_action_fact is not None
        return build_action_binding_rejection_trace(
            mandate=self.fixture.mandate,
            authorized_order=self.fixture.adaptation.order,
            current_order=self.fixture.adaptation.order,
            bound_request=outcome.bound_request,
            prepayment_result=outcome.prepayment_result,
            governed_action=action,
            execution_candidate=self.fixture.execution,
            governed_action_fact=outcome.governed_action_fact,
            base_outcome=replace(outcome, authoritative_trace=None),
        )

    def test_invalid_agent_binding_rebuilds_same_valid_trace_from_facts(self) -> None:
        action = replace(self.fixture.governed_action, agent_ref="agent-evil")
        outcome, calls = self.fixture.invoke(governed_action=action)

        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertEqual(0, outcome.callback_count)
        self.assertEqual([], calls)
        self.assertEqual(VerificationStatus.INVALID, outcome.governed_action_fact.status)

        rebuilt = self._rebuild(action, outcome)
        self.assertEqual(outcome.authoritative_trace, rebuilt)
        validation = validate_product_authoritative_trace(rebuilt)
        self.assertEqual(TraceValidationStatus.VALID, validation.status)
        self.assertEqual("WEBSHOP_ACTION_BINDING_T05_V2", validation.profile)

    def test_missing_action_id_uses_missing_id_projection_without_fabrication(self) -> None:
        action = replace(self.fixture.governed_action, action_id="")
        outcome, calls = self.fixture.invoke(governed_action=action)

        self.assertEqual(Decision.INDETERMINATE, outcome.decision)
        self.assertEqual(0, outcome.callback_count)
        self.assertEqual([], calls)
        self.assertEqual(
            VerificationStatus.MISSING_EVIDENCE,
            outcome.governed_action_fact.status,
        )
        self.assertIsNone(outcome.governed_action_fact.action_id)

        rebuilt = self._rebuild(action, outcome)
        validation = validate_product_authoritative_trace(rebuilt)
        self.assertEqual(TraceValidationStatus.VALID, validation.status)
        self.assertEqual("WEBSHOP_ACTION_BINDING_T06_V2", validation.profile)
        action_event = next(
            event for event in rebuilt.events if event.event_type == "ACTION_RECORDED"
        )
        self.assertTrue(action_event.entity_ref.startswith("GovernedPaymentAction:binding:"))
        self.assertNotEqual("GovernedPaymentAction:", action_event.entity_ref)

    def test_unrelated_invalid_binding_is_not_forced_into_target_profile(self) -> None:
        action = replace(
            self.fixture.governed_action,
            subject_ref="different-user",
            payment_ref="different-payment",
        )
        outcome, calls = self.fixture.invoke(governed_action=action)

        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertEqual(0, outcome.callback_count)
        self.assertEqual([], calls)
        self.assertIsNone(outcome.authoritative_trace)
        self.assertIsNone(self._rebuild(action, outcome))

    def test_trace_failure_does_not_change_existing_rejection_outcome(self) -> None:
        action = replace(self.fixture.governed_action, agent_ref="agent-evil")
        outcome, calls = self.fixture.invoke(governed_action=action)
        assert outcome.bound_request is not None
        assert outcome.prepayment_result is not None
        assert outcome.governed_action_fact is not None

        mismatched_order = replace(
            self.fixture.adaptation.order,
            total_amount=self.fixture.adaptation.order.total_amount + 1,
        )
        trace = build_action_binding_rejection_trace(
            mandate=self.fixture.mandate,
            authorized_order=mismatched_order,
            current_order=self.fixture.adaptation.order,
            bound_request=outcome.bound_request,
            prepayment_result=outcome.prepayment_result,
            governed_action=action,
            execution_candidate=self.fixture.execution,
            governed_action_fact=outcome.governed_action_fact,
            base_outcome=replace(outcome, authoritative_trace=None),
        )

        self.assertIsNone(trace)
        self.assertEqual(Decision.DENY, outcome.decision)
        self.assertEqual(0, outcome.callback_count)
        self.assertFalse(outcome.checkout_executed)
        self.assertEqual([], calls)


if __name__ == "__main__":
    unittest.main()

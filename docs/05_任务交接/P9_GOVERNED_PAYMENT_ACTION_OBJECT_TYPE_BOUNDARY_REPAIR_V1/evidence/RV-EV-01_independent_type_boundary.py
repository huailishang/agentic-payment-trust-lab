from __future__ import annotations

import json
from types import SimpleNamespace

from agentic_payment_experiment import Decision
from agentic_payment_experiment.trusted_execution import (
    GovernedPaymentAction,
    VerificationStatus,
    verify_governed_payment_action,
)
from tests.test_webshop_runtime_gate import WebShopRuntimeGateTest
from tests.trusted_execution.test_governed_action import GovernedActionTest


class ActionSubclass(GovernedPaymentAction):
    pass


class ExplodingProxy:
    def __getattribute__(self, name):
        raise AssertionError(f"invalid object attribute read: {name}")


def main() -> None:
    verifier_case = GovernedActionTest(
        methodName="test_valid_action_is_immutable_and_serializes_to_primitives"
    )
    verifier_case.setUp()
    kwargs = {
        "mandate": verifier_case.mandate,
        "order": verifier_case.order,
        "request": verifier_case.request,
        "execution": verifier_case.execution,
        "agent_identity": verifier_case.identity,
        "current_executor_instance_ref": verifier_case.executor_id,
        "context_policy_fact": verifier_case.context,
    }

    invalid_objects = {
        "mutable_lookalike": SimpleNamespace(**verifier_case.action.__dict__),
        "serialized_dict": verifier_case.action.to_dict(),
        "list": [verifier_case.action],
        "string": "execute_payment",
        "subclass": ActionSubclass(**verifier_case.action.__dict__),
        "exploding_proxy": ExplodingProxy(),
    }

    verifier_results: dict[str, object] = {}
    for name, obj in invalid_objects.items():
        fact = verify_governed_payment_action(obj, **kwargs)  # type: ignore[arg-type]
        assert fact.status is VerificationStatus.INVALID, (name, fact)
        assert fact.action_id is None
        assert fact.reason_codes == ("governed_action_invalid_type",)
        assert fact.checked_action_type is None
        assert fact.checked_order_ref is None
        assert fact.checked_request_ref is None
        assert fact.checked_payment_ref is None
        verifier_results[name] = fact.to_dict()

    valid_fact = verify_governed_payment_action(verifier_case.action, **kwargs)
    assert valid_fact.status is VerificationStatus.VALID

    none_fact = verify_governed_payment_action(None, **kwargs)
    assert none_fact.status is VerificationStatus.MISSING_EVIDENCE
    assert none_fact.reason_codes == ("governed_action_missing",)

    gate_case = WebShopRuntimeGateTest(
        methodName="test_valid_governed_action_continues_through_p2_p4_and_one_callback"
    )
    gate_case.setUp()

    gate_objects = {
        "mutable_lookalike": SimpleNamespace(**gate_case.governed_action.__dict__),
        "serialized_dict": gate_case.governed_action.to_dict(),
        "list": [gate_case.governed_action],
        "string": "execute_payment",
        "subclass": ActionSubclass(**gate_case.governed_action.__dict__),
        "exploding_proxy": ExplodingProxy(),
    }

    gate_results: dict[str, object] = {}
    for name, obj in gate_objects.items():
        outcome, calls = gate_case.invoke(governed_action=obj)
        assert outcome.decision is Decision.DENY, (name, outcome)
        assert outcome.checkout_executed is False
        assert outcome.callback_count == 0
        assert calls == []
        assert outcome.runtime_gate_record is None
        assert outcome.governed_action_fact is not None
        assert outcome.governed_action_fact.status is VerificationStatus.INVALID
        assert outcome.reason_codes == ("action:governed_action_invalid_type",)
        gate_results[name] = {
            "decision": outcome.decision.value,
            "callback_count": outcome.callback_count,
            "callback_observations": len(calls),
            "runtime_gate_record": None,
            "fact": outcome.governed_action_fact.to_dict(),
        }

    valid_outcome, valid_calls = gate_case.invoke(
        governed_action=gate_case.governed_action
    )
    assert valid_outcome.decision is Decision.ALLOW
    assert valid_outcome.callback_count == 1
    assert valid_calls == ["checkout"]

    omitted_outcome, omitted_calls = gate_case.invoke()
    assert omitted_outcome.decision is Decision.ALLOW
    assert omitted_outcome.callback_count == 1
    assert omitted_outcome.governed_action_fact is None
    assert omitted_calls == ["checkout"]

    print(
        json.dumps(
            {
                "verifier_invalid_objects": verifier_results,
                "gate_invalid_objects": gate_results,
                "valid_exact_type": {
                    "verification": valid_fact.status.value,
                    "gate_decision": valid_outcome.decision.value,
                    "callback_count": valid_outcome.callback_count,
                },
                "none_or_omitted": {
                    "pure_verifier": none_fact.status.value,
                    "gate_backward_compatible_decision": omitted_outcome.decision.value,
                    "gate_callback_count": omitted_outcome.callback_count,
                },
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

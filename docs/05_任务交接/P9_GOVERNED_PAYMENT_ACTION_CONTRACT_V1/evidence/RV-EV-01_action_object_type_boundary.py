from __future__ import annotations

import json
from types import SimpleNamespace

from agentic_payment_experiment.trusted_execution import (
    VerificationStatus,
    verify_governed_payment_action,
)
from tests.test_webshop_runtime_gate import WebShopRuntimeGateTest
from tests.trusted_execution.test_governed_action import GovernedActionTest


def main() -> None:
    verifier_case = GovernedActionTest(
        methodName="test_valid_action_is_immutable_and_serializes_to_primitives"
    )
    verifier_case.setUp()
    verifier_kwargs = {
        "mandate": verifier_case.mandate,
        "order": verifier_case.order,
        "request": verifier_case.request,
        "execution": verifier_case.execution,
        "agent_identity": verifier_case.identity,
        "current_executor_instance_ref": verifier_case.executor_id,
        "context_policy_fact": verifier_case.context,
    }

    mutable_action = SimpleNamespace(**verifier_case.action.__dict__)
    mutable_fact = verify_governed_payment_action(mutable_action, **verifier_kwargs)
    mutable_action.payment_ref = "changed-after-verification"

    dict_exception: dict[str, str] | None = None
    dict_fact = None
    try:
        dict_fact = verify_governed_payment_action(
            verifier_case.action.to_dict(),  # type: ignore[arg-type]
            **verifier_kwargs,
        )
    except Exception as exc:  # evaluator evidence intentionally records live failure
        dict_exception = {
            "type": type(exc).__name__,
            "message": str(exc),
        }

    gate_case = WebShopRuntimeGateTest(
        methodName="test_valid_governed_action_continues_through_p2_p4_and_one_callback"
    )
    gate_case.setUp()
    mutable_gate_action = SimpleNamespace(**gate_case.governed_action.__dict__)
    mutable_outcome, mutable_calls = gate_case.invoke(
        governed_action=mutable_gate_action  # type: ignore[arg-type]
    )

    dict_gate_exception: dict[str, str] | None = None
    dict_gate_outcome = None
    dict_gate_calls = None
    try:
        dict_gate_outcome, dict_gate_calls = gate_case.invoke(
            governed_action=gate_case.governed_action.to_dict()  # type: ignore[arg-type]
        )
    except Exception as exc:  # evaluator evidence intentionally records live failure
        dict_gate_exception = {
            "type": type(exc).__name__,
            "message": str(exc),
        }

    result = {
        "expected_boundary": {
            "mutable_lookalike": "INVALID and zero callback",
            "dict": "INVALID and zero callback without exception",
        },
        "actual": {
            "mutable_verifier_status": mutable_fact.status.value,
            "mutable_verifier_reasons": list(mutable_fact.reason_codes),
            "mutable_was_mutated_after_verification": (
                mutable_action.payment_ref == "changed-after-verification"
            ),
            "dict_verifier_status": (
                dict_fact.status.value if dict_fact is not None else None
            ),
            "dict_verifier_reasons": (
                list(dict_fact.reason_codes) if dict_fact is not None else None
            ),
            "dict_verifier_exception": dict_exception,
            "mutable_gate_decision": mutable_outcome.decision.value,
            "mutable_gate_fact_status": (
                mutable_outcome.governed_action_fact.status.value
                if mutable_outcome.governed_action_fact is not None
                else None
            ),
            "mutable_gate_callback_count": mutable_outcome.callback_count,
            "mutable_gate_callback_observations": len(mutable_calls),
            "dict_gate_decision": (
                dict_gate_outcome.decision.value
                if dict_gate_outcome is not None
                else None
            ),
            "dict_gate_callback_count": (
                dict_gate_outcome.callback_count
                if dict_gate_outcome is not None
                else None
            ),
            "dict_gate_callback_observations": (
                len(dict_gate_calls) if dict_gate_calls is not None else None
            ),
            "dict_gate_exception": dict_gate_exception,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))

    assert mutable_fact.status is VerificationStatus.VALID
    assert mutable_outcome.governed_action_fact is not None
    assert mutable_outcome.governed_action_fact.status is VerificationStatus.VALID
    assert mutable_outcome.callback_count == 1
    assert len(mutable_calls) == 1
    assert dict_exception is not None
    assert dict_exception["type"] == "AttributeError"
    assert dict_gate_exception is not None
    assert dict_gate_exception["type"] == "AttributeError"


if __name__ == "__main__":
    main()

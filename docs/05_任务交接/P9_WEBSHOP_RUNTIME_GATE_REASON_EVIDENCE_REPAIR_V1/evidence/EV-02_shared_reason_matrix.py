from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from agentic_payment_experiment.models import AgentIdentity, Decision
from agentic_payment_experiment.payment_execution import observe_payment_execution_gate
from agentic_payment_experiment.trusted_execution import (
    IdentityAssuranceLevel,
    VerificationStatus,
)
from tests.trusted_execution.test_payment_binding import PaymentExecutionBindingTests


case = PaymentExecutionBindingTests(methodName="runTest")
case.setUp()
allowed_outcome, allowed_calls = case.execute()
assert allowed_calls == ["paid"]
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
        case.mandate,
        case.order,
        case.request,
        case.payment if payment is None else payment,
        lambda: calls.append("paid") or "provider-payment-1",
        agent_identity=case.identity if identity is None else identity,
        current_provider_ref=provider_ref,
        current_executor_instance_ref=executor_ref,
        context_policy_fact=context_policy_fact,
    )
    return record, calls


def capture(name, kwargs, expected_decision, expected_reason):
    record, calls = observe(**kwargs)
    assert record.final_decision is expected_decision
    assert expected_reason in record.reason_codes
    expected_count = 1 if expected_decision is Decision.ALLOW else 0
    assert record.callback_count == expected_count
    assert calls == (["paid"] if expected_count else [])
    if expected_decision is not Decision.ALLOW:
        assert any(
            reason in record.reason_codes
            for reason in (
                "p1:upstream_prepayment_non_allow",
                "p2:binding_missing",
                "p2:binding_invalid",
                "p3:identity_missing",
                "p3:identity_invalid",
                "p3:assurance_insufficient",
                "p4:context_missing",
                "p4:context_invalid",
                "p4:policy_version_mismatch",
                "p4:current_action_mismatch",
                "p4:required_source_paths_mismatch",
                "p4:covered_source_paths_mismatch",
                "p4:missing_source_paths",
                "p4:source_coverage_value_mismatch",
            )
        )
    return {
        "case": name,
        "decision": record.final_decision.value,
        "callback_count": record.callback_count,
        "callback_executed": record.callback_executed,
        "expected_causal_reason": expected_reason,
        "reason_codes": list(record.reason_codes),
        "binding_status": record.binding_status,
        "identity_status": record.identity_status,
        "context_policy_status": record.context_policy_status,
    }


specs = (
    (
        "upstream_prepayment_non_allow",
        {"decision": Decision.DENY},
        Decision.DENY,
        "p1:upstream_prepayment_non_allow",
    ),
    (
        "p2_binding_missing",
        {"payment": replace(case.payment, request_id="")},
        Decision.INDETERMINATE,
        "p2:binding_missing",
    ),
    (
        "p2_binding_invalid",
        {"payment": replace(case.payment, request_id="request-other")},
        Decision.DENY,
        "p2:binding_invalid",
    ),
    (
        "p3_identity_missing",
        {
            "identity": AgentIdentity("", "", None, ""),
            "provider_ref": "provider-current",
            "executor_ref": "executor-current",
        },
        Decision.INDETERMINATE,
        "p3:identity_missing",
    ),
    (
        "p3_identity_invalid",
        {"identity": replace(case.identity, executor_instance_id="executor-other")},
        Decision.DENY,
        "p3:identity_invalid",
    ),
    (
        "p4_context_missing",
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
        "p4_context_invalid",
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
        "p4_policy_version_mismatch",
        {"context_policy_fact": replace(valid_context, policy_version="unsupported")},
        Decision.INDETERMINATE,
        "p4:policy_version_mismatch",
    ),
    (
        "p4_current_action_mismatch",
        {"context_policy_fact": replace(valid_context, current_action="refund_payment")},
        Decision.INDETERMINATE,
        "p4:current_action_mismatch",
    ),
    (
        "p4_required_source_paths_mismatch",
        {"context_policy_fact": replace(valid_context, required_source_paths=("request.amount",))},
        Decision.INDETERMINATE,
        "p4:required_source_paths_mismatch",
    ),
    (
        "p4_covered_source_paths_mismatch",
        {"context_policy_fact": replace(valid_context, covered_source_paths=("request.amount",))},
        Decision.INDETERMINATE,
        "p4:covered_source_paths_mismatch",
    ),
    (
        "p4_missing_source_paths",
        {"context_policy_fact": replace(valid_context, missing_source_paths=("request.amount",))},
        Decision.INDETERMINATE,
        "p4:missing_source_paths",
    ),
    (
        "p4_source_coverage_value_mismatch",
        {"context_policy_fact": replace(valid_context, source_coverage=())},
        Decision.INDETERMINATE,
        "p4:source_coverage_value_mismatch",
    ),
    (
        "runtime_gate_allow",
        {},
        Decision.ALLOW,
        "runtime:allow",
    ),
)

rows = [capture(*spec) for spec in specs]
weak_identity = replace(valid_identity, assurance_level=IdentityAssuranceLevel.DECLARED)
with patch(
    "agentic_payment_experiment.payment_execution.verify_agent_executor_identity",
    return_value=weak_identity,
):
    rows.append(
        capture(
            "p3_assurance_insufficient",
            {},
            Decision.INDETERMINATE,
            "p3:assurance_insufficient",
        )
    )

payload = {
    "schema": "shared-runtime-gate-reason-matrix/v1",
    "case_count": len(rows),
    "all_non_allow_have_causal_reason": True,
    "cases": rows,
}
output = Path(__file__).with_name("EV-02.shared_reason_matrix.json")
output.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

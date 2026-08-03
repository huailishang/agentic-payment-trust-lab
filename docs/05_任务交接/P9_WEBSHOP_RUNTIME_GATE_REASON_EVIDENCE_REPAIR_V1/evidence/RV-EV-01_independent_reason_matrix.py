from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tests" / "trusted_execution"))

from agentic_payment_experiment import Decision
from agentic_payment_experiment.payment_execution import observe_payment_execution_gate
from agentic_payment_experiment.trusted_execution import (
    IdentityAssuranceLevel,
    VerificationStatus,
)
from test_payment_binding import PaymentExecutionBindingTests
from test_webshop_runtime_gate import WebShopRuntimeGateTest, context_fact


def assert_causal(record, expected: str, calls: list[str]) -> dict[str, object]:
    assert expected in record.reason_codes, (expected, record.reason_codes)
    if record.final_decision is Decision.ALLOW:
        assert record.callback_count == 1 and calls == ["paid"]
    else:
        assert record.callback_count == 0 and calls == []
        causal = [
            code
            for code in record.reason_codes
            if code in {
                "p1:upstream_prepayment_non_allow",
                "p2:binding_missing",
                "p2:binding_invalid",
                "p3:identity_missing",
                "p3:identity_invalid",
                "p3:assurance_insufficient",
                "p4:context_missing",
                "p4:context_invalid",
                "p4:unauthorized_state_change",
                "p4:policy_version_mismatch",
                "p4:current_action_mismatch",
                "p4:required_source_paths_mismatch",
                "p4:covered_source_paths_mismatch",
                "p4:missing_source_paths",
                "p4:source_coverage_value_mismatch",
            }
        ]
        assert causal, record.reason_codes
    return {
        "decision": record.final_decision.value,
        "callback_count": record.callback_count,
        "expected_reason": expected,
        "reason_codes": list(record.reason_codes),
    }


shared = PaymentExecutionBindingTests(methodName="test_valid_continuous_binding_is_the_only_path_that_executes")
shared.setUp()
allowed, allowed_calls = shared.execute()
valid_context = allowed.context_policy_fact
valid_identity = allowed.identity_fact


def observe(*, decision=Decision.ALLOW, payment=None, identity=None,
            provider_ref="offline-provider-1", executor_ref="executor-1",
            context_policy_fact=valid_context):
    calls: list[str] = []
    record = observe_payment_execution_gate(
        decision,
        shared.mandate,
        shared.order,
        shared.request,
        shared.payment if payment is None else payment,
        lambda: calls.append("paid") or "provider-payment-1",
        agent_identity=shared.identity if identity is None else identity,
        current_provider_ref=provider_ref,
        current_executor_instance_ref=executor_ref,
        context_policy_fact=context_policy_fact,
    )
    return record, calls

cases: dict[str, dict[str, object]] = {}
branch_specs = (
    ("upstream", {"decision": Decision.DENY}, "p1:upstream_prepayment_non_allow"),
    ("p2_missing", {"payment": replace(shared.payment, request_id="")}, "p2:binding_missing"),
    ("p2_invalid", {"payment": replace(shared.payment, request_id="request-other")}, "p2:binding_invalid"),
    ("p3_missing", {
        "identity": replace(shared.identity, agent_id="", provider="", executor_instance_id=None, status=""),
        "provider_ref": "provider-current", "executor_ref": "executor-current",
    }, "p3:identity_missing"),
    ("p3_invalid", {"identity": replace(shared.identity, executor_instance_id="executor-other")}, "p3:identity_invalid"),
    ("p4_missing", {"context_policy_fact": replace(valid_context, status=VerificationStatus.MISSING_EVIDENCE, reason_codes=("synthetic_missing",))}, "p4:context_missing"),
    ("p4_invalid", {"context_policy_fact": replace(valid_context, status=VerificationStatus.INVALID, reason_codes=("synthetic_invalid",))}, "p4:context_invalid"),
    ("p4_policy_version", {"context_policy_fact": replace(valid_context, policy_version="unsupported")}, "p4:policy_version_mismatch"),
    ("p4_current_action", {"context_policy_fact": replace(valid_context, current_action="refund_payment")}, "p4:current_action_mismatch"),
    ("p4_required_paths", {"context_policy_fact": replace(valid_context, required_source_paths=("request.amount",))}, "p4:required_source_paths_mismatch"),
    ("p4_covered_paths", {"context_policy_fact": replace(valid_context, covered_source_paths=("request.amount",))}, "p4:covered_source_paths_mismatch"),
    ("p4_missing_paths", {"context_policy_fact": replace(valid_context, missing_source_paths=("request.amount",))}, "p4:missing_source_paths"),
    ("p4_digest", {"context_policy_fact": replace(valid_context, source_coverage=())}, "p4:source_coverage_value_mismatch"),
    ("allow", {}, "runtime:allow"),
)
for name, kwargs, expected in branch_specs:
    record, calls = observe(**kwargs)
    cases[name] = assert_causal(record, expected, calls)

weak_identity = replace(valid_identity, assurance_level=IdentityAssuranceLevel.DECLARED)
with patch(
    "agentic_payment_experiment.payment_execution.verify_agent_executor_identity",
    return_value=weak_identity,
):
    record, calls = observe()
cases["p3_assurance"] = assert_causal(record, "p3:assurance_insufficient", calls)
assert len(cases) == 15

# Reproduce the two original WebShop counterexamples and verify wrapper forwarding.
webshop = WebShopRuntimeGateTest(methodName="test_permissive_explicit_mandate_allows_one_injected_callback")
webshop.setUp()
wrong_action = context_fact(
    webshop.mandate,
    webshop.adaptation.order,
    webshop.bound_request,
    current_action="refund_payment",
)
wrong_outcome, wrong_calls = webshop.invoke(context_policy_fact=wrong_action)
assert wrong_outcome.decision is Decision.INDETERMINATE
assert wrong_outcome.callback_count == 0 and wrong_calls == []
assert "p4:current_action_mismatch" in wrong_outcome.reason_codes
assert wrong_outcome.runtime_gate_record is not None
assert wrong_outcome.reason_codes == wrong_outcome.runtime_gate_record.reason_codes

digest_context = context_fact(
    webshop.mandate,
    webshop.adaptation.order,
    webshop.bound_request,
    state_overrides={"request": {"amount": Decimal("999.00")}},
)
digest_outcome, digest_calls = webshop.invoke(context_policy_fact=digest_context)
assert digest_outcome.decision is Decision.INDETERMINATE
assert digest_outcome.callback_count == 0 and digest_calls == []
assert "p4:source_coverage_value_mismatch" in digest_outcome.reason_codes
assert digest_outcome.runtime_gate_record is not None
assert digest_outcome.reason_codes == digest_outcome.runtime_gate_record.reason_codes

print(json.dumps({
    "shared_branch_count": len(cases),
    "all_non_allow_have_causal_reason": True,
    "branches": cases,
    "webshop_counterexamples": {
        "wrong_action": {
            "decision": wrong_outcome.decision.value,
            "callback_count": wrong_outcome.callback_count,
            "reason_codes": list(wrong_outcome.reason_codes),
            "reason_equality": True,
        },
        "digest_mismatch": {
            "decision": digest_outcome.decision.value,
            "callback_count": digest_outcome.callback_count,
            "reason_codes": list(digest_outcome.reason_codes),
            "reason_equality": True,
        },
    },
}, ensure_ascii=False, indent=2, sort_keys=True))

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from agentic_payment_experiment.models import AgentIdentity, Decision
from agentic_payment_experiment.payment_execution import (
    PAYMENT_CONTEXT_ACTION,
    PAYMENT_REQUIRED_SOURCE_PATHS,
)
from agentic_payment_experiment.trusted_execution import evaluate_context_policy
from tests.test_webshop_runtime_gate import WebShopRuntimeGateTest, context_fact


def result_view(name, outcome, calls):
    record = outcome.runtime_gate_record
    return {
        "case": name,
        "decision": outcome.decision.value,
        "checkout_executed": outcome.checkout_executed,
        "callback_count": outcome.callback_count,
        "calls": list(calls),
        "reason_codes": list(outcome.reason_codes),
        "binding_status": record.binding_status if record else None,
        "binding_reason_codes": list(record.binding_reason_codes) if record else [],
        "identity_status": record.identity_status if record else None,
        "identity_reason_codes": list(record.identity_reason_codes) if record else [],
        "context_policy_status": record.context_policy_status if record else None,
        "context_policy_reason_codes": list(record.context_policy_reason_codes) if record else [],
    }


case = WebShopRuntimeGateTest(methodName="runTest")
case.setUp()

matrix = []
p2_cases = {
    "p2_request_ref_mismatch": replace(case.execution, request_id="request-other"),
    "p2_transaction_object_ref_mismatch": replace(
        case.execution, transaction_object_ref="request-other"
    ),
    "p2_order_ref_mismatch": replace(case.execution, order_id="order-other"),
    "p2_authority_ref_mismatch": replace(
        case.execution, authority_ref="authority-other"
    ),
    "p2_agent_ref_mismatch": replace(case.execution, agent_ref="agent-other"),
    "p2_payee_mismatch": replace(case.execution, payee="payee-other"),
    "p2_amount_mismatch": replace(
        case.execution, amount=case.execution.amount + Decimal("1.00")
    ),
    "p2_currency_mismatch": replace(case.execution, currency="CNY"),
}
for name, execution in p2_cases.items():
    outcome, calls = case.invoke(execution_candidate=execution)
    assert outcome.decision is Decision.DENY
    assert outcome.callback_count == 0
    assert not calls
    assert outcome.runtime_gate_record is not None
    assert outcome.runtime_gate_record.binding_status == "INVALID"
    matrix.append(result_view(name, outcome, calls))

missing_identity = AgentIdentity("", "", None, "")
outcome, calls = case.invoke(
    agent_identity=missing_identity,
    current_provider_ref="provider-current",
    current_executor_instance_ref="executor-current",
)
assert outcome.decision is Decision.INDETERMINATE
assert outcome.callback_count == 0
matrix.append(result_view("p3_identity_evidence_missing", outcome, calls))

identity_mismatch = replace(case.identity, executor_instance_id="executor-other")
outcome, calls = case.invoke(agent_identity=identity_mismatch)
assert outcome.decision is Decision.DENY
assert outcome.callback_count == 0
matrix.append(result_view("p3_executor_mismatch", outcome, calls))

missing_context = evaluate_context_policy(
    {},
    required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
    current_action=PAYMENT_CONTEXT_ACTION,
).fact
outcome, calls = case.invoke(context_policy_fact=missing_context)
assert outcome.decision is Decision.INDETERMINATE
assert outcome.callback_count == 0
matrix.append(result_view("p4_context_missing", outcome, calls))

invalid_context = evaluate_context_policy(
    {},
    current_action=PAYMENT_CONTEXT_ACTION,
    observed_state_after={"request": {"amount": "999.00"}},
).fact
outcome, calls = case.invoke(context_policy_fact=invalid_context)
assert outcome.decision is Decision.DENY
assert outcome.callback_count == 0
matrix.append(result_view("p4_unauthorized_state_change", outcome, calls))

wrong_action = context_fact(
    case.mandate,
    case.adaptation.order,
    case.bound_request,
    current_action="refund_payment",
)
outcome, calls = case.invoke(context_policy_fact=wrong_action)
assert outcome.decision is Decision.INDETERMINATE
assert outcome.callback_count == 0
matrix.append(result_view("p4_stale_wrong_action", outcome, calls))

wrong_value = context_fact(
    case.mandate,
    case.adaptation.order,
    case.bound_request,
    state_overrides={"request": {"amount": Decimal("999.00")}},
)
outcome, calls = case.invoke(context_policy_fact=wrong_value)
assert outcome.decision is Decision.INDETERMINATE
assert outcome.callback_count == 0
matrix.append(result_view("p4_value_digest_mismatch", outcome, calls))

payload = {
    "schema": "webshop-runtime-gate-mismatch-matrix/v1",
    "case_count": len(matrix),
    "all_callbacks_blocked": all(item["callback_count"] == 0 for item in matrix),
    "cases": matrix,
}
output = Path(__file__).with_name("EV-02.runtime_mismatch_matrix.json")
output.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

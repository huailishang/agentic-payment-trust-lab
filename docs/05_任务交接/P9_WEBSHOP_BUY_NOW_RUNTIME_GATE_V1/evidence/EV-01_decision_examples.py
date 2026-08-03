from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from agentic_payment_experiment.models import Decision
from tests.test_webshop_runtime_gate import WebShopRuntimeGateTest


def view(outcome, calls):
    return {
        "decision": outcome.decision.value,
        "checkout_executed": outcome.checkout_executed,
        "callback_count": outcome.callback_count,
        "callback_result_ref": outcome.callback_result_ref,
        "calls": list(calls),
        "bound_request_agent_id": (
            outcome.bound_request.agent_id if outcome.bound_request is not None else None
        ),
        "prepayment_decision": (
            outcome.prepayment_result.decision.value
            if outcome.prepayment_result is not None
            else None
        ),
        "runtime_gate": (
            outcome.runtime_gate_record.to_dict()
            if outcome.runtime_gate_record is not None
            else None
        ),
        "reason_codes": list(outcome.reason_codes),
        "limitations": list(outcome.limitations),
    }


case = WebShopRuntimeGateTest(methodName="runTest")
case.setUp()

allow, calls = case.invoke()
assert allow.decision is Decision.ALLOW
assert allow.callback_count == 1
assert allow.checkout_executed

restrictive = replace(
    case.mandate,
    max_amount=Decimal("30.00"),
    allowed_categories=frozenset({"clothing"}),
)
deny, deny_calls = case.invoke(mandate=restrictive)
assert deny.decision is Decision.DENY
assert deny.callback_count == 0

stale = replace(
    case.confirmation,
    expires_at=case.bound_request.occurred_at - timedelta(seconds=1),
)
confirmation, confirmation_calls = case.invoke(confirmation_record=stale)
assert confirmation.decision is Decision.CONFIRMATION_REQUIRED
assert confirmation.callback_count == 0

indeterminate, indeterminate_calls = case.invoke(confirmation_record=None)
assert indeterminate.decision is Decision.INDETERMINATE
assert indeterminate.callback_count == 0

exception_calls: list[str] = []

def failing_callback():
    exception_calls.append("attempt")
    raise RuntimeError("offline checkout failed")

callback_failure, _ = case.invoke(checkout_callback=failing_callback)
assert callback_failure.decision is Decision.INDETERMINATE
assert callback_failure.callback_count == 1
assert not callback_failure.checkout_executed
assert exception_calls == ["attempt"]

payload = {
    "schema": "webshop-buy-now-gate-examples/v1",
    "allow": view(allow, calls),
    "deny_restrictive_mandate": view(deny, deny_calls),
    "confirmation_required": view(confirmation, confirmation_calls),
    "indeterminate_missing_confirmation": view(indeterminate, indeterminate_calls),
    "callback_exception": view(callback_failure, exception_calls),
}
output = Path(__file__).with_name("EV-01.decision_examples.json")
output.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

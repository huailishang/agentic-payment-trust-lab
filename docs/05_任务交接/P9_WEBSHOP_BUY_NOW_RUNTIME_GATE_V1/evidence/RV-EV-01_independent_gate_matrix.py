from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from agentic_payment_experiment import Decision
from test_webshop_runtime_gate import WebShopRuntimeGateTest, context_fact

case = WebShopRuntimeGateTest(methodName="test_permissive_explicit_mandate_allows_one_injected_callback")
case.setUp()

results: dict[str, dict[str, object]] = {}


def record(name: str, outcome, calls: list[str]) -> None:
    results[name] = {
        "decision": outcome.decision.value,
        "checkout_executed": outcome.checkout_executed,
        "callback_count": outcome.callback_count,
        "callback_result_ref": outcome.callback_result_ref,
        "calls": list(calls),
        "bound_agent_id": outcome.bound_request.agent_id if outcome.bound_request else None,
        "prepayment_decision": (
            outcome.prepayment_result.decision.value if outcome.prepayment_result else None
        ),
        "runtime_final_decision": (
            outcome.runtime_gate_record.final_decision.value
            if outcome.runtime_gate_record
            else None
        ),
        "reason_codes": list(outcome.reason_codes),
    }


# Explicit permissive mandate: final ALLOW and exactly one local seam call.
allow, allow_calls = case.invoke()
assert allow.decision is Decision.ALLOW
assert allow.checkout_executed is True
assert allow.callback_count == 1
assert allow_calls == ["checkout"]
assert allow.bound_request is not None and allow.bound_request.agent_id == case.agent_id
assert case.adaptation.payment_request is not None
assert case.adaptation.payment_request.agent_id is None
record("allow", allow, allow_calls)

# Instruction-like restrictive mandate: the expensive furniture item is denied.
restrictive = replace(
    case.mandate,
    max_amount=Decimal("30.00"),
    allowed_categories=frozenset({"clothing"}),
)
deny, deny_calls = case.invoke(mandate=restrictive)
assert deny.decision is Decision.DENY
assert deny.callback_count == 0 and deny_calls == []
assert {"p1:over_budget", "p1:category_out_of_scope"}.issubset(deny.reason_codes)
record("deny", deny, deny_calls)

# Stale confirmation and missing confirmation preserve non-ALLOW and never reach runtime callback.
stale = replace(
    case.confirmation,
    expires_at=case.bound_request.occurred_at - timedelta(seconds=1),
)
confirm, confirm_calls = case.invoke(confirmation_record=stale)
assert confirm.decision is Decision.CONFIRMATION_REQUIRED
assert confirm.callback_count == 0 and confirm_calls == []
assert confirm.runtime_gate_record is None
record("confirmation_required", confirm, confirm_calls)

indeterminate, indeterminate_calls = case.invoke(confirmation_record=None)
assert indeterminate.decision is Decision.INDETERMINATE
assert indeterminate.callback_count == 0 and indeterminate_calls == []
assert indeterminate.runtime_gate_record is None
record("p1_indeterminate", indeterminate, indeterminate_calls)

# P4 digest bound to another amount must stop before the callback.
mismatched_context = context_fact(
    case.mandate,
    case.adaptation.order,
    case.bound_request,
    state_overrides={"request": {"amount": Decimal("999.00")}},
)
p4_block, p4_calls = case.invoke(context_policy_fact=mismatched_context)
assert p4_block.decision is Decision.INDETERMINATE
assert p4_block.callback_count == 0 and p4_calls == []
assert p4_block.runtime_gate_record is not None
record("p4_value_mismatch", p4_block, p4_calls)

# Callback exception: one attempted call, no retry, no false success.
exception_calls: list[str] = []


def failing_callback() -> str:
    exception_calls.append("attempt")
    raise RuntimeError("independent failure")

exception, _ = case.invoke(checkout_callback=failing_callback)
assert exception.decision is Decision.INDETERMINATE
assert exception.checkout_executed is False
assert exception.callback_count == 1
assert exception_calls == ["attempt"]
assert exception.callback_result_ref is None
assert exception.runtime_gate_record is not None
assert exception.runtime_gate_record.callback_count == 1
assert exception.runtime_gate_record.final_decision is Decision.INDETERMINATE
assert "checkout_callback_exception:RuntimeError" in exception.reason_codes
record("callback_exception", exception, exception_calls)

print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from agentic_payment_experiment.models import Decision
from tests.test_webshop_runtime_gate import WebShopRuntimeGateTest, context_fact


PARENT_BEFORE = (
    ROOT
    / "docs/05_任务交接/P9_WEBSHOP_BUY_NOW_RUNTIME_GATE_V1/evidence/RV-EV-07.stdout.log"
)


def view(name, outcome, calls):
    record = outcome.runtime_gate_record
    assert record is not None
    return {
        "case": name,
        "decision": outcome.decision.value,
        "checkout_executed": outcome.checkout_executed,
        "callback_count": outcome.callback_count,
        "calls": list(calls),
        "outcome_reason_codes": list(outcome.reason_codes),
        "runtime_reason_codes": list(record.reason_codes),
        "reason_equality": outcome.reason_codes == record.reason_codes,
        "context_policy_status": record.context_policy_status,
        "context_policy_reason_codes": list(record.context_policy_reason_codes),
    }


before = json.loads(PARENT_BEFORE.read_text(encoding="utf-8"))
case = WebShopRuntimeGateTest(methodName="runTest")
case.setUp()

wrong_action_fact = context_fact(
    case.mandate,
    case.adaptation.order,
    case.bound_request,
    current_action="refund_payment",
)
wrong_action, wrong_action_calls = case.invoke(
    context_policy_fact=wrong_action_fact,
)
assert wrong_action.decision is Decision.INDETERMINATE
assert wrong_action.callback_count == 0
assert not wrong_action.checkout_executed
assert wrong_action_calls == []
assert "p4:current_action_mismatch" in wrong_action.reason_codes
assert wrong_action.runtime_gate_record is not None
assert wrong_action.reason_codes == wrong_action.runtime_gate_record.reason_codes

wrong_digest_fact = context_fact(
    case.mandate,
    case.adaptation.order,
    case.bound_request,
    state_overrides={"request": {"amount": Decimal("999.00")}},
)
wrong_digest, wrong_digest_calls = case.invoke(
    context_policy_fact=wrong_digest_fact,
)
assert wrong_digest.decision is Decision.INDETERMINATE
assert wrong_digest.callback_count == 0
assert not wrong_digest.checkout_executed
assert wrong_digest_calls == []
assert "p4:source_coverage_value_mismatch" in wrong_digest.reason_codes
assert wrong_digest.runtime_gate_record is not None
assert wrong_digest.reason_codes == wrong_digest.runtime_gate_record.reason_codes

after = {
    "cases": [
        view("p4_stale_wrong_action", wrong_action, wrong_action_calls),
        view("p4_value_digest_mismatch", wrong_digest, wrong_digest_calls),
    ],
    "finding": "P4 runtime contract mismatches remain safely blocked and now expose causal reasons",
}
payload = {
    "schema": "webshop-runtime-gate-reason-counterexamples/v1",
    "before": before,
    "after": after,
}
output = Path(__file__).with_name("EV-01.reason_counterexamples.json")
output.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

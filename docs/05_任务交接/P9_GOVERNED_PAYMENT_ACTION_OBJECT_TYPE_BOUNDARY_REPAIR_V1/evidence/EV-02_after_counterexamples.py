from pathlib import Path
import sys
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))

from tests.trusted_execution.test_governed_action import GovernedActionTest
from tests.test_webshop_runtime_gate import WebShopRuntimeGateTest

pure = GovernedActionTest(methodName='test_valid_action_is_immutable_and_serializes_to_primitives')
pure.setUp()
for label, invalid in (
    ('PURE_LOOKALIKE', SimpleNamespace(**pure.action.__dict__)),
    ('PURE_DICT', pure.action.to_dict()),
):
    print(label)
    fact = pure.verify(invalid)
    print('status=', fact.status.value)
    print('action_id=', fact.action_id)
    print('reasons=', fact.reason_codes)
    print('checked=', (
        fact.checked_action_type,
        fact.checked_order_ref,
        fact.checked_request_ref,
        fact.checked_payment_ref,
    ))
    print('exception=NONE')

runtime = WebShopRuntimeGateTest(methodName='test_permissive_explicit_mandate_allows_one_injected_callback')
runtime.setUp()
for label, invalid in (
    ('GATE_LOOKALIKE', SimpleNamespace(**runtime.governed_action.__dict__)),
    ('GATE_DICT', runtime.governed_action.to_dict()),
):
    print(label)
    outcome, calls = runtime.invoke(governed_action=invalid)
    print('decision=', outcome.decision.value)
    print('checkout_executed=', outcome.checkout_executed)
    print('callback_count=', outcome.callback_count)
    print('calls=', len(calls))
    print('runtime_gate_record=', outcome.runtime_gate_record)
    print('fact_status=', outcome.governed_action_fact.status.value)
    print('reasons=', outcome.reason_codes)
    print('exception=NONE')

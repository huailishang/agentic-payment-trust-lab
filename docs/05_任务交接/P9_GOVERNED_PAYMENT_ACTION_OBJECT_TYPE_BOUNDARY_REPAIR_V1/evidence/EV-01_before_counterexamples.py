from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from types import SimpleNamespace
from tests.trusted_execution.test_governed_action import GovernedActionTest
from tests.test_webshop_runtime_gate import WebShopRuntimeGateTest

pure = GovernedActionTest(methodName='test_valid_action_is_immutable_and_serializes_to_primitives')
pure.setUp()
lookalike = SimpleNamespace(**pure.action.__dict__)
print('PURE_LOOKALIKE')
fact = pure.verify(lookalike)
print('status=', fact.status.value)
print('reasons=', fact.reason_codes)

print('PURE_DICT')
try:
    pure.verify(pure.action.to_dict())
except Exception as exc:
    print('exception=', type(exc).__name__)
    print('message=', str(exc))
else:
    print('exception=NONE')

runtime = WebShopRuntimeGateTest(methodName='test_permissive_explicit_mandate_allows_one_injected_callback')
runtime.setUp()
print('GATE_LOOKALIKE')
outcome, calls = runtime.invoke(governed_action=SimpleNamespace(**runtime.governed_action.__dict__))
print('decision=', outcome.decision.value)
print('callback_count=', outcome.callback_count)
print('calls=', len(calls))
print('reasons=', outcome.reason_codes)

print('GATE_DICT')
try:
    runtime.invoke(governed_action=runtime.governed_action.to_dict())
except Exception as exc:
    print('exception=', type(exc).__name__)
    print('message=', str(exc))
else:
    print('exception=NONE')

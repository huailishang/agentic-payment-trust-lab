import importlib.util
from pathlib import Path

from agentic_payment_experiment.trusted_execution import (
    VerificationStatus,
    evaluate_context_policy,
)


test_path = (
    Path.cwd()
    / "tests"
    / "trusted_execution"
    / "test_payment_binding.py"
)
spec = importlib.util.spec_from_file_location("p4_payment_binding_test", test_path)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
PaymentExecutionBindingTests = module.PaymentExecutionBindingTests

fact = evaluate_context_policy({}, current_action="execute_payment").fact
case = PaymentExecutionBindingTests()
case.setUp()
outcome, calls = case.execute(context_policy_fact=fact)

observed = {
    "p4_status": fact.status.value,
    "source_count": 0,
    "decision": outcome.decision.value,
    "executed": outcome.executed,
    "callback_calls": calls,
}
print(observed)

assert fact.status is VerificationStatus.VALID
assert outcome.executed
assert calls == ["paid"]

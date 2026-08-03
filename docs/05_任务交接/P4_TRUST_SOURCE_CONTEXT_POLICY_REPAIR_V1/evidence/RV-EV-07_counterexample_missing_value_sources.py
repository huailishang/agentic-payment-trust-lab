import importlib.util
from pathlib import Path

from agentic_payment_experiment.payment_execution import (
    PAYMENT_CONTEXT_ACTION,
    PAYMENT_REQUIRED_SOURCE_PATHS,
)
from agentic_payment_experiment.trusted_execution import (
    SourceType,
    VerificationStatus,
    evaluate_context_policy,
)


test_path = (
    Path.cwd()
    / "tests"
    / "trusted_execution"
    / "test_payment_binding.py"
)
spec = importlib.util.spec_from_file_location("repair_payment_binding_test", test_path)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
PaymentExecutionBindingTests = module.PaymentExecutionBindingTests

case = PaymentExecutionBindingTests()
case.setUp()

state = {
    "mandate": {"mandate_id": case.mandate.mandate_id},
    "final_order": {"order_id": case.order.order_id},
    "request": {
        "request_id": case.request.request_id,
        "agent_id": case.request.agent_id,
    },
}
sources = {
    "mandate.mandate_id": SourceType.USER_CONFIRMED,
    "final_order.order_id": SourceType.USER_CONFIRMED,
    "request.request_id": SourceType.PROTOCOL_VERIFIED,
    "request.agent_id": SourceType.USER_CONFIRMED,
}
fact = evaluate_context_policy(
    state,
    trusted_sources=sources,
    required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
    current_action=PAYMENT_CONTEXT_ACTION,
).fact
outcome, calls = case.execute(context_policy_fact=fact)

uncovered_critical_paths = (
    "request.amount",
    "request.payee",
    "request.currency",
)
observed = {
    "p4_status": fact.status.value,
    "required_paths": fact.required_source_paths,
    "uncovered_critical_paths": uncovered_critical_paths,
    "decision": outcome.decision.value,
    "executed": outcome.executed,
    "callback_calls": calls,
}
print(observed)

assert fact.status is VerificationStatus.VALID
assert all(path not in fact.required_source_paths for path in uncovered_critical_paths)
assert outcome.executed
assert calls == ["paid"]

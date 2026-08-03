from tests.trusted_execution.test_payment_binding import PaymentExecutionBindingTests
from agentic_payment_experiment.models import Decision
from agentic_payment_experiment.payment_execution import (
    PAYMENT_CONTEXT_ACTION,
    PAYMENT_REQUIRED_SOURCE_PATHS,
    observe_payment_execution_gate,
)
from agentic_payment_experiment.trusted_execution import SourceType, evaluate_context_policy


case = PaymentExecutionBindingTests()
case.setUp()
state = {
    "mandate": {"mandate_id": case.mandate.mandate_id},
    "final_order": {"order_id": case.order.order_id},
    "request": {
        "request_id": case.request.request_id,
        "agent_id": case.request.agent_id,
        "amount": case.request.amount,
        "payee": case.request.payee,
        "currency": case.request.currency,
    },
}
sources = {
    "mandate.mandate_id": SourceType.USER_CONFIRMED,
    "final_order.order_id": SourceType.USER_CONFIRMED,
    "request.request_id": SourceType.PROTOCOL_VERIFIED,
    "request.agent_id": SourceType.USER_CONFIRMED,
    "request.payee": SourceType.USER_CONFIRMED,
    "request.currency": SourceType.USER_CONFIRMED,
}
fact = evaluate_context_policy(
    state,
    trusted_sources=sources,
    required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
    current_action=PAYMENT_CONTEXT_ACTION,
).fact
callbacks: list[str] = []
record = observe_payment_execution_gate(
    Decision.ALLOW,
    case.mandate,
    case.order,
    case.request,
    case.payment,
    lambda: callbacks.append("paid"),
    agent_identity=case.identity,
    current_provider_ref="offline-provider-1",
    current_executor_instance_ref="executor-1",
    context_policy_fact=fact,
)
print(f"p4_status={fact.status.value}")
print(f"final={record.final_decision.value}")
print(f"callback_count={record.callback_count}")
print(f"calls={len(callbacks)}")
assert fact.status.value == "MISSING_EVIDENCE"
assert record.final_decision is Decision.INDETERMINATE
assert record.callback_count == 0
assert not callbacks

from agentic_payment_experiment.trusted_execution import (
    CandidateFactUpdate,
    FactDomain,
    SourceType,
    VerificationStatus,
    evaluate_context_policy,
)


state = {"payment_status_observation": {"status": "PENDING"}}
update = CandidateFactUpdate(
    SourceType.PAYMENT_PROVIDER_OBSERVED,
    FactDomain.PAYMENT_STATUS,
    "payment_status_observation.status",
    value_ref="provider-status-ref",
    source_ref="provider-source",
)
result = evaluate_context_policy(
    state,
    (update,),
    current_action="execute_payment",
)

observed = {
    "status": result.fact.status.value,
    "applied": result.fact.applied_paths,
    "merged_status": result.trusted_state["payment_status_observation"]["status"],
    "changed": result.fact.trusted_state_changed,
}
print(observed)

assert result.fact.status is VerificationStatus.VALID
assert result.fact.applied_paths == ("payment_status_observation.status",)
assert result.trusted_state["payment_status_observation"]["status"] is None

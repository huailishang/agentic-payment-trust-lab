"""Independent evaluator checks for repaired finality boundaries."""

from dataclasses import replace
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from agentic_payment_experiment import (  # noqa: E402
    PaymentQueryEvidenceStage,
    PaymentStatus,
    assess_payment_recovery,
    derive_payment_query_finality,
)
from agentic_payment_experiment.scenario_loader import load_scenario  # noqa: E402


scenario = load_scenario(
    ROOT / "samples" / "scenarios" / "S12_unknown_payment_state_recovery.json"
)


def recovery_for(payment, observation):
    return assess_payment_recovery(
        payment,
        observation,
        mandate=scenario.mandate,
        request=scenario.request,
        order=scenario.final_order,
    )


failed_observation = replace(
    scenario.payment_status_observation,
    status=PaymentStatus.FAILED,
)
failed_recovery = recovery_for(scenario.payment_recovery_initial, failed_observation)
failed_fact = derive_payment_query_finality(
    scenario.payment_recovery_initial,
    failed_observation,
    failed_recovery,
)
assert failed_fact.evidence_stage is PaymentQueryEvidenceStage.QUERY_CONFIRMED
assert failed_fact.effective_status_terminal is True
assert not any(
    (
        failed_fact.business_success_confirmed,
        failed_fact.fulfillment_confirmed,
        failed_fact.user_task_success_confirmed,
        failed_fact.reconciliation_confirmed,
        failed_fact.settlement_confirmed,
        failed_fact.legal_finality_confirmed,
    )
)

pending_observation = replace(
    scenario.payment_status_observation,
    status=PaymentStatus.PENDING,
)
pending_fact = derive_payment_query_finality(
    scenario.payment_recovery_initial,
    pending_observation,
    recovery_for(scenario.payment_recovery_initial, pending_observation),
)
assert pending_fact.evidence_stage is PaymentQueryEvidenceStage.QUERY_UNRESOLVED
assert pending_fact.effective_status_terminal is False

known_success = replace(
    scenario.payment_recovery_initial,
    status=PaymentStatus.SUCCEEDED,
)
conflict_recovery = recovery_for(known_success, failed_observation)
conflict_fact = derive_payment_query_finality(
    known_success,
    failed_observation,
    conflict_recovery,
)
assert conflict_fact.evidence_stage is PaymentQueryEvidenceStage.QUERY_BLOCKED
assert conflict_fact.effective_status_terminal is False

for label, inconsistent in (
    (
        "initial",
        replace(failed_recovery, initial_status=PaymentStatus.SUCCEEDED),
    ),
    (
        "observed",
        replace(failed_recovery, observed_status=PaymentStatus.SUCCEEDED),
    ),
):
    try:
        derive_payment_query_finality(
            scenario.payment_recovery_initial,
            failed_observation,
            inconsistent,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(f"inconsistent {label} status did not fail closed")

print("trusted_failed=QUERY_CONFIRMED/terminal")
print("pending=QUERY_UNRESOLVED/non-terminal")
print("conflict=QUERY_BLOCKED/non-terminal")
print("inconsistent_initial_and_observed=ValueError")
print("upper_layer_claims=false")

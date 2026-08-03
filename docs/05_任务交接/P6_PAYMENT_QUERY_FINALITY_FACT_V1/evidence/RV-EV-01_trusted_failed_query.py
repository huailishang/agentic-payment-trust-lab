"""Evaluator counterexample for trusted FAILED query finality."""

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
observation = replace(
    scenario.payment_status_observation,
    status=PaymentStatus.FAILED,
)
recovery = assess_payment_recovery(
    scenario.payment_recovery_initial,
    observation,
    mandate=scenario.mandate,
    request=scenario.request,
    order=scenario.final_order,
)
fact = derive_payment_query_finality(
    scenario.payment_recovery_initial,
    observation,
    recovery,
)

print("recovery_status:", recovery.recovery_status.value)
print("effective_status:", fact.effective_status.value)
print("evidence_stage:", fact.evidence_stage.value)
print("effective_status_terminal:", fact.effective_status_terminal)

assert fact.evidence_stage is PaymentQueryEvidenceStage.QUERY_CONFIRMED
assert fact.effective_status_terminal is True

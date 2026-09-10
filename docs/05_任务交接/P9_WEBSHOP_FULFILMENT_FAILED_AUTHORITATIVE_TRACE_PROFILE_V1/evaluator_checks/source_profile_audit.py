from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

PROTECTED = {
    ROOT / "src/agentic_payment_experiment/webshop_sidecar_trace_toolkit.py": "1ccf37b62f6eedc0eff41216ec983ddaea74aed7a0e0529be686f6b15aefbbf3",
    ROOT / "src/agentic_payment_experiment/webshop_payment_sidecar.py": "e74939a0b1da9eba5e70f34ab8f745ac61e8ae2254c2ab823ee92c5299a210c8",
    ROOT / "src/agentic_payment_experiment/payment_recovery.py": "c8c2d7a71b4293105ea2365a7486f143b4ad2f8a9ea10d842bf00dae522107de",
    ROOT / "src/agentic_payment_experiment/payment_finality.py": "b517d00e28d6a018d03f333af2a638ec8b0f95532a819fcad64a415d4018c9a1",
    ROOT / "src/agentic_payment_experiment/payment_status_conflict.py": "75c87e9382f29b045caf987a4d6e92281395748189df505294a210bb1fbbbf4d",
    ROOT / "src/agentic_payment_experiment/lifecycle.py": "8fc6df6f56d5aad47cc9c449340307324150f12760f0a124bd32296a659a4c92",
    ROOT / "src/agentic_payment_experiment/remediation.py": "43a76921fe3058edee4b1778b73949a00dc76a44de08a36f8a3d4e8cdb8c15d3",
    ROOT / "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    ROOT / "src/agentic_payment_experiment/action_origin.py": "95ef06d6d396f9c912f321df907ed198908f629abf93c296ce0f9bf3d68439a6",
    ROOT / "scripts/validation/webshop/run_same_journey_lifecycle_branches.py": "c726ba93fe8840bb698673bd38c7e119c38aebff3110b394c4882da7c2e73898",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_PAYMENT_LIFECYCLE_BRANCH_MEASUREMENT_V1/evaluator_fixtures/LIFECYCLE_BRANCH_MATRIX.json": "c6f6c22c7c2ff637950b2611cb99ef6762f76eff0ee52def90ecf707e6839c7d",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_BASELINE_LIFECYCLE_REPAIR_V1/evidence/SAME_JOURNEY_RESULT.json": "9c611dfe121d970569ea41d1e1831d0f829da307c61a6839996846ca893545fc",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_BASELINE_LIFECYCLE_REPAIR_V1/evaluator_fixtures/SAME_JOURNEY_EXPERIMENT_CONTEXT.json": "6a52d7cb77a1186209a88ab877560a352089b818e8c898977e1e0148dc94b3d1",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_PAYMENT_LIFECYCLE_BRANCH_MEASUREMENT_V1/evaluator_checks/lifecycle_branch_result_audit.py": "34476634b86643c00cbfd456b4386fa4509fad4f48a592c585286c538cac6fc1",
}

PROFILE_FILE = ROOT / "src/agentic_payment_experiment/webshop_sidecar_trace_profiles.py"
FORBIDDEN_PROFILE_TOKENS = (
    "J03",
    "P9-AUTONOMOUS-WEBSHOP-SAME-JOURNEY-PAYMENT-LIFECYCLE-BRANCH-MEASUREMENT-V1",
    "B099231V35",
    "webshop-order-c3345ef469f6d13dab2688e5",
    "webshop-request-096ba6496e0c73b413933ae1",
    "same-journey-payment-webshop-request-096ba6496e0c73b413933ae1",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    for path, expected in PROTECTED.items():
        require(path.is_file(), f"protected file missing: {path}")
        require(sha256(path) == expected, f"protected file changed: {path}")

    text = PROFILE_FILE.read_text(encoding="utf-8")
    for token in FORBIDDEN_PROFILE_TOKENS:
        require(token not in text, f"case-specific token forbidden in profile file: {token}")

    from agentic_payment_experiment.models import (
        FulfillmentStatus,
        PaymentRecoveryStatus,
        PaymentStatus,
        RemediationStatus,
        TaskStatus,
    )
    from agentic_payment_experiment.payment_status_conflict import (
        PaymentStatusConflictResolution,
    )
    from agentic_payment_experiment.webshop_sidecar_trace_profiles import (
        SIDECAR_TRACE_PROFILES,
        SidecarExtensionKind,
        T01_PROFILE,
        T09_PROFILE,
        T12_PROFILE,
    )

    require(type(SIDECAR_TRACE_PROFILES) is tuple, "SIDECAR_TRACE_PROFILES must remain a tuple")
    require(len(SIDECAR_TRACE_PROFILES) == 4, "expected exactly four Sidecar trace profiles")
    require(SIDECAR_TRACE_PROFILES[:3] == (T01_PROFILE, T09_PROFILE, T12_PROFILE), "existing T01/T09/T12 profile order or identity changed")

    require(T01_PROFILE.profile_name == "WEBSHOP_NORMAL_PURCHASE_V2", "T01 profile name changed")
    require(T01_PROFILE.extension_kind is SidecarExtensionKind.FULFILMENT, "T01 extension changed")
    require(T01_PROFILE.initial_payment_status is PaymentStatus.SUCCEEDED, "T01 initial payment changed")
    require(T01_PROFILE.effective_payment_status is PaymentStatus.SUCCEEDED, "T01 effective payment changed")
    require(T01_PROFILE.lifecycle_fulfilment_status is FulfillmentStatus.SUCCEEDED, "T01 fulfillment changed")
    require(T01_PROFILE.lifecycle_task_status is TaskStatus.SUCCEEDED, "T01 task status changed")
    require(T01_PROFILE.remediation_status is RemediationStatus.NOT_REQUIRED, "T01 remediation changed")

    require(T09_PROFILE.profile_name == "WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2", "T09 profile name changed")
    require(T09_PROFILE.extension_kind is SidecarExtensionKind.RECOVERY, "T09 extension changed")
    require(T09_PROFILE.initial_payment_status is PaymentStatus.UNKNOWN, "T09 initial payment changed")
    require(T09_PROFILE.effective_payment_status is PaymentStatus.SUCCEEDED, "T09 effective payment changed")
    require(T09_PROFILE.recovery_status is PaymentRecoveryStatus.RECOVERED, "T09 recovery changed")
    require(T09_PROFILE.lifecycle_task_status is TaskStatus.SUCCEEDED, "T09 task status changed")
    require(T09_PROFILE.remediation_status is RemediationStatus.NOT_REQUIRED, "T09 remediation changed")

    require(T12_PROFILE.profile_name == "WEBSHOP_PAYMENT_STATUS_CONFLICT_V2", "T12 profile name changed")
    require(T12_PROFILE.extension_kind is SidecarExtensionKind.STATUS_CONFLICT, "T12 extension changed")
    require(T12_PROFILE.conflict_resolution is PaymentStatusConflictResolution.CONFLICT, "T12 conflict resolution changed")
    require(T12_PROFILE.lifecycle_payment_status is PaymentStatus.UNKNOWN, "T12 lifecycle payment changed")
    require(T12_PROFILE.lifecycle_task_status is TaskStatus.UNKNOWN, "T12 task status changed")
    require(T12_PROFILE.remediation_status is RemediationStatus.REQUIRED, "T12 remediation changed")

    new_profile = SIDECAR_TRACE_PROFILES[3]
    require(new_profile not in (T01_PROFILE, T09_PROFILE, T12_PROFILE), "fourth profile must be new")
    require(new_profile.extension_kind is SidecarExtensionKind.FULFILMENT, "new profile must use FULFILMENT extension")
    require(new_profile.initial_payment_status is PaymentStatus.SUCCEEDED, "new profile initial payment must be SUCCEEDED")
    require(new_profile.effective_payment_status is PaymentStatus.SUCCEEDED, "new profile effective payment must be SUCCEEDED")
    require(new_profile.recovery_initial_status is None, "new profile must not require recovery")
    require(new_profile.recovery_status is None, "new profile must not require recovery result")
    require(new_profile.conflict_resolution is None, "new profile must not require status conflict")
    require(new_profile.lifecycle_payment_status is PaymentStatus.SUCCEEDED, "new profile lifecycle payment must be SUCCEEDED")
    require(new_profile.lifecycle_fulfilment_status is FulfillmentStatus.FAILED, "new profile fulfillment must be FAILED")
    require(new_profile.lifecycle_task_status is TaskStatus.FAILED, "new profile task status must be FAILED")
    require(new_profile.remediation_status is RemediationStatus.REQUIRED, "new profile remediation must be REQUIRED")

    print("PASS: protected lifecycle/trace/origin code is frozen and exactly one generic failed-fulfilment declarative profile was added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

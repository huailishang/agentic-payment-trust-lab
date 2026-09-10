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
    ROOT / "scripts/validation/webshop/run_same_journey_lifecycle_branches.py": "c726ba93fe8840bb698673bd38c7e119c38aebff3110b394c4882da7c2e73898",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_PAYMENT_LIFECYCLE_BRANCH_MEASUREMENT_V1/evaluator_fixtures/LIFECYCLE_BRANCH_MATRIX.json": "c6f6c22c7c2ff637950b2611cb99ef6762f76eff0ee52def90ecf707e6839c7d",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_BASELINE_LIFECYCLE_REPAIR_V1/evidence/SAME_JOURNEY_RESULT.json": "9c611dfe121d970569ea41d1e1831d0f829da307c61a6839996846ca893545fc",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_BASELINE_LIFECYCLE_REPAIR_V1/evaluator_fixtures/SAME_JOURNEY_EXPERIMENT_CONTEXT.json": "6a52d7cb77a1186209a88ab877560a352089b818e8c898977e1e0148dc94b3d1",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_PAYMENT_LIFECYCLE_BRANCH_MEASUREMENT_V1/evaluator_checks/lifecycle_branch_result_audit.py": "34476634b86643c00cbfd456b4386fa4509fad4f48a592c585286c538cac6fc1",
}

PROFILE_FILE = ROOT / "src/agentic_payment_experiment/webshop_sidecar_trace_profiles.py"
ORIGIN_FILE = ROOT / "src/agentic_payment_experiment/action_origin.py"
FORBIDDEN_TOKENS = (
    "J02",
    "J03",
    "J04",
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

    for path in (PROFILE_FILE, ORIGIN_FILE):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TOKENS:
            require(token not in text, f"case-specific token forbidden in product registry: {path}: {token}")

    from agentic_payment_experiment.models import (
        FulfillmentStatus,
        PaymentRecoveryStatus,
        PaymentStatus,
        RemediationStatus,
        TaskStatus,
    )
    from agentic_payment_experiment.payment_status_conflict import PaymentStatusConflictResolution
    from agentic_payment_experiment.webshop_sidecar_trace_profiles import (
        SIDECAR_TRACE_PROFILES,
        SidecarExtensionKind,
        T01_PROFILE,
        T09_PROFILE,
        T12_PROFILE,
    )
    from agentic_payment_experiment.action_origin import (
        ActionOrigin,
        _TRACE_ORIGIN_BY_EVENT_ROLE,
    )

    require(type(SIDECAR_TRACE_PROFILES) is tuple, "SIDECAR_TRACE_PROFILES must remain tuple")
    require(len(SIDECAR_TRACE_PROFILES) == 4, "expected exactly four trace profiles")
    require(SIDECAR_TRACE_PROFILES[:3] == (T01_PROFILE, T09_PROFILE, T12_PROFILE), "existing T01/T09/T12 profile identity/order changed")

    require(T01_PROFILE.profile_name == "WEBSHOP_NORMAL_PURCHASE_V2", "T01 profile changed")
    require(T01_PROFILE.extension_kind is SidecarExtensionKind.FULFILMENT, "T01 extension changed")
    require(T01_PROFILE.lifecycle_fulfilment_status is FulfillmentStatus.SUCCEEDED, "T01 fulfilment changed")
    require(T01_PROFILE.lifecycle_task_status is TaskStatus.SUCCEEDED, "T01 task status changed")
    require(T01_PROFILE.remediation_status is RemediationStatus.NOT_REQUIRED, "T01 remediation changed")

    require(T09_PROFILE.profile_name == "WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2", "T09 profile changed")
    require(T09_PROFILE.extension_kind is SidecarExtensionKind.RECOVERY, "T09 extension changed")
    require(T09_PROFILE.recovery_status is PaymentRecoveryStatus.RECOVERED, "T09 recovery status changed")
    require(T09_PROFILE.lifecycle_task_status is TaskStatus.SUCCEEDED, "T09 task changed")

    require(T12_PROFILE.profile_name == "WEBSHOP_PAYMENT_STATUS_CONFLICT_V2", "T12 profile changed")
    require(T12_PROFILE.extension_kind is SidecarExtensionKind.STATUS_CONFLICT, "T12 extension changed")
    require(T12_PROFILE.conflict_resolution is PaymentStatusConflictResolution.CONFLICT, "T12 conflict changed")
    require(T12_PROFILE.lifecycle_payment_status is PaymentStatus.UNKNOWN, "T12 payment changed")
    require(T12_PROFILE.lifecycle_task_status is TaskStatus.UNKNOWN, "T12 task changed")
    require(T12_PROFILE.remediation_status is RemediationStatus.REQUIRED, "T12 remediation changed")

    new_profile = SIDECAR_TRACE_PROFILES[3]
    require(new_profile not in (T01_PROFILE, T09_PROFILE, T12_PROFILE), "fourth profile must be new")
    require(new_profile.extension_kind is SidecarExtensionKind.FULFILMENT, "new profile must use FULFILMENT extension")
    require(new_profile.initial_payment_status is PaymentStatus.SUCCEEDED, "new profile initial payment must be SUCCEEDED")
    require(new_profile.effective_payment_status is PaymentStatus.SUCCEEDED, "new profile effective payment must be SUCCEEDED")
    require(new_profile.recovery_initial_status is None and new_profile.recovery_status is None, "new profile must not require recovery")
    require(new_profile.conflict_resolution is None, "new profile must not require conflict")
    require(new_profile.lifecycle_payment_status is PaymentStatus.SUCCEEDED, "new profile lifecycle payment must be SUCCEEDED")
    require(new_profile.lifecycle_fulfilment_status is FulfillmentStatus.FAILED, "new profile fulfilment must be FAILED")
    require(new_profile.lifecycle_task_status is TaskStatus.FAILED, "new profile task must be FAILED")
    require(new_profile.remediation_status is RemediationStatus.REQUIRED, "new profile remediation must be REQUIRED")

    require(tuple(item.value for item in ActionOrigin) == (
        "USER_AUTHORITY",
        "AGENT_DECISION",
        "RUNTIME_DECISION",
        "EXTERNAL_FACT",
        "EXECUTION_RESULT",
    ), "ActionOrigin closed enum changed")

    expected_existing = {
        ("AUTHORITY_RECORDED", "AUTHORITY"): ActionOrigin.USER_AUTHORITY,
        ("ORDER_RECORDED", "AUTHORIZED_ORDER_SNAPSHOT"): ActionOrigin.USER_AUTHORITY,
        ("ORDER_RECORDED", "CURRENT_ORDER_SNAPSHOT"): ActionOrigin.EXTERNAL_FACT,
        ("REQUEST_RECORDED", "CURRENT_REQUEST"): ActionOrigin.EXTERNAL_FACT,
        ("ACTION_RECORDED", "GOVERNED_ACTION"): ActionOrigin.AGENT_DECISION,
        ("PAYMENT_CANDIDATE_RECORDED", "CURRENT_PAYMENT_CANDIDATE"): ActionOrigin.EXTERNAL_FACT,
        ("ACTION_BINDING_DECISION_RECORDED", "ACTION_BINDING_FACT"): ActionOrigin.RUNTIME_DECISION,
        ("RUNTIME_DECISION_RECORDED", "RUNTIME_GATE_OBSERVATION"): ActionOrigin.RUNTIME_DECISION,
        ("PAYMENT_OUTCOME_RECORDED", "PAYMENT_EXECUTION_OUTCOME"): ActionOrigin.EXECUTION_RESULT,
        ("FULFILMENT_OUTCOME_RECORDED", "FULFILMENT_OUTCOME"): ActionOrigin.EXECUTION_RESULT,
        ("RESULT_RECORDED", "FINAL_OUTCOME"): ActionOrigin.EXECUTION_RESULT,
    }
    for key, expected in expected_existing.items():
        require(_TRACE_ORIGIN_BY_EVENT_ROLE.get(key) is expected, f"existing origin mapping changed: {key}")

    require(len(_TRACE_ORIGIN_BY_EVENT_ROLE) == 13, "expected exactly two new origin mappings")
    require(_TRACE_ORIGIN_BY_EVENT_ROLE.get(("RECOVERY_OUTCOME_RECORDED", "RECOVERY_OUTCOME")) is ActionOrigin.EXECUTION_RESULT, "recovery outcome mapping must be EXECUTION_RESULT")
    require(_TRACE_ORIGIN_BY_EVENT_ROLE.get(("STATUS_CONFLICT_RECORDED", "STATUS_CONFLICT_FACT")) is ActionOrigin.EXTERNAL_FACT, "status conflict mapping must be EXTERNAL_FACT")

    print("PASS: lifecycle evidence registry is narrowly extended: one generic failed-fulfilment profile + two existing lifecycle event-role origin mappings; protected business/trace core remains frozen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

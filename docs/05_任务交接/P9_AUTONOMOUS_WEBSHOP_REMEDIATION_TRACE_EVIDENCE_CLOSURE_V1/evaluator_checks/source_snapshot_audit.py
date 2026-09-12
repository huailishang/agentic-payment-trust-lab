from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

PROTECTED = {
    ROOT / "src/agentic_payment_experiment/remediation.py": "43a76921fe3058edee4b1778b73949a00dc76a44de08a36f8a3d4e8cdb8c15d3",
    ROOT / "src/agentic_payment_experiment/lifecycle.py": "8fc6df6f56d5aad47cc9c449340307324150f12760f0a124bd32296a659a4c92",
    ROOT / "src/agentic_payment_experiment/trusted_execution/original_transaction.py": "482b7aa23e07f7724b909ab289928e61f9227f2544611b886e028047d4e9e5d9",
    ROOT / "src/agentic_payment_experiment/webshop_sidecar_trace_toolkit.py": "1ccf37b62f6eedc0eff41216ec983ddaea74aed7a0e0529be686f6b15aefbbf3",
    ROOT / "scripts/validation/webshop/run_same_journey_remediation_closure.py": "5249bc310ecc4b0c4fbf3ff469d009e3048d1e83dfd8f74bb6ec76d08e9ea227",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_REMEDIATION_CLOSURE_MEASUREMENT_V1/evidence/H21_REMEDIATION_CLOSURE_RESULT.json": "9d794317cc77753bb84e6b7b0ec3c6a441ff1d6a632753c782ba556c7fb4f8bb",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_REMEDIATION_CLOSURE_MEASUREMENT_V1/evaluator_fixtures/REMEDIATION_CLOSURE_MATRIX.json": "abe7a75d32d6833f5289160c1477d18b6265aae18476c3e1b509989373f26acc",
    ROOT / "docs/05_任务交接/P9_WEBSHOP_LIFECYCLE_EVIDENCE_CONTINUITY_CLOSURE_V1/evidence/H20_LIFECYCLE_BRANCH_RESULT.json": "312bcef7e3ff4c92b2cf60ed898ac9f4d384ef7cf4639a2a66cce8814e3f3455",
}

PRODUCT_FILES = (
    ROOT / "src/agentic_payment_experiment/webshop_remediation_trace.py",
    ROOT / "src/agentic_payment_experiment/webshop_trace_assembler.py",
    ROOT / "src/agentic_payment_experiment/authoritative_trace.py",
    ROOT / "src/agentic_payment_experiment/action_origin.py",
)

FORBIDDEN_CASE_TOKENS = (
    "R01_FULL_REFUND",
    "R02_PARTIAL_REFUND",
    "R03_DISPUTE_OPEN",
    "R04_DISPUTE_RESOLVED_OUTCOME_UNVERIFIED",
    "R05_REFUND_PAYMENT_BINDING_MISMATCH",
)

EXPECTED_ORIGINS = {
    ("REMEDIATION_OBSERVATION_RECORDED", "REMEDIATION_OBSERVATION"): "EXTERNAL_FACT",
    ("ORIGINAL_TRANSACTION_BINDING_RECORDED", "ORIGINAL_TRANSACTION_BINDING_FACT"): "RUNTIME_DECISION",
    ("REMEDIATION_CLOSURE_RECORDED", "REMEDIATION_CLOSURE_OUTCOME"): "EXECUTION_RESULT",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    for path, expected in PROTECTED.items():
        require(path.is_file(), f"protected file missing: {path}")
        require(sha256(path) == expected, f"protected file changed: {path}")

    extension = PRODUCT_FILES[0]
    require(extension.is_file(), "generic product remediation trace extension is missing")

    for path in PRODUCT_FILES:
        require(path.is_file(), f"expected product file missing: {path}")
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_CASE_TOKENS:
            require(token not in text, f"case-specific product branch forbidden: {path}: {token}")

    from agentic_payment_experiment.action_origin import ActionOrigin, _TRACE_ORIGIN_BY_EVENT_ROLE
    from agentic_payment_experiment.authoritative_trace import PROJECTION_REGISTRY

    require(
        tuple(item.value for item in ActionOrigin)
        == ("USER_AUTHORITY", "AGENT_DECISION", "RUNTIME_DECISION", "EXTERNAL_FACT", "EXECUTION_RESULT"),
        "ActionOrigin closed enum changed",
    )
    require(len(_TRACE_ORIGIN_BY_EVENT_ROLE) == 16, "expected exactly three H-22 origin mappings on top of accepted 13")
    for key, expected_value in EXPECTED_ORIGINS.items():
        origin = _TRACE_ORIGIN_BY_EVENT_ROLE.get(key)
        require(origin is not None, f"missing remediation origin mapping: {key}")
        require(origin.value == expected_value, f"wrong remediation origin mapping: {key} -> {origin.value}")

    projection_source_types = {str(spec["source_object_type"]) for spec in PROJECTION_REGISTRY.values()}
    for source_type in ("RefundRecord", "DisputeRecord", "OriginalTransactionBindingFact", "LifecycleResult"):
        require(source_type in projection_source_types, f"projection registry missing source object type: {source_type}")

    extension_text = extension.read_text(encoding="utf-8")
    for required in ("RefundRecord", "DisputeRecord", "OriginalTransactionBindingFact", "LifecycleResult"):
        require(required in extension_text, f"generic extension does not consume required source type: {required}")

    print(
        "PASS: frozen H-21/business semantics unchanged; one generic remediation trace extension exists; "
        "projection registry covers Refund/Dispute/OriginalTransactionBindingFact/LifecycleResult; "
        "three closed Action Origin mappings are present with no case-specific product branches"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

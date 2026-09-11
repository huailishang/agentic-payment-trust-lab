from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

PROTECTED = {
    ROOT / "docs/05_任务交接/P9_WEBSHOP_LIFECYCLE_EVIDENCE_CONTINUITY_CLOSURE_V1/evidence/H20_LIFECYCLE_BRANCH_RESULT.json": "312bcef7e3ff4c92b2cf60ed898ac9f4d384ef7cf4639a2a66cce8814e3f3455",
    ROOT / "docs/05_任务交接/P9_WEBSHOP_LIFECYCLE_EVIDENCE_CONTINUITY_CLOSURE_V1/REVIEW.md": "3e2a2588574fa610fd8015656b54f052f5ef53dda1cb10d4ab479b6d5980ee10",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_REMEDIATION_CLOSURE_MEASUREMENT_V1/evaluator_fixtures/REMEDIATION_CLOSURE_MATRIX.json": "abe7a75d32d6833f5289160c1477d18b6265aae18476c3e1b509989373f26acc",
    ROOT / "src/agentic_payment_experiment/action_origin.py": "61d87e1e87aee585580c10710e99be566fc7af6d2d1c72545a9b70d83ce8ddd6",
    ROOT / "src/agentic_payment_experiment/webshop_sidecar_trace_profiles.py": "7b9c390059ab11e06ecca2722d19e5284ffe9ec7cbf92c8438c77daf6375942f",
    ROOT / "src/agentic_payment_experiment/remediation.py": "43a76921fe3058edee4b1778b73949a00dc76a44de08a36f8a3d4e8cdb8c15d3",
    ROOT / "src/agentic_payment_experiment/lifecycle.py": "8fc6df6f56d5aad47cc9c449340307324150f12760f0a124bd32296a659a4c92",
    ROOT / "src/agentic_payment_experiment/webshop_payment_sidecar.py": "e74939a0b1da9eba5e70f34ab8f745ac61e8ae2254c2ab823ee92c5299a210c8",
    ROOT / "src/agentic_payment_experiment/payment_recovery.py": "c8c2d7a71b4293105ea2365a7486f143b4ad2f8a9ea10d842bf00dae522107de",
    ROOT / "src/agentic_payment_experiment/payment_finality.py": "b517d00e28d6a018d03f333af2a638ec8b0f95532a819fcad64a415d4018c9a1",
    ROOT / "src/agentic_payment_experiment/payment_status_conflict.py": "75c87e9382f29b045caf987a4d6e92281395748189df505294a210bb1fbbbf4d",
    ROOT / "src/agentic_payment_experiment/webshop_sidecar_trace_toolkit.py": "1ccf37b62f6eedc0eff41216ec983ddaea74aed7a0e0529be686f6b15aefbbf3",
    ROOT / "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
}

RUNNER = ROOT / "scripts/validation/webshop/run_same_journey_remediation_closure.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    for path, expected in PROTECTED.items():
        require(path.is_file(), f"protected file missing: {path}")
        require(sha256(path) == expected, f"protected file changed: {path}")

    require(RUNNER.is_file(), f"measurement runner missing: {RUNNER}")
    text = RUNNER.read_text(encoding="utf-8")

    required_tokens = (
        "assess_remediation",
        "verify_original_transaction",
    )
    for token in required_tokens:
        require(token in text, f"runner must use/declare frozen measurement primitive: {token}")

    forbidden_tokens = (
        "requests.",
        "urllib.request",
        "selenium",
        "playwright",
        "http://",
        "https://",
        "execute_refund",
        "submit_dispute",
        "real_refund",
        "real_payment",
        "R01_FULL_REFUND",
        "R02_PARTIAL_REFUND",
        "R03_DISPUTE_OPEN",
        "R04_DISPUTE_RESOLVED_OUTCOME_UNVERIFIED",
        "R05_REFUND_PAYMENT_BINDING_MISMATCH",
    )
    for token in forbidden_tokens:
        require(token not in text, f"forbidden side-effect or case-specific runner token: {token}")

    # Measurement code may validate/read an existing product trace, but must not
    # manufacture a new authoritative trace or mutate product registries to make
    # remediation evidence appear present.
    forbidden_trace_builders = (
        "build_authoritative_trace(",
        "assemble_authoritative_trace(",
        "SIDECAR_TRACE_PROFILES.append",
        "_TRACE_ORIGIN_BY_EVENT_ROLE[",
    )
    for token in forbidden_trace_builders:
        require(token not in text, f"runner must not manufacture product trace/origin coverage: {token}")

    print(
        "PASS: H-20 parent, remediation/lifecycle/trace/origin product snapshot and H-21 matrix are frozen; runner is local measurement-only and does not manufacture remediation trace coverage"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

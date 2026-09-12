from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

PROTECTED = {
    ROOT / "pyproject.toml": "cd824a63e40ca8a846c250b85e0ef69e8b4874dde4c676b99ac3deaff682a193",
    ROOT / "src/agentic_payment_experiment/adapters/acp.py": "726848d2527da9dc916db20de9c7c08c93cfedc9e20be45a14f3a7c44b3c93dc",
    ROOT / "src/agentic_payment_experiment/adapters/ap2.py": "22325219bdcd02c69bedd26831608d3fe1752b0cc43e1e34a0442ff3a698b867",
    ROOT / "src/agentic_payment_experiment/trusted_execution/execution_facts.py": "cfd1ce9168eafecba894b45d5893be93b8c9e2f9668231a55a35930e23bb2c3c",
    ROOT / "src/agentic_payment_experiment/payment_execution.py": "25113d7c067a6ba43bcae7a182c60ec77404a50229987b0314805b1c10e0ce71",
    ROOT / "scripts/validation/run_actor_authenticity_gap_measurement.py": "217f1d818e58b2e71df63c38598cc8b7171e5aa9268a3d833d11308215536794",
    ROOT / "docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evaluator_fixtures/ACP_WEBHOOK_SIGNATURE_MATRIX.json": "ea9224839b6b183abdf613d5759640ddc21062bd415348f3b7e4f383840d2994",
}

REQUIRED_NEW = (
    ROOT / "src/agentic_payment_experiment/trusted_execution/signed_instruction.py",
    ROOT / "src/agentic_payment_experiment/adapters/acp_webhook.py",
    ROOT / "scripts/validation/run_signed_instruction_verification_capability.py",
    ROOT / "tests/trusted_execution/test_signed_instruction.py",
    ROOT / "tests/test_acp_webhook_signature.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    for path, expected in PROTECTED.items():
        if not path.is_file():
            raise AssertionError(f"protected file missing: {path}")
        actual = sha256(path)
        if actual != expected:
            raise AssertionError(f"protected file changed: {path}: {actual} != {expected}")

    for path in REQUIRED_NEW:
        if not path.is_file():
            raise AssertionError(f"required H-25 implementation file missing: {path}")

    print(
        "PASS: H-24/P3/AP2/ACP checkout baseline and dependency manifest remain frozen; "
        "required H-25 first-consumer files exist"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

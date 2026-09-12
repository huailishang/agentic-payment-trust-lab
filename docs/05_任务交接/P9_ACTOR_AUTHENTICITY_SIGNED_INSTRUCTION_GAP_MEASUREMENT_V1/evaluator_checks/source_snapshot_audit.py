from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

PROTECTED = {
    ROOT / "src/agentic_payment_experiment/trusted_execution/execution_facts.py": "cfd1ce9168eafecba894b45d5893be93b8c9e2f9668231a55a35930e23bb2c3c",
    ROOT / "src/agentic_payment_experiment/payment_execution.py": "25113d7c067a6ba43bcae7a182c60ec77404a50229987b0314805b1c10e0ce71",
    ROOT / "src/agentic_payment_experiment/adapters/ap2.py": "22325219bdcd02c69bedd26831608d3fe1752b0cc43e1e34a0442ff3a698b867",
    ROOT / "src/agentic_payment_experiment/adapters/acp.py": "726848d2527da9dc916db20de9c7c08c93cfedc9e20be45a14f3a7c44b3c93dc",
    ROOT / "tests/trusted_execution/test_identity_assurance.py": "8fd31115603dfe5cb6763d26684bed94a5dd14314a3ff7484e63309879988998",
    ROOT / "tests/test_ap2_flow_adapter.py": "9a821ffca517c73e4148f1f70e0290e08a8dd290cbb71b4d19689a5c1951bda1",
    ROOT / "tests/test_ap2_adapter.py": "162969aaa6c50dddd54e27f4a4aeb273b36bace188db371ba12f60bbcac8324c",
    ROOT / "tests/test_acp_adapter.py": "e6fc93f9f3c83151ea61f27ab2d2e602379b02d598c278f22a30aab1ed081b13",
    ROOT / "samples/protocol_snapshots/AP2_v020_HP_cards.json": "cf7c55e62cb3d8d90861575c9a0a5fba46d75d5ae676cffaa4a9cd16c0aa80c8",
    ROOT / "samples/protocol_snapshots/AP2_v020_HNP_cards.json": "bcd63d8b46263927a8ccb06f30f88580507665db00d054e08fc2876307da6481",
    ROOT / "samples/protocol_snapshots/ACP_S09_order_total_changed.json": "a519a0449295a3bbb2fac5130e9177439bbea64df23b2404fe3db5e7a8b8363a",
    ROOT / "docs/05_任务交接/P9_ACTOR_AUTHENTICITY_SIGNED_INSTRUCTION_GAP_MEASUREMENT_V1/evaluator_fixtures/AUTHENTICITY_GAP_MATRIX.json": "cfa9896d543e9b32c215d7b1d801a15d55ad01bd29bfd15913a6a4cb3212ad17",
}

FORBIDDEN_IMPLEMENTATION_TOKENS = (
    "cryptography",
    "pyjwt",
    "jwcrypto",
    "verify_signature",
    "verify_credential",
    "private_key",
    "privatekey",
    "BEGIN PRIVATE KEY",
    "requests.",
    "httpx.",
    "urllib.request",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    for path, expected in PROTECTED.items():
        if not path.is_file():
            raise AssertionError(f"protected file missing: {path}")
        if sha256(path) != expected:
            raise AssertionError(f"protected file changed: {path}")

    runner = ROOT / "scripts/validation/run_actor_authenticity_gap_measurement.py"
    if not runner.is_file():
        raise AssertionError(f"measurement runner missing: {runner}")
    source = runner.read_text(encoding="utf-8")
    lowered = source.lower()
    for token in FORBIDDEN_IMPLEMENTATION_TOKENS:
        if token.lower() in lowered:
            raise AssertionError(
                f"measurement runner contains forbidden verifier/network implementation token: {token}"
            )

    print(
        "PASS: P3/AP2/ACP products, tests, fixtures, and evaluator matrix remain frozen; "
        "H-24 runner exists without credential/signature verifier or network implementation"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

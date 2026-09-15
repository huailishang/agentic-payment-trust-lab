from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MODULE = ROOT / "src/agentic_payment_experiment/trusted_execution/credential_possession.py"
EXEC = ROOT / "src/agentic_payment_experiment/trusted_execution/execution_facts.py"
PAY = ROOT / "src/agentic_payment_experiment/payment_execution.py"


def main() -> int:
    text = MODULE.read_text(encoding="utf-8")
    lowered = text.lower()
    forbidden = ("decision.allow", "decision.deny", "ap2", "acp", "x402", "order.", "amount", "payee")
    hits = [token for token in forbidden if token in lowered]
    if hits:
        raise AssertionError(f"credential_possession.py crossed protocol/payment boundary: {hits}")
    for required in (
        "CredentialPossessionVerificationFact",
        "verify_x509_svid_credential_possession",
        "credential_valid",
        "subject_binding_valid",
        "proof_of_possession_valid",
        "freshness_valid",
        "replay_detected",
    ):
        if required not in text:
            raise AssertionError(f"missing required protocol-neutral element: {required}")

    exec_text = EXEC.read_text(encoding="utf-8")
    if "credential_possession_fact" not in exec_text or "IdentityAssuranceLevel.VERIFIED" not in exec_text:
        raise AssertionError("P3 promotion wiring missing from execution_facts.py")

    pay_text = PAY.read_text(encoding="utf-8")
    if "credential_possession" not in pay_text:
        raise AssertionError("payment gate does not thread optional P3 credential-possession evidence")
    if "IdentityAssuranceLevel.BOUND" not in pay_text or "IdentityAssuranceLevel.VERIFIED" not in pay_text:
        raise AssertionError("existing BOUND/VERIFIED acceptance boundary unexpectedly changed")

    print("PASS: H-29 stays in identity evidence layer and wires optional evidence into existing P3 without protocol/payment policy leakage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
GENERIC = ROOT / "src/agentic_payment_experiment/trusted_execution/signed_instruction.py"
ADAPTER = ROOT / "src/agentic_payment_experiment/adapters/ap2_signed_instruction.py"


def main() -> int:
    generic = GENERIC.read_text(encoding="utf-8")
    adapter = ADAPTER.read_text(encoding="utf-8")

    required_generic = (
        "verify_es256_compact_jws_signed_instruction",
        "SignedInstructionVerificationFact",
        "cryptography",
    )
    for token in required_generic:
        if token not in generic:
            raise AssertionError(f"generic verifier missing required token: {token}")

    forbidden_generic = (
        "merchant_authorization",
        "cart_hash",
        "CartMandate",
        "PaymentMandate",
        "checkout_hash",
    )
    for token in forbidden_generic:
        if token in generic:
            raise AssertionError(f"AP2-specific token leaked into generic verifier: {token}")

    if "verify_es256_compact_jws_signed_instruction" not in adapter:
        raise AssertionError("AP2 adapter does not consume generic ES256 verifier")

    forbidden_adapter = ("ec.ECDSA", "decode_dss_signature", "encode_dss_signature")
    for token in forbidden_adapter:
        if token in adapter:
            raise AssertionError(f"AP2 adapter duplicates cryptographic verification: {token}")

    print("PASS: generic ES256 verification remains protocol-neutral and AP2 owns only protocol mapping/binding")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

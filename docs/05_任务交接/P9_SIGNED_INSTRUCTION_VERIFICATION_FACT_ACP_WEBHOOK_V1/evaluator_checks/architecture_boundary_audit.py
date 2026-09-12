from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
GENERIC = ROOT / "src/agentic_payment_experiment/trusted_execution/signed_instruction.py"
ACP = ROOT / "src/agentic_payment_experiment/adapters/acp_webhook.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    generic = GENERIC.read_text(encoding="utf-8")
    acp = ACP.read_text(encoding="utf-8")
    generic_lower = generic.lower()
    acp_lower = acp.lower()

    require("compare_digest" in generic, "generic verifier must use constant-time compare_digest")
    require("hmac" in generic_lower and "sha256" in generic_lower, "generic verifier must implement HMAC-SHA256")
    for forbidden in (
        "merchant-signature",
        "merchant_signature",
        "acp",
        "paymentexecutiongateoutcome",
        "decision.allow",
        "decision.deny",
    ):
        require(forbidden not in generic_lower, f"generic verifier leaked protocol/business coupling: {forbidden}")

    require("verify_hmac_sha256_signed_instruction" in acp, "ACP consumer must call generic HMAC verifier")
    require("merchant-signature" in acp_lower or "merchant_signature" in acp_lower, "ACP parser must own Merchant-Signature semantics")
    for forbidden in ("hmac.new", "compare_digest"):
        require(forbidden not in acp_lower, f"ACP adapter duplicated cryptographic comparison: {forbidden}")

    print(
        "PASS: generic Signed Instruction verifier is protocol-neutral and ACP owns only protocol parsing/composition"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

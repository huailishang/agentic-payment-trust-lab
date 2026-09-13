"""Bounded ACP 2026-04-17 webhook signature adapter.

This module owns only ACP-specific Merchant-Signature parsing and signed-byte
composition. Cryptographic comparison and freshness evaluation are delegated to
the protocol-neutral trusted-execution verifier.
"""

from __future__ import annotations

import re

from ..trusted_execution.execution_facts import VerificationStatus
from ..trusted_execution.signed_instruction import (
    HMAC_SHA256_ALGORITHM,
    SignedInstructionVerificationFact,
    verify_hmac_sha256_signed_instruction,
)


ACP_WEBHOOK_DEFAULT_TOLERANCE_SECONDS = 300
_MERCHANT_SIGNATURE_PATTERN = re.compile(
    r"^t=(0|[1-9][0-9]*),v1=([0-9a-fA-F]{64})$"
)


def verify_acp_webhook_signature(
    *,
    raw_body: bytes,
    merchant_signature: str | None,
    secret: bytes,
    observed_at_epoch: int,
    signer_ref: str | None,
    key_ref: str | None,
    max_age_seconds: int = ACP_WEBHOOK_DEFAULT_TOLERANCE_SECONDS,
) -> SignedInstructionVerificationFact:
    """Verify one ACP webhook using the frozen Merchant-Signature contract.

    The accepted header form is exactly ``t=<unix_seconds>,v1=<64_hex>``. Extra,
    duplicate, reordered, or otherwise malformed components fail closed.
    """

    if not isinstance(raw_body, bytes):
        raise TypeError("raw_body must be bytes")
    if not isinstance(secret, bytes):
        raise TypeError("secret must be bytes")

    if merchant_signature is None or merchant_signature == "":
        return SignedInstructionVerificationFact(
            status=VerificationStatus.MISSING_EVIDENCE,
            reason_codes=("signed_instruction_signature_missing",),
            algorithm=HMAC_SHA256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=key_ref,
            signed_payload_sha256=None,
            signed_at_epoch=None,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=max_age_seconds,
            cryptographic_signature_verified=False,
        )

    match = _MERCHANT_SIGNATURE_PATTERN.fullmatch(merchant_signature)
    if match is None:
        return SignedInstructionVerificationFact(
            status=VerificationStatus.INVALID,
            reason_codes=("signed_instruction_signature_format_invalid",),
            algorithm=HMAC_SHA256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=key_ref,
            signed_payload_sha256=None,
            signed_at_epoch=None,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=max_age_seconds,
            cryptographic_signature_verified=False,
        )

    signed_at_epoch = int(match.group(1))
    signature_hex = match.group(2)
    signed_payload = str(signed_at_epoch).encode("ascii") + b"." + raw_body
    return verify_hmac_sha256_signed_instruction(
        signed_payload=signed_payload,
        signature_hex=signature_hex,
        secret=secret,
        signer_ref=signer_ref,
        key_ref=key_ref,
        signed_at_epoch=signed_at_epoch,
        observed_at_epoch=observed_at_epoch,
        max_age_seconds=max_age_seconds,
    )

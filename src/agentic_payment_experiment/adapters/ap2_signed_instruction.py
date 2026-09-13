"""Bounded AP2 merchant-authorization mapping for signed-instruction evidence.

This adapter only maps the frozen AP2 JWT profile into the protocol-neutral
signed-instruction verifier. It does not validate cart/payment business meaning,
complete AP2 conformance, SD-JWT holder binding, or payment authorization.
"""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
import hashlib
import json

from agentic_payment_experiment.trusted_execution.execution_facts import VerificationStatus
from agentic_payment_experiment.trusted_execution.signed_instruction import (
    ES256_ALGORITHM,
    SignedInstructionVerificationFact,
    verify_es256_compact_jws_signed_instruction,
)


def verify_ap2_merchant_authorization_signature(
    *,
    merchant_authorization: str | None,
    public_jwk: Mapping[str, object] | None,
    expected_signer_ref: str,
    expected_key_ref: str,
    observed_at_epoch: int,
) -> SignedInstructionVerificationFact:
    """Verify the frozen AP2 merchant-signed compact JWT profile.

    AP2-shaped claim extraction remains here. Cryptographic verification and
    JOSE key/signature handling are delegated to the generic Trusted Execution
    verifier.
    """

    if merchant_authorization is None or merchant_authorization == "":
        return verify_es256_compact_jws_signed_instruction(
            compact_jws=merchant_authorization,
            public_jwk=public_jwk,
            signer_ref=None,
            expected_signer_ref=expected_signer_ref,
            expected_key_ref=expected_key_ref,
            signed_at_epoch=None,
            expires_at_epoch=None,
            observed_at_epoch=observed_at_epoch,
        )

    claims = _decode_required_claims(merchant_authorization)
    if claims is None:
        return _format_invalid_fact(
            compact_jws=merchant_authorization,
            observed_at_epoch=observed_at_epoch,
            expected_key_ref=expected_key_ref,
        )

    signer_ref, signed_at_epoch, expires_at_epoch = claims
    return verify_es256_compact_jws_signed_instruction(
        compact_jws=merchant_authorization,
        public_jwk=public_jwk,
        signer_ref=signer_ref,
        expected_signer_ref=expected_signer_ref,
        expected_key_ref=expected_key_ref,
        signed_at_epoch=signed_at_epoch,
        expires_at_epoch=expires_at_epoch,
        observed_at_epoch=observed_at_epoch,
    )


def _decode_required_claims(compact_jws: str) -> tuple[str, int, int] | None:
    parts = compact_jws.split(".")
    if len(parts) != 3 or any(part == "" for part in parts):
        return None
    try:
        payload_bytes = _decode_base64url(parts[1])
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, binascii.Error):
        return None
    if not isinstance(payload, dict):
        return None

    issuer = payload.get("iss")
    issued_at = payload.get("iat")
    expires_at = payload.get("exp")
    if not isinstance(issuer, str) or not issuer:
        return None
    if not _is_int_epoch(issued_at) or not _is_int_epoch(expires_at):
        return None
    return issuer, issued_at, expires_at


def _format_invalid_fact(
    *,
    compact_jws: str,
    observed_at_epoch: int,
    expected_key_ref: str,
) -> SignedInstructionVerificationFact:
    signing_input_hash: str | None = None
    parts = compact_jws.split(".")
    if len(parts) == 3 and parts[0] and parts[1]:
        try:
            signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
        except UnicodeEncodeError:
            signing_input = None
        if signing_input is not None:
            signing_input_hash = hashlib.sha256(signing_input).hexdigest()

    return SignedInstructionVerificationFact(
        status=VerificationStatus.INVALID,
        reason_codes=("signed_instruction_compact_jws_format_invalid",),
        algorithm=ES256_ALGORITHM,
        signer_ref=None,
        key_ref=expected_key_ref,
        signed_payload_sha256=signing_input_hash,
        signed_at_epoch=None,
        observed_at_epoch=observed_at_epoch,
        max_age_seconds=0,
        cryptographic_signature_verified=False,
    )


def _decode_base64url(value: str) -> bytes:
    if not value or "=" in value:
        raise ValueError("base64url must be non-empty and unpadded")
    if any(character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for character in value):
        raise ValueError("invalid base64url character")
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.b64decode(value + padding, altchars=b"-_", validate=True)


def _is_int_epoch(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)

"""Protocol-neutral verification facts for signed instructions.

A VALID fact proves only that the supplied verification material matches the
exact signed bytes under the named cryptographic mechanism and that the frozen
time/binding checks passed. It is not a payment authorization, identity proof,
merchant-legitimacy assertion, or regulatory/compliance decision.
"""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import hmac
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

from .execution_facts import VerificationStatus


HMAC_SHA256_ALGORITHM = "HMAC-SHA256"
ES256_ALGORITHM = "ES256"


@dataclass(frozen=True)
class SignedInstructionVerificationFact:
    """Replayable, minimized evidence about one signed-instruction verification."""

    status: VerificationStatus
    reason_codes: tuple[str, ...]
    algorithm: str
    signer_ref: str | None
    key_ref: str | None
    signed_payload_sha256: str | None
    signed_at_epoch: int | None
    observed_at_epoch: int | None
    max_age_seconds: int
    cryptographic_signature_verified: bool


def verify_hmac_sha256_signed_instruction(
    *,
    signed_payload: bytes | None,
    signature_hex: str | None,
    secret: bytes | None,
    signer_ref: str | None,
    key_ref: str | None,
    signed_at_epoch: int | None,
    observed_at_epoch: int | None,
    max_age_seconds: int,
) -> SignedInstructionVerificationFact:
    """Verify HMAC-SHA256 evidence without interpreting protocol/business fields.

    ``signed_payload`` must already be the exact byte sequence defined by the
    calling protocol. The function deliberately accepts only a minimized set of
    verification inputs and never returns the secret, signature, or raw payload.
    Freshness uses an inclusive absolute window: ``abs(observed - signed) <=
    max_age_seconds``.
    """

    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative")

    payload_digest = (
        hashlib.sha256(signed_payload).hexdigest()
        if isinstance(signed_payload, bytes)
        else None
    )

    missing_reasons: list[str] = []
    if signed_payload is None:
        missing_reasons.append("signed_instruction_payload_missing")
    if signature_hex is None or signature_hex == "":
        missing_reasons.append("signed_instruction_signature_missing")
    if secret is None or secret == b"":
        missing_reasons.append("signed_instruction_verification_key_missing")
    if signed_at_epoch is None:
        missing_reasons.append("signed_instruction_signed_at_missing")
    if observed_at_epoch is None:
        missing_reasons.append("signed_instruction_observed_at_missing")
    if missing_reasons:
        return _fact(
            status=VerificationStatus.MISSING_EVIDENCE,
            reason_codes=tuple(missing_reasons),
            algorithm=HMAC_SHA256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=key_ref,
            signed_payload_sha256=payload_digest,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=max_age_seconds,
            cryptographic_signature_verified=False,
        )

    if not _is_sha256_hex(signature_hex):
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("signed_instruction_signature_format_invalid",),
            algorithm=HMAC_SHA256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=key_ref,
            signed_payload_sha256=payload_digest,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=max_age_seconds,
            cryptographic_signature_verified=False,
        )

    assert signed_at_epoch is not None
    assert observed_at_epoch is not None
    assert signed_payload is not None
    assert secret is not None

    if abs(observed_at_epoch - signed_at_epoch) > max_age_seconds:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("signed_instruction_timestamp_outside_window",),
            algorithm=HMAC_SHA256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=key_ref,
            signed_payload_sha256=payload_digest,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=max_age_seconds,
            cryptographic_signature_verified=False,
        )

    expected_signature = hmac.new(secret, signed_payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_signature, signature_hex.lower()):
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("signed_instruction_signature_mismatch",),
            algorithm=HMAC_SHA256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=key_ref,
            signed_payload_sha256=payload_digest,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=max_age_seconds,
            cryptographic_signature_verified=False,
        )

    return _fact(
        status=VerificationStatus.VALID,
        reason_codes=("signed_instruction_signature_valid",),
        algorithm=HMAC_SHA256_ALGORITHM,
        signer_ref=signer_ref,
        key_ref=key_ref,
        signed_payload_sha256=payload_digest,
        signed_at_epoch=signed_at_epoch,
        observed_at_epoch=observed_at_epoch,
        max_age_seconds=max_age_seconds,
        cryptographic_signature_verified=True,
    )


def verify_es256_compact_jws_signed_instruction(
    *,
    compact_jws: str | None,
    public_jwk: Mapping[str, object] | None,
    signer_ref: str | None,
    expected_signer_ref: str | None,
    expected_key_ref: str | None,
    signed_at_epoch: int | None,
    expires_at_epoch: int | None,
    observed_at_epoch: int | None,
) -> SignedInstructionVerificationFact:
    """Verify a compact JWS with ES256/P-256 under protocol-neutral bindings.

    The caller owns protocol-specific claim extraction and supplies only neutral
    signer/time expectations. This function owns compact-JWS structure, JOSE
    ``alg``/``kid`` checks, public-JWK validation, the exact signing-input hash,
    ES256 signature verification, and the inclusive ``iat <= observed <= exp``
    time window. Raw tokens, signatures, payloads, and key coordinates are never
    returned in the fact.
    """

    if compact_jws is None or compact_jws == "":
        return _fact(
            status=VerificationStatus.MISSING_EVIDENCE,
            reason_codes=("signed_instruction_signature_missing",),
            algorithm=ES256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=expected_key_ref,
            signed_payload_sha256=None,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=_safe_window_seconds(signed_at_epoch, expires_at_epoch),
            cryptographic_signature_verified=False,
        )

    parsed = _parse_compact_jws(compact_jws)
    if parsed is None:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("signed_instruction_compact_jws_format_invalid",),
            algorithm=ES256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=expected_key_ref,
            signed_payload_sha256=None,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=_safe_window_seconds(signed_at_epoch, expires_at_epoch),
            cryptographic_signature_verified=False,
        )

    header, signing_input, signature = parsed
    payload_digest = hashlib.sha256(signing_input).hexdigest()
    header_alg = header.get("alg")
    header_kid = header.get("kid")
    key_ref = header_kid if isinstance(header_kid, str) else None

    if header_alg != ES256_ALGORITHM:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("signed_instruction_algorithm_unsupported",),
            algorithm=ES256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=key_ref,
            signed_payload_sha256=payload_digest,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=_safe_window_seconds(signed_at_epoch, expires_at_epoch),
            cryptographic_signature_verified=False,
        )

    if not isinstance(header_kid, str) or not header_kid:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("signed_instruction_key_ref_mismatch",),
            algorithm=ES256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=key_ref,
            signed_payload_sha256=payload_digest,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=_safe_window_seconds(signed_at_epoch, expires_at_epoch),
            cryptographic_signature_verified=False,
        )

    if expected_key_ref is not None and header_kid != expected_key_ref:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("signed_instruction_key_ref_mismatch",),
            algorithm=ES256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=header_kid,
            signed_payload_sha256=payload_digest,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=_safe_window_seconds(signed_at_epoch, expires_at_epoch),
            cryptographic_signature_verified=False,
        )

    if signer_ref is None or signer_ref == "":
        return _fact(
            status=VerificationStatus.MISSING_EVIDENCE,
            reason_codes=("signed_instruction_signer_ref_missing",),
            algorithm=ES256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=header_kid,
            signed_payload_sha256=payload_digest,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=_safe_window_seconds(signed_at_epoch, expires_at_epoch),
            cryptographic_signature_verified=False,
        )

    if expected_signer_ref is not None and signer_ref != expected_signer_ref:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("signed_instruction_signer_mismatch",),
            algorithm=ES256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=header_kid,
            signed_payload_sha256=payload_digest,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=_safe_window_seconds(signed_at_epoch, expires_at_epoch),
            cryptographic_signature_verified=False,
        )

    missing_reasons: list[str] = []
    if signed_at_epoch is None:
        missing_reasons.append("signed_instruction_signed_at_missing")
    if expires_at_epoch is None:
        missing_reasons.append("signed_instruction_expires_at_missing")
    if observed_at_epoch is None:
        missing_reasons.append("signed_instruction_observed_at_missing")
    if public_jwk is None:
        missing_reasons.append("signed_instruction_verification_key_missing")
    if missing_reasons:
        return _fact(
            status=VerificationStatus.MISSING_EVIDENCE,
            reason_codes=tuple(missing_reasons),
            algorithm=ES256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=header_kid,
            signed_payload_sha256=payload_digest,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=_safe_window_seconds(signed_at_epoch, expires_at_epoch),
            cryptographic_signature_verified=False,
        )

    if not _is_epoch_int(signed_at_epoch) or not _is_epoch_int(expires_at_epoch) or not _is_epoch_int(observed_at_epoch):
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("signed_instruction_timestamp_outside_window",),
            algorithm=ES256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=header_kid,
            signed_payload_sha256=payload_digest,
            signed_at_epoch=signed_at_epoch if isinstance(signed_at_epoch, int) else None,
            observed_at_epoch=observed_at_epoch if isinstance(observed_at_epoch, int) else None,
            max_age_seconds=0,
            cryptographic_signature_verified=False,
        )

    assert signed_at_epoch is not None
    assert expires_at_epoch is not None
    assert observed_at_epoch is not None
    assert public_jwk is not None

    max_age_seconds = max(0, expires_at_epoch - signed_at_epoch)
    if expires_at_epoch < signed_at_epoch or not (
        signed_at_epoch <= observed_at_epoch <= expires_at_epoch
    ):
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("signed_instruction_timestamp_outside_window",),
            algorithm=ES256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=header_kid,
            signed_payload_sha256=payload_digest,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=max_age_seconds,
            cryptographic_signature_verified=False,
        )

    public_key = _public_key_from_es256_jwk(public_jwk, expected_key_ref=header_kid)
    if public_key is None:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("signed_instruction_verification_key_invalid",),
            algorithm=ES256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=header_kid,
            signed_payload_sha256=payload_digest,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=max_age_seconds,
            cryptographic_signature_verified=False,
        )

    if len(signature) != 64:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("signed_instruction_compact_jws_format_invalid",),
            algorithm=ES256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=header_kid,
            signed_payload_sha256=payload_digest,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=max_age_seconds,
            cryptographic_signature_verified=False,
        )

    r = int.from_bytes(signature[:32], "big")
    s = int.from_bytes(signature[32:], "big")
    der_signature = encode_dss_signature(r, s)
    try:
        public_key.verify(der_signature, signing_input, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("signed_instruction_signature_mismatch",),
            algorithm=ES256_ALGORITHM,
            signer_ref=signer_ref,
            key_ref=header_kid,
            signed_payload_sha256=payload_digest,
            signed_at_epoch=signed_at_epoch,
            observed_at_epoch=observed_at_epoch,
            max_age_seconds=max_age_seconds,
            cryptographic_signature_verified=False,
        )

    return _fact(
        status=VerificationStatus.VALID,
        reason_codes=("signed_instruction_signature_valid",),
        algorithm=ES256_ALGORITHM,
        signer_ref=signer_ref,
        key_ref=header_kid,
        signed_payload_sha256=payload_digest,
        signed_at_epoch=signed_at_epoch,
        observed_at_epoch=observed_at_epoch,
        max_age_seconds=max_age_seconds,
        cryptographic_signature_verified=True,
    )


def _parse_compact_jws(
    compact_jws: str,
) -> tuple[dict[str, object], bytes, bytes] | None:
    parts = compact_jws.split(".")
    if len(parts) != 3 or any(part == "" for part in parts):
        return None
    header_segment, payload_segment, signature_segment = parts
    try:
        header_bytes = _decode_base64url_segment(header_segment)
        _decode_base64url_segment(payload_segment)
        signature = _decode_base64url_segment(signature_segment)
        header_value = json.loads(header_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, binascii.Error):
        return None
    if not isinstance(header_value, dict):
        return None
    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    return header_value, signing_input, signature


def _public_key_from_es256_jwk(
    jwk: Mapping[str, object],
    *,
    expected_key_ref: str,
) -> ec.EllipticCurvePublicKey | None:
    if jwk.get("kty") != "EC" or jwk.get("crv") != "P-256":
        return None
    if jwk.get("alg") not in (None, ES256_ALGORITHM):
        return None
    if jwk.get("use") not in (None, "sig"):
        return None
    if jwk.get("kid") != expected_key_ref:
        return None

    x_value = jwk.get("x")
    y_value = jwk.get("y")
    if not isinstance(x_value, str) or not isinstance(y_value, str):
        return None
    try:
        x_bytes = _decode_base64url_segment(x_value)
        y_bytes = _decode_base64url_segment(y_value)
    except (ValueError, binascii.Error):
        return None
    if len(x_bytes) != 32 or len(y_bytes) != 32:
        return None

    numbers = ec.EllipticCurvePublicNumbers(
        int.from_bytes(x_bytes, "big"),
        int.from_bytes(y_bytes, "big"),
        ec.SECP256R1(),
    )
    try:
        return numbers.public_key()
    except ValueError:
        return None


def _decode_base64url_segment(value: str) -> bytes:
    if not value or "=" in value:
        raise ValueError("compact JWS/JWK base64url must be non-empty and unpadded")
    if any(character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for character in value):
        raise ValueError("invalid base64url character")
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.b64decode(value + padding, altchars=b"-_", validate=True)


def _safe_window_seconds(signed_at_epoch: int | None, expires_at_epoch: int | None) -> int:
    if not _is_epoch_int(signed_at_epoch) or not _is_epoch_int(expires_at_epoch):
        return 0
    assert signed_at_epoch is not None
    assert expires_at_epoch is not None
    return max(0, expires_at_epoch - signed_at_epoch)


def _is_epoch_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_sha256_hex(value: str) -> bool:
    if len(value) != 64:
        return False
    return all(character in "0123456789abcdefABCDEF" for character in value)


def _fact(
    *,
    status: VerificationStatus,
    reason_codes: tuple[str, ...],
    algorithm: str,
    signer_ref: str | None,
    key_ref: str | None,
    signed_payload_sha256: str | None,
    signed_at_epoch: int | None,
    observed_at_epoch: int | None,
    max_age_seconds: int,
    cryptographic_signature_verified: bool,
) -> SignedInstructionVerificationFact:
    return SignedInstructionVerificationFact(
        status=status,
        reason_codes=reason_codes,
        algorithm=algorithm,
        signer_ref=signer_ref,
        key_ref=key_ref,
        signed_payload_sha256=signed_payload_sha256,
        signed_at_epoch=signed_at_epoch,
        observed_at_epoch=observed_at_epoch,
        max_age_seconds=max_age_seconds,
        cryptographic_signature_verified=cryptographic_signature_verified,
    )

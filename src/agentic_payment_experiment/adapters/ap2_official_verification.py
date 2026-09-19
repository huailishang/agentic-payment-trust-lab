"""Thin optional-dependency bridge to the pinned AP2 v0.2.0 mandate verifier."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib

from ..trusted_execution.execution_facts import VerificationStatus


AP2_V020_PROTOCOL_VERSION = "AP2-v0.2.0"


@dataclass(frozen=True)
class AP2OfficialDelegationVerificationFact:
    """Minimized evidence from the pinned AP2 official two-hop verifier."""

    status: VerificationStatus
    reason_codes: tuple[str, ...]
    protocol_version: str
    token_sha256: str | None
    verified_hop_count: int
    official_verifier_completed: bool
    audience_check_requested: bool
    nonce_check_requested: bool


def verify_ap2_v020_official_two_hop_chain(
    *,
    token: str | None,
    root_public_jwk: Mapping[str, object] | None,
    expected_aud: str | None,
    expected_nonce: str | None,
    current_time: int,
) -> AP2OfficialDelegationVerificationFact:
    """Verify one root + terminal AP2 delegation chain with the official SDK."""

    token_digest = (
        hashlib.sha256(token.encode("utf-8")).hexdigest()
        if isinstance(token, str) and token
        else None
    )
    audience_requested = isinstance(expected_aud, str) and bool(expected_aud)
    nonce_requested = isinstance(expected_nonce, str) and bool(expected_nonce)

    missing_reasons: list[str] = []
    if token is None or token == "":
        missing_reasons.append("ap2_official_token_missing")
    if root_public_jwk is None:
        missing_reasons.append("ap2_official_root_public_jwk_missing")
    if not audience_requested:
        missing_reasons.append("ap2_official_expected_aud_missing")
    if not nonce_requested:
        missing_reasons.append("ap2_official_expected_nonce_missing")
    if missing_reasons:
        return _fact(
            status=VerificationStatus.MISSING_EVIDENCE,
            reason_codes=tuple(missing_reasons),
            token_sha256=token_digest,
            verified_hop_count=0,
            official_verifier_completed=False,
            audience_check_requested=audience_requested,
            nonce_check_requested=nonce_requested,
        )

    if isinstance(current_time, bool) or not isinstance(current_time, int):
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("ap2_official_current_time_invalid",),
            token_sha256=token_digest,
            verified_hop_count=0,
            official_verifier_completed=False,
            audience_check_requested=True,
            nonce_check_requested=True,
        )

    assert token is not None
    assert root_public_jwk is not None
    assert expected_aud is not None
    assert expected_nonce is not None

    if len(token.split("~~")) != 2:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("ap2_official_two_hop_shape_invalid",),
            token_sha256=token_digest,
            verified_hop_count=0,
            official_verifier_completed=False,
            audience_check_requested=True,
            nonce_check_requested=True,
        )

    try:
        from ap2.sdk.mandate import MandateClient
        from jwcrypto.jwk import JWK
    except (ImportError, ModuleNotFoundError):
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("ap2_official_verifier_unavailable",),
            token_sha256=token_digest,
            verified_hop_count=0,
            official_verifier_completed=False,
            audience_check_requested=True,
            nonce_check_requested=True,
        )

    try:
        root_key = JWK(**dict(root_public_jwk))
    except Exception:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("ap2_official_root_public_jwk_invalid",),
            token_sha256=token_digest,
            verified_hop_count=0,
            official_verifier_completed=False,
            audience_check_requested=True,
            nonce_check_requested=True,
        )

    def root_key_provider(_parsed_token: object):
        return root_key

    try:
        verified_payloads = MandateClient().verify(
            token,
            root_key_provider,
            expected_aud=expected_aud,
            expected_nonce=expected_nonce,
            current_time=current_time,
        )
    except Exception:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("ap2_official_verification_failed",),
            token_sha256=token_digest,
            verified_hop_count=0,
            official_verifier_completed=False,
            audience_check_requested=True,
            nonce_check_requested=True,
        )

    if not isinstance(verified_payloads, list) or len(verified_payloads) != 2:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("ap2_official_two_hop_result_invalid",),
            token_sha256=token_digest,
            verified_hop_count=0,
            official_verifier_completed=False,
            audience_check_requested=True,
            nonce_check_requested=True,
        )

    return _fact(
        status=VerificationStatus.VALID,
        reason_codes=("ap2_official_two_hop_verified",),
        token_sha256=token_digest,
        verified_hop_count=2,
        official_verifier_completed=True,
        audience_check_requested=True,
        nonce_check_requested=True,
    )


def _fact(
    *,
    status: VerificationStatus,
    reason_codes: tuple[str, ...],
    token_sha256: str | None,
    verified_hop_count: int,
    official_verifier_completed: bool,
    audience_check_requested: bool,
    nonce_check_requested: bool,
) -> AP2OfficialDelegationVerificationFact:
    return AP2OfficialDelegationVerificationFact(
        status=status,
        reason_codes=reason_codes,
        protocol_version=AP2_V020_PROTOCOL_VERSION,
        token_sha256=token_sha256,
        verified_hop_count=verified_hop_count,
        official_verifier_completed=official_verifier_completed,
        audience_check_requested=audience_check_requested,
        nonce_check_requested=nonce_check_requested,
    )

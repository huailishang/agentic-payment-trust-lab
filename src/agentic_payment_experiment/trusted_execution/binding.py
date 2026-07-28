"""Protocol-neutral object-binding verification facts.

Binding verification reports whether an actual object reproduces an expected
canonical digest. It deliberately does not map the fact to payment decisions.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .hashing import canonical_hash


class BindingStatus(str, Enum):
    """Deterministic status returned by the trusted-execution binding check."""

    VALID = "VALID"
    INVALID = "INVALID"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"


@dataclass(frozen=True)
class BindingResult:
    """Verification fact for one expected digest and one actual object."""

    status: BindingStatus
    reason_code: str
    expected_digest: str | None
    actual_digest: str | None
    algorithm: str = "sha256"


def verify_binding(
    expected_digest: str | None,
    actual_object: Any | None,
    *,
    algorithm: str = "sha256",
) -> BindingResult:
    """Compare *actual_object* with an expected canonical digest.

    ``VALID`` means the canonical digest matches. ``INVALID`` means both pieces
    of evidence are present but the digests differ. ``MISSING_EVIDENCE`` means
    the expected digest is absent/malformed, the actual object is absent, or the
    actual object cannot satisfy the canonicalization contract.

    The caller remains responsible for all business decisions.
    """

    digest_size = _digest_size(algorithm)
    normalized_expected = _normalize_expected_digest(expected_digest, digest_size)
    if normalized_expected is None:
        reason = "expected_digest_missing" if not str(expected_digest or "").strip() else "expected_digest_invalid"
        return BindingResult(
            status=BindingStatus.MISSING_EVIDENCE,
            reason_code=reason,
            expected_digest=None,
            actual_digest=None,
            algorithm=algorithm,
        )

    if actual_object is None:
        return BindingResult(
            status=BindingStatus.MISSING_EVIDENCE,
            reason_code="actual_object_missing",
            expected_digest=normalized_expected,
            actual_digest=None,
            algorithm=algorithm,
        )

    try:
        actual_digest = canonical_hash(actual_object, algorithm=algorithm)
    except (TypeError, ValueError):
        return BindingResult(
            status=BindingStatus.MISSING_EVIDENCE,
            reason_code="actual_object_not_canonicalizable",
            expected_digest=normalized_expected,
            actual_digest=None,
            algorithm=algorithm,
        )

    matches = hmac.compare_digest(normalized_expected, actual_digest.lower())
    return BindingResult(
        status=BindingStatus.VALID if matches else BindingStatus.INVALID,
        reason_code="binding_match" if matches else "binding_mismatch",
        expected_digest=normalized_expected,
        actual_digest=actual_digest,
        algorithm=algorithm,
    )


def _digest_size(algorithm: str) -> int:
    try:
        return hashlib.new(algorithm).digest_size
    except ValueError as exc:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from exc


def _normalize_expected_digest(value: str | None, digest_size: int) -> str | None:
    text = str(value or "").strip().lower()
    if len(text) != digest_size * 2:
        return None
    try:
        int(text, 16)
    except ValueError:
        return None
    return text

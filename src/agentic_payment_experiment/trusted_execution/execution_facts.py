"""Protocol-neutral execution, observation, and idempotency verification facts.

These helpers expose deterministic relationships between references. They do not
choose payment recovery actions, retries, refunds, or other business outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VerificationStatus(str, Enum):
    """Whether the supplied evidence is sufficient and internally consistent."""

    VALID = "VALID"
    INVALID = "INVALID"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"


@dataclass(frozen=True)
class VerificationResult:
    """Deterministic result for one reference-consistency check."""

    status: VerificationStatus
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionAttemptFact:
    """Minimal protocol-neutral view of one execution attempt."""

    execution_id: str
    request_id: str
    status: str
    idempotency_key: str | None = None


@dataclass(frozen=True)
class IdempotencyFact:
    """Evidence inventory for one request's idempotency boundary.

    ``VALID`` only means an explicit idempotency key is present. It does not mean
    a retry is safe. Related attempts and their statuses remain facts for the
    payment domain to interpret.
    """

    status: VerificationStatus
    reason_code: str
    idempotency_key: str | None
    related_attempts: tuple[ExecutionAttemptFact, ...]
    same_key_execution_ids: tuple[str, ...]
    different_key_execution_ids: tuple[str, ...]


def verify_declared_identity_binding(
    *,
    expected_identity_id: str | None,
    actual_identity_id: str | None,
) -> VerificationResult:
    """Compare two declared identity references without claiming authentication.

    A matching identifier only proves that two supplied references are equal. It
    does not prove identity proofing, possession of an authenticator, credential
    validity, federation assurance, or control of the represented agent.
    """

    expected = str(expected_identity_id or "").strip()
    actual = str(actual_identity_id or "").strip()
    if not expected or not actual:
        return VerificationResult(
            status=VerificationStatus.MISSING_EVIDENCE,
            reason_codes=("declared_identity_reference_missing",),
        )
    if expected != actual:
        return VerificationResult(
            status=VerificationStatus.INVALID,
            reason_codes=("declared_identity_reference_mismatch",),
        )
    return VerificationResult(
        status=VerificationStatus.VALID,
        reason_codes=("declared_identity_reference_match",),
    )


def verify_execution_identity(
    *,
    expected_execution_id: str,
    actual_execution_id: str,
    expected_object_id: str,
    actual_object_id: str,
    expected_provider_ref: str | None = None,
    actual_provider_ref: str | None = None,
) -> VerificationResult:
    """Verify deterministic execution/object/provider reference relationships."""

    required = (
        expected_execution_id,
        actual_execution_id,
        expected_object_id,
        actual_object_id,
    )
    if any(not str(value).strip() for value in required):
        return VerificationResult(
            status=VerificationStatus.MISSING_EVIDENCE,
            reason_codes=("required_execution_reference_missing",),
        )

    reasons: list[str] = []
    if actual_execution_id != expected_execution_id:
        reasons.append("execution_reference_mismatch")
    if actual_object_id != expected_object_id:
        reasons.append("object_reference_mismatch")
    if (
        expected_provider_ref
        and actual_provider_ref
        and actual_provider_ref != expected_provider_ref
    ):
        reasons.append("provider_reference_mismatch")

    if reasons:
        return VerificationResult(
            status=VerificationStatus.INVALID,
            reason_codes=tuple(reasons),
        )

    return VerificationResult(
        status=VerificationStatus.VALID,
        reason_codes=("execution_identity_match",),
    )


def validate_status_observation(
    *,
    expected_execution_id: str,
    observed_execution_id: str,
    expected_object_id: str,
    observed_object_id: str,
    expected_provider_ref: str | None = None,
    observed_provider_ref: str | None = None,
) -> VerificationResult:
    """Validate that a status observation belongs to the expected execution.

    Status semantics are intentionally outside this helper. This function only
    validates the references that bind an observation to an execution.
    """

    return verify_execution_identity(
        expected_execution_id=expected_execution_id,
        actual_execution_id=observed_execution_id,
        expected_object_id=expected_object_id,
        actual_object_id=observed_object_id,
        expected_provider_ref=expected_provider_ref,
        actual_provider_ref=observed_provider_ref,
    )


def check_idempotency(
    *,
    idempotency_key: str | None,
    request_id: str,
    current_execution_id: str,
    known_attempts: tuple[ExecutionAttemptFact, ...] = (),
) -> IdempotencyFact:
    """Inventory the idempotency boundary and related execution attempts.

    This helper does not decide whether any related status permits a retry. It
    identifies the attempts for the same business request and whether they use
    the same explicit key, a different key, or no key.
    """

    normalized_key = str(idempotency_key or "").strip() or None
    related = tuple(
        attempt
        for attempt in known_attempts
        if attempt.request_id == request_id and attempt.execution_id != current_execution_id
    )

    same_key_ids: list[str] = []
    different_key_ids: list[str] = []
    if normalized_key is not None:
        for attempt in related:
            attempt_key = str(attempt.idempotency_key or "").strip() or None
            if attempt_key == normalized_key:
                same_key_ids.append(attempt.execution_id)
            else:
                different_key_ids.append(attempt.execution_id)

    if normalized_key is None:
        return IdempotencyFact(
            status=VerificationStatus.MISSING_EVIDENCE,
            reason_code="idempotency_key_missing",
            idempotency_key=None,
            related_attempts=related,
            same_key_execution_ids=(),
            different_key_execution_ids=tuple(attempt.execution_id for attempt in related),
        )

    return IdempotencyFact(
        status=VerificationStatus.VALID,
        reason_code="idempotency_boundary_present",
        idempotency_key=normalized_key,
        related_attempts=related,
        same_key_execution_ids=tuple(same_key_ids),
        different_key_execution_ids=tuple(different_key_ids),
    )

"""Protocol-neutral execution, observation, and idempotency verification facts.

These helpers expose deterministic relationships between references. They do not
choose payment recovery actions, retries, refunds, or other business outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class VerificationStatus(str, Enum):
    """Whether the supplied evidence is sufficient and internally consistent."""

    VALID = "VALID"
    INVALID = "INVALID"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"


class IdentityAssuranceLevel(str, Enum):
    """Strength of the evidence relating an Agent reference to an executor."""

    DECLARED = "DECLARED"
    BOUND = "BOUND"
    VERIFIED = "VERIFIED"


@dataclass(frozen=True)
class VerificationResult:
    """Deterministic result for one reference-consistency check."""

    status: VerificationStatus
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class IdentityAssuranceFact:
    """Replayable P3 identity fact, not an authentication assertion.

    ``VERIFIED`` is reserved for a future explicit credential verifier or
    provider attestation. The deterministic offline verifier in this module can
    produce at most ``BOUND``.
    """

    status: VerificationStatus
    reason_codes: tuple[str, ...]
    assurance_level: IdentityAssuranceLevel
    authorized_agent_ref: str | None
    request_agent_ref: str | None
    execution_agent_ref: str | None
    identity_agent_ref: str | None
    identity_provider_ref: str | None
    identity_executor_instance_ref: str | None
    identity_credential_ref: str | None
    provider_ref: str | None
    executor_instance_ref: str | None
    credential_ref: str | None
    credential_available: bool


class _AgentIdentityLike(Protocol):
    agent_id: str
    provider: str
    executor_instance_id: str | None
    status: str
    credential_ref: str | None


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


def verify_agent_executor_identity(
    *,
    authorized_agent_ref: str | None,
    request_agent_ref: str | None,
    execution_agent_ref: str | None,
    identity: _AgentIdentityLike | None,
    current_provider_ref: str | None,
    current_executor_instance_ref: str | None,
    current_credential_ref: str | None = None,
) -> IdentityAssuranceFact:
    """Verify deterministic Agent/executor binding without authenticating it.

    The supplied identity object is the expected offline binding record. Current
    provider, executor, and optional credential references are observations made
    at the payment gate. Matching references can establish ``BOUND`` only; this
    function has no credential-validity, possession, attestation, PKI, or
    federation verifier and therefore never emits ``VERIFIED``.
    """

    identity_agent_ref = identity.agent_id if identity is not None else None
    identity_provider_ref = identity.provider if identity is not None else None
    identity_executor_ref = (
        identity.executor_instance_id if identity is not None else None
    )
    identity_credential_ref = identity.credential_ref if identity is not None else None
    identity_status = identity.status if identity is not None else None

    missing_reasons = tuple(
        reason
        for value, reason in (
            (authorized_agent_ref, "identity_authorized_agent_ref_missing"),
            (request_agent_ref, "identity_request_agent_ref_missing"),
            (execution_agent_ref, "identity_execution_agent_ref_missing"),
            (identity_agent_ref, "identity_object_agent_ref_missing"),
            (identity_provider_ref, "identity_provider_ref_missing"),
            (identity_executor_ref, "identity_expected_executor_ref_missing"),
            (identity_status, "identity_status_missing"),
            (current_provider_ref, "identity_current_provider_ref_missing"),
            (
                current_executor_instance_ref,
                "identity_current_executor_ref_missing",
            ),
        )
        if not _normalized_ref(value)
    )
    if missing_reasons:
        return _identity_fact(
            status=VerificationStatus.MISSING_EVIDENCE,
            reason_codes=missing_reasons,
            assurance_level=IdentityAssuranceLevel.DECLARED,
            authorized_agent_ref=authorized_agent_ref,
            request_agent_ref=request_agent_ref,
            execution_agent_ref=execution_agent_ref,
            identity=identity,
            current_provider_ref=current_provider_ref,
            current_executor_instance_ref=current_executor_instance_ref,
            current_credential_ref=current_credential_ref,
        )

    normalized_status = _normalized_ref(identity_status).lower()
    reasons: list[str] = []
    checks = (
        (
            request_agent_ref != authorized_agent_ref,
            "identity_request_agent_ref_mismatch",
        ),
        (
            execution_agent_ref != authorized_agent_ref,
            "identity_execution_agent_ref_mismatch",
        ),
        (
            identity_agent_ref != authorized_agent_ref,
            "identity_object_agent_ref_mismatch",
        ),
        (
            current_provider_ref != identity_provider_ref,
            "identity_provider_ref_mismatch",
        ),
        (
            current_executor_instance_ref != identity_executor_ref,
            "identity_executor_instance_ref_mismatch",
        ),
        (
            bool(
                _normalized_ref(identity_credential_ref)
                and _normalized_ref(current_credential_ref)
            )
            and current_credential_ref != identity_credential_ref,
            "identity_credential_ref_mismatch",
        ),
        (
            normalized_status == "inactive",
            "identity_status_inactive",
        ),
        (
            normalized_status == "revoked",
            "identity_status_revoked",
        ),
        (
            normalized_status not in {"active", "inactive", "revoked"},
            "identity_status_unsupported",
        ),
    )
    reasons.extend(reason for failed, reason in checks if failed)
    if reasons:
        return _identity_fact(
            status=VerificationStatus.INVALID,
            reason_codes=tuple(reasons),
            assurance_level=IdentityAssuranceLevel.DECLARED,
            authorized_agent_ref=authorized_agent_ref,
            request_agent_ref=request_agent_ref,
            execution_agent_ref=execution_agent_ref,
            identity=identity,
            current_provider_ref=current_provider_ref,
            current_executor_instance_ref=current_executor_instance_ref,
            current_credential_ref=current_credential_ref,
        )

    return _identity_fact(
        status=VerificationStatus.VALID,
        reason_codes=("identity_executor_binding_match",),
        assurance_level=IdentityAssuranceLevel.BOUND,
        authorized_agent_ref=authorized_agent_ref,
        request_agent_ref=request_agent_ref,
        execution_agent_ref=execution_agent_ref,
        identity=identity,
        current_provider_ref=current_provider_ref,
        current_executor_instance_ref=current_executor_instance_ref,
        current_credential_ref=current_credential_ref,
    )


def _identity_fact(
    *,
    status: VerificationStatus,
    reason_codes: tuple[str, ...],
    assurance_level: IdentityAssuranceLevel,
    authorized_agent_ref: str | None,
    request_agent_ref: str | None,
    execution_agent_ref: str | None,
    identity: _AgentIdentityLike | None,
    current_provider_ref: str | None,
    current_executor_instance_ref: str | None,
    current_credential_ref: str | None,
) -> IdentityAssuranceFact:
    return IdentityAssuranceFact(
        status=status,
        reason_codes=reason_codes,
        assurance_level=assurance_level,
        authorized_agent_ref=_optional_ref(authorized_agent_ref),
        request_agent_ref=_optional_ref(request_agent_ref),
        execution_agent_ref=_optional_ref(execution_agent_ref),
        identity_agent_ref=(
            _optional_ref(identity.agent_id) if identity is not None else None
        ),
        identity_provider_ref=(
            _optional_ref(identity.provider) if identity is not None else None
        ),
        identity_executor_instance_ref=(
            _optional_ref(identity.executor_instance_id)
            if identity is not None
            else None
        ),
        identity_credential_ref=(
            _optional_ref(identity.credential_ref) if identity is not None else None
        ),
        provider_ref=_optional_ref(current_provider_ref),
        executor_instance_ref=_optional_ref(current_executor_instance_ref),
        credential_ref=_optional_ref(current_credential_ref),
        credential_available=bool(_normalized_ref(current_credential_ref)),
    )


def _normalized_ref(value: object | None) -> str:
    return str(value or "").strip()


def _optional_ref(value: object | None) -> str | None:
    normalized = _normalized_ref(value)
    return normalized or None


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

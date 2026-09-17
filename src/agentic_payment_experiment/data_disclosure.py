"""Protocol-neutral field-name data minimization facts.

This module reasons only about field identifiers. It does not inspect, retain,
redact, classify, or otherwise process personal-data values.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .trusted_execution.execution_facts import VerificationStatus


@dataclass(frozen=True)
class DataDisclosureFact:
    """Deterministic disclosure decision over field identifiers only."""

    status: VerificationStatus
    reason_codes: tuple[str, ...]
    required_fields: tuple[str, ...]
    allowed_fields: tuple[str, ...]
    requested_fields: tuple[str, ...]
    approved_fields: tuple[str, ...]
    blocked_fields: tuple[str, ...]


def evaluate_data_disclosure(
    required_fields: Iterable[str],
    allowed_fields: Iterable[str],
    requested_fields: Iterable[str],
) -> DataDisclosureFact:
    """Evaluate whether requested fields are both necessary and policy-allowed.

    A valid fact approves only ``required ∩ allowed ∩ requested``. Optional
    requested fields are blocked without rejecting the whole operation when all
    required fields remain available. Missing or disallowed required fields, or
    malformed field evidence, fail closed and approve nothing.
    """

    required, required_valid = _normalize_fields(required_fields)
    allowed, allowed_valid = _normalize_fields(allowed_fields)
    requested, requested_valid = _normalize_fields(requested_fields)

    if not (required_valid and allowed_valid and requested_valid) or not required:
        return DataDisclosureFact(
            status=VerificationStatus.INVALID,
            reason_codes=("data_disclosure_invalid_evidence",),
            required_fields=required,
            allowed_fields=allowed,
            requested_fields=requested,
            approved_fields=(),
            blocked_fields=requested,
        )

    required_set = set(required)
    allowed_set = set(allowed)
    requested_set = set(requested)

    missing_required = tuple(field for field in required if field not in requested_set)
    disallowed_required = tuple(field for field in required if field not in allowed_set)

    if missing_required or disallowed_required:
        reasons: list[str] = []
        if missing_required:
            reasons.append("data_disclosure_required_field_missing")
        if disallowed_required:
            reasons.append("data_disclosure_required_field_not_allowed")
        return DataDisclosureFact(
            status=VerificationStatus.INVALID,
            reason_codes=tuple(reasons),
            required_fields=required,
            allowed_fields=allowed,
            requested_fields=requested,
            approved_fields=(),
            blocked_fields=requested,
        )

    approved = tuple(
        field
        for field in requested
        if field in required_set and field in allowed_set
    )
    blocked = tuple(field for field in requested if field not in approved)
    nonessential_blocked = tuple(field for field in blocked if field not in required_set)

    reasons = ["data_disclosure_minimized"]
    if nonessential_blocked:
        reasons.append("data_disclosure_nonessential_field_blocked")

    return DataDisclosureFact(
        status=VerificationStatus.VALID,
        reason_codes=tuple(reasons),
        required_fields=required,
        allowed_fields=allowed,
        requested_fields=requested,
        approved_fields=approved,
        blocked_fields=blocked,
    )


def _normalize_fields(fields: Iterable[str]) -> tuple[tuple[str, ...], bool]:
    if isinstance(fields, (str, bytes)):
        return (), False

    try:
        raw_fields = tuple(fields)
    except TypeError:
        return (), False

    normalized: list[str] = []
    seen: set[str] = set()
    for field in raw_fields:
        if not isinstance(field, str) or not field or field != field.strip():
            return (), False
        if any(char.isspace() for char in field):
            return (), False
        if field not in seen:
            normalized.append(field)
            seen.add(field)
    return tuple(normalized), True

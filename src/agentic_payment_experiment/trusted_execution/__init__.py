"""Protocol-neutral trusted-execution primitives used by the payment experiment.

This package returns deterministic verification facts. It must not define payment
business decisions such as ALLOW, DENY, CONFIRMATION_REQUIRED, refunds, disputes,
or lifecycle policy.
"""

from .binding import BindingResult, BindingStatus, verify_binding
from .execution_facts import (
    ExecutionAttemptFact,
    IdempotencyFact,
    VerificationResult,
    VerificationStatus,
    check_idempotency,
    validate_status_observation,
    verify_declared_identity_binding,
    verify_execution_identity,
)
from .hashing import canonical_hash, canonical_json, canonicalize, verify_hash

__all__ = [
    "BindingResult",
    "BindingStatus",
    "ExecutionAttemptFact",
    "IdempotencyFact",
    "VerificationResult",
    "VerificationStatus",
    "canonicalize",
    "canonical_json",
    "canonical_hash",
    "check_idempotency",
    "validate_status_observation",
    "verify_binding",
    "verify_declared_identity_binding",
    "verify_execution_identity",
    "verify_hash",
]

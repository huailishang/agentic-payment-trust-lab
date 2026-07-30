"""Protocol-neutral trusted-execution primitives used by the payment experiment.

This package returns deterministic verification facts. It must not define payment
business decisions such as ALLOW, DENY, CONFIRMATION_REQUIRED, refunds, disputes,
or lifecycle policy.
"""

from .binding import BindingResult, BindingStatus, verify_binding
from .confirmation import (
    ConfirmationBindingFact,
    ConfirmationRecord,
    ConfirmationStatus,
    PaymentGateOutcome,
    confirmation_order_payload,
    create_confirmation_record,
    execute_with_confirmation_gate,
    verify_confirmation_binding,
)
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
    "ConfirmationBindingFact",
    "ConfirmationRecord",
    "ConfirmationStatus",
    "PaymentGateOutcome",
    "ExecutionAttemptFact",
    "IdempotencyFact",
    "VerificationResult",
    "VerificationStatus",
    "canonicalize",
    "canonical_json",
    "canonical_hash",
    "confirmation_order_payload",
    "create_confirmation_record",
    "execute_with_confirmation_gate",
    "check_idempotency",
    "validate_status_observation",
    "verify_binding",
    "verify_confirmation_binding",
    "verify_declared_identity_binding",
    "verify_execution_identity",
    "verify_hash",
]

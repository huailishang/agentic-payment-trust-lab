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
from .context_policy import (
    POLICY_VERSION,
    CandidateFactUpdate,
    ContextPolicyFact,
    ContextPolicyResult,
    FactDomain,
    SourceType,
    evaluate_context_policy,
    infer_fact_domain,
    missing_context_policy_fact,
)
from .execution_facts import (
    ExecutionAttemptFact,
    IdempotencyFact,
    IdentityAssuranceFact,
    IdentityAssuranceLevel,
    VerificationResult,
    VerificationStatus,
    check_idempotency,
    validate_status_observation,
    verify_agent_executor_identity,
    verify_declared_identity_binding,
    verify_execution_identity,
)
from .hashing import canonical_hash, canonical_json, canonicalize, verify_hash
from .payment_binding import (
    PaymentExecutionBindingFact,
    verify_payment_execution_binding,
)

__all__ = [
    "BindingResult",
    "BindingStatus",
    "ConfirmationBindingFact",
    "ConfirmationRecord",
    "ConfirmationStatus",
    "PaymentGateOutcome",
    "PaymentExecutionBindingFact",
    "CandidateFactUpdate",
    "ContextPolicyFact",
    "ContextPolicyResult",
    "ExecutionAttemptFact",
    "IdempotencyFact",
    "IdentityAssuranceFact",
    "IdentityAssuranceLevel",
    "FactDomain",
    "SourceType",
    "POLICY_VERSION",
    "VerificationResult",
    "VerificationStatus",
    "canonicalize",
    "canonical_json",
    "canonical_hash",
    "confirmation_order_payload",
    "create_confirmation_record",
    "execute_with_confirmation_gate",
    "evaluate_context_policy",
    "check_idempotency",
    "validate_status_observation",
    "verify_agent_executor_identity",
    "verify_binding",
    "verify_confirmation_binding",
    "verify_declared_identity_binding",
    "verify_execution_identity",
    "verify_hash",
    "infer_fact_domain",
    "missing_context_policy_fact",
    "verify_payment_execution_binding",
]

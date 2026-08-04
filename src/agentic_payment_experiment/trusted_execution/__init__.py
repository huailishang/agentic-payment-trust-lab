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
    SourceCoverage,
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
from .fact_lineage import (
    FactLineageNode,
    FactLineageResult,
    ResolvedFactLineage,
    resolve_fact_lineage,
)
from .governed_action import (
    ActionReversibility,
    GovernedActionBindingFact,
    GovernedActionType,
    GovernedPaymentAction,
    SideEffectClass,
    verify_governed_payment_action,
)
from .hashing import canonical_hash, canonical_json, canonicalize, verify_hash
from .known_payment_attempt import (
    KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_LIMITATIONS,
    KnownPaymentAttemptPreflightFact,
    KnownPaymentAttemptPreflightStatus,
    derive_known_payment_attempt_preflight,
)
from .payment_binding import (
    PaymentExecutionBindingFact,
    verify_payment_execution_binding,
)
from .original_transaction import FollowUpAction, OriginalTransactionBindingFact, verify_original_transaction
from .replay import (
    ReplayEvent,
    ReplayEventType,
    ReplayResult,
    ReplaySourceType,
    ReplayStatus,
    RuntimeGateRecord,
    replay_events,
)

__all__ = [
    "ResolvedFactLineage",
    "FactLineageResult",
    "FactLineageNode",
    "SideEffectClass",
    "GovernedPaymentAction",
    "GovernedActionType",
    "GovernedActionBindingFact",
    "ActionReversibility",
    "BindingResult",
    "BindingStatus",
    "KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_LIMITATIONS",
    "KnownPaymentAttemptPreflightFact",
    "KnownPaymentAttemptPreflightStatus",
    "ConfirmationBindingFact",
    "ConfirmationRecord",
    "ConfirmationStatus",
    "PaymentGateOutcome",
    "PaymentExecutionBindingFact",
    "FollowUpAction",
    "OriginalTransactionBindingFact",
    "ReplayEvent",
    "ReplayEventType",
    "ReplayResult",
    "ReplaySourceType",
    "ReplayStatus",
    "RuntimeGateRecord",
    "CandidateFactUpdate",
    "ContextPolicyFact",
    "ContextPolicyResult",
    "ExecutionAttemptFact",
    "IdempotencyFact",
    "IdentityAssuranceFact",
    "IdentityAssuranceLevel",
    "FactDomain",
    "SourceType",
    "SourceCoverage",
    "POLICY_VERSION",
    "VerificationResult",
    "VerificationStatus",
    "canonicalize",
    "canonical_json",
    "canonical_hash",
    "confirmation_order_payload",
    "create_confirmation_record",
    "execute_with_confirmation_gate",
    "derive_known_payment_attempt_preflight",
    "evaluate_context_policy",
    "check_idempotency",
    "validate_status_observation",
    "verify_agent_executor_identity",
    "verify_binding",
    "verify_confirmation_binding",
    "verify_declared_identity_binding",
    "verify_execution_identity",
    "verify_hash",
    "verify_governed_payment_action",
    "infer_fact_domain",
    "missing_context_policy_fact",
    "verify_payment_execution_binding",
    "verify_original_transaction",
    "replay_events",
    "resolve_fact_lineage",
]

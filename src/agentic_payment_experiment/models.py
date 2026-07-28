from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class Decision(str, Enum):
    """Protocol-neutral decision for one simulated payment request."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    INDETERMINATE = "INDETERMINATE"


class PaymentStatus(str, Enum):
    """Observed status of the payment execution layer, not a pre-payment decision."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"


class PaymentRecoveryStatus(str, Enum):
    """Whether an uncertain payment state has been safely recovered or still needs work."""

    RECOVERED = "RECOVERED"
    UNRESOLVED = "UNRESOLVED"
    RETRY_CANDIDATE = "RETRY_CANDIDATE"
    BLOCKED = "BLOCKED"


class FulfillmentStatus(str, Enum):
    """Observed status of delivery or service fulfilment after payment."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"


class RemediationStatus(str, Enum):
    """Whether a post-payment problem requires or is undergoing remediation."""

    NOT_REQUIRED = "NOT_REQUIRED"
    REQUIRED = "REQUIRED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


class RefundStatus(str, Enum):
    """Observed status of one protocol-neutral refund record."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"


class DisputeStatus(str, Enum):
    """Observed status of one protocol-neutral dispute record."""

    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    UNKNOWN = "UNKNOWN"


class TaskStatus(str, Enum):
    """End-to-end user task status, deliberately separate from payment status."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    provider: str
    status: str = "active"
    credential_ref: str | None = None


@dataclass(frozen=True)
class IntentMandate:
    mandate_id: str
    user_id: str
    max_amount: Decimal
    allowed_merchants: frozenset[str]
    allowed_categories: frozenset[str]
    expires_at: datetime
    max_count: int = 1
    confirmation_above: Decimal | None = None
    expected_agent_id: str | None = None
    currency: str = "CNY"


@dataclass(frozen=True)
class TransactionRequest:
    request_id: str
    amount: Decimal
    merchant: str
    category: str
    occurred_at: datetime
    sequence_count: int = 1
    agent_id: str | None = None
    currency: str = "CNY"


@dataclass(frozen=True)
class OrderItem:
    item_id: str
    name: str
    category: str
    quantity: int
    unit_amount: Decimal
    kind: str = "product"


@dataclass(frozen=True)
class Order:
    order_id: str
    order_version: str
    merchant: str
    payee: str
    items: tuple[OrderItem, ...]
    total_amount: Decimal
    currency: str
    quote_expires_at: datetime
    fulfilment_terms: str
    mandate_ref: str
    service_id: str | None = None
    candidate_rails: tuple[str, ...] = ()


@dataclass(frozen=True)
class PaymentExecutionRecord:
    payment_id: str
    request_id: str
    order_id: str
    status: PaymentStatus
    amount: Decimal
    currency: str
    occurred_at: datetime
    receipt_ref: str | None = None
    provider_ref: str | None = None
    idempotency_key: str | None = None


@dataclass(frozen=True)
class PaymentStatusObservation:
    payment_id: str
    order_id: str
    status: PaymentStatus
    observed_at: datetime
    source: str
    provider_ref: str | None = None


@dataclass(frozen=True)
class PaymentRecoveryResult:
    initial_status: PaymentStatus
    observed_status: PaymentStatus
    effective_status: PaymentStatus
    recovery_status: PaymentRecoveryStatus
    next_action: str
    retry_allowed: bool
    issues: tuple[ValidationIssue, ...]
    evidence: tuple[EvidenceRef, ...]
    rule_version: str = "payment-recovery-rules-v0.2"
    limitations: tuple[str, ...] = (
        "simulation_only",
        "does_not_execute_real_payment_retry",
        "trusted_execution_facts_do_not_choose_recovery_action",
        "status_observations_are_fixed_offline_fixtures",
    )


@dataclass(frozen=True)
class FulfillmentRecord:
    fulfillment_id: str
    order_id: str
    status: FulfillmentStatus
    occurred_at: datetime
    service_id: str | None = None
    evidence_ref: str | None = None
    failure_code: str | None = None


@dataclass(frozen=True)
class RefundRecord:
    refund_id: str
    payment_id: str
    order_id: str
    status: RefundStatus
    amount: Decimal
    currency: str
    occurred_at: datetime
    receipt_ref: str | None = None
    reason_code: str | None = None


@dataclass(frozen=True)
class DisputeRecord:
    dispute_id: str
    payment_id: str
    order_id: str
    status: DisputeStatus
    opened_at: datetime
    reason_code: str | None = None
    evidence_ref: str | None = None


@dataclass(frozen=True)
class RemediationState:
    status: RemediationStatus
    next_action: str
    case_ref: str | None = None


@dataclass(frozen=True)
class OrderDifference:
    code: str
    field_path: str
    before: str
    after: str


@dataclass(frozen=True)
class EvidenceRef:
    code: str
    field_path: str
    observed: str
    expected: str | None = None


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    decision: Decision
    issues: tuple[ValidationIssue, ...]
    evidence: tuple[EvidenceRef, ...]
    rule_version: str = "mandate-rules-v0.1"
    limitations: tuple[str, ...] = (
        "simulation_only",
        "not_a_production_payment_authorization",
    )
    order_differences: tuple[OrderDifference, ...] = ()

    @property
    def approved(self) -> bool:
        """Compatibility view for callers that still need a boolean."""

        return self.decision is Decision.ALLOW


@dataclass(frozen=True)
class LifecycleResult:
    payment_status: PaymentStatus
    fulfillment_status: FulfillmentStatus
    remediation: RemediationState
    task_status: TaskStatus
    issues: tuple[ValidationIssue, ...]
    evidence: tuple[EvidenceRef, ...]
    refund_status: RefundStatus | None = None
    dispute_status: DisputeStatus | None = None
    rule_version: str = "lifecycle-rules-v0.1"
    limitations: tuple[str, ...] = (
        "simulation_only",
        "post_payment_statuses_are_fixture_observations",
        "does_not_execute_real_refund_or_dispute",
        "does_not_assign_legal_liability",
    )

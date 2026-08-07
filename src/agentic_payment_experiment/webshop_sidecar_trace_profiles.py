"""Closed declarative profiles for the WebShop payment sidecar trace family."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import (
    FulfillmentStatus,
    PaymentRecoveryStatus,
    PaymentStatus,
    RemediationStatus,
    TaskStatus,
)
from .payment_status_conflict import PaymentStatusConflictResolution


class SidecarExtensionKind(str, Enum):
    FULFILMENT = "FULFILMENT"
    RECOVERY = "RECOVERY"
    STATUS_CONFLICT = "STATUS_CONFLICT"


@dataclass(frozen=True)
class SidecarTraceProfile:
    profile_name: str
    extension_kind: SidecarExtensionKind
    initial_payment_status: PaymentStatus
    effective_payment_status: PaymentStatus
    recovery_initial_status: PaymentStatus | None
    recovery_observed_status: PaymentStatus | None
    recovery_effective_status: PaymentStatus | None
    recovery_status: PaymentRecoveryStatus | None
    recovery_retry_allowed: bool | None
    conflict_resolution: PaymentStatusConflictResolution | None
    conflict_initial_status: PaymentStatus | None
    conflict_query_status: PaymentStatus | None
    conflict_async_status: PaymentStatus | None
    conflict_effective_status: PaymentStatus | None
    conflict_effective_status_terminal: bool | None
    required_conflict_reason_codes: tuple[str, ...]
    lifecycle_payment_status: PaymentStatus
    lifecycle_fulfilment_status: FulfillmentStatus
    lifecycle_task_status: TaskStatus
    remediation_status: RemediationStatus


T01_PROFILE = SidecarTraceProfile(
    profile_name="WEBSHOP_NORMAL_PURCHASE_V2",
    extension_kind=SidecarExtensionKind.FULFILMENT,
    initial_payment_status=PaymentStatus.SUCCEEDED,
    effective_payment_status=PaymentStatus.SUCCEEDED,
    recovery_initial_status=None,
    recovery_observed_status=None,
    recovery_effective_status=None,
    recovery_status=None,
    recovery_retry_allowed=None,
    conflict_resolution=None,
    conflict_initial_status=None,
    conflict_query_status=None,
    conflict_async_status=None,
    conflict_effective_status=None,
    conflict_effective_status_terminal=None,
    required_conflict_reason_codes=(),
    lifecycle_payment_status=PaymentStatus.SUCCEEDED,
    lifecycle_fulfilment_status=FulfillmentStatus.SUCCEEDED,
    lifecycle_task_status=TaskStatus.SUCCEEDED,
    remediation_status=RemediationStatus.NOT_REQUIRED,
)

T09_PROFILE = SidecarTraceProfile(
    profile_name="WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2",
    extension_kind=SidecarExtensionKind.RECOVERY,
    initial_payment_status=PaymentStatus.UNKNOWN,
    effective_payment_status=PaymentStatus.SUCCEEDED,
    recovery_initial_status=PaymentStatus.UNKNOWN,
    recovery_observed_status=PaymentStatus.SUCCEEDED,
    recovery_effective_status=PaymentStatus.SUCCEEDED,
    recovery_status=PaymentRecoveryStatus.RECOVERED,
    recovery_retry_allowed=False,
    conflict_resolution=None,
    conflict_initial_status=None,
    conflict_query_status=None,
    conflict_async_status=None,
    conflict_effective_status=None,
    conflict_effective_status_terminal=None,
    required_conflict_reason_codes=(),
    lifecycle_payment_status=PaymentStatus.SUCCEEDED,
    lifecycle_fulfilment_status=FulfillmentStatus.SUCCEEDED,
    lifecycle_task_status=TaskStatus.SUCCEEDED,
    remediation_status=RemediationStatus.NOT_REQUIRED,
)

T12_PROFILE = SidecarTraceProfile(
    profile_name="WEBSHOP_PAYMENT_STATUS_CONFLICT_V2",
    extension_kind=SidecarExtensionKind.STATUS_CONFLICT,
    initial_payment_status=PaymentStatus.UNKNOWN,
    effective_payment_status=PaymentStatus.UNKNOWN,
    recovery_initial_status=PaymentStatus.UNKNOWN,
    recovery_observed_status=PaymentStatus.SUCCEEDED,
    recovery_effective_status=PaymentStatus.SUCCEEDED,
    recovery_status=PaymentRecoveryStatus.RECOVERED,
    recovery_retry_allowed=False,
    conflict_resolution=PaymentStatusConflictResolution.CONFLICT,
    conflict_initial_status=PaymentStatus.UNKNOWN,
    conflict_query_status=PaymentStatus.SUCCEEDED,
    conflict_async_status=PaymentStatus.FAILED,
    conflict_effective_status=PaymentStatus.UNKNOWN,
    conflict_effective_status_terminal=False,
    required_conflict_reason_codes=("payment_status_opposite_terminal_claims",),
    lifecycle_payment_status=PaymentStatus.UNKNOWN,
    lifecycle_fulfilment_status=FulfillmentStatus.SUCCEEDED,
    lifecycle_task_status=TaskStatus.UNKNOWN,
    remediation_status=RemediationStatus.REQUIRED,
)

SIDECAR_TRACE_PROFILES = (T01_PROFILE, T09_PROFILE, T12_PROFILE)


__all__ = [
    "SIDECAR_TRACE_PROFILES",
    "SidecarExtensionKind",
    "SidecarTraceProfile",
    "T01_PROFILE",
    "T09_PROFILE",
    "T12_PROFILE",
]

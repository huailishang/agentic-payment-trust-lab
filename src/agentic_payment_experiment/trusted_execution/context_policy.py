"""Protocol-neutral trust-source and context-policy verification facts.

The source label is a declared policy input.  It is not proof that the source
has been authenticated.  This module only evaluates and merges facts; payment
decisions remain in the payment-domain gate.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .execution_facts import VerificationStatus


class SourceType(str, Enum):
    USER_CONFIRMED = "USER_CONFIRMED"
    SYSTEM_POLICY = "SYSTEM_POLICY"
    AGENT_DECLARED = "AGENT_DECLARED"
    AGENT_INFERRED = "AGENT_INFERRED"
    MERCHANT_PROVIDED = "MERCHANT_PROVIDED"
    PROTOCOL_VERIFIED = "PROTOCOL_VERIFIED"
    PAYMENT_PROVIDER_OBSERVED = "PAYMENT_PROVIDER_OBSERVED"
    EXTERNAL_TOOL_UNTRUSTED = "EXTERNAL_TOOL_UNTRUSTED"
    WEB_UNTRUSTED = "WEB_UNTRUSTED"
    LLM_GENERATED = "LLM_GENERATED"


class FactDomain(str, Enum):
    AUTHORITY = "AUTHORITY"
    TRANSACTION_ORDER = "TRANSACTION_ORDER"
    PAYMENT_REQUEST = "PAYMENT_REQUEST"
    PAYMENT_STATUS = "PAYMENT_STATUS"
    EXECUTOR_IDENTITY = "EXECUTOR_IDENTITY"
    POLICY_CONTEXT = "POLICY_CONTEXT"


@dataclass(frozen=True)
class CandidateFactUpdate:
    source_type: SourceType | str
    target_domain: FactDomain | str
    target_path: str
    value: Any = None
    value_ref: str | None = None
    source_ref: str | None = None


@dataclass(frozen=True)
class ContextPolicyFact:
    status: VerificationStatus
    reason_codes: tuple[str, ...]
    policy_version: str | None
    current_action: str | None
    applied_paths: tuple[str, ...]
    blocked_paths: tuple[str, ...]
    source_refs: tuple[str, ...]
    trusted_state_changed: bool
    unauthorized_state_change_detected: bool


@dataclass(frozen=True)
class ContextPolicyResult:
    fact: ContextPolicyFact
    trusted_state: dict[str, Any]
    trusted_sources: dict[str, SourceType]


POLICY_VERSION = "context-source-matrix-v1"

# Explicit source x fact-domain permissions.  Every undeclared pair is denied.
_ALLOWED_WRITES = frozenset(
    {
        (SourceType.USER_CONFIRMED, FactDomain.AUTHORITY),
        (SourceType.USER_CONFIRMED, FactDomain.TRANSACTION_ORDER),
        (SourceType.USER_CONFIRMED, FactDomain.PAYMENT_REQUEST),
        (SourceType.USER_CONFIRMED, FactDomain.EXECUTOR_IDENTITY),
        (SourceType.SYSTEM_POLICY, FactDomain.POLICY_CONTEXT),
        (SourceType.MERCHANT_PROVIDED, FactDomain.TRANSACTION_ORDER),
        (SourceType.PROTOCOL_VERIFIED, FactDomain.PAYMENT_REQUEST),
        (SourceType.PAYMENT_PROVIDER_OBSERVED, FactDomain.PAYMENT_STATUS),
    }
)

_PROTECTED_EXISTING_SOURCES = frozenset(
    {
        SourceType.USER_CONFIRMED,
        SourceType.SYSTEM_POLICY,
        SourceType.PROTOCOL_VERIFIED,
        SourceType.PAYMENT_PROVIDER_OBSERVED,
    }
)


def infer_fact_domain(target_path: str) -> FactDomain | None:
    """Map a concrete trusted-state path to its closed fact domain."""

    if target_path.startswith("mandate."):
        return FactDomain.AUTHORITY
    if target_path in {"request.agent_id", "payment_execution.agent_ref"}:
        return FactDomain.EXECUTOR_IDENTITY
    if target_path.startswith(("authorized_order.", "final_order.")):
        return FactDomain.TRANSACTION_ORDER
    if target_path.startswith("request."):
        return FactDomain.PAYMENT_REQUEST
    if target_path.startswith("payment_status_observation."):
        return FactDomain.PAYMENT_STATUS
    if target_path == "payment_execution.status":
        return FactDomain.PAYMENT_STATUS
    if target_path.startswith(("agent_identity.", "executor_identity.")):
        return FactDomain.EXECUTOR_IDENTITY
    if target_path.startswith(("policy.", "context.")):
        return FactDomain.POLICY_CONTEXT
    return None


def evaluate_context_policy(
    trusted_state: Mapping[str, Any],
    updates: tuple[CandidateFactUpdate, ...] = (),
    *,
    trusted_sources: Mapping[str, SourceType] | None = None,
    policy_version: str | None = POLICY_VERSION,
    current_action: str | None,
    observed_state_after: Mapping[str, Any] | None = None,
) -> ContextPolicyResult:
    """Evaluate candidates, immutably merge allowed facts, and detect pollution."""

    before = deepcopy(dict(trusted_state))
    merged = deepcopy(before)
    merged_sources = dict(trusted_sources or {})
    applied: list[str] = []
    blocked: list[str] = []
    reasons: list[str] = []
    refs: list[str] = []
    missing = not policy_version or not current_action
    if not policy_version:
        reasons.append("context_policy_version_missing")
    if not current_action:
        reasons.append("context_current_action_missing")

    for update in sorted(updates, key=lambda item: item.target_path):
        path = update.target_path
        source = _enum_value(SourceType, update.source_type)
        domain = _enum_value(FactDomain, update.target_domain)
        inferred = infer_fact_domain(path)
        allowed = True
        if source is None:
            reasons.append(f"unknown_source_type:{path}")
            missing = True
            allowed = False
        if domain is None:
            reasons.append(f"unknown_fact_domain:{path}")
            missing = True
            allowed = False
        if not update.source_ref:
            reasons.append(f"source_ref_missing:{path}")
            missing = True
            allowed = False
        else:
            refs.append(update.source_ref)
        if update.value is None and not update.value_ref:
            reasons.append(f"candidate_value_missing:{path}")
            missing = True
            allowed = False
        if inferred is None or domain is not inferred:
            reasons.append(f"target_domain_path_mismatch:{path}")
            allowed = False
        if source is not None and domain is not None:
            if (source, domain) not in _ALLOWED_WRITES:
                reasons.append(f"source_domain_write_blocked:{path}")
                allowed = False
            existing_source = merged_sources.get(path)
            if (
                existing_source in _PROTECTED_EXISTING_SOURCES
                and source is not existing_source
            ):
                reasons.append(f"protected_fact_overwrite_blocked:{path}")
                allowed = False
        if missing:
            allowed = False
        if allowed:
            _set_path(merged, path, deepcopy(update.value))
            merged_sources[path] = source
            applied.append(path)
        else:
            blocked.append(path)

    unauthorized = False
    if observed_state_after is not None and deepcopy(dict(observed_state_after)) != merged:
        unauthorized = True
        reasons.append("unauthorized_trusted_state_change_detected")

    if unauthorized:
        status = VerificationStatus.INVALID
    elif missing:
        status = VerificationStatus.MISSING_EVIDENCE
    else:
        status = VerificationStatus.VALID
    if blocked and not missing and not unauthorized:
        reasons.append("context_updates_safely_blocked")
    if not reasons:
        reasons.append("context_policy_valid")

    fact = ContextPolicyFact(
        status=status,
        reason_codes=tuple(sorted(set(reasons))),
        policy_version=policy_version,
        current_action=current_action,
        applied_paths=tuple(sorted(applied)),
        blocked_paths=tuple(sorted(set(blocked))),
        source_refs=tuple(sorted(set(refs))),
        trusted_state_changed=before != merged,
        unauthorized_state_change_detected=unauthorized,
    )
    return ContextPolicyResult(fact, merged, merged_sources)


def missing_context_policy_fact() -> ContextPolicyFact:
    return ContextPolicyFact(
        status=VerificationStatus.MISSING_EVIDENCE,
        reason_codes=("context_policy_fact_missing",),
        policy_version=None,
        current_action=None,
        applied_paths=(),
        blocked_paths=(),
        source_refs=(),
        trusted_state_changed=False,
        unauthorized_state_change_detected=False,
    )


def _enum_value(enum_type: type[Enum], value: Any) -> Any | None:
    try:
        return value if isinstance(value, enum_type) else enum_type(value)
    except (TypeError, ValueError):
        return None


def _set_path(target: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    if len(parts) < 2 or any(not part for part in parts):
        raise ValueError(f"invalid target path: {path}")
    cursor = target
    for part in parts[:-1]:
        child = cursor.get(part)
        if child is None:
            child = {}
            cursor[part] = child
        if not isinstance(child, dict):
            raise ValueError(f"target path crosses a non-object: {path}")
        cursor = child
    cursor[parts[-1]] = value

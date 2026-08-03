"""Protocol-neutral governed payment action facts.

The action contract binds an intended payment execution to explicit references.
This module only classifies supplied evidence. It never executes a callback,
payment, network, process, file, environment, or other side effect.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from ..models import (
    AgentIdentity,
    IntentMandate,
    Order,
    PaymentExecutionRecord,
    TransactionRequest,
)
from .context_policy import ContextPolicyFact
from .execution_facts import VerificationStatus


class GovernedActionType(str, Enum):
    """Closed v1 governed-action vocabulary."""

    EXECUTE_PAYMENT = "execute_payment"


class SideEffectClass(str, Enum):
    """Closed side-effect classification for the v1 payment action."""

    PAYMENT_EXECUTION = "PAYMENT_EXECUTION"


class ActionReversibility(str, Enum):
    """Whether an action can be reversed or only compensated."""

    COMPENSATABLE_NOT_REVERSIBLE = "COMPENSATABLE_NOT_REVERSIBLE"


@dataclass(frozen=True)
class GovernedPaymentAction:
    """Immutable intended payment action; it contains no executable payload."""

    action_id: str
    action_type: GovernedActionType
    subject_ref: str
    agent_ref: str
    executor_ref: str
    authority_ref: str
    authority_version: str
    order_ref: str
    order_version: str
    request_ref: str
    payment_ref: str
    source_refs: tuple[str, ...]
    side_effect_class: SideEffectClass
    reversibility: ActionReversibility
    occurred_at: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "action_id": self.action_id,
            "action_type": _enum_value(self.action_type),
            "subject_ref": self.subject_ref,
            "agent_ref": self.agent_ref,
            "executor_ref": self.executor_ref,
            "authority_ref": self.authority_ref,
            "authority_version": self.authority_version,
            "order_ref": self.order_ref,
            "order_version": self.order_version,
            "request_ref": self.request_ref,
            "payment_ref": self.payment_ref,
            "source_refs": list(self.source_refs),
            "side_effect_class": _enum_value(self.side_effect_class),
            "reversibility": _enum_value(self.reversibility),
            "occurred_at": (
                self.occurred_at.isoformat()
                if isinstance(self.occurred_at, datetime)
                else None
            ),
        }


@dataclass(frozen=True)
class GovernedActionBindingFact:
    """Deterministic evidence classification for one governed action."""

    status: VerificationStatus
    action_id: str | None
    reason_codes: tuple[str, ...]
    checked_action_type: str | None
    checked_order_ref: str | None
    checked_request_ref: str | None
    checked_payment_ref: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "action_id": self.action_id,
            "reason_codes": list(self.reason_codes),
            "checked_action_type": self.checked_action_type,
            "checked_order_ref": self.checked_order_ref,
            "checked_request_ref": self.checked_request_ref,
            "checked_payment_ref": self.checked_payment_ref,
        }


def verify_governed_payment_action(
    action: GovernedPaymentAction | None,
    *,
    mandate: IntentMandate | None,
    order: Order | None,
    request: TransactionRequest | None,
    execution: PaymentExecutionRecord | None,
    agent_identity: AgentIdentity | None,
    current_executor_instance_ref: str | None,
    context_policy_fact: ContextPolicyFact | None,
) -> GovernedActionBindingFact:
    """Verify a supplied EXECUTE_PAYMENT action without executing it.

    Missing evidence is separated from contradictory or unsupported evidence.
    All checks are local, deterministic, copy-free reads of immutable inputs.
    """

    if action is None:
        return _fact(
            VerificationStatus.MISSING_EVIDENCE,
            None,
            ("governed_action_missing",),
            (None, None, None, None),
        )
    if type(action) is not GovernedPaymentAction:
        return _fact(
            VerificationStatus.INVALID,
            None,
            ("governed_action_invalid_type",),
            (None, None, None, None),
        )

    checked = _checked_values(action)
    missing: list[str] = []
    invalid: list[str] = []

    _require_text(action.action_id, "action_id", missing, invalid)
    _require_text(action.subject_ref, "subject_ref", missing, invalid)
    _require_text(action.agent_ref, "agent_ref", missing, invalid)
    _require_text(action.executor_ref, "executor_ref", missing, invalid)
    _require_text(action.authority_ref, "authority_ref", missing, invalid)
    _require_text(action.authority_version, "authority_version", missing, invalid)
    _require_text(action.order_ref, "order_ref", missing, invalid)
    _require_text(action.order_version, "order_version", missing, invalid)
    _require_text(action.request_ref, "request_ref", missing, invalid)
    _require_text(action.payment_ref, "payment_ref", missing, invalid)

    if action.action_type is None:
        missing.append("action_type_missing")
    elif not isinstance(action.action_type, GovernedActionType):
        invalid.append("action_type_invalid")
    elif action.action_type is not GovernedActionType.EXECUTE_PAYMENT:
        invalid.append("action_type_unsupported")

    if action.side_effect_class is None:
        missing.append("side_effect_class_missing")
    elif not isinstance(action.side_effect_class, SideEffectClass):
        invalid.append("side_effect_class_invalid")
    elif action.side_effect_class is not SideEffectClass.PAYMENT_EXECUTION:
        invalid.append("side_effect_class_unsupported")

    if action.reversibility is None:
        missing.append("reversibility_missing")
    elif not isinstance(action.reversibility, ActionReversibility):
        invalid.append("reversibility_invalid")
    elif (
        action.reversibility
        is not ActionReversibility.COMPENSATABLE_NOT_REVERSIBLE
    ):
        invalid.append("reversibility_unsupported")

    if action.source_refs is None or action.source_refs == ():
        missing.append("source_refs_missing")
    elif not isinstance(action.source_refs, tuple):
        invalid.append("source_refs_invalid_type")
    elif any(not isinstance(item, str) for item in action.source_refs):
        invalid.append("source_refs_invalid_type")
    elif any(not item.strip() for item in action.source_refs):
        invalid.append("source_refs_blank")

    if action.occurred_at is None:
        missing.append("action_occurred_at_missing")
    elif not isinstance(action.occurred_at, datetime):
        invalid.append("action_occurred_at_invalid_type")
    elif action.occurred_at.tzinfo is None or action.occurred_at.utcoffset() is None:
        invalid.append("action_occurred_at_timezone_missing")

    if mandate is None:
        missing.append("mandate_missing")
    if order is None:
        missing.append("order_missing")
    if request is None:
        missing.append("request_missing")
    if execution is None:
        missing.append("payment_execution_missing")
    if agent_identity is None:
        missing.append("agent_identity_missing")
    if context_policy_fact is None:
        missing.append("context_policy_fact_missing")
    _require_external_text(
        current_executor_instance_ref,
        "current_executor_instance_ref",
        missing,
        invalid,
    )

    if mandate is not None:
        _require_external_text(mandate.user_id, "mandate_user_id", missing, invalid)
        _require_external_text(
            mandate.mandate_id, "mandate_authority_ref", missing, invalid
        )
        _require_external_text(
            mandate.authority_version,
            "mandate_authority_version",
            missing,
            invalid,
        )
        _require_external_text(
            mandate.expected_agent_id,
            "mandate_expected_agent_id",
            missing,
            invalid,
        )
    if order is not None:
        _require_external_text(order.order_id, "order_id", missing, invalid)
        _require_external_text(order.order_version, "order_version", missing, invalid)
    if request is not None:
        _require_external_text(request.request_id, "request_id", missing, invalid)
        _require_external_text(request.agent_id, "request_agent_id", missing, invalid)
        if not isinstance(request.occurred_at, datetime):
            invalid.append("request_occurred_at_invalid_type")
        elif request.occurred_at.tzinfo is None or request.occurred_at.utcoffset() is None:
            invalid.append("request_occurred_at_timezone_missing")
    if execution is not None:
        _require_external_text(execution.payment_id, "payment_id", missing, invalid)
        _require_external_text(
            execution.request_id, "execution_request_id", missing, invalid
        )
        _require_external_text(execution.order_id, "execution_order_id", missing, invalid)
        if not isinstance(execution.occurred_at, datetime):
            invalid.append("execution_occurred_at_invalid_type")
        elif (
            execution.occurred_at.tzinfo is None
            or execution.occurred_at.utcoffset() is None
        ):
            invalid.append("execution_occurred_at_timezone_missing")
    if agent_identity is not None:
        _require_external_text(
            agent_identity.agent_id, "identity_agent_id", missing, invalid
        )
        _require_external_text(
            agent_identity.executor_instance_id,
            "identity_executor_instance_ref",
            missing,
            invalid,
        )
    if context_policy_fact is not None:
        _require_external_text(
            context_policy_fact.current_action,
            "context_current_action",
            missing,
            invalid,
        )

    if missing:
        return _fact(
            VerificationStatus.MISSING_EVIDENCE,
            _optional_text(action.action_id),
            _deduplicate(missing),
            checked,
        )
    if invalid:
        return _fact(
            VerificationStatus.INVALID,
            _optional_text(action.action_id),
            _deduplicate(invalid),
            checked,
        )

    assert mandate is not None
    assert order is not None
    assert request is not None
    assert execution is not None
    assert agent_identity is not None
    assert context_policy_fact is not None
    assert isinstance(action.action_type, GovernedActionType)
    assert isinstance(action.occurred_at, datetime)
    assert isinstance(request.occurred_at, datetime)
    assert isinstance(execution.occurred_at, datetime)
    assert isinstance(current_executor_instance_ref, str)
    assert isinstance(agent_identity.executor_instance_id, str)
    assert isinstance(mandate.expected_agent_id, str)
    assert isinstance(request.agent_id, str)
    assert isinstance(context_policy_fact.current_action, str)

    if action.subject_ref != mandate.user_id:
        invalid.append("subject_ref_mismatch")
    if action.authority_ref != mandate.mandate_id:
        invalid.append("authority_ref_mismatch")
    if action.authority_version != mandate.authority_version:
        invalid.append("authority_version_mismatch")

    if action.order_ref != order.order_id:
        invalid.append("order_ref_mismatch")
    if action.order_version != order.order_version:
        invalid.append("order_version_mismatch")
    if action.request_ref != request.request_id:
        invalid.append("request_ref_mismatch")
    if action.payment_ref != execution.payment_id:
        invalid.append("payment_ref_mismatch")
    if execution.request_id != request.request_id:
        invalid.append("execution_request_chain_mismatch")
    if execution.order_id != order.order_id:
        invalid.append("execution_order_chain_mismatch")

    if action.agent_ref != request.agent_id:
        invalid.append("agent_ref_request_mismatch")
    if action.agent_ref != mandate.expected_agent_id:
        invalid.append("agent_ref_mandate_mismatch")
    if action.agent_ref != agent_identity.agent_id:
        invalid.append("agent_ref_identity_mismatch")
    if action.executor_ref != current_executor_instance_ref:
        invalid.append("executor_ref_current_mismatch")
    if action.executor_ref != agent_identity.executor_instance_id:
        invalid.append("executor_ref_identity_mismatch")

    if action.action_type.value != context_policy_fact.current_action:
        invalid.append("context_action_mismatch")

    if action.occurred_at < request.occurred_at:
        invalid.append("action_before_request")
    if action.occurred_at > execution.occurred_at:
        invalid.append("action_after_execution")

    if action.action_id == order.order_id:
        invalid.append("action_id_order_ref_collision")
    if action.action_id == request.request_id:
        invalid.append("action_id_request_ref_collision")
    if action.action_id == execution.payment_id:
        invalid.append("action_id_payment_ref_collision")

    status = VerificationStatus.INVALID if invalid else VerificationStatus.VALID
    reasons = _deduplicate(invalid) if invalid else ("governed_action_binding_valid",)
    return _fact(status, action.action_id, reasons, checked)


def _checked_values(
    action: GovernedPaymentAction | None,
) -> tuple[str | None, str | None, str | None, str | None]:
    if action is None:
        return None, None, None, None
    return (
        _enum_value(action.action_type),
        _optional_text(action.order_ref),
        _optional_text(action.request_ref),
        _optional_text(action.payment_ref),
    )


def _fact(
    status: VerificationStatus,
    action_id: str | None,
    reasons: tuple[str, ...],
    checked: tuple[str | None, str | None, str | None, str | None],
) -> GovernedActionBindingFact:
    return GovernedActionBindingFact(
        status=status,
        action_id=action_id,
        reason_codes=reasons,
        checked_action_type=checked[0],
        checked_order_ref=checked[1],
        checked_request_ref=checked[2],
        checked_payment_ref=checked[3],
    )


def _require_text(
    value: Any,
    field: str,
    missing: list[str],
    invalid: list[str],
) -> None:
    if value is None or value == "":
        missing.append(f"{field}_missing")
    elif not isinstance(value, str):
        invalid.append(f"{field}_invalid_type")
    elif not value.strip():
        missing.append(f"{field}_missing")


def _require_external_text(
    value: Any,
    field: str,
    missing: list[str],
    invalid: list[str],
) -> None:
    _require_text(value, field, missing, invalid)


def _enum_value(value: Any) -> str | None:
    return value.value if isinstance(value, Enum) else None


def _optional_text(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _deduplicate(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))

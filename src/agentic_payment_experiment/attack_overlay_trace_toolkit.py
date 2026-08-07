"""Product-observed authoritative traces for the Attack Overlay family.

This module consumes only facts already produced by ``evaluate_attack_overlay``.
It never reruns policy, lineage, validation, evaluation, or any side effect.
"""

from __future__ import annotations

from .attack_overlay import AttackOverlayResult, AttackOverrideLineageFact
from .attack_overlay_trace_profiles import (
    ATTACK_OVERLAY_TRACE_PROFILES,
    AttackOverlayTraceProfile,
)
from .authoritative_trace import ProductAuthoritativeTrace, TraceContractError
from .trusted_execution import VerificationStatus
from .webshop_trace_assembler import (
    assemble_product_trace,
    create_event,
    create_source_binding,
)


def _profile_matches(
    profile: AttackOverlayTraceProfile,
    *,
    result: AttackOverlayResult,
) -> bool:
    if (
        result.authoritative_trace is not None
        or result.attack_attempted is not True
        or result.applied_paths != ()
        or result.blocked_override_paths != (profile.blocked_path,)
        or result.trusted_state_changed is not False
        or result.decision_drift is not False
        or result.baseline_decision is not result.defended_decision
        or result.lineage_status is not VerificationStatus.VALID
        or result.evaluation.status != "PASS"
        or result.evaluation.decision_correct is not True
        or result.evaluation.decision_error is not False
        or result.evaluation.forbidden_side_effect is not False
        or not result.reason_codes
        or not result.lineage_reason_codes
        or not result.policy_version
        or len(result.lineage_facts) != 1
    ):
        return False

    fact = result.lineage_facts[0]
    if type(fact) is not AttackOverrideLineageFact:
        return False
    return (
        fact.fact_path == profile.blocked_path
        and fact.direct_source_type is result.source_type
        and fact.effective_source_types == (result.source_type,)
        and fact.contains_untrusted_ancestry is True
        and fact.source_ref == result.source_ref
    )


def _select_profile(
    *,
    result: AttackOverlayResult,
    profiles: tuple[AttackOverlayTraceProfile, ...] = ATTACK_OVERLAY_TRACE_PROFILES,
) -> AttackOverlayTraceProfile | None:
    if type(result) is not AttackOverlayResult:
        return None
    if type(profiles) is not tuple or any(
        type(profile) is not AttackOverlayTraceProfile for profile in profiles
    ):
        return None
    matches = tuple(
        profile for profile in profiles if _profile_matches(profile, result=result)
    )
    return matches[0] if len(matches) == 1 else None


def project_attack_overlay_result(result: AttackOverlayResult) -> dict[str, object]:
    """Project only fields frozen by ``attack-overlay-result-trace/v2``."""

    return {
        "attack_id": result.attack_id,
        "source_type": result.source_type.value,
        "baseline_decision": result.baseline_decision.value,
        "defended_decision": result.defended_decision.value,
        "attack_attempted": result.attack_attempted,
        "applied_paths": list(result.applied_paths),
        "blocked_override_paths": list(result.blocked_override_paths),
        "trusted_state_changed": result.trusted_state_changed,
        "reason_codes": list(result.reason_codes),
        "policy_version": result.policy_version,
        "decision_drift": result.decision_drift,
        "lineage_status": result.lineage_status.value,
        "lineage_reason_codes": list(result.lineage_reason_codes),
        "lineage_fact_refs": [fact.fact_ref for fact in result.lineage_facts],
        "lineage_effective_source_types": [
            source.value
            for fact in result.lineage_facts
            for source in fact.effective_source_types
        ],
    }


def build_attack_overlay_product_trace(
    result: AttackOverlayResult,
    *,
    profiles: tuple[AttackOverlayTraceProfile, ...] = ATTACK_OVERLAY_TRACE_PROFILES,
) -> ProductAuthoritativeTrace | None:
    """Build one complete family trace when exactly one frozen profile matches."""

    if type(result) is not AttackOverlayResult or result.authoritative_trace is not None:
        return None
    try:
        profile = _select_profile(result=result, profiles=profiles)
        if profile is None:
            return None

        projection = project_attack_overlay_result(result)
        binding = create_source_binding(
            "AttackOverlayResult",
            "attack-overlay-result-trace/v2",
            projection,
        )
        entity_ref_template = "AttackOverlayResult:{projection.attack_id}"
        events = (
            create_event(
                1,
                "POLICY_DECISION_RECORDED",
                "AttackOverlayResult",
                "ATTACK_POLICY_RESULT",
                binding,
                entity_ref_template,
                decision=result.defended_decision.value,
                reason_codes=result.reason_codes,
            ),
            create_event(
                2,
                "LINEAGE_DECISION_RECORDED",
                "AttackOverlayResult",
                "ATTACK_LINEAGE_RESULT",
                binding,
                entity_ref_template,
                status=result.lineage_status.value,
                reason_codes=result.lineage_reason_codes,
            ),
            create_event(
                3,
                "RESULT_RECORDED",
                "AttackOverlayResult",
                "FINAL_OUTCOME",
                binding,
                entity_ref_template,
                decision=result.defended_decision.value,
                reason_codes=result.reason_codes,
            ),
        )
        return assemble_product_trace(
            profile=profile.profile_name,
            trace_ref=(
                f"ProductAuthoritativeTrace:{profile.profile_name}:{result.attack_id}"
            ),
            events=events,
            source_bindings=(binding,),
            expected_unique_binding_count=1,
        )
    except (AttributeError, KeyError, TypeError, ValueError, TraceContractError):
        return None


__all__ = [
    "build_attack_overlay_product_trace",
    "project_attack_overlay_result",
]

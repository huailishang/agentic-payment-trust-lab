from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Mapping

from .authoritative_trace import ProductAuthoritativeTrace
from .evaluator import EvaluationResult, ExpectedOutcome, ObservedOutcome, evaluate_outcome
from .models import Decision, ValidationResult
from .scenario_loader import Scenario, load_scenario
from .trusted_execution import (
    POLICY_VERSION,
    CandidateFactUpdate,
    FactDomain,
    FactLineageNode,
    SourceType,
    VerificationStatus,
    canonical_hash,
    evaluate_context_policy,
    infer_fact_domain,
    resolve_fact_lineage,
)
from .validator import validate_request


_TRUSTED_EXECUTION_ROOTS = frozenset(
    {
        "mandate",
        "request",
        "authorized_order",
        "final_order",
        "confirmation_record",
        "payment_execution",
        "payment_status_observation",
        "known_payment_attempts",
        "fulfillment",
        "refund",
        "dispute",
    }
)


@dataclass(frozen=True)
class AttackOverlay:
    """One untrusted-data injection layered on top of a trusted payment scenario.

    The text itself is intentionally treated as data. ``proposed_overrides`` records
    what the hostile content is trying to make the agent change. Version 1 does
    not execute an LLM and does not parse natural language into actions.
    """

    attack_id: str
    title: str
    source: str
    untrusted_content: str
    proposed_overrides: dict[str, Any]
    source_type: SourceType = SourceType.EXTERNAL_TOOL_UNTRUSTED
    source_ref: str = "legacy-untrusted-overlay"


@dataclass(frozen=True)
class AttackOverlaySuite:
    name: str
    base_scenario: str
    source_repository: str
    source_version: str
    license: str
    accessed_at: str
    overlays: tuple[AttackOverlay, ...]


@dataclass(frozen=True)
class AttackOverrideLineageFact:
    fact_ref: str
    fact_path: str
    value_digest: str
    direct_source_type: SourceType
    effective_source_types: tuple[SourceType, ...]
    contains_untrusted_ancestry: bool
    source_ref: str

    def to_dict(self) -> dict[str, object]:
        return {
            "fact_ref": self.fact_ref,
            "fact_path": self.fact_path,
            "value_digest": self.value_digest,
            "direct_source_type": self.direct_source_type.value,
            "effective_source_types": [
                source.value for source in self.effective_source_types
            ],
            "contains_untrusted_ancestry": self.contains_untrusted_ancestry,
            "source_ref": self.source_ref,
        }


@dataclass(frozen=True)
class AttackBoundaryResult:
    attack_attempted: bool
    applied_paths: tuple[str, ...]
    blocked_override_paths: tuple[str, ...]
    trusted_state_changed: bool
    reason_codes: tuple[str, ...]
    policy_version: str | None
    unauthorized_state_change_detected: bool
    lineage_status: VerificationStatus
    lineage_reason_codes: tuple[str, ...]
    lineage_facts: tuple[AttackOverrideLineageFact, ...]


@dataclass(frozen=True)
class AttackOverlayResult:
    attack_id: str
    title: str
    source: str
    source_type: SourceType
    source_ref: str
    baseline_decision: Decision
    defended_decision: Decision
    attack_attempted: bool
    applied_paths: tuple[str, ...]
    blocked_override_paths: tuple[str, ...]
    trusted_state_changed: bool
    reason_codes: tuple[str, ...]
    policy_version: str | None
    decision_drift: bool
    evaluation: EvaluationResult
    lineage_status: VerificationStatus
    lineage_reason_codes: tuple[str, ...]
    lineage_facts: tuple[AttackOverrideLineageFact, ...]
    authoritative_trace: ProductAuthoritativeTrace | None = None


@dataclass(frozen=True)
class AttackOverlayBatchResult:
    results: tuple[AttackOverlayResult, ...]
    total: int
    passed: int
    failed: int
    attack_cases: int
    blocked_attack_cases: int
    decision_drifts: int
    trusted_state_mutations: int


def load_attack_overlay_suite(path: Path) -> AttackOverlaySuite:
    data = json.loads(path.read_text(encoding="utf-8"))
    meta = data["_meta"]
    overlays = tuple(
        AttackOverlay(
            attack_id=str(item["attack_id"]),
            title=str(item["title"]),
            source=str(item["source"]),
            source_type=SourceType(str(item["source_type"])),
            source_ref=str(item["source_ref"]),
            untrusted_content=str(item["untrusted_content"]),
            proposed_overrides=dict(item.get("proposed_overrides", {})),
        )
        for item in data["overlays"]
    )
    for overlay in overlays:
        _validate_overlay_paths(overlay)
    return AttackOverlaySuite(
        name=str(meta["name"]),
        base_scenario=str(meta["base_scenario"]),
        source_repository=str(meta["source_repository"]),
        source_version=str(meta["source_version"]),
        license=str(meta["license"]),
        accessed_at=str(meta["accessed_at"]),
        overlays=overlays,
    )


def enforce_untrusted_overlay(
    trusted_state: Mapping[str, Any],
    overlay: AttackOverlay,
) -> AttackBoundaryResult:
    """Evaluate every proposed write through the shared P4 source matrix."""

    _validate_overlay_paths(overlay)
    sources = {
        path: SourceType.USER_CONFIRMED
        for path in overlay.proposed_overrides
        if _path_exists(trusted_state, path)
    }
    updates = tuple(
        CandidateFactUpdate(
            source_type=overlay.source_type,
            target_domain=infer_fact_domain(path) or FactDomain.POLICY_CONTEXT,
            target_path=path,
            value=value,
            source_ref=overlay.source_ref,
        )
        for path, value in overlay.proposed_overrides.items()
    )
    result = evaluate_context_policy(
        trusted_state,
        updates,
        trusted_sources=sources,
        policy_version=POLICY_VERSION,
        current_action="evaluate_payment_context",
    )
    lineage_status, lineage_reasons, lineage_facts = _resolve_overlay_lineage(overlay)
    return AttackBoundaryResult(
        attack_attempted=bool(overlay.proposed_overrides),
        applied_paths=result.fact.applied_paths,
        blocked_override_paths=result.fact.blocked_paths,
        trusted_state_changed=result.fact.trusted_state_changed,
        reason_codes=result.fact.reason_codes,
        policy_version=result.fact.policy_version,
        unauthorized_state_change_detected=(
            result.fact.unauthorized_state_change_detected
        ),
        lineage_status=lineage_status,
        lineage_reason_codes=lineage_reasons,
        lineage_facts=lineage_facts,
    )


def evaluate_attack_overlay(scenario: Scenario, overlay: AttackOverlay) -> AttackOverlayResult:
    baseline = _validate_scenario(scenario)
    boundary = enforce_untrusted_overlay(_trusted_state_snapshot(scenario), overlay)

    defended = _validate_scenario(scenario)
    observed_effects = (
        frozenset({"trusted_field_override_applied"})
        if boundary.unauthorized_state_change_detected
        else frozenset()
    )
    evaluation = evaluate_outcome(
        ExpectedOutcome(
            expected_decision=scenario.expected.decision,
            forbidden_effects=frozenset({"trusted_field_override_applied"}),
        ),
        ObservedOutcome(
            actual_decision=defended.decision,
            observed_effects=observed_effects,
        ),
    )
    base_result = AttackOverlayResult(
        attack_id=overlay.attack_id,
        title=overlay.title,
        source=overlay.source,
        source_type=overlay.source_type,
        source_ref=overlay.source_ref,
        baseline_decision=baseline.decision,
        defended_decision=defended.decision,
        attack_attempted=boundary.attack_attempted,
        applied_paths=boundary.applied_paths,
        blocked_override_paths=boundary.blocked_override_paths,
        trusted_state_changed=boundary.trusted_state_changed,
        reason_codes=boundary.reason_codes,
        policy_version=boundary.policy_version,
        decision_drift=defended.decision is not baseline.decision,
        evaluation=evaluation,
        lineage_status=boundary.lineage_status,
        lineage_reason_codes=boundary.lineage_reason_codes,
        lineage_facts=boundary.lineage_facts,
    )
    from .attack_overlay_trace_toolkit import build_attack_overlay_product_trace

    authoritative_trace = build_attack_overlay_product_trace(base_result)
    return (
        replace(base_result, authoritative_trace=authoritative_trace)
        if authoritative_trace is not None
        else base_result
    )


def run_attack_overlay_suite(
    suite: AttackOverlaySuite,
    *,
    scenarios_dir: Path,
) -> AttackOverlayBatchResult:
    scenario = load_scenario(scenarios_dir / suite.base_scenario)
    results = tuple(evaluate_attack_overlay(scenario, overlay) for overlay in suite.overlays)
    passed = sum(result.evaluation.status == "PASS" for result in results)
    attack_results = tuple(result for result in results if result.attack_attempted)
    return AttackOverlayBatchResult(
        results=results,
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        attack_cases=len(attack_results),
        blocked_attack_cases=sum(bool(result.blocked_override_paths) for result in attack_results),
        decision_drifts=sum(result.decision_drift for result in results),
        trusted_state_mutations=sum(result.trusted_state_changed for result in results),
    )


def write_attack_overlay_report(
    suite: AttackOverlaySuite,
    batch: AttackOverlayBatchResult,
    path: Path,
) -> None:
    report = {
        "benchmark": suite.name,
        "status": "PASS" if batch.failed == 0 else "FAIL",
        "mode": "deterministic_untrusted_data_trust_boundary",
        "source": {
            "repository": suite.source_repository,
            "version": suite.source_version,
            "license": suite.license,
            "accessed_at": suite.accessed_at,
        },
        "base_scenario": suite.base_scenario,
        "summary": {
            "total": batch.total,
            "passed": batch.passed,
            "failed": batch.failed,
            "attack_cases": batch.attack_cases,
            "blocked_attack_cases": batch.blocked_attack_cases,
            "decision_drifts": batch.decision_drifts,
            "trusted_state_mutations": batch.trusted_state_mutations,
        },
        "limitations": {
            "does_not_execute_llm": True,
            "does_not_measure_prompt_injection_attack_success_rate": True,
            "does_not_parse_natural_language_into_tool_calls": True,
            "does_not_execute_real_payment": True,
            "purpose": "verify that untrusted content cannot directly rewrite trusted payment inputs",
        },
        "results": [
            {
                "attack_id": result.attack_id,
                "title": result.title,
                "source": result.source,
                "source_type": result.source_type.value,
                "source_ref": result.source_ref,
                "baseline_decision": result.baseline_decision.value,
                "defended_decision": result.defended_decision.value,
                "attack_attempted": result.attack_attempted,
                "applied_paths": list(result.applied_paths),
                "blocked_override_paths": list(result.blocked_override_paths),
                "reason_codes": list(result.reason_codes),
                "policy_version": result.policy_version,
                "trusted_state_changed": result.trusted_state_changed,
                "decision_drift": result.decision_drift,
                "evaluation": asdict(result.evaluation),
                "lineage": {
                    "status": result.lineage_status.value,
                    "reason_codes": list(result.lineage_reason_codes),
                    "facts": [fact.to_dict() for fact in result.lineage_facts],
                },
            }
            for result in batch.results
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _resolve_overlay_lineage(
    overlay: AttackOverlay,
) -> tuple[
    VerificationStatus,
    tuple[str, ...],
    tuple[AttackOverrideLineageFact, ...],
]:
    nodes: list[FactLineageNode] = []
    digest_failures: list[str] = []
    for path, value in sorted(overlay.proposed_overrides.items()):
        digest = _overlay_value_digest(value)
        if digest is None:
            digest_failures.append(f"overlay_lineage_value_digest_missing:{path}")
            continue
        nodes.append(
            FactLineageNode(
                fact_ref=f"overlay:{overlay.attack_id}:{path}",
                fact_path=path,
                value_digest=digest,
                direct_source_type=overlay.source_type,
                upstream_fact_refs=(),
                transformation_ref=f"proposed_override:{overlay.attack_id}",
            )
        )
    if digest_failures:
        return VerificationStatus.MISSING_EVIDENCE, tuple(digest_failures), ()

    lineage = resolve_fact_lineage(tuple(nodes))
    facts = tuple(
        AttackOverrideLineageFact(
            fact_ref=fact.fact_ref,
            fact_path=fact.fact_path,
            value_digest=fact.value_digest,
            direct_source_type=fact.direct_source_type,
            effective_source_types=fact.effective_source_types,
            contains_untrusted_ancestry=fact.contains_untrusted_ancestry,
            source_ref=overlay.source_ref,
        )
        for fact in lineage.resolved_facts
    )
    return lineage.status, lineage.reason_codes, facts


def _overlay_value_digest(value: object) -> str | None:
    try:
        return canonical_hash(value)
    except (TypeError, ValueError):
        try:
            json_text = json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        except (TypeError, ValueError):
            return None
        return canonical_hash({"overlay_json_value": json_text})


def _validate_overlay_paths(overlay: AttackOverlay) -> None:
    for path in overlay.proposed_overrides:
        root = path.split(".", 1)[0].strip()
        if not path.strip() or root not in _TRUSTED_EXECUTION_ROOTS:
            raise ValueError(
                f"attack overlay {overlay.attack_id!r} targets unsupported field path: {path!r}"
            )


def _path_exists(state: Mapping[str, Any], path: str) -> bool:
    cursor: Any = state
    for part in path.split("."):
        if not isinstance(cursor, Mapping) or part not in cursor:
            return False
        cursor = cursor[part]
    return True


def _trusted_state_snapshot(scenario: Scenario) -> dict[str, Any]:
    return {
        "mandate": asdict(scenario.mandate),
        "request": asdict(scenario.request),
        "authorized_order": asdict(scenario.authorized_order) if scenario.authorized_order else None,
        "final_order": asdict(scenario.final_order) if scenario.final_order else None,
        "confirmation_record": (
            asdict(scenario.confirmation_record) if scenario.confirmation_record else None
        ),
    }


def _validate_scenario(scenario: Scenario) -> ValidationResult:
    return validate_request(
        scenario.mandate,
        scenario.request,
        seen_request_ids=scenario.seen_request_ids,
        authorized_order=scenario.authorized_order,
        final_order=scenario.final_order,
        confirmation_record=scenario.confirmation_record,
    )

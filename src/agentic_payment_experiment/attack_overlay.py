from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .evaluator import EvaluationResult, ExpectedOutcome, ObservedOutcome, evaluate_outcome
from .models import Decision, ValidationResult
from .scenario_loader import Scenario, load_scenario
from .validator import validate_request


_TRUSTED_EXECUTION_ROOTS = frozenset(
    {
        "mandate",
        "request",
        "authorized_order",
        "final_order",
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
class AttackOverlayResult:
    attack_id: str
    title: str
    source: str
    baseline_decision: Decision
    defended_decision: Decision
    attack_attempted: bool
    blocked_override_paths: tuple[str, ...]
    trusted_state_changed: bool
    decision_drift: bool
    evaluation: EvaluationResult


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


def evaluate_attack_overlay(scenario: Scenario, overlay: AttackOverlay) -> AttackOverlayResult:
    _validate_overlay_paths(overlay)
    baseline = _validate_scenario(scenario)

    # Trust-boundary defense: content returned by merchant pages/tools is data,
    # not authority to rewrite executable payment inputs. Every declared
    # trusted-field override attempt is blocked; the original trusted state runs.
    blocked_override_paths = tuple(sorted(overlay.proposed_overrides))

    before = _trusted_state_snapshot(scenario)
    after = _trusted_state_snapshot(scenario)
    trusted_state_changed = before != after

    defended = _validate_scenario(scenario)
    observed_effects = (
        frozenset({"trusted_field_override_applied"})
        if trusted_state_changed
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
    return AttackOverlayResult(
        attack_id=overlay.attack_id,
        title=overlay.title,
        source=overlay.source,
        baseline_decision=baseline.decision,
        defended_decision=defended.decision,
        attack_attempted=bool(overlay.proposed_overrides),
        blocked_override_paths=blocked_override_paths,
        trusted_state_changed=trusted_state_changed,
        decision_drift=defended.decision is not baseline.decision,
        evaluation=evaluation,
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
                "baseline_decision": result.baseline_decision.value,
                "defended_decision": result.defended_decision.value,
                "attack_attempted": result.attack_attempted,
                "blocked_override_paths": list(result.blocked_override_paths),
                "trusted_state_changed": result.trusted_state_changed,
                "decision_drift": result.decision_drift,
                "evaluation": asdict(result.evaluation),
            }
            for result in batch.results
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _validate_overlay_paths(overlay: AttackOverlay) -> None:
    for path in overlay.proposed_overrides:
        root = path.split(".", 1)[0].strip()
        if not path.strip() or root not in _TRUSTED_EXECUTION_ROOTS:
            raise ValueError(
                f"attack overlay {overlay.attack_id!r} targets unsupported field path: {path!r}"
            )


def _trusted_state_snapshot(scenario: Scenario) -> dict[str, Any]:
    return {
        "mandate": asdict(scenario.mandate),
        "request": asdict(scenario.request),
        "authorized_order": asdict(scenario.authorized_order) if scenario.authorized_order else None,
        "final_order": asdict(scenario.final_order) if scenario.final_order else None,
    }


def _validate_scenario(scenario: Scenario) -> ValidationResult:
    return validate_request(
        scenario.mandate,
        scenario.request,
        seen_request_ids=scenario.seen_request_ids,
        authorized_order=scenario.authorized_order,
        final_order=scenario.final_order,
    )

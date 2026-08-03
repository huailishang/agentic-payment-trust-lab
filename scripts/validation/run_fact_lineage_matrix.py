"""Run the fixed offline fact-lineage/source-propagation matrix."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_payment_experiment.attack_overlay import AttackOverlay, enforce_untrusted_overlay
from agentic_payment_experiment.trusted_execution import (
    FactLineageNode,
    SourceType,
    canonical_hash,
    resolve_fact_lineage,
)

DEFAULT_SPEC = ROOT / "samples" / "attacks" / "fact_lineage_matrix_v1.json"


def _node(
    fact_ref: str,
    source: SourceType,
    *,
    path: str = "request.amount",
    value: object = "100.00",
    upstream: tuple[str, ...] = (),
    transformation_ref: str | None = None,
    trust_upgrade_evidence_ref: str | None = None,
) -> FactLineageNode:
    return FactLineageNode(
        fact_ref=fact_ref,
        fact_path=path,
        value_digest=canonical_hash(value),
        direct_source_type=source,
        upstream_fact_refs=upstream,
        transformation_ref=transformation_ref,
        trust_upgrade_evidence_ref=trust_upgrade_evidence_ref,
    )


def _graph_for(scenario: str) -> tuple[object, ...]:
    if scenario == "root_user_confirmed":
        return (_node("root-user", SourceType.USER_CONFIRMED),)
    if scenario == "root_web_untrusted":
        return (_node("root-web", SourceType.WEB_UNTRUSTED),)
    if scenario == "web_to_llm_summary":
        return (
            _node("llm-summary", SourceType.LLM_GENERATED, upstream=("web-price",), transformation_ref="llm-summary-v1"),
            _node("web-price", SourceType.WEB_UNTRUSTED),
        )
    if scenario == "multi_source_user_and_web":
        return (
            _node("derived-multi", SourceType.AGENT_INFERRED, upstream=("user-budget", "web-price"), transformation_ref="compare-v1"),
            _node("web-price", SourceType.WEB_UNTRUSTED),
            _node("user-budget", SourceType.USER_CONFIRMED),
        )
    if scenario == "claimed_user_confirmation_with_web_ancestor":
        return (
            _node("claimed-user", SourceType.USER_CONFIRMED, upstream=("web-origin",)),
            _node("web-origin", SourceType.WEB_UNTRUSTED),
        )
    if scenario == "claimed_upgrade_with_evidence_and_web_ancestor":
        return (
            _node(
                "claimed-upgrade",
                SourceType.USER_CONFIRMED,
                upstream=("web-origin",),
                trust_upgrade_evidence_ref="confirmation-record-1",
            ),
            _node("web-origin", SourceType.WEB_UNTRUSTED),
        )
    if scenario == "missing_upstream":
        return (_node("derived-missing", SourceType.LLM_GENERATED, upstream=("missing-root",)),)
    if scenario == "self_reference":
        return (_node("self", SourceType.WEB_UNTRUSTED, upstream=("self",)),)
    if scenario == "multi_node_cycle":
        return (
            _node("cycle-a", SourceType.WEB_UNTRUSTED, upstream=("cycle-b",)),
            _node("cycle-b", SourceType.LLM_GENERATED, upstream=("cycle-a",)),
        )
    if scenario == "duplicate_fact_ref":
        return (
            _node("dup", SourceType.USER_CONFIRMED),
            _node("dup", SourceType.WEB_UNTRUSTED, value="200.00"),
        )
    if scenario == "duplicate_upstream_ref":
        return (
            _node("root", SourceType.WEB_UNTRUSTED),
            _node("derived", SourceType.LLM_GENERATED, upstream=("root", "root")),
        )
    if scenario == "invalid_direct_source_type":
        return (
            replace(
                _node("bad-source", SourceType.WEB_UNTRUSTED),
                direct_source_type="WEB_UNTRUSTED",  # type: ignore[arg-type]
            ),
        )
    if scenario == "mutable_lookalike_node":
        node = _node("lookalike", SourceType.WEB_UNTRUSTED)
        return (SimpleNamespace(**node.__dict__),)
    if scenario == "serialized_dict_node":
        return (_node("serialized", SourceType.WEB_UNTRUSTED).to_dict(),)
    raise ValueError(f"unknown graph scenario: {scenario}")


def _run_overlay(scenario: str):
    if scenario == "overlay_untrusted_amount_override":
        overlay = AttackOverlay(
            attack_id="MATRIX-AMOUNT",
            title="matrix amount",
            source="offline-page",
            untrusted_content="fixed offline input",
            proposed_overrides={"request.amount": "699.00"},
            source_type=SourceType.WEB_UNTRUSTED,
            source_ref="matrix-page-amount",
        )
    elif scenario == "overlay_untrusted_payee_override":
        overlay = AttackOverlay(
            attack_id="MATRIX-PAYEE",
            title="matrix payee",
            source="offline-llm",
            untrusted_content="fixed offline input",
            proposed_overrides={"request.payee": "payee-evil"},
            source_type=SourceType.LLM_GENERATED,
            source_ref="matrix-llm-payee",
        )
    else:
        raise ValueError(f"unknown overlay scenario: {scenario}")
    boundary = enforce_untrusted_overlay(
        {"request": {"amount": "100.00", "payee": "payee-a"}},
        overlay,
    )
    return {
        "status": boundary.lineage_status.value,
        "reason_codes": list(boundary.lineage_reason_codes),
        "facts": [fact.to_dict() for fact in boundary.lineage_facts],
        "unresolved_fact_refs": [],
        "consumer": "attack_overlay",
    }


def _run_case(scenario: str) -> dict[str, Any]:
    if scenario.startswith("overlay_"):
        return _run_overlay(scenario)
    result = resolve_fact_lineage(_graph_for(scenario))  # type: ignore[arg-type]
    return {
        "status": result.status.value,
        "reason_codes": list(result.reason_codes),
        "facts": [fact.to_dict() for fact in result.resolved_facts],
        "unresolved_fact_refs": list(result.unresolved_fact_refs),
        "consumer": "fact_lineage_resolver",
    }


def build_matrix(spec_path: Path = DEFAULT_SPEC) -> dict[str, Any]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []
    for case in spec["cases"]:
        actual = _run_case(case["scenario"])
        by_ref = {fact["fact_ref"]: fact for fact in actual["facts"]}
        target = by_ref.get(case["target_fact_ref"])
        actual_effective = target["effective_source_types"] if target else []
        actual_untrusted = target["contains_untrusted_ancestry"] if target else None
        actual_resolved_refs = sorted(by_ref)
        comparisons = {
            "status": actual["status"] == case["expected_status"],
            "effective_source_types": actual_effective == case["expected_effective_source_types"],
            "contains_untrusted_ancestry": actual_untrusted == case["expected_contains_untrusted_ancestry"],
            "reason_codes": actual["reason_codes"] == case["expected_reason_codes"],
            "resolved_refs": actual_resolved_refs == case["expected_resolved_refs"],
            "unresolved_refs": actual["unresolved_fact_refs"] == case["expected_unresolved_refs"],
        }
        results.append(
            {
                "case_id": case["case_id"],
                "scenario": case["scenario"],
                "consumer": actual["consumer"],
                "expected_status": case["expected_status"],
                "actual_status": actual["status"],
                "expected_effective_source_types": case["expected_effective_source_types"],
                "actual_effective_source_types": actual_effective,
                "expected_contains_untrusted_ancestry": case["expected_contains_untrusted_ancestry"],
                "actual_contains_untrusted_ancestry": actual_untrusted,
                "expected_reason_codes": case["expected_reason_codes"],
                "actual_reason_codes": actual["reason_codes"],
                "expected_resolved_refs": case["expected_resolved_refs"],
                "actual_resolved_refs": actual_resolved_refs,
                "expected_unresolved_refs": case["expected_unresolved_refs"],
                "actual_unresolved_refs": actual["unresolved_fact_refs"],
                "facts": actual["facts"],
                "comparisons": comparisons,
                "matched": all(comparisons.values()),
                "limitations": dict(spec["limitations"]),
            }
        )
    return {
        "schema": spec["schema"],
        "limitations": spec["limitations"],
        "summary": {
            "total": len(results),
            "matched": sum(item["matched"] for item in results),
            "failed": sum(not item["matched"] for item in results),
        },
        "cases": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    args = parser.parse_args()
    result = build_matrix(args.spec)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Immutable, protocol-neutral fact lineage and source propagation.

The resolver records provenance only. It does not authorize a payment, interpret
natural language, or replace Context Policy. AGENT_DECLARED is preserved but
classified as untrusted ancestry in V1 because a self-declared Agent source is
not independently authoritative evidence.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass

from .context_policy import SourceType
from .execution_facts import VerificationStatus


_UNTRUSTED_ANCESTRY_SOURCE_TYPES = frozenset(
    {
        SourceType.AGENT_DECLARED,
        SourceType.AGENT_INFERRED,
        SourceType.EXTERNAL_TOOL_UNTRUSTED,
        SourceType.WEB_UNTRUSTED,
        SourceType.LLM_GENERATED,
    }
)


@dataclass(frozen=True)
class FactLineageNode:
    """One immutable fact and its direct graph dependencies."""

    fact_ref: str
    fact_path: str
    value_digest: str
    direct_source_type: SourceType
    upstream_fact_refs: tuple[str, ...]
    transformation_ref: str | None = None
    trust_upgrade_evidence_ref: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "fact_ref": self.fact_ref,
            "fact_path": self.fact_path,
            "value_digest": self.value_digest,
            "direct_source_type": self.direct_source_type.value,
            "upstream_fact_refs": list(self.upstream_fact_refs),
            "transformation_ref": self.transformation_ref,
            "trust_upgrade_evidence_ref": self.trust_upgrade_evidence_ref,
        }


@dataclass(frozen=True)
class ResolvedFactLineage:
    """One fact after deterministic upstream source propagation."""

    fact_ref: str
    fact_path: str
    value_digest: str
    direct_source_type: SourceType
    effective_source_types: tuple[SourceType, ...]
    upstream_fact_refs: tuple[str, ...]
    transformation_ref: str | None
    trust_upgrade_evidence_ref: str | None
    contains_untrusted_ancestry: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "fact_ref": self.fact_ref,
            "fact_path": self.fact_path,
            "value_digest": self.value_digest,
            "direct_source_type": self.direct_source_type.value,
            "effective_source_types": [
                source.value for source in self.effective_source_types
            ],
            "upstream_fact_refs": list(self.upstream_fact_refs),
            "transformation_ref": self.transformation_ref,
            "trust_upgrade_evidence_ref": self.trust_upgrade_evidence_ref,
            "contains_untrusted_ancestry": self.contains_untrusted_ancestry,
        }


@dataclass(frozen=True)
class FactLineageResult:
    """Deterministic graph validation and resolution result."""

    status: VerificationStatus
    reason_codes: tuple[str, ...]
    resolved_facts: tuple[ResolvedFactLineage, ...]
    unresolved_fact_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "reason_codes": list(self.reason_codes),
            "resolved_facts": [fact.to_dict() for fact in self.resolved_facts],
            "unresolved_fact_refs": list(self.unresolved_fact_refs),
        }


def resolve_fact_lineage(
    nodes: tuple[FactLineageNode, ...] | None,
) -> FactLineageResult:
    """Validate and resolve an immutable fact graph without side effects.

    Only an exact tuple containing exact FactLineageNode objects crosses the
    object boundary. Invalid lookalikes are rejected before any attribute read.
    """

    if nodes is None:
        return _result(
            VerificationStatus.MISSING_EVIDENCE,
            ("fact_lineage_nodes_missing",),
        )
    if type(nodes) is not tuple:
        return _result(
            VerificationStatus.INVALID,
            ("fact_lineage_nodes_invalid_type",),
        )
    if not nodes:
        return _result(
            VerificationStatus.MISSING_EVIDENCE,
            ("fact_lineage_nodes_missing",),
        )
    if any(type(node) is not FactLineageNode for node in nodes):
        return _result(
            VerificationStatus.INVALID,
            ("fact_lineage_node_invalid_type",),
        )

    missing: list[str] = []
    invalid: list[str] = []
    for index, node in enumerate(nodes):
        identity = _node_identity(node, index)
        _require_text(node.fact_ref, "fact_ref", identity, missing, invalid)
        _require_text(node.fact_path, "fact_path", identity, missing, invalid)
        _require_text(node.value_digest, "value_digest", identity, missing, invalid)

        if node.direct_source_type is None:
            missing.append(f"direct_source_type_missing:{identity}")
        elif type(node.direct_source_type) is not SourceType:
            invalid.append(f"direct_source_type_invalid:{identity}")

        if node.upstream_fact_refs is None:
            missing.append(f"upstream_fact_refs_missing:{identity}")
        elif type(node.upstream_fact_refs) is not tuple:
            invalid.append(f"upstream_fact_refs_invalid_type:{identity}")
        else:
            seen_upstream: set[str] = set()
            for upstream_index, upstream_ref in enumerate(node.upstream_fact_refs):
                if type(upstream_ref) is not str:
                    invalid.append(
                        f"upstream_fact_ref_invalid_type:{identity}:{upstream_index}"
                    )
                    continue
                if not upstream_ref.strip():
                    missing.append(
                        f"upstream_fact_ref_missing:{identity}:{upstream_index}"
                    )
                    continue
                if upstream_ref in seen_upstream:
                    invalid.append(
                        f"duplicate_upstream_fact_ref:{identity}:{upstream_ref}"
                    )
                seen_upstream.add(upstream_ref)
                if type(node.fact_ref) is str and upstream_ref == node.fact_ref:
                    invalid.append(f"upstream_self_reference:{identity}")

        _optional_ref(
            node.transformation_ref,
            "transformation_ref",
            identity,
            invalid,
        )
        _optional_ref(
            node.trust_upgrade_evidence_ref,
            "trust_upgrade_evidence_ref",
            identity,
            invalid,
        )

    if invalid:
        return _result(VerificationStatus.INVALID, _stable_unique(invalid))
    if missing:
        return _result(VerificationStatus.MISSING_EVIDENCE, _stable_unique(missing))

    node_map: dict[str, FactLineageNode] = {}
    duplicate_refs: list[str] = []
    for node in nodes:
        if node.fact_ref in node_map:
            duplicate_refs.append(f"duplicate_fact_ref:{node.fact_ref}")
        node_map[node.fact_ref] = node
    if duplicate_refs:
        return _result(VerificationStatus.INVALID, _stable_unique(duplicate_refs))

    missing_upstream = sorted(
        {
            upstream_ref
            for node in nodes
            for upstream_ref in node.upstream_fact_refs
            if upstream_ref not in node_map
        }
    )
    if missing_upstream:
        return _result(
            VerificationStatus.MISSING_EVIDENCE,
            tuple(f"upstream_fact_missing:{ref}" for ref in missing_upstream),
            unresolved_fact_refs=tuple(missing_upstream),
        )

    indegree = {
        fact_ref: len(node.upstream_fact_refs)
        for fact_ref, node in node_map.items()
    }
    dependents: dict[str, list[str]] = {fact_ref: [] for fact_ref in node_map}
    for node in nodes:
        for upstream_ref in node.upstream_fact_refs:
            dependents[upstream_ref].append(node.fact_ref)
    for refs in dependents.values():
        refs.sort()

    ready = [fact_ref for fact_ref, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    resolved_by_ref: dict[str, ResolvedFactLineage] = {}

    while ready:
        fact_ref = heapq.heappop(ready)
        node = node_map[fact_ref]
        effective = {node.direct_source_type}
        for upstream_ref in node.upstream_fact_refs:
            effective.update(resolved_by_ref[upstream_ref].effective_source_types)
        effective_sources = tuple(sorted(effective, key=lambda item: item.value))
        resolved_by_ref[fact_ref] = ResolvedFactLineage(
            fact_ref=node.fact_ref,
            fact_path=node.fact_path,
            value_digest=node.value_digest,
            direct_source_type=node.direct_source_type,
            effective_source_types=effective_sources,
            upstream_fact_refs=tuple(sorted(node.upstream_fact_refs)),
            transformation_ref=node.transformation_ref,
            trust_upgrade_evidence_ref=node.trust_upgrade_evidence_ref,
            contains_untrusted_ancestry=any(
                source in _UNTRUSTED_ANCESTRY_SOURCE_TYPES
                for source in effective_sources
            ),
        )
        for dependent_ref in dependents[fact_ref]:
            indegree[dependent_ref] -= 1
            if indegree[dependent_ref] == 0:
                heapq.heappush(ready, dependent_ref)

    if len(resolved_by_ref) != len(node_map):
        cyclic_refs = tuple(sorted(set(node_map) - set(resolved_by_ref)))
        return _result(
            VerificationStatus.INVALID,
            ("fact_lineage_cycle_detected",),
            unresolved_fact_refs=cyclic_refs,
        )

    return FactLineageResult(
        status=VerificationStatus.VALID,
        reason_codes=("fact_lineage_valid",),
        resolved_facts=tuple(
            resolved_by_ref[fact_ref] for fact_ref in sorted(resolved_by_ref)
        ),
        unresolved_fact_refs=(),
    )


def _result(
    status: VerificationStatus,
    reason_codes: tuple[str, ...],
    *,
    unresolved_fact_refs: tuple[str, ...] = (),
) -> FactLineageResult:
    return FactLineageResult(
        status=status,
        reason_codes=reason_codes,
        resolved_facts=(),
        unresolved_fact_refs=unresolved_fact_refs,
    )


def _node_identity(node: FactLineageNode, index: int) -> str:
    if type(node.fact_ref) is str and node.fact_ref.strip():
        return node.fact_ref
    return f"index-{index}"


def _require_text(
    value: object,
    field: str,
    identity: str,
    missing: list[str],
    invalid: list[str],
) -> None:
    if value is None:
        missing.append(f"{field}_missing:{identity}")
    elif type(value) is not str:
        invalid.append(f"{field}_invalid_type:{identity}")
    elif not value.strip():
        missing.append(f"{field}_missing:{identity}")


def _optional_ref(
    value: object,
    field: str,
    identity: str,
    invalid: list[str],
) -> None:
    if value is None:
        return
    if type(value) is not str or not value.strip():
        invalid.append(f"{field}_invalid:{identity}")


def _stable_unique(values: list[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))

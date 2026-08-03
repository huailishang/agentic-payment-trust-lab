from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace

from agentic_payment_experiment.trusted_execution import (
    FactLineageNode,
    SourceType,
    VerificationStatus,
    canonical_hash,
    resolve_fact_lineage,
)


def node(
    fact_ref: str,
    source: SourceType,
    *,
    upstream: tuple[str, ...] = (),
    path: str = "request.amount",
    trust_upgrade_evidence_ref: str | None = None,
) -> FactLineageNode:
    return FactLineageNode(
        fact_ref=fact_ref,
        fact_path=path,
        value_digest=canonical_hash({"fact": fact_ref}),
        direct_source_type=source,
        upstream_fact_refs=upstream,
        transformation_ref="rv-transform-v1" if upstream else None,
        trust_upgrade_evidence_ref=trust_upgrade_evidence_ref,
    )


class NodeSubclass(FactLineageNode):
    pass


class ExplodingProxy:
    def __getattribute__(self, name: str):
        raise AssertionError(f"unexpected attribute read: {name}")


valid = node("valid", SourceType.USER_CONFIRMED)
invalid_objects = {
    "mutable_lookalike": SimpleNamespace(**valid.__dict__),
    "serialized_dict": valid.to_dict(),
    "list": [valid],
    "string": "node",
    "subclass": NodeSubclass(**valid.__dict__),
    "exploding_proxy": ExplodingProxy(),
}
invalid_results: dict[str, object] = {}
for name, obj in invalid_objects.items():
    result = resolve_fact_lineage((obj,))  # type: ignore[arg-type]
    assert result.status is VerificationStatus.INVALID
    assert result.reason_codes == ("fact_lineage_node_invalid_type",)
    assert result.resolved_facts == ()
    invalid_results[name] = result.to_dict()

cycle = resolve_fact_lineage(
    (
        node("root", SourceType.SYSTEM_POLICY),
        node("cycle-a", SourceType.WEB_UNTRUSTED, upstream=("cycle-b",)),
        node("cycle-b", SourceType.LLM_GENERATED, upstream=("cycle-a",)),
    )
)
assert cycle.status is VerificationStatus.INVALID
assert cycle.reason_codes == ("fact_lineage_cycle_detected",)
assert cycle.resolved_facts == ()
assert cycle.unresolved_fact_refs == ("cycle-a", "cycle-b")

missing = resolve_fact_lineage(
    (
        node("root-safe", SourceType.SYSTEM_POLICY),
        node("derived-missing", SourceType.LLM_GENERATED, upstream=("absent",)),
    )
)
assert missing.status is VerificationStatus.MISSING_EVIDENCE
assert missing.resolved_facts == ()
assert missing.unresolved_fact_refs == ("absent",)

web = node("web", SourceType.WEB_UNTRUSTED)
claimed = node(
    "claimed",
    SourceType.USER_CONFIRMED,
    upstream=("web",),
    trust_upgrade_evidence_ref="confirmation-1",
)
upgrade = resolve_fact_lineage((claimed, web))
claimed_fact = next(item for item in upgrade.resolved_facts if item.fact_ref == "claimed")
assert claimed_fact.effective_source_types == (
    SourceType.USER_CONFIRMED,
    SourceType.WEB_UNTRUSTED,
)
assert claimed_fact.contains_untrusted_ancestry is True

user = node("user", SourceType.USER_CONFIRMED)
derived = node(
    "derived",
    SourceType.AGENT_INFERRED,
    upstream=("user", "web"),
)
first = resolve_fact_lineage((derived, web, user))
second = resolve_fact_lineage((user, derived, web))
assert first == second
resolved_derived = next(item for item in first.resolved_facts if item.fact_ref == "derived")
assert resolved_derived.effective_source_types == (
    SourceType.AGENT_INFERRED,
    SourceType.USER_CONFIRMED,
    SourceType.WEB_UNTRUSTED,
)

agent_declared = resolve_fact_lineage((node("declared", SourceType.AGENT_DECLARED),))
assert agent_declared.resolved_facts[0].contains_untrusted_ancestry is True
clean = resolve_fact_lineage(
    (
        node("policy", SourceType.SYSTEM_POLICY),
        node("confirmed", SourceType.USER_CONFIRMED, upstream=("policy",)),
    )
)
assert all(not item.contains_untrusted_ancestry for item in clean.resolved_facts)

try:
    valid.fact_ref = "mutated"  # type: ignore[misc]
    raise AssertionError("FactLineageNode was mutable")
except FrozenInstanceError:
    pass

primitive = first.to_dict()
json.dumps(primitive, ensure_ascii=False, sort_keys=True)

module_path = Path("src/agentic_payment_experiment/trusted_execution/fact_lineage.py")
source = module_path.read_text(encoding="utf-8")
tree = ast.parse(source)
imports: set[str] = set()
calls: set[str] = set()
for item in ast.walk(tree):
    if isinstance(item, ast.Import):
        imports.update(alias.name.split(".")[0] for alias in item.names)
    elif isinstance(item, ast.ImportFrom) and item.module:
        imports.add(item.module.split(".")[0])
    elif isinstance(item, ast.Call):
        if isinstance(item.func, ast.Name):
            calls.add(item.func.id)
        elif isinstance(item.func, ast.Attribute):
            calls.add(item.func.attr)
assert imports.isdisjoint({"os", "subprocess", "socket", "requests", "urllib", "pathlib"})
assert calls.isdisjoint({"open", "write_text", "write_bytes", "system", "popen", "run", "urlopen"})
assert "Decision" not in source and "ALLOW" not in source and "DENY" not in source

print(
    json.dumps(
        {
            "invalid_exact_type_boundary": invalid_results,
            "cycle": cycle.to_dict(),
            "missing_upstream": missing.to_dict(),
            "trust_upgrade": claimed_fact.to_dict(),
            "multi_source": resolved_derived.to_dict(),
            "agent_declared_untrusted": agent_declared.resolved_facts[0].to_dict(),
            "clean_chain": [item.to_dict() for item in clean.resolved_facts],
            "deterministic_order_independent": first == second,
            "frozen_contract": True,
            "primitive_serialization": True,
            "pure_resolver_static_audit": True,
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
)

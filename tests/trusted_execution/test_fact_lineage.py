from __future__ import annotations

import ast
import importlib.util
import json
import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_payment_experiment import (
    FactLineageNode as RootFactLineageNode,
    FactLineageResult as RootFactLineageResult,
    ResolvedFactLineage as RootResolvedFactLineage,
    resolve_fact_lineage as root_resolve_fact_lineage,
)
from agentic_payment_experiment.trusted_execution import (
    FactLineageNode,
    FactLineageResult,
    ResolvedFactLineage,
    SourceType,
    VerificationStatus,
    canonical_hash,
    resolve_fact_lineage,
)

MODULE_PATH = SRC / "agentic_payment_experiment" / "trusted_execution" / "fact_lineage.py"
MATRIX_PATH = ROOT / "samples" / "attacks" / "fact_lineage_matrix_v1.json"
RUNNER_PATH = ROOT / "scripts" / "validation" / "run_fact_lineage_matrix.py"


def _primitive_only(value: object) -> bool:
    if value is None or type(value) in {str, int, float, bool}:
        return True
    if isinstance(value, list):
        return all(_primitive_only(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _primitive_only(item) for key, item in value.items())
    return False


def _node(
    fact_ref: str,
    source: SourceType = SourceType.USER_CONFIRMED,
    *,
    upstream: tuple[str, ...] = (),
    path: str = "request.amount",
    value: object = "100.00",
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


def _load_matrix_runner():
    spec = importlib.util.spec_from_file_location("fact_lineage_matrix_runner", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load fact lineage matrix runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FactLineageTest(unittest.TestCase):
    def test_public_contracts_are_frozen_exported_and_primitive_only(self) -> None:
        node = _node("root", transformation_ref="extract-v1")
        result = resolve_fact_lineage((node,))
        resolved = result.resolved_facts[0]

        self.assertIs(FactLineageNode, RootFactLineageNode)
        self.assertIs(FactLineageResult, RootFactLineageResult)
        self.assertIs(ResolvedFactLineage, RootResolvedFactLineage)
        self.assertIs(resolve_fact_lineage, root_resolve_fact_lineage)
        self.assertTrue(_primitive_only(node.to_dict()))
        self.assertTrue(_primitive_only(resolved.to_dict()))
        self.assertTrue(_primitive_only(result.to_dict()))
        json.dumps(result.to_dict(), sort_keys=True)
        with self.assertRaises(FrozenInstanceError):
            node.fact_ref = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            resolved.contains_untrusted_ancestry = True  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            result.status = VerificationStatus.INVALID  # type: ignore[misc]

    def test_exact_outer_container_and_node_type_boundaries_precede_attribute_access(self) -> None:
        class NodeSubclass(FactLineageNode):
            pass

        class ExplodingProxy:
            def __getattribute__(self, name):
                raise AssertionError(f"attribute read: {name}")

            def __eq__(self, other):
                raise AssertionError("comparison attempted")

        valid = _node("valid")
        invalid_nodes = (
            SimpleNamespace(**valid.__dict__),
            valid.to_dict(),
            [valid],
            "fact",
            NodeSubclass(**valid.__dict__),
            ExplodingProxy(),
        )
        for invalid in invalid_nodes:
            with self.subTest(kind=type(invalid).__name__):
                result = resolve_fact_lineage((invalid,))  # type: ignore[arg-type]
                self.assertEqual(VerificationStatus.INVALID, result.status)
                self.assertEqual(("fact_lineage_node_invalid_type",), result.reason_codes)
                self.assertEqual((), result.resolved_facts)

        for invalid_container in ([valid], "nodes", {"node": valid}, ExplodingProxy()):
            with self.subTest(container=type(invalid_container).__name__):
                result = resolve_fact_lineage(invalid_container)  # type: ignore[arg-type]
                self.assertEqual(VerificationStatus.INVALID, result.status)
                self.assertEqual(("fact_lineage_nodes_invalid_type",), result.reason_codes)

    def test_missing_and_invalid_fields_have_stable_classification(self) -> None:
        base = _node("base")
        missing_cases = (
            (replace(base, fact_ref=""), "fact_ref_missing:index-0"),
            (replace(base, fact_path=""), "fact_path_missing:base"),
            (replace(base, value_digest=""), "value_digest_missing:base"),
            (replace(base, direct_source_type=None), "direct_source_type_missing:base"),  # type: ignore[arg-type]
            (replace(base, upstream_fact_refs=None), "upstream_fact_refs_missing:base"),  # type: ignore[arg-type]
            (replace(base, upstream_fact_refs=("",)), "upstream_fact_ref_missing:base:0"),
        )
        for node, reason in missing_cases:
            with self.subTest(reason=reason):
                result = resolve_fact_lineage((node,))
                self.assertEqual(VerificationStatus.MISSING_EVIDENCE, result.status)
                self.assertIn(reason, result.reason_codes)

        invalid_cases = (
            (replace(base, fact_path=7), "fact_path_invalid_type:base"),  # type: ignore[arg-type]
            (replace(base, direct_source_type="USER_CONFIRMED"), "direct_source_type_invalid:base"),  # type: ignore[arg-type]
            (replace(base, upstream_fact_refs=[]), "upstream_fact_refs_invalid_type:base"),  # type: ignore[arg-type]
            (replace(base, upstream_fact_refs=(7,)), "upstream_fact_ref_invalid_type:base:0"),  # type: ignore[arg-type]
            (replace(base, transformation_ref=""), "transformation_ref_invalid:base"),
            (replace(base, trust_upgrade_evidence_ref=""), "trust_upgrade_evidence_ref_invalid:base"),
        )
        for node, reason in invalid_cases:
            with self.subTest(reason=reason):
                result = resolve_fact_lineage((node,))
                self.assertEqual(VerificationStatus.INVALID, result.status)
                self.assertIn(reason, result.reason_codes)

        for nodes in (None, ()):
            result = resolve_fact_lineage(nodes)
            self.assertEqual(VerificationStatus.MISSING_EVIDENCE, result.status)
            self.assertEqual(("fact_lineage_nodes_missing",), result.reason_codes)

    def test_graph_integrity_failures_do_not_return_partial_resolution(self) -> None:
        cases = (
            (
                (_node("derived", upstream=("missing",)),),
                VerificationStatus.MISSING_EVIDENCE,
                ("upstream_fact_missing:missing",),
                ("missing",),
            ),
            (
                (_node("self", upstream=("self",)),),
                VerificationStatus.INVALID,
                ("upstream_self_reference:self",),
                (),
            ),
            (
                (_node("a", upstream=("b",)), _node("b", upstream=("a",))),
                VerificationStatus.INVALID,
                ("fact_lineage_cycle_detected",),
                ("a", "b"),
            ),
            (
                (_node("dup"), _node("dup", SourceType.WEB_UNTRUSTED)),
                VerificationStatus.INVALID,
                ("duplicate_fact_ref:dup",),
                (),
            ),
            (
                (_node("root"), _node("derived", upstream=("root", "root"))),
                VerificationStatus.INVALID,
                ("duplicate_upstream_fact_ref:derived:root",),
                (),
            ),
        )
        for nodes, status, reasons, unresolved in cases:
            with self.subTest(reasons=reasons):
                result = resolve_fact_lineage(nodes)
                self.assertEqual(status, result.status)
                self.assertEqual(reasons, result.reason_codes)
                self.assertEqual((), result.resolved_facts)
                self.assertEqual(unresolved, result.unresolved_fact_refs)

    def test_source_propagation_retains_web_and_llm_ancestors(self) -> None:
        web = _node("web", SourceType.WEB_UNTRUSTED)
        summary = _node(
            "summary",
            SourceType.LLM_GENERATED,
            upstream=("web",),
            transformation_ref="summarize-v1",
        )
        result = resolve_fact_lineage((summary, web))
        by_ref = {fact.fact_ref: fact for fact in result.resolved_facts}
        self.assertEqual(VerificationStatus.VALID, result.status)
        self.assertEqual(
            (SourceType.LLM_GENERATED, SourceType.WEB_UNTRUSTED),
            by_ref["summary"].effective_source_types,
        )
        self.assertTrue(by_ref["summary"].contains_untrusted_ancestry)

    def test_multi_source_propagation_unions_every_ancestor(self) -> None:
        nodes = (
            _node("user", SourceType.USER_CONFIRMED),
            _node("web", SourceType.WEB_UNTRUSTED),
            _node(
                "derived",
                SourceType.AGENT_INFERRED,
                upstream=("web", "user"),
            ),
        )
        result = resolve_fact_lineage(nodes)
        derived = next(fact for fact in result.resolved_facts if fact.fact_ref == "derived")
        self.assertEqual(
            (
                SourceType.AGENT_INFERRED,
                SourceType.USER_CONFIRMED,
                SourceType.WEB_UNTRUSTED,
            ),
            derived.effective_source_types,
        )

    def test_claimed_trust_upgrade_never_erases_web_ancestry(self) -> None:
        web = _node("web", SourceType.WEB_UNTRUSTED)
        for evidence_ref in (None, "confirmation-record-1"):
            with self.subTest(evidence_ref=evidence_ref):
                claimed = _node(
                    "claimed",
                    SourceType.USER_CONFIRMED,
                    upstream=("web",),
                    trust_upgrade_evidence_ref=evidence_ref,
                )
                result = resolve_fact_lineage((claimed, web))
                resolved = next(fact for fact in result.resolved_facts if fact.fact_ref == "claimed")
                self.assertEqual(
                    (SourceType.USER_CONFIRMED, SourceType.WEB_UNTRUSTED),
                    resolved.effective_source_types,
                )
                self.assertTrue(resolved.contains_untrusted_ancestry)
                self.assertEqual(evidence_ref, resolved.trust_upgrade_evidence_ref)

    def test_untrusted_ancestry_classification_is_explicit_for_every_source(self) -> None:
        untrusted = {
            SourceType.AGENT_DECLARED,
            SourceType.AGENT_INFERRED,
            SourceType.EXTERNAL_TOOL_UNTRUSTED,
            SourceType.WEB_UNTRUSTED,
            SourceType.LLM_GENERATED,
        }
        trusted = {
            SourceType.USER_CONFIRMED,
            SourceType.SYSTEM_POLICY,
            SourceType.MERCHANT_PROVIDED,
            SourceType.PROTOCOL_VERIFIED,
            SourceType.PAYMENT_PROVIDER_OBSERVED,
        }
        self.assertEqual(set(SourceType), untrusted | trusted)
        for source in sorted(untrusted, key=lambda item: item.value):
            with self.subTest(source=source.value):
                resolved = resolve_fact_lineage((_node("root", source),)).resolved_facts[0]
                self.assertTrue(resolved.contains_untrusted_ancestry)
        for source in sorted(trusted, key=lambda item: item.value):
            with self.subTest(source=source.value):
                resolved = resolve_fact_lineage((_node("root", source),)).resolved_facts[0]
                self.assertFalse(resolved.contains_untrusted_ancestry)

    def test_resolution_is_order_independent_deterministic_and_does_not_mutate_inputs(self) -> None:
        nodes = (
            _node("z", SourceType.LLM_GENERATED, upstream=("a",)),
            _node("a", SourceType.WEB_UNTRUSTED),
        )
        before = tuple(nodes)
        first = resolve_fact_lineage(nodes)
        second = resolve_fact_lineage(tuple(reversed(nodes)))
        self.assertEqual(first, second)
        self.assertEqual(("a", "z"), tuple(f.fact_ref for f in first.resolved_facts))
        self.assertEqual(before, nodes)

    def test_long_chain_uses_non_recursive_resolution(self) -> None:
        nodes = []
        for index in range(1500):
            ref = f"fact-{index:04d}"
            upstream = () if index == 0 else (f"fact-{index - 1:04d}",)
            source = SourceType.WEB_UNTRUSTED if index == 0 else SourceType.SYSTEM_POLICY
            nodes.append(_node(ref, source, upstream=upstream))
        result = resolve_fact_lineage(tuple(reversed(nodes)))
        self.assertEqual(VerificationStatus.VALID, result.status)
        self.assertEqual(1500, len(result.resolved_facts))
        final = next(fact for fact in result.resolved_facts if fact.fact_ref == "fact-1499")
        self.assertIn(SourceType.WEB_UNTRUSTED, final.effective_source_types)
        self.assertTrue(final.contains_untrusted_ancestry)

    def test_machine_matrix_is_complete_matched_and_primitive_only(self) -> None:
        result = _load_matrix_runner().build_matrix(MATRIX_PATH)
        self.assertEqual({"total": 16, "matched": 16, "failed": 0}, result["summary"])
        required_ids = {
            "root_user_confirmed",
            "root_web_untrusted",
            "web_to_llm_summary",
            "multi_source_user_and_web",
            "claimed_user_confirmation_with_web_ancestor",
            "claimed_upgrade_with_evidence_and_web_ancestor",
            "missing_upstream",
            "self_reference",
            "multi_node_cycle",
            "duplicate_fact_ref",
            "duplicate_upstream_ref",
            "invalid_direct_source_type",
            "mutable_lookalike_node",
            "serialized_dict_node",
            "overlay_untrusted_amount_override",
            "overlay_untrusted_payee_override",
        }
        self.assertEqual(required_ids, {item["case_id"] for item in result["cases"]})
        self.assertTrue(_primitive_only(result))
        for item in result["cases"]:
            self.assertTrue(item["matched"], item["case_id"])
            self.assertTrue(item["limitations"]["no_llm"])
            self.assertTrue(item["limitations"]["no_network"])
            self.assertTrue(item["limitations"]["no_payment"])

    def test_production_resolver_has_no_io_network_process_environment_or_policy_decision(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_roots = set()
        called_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_names.add(node.func.attr)
        self.assertTrue(imported_roots.isdisjoint({"os", "subprocess", "socket", "requests", "urllib", "pathlib"}))
        self.assertTrue(called_names.isdisjoint({"open", "write_text", "write_bytes", "system", "popen", "run", "urlopen"}))
        self.assertNotIn("Decision", source)
        self.assertNotIn("ALLOW", source)
        self.assertNotIn("DENY", source)


if __name__ == "__main__":
    unittest.main()

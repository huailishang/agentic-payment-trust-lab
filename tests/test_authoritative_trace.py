from __future__ import annotations

import hashlib
import json
import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment.authoritative_trace import (
    ACCEPTED_FORMULA_REGISTRY_SHA256,
    ACCEPTED_PROFILES_SHA256,
    ACCEPTED_PROJECTION_REGISTRY_SHA256,
    ACCEPTED_RUNTIME_CONTRACT_SHA256,
    ProductAuthoritativeTrace,
    TraceContractError,
    TraceSourceBinding,
    TraceValidationStatus,
    canonical_primitive,
    compute_binding_ref,
    compute_projection_source_ref,
    runtime_contract_primitive,
    runtime_registry_hashes,
    trace_binding_from_mapping,
    trace_from_mapping,
    validate_product_authoritative_trace,
    validate_trace_source_binding,
)

ROOT = Path(__file__).resolve().parents[1]
ACCEPTED_COVERAGE = (
    ROOT
    / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-01-coverage-projection-identity-formula.json"
)
IDENTITY_VECTORS = (
    ROOT
    / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-01-projection-identity-vectors.json"
)
T10_INSTANCE = (
    ROOT
    / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1/evidence/EV-01-t10-grounded-instance.json"
)
T12_EXAMPLES = (
    ROOT
    / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1/evidence/EV-01-t12-sidecar-examples.json"
)
MODULE_PATH = ROOT / "src/agentic_payment_experiment/authoritative_trace.py"


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _replace_binding(
    trace: ProductAuthoritativeTrace,
    index: int,
    binding: TraceSourceBinding,
    *,
    update_event_refs: bool = True,
) -> ProductAuthoritativeTrace:
    bindings = list(trace.source_bindings)
    old_ref = bindings[index].binding_ref
    bindings[index] = binding
    events = trace.events
    if update_event_refs:
        events = tuple(
            replace(event, source_binding_ref=binding.binding_ref)
            if event.source_binding_ref == old_ref
            else event
            for event in trace.events
        )
    return replace(trace, source_bindings=tuple(bindings), events=events)


class _ExampleEnum(str, Enum):
    VALUE = "VALUE"


class AuthoritativeTraceContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.coverage = json.loads(ACCEPTED_COVERAGE.read_text(encoding="utf-8"))
        cls.vectors = json.loads(IDENTITY_VECTORS.read_text(encoding="utf-8"))
        cls.t10_data = json.loads(T10_INSTANCE.read_text(encoding="utf-8"))
        cls.t12_data = json.loads(T12_EXAMPLES.read_text(encoding="utf-8"))
        cls.trace = trace_from_mapping(cls.t10_data)

    def test_embedded_registry_hashes_match_accepted_contract(self) -> None:
        hashes = dict(runtime_registry_hashes())
        self.assertEqual(ACCEPTED_FORMULA_REGISTRY_SHA256, hashes["formula_registry"])
        self.assertEqual(
            ACCEPTED_PROJECTION_REGISTRY_SHA256,
            hashes["projection_registry"],
        )
        self.assertEqual(ACCEPTED_PROFILES_SHA256, hashes["profiles"])
        self.assertEqual(ACCEPTED_RUNTIME_CONTRACT_SHA256, hashes["runtime_contract"])

        embedded = runtime_contract_primitive()
        expected = {
            key: self.coverage[key]
            for key in (
                "projection_identity_formula_registry",
                "projection_registry",
                "tasks",
                "forbidden_projection_fields",
                "reference_model",
                "canonical_decimal",
            )
        }
        self.assertEqual(expected, embedded)
        self.assertEqual(
            ACCEPTED_RUNTIME_CONTRACT_SHA256,
            _canonical_hash(embedded),
        )

    def test_runtime_module_has_no_docs_or_evidence_file_dependency(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("Path(", source)
        self.assertNotIn("open(", source)
        self.assertNotIn("read_text(", source)
        self.assertNotIn("CURRENT.md", source)
        self.assertNotIn("EV-01-build-grounded-reference-model", source)
        self.assertNotIn("GateContext", source)
        self.assertIn("_RUNTIME_CONTRACT_JSON", source)

    def test_public_contract_is_frozen_and_projection_is_deeply_immutable(self) -> None:
        binding = self.trace.source_bindings[0]
        with self.assertRaises(FrozenInstanceError):
            binding.source_object_ref = "changed"  # type: ignore[misc]
        with self.assertRaises(TypeError):
            binding.projection["mandate_id"] = "changed"  # type: ignore[index]
        with self.assertRaises(FrozenInstanceError):
            self.trace.profile = "changed"  # type: ignore[misc]

    def test_public_ordered_collections_are_copied_to_tuples(self) -> None:
        source_event = self.trace.events[1]
        assertions = list(source_event.relations[0].target_binding_assertions)
        relation = replace(
            source_event.relations[0],
            target_binding_assertions=assertions,  # type: ignore[arg-type]
        )
        assertions.clear()
        self.assertIsInstance(relation.target_binding_assertions, tuple)
        self.assertEqual(1, len(relation.target_binding_assertions))

        relations = [relation]
        event = replace(
            source_event,
            reason_codes=list(source_event.reason_codes),  # type: ignore[arg-type]
            relations=relations,  # type: ignore[arg-type]
        )
        relations.clear()
        self.assertIsInstance(event.reason_codes, tuple)
        self.assertIsInstance(event.relations, tuple)
        self.assertEqual(1, len(event.relations))

        events = [self.trace.events[0], event, *self.trace.events[2:]]
        bindings = list(self.trace.source_bindings)
        reasons = ["trace_reason"]
        trace = replace(
            self.trace,
            reason_codes=reasons,  # type: ignore[arg-type]
            events=events,  # type: ignore[arg-type]
            source_bindings=bindings,  # type: ignore[arg-type]
        )
        reasons.clear()
        events.clear()
        bindings.clear()
        self.assertEqual(("trace_reason",), trace.reason_codes)
        self.assertIsInstance(trace.events, tuple)
        self.assertIsInstance(trace.source_bindings, tuple)
        self.assertEqual(len(self.trace.events), len(trace.events))
        self.assertEqual(len(self.trace.source_bindings), len(trace.source_bindings))

    def test_canonical_primitive_closed_set(self) -> None:
        value = {
            "none": None,
            "bool": True,
            "int": 7,
            "str": "文本",
            "decimal": Decimal("1.00"),
            "negative_zero": Decimal("-0"),
            "enum": _ExampleEnum.VALUE,
            "datetime": datetime(2026, 8, 5, 1, 2, 3, tzinfo=timezone.utc),
            "tuple": ("a", Decimal("0.10")),
        }
        self.assertEqual(
            {
                "none": None,
                "bool": True,
                "int": 7,
                "str": "文本",
                "decimal": "1",
                "negative_zero": "0",
                "enum": "VALUE",
                "datetime": "2026-08-05T01:02:03+00:00",
                "tuple": ["a", "0.1"],
            },
            canonical_primitive(value),
        )

    def test_float_nan_infinity_and_unsupported_values_fail_closed(self) -> None:
        for value in (1.0, float("nan"), float("inf"), object()):
            with self.subTest(value=repr(value)):
                with self.assertRaises(TraceContractError):
                    canonical_primitive(value)

    def test_all_nine_hash_identity_vectors_and_binding_digests_recompute(self) -> None:
        positives = self.vectors["positive_vectors"]
        self.assertEqual(9, len(positives))
        for item in positives:
            with self.subTest(schema=item["projection_schema"]):
                source_ref = compute_projection_source_ref(
                    item["source_object_type"],
                    item["projection_schema"],
                    item["projection"],
                )
                self.assertEqual(item["expected_source_object_ref"], source_ref)
                binding = TraceSourceBinding(
                    binding_ref=item["expected_binding_ref"],
                    source_object_type=item["source_object_type"],
                    source_object_ref=source_ref,
                    projection_schema=item["projection_schema"],
                    projection=item["projection"],
                )
                self.assertEqual(item["expected_binding_ref"], compute_binding_ref(binding))
                self.assertEqual(
                    TraceValidationStatus.VALID,
                    validate_trace_source_binding(binding).status,
                )

    def test_native_identity_and_all_t10_binding_digests_recompute(self) -> None:
        self.assertEqual(11, len(self.trace.source_bindings))
        for binding in self.trace.source_bindings:
            with self.subTest(schema=binding.projection_schema):
                self.assertEqual(
                    binding.source_object_ref,
                    compute_projection_source_ref(
                        binding.source_object_type,
                        binding.projection_schema,
                        binding.projection,
                    ),
                )
                self.assertEqual(binding.binding_ref, compute_binding_ref(binding))
                self.assertEqual(
                    TraceValidationStatus.VALID,
                    validate_trace_source_binding(binding).status,
                )

    def test_t10_exact_synthetic_envelope_is_valid(self) -> None:
        result = validate_product_authoritative_trace(self.trace)
        self.assertEqual(TraceValidationStatus.VALID, result.status)
        self.assertEqual(("product_authoritative_trace_valid",), result.reason_codes)
        self.assertEqual(12, len(self.trace.events))
        self.assertEqual(11, len(self.trace.source_bindings))
        self.assertEqual(12, len(result.event_types))

    def test_t10_two_order_roles_share_one_binding(self) -> None:
        orders = [event for event in self.trace.events if event.event_type == "ORDER_RECORDED"]
        self.assertEqual(2, len(orders))
        self.assertEqual(
            {"AUTHORIZED_ORDER_SNAPSHOT", "CURRENT_ORDER_SNAPSHOT"},
            {event.entity_role for event in orders},
        )
        self.assertEqual(1, len({event.source_binding_ref for event in orders}))
        self.assertEqual(1, len({event.entity_ref for event in orders}))

    def test_t10_relation_targets_are_resolved(self) -> None:
        identities = {
            (event.entity_type, event.entity_role, event.entity_ref)
            for event in self.trace.events
        }
        relation_count = 0
        for event in self.trace.events:
            for relation in event.relations:
                relation_count += 1
                self.assertIn(
                    (
                        relation.target_entity_type,
                        relation.target_entity_role,
                        relation.target_entity_ref,
                    ),
                    identities,
                )
                self.assertIsNot(False, relation.target_resolved)
        self.assertEqual(16, relation_count)

    def test_t12_conflict_and_sidecar_bindings_recompute(self) -> None:
        for key in ("conflict_fact", "sidecar_result"):
            with self.subTest(key=key):
                binding = trace_binding_from_mapping(self.t12_data[key])
                self.assertEqual(
                    binding.source_object_ref,
                    compute_projection_source_ref(
                        binding.source_object_type,
                        binding.projection_schema,
                        binding.projection,
                    ),
                )
                self.assertEqual(binding.binding_ref, compute_binding_ref(binding))
                self.assertEqual(
                    TraceValidationStatus.VALID,
                    validate_trace_source_binding(binding).status,
                )
        self.assertIsNone(self.t12_data["sidecar_decision_extraction"])

    def test_sidecar_fabricated_decision_is_invalid_extra_field(self) -> None:
        original = self.t12_data["sidecar_result"]
        projection = dict(original["projection"])
        projection["decision"] = "ALLOW"
        binding = TraceSourceBinding(
            binding_ref=original["binding_ref"],
            source_object_type=original["source_object_type"],
            source_object_ref=original["source_object_ref"],
            projection_schema=original["projection_schema"],
            projection=projection,
        )
        result = validate_trace_source_binding(binding)
        self.assertEqual(TraceValidationStatus.INVALID, result.status)
        self.assertEqual(("trace_projection_field_extra",), result.reason_codes)

    def test_result_projection_containing_authoritative_trace_is_invalid(self) -> None:
        original = self.t12_data["sidecar_result"]
        projection = dict(original["projection"])
        projection["authoritative_trace"] = {}
        binding = TraceSourceBinding(
            binding_ref=original["binding_ref"],
            source_object_type=original["source_object_type"],
            source_object_ref=original["source_object_ref"],
            projection_schema=original["projection_schema"],
            projection=projection,
        )
        result = validate_trace_source_binding(binding)
        self.assertEqual(TraceValidationStatus.INVALID, result.status)

    def test_missing_projection_field_is_indeterminate(self) -> None:
        original = self.trace.source_bindings[0]
        projection = dict(original.projection)
        projection.pop("mandate_id")
        binding = replace(original, projection=projection)
        result = validate_trace_source_binding(binding)
        self.assertEqual(TraceValidationStatus.INDETERMINATE, result.status)
        self.assertEqual(("trace_projection_field_missing",), result.reason_codes)

    def test_extra_projection_field_is_invalid(self) -> None:
        original = self.trace.source_bindings[0]
        projection = dict(original.projection)
        projection["extra"] = "x"
        result = validate_trace_source_binding(replace(original, projection=projection))
        self.assertEqual(TraceValidationStatus.INVALID, result.status)
        self.assertEqual(("trace_projection_field_extra",), result.reason_codes)

    def test_unknown_projection_schema_is_indeterminate(self) -> None:
        binding = replace(self.trace.source_bindings[0], projection_schema="unknown/v1")
        result = validate_trace_source_binding(binding)
        self.assertEqual(TraceValidationStatus.INDETERMINATE, result.status)
        self.assertEqual(("trace_projection_schema_unknown",), result.reason_codes)

    def test_native_and_hash_identity_mismatch_are_invalid(self) -> None:
        native = replace(self.trace.source_bindings[0], source_object_ref="IntentMandate:wrong")
        self.assertEqual(
            ("trace_source_object_ref_mismatch",),
            validate_trace_source_binding(native).reason_codes,
        )
        hashed = next(
            binding
            for binding in self.trace.source_bindings
            if ":projection-sha256:" in binding.source_object_ref
        )
        digest = hashed.source_object_ref.rsplit(":", 1)[1]
        uppercase = replace(
            hashed,
            source_object_ref=hashed.source_object_ref[: -len(digest)] + digest.upper(),
        )
        self.assertEqual(
            TraceValidationStatus.INVALID,
            validate_trace_source_binding(uppercase).status,
        )

    def test_wrong_source_and_unknown_profile_fail_closed(self) -> None:
        wrong_source = validate_product_authoritative_trace(
            replace(self.trace, source="EVALUATOR_REPLAY")
        )
        self.assertEqual(TraceValidationStatus.INVALID, wrong_source.status)
        self.assertEqual(("trace_source_invalid",), wrong_source.reason_codes)
        unknown = validate_product_authoritative_trace(
            replace(self.trace, profile="UNKNOWN_PROFILE")
        )
        self.assertEqual(TraceValidationStatus.INDETERMINATE, unknown.status)
        self.assertEqual(("trace_profile_unknown",), unknown.reason_codes)

    def test_missing_extra_and_reordered_events_have_exact_statuses(self) -> None:
        missing = validate_product_authoritative_trace(
            replace(self.trace, events=self.trace.events[:-1])
        )
        self.assertEqual(TraceValidationStatus.INDETERMINATE, missing.status)
        self.assertEqual(("trace_event_missing",), missing.reason_codes)

        extra = validate_product_authoritative_trace(
            replace(self.trace, events=self.trace.events + (self.trace.events[-1],))
        )
        self.assertEqual(TraceValidationStatus.INVALID, extra.status)
        self.assertEqual(("trace_event_extra",), extra.reason_codes)

        reordered_events = list(self.trace.events)
        reordered_events[0], reordered_events[1] = reordered_events[1], reordered_events[0]
        reordered = validate_product_authoritative_trace(
            replace(self.trace, events=tuple(reordered_events))
        )
        self.assertEqual(TraceValidationStatus.INVALID, reordered.status)
        self.assertEqual(("trace_event_sequence_invalid",), reordered.reason_codes)

    def test_missing_duplicate_and_unreferenced_bindings_have_exact_statuses(self) -> None:
        missing = validate_product_authoritative_trace(
            replace(self.trace, source_bindings=self.trace.source_bindings[1:])
        )
        self.assertEqual(TraceValidationStatus.INDETERMINATE, missing.status)
        self.assertEqual(("trace_event_binding_unresolved",), missing.reason_codes)

        duplicate = validate_product_authoritative_trace(
            replace(
                self.trace,
                source_bindings=self.trace.source_bindings
                + (self.trace.source_bindings[0],),
            )
        )
        self.assertEqual(TraceValidationStatus.INVALID, duplicate.status)
        self.assertEqual(("trace_binding_ref_duplicate",), duplicate.reason_codes)

        unreferenced = replace(
            self.trace.source_bindings[0],
            binding_ref="TraceSourceBinding:sha256:" + "a" * 64,
        )
        result = validate_product_authoritative_trace(
            replace(
                self.trace,
                source_bindings=self.trace.source_bindings + (unreferenced,),
            )
        )
        self.assertEqual(TraceValidationStatus.INVALID, result.status)
        self.assertEqual(("trace_binding_unreferenced",), result.reason_codes)

    def test_binding_digest_mismatch_is_invalid(self) -> None:
        original = self.trace.source_bindings[0]
        bad = replace(
            original,
            binding_ref="TraceSourceBinding:sha256:" + "b" * 64,
        )
        trace = _replace_binding(self.trace, 0, bad)
        result = validate_product_authoritative_trace(trace)
        self.assertEqual(TraceValidationStatus.INVALID, result.status)
        self.assertEqual(("trace_binding_digest_mismatch",), result.reason_codes)

    def test_unresolved_source_binding_is_indeterminate(self) -> None:
        events = list(self.trace.events)
        events[0] = replace(
            events[0],
            source_binding_ref="TraceSourceBinding:sha256:" + "c" * 64,
        )
        result = validate_product_authoritative_trace(
            replace(self.trace, events=tuple(events))
        )
        self.assertEqual(TraceValidationStatus.INDETERMINATE, result.status)
        self.assertEqual(("trace_event_binding_unresolved",), result.reason_codes)

    def test_entity_and_relation_tamper_are_invalid(self) -> None:
        events = list(self.trace.events)
        events[0] = replace(events[0], entity_ref="IntentMandate:wrong")
        entity_result = validate_product_authoritative_trace(
            replace(self.trace, events=tuple(events))
        )
        self.assertEqual(TraceValidationStatus.INVALID, entity_result.status)
        self.assertEqual(("trace_entity_ref_mismatch",), entity_result.reason_codes)

        events = list(self.trace.events)
        event = events[1]
        relation = event.relations[0]
        events[1] = replace(
            event,
            relations=(replace(relation, target_entity_ref="IntentMandate:wrong"),),
        )
        relation_result = validate_product_authoritative_trace(
            replace(self.trace, events=tuple(events))
        )
        self.assertEqual(TraceValidationStatus.INVALID, relation_result.status)
        self.assertEqual(
            ("trace_relation_target_ref_mismatch",),
            relation_result.reason_codes,
        )

    def test_target_binding_assertion_tamper_is_invalid(self) -> None:
        events = list(self.trace.events)
        event = events[1]
        relation = event.relations[0]
        assertion = relation.target_binding_assertions[0]
        events[1] = replace(
            event,
            relations=(
                replace(
                    relation,
                    target_binding_assertions=(
                        replace(assertion, target_value="wrong"),
                    ),
                ),
            ),
        )
        result = validate_product_authoritative_trace(
            replace(self.trace, events=tuple(events))
        )
        self.assertEqual(TraceValidationStatus.INVALID, result.status)
        self.assertEqual(
            ("trace_relation_assertion_target_value_mismatch",),
            result.reason_codes,
        )


if __name__ == "__main__":
    unittest.main()

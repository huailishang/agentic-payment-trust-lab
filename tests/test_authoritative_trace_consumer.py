from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment.authoritative_trace import (
    TraceValidationStatus,
    canonical_primitive,
)
from agentic_payment_experiment.authoritative_trace_consumer import (
    TraceConsumerStatus,
    consume_authoritative_trace,
    trace_read_model_json_bytes,
    trace_read_model_sha256,
    trace_read_model_to_primitive,
)
from agentic_payment_experiment.webshop_prepayment_trace_profiles import (
    PrepaymentScenarioKind,
)
from tests import test_attack_overlay_trace_toolkit as attack_tests
from tests import test_webshop_prepayment_trace_toolkit as prepayment_tests
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01


ROOT = Path(__file__).resolve().parents[1]
CONSUMER_PATH = ROOT / "src" / "agentic_payment_experiment" / "authoritative_trace_consumer.py"
EXPECTED_TRACE_HASHES = {
    "T01": "7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906",
    "T02": "fb1a79d73931f3e0bb87eafeffdaffe4004add137998d107ea425554605be624",
    "T10": "2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3",
}


def _snapshot_primitive(value: object) -> object:
    if is_dataclass(value):
        return {
            field.name: _snapshot_primitive(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Mapping):
        return {str(key): _snapshot_primitive(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_snapshot_primitive(item) for item in value]
    if isinstance(value, Enum):
        return _snapshot_primitive(value.value)
    if isinstance(value, Decimal):
        text = format(value, "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return "0" if text in {"", "-0"} else text
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or isinstance(value, (bool, int, str)):
        return value
    raise TypeError(type(value))


def _digest(value: object) -> str:
    primitive = _snapshot_primitive(value)
    raw = json.dumps(
        primitive,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class AuthoritativeTraceConsumerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        *_, t01_outcome = _valid_t01()
        assert t01_outcome.authoritative_trace is not None

        prepayment = prepayment_tests.WebShopPrepaymentTraceToolkitTest(methodName="runTest")
        prepayment.setUp()
        *_, t02_trace = prepayment.build_case(PrepaymentScenarioKind.PRICE_INCREASE)
        assert t02_trace is not None

        overlay = attack_tests.AttackOverlayTraceToolkitTest(methodName="runTest")
        overlay.setUp()
        t07_result = overlay.evaluate(
            "request.amount",
            attack_id="CONSUMER-REPRESENTATIVE-T07",
            title="consumer representative",
            source_ref="consumer-representative-source",
        )
        assert t07_result.authoritative_trace is not None

        _, _, t10_outcome, _ = _valid_t10()
        assert t10_outcome.authoritative_trace is not None

        cls.traces = {
            "T01": t01_outcome.authoritative_trace,
            "T02": t02_trace,
            "T07": t07_result.authoritative_trace,
            "T10": t10_outcome.authoritative_trace,
        }

    def _available(self, task_id: str):
        result = consume_authoritative_trace(self.traces[task_id])
        self.assertIs(TraceConsumerStatus.AVAILABLE, result.status)
        self.assertIs(TraceValidationStatus.VALID, result.validation_status)
        self.assertEqual(("product_authoritative_trace_valid",), result.reason_codes)
        self.assertIsNotNone(result.read_model)
        return result.read_model

    def _assert_rejected(self, trace: object):
        result = consume_authoritative_trace(trace)
        self.assertIs(TraceConsumerStatus.REJECTED, result.status)
        self.assertIsNone(result.read_model)
        self.assertIsNot(TraceValidationStatus.VALID, result.validation_status)
        self.assertTrue(result.reason_codes)
        return result

    def test_one_consumer_accepts_all_four_representative_families(self) -> None:
        for task_id in self.traces:
            with self.subTest(task_id=task_id):
                self._available(task_id)

    def test_top_level_read_model_metadata_is_exact(self) -> None:
        for task_id, trace in self.traces.items():
            with self.subTest(task_id=task_id):
                model = self._available(task_id)
                assert model is not None
                self.assertEqual(trace.trace_ref, model.trace_ref)
                self.assertEqual(trace.profile, model.profile)
                self.assertEqual(trace.schema_version, model.schema_version)
                self.assertEqual(trace.source, model.source)
                self.assertEqual(trace.completeness_status, model.completeness_status)
                self.assertEqual(trace.reason_codes, model.reason_codes)

    def test_event_count_order_and_fields_are_exact(self) -> None:
        for task_id, trace in self.traces.items():
            with self.subTest(task_id=task_id):
                model = self._available(task_id)
                assert model is not None
                self.assertEqual(len(trace.events), len(model.events))
                for source, projected in zip(trace.events, model.events):
                    self.assertEqual(source.sequence_no, projected.sequence_no)
                    self.assertEqual(source.event_type, projected.event_type)
                    self.assertEqual(source.entity_type, projected.entity_type)
                    self.assertEqual(source.entity_role, projected.entity_role)
                    self.assertEqual(source.entity_ref, projected.entity_ref)
                    self.assertEqual(source.source_binding_ref, projected.source_binding_ref)
                    self.assertEqual(source.decision, projected.decision)
                    self.assertEqual(source.status, projected.status)
                    self.assertEqual(source.reason_codes, projected.reason_codes)

    def test_relations_and_binding_assertions_are_exact(self) -> None:
        relation_count = 0
        assertion_count = 0
        for task_id, trace in self.traces.items():
            model = self._available(task_id)
            assert model is not None
            for source_event, projected_event in zip(trace.events, model.events):
                self.assertEqual(len(source_event.relations), len(projected_event.relations))
                for source_relation, projected_relation in zip(
                    source_event.relations, projected_event.relations
                ):
                    relation_count += 1
                    self.assertEqual(source_relation.relation_type, projected_relation.relation_type)
                    self.assertEqual(
                        source_relation.target_entity_type,
                        projected_relation.target_entity_type,
                    )
                    self.assertEqual(
                        source_relation.target_entity_role,
                        projected_relation.target_entity_role,
                    )
                    self.assertEqual(
                        source_relation.target_entity_ref,
                        projected_relation.target_entity_ref,
                    )
                    self.assertEqual(
                        source_relation.target_resolved,
                        projected_relation.target_resolved,
                    )
                    self.assertEqual(
                        len(source_relation.target_binding_assertions),
                        len(projected_relation.target_binding_assertions),
                    )
                    for source_assertion, projected_assertion in zip(
                        source_relation.target_binding_assertions,
                        projected_relation.target_binding_assertions,
                    ):
                        assertion_count += 1
                        self.assertEqual(source_assertion.source_path, projected_assertion.source_path)
                        self.assertEqual(source_assertion.target_path, projected_assertion.target_path)
                        self.assertEqual(source_assertion.source_value, projected_assertion.source_value)
                        self.assertEqual(source_assertion.target_value, projected_assertion.target_value)
                        self.assertEqual(source_assertion.equal, projected_assertion.equal)
        self.assertGreater(relation_count, 0)
        self.assertGreater(assertion_count, 0)

    def test_source_bindings_resolve_and_projection_is_exact(self) -> None:
        for task_id, trace in self.traces.items():
            with self.subTest(task_id=task_id):
                model = self._available(task_id)
                assert model is not None
                source_by_ref = {binding.binding_ref: binding for binding in trace.source_bindings}
                read_by_ref = {binding.binding_ref: binding for binding in model.source_bindings}
                self.assertEqual(set(source_by_ref), set(read_by_ref))
                for event in model.events:
                    self.assertIn(event.source_binding_ref, read_by_ref)
                for ref, source in source_by_ref.items():
                    projected = read_by_ref[ref]
                    self.assertEqual(source.source_object_type, projected.source_object_type)
                    self.assertEqual(source.source_object_ref, projected.source_object_ref)
                    self.assertEqual(source.projection_schema, projected.projection_schema)
                    self.assertEqual(source.projection, projected.projection)

    def test_same_trace_consumed_three_times_has_identical_canonical_sha(self) -> None:
        for task_id in self.traces:
            with self.subTest(task_id=task_id):
                digests = []
                for _ in range(3):
                    model = self._available(task_id)
                    assert model is not None
                    digests.append(trace_read_model_sha256(model))
                self.assertEqual(1, len(set(digests)))

    def test_primitive_serialization_is_closed_and_json_round_trips(self) -> None:
        for task_id in self.traces:
            with self.subTest(task_id=task_id):
                model = self._available(task_id)
                assert model is not None
                primitive = trace_read_model_to_primitive(model)
                self.assertEqual(
                    {
                        "trace_ref",
                        "profile",
                        "schema_version",
                        "source",
                        "completeness_status",
                        "reason_codes",
                        "events",
                        "source_bindings",
                    },
                    set(primitive),
                )
                self.assertEqual(
                    primitive,
                    json.loads(trace_read_model_json_bytes(model).decode("utf-8")),
                )
                self.assertEqual(primitive, canonical_primitive(primitive))

    def test_frozen_representative_source_trace_hashes_remain_unchanged(self) -> None:
        for task_id, expected in EXPECTED_TRACE_HASHES.items():
            with self.subTest(task_id=task_id):
                self.assertEqual(expected, _digest(self.traces[task_id]))

    def test_production_consumer_has_no_family_branch_or_business_reexecution(self) -> None:
        source = CONSUMER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        string_constants = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        for forbidden in ("T01", "T02", "T07", "T10"):
            self.assertNotIn(forbidden, string_constants)
        self.assertFalse(
            any(
                value.startswith("WEBSHOP_") or value.startswith("ATTACK_OVERLAY_")
                for value in string_constants
            )
        )
        imported_modules = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertFalse(
            any(
                token in module
                for module in imported_modules
                for token in (
                    "webshop",
                    "attack_overlay",
                    "payment_recovery",
                    "payment_finality",
                    "project_impact",
                    "evaluator",
                )
            )
        )
        called_names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        for forbidden_call in (
            "validate_request",
            "evaluate_context_policy",
            "resolve_fact_lineage",
            "evaluate_attack_overlay",
            "eval",
            "exec",
            "__import__",
        ):
            self.assertNotIn(forbidden_call, called_names)

    def test_wrong_input_type_fails_closed(self) -> None:
        self._assert_rejected({"profile": "plausible-but-not-a-trace"})

    def test_missing_required_source_binding_fails_closed(self) -> None:
        trace = self.traces["T02"]
        bad = replace(trace, source_bindings=trace.source_bindings[:-1])
        self._assert_rejected(bad)

    def test_duplicate_event_sequence_fails_closed(self) -> None:
        trace = self.traces["T02"]
        events = list(trace.events)
        events[1] = replace(events[1], sequence_no=1)
        self._assert_rejected(replace(trace, events=tuple(events)))

    def test_unresolved_relation_target_fails_closed(self) -> None:
        trace = self.traces["T02"]
        index = next(index for index, event in enumerate(trace.events) if event.relations)
        events = list(trace.events)
        relations = list(events[index].relations)
        relations[0] = replace(relations[0], target_entity_ref="MissingEntity:consumer-negative")
        events[index] = replace(events[index], relations=tuple(relations))
        self._assert_rejected(replace(trace, events=tuple(events)))

    def test_missing_event_binding_ref_fails_closed(self) -> None:
        trace = self.traces["T02"]
        events = list(trace.events)
        events[0] = replace(events[0], source_binding_ref="")
        self._assert_rejected(replace(trace, events=tuple(events)))

    def test_malformed_source_binding_projection_fails_closed(self) -> None:
        trace = self.traces["T02"]
        bindings = list(trace.source_bindings)
        bindings[0] = replace(bindings[0], projection={})
        self._assert_rejected(replace(trace, source_bindings=tuple(bindings)))

    def test_duplicate_binding_identity_fails_closed(self) -> None:
        trace = self.traces["T02"]
        bad = replace(trace, source_bindings=trace.source_bindings + (trace.source_bindings[0],))
        self._assert_rejected(bad)

    def test_incomplete_trace_fails_closed(self) -> None:
        trace = self.traces["T02"]
        result = self._assert_rejected(replace(trace, completeness_status="PARTIAL"))
        self.assertIs(TraceValidationStatus.INDETERMINATE, result.validation_status)

    def test_plausible_events_with_invalid_trace_envelope_fail_closed(self) -> None:
        trace = self.traces["T02"]
        bad = replace(trace, schema_version="product-authoritative-trace/v999")
        result = self._assert_rejected(bad)
        self.assertEqual(trace.events, bad.events)
        self.assertIs(TraceValidationStatus.INVALID, result.validation_status)

    def test_repeated_failed_consume_does_not_mutate_or_later_succeed(self) -> None:
        trace = self.traces["T02"]
        bad = replace(trace, completeness_status="PARTIAL")
        before = _digest(bad)
        statuses = [consume_authoritative_trace(bad).status for _ in range(3)]
        self.assertEqual([TraceConsumerStatus.REJECTED] * 3, statuses)
        self.assertEqual(before, _digest(bad))
        self.assertIs(TraceConsumerStatus.AVAILABLE, consume_authoritative_trace(trace).status)


if __name__ == "__main__":
    unittest.main()

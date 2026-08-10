from __future__ import annotations

import ast
import copy
from collections.abc import Mapping
from dataclasses import fields, is_dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import Enum
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment.adapters.webshop import (
    WebShopCommerceAdaptation,
    adapt_webshop_purchase_candidate,
)
from agentic_payment_experiment.authoritative_trace_consumer import (
    consume_authoritative_trace,
    trace_read_model_to_primitive,
)
from agentic_payment_experiment.webshop_journey_read_model import (
    EXPECTED_EXPERIMENT_CONTEXT_ORIGIN,
    WebShopJourneyReadModelError,
    build_webshop_journey_read_model,
    webshop_journey_read_model_json_bytes,
    webshop_journey_read_model_sha256,
    webshop_journey_read_model_to_primitive,
)
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "samples/external/webshop/pre_buy_now_candidate_v1.json"
MODULE_PATH = ROOT / "src" / "agentic_payment_experiment" / "webshop_journey_read_model.py"
EXPECTED_TOP_LEVEL = {
    "schema_version",
    "journey_ref",
    "source_classification_status",
    "correlations",
    "webshop_runtime",
    "experiment_context",
    "commerce_adaptation",
    "payment_authoritative_trace",
    "limitations",
}
EXPECTED_RUNTIME_FIELDS = {
    "session_id",
    "task_identifier",
    "instruction_text",
    "actions_executed",
    "buy_now_available",
    "buy_now_executed",
    "product",
    "source",
}


def load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _primitive(value):
    if is_dataclass(value):
        return {field.name: _primitive(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _primitive(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_primitive(item) for item in value]
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return _primitive(value.value)
    return value


def primitive_adaptation(adaptation: WebShopCommerceAdaptation) -> dict[str, object]:
    projected = {
        field.name: _primitive(getattr(adaptation, field.name))
        for field in fields(adaptation)
    }
    projected["ready"] = adaptation.ready
    return projected


class WebShopJourneyReadModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = load_fixture()
        cls.adaptation = adapt_webshop_purchase_candidate(cls.fixture)
        assert cls.adaptation.ready
        *_, outcome = _valid_t01()
        assert outcome.authoritative_trace is not None
        consumed = consume_authoritative_trace(outcome.authoritative_trace)
        assert consumed.read_model is not None
        cls.payment_read_model = consumed.read_model

    def build(self, fixture=None, adaptation=None, payment_read_model=None):
        return build_webshop_journey_read_model(
            self.fixture if fixture is None else fixture,
            self.adaptation if adaptation is None else adaptation,
            self.payment_read_model if payment_read_model is None else payment_read_model,
        )

    def test_four_evidence_namespaces_remain_separate(self) -> None:
        primitive = webshop_journey_read_model_to_primitive(self.build())
        self.assertEqual(EXPECTED_TOP_LEVEL, set(primitive))
        for namespace in (
            "webshop_runtime",
            "experiment_context",
            "commerce_adaptation",
            "payment_authoritative_trace",
        ):
            self.assertIsInstance(primitive[namespace], dict)
        self.assertEqual("VERIFIED_SEPARATE_SOURCES", primitive["source_classification_status"])

    def test_webshop_runtime_projection_is_exact_and_bounded(self) -> None:
        runtime = webshop_journey_read_model_to_primitive(self.build())["webshop_runtime"]
        self.assertEqual(EXPECTED_RUNTIME_FIELDS, set(runtime))
        for key in EXPECTED_RUNTIME_FIELDS:
            self.assertEqual(self.fixture[key], runtime[key])
        serialized = json.dumps(runtime, ensure_ascii=False).lower()
        for forbidden in ("reward", "observation", "search_results", "agent_reasoning", '"done"'):
            self.assertNotIn(forbidden, serialized)

    def test_experiment_context_is_exact_and_origin_not_promoted(self) -> None:
        context = webshop_journey_read_model_to_primitive(self.build())["experiment_context"]
        self.assertEqual(self.fixture["experiment_context"], context)
        self.assertEqual(EXPECTED_EXPERIMENT_CONTEXT_ORIGIN, context["origin"])
        self.assertNotIn(context["origin"], {"webshop_verified", "payment_verified", "user_confirmed"})

    def test_commerce_adaptation_projection_is_exact(self) -> None:
        actual = webshop_journey_read_model_to_primitive(self.build())["commerce_adaptation"]
        self.assertEqual(primitive_adaptation(self.adaptation), actual)
        self.assertTrue(actual["ready"])
        self.assertEqual([], actual["missing_fields"])
        self.assertEqual([], actual["unmapped_fields"])

    def test_payment_authoritative_trace_projection_is_exact(self) -> None:
        actual = webshop_journey_read_model_to_primitive(self.build())["payment_authoritative_trace"]
        expected = trace_read_model_to_primitive(self.payment_read_model)
        self.assertEqual(expected, actual)
        self.assertEqual(self.payment_read_model.trace_ref, actual["trace_ref"])

    def test_required_correlation_matrix_is_explicit_and_all_true(self) -> None:
        correlations = webshop_journey_read_model_to_primitive(self.build())["correlations"]
        by_id = {item["correlation_id"]: item for item in correlations}
        required = {
            "session_task_identifier",
            "instruction_to_user_intent",
            "product_asin_to_order_item",
            "product_name_to_order_item",
            "product_unit_amount_to_order_item",
            "product_quantity_to_order_item",
            "product_total_to_order",
            "experiment_origin_to_adaptation",
            "adaptation_order_request_binding",
            "order_id_to_payment_trace",
            "request_id_to_payment_trace",
            "trace_request_order_binding",
            "trace_ref_to_request_id",
        }
        self.assertTrue(required.issubset(by_id))
        self.assertTrue(all(item["equal"] is True for item in correlations))
        for item in correlations:
            self.assertTrue(item["source_path"])
            self.assertTrue(item["target_path"])

    def test_trace_order_and_request_correlations_resolve_from_bindings(self) -> None:
        correlations = {
            item["correlation_id"]: item
            for item in webshop_journey_read_model_to_primitive(self.build())["correlations"]
        }
        assert self.adaptation.order is not None
        assert self.adaptation.payment_request is not None
        self.assertEqual(
            self.adaptation.order.order_id,
            correlations["order_id_to_payment_trace"]["target_value"],
        )
        self.assertEqual(
            self.adaptation.payment_request.request_id,
            correlations["request_id_to_payment_trace"]["target_value"],
        )

    def test_output_is_deterministic_three_times(self) -> None:
        models = [self.build() for _ in range(3)]
        primitives = [webshop_journey_read_model_to_primitive(model) for model in models]
        json_bytes = [webshop_journey_read_model_json_bytes(model) for model in models]
        hashes = [webshop_journey_read_model_sha256(model) for model in models]
        self.assertEqual(1, len({json.dumps(value, sort_keys=True) for value in primitives}))
        self.assertEqual(1, len(set(json_bytes)))
        self.assertEqual(1, len(set(hashes)))

    def test_journey_ref_is_deterministic_metadata_not_fixed_task_literal(self) -> None:
        first = self.build()
        second = self.build()
        self.assertEqual(first.journey_ref, second.journey_ref)
        self.assertTrue(first.journey_ref.startswith("WebShopJourneyReadModel:sha256:"))
        self.assertNotIn("T01", first.journey_ref)

    def test_wrong_boundary_types_fail_closed(self) -> None:
        cases = (
            (None, self.adaptation, self.payment_read_model),
            (self.fixture, None, self.payment_read_model),
            (self.fixture, self.adaptation, None),
        )
        for fixture, adaptation, read_model in cases:
            with self.subTest(types=(type(fixture), type(adaptation), type(read_model))):
                with self.assertRaises(WebShopJourneyReadModelError):
                    build_webshop_journey_read_model(fixture, adaptation, read_model)

    def test_promoted_experiment_origin_fails_closed(self) -> None:
        fixture = copy.deepcopy(self.fixture)
        fixture["experiment_context"]["origin"] = "webshop_verified"
        with self.assertRaisesRegex(WebShopJourneyReadModelError, "cannot be promoted"):
            self.build(fixture=fixture)

    def test_instruction_mismatch_fails_closed(self) -> None:
        bad = replace(self.adaptation, user_intent_text="different instruction")
        with self.assertRaisesRegex(WebShopJourneyReadModelError, "instruction_to_user_intent"):
            self.build(adaptation=bad)

    def _adaptation_with_item(self, **changes):
        order = self.adaptation.order
        assert order is not None
        item = replace(order.items[0], **changes)
        return replace(self.adaptation, order=replace(order, items=(item,)))

    def test_product_asin_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(WebShopJourneyReadModelError, "product_asin_to_order_item"):
            self.build(adaptation=self._adaptation_with_item(item_id="B00MISMATCH"))

    def test_product_name_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(WebShopJourneyReadModelError, "product_name_to_order_item"):
            self.build(adaptation=self._adaptation_with_item(name="different product"))

    def test_product_amount_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(WebShopJourneyReadModelError, "product_unit_amount_to_order_item"):
            self.build(adaptation=self._adaptation_with_item(unit_amount=Decimal("1.00")))

    def test_product_quantity_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(WebShopJourneyReadModelError, "product_quantity_to_order_item"):
            self.build(adaptation=self._adaptation_with_item(quantity=2))

    def test_order_total_mismatch_fails_closed(self) -> None:
        order = self.adaptation.order
        assert order is not None
        bad = replace(self.adaptation, order=replace(order, total_amount=Decimal("1.00")))
        with self.assertRaisesRegex(WebShopJourneyReadModelError, "product_total_to_order"):
            self.build(adaptation=bad)

    def test_adaptation_origin_mismatch_fails_closed(self) -> None:
        bad = replace(self.adaptation, experiment_context_origin="other-origin")
        with self.assertRaisesRegex(WebShopJourneyReadModelError, "experiment_origin_to_adaptation"):
            self.build(adaptation=bad)

    def test_adaptation_order_request_binding_mismatch_fails_closed(self) -> None:
        request = self.adaptation.payment_request
        assert request is not None
        bad = replace(self.adaptation, payment_request=replace(request, order_ref="wrong-order"))
        with self.assertRaisesRegex(WebShopJourneyReadModelError, "adaptation_order_request_binding"):
            self.build(adaptation=bad)

    def test_adaptation_order_id_mismatch_to_trace_fails_closed(self) -> None:
        order = self.adaptation.order
        request = self.adaptation.payment_request
        assert order is not None and request is not None
        bad = replace(
            self.adaptation,
            order=replace(order, order_id="wrong-order"),
            payment_request=replace(request, order_ref="wrong-order"),
        )
        with self.assertRaisesRegex(WebShopJourneyReadModelError, "order_id_to_payment_trace"):
            self.build(adaptation=bad)

    def test_adaptation_request_id_mismatch_to_trace_fails_closed(self) -> None:
        request = self.adaptation.payment_request
        assert request is not None
        bad = replace(self.adaptation, payment_request=replace(request, request_id="wrong-request"))
        with self.assertRaisesRegex(WebShopJourneyReadModelError, "request_id_to_payment_trace"):
            self.build(adaptation=bad)

    def _mutate_trace_binding(self, source_object_type: str, **projection_changes):
        bindings = list(self.payment_read_model.source_bindings)
        matches = [
            i for i, binding in enumerate(bindings)
            if binding.source_object_type == source_object_type
        ]
        self.assertEqual(1, len(matches))
        index = matches[0]
        projection = dict(bindings[index].projection)
        projection.update(projection_changes)
        bindings[index] = replace(bindings[index], projection=projection)
        return replace(self.payment_read_model, source_bindings=tuple(bindings))

    def test_trace_order_projection_mismatch_fails_closed(self) -> None:
        bad = self._mutate_trace_binding("Order", order_id="wrong-order")
        with self.assertRaisesRegex(WebShopJourneyReadModelError, "order_id_to_payment_trace"):
            self.build(payment_read_model=bad)

    def test_trace_request_projection_mismatch_fails_closed(self) -> None:
        bad = self._mutate_trace_binding("TransactionRequest", request_id="wrong-request")
        with self.assertRaisesRegex(WebShopJourneyReadModelError, "request_id_to_payment_trace"):
            self.build(payment_read_model=bad)

    def test_trace_request_order_binding_mismatch_fails_closed(self) -> None:
        bad = self._mutate_trace_binding("TransactionRequest", order_ref="wrong-order")
        with self.assertRaisesRegex(WebShopJourneyReadModelError, "trace_request_order_binding"):
            self.build(payment_read_model=bad)

    def test_trace_ref_request_binding_mismatch_fails_closed(self) -> None:
        bad = replace(self.payment_read_model, trace_ref="ProductAuthoritativeTrace:any:wrong-request")
        with self.assertRaisesRegex(WebShopJourneyReadModelError, "trace_ref_to_request_id"):
            self.build(payment_read_model=bad)

    def test_production_path_is_generic_and_has_no_execution_or_ui_imports(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        modules = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertEqual(
            {
                "__future__",
                "dataclasses",
                "datetime",
                "decimal",
                "enum",
                "hashlib",
                "json",
                "typing",
                "adapters.webshop",
                "authoritative_trace_consumer",
            },
            modules,
        )
        constants = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        for forbidden in (
            "T01",
            "WEBSHOP_NORMAL_PURCHASE_V2",
            "webshop-order-9eccab2b0154fca4af27f322",
            "webshop-request-6c6a78eddffdb552c2af66ef",
        ):
            self.assertNotIn(forbidden, constants)
        for forbidden in (
            "authoritative_trace_player",
            "webshop_payment_sidecar",
            "policy",
            "lineage",
            "runner",
            "evaluator",
            "requests",
            "urllib",
            "socket",
            "playwright",
            "selenium",
        ):
            self.assertNotIn(f"import {forbidden}", source)
            self.assertNotIn(f"from .{forbidden}", source)
        self.assertNotIn("adapt_webshop_purchase_candidate(", source)

    def test_limitations_preserve_fixed_script_and_source_boundary(self) -> None:
        limitations = set(self.build().limitations)
        self.assertIn("fixed_script_webshop_smoke_not_autonomous_agent", limitations)
        self.assertIn("experiment_context_not_webshop_verified", limitations)
        self.assertIn("payment_authoritative_trace_is_separate_evidence_namespace", limitations)
        self.assertIn("no_webshop_or_payment_execution", limitations)


if __name__ == "__main__":
    unittest.main()

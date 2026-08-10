from __future__ import annotations

import ast
import copy
from dataclasses import replace
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment.adapters.webshop import adapt_webshop_purchase_candidate
from agentic_payment_experiment.authoritative_trace_consumer import consume_authoritative_trace
from agentic_payment_experiment.webshop_journey_player import (
    WebShopJourneyPlayerInputError,
    build_webshop_journey_player_payload,
    render_webshop_journey_player,
    webshop_journey_player_html_sha256,
    webshop_journey_player_payload_json,
    webshop_journey_player_payload_sha256,
)
from agentic_payment_experiment.webshop_journey_read_model import (
    build_webshop_journey_read_model,
    webshop_journey_read_model_to_primitive,
)
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "samples/external/webshop/pre_buy_now_candidate_v1.json"
PLAYER_PATH = ROOT / "src" / "agentic_payment_experiment" / "webshop_journey_player.py"
PAYLOAD_RE = re.compile(
    r'<script id="journey-payload" type="application/json">(.*?)</script>',
    re.DOTALL,
)


def build_representative_journey():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    adaptation = adapt_webshop_purchase_candidate(fixture)
    assert adaptation.ready
    *_, outcome = _valid_t01()
    assert outcome.authoritative_trace is not None
    consumed = consume_authoritative_trace(outcome.authoritative_trace)
    assert consumed.read_model is not None
    return build_webshop_journey_read_model(fixture, adaptation, consumed.read_model)


def embedded_payload(html: str) -> dict[str, object]:
    match = PAYLOAD_RE.search(html)
    assert match is not None
    return json.loads(match.group(1))


class WebShopJourneyPlayerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.journey = build_representative_journey()
        cls.primitive = webshop_journey_read_model_to_primitive(cls.journey)

    def test_player_requires_webshop_journey_read_model(self) -> None:
        for value in (None, {}, self.primitive):
            with self.subTest(type=type(value).__name__):
                with self.assertRaises(WebShopJourneyPlayerInputError):
                    build_webshop_journey_player_payload(value)

    def test_embedded_payload_equals_journey_primitive_exactly(self) -> None:
        html = render_webshop_journey_player(self.journey)
        self.assertEqual(self.primitive, embedded_payload(html))
        self.assertEqual(self.primitive, build_webshop_journey_player_payload(self.journey))

    def test_all_four_source_namespaces_and_two_audit_sections_are_visible(self) -> None:
        html = render_webshop_journey_player(self.journey)
        labels = (
            "1. 用户需求与商城动作 / webshop_runtime",
            "2. 实验补充上下文 / experiment_context",
            "3. Commerce 派生对象 / commerce_adaptation",
            "4. 支付权威证据 / payment_authoritative_trace",
            "5. 跨源关联 / correlations",
            "6. 限制与事实边界 / limitations",
        )
        for label in labels:
            self.assertIn(label, html)

    def test_source_semantics_notice_is_explicit(self) -> None:
        html = render_webshop_journey_player(self.journey)
        self.assertIn("实验补充字段不是 WebShop 核验事实", html)
        self.assertIn("支付权威轨迹是独立证据源", html)
        payload = embedded_payload(html)
        self.assertEqual(
            "explicit_experiment_context_not_webshop_verified",
            payload["experiment_context"]["origin"],
        )

    def test_fixed_script_boundary_is_explicit_and_autonomous_claim_absent(self) -> None:
        html = render_webshop_journey_player(self.journey)
        self.assertIn("固定脚本轨迹，不代表自主 Agent", html)
        self.assertNotIn("autonomous Agent completed purchase", html)
        self.assertNotIn("自主 Agent 已完成购买", html)
        payload = embedded_payload(html)
        self.assertIn(
            "fixed_script_webshop_smoke_not_autonomous_agent",
            payload["limitations"],
        )

    def test_instruction_and_selected_product_mismatch_are_preserved_without_match_claim(self) -> None:
        payload = embedded_payload(render_webshop_journey_player(self.journey))
        instruction = payload["webshop_runtime"]["instruction_text"]
        product = payload["webshop_runtime"]["product"]
        self.assertIn("cargo pants", instruction)
        self.assertIn("orange", instruction)
        self.assertIn("30.00", instruction)
        self.assertIn("Vhomes Lights", product["title"])
        self.assertEqual("877.80", product["order_total"])
        html = render_webshop_journey_player(self.journey)
        self.assertIn("不判断二者是否匹配", html)
        self.assertNotIn("商品符合用户需求", html)

    def test_commerce_order_request_and_payment_drill_down_remain_in_payload(self) -> None:
        payload = embedded_payload(render_webshop_journey_player(self.journey))
        order = payload["commerce_adaptation"]["order"]
        request = payload["commerce_adaptation"]["payment_request"]
        payment = payload["payment_authoritative_trace"]
        self.assertTrue(order["order_id"])
        self.assertTrue(request["request_id"])
        self.assertGreater(len(payment["events"]), 0)
        self.assertGreater(len(payment["source_bindings"]), 0)
        self.assertEqual(order["order_id"], request["order_ref"])

    def test_correlations_preserve_paths_values_and_equality(self) -> None:
        payload = embedded_payload(render_webshop_journey_player(self.journey))
        self.assertGreaterEqual(len(payload["correlations"]), 10)
        for item in payload["correlations"]:
            self.assertTrue(item["correlation_id"])
            self.assertTrue(item["source_path"])
            self.assertTrue(item["target_path"])
            self.assertIs(item["equal"], True)
            self.assertIn("source_value", item)
            self.assertIn("target_value", item)

    def test_payment_playback_controls_and_source_navigation_are_local_only(self) -> None:
        html = render_webshop_journey_player(self.journey)
        for text in ("上一步", "下一步", "回到起点", "自动播放", "事实源导航"):
            self.assertIn(text, html)
        self.assertIn("paymentIndex", html)
        self.assertIn("paymentTimer", html)
        for forbidden in (
            "fetch(",
            "XMLHttpRequest",
            "WebSocket",
            "EventSource",
            "sendBeacon",
            "navigator.sendBeacon",
        ):
            self.assertNotIn(forbidden, html)

    def test_same_journey_rendered_three_times_is_deterministic(self) -> None:
        html_hashes = [webshop_journey_player_html_sha256(self.journey) for _ in range(3)]
        payload_hashes = [webshop_journey_player_payload_sha256(self.journey) for _ in range(3)]
        payload_json = [webshop_journey_player_payload_json(self.journey) for _ in range(3)]
        self.assertEqual(1, len(set(html_hashes)))
        self.assertEqual(1, len(set(payload_hashes)))
        self.assertEqual(1, len(set(payload_json)))

    def test_promoted_experiment_origin_fails_closed(self) -> None:
        experiment = dict(self.journey.experiment_context)
        experiment["origin"] = "webshop_verified"
        bad = replace(self.journey, experiment_context=experiment)
        with self.assertRaisesRegex(WebShopJourneyPlayerInputError, "origin"):
            render_webshop_journey_player(bad)

    def test_missing_fixed_script_limitation_fails_closed(self) -> None:
        limitations = tuple(
            item
            for item in self.journey.limitations
            if item != "fixed_script_webshop_smoke_not_autonomous_agent"
        )
        with self.assertRaisesRegex(WebShopJourneyPlayerInputError, "fixed-script"):
            render_webshop_journey_player(replace(self.journey, limitations=limitations))

    def test_missing_source_semantic_limitation_fails_closed(self) -> None:
        limitations = tuple(
            item
            for item in self.journey.limitations
            if item != "experiment_context_not_webshop_verified"
        )
        with self.assertRaisesRegex(WebShopJourneyPlayerInputError, "source-boundary"):
            render_webshop_journey_player(replace(self.journey, limitations=limitations))

    def test_false_correlation_fails_closed(self) -> None:
        correlations = list(self.journey.correlations)
        correlations[0] = replace(correlations[0], equal=False)
        bad = replace(self.journey, correlations=tuple(correlations))
        with self.assertRaisesRegex(WebShopJourneyPlayerInputError, "verified equal"):
            render_webshop_journey_player(bad)

    def test_empty_correlations_fail_closed(self) -> None:
        with self.assertRaisesRegex(WebShopJourneyPlayerInputError, "correlations"):
            render_webshop_journey_player(replace(self.journey, correlations=()))

    def test_missing_runtime_field_fails_closed(self) -> None:
        runtime = dict(self.journey.webshop_runtime)
        del runtime["product"]
        with self.assertRaisesRegex(WebShopJourneyPlayerInputError, "unexpected shape"):
            render_webshop_journey_player(replace(self.journey, webshop_runtime=runtime))

    def test_commerce_not_ready_fails_closed(self) -> None:
        commerce = dict(self.journey.commerce_adaptation)
        commerce["ready"] = False
        with self.assertRaisesRegex(WebShopJourneyPlayerInputError, "ready"):
            render_webshop_journey_player(replace(self.journey, commerce_adaptation=commerce))

    def test_empty_payment_events_fail_closed(self) -> None:
        payment = copy.deepcopy(dict(self.journey.payment_authoritative_trace))
        payment["events"] = []
        bad = replace(self.journey, payment_authoritative_trace=payment)
        with self.assertRaisesRegex(WebShopJourneyPlayerInputError, "events"):
            render_webshop_journey_player(bad)

    def test_unresolved_payment_binding_fails_closed(self) -> None:
        payment = copy.deepcopy(dict(self.journey.payment_authoritative_trace))
        payment["events"][0]["source_binding_ref"] = "missing-binding"
        bad = replace(self.journey, payment_authoritative_trace=payment)
        with self.assertRaisesRegex(WebShopJourneyPlayerInputError, "unresolved"):
            render_webshop_journey_player(bad)

    def test_duplicate_payment_binding_fails_closed(self) -> None:
        payment = copy.deepcopy(dict(self.journey.payment_authoritative_trace))
        payment["source_bindings"].append(copy.deepcopy(payment["source_bindings"][0]))
        bad = replace(self.journey, payment_authoritative_trace=payment)
        with self.assertRaisesRegex(WebShopJourneyPlayerInputError, "unique"):
            render_webshop_journey_player(bad)

    def test_hostile_display_string_round_trips_without_script_escape(self) -> None:
        hostile = '</script><script>alert("hostile")</script><b>危险 & evidence</b>'
        runtime = dict(self.journey.webshop_runtime)
        runtime["instruction_text"] = hostile
        commerce = dict(self.journey.commerce_adaptation)
        commerce["user_intent_text"] = hostile
        correlations = list(self.journey.correlations)
        for index, item in enumerate(correlations):
            if item.correlation_id == "instruction_to_user_intent":
                correlations[index] = replace(
                    item,
                    source_value=hostile,
                    target_value=hostile,
                    equal=True,
                )
        hostile_journey = replace(
            self.journey,
            webshop_runtime=runtime,
            commerce_adaptation=commerce,
            correlations=tuple(correlations),
        )
        html = render_webshop_journey_player(hostile_journey)
        match = PAYLOAD_RE.search(html)
        self.assertIsNotNone(match)
        assert match is not None
        payload_text = match.group(1)
        payload = json.loads(payload_text)
        self.assertEqual(hostile, payload["webshop_runtime"]["instruction_text"])
        self.assertNotIn(hostile, html)
        self.assertIn("\\u003c/script\\u003e", payload_text)
        self.assertIn("\\u0026", payload_text)

    def test_safe_dom_rendering_avoids_html_injection_primitives(self) -> None:
        source = PLAYER_PATH.read_text(encoding="utf-8")
        self.assertIn(".textContent", source)
        self.assertIn("document.createElement", source)
        for forbidden in ("innerHTML", "insertAdjacentHTML", "document.write"):
            self.assertNotIn(forbidden, source)

    def test_production_imports_only_stdlib_and_journey_read_model(self) -> None:
        source = PLAYER_PATH.read_text(encoding="utf-8")
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
                "hashlib",
                "json",
                "typing",
                "webshop_journey_read_model",
            },
            modules,
        )

    def test_production_has_no_task_profile_fixed_id_or_execution_branch(self) -> None:
        source = PLAYER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
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
            "adapters.webshop",
            "authoritative_trace_consumer",
            "authoritative_trace_player",
            "webshop_payment_sidecar",
            "validate_request",
            "adapt_webshop_purchase_candidate(",
            "consume_authoritative_trace(",
            "requests",
            "urllib",
            "socket",
            "playwright",
            "selenium",
        ):
            self.assertNotIn(forbidden, source)

    def test_html_is_self_contained_without_external_assets(self) -> None:
        html = render_webshop_journey_player(self.journey)
        self.assertNotIn("https://", html)
        self.assertNotIn("http://", html)
        self.assertNotIn("<link ", html)
        self.assertNotIn("<script src=", html)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import ast
from dataclasses import replace
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment.authoritative_trace_consumer import (
    TraceConsumerStatus,
    consume_authoritative_trace,
    trace_read_model_to_primitive,
)
from agentic_payment_experiment.authoritative_trace_player import (
    TracePlayerInputError,
    build_trace_player_payload,
    render_authoritative_trace_player,
    trace_player_html_sha256,
    trace_player_payload_json,
    trace_player_payload_sha256,
)
from agentic_payment_experiment.webshop_prepayment_trace_profiles import (
    PrepaymentScenarioKind,
)
from tests import test_attack_overlay_trace_toolkit as attack_tests
from tests import test_webshop_prepayment_trace_toolkit as prepayment_tests
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01


ROOT = Path(__file__).resolve().parents[1]
PLAYER_PATH = ROOT / "src" / "agentic_payment_experiment" / "authoritative_trace_player.py"
PAYLOAD_RE = re.compile(
    r'<script id="trace-payload" type="application/json">(.*?)</script>',
    re.DOTALL,
)


def _extract_payload_text(html: str) -> str:
    match = PAYLOAD_RE.search(html)
    if match is None:
        raise AssertionError("trace payload script not found")
    return match.group(1)


def _extract_payload(html: str) -> dict[str, object]:
    return json.loads(_extract_payload_text(html))


class AuthoritativeTracePlayerTest(unittest.TestCase):
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
            attack_id="PLAYER-REPRESENTATIVE-ATTACK",
            title="player representative",
            source_ref="player-representative-source",
        )
        assert t07_result.authoritative_trace is not None

        _, _, t10_outcome, _ = _valid_t10()
        assert t10_outcome.authoritative_trace is not None

        traces = {
            "T01": t01_outcome.authoritative_trace,
            "T02": t02_trace,
            "T07": t07_result.authoritative_trace,
            "T10": t10_outcome.authoritative_trace,
        }
        cls.read_models = {}
        for task_id, trace in traces.items():
            consumed = consume_authoritative_trace(trace)
            assert consumed.status is TraceConsumerStatus.AVAILABLE
            assert consumed.read_model is not None
            cls.read_models[task_id] = consumed.read_model

    def test_same_player_renders_all_four_representative_families(self) -> None:
        rendered = 0
        for task_id, model in self.read_models.items():
            with self.subTest(task_id=task_id):
                html = render_authoritative_trace_player(model)
                self.assertTrue(html.startswith("<!doctype html>"))
                self.assertIn("权威轨迹只读播放器", html)
                self.assertEqual(trace_read_model_to_primitive(model), _extract_payload(html))
                rendered += 1
        self.assertEqual(4, rendered)

    def test_embedded_payload_is_exact_read_model_primitive(self) -> None:
        for task_id, model in self.read_models.items():
            with self.subTest(task_id=task_id):
                self.assertEqual(
                    trace_read_model_to_primitive(model),
                    _extract_payload(render_authoritative_trace_player(model)),
                )

    def test_build_payload_does_not_enrich_read_model(self) -> None:
        for task_id, model in self.read_models.items():
            with self.subTest(task_id=task_id):
                self.assertEqual(trace_read_model_to_primitive(model), build_trace_player_payload(model))

    def test_event_count_order_and_fields_are_preserved(self) -> None:
        for task_id, model in self.read_models.items():
            source = trace_read_model_to_primitive(model)
            payload = _extract_payload(render_authoritative_trace_player(model))
            with self.subTest(task_id=task_id):
                self.assertEqual(source["events"], payload["events"])
                self.assertEqual(
                    [event["sequence_no"] for event in source["events"]],
                    [event["sequence_no"] for event in payload["events"]],
                )

    def test_relations_and_assertions_are_preserved(self) -> None:
        observed_relations = 0
        for model in self.read_models.values():
            source = trace_read_model_to_primitive(model)
            payload = _extract_payload(render_authoritative_trace_player(model))
            for source_event, payload_event in zip(source["events"], payload["events"]):
                self.assertEqual(source_event["relations"], payload_event["relations"])
                observed_relations += len(source_event["relations"])
        self.assertGreater(observed_relations, 0)

    def test_every_event_source_binding_ref_resolves_exactly_once(self) -> None:
        for task_id, model in self.read_models.items():
            payload = _extract_payload(render_authoritative_trace_player(model))
            refs = [binding["binding_ref"] for binding in payload["source_bindings"]]
            with self.subTest(task_id=task_id):
                self.assertEqual(len(refs), len(set(refs)))
                for event in payload["events"]:
                    self.assertEqual(1, refs.count(event["source_binding_ref"]))

    def test_source_binding_drill_down_payload_is_exact(self) -> None:
        for task_id, model in self.read_models.items():
            source = trace_read_model_to_primitive(model)
            payload = _extract_payload(render_authoritative_trace_player(model))
            with self.subTest(task_id=task_id):
                self.assertEqual(source["source_bindings"], payload["source_bindings"])
                for binding in payload["source_bindings"]:
                    self.assertEqual(
                        {
                            "binding_ref",
                            "source_object_type",
                            "source_object_ref",
                            "projection_schema",
                            "projection",
                        },
                        set(binding),
                    )

    def test_chinese_first_controls_and_evidence_labels_are_present(self) -> None:
        html = render_authoritative_trace_player(self.read_models["T01"])
        for label in (
            "上一步",
            "下一步",
            "回到起点",
            "自动播放",
            "轨迹元数据",
            "当前事件",
            "关系证据",
            "来源绑定证据",
            "轨迹引用（trace_ref）",
            "来源绑定（source_binding_ref）",
            "冻结投影（projection）",
        ):
            self.assertIn(label, html)

    def test_player_has_explicit_offline_read_only_notice(self) -> None:
        html = render_authoritative_trace_player(self.read_models["T01"])
        self.assertIn("离线只读", html)
        self.assertIn("不会执行 WebShop、Buy Now、支付、订单或履约动作", html)

    def test_playback_uses_only_local_index_and_timer_state(self) -> None:
        html = render_authoritative_trace_player(self.read_models["T01"])
        self.assertIn("let playbackIndex = 0", html)
        self.assertIn("let playbackTimer = null", html)
        self.assertIn("setInterval", html)
        self.assertIn("clearInterval", html)
        self.assertNotIn("payload.events.push", html)
        self.assertNotIn("payload.source_bindings.push", html)

    def test_generated_document_has_no_network_or_external_resource_hooks(self) -> None:
        html = render_authoritative_trace_player(self.read_models["T01"])
        for forbidden in (
            "fetch(",
            "XMLHttpRequest",
            "WebSocket",
            "EventSource",
            "sendBeacon",
            "src=\"http",
            "href=\"http",
            "https://",
            "http://",
        ):
            self.assertNotIn(forbidden, html)

    def test_frontend_uses_text_content_not_inner_html_for_evidence(self) -> None:
        html = render_authoritative_trace_player(self.read_models["T01"])
        self.assertIn(".textContent", html)
        self.assertIn("document.createElement", html)
        self.assertNotIn("innerHTML", html)
        self.assertNotIn("insertAdjacentHTML", html)
        self.assertNotIn("document.write", html)

    def test_rendering_is_byte_deterministic_three_times_per_family(self) -> None:
        for task_id, model in self.read_models.items():
            with self.subTest(task_id=task_id):
                hashes = [trace_player_html_sha256(model) for _ in range(3)]
                self.assertEqual(1, len(set(hashes)))

    def test_embedded_payload_is_deterministic_three_times_per_family(self) -> None:
        for task_id, model in self.read_models.items():
            with self.subTest(task_id=task_id):
                hashes = [trace_player_payload_sha256(model) for _ in range(3)]
                payload_text = [trace_player_payload_json(model) for _ in range(3)]
                self.assertEqual(1, len(set(hashes)))
                self.assertEqual(1, len(set(payload_text)))

    def test_wrong_input_type_fails_closed(self) -> None:
        for bad in (None, {}, [], "read model", object()):
            with self.subTest(type=type(bad).__name__):
                with self.assertRaises(TracePlayerInputError):
                    render_authoritative_trace_player(bad)

    def test_empty_event_read_model_fails_closed(self) -> None:
        bad = replace(self.read_models["T01"], events=())
        with self.assertRaisesRegex(TracePlayerInputError, "events must be a non-empty list"):
            render_authoritative_trace_player(bad)

    def test_unresolved_source_binding_ref_fails_closed(self) -> None:
        model = self.read_models["T01"]
        events = list(model.events)
        events[0] = replace(events[0], source_binding_ref="missing-binding")
        bad = replace(model, events=tuple(events))
        with self.assertRaisesRegex(TracePlayerInputError, "source_binding_ref is unresolved"):
            render_authoritative_trace_player(bad)

    def test_duplicate_source_binding_ref_fails_closed(self) -> None:
        model = self.read_models["T01"]
        bindings = list(model.source_bindings)
        bindings[1] = replace(bindings[1], binding_ref=bindings[0].binding_ref)
        bad = replace(model, source_bindings=tuple(bindings))
        with self.assertRaisesRegex(TracePlayerInputError, "source binding refs must be unique"):
            render_authoritative_trace_player(bad)

    def test_hostile_display_string_round_trips_without_breaking_script_boundary(self) -> None:
        hostile = '</script><script>alert("player-hostile")</script><b>危险 & evidence</b>'
        model = self.read_models["T01"]
        events = list(model.events)
        events[0] = replace(events[0], entity_ref=hostile)
        hostile_model = replace(model, events=tuple(events))
        html = render_authoritative_trace_player(hostile_model)
        payload_text = _extract_payload_text(html)
        payload = json.loads(payload_text)

        self.assertEqual(hostile, payload["events"][0]["entity_ref"])
        self.assertNotIn(hostile, html)
        self.assertNotIn('</script><script>alert("player-hostile")', html)
        self.assertIn("\\u003c/script\\u003e", payload_text)
        self.assertIn("\\u0026", payload_text)
        self.assertEqual(trace_read_model_to_primitive(hostile_model), payload)
        self.assertNotIn("innerHTML", html)

    def test_production_player_has_generic_consumer_only_dependency(self) -> None:
        source = PLAYER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
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
        self.assertEqual(
            {"__future__", "hashlib", "json", "typing", "authoritative_trace_consumer"},
            imported_modules,
        )
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

    def test_production_player_has_no_business_or_network_calls(self) -> None:
        source = PLAYER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        for forbidden in (
            "consume_authoritative_trace",
            "validate_product_authoritative_trace",
            "validate_request",
            "evaluate_context_policy",
            "resolve_fact_lineage",
            "evaluate_attack_overlay",
            "run_scenarios",
            "urlopen",
            "request",
            "eval",
            "exec",
            "__import__",
        ):
            self.assertNotIn(forbidden, called)
        source_lower = source.lower()
        for forbidden_module in (
            "webshop_",
            "attack_overlay",
            "payment_",
            "runner",
            "evaluator",
            "urllib",
            "requests",
            "socket",
        ):
            self.assertNotIn(f"from .{forbidden_module}", source_lower)
            self.assertNotIn(f"import {forbidden_module}", source_lower)


if __name__ == "__main__":
    unittest.main()

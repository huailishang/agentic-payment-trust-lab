from __future__ import annotations

import ast
import copy
from dataclasses import replace
import hashlib
import json
import re
import sys
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
for entry in (ROOT, ROOT / "src"):
    sys.path.insert(0, str(entry))

from agentic_payment_experiment.adapters.webshop import adapt_webshop_purchase_candidate
from agentic_payment_experiment.authoritative_trace_consumer import consume_authoritative_trace
from agentic_payment_experiment.webshop_journey_player import render_webshop_journey_player
from agentic_payment_experiment.webshop_journey_read_model import build_webshop_journey_read_model
from agentic_payment_experiment.webshop_prepayment_trace_profiles import PrepaymentScenarioKind
from tests import test_webshop_prepayment_trace_toolkit as prepayment_tests
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01, _valid_t12
from tests.test_webshop_unknown_payment_authoritative_trace import _valid_t09

EVID = Path(__file__).resolve().parent
START_MANIFEST = EVID / "TASK-START-src-manifest.json"
PLAYER_REL = "src/agentic_payment_experiment/webshop_journey_player.py"
PLAYER_PATH = ROOT / PLAYER_REL
TEST_PATH = ROOT / "tests/test_webshop_journey_player.py"
FIXTURE_PATH = ROOT / "samples/external/webshop/pre_buy_now_candidate_v1.json"
PAYLOAD_RE = re.compile(
    r'<script id="journey-payload" type="application/json">(.*?)</script>',
    re.DOTALL,
)
FROZEN = {
    "src/agentic_payment_experiment/webshop_journey_read_model.py": "70d6c19fe7d48d27fc377f943ba53b0db276391f3f48402b66f0a57490d1ba7d",
    "tests/test_webshop_journey_read_model.py": "9767c6bb0877d081812bd43d43b2d939f6353bf0d59b56988a02b37a9ccd5263",
    "src/agentic_payment_experiment/authoritative_trace_player.py": "9cd38620ee966632191b376f13d95446711ff55d08b18aa844f9a7fb6ef74541",
    "src/agentic_payment_experiment/authoritative_trace_consumer.py": "6ad65118a4ab50e648e4f6098f6c2c5009ce5731232ae0a4e11d2f60c0c431b5",
    "samples/external/webshop/pre_buy_now_candidate_v1.json": "6e9d67c3b787cc2d9202bd22b30dec88bf9f920dfa3741bdeb364108a2a3c8e5",
    "samples/evaluation/project_impact_baseline_v1.json": "e7a1d338ece0c65c6417ce58384e8dc9eb2dc29b2e37ad461cf92b9deb9b89c0",
    "scripts/validation/run_project_impact_baseline.py": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
}
EXPECTED_TRACE_HASHES = {
    "T01": "7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906",
    "T02": "fb1a79d73931f3e0bb87eafeffdaffe4004add137998d107ea425554605be624",
    "T03": "7f0e1ccb14cc9256c5c336fb460647ce040bf0549a3328764c061c7b766c92a7",
    "T04": "405e6b8971f9f5e3ad67069ace074df15af4fee6f80418a70466315dcd642c33",
    "T09": "a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e",
    "T10": "2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3",
    "T12": "ebb38113abb2582d52f434b1a1b30247cc68ee8f4b57c0c18f52efa37bb1c230",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def primitive(value: object) -> object:
    if is_dataclass(value):
        return {field.name: primitive(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): primitive(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [primitive(item) for item in value]
    if isinstance(value, Enum):
        return primitive(value.value)
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


def digest(value: object) -> str:
    raw = json.dumps(
        primitive(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def accepted_trace_hashes() -> dict[str, str]:
    *_, t01_outcome = _valid_t01()
    assert t01_outcome.authoritative_trace is not None
    prepayment = prepayment_tests.WebShopPrepaymentTraceToolkitTest(methodName="runTest")
    prepayment.setUp()
    traces = {}
    for task_id, kind in (
        ("T02", PrepaymentScenarioKind.PRICE_INCREASE),
        ("T03", PrepaymentScenarioKind.PRICE_DECREASE),
        ("T04", PrepaymentScenarioKind.PAYEE_CHANGE),
    ):
        *_, trace = prepayment.build_case(kind)
        assert trace is not None
        traces[task_id] = trace
    *_, t09_outcome = _valid_t09()
    assert t09_outcome.authoritative_trace is not None
    _, _, t10_outcome, _ = _valid_t10()
    assert t10_outcome.authoritative_trace is not None
    *_, t12_outcome = _valid_t12()
    assert t12_outcome.authoritative_trace is not None
    traces.update(
        {
            "T01": t01_outcome.authoritative_trace,
            "T09": t09_outcome.authoritative_trace,
            "T10": t10_outcome.authoritative_trace,
            "T12": t12_outcome.authoritative_trace,
        }
    )
    return {task_id: digest(trace) for task_id, trace in sorted(traces.items())}


def static_audit() -> dict[str, object]:
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
    expected = {"__future__", "hashlib", "json", "typing", "webshop_journey_read_model"}
    assert modules == expected, (expected, modules)
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    for literal in (
        "T01",
        "WEBSHOP_NORMAL_PURCHASE_V2",
        "webshop-order-9eccab2b0154fca4af27f322",
        "webshop-request-6c6a78eddffdb552c2af66ef",
    ):
        assert literal not in strings
    forbidden = (
        "adapters.webshop",
        "authoritative_trace_consumer",
        "authoritative_trace_player",
        "webshop_payment_sidecar",
        "adapt_webshop_purchase_candidate(",
        "consume_authoritative_trace(",
        "validate_request",
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "EventSource",
        "sendBeacon",
        "innerHTML",
        "insertAdjacentHTML",
        "document.write",
        "https://",
        "http://",
    )
    assert all(token not in source for token in forbidden), [token for token in forbidden if token in source]
    assert ".textContent" in source
    assert "document.createElement" in source
    return {
        "imports": sorted(modules),
        "fixed_task_profile_ids": False,
        "direct_adapter_consumer_trace_player_imports": False,
        "business_execution_calls": False,
        "network_browser_calls": False,
        "unsafe_html_insertion": False,
        "safe_text_content": True,
    }


def hostile_string_audit() -> dict[str, object]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    adaptation = adapt_webshop_purchase_candidate(fixture)
    assert adaptation.ready
    *_, outcome = _valid_t01()
    assert outcome.authoritative_trace is not None
    consumed = consume_authoritative_trace(outcome.authoritative_trace)
    assert consumed.read_model is not None
    journey = build_webshop_journey_read_model(fixture, adaptation, consumed.read_model)
    hostile = '</script><script>alert("hostile")</script><b>危险 & evidence</b>'
    runtime = dict(journey.webshop_runtime)
    runtime["instruction_text"] = hostile
    commerce = dict(journey.commerce_adaptation)
    commerce["user_intent_text"] = hostile
    correlations = list(journey.correlations)
    for index, item in enumerate(correlations):
        if item.correlation_id == "instruction_to_user_intent":
            correlations[index] = replace(item, source_value=hostile, target_value=hostile, equal=True)
    bad_for_display = replace(
        journey,
        webshop_runtime=runtime,
        commerce_adaptation=commerce,
        correlations=tuple(correlations),
    )
    html = render_webshop_journey_player(bad_for_display)
    match = PAYLOAD_RE.search(html)
    assert match is not None
    payload_text = match.group(1)
    payload = json.loads(payload_text)
    assert payload["webshop_runtime"]["instruction_text"] == hostile
    assert hostile not in html
    assert "\\u003c/script\\u003e" in payload_text
    assert "\\u0026" in payload_text
    return {
        "round_trip_exact": True,
        "raw_hostile_string_absent_from_html": True,
        "script_boundary_escaped": True,
        "text_content_only": True,
    }


def main() -> None:
    start = json.loads(START_MANIFEST.read_text(encoding="utf-8"))
    current = {
        path.relative_to(ROOT).as_posix(): sha(path)
        for path in sorted((ROOT / "src").rglob("*.py"))
    }
    assert set(current) == set(start) | {PLAYER_REL}
    for rel, expected in start.items():
        assert current[rel] == expected, (rel, expected, current[rel])
    for rel, expected in FROZEN.items():
        assert sha(ROOT / rel) == expected, (rel, expected, sha(ROOT / rel))
    traces = accepted_trace_hashes()
    assert traces == EXPECTED_TRACE_HASHES, (EXPECTED_TRACE_HASHES, traces)
    output = {
        "task_start_src_count": len(start),
        "current_src_count": len(current),
        "added_src": [PLAYER_REL],
        "preexisting_src_unchanged": True,
        "journey_player_sha256": sha(PLAYER_PATH),
        "journey_player_test_sha256": sha(TEST_PATH),
        "frozen_hashes": {rel: sha(ROOT / rel) for rel in FROZEN},
        "accepted_trace_hashes": traces,
        "static_audit": static_audit(),
        "hostile_string_audit": hostile_string_audit(),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

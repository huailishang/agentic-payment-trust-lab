from __future__ import annotations

import ast
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

from agentic_payment_experiment.authoritative_trace_consumer import consume_authoritative_trace
from agentic_payment_experiment.authoritative_trace_player import render_authoritative_trace_player
from agentic_payment_experiment.webshop_prepayment_trace_profiles import PrepaymentScenarioKind
from tests import test_webshop_prepayment_trace_toolkit as prepayment_tests
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01, _valid_t12
from tests.test_webshop_unknown_payment_authoritative_trace import _valid_t09

EVID = Path(__file__).resolve().parent
START_MANIFEST = EVID / "TASK-START-src-manifest.json"
PLAYER_REL = "src/agentic_payment_experiment/authoritative_trace_player.py"
PLAYER_PATH = ROOT / PLAYER_REL
PLAYER_TEST = ROOT / "tests/test_authoritative_trace_player.py"
FROZEN = {
    "src/agentic_payment_experiment/authoritative_trace_consumer.py": "6ad65118a4ab50e648e4f6098f6c2c5009ce5731232ae0a4e11d2f60c0c431b5",
    "tests/test_authoritative_trace_consumer.py": "dfa4a7717020819c96fdc0c21a8c7e68a9aee043a4fb02932b4d8252026100fc",
    "src/agentic_payment_experiment/html_report.py": "b93aeb6f18b59bac195e624b7acf10c20e6ed46338796735a3bfc1017f93164a",
    "src/agentic_payment_experiment/interactive_lab.py": "cb083a9fee9c21e5d87e49f097b1ce33d0546c1b0fb79bb59f7b5b7da6308150",
    "src/agentic_payment_experiment/interactive_server.py": "d0be3aa65cca715845d3c41e38a75cb251764e2287cf49c3eb5efef1019b718f",
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
PAYLOAD_RE = re.compile(r'<script id="trace-payload" type="application/json">(.*?)</script>', re.DOTALL)


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
        primitive(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
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


def static_player_audit() -> dict[str, object]:
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
    assert modules == {"__future__", "hashlib", "json", "typing", "authoritative_trace_consumer"}
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert not any(value in {"T01", "T02", "T07", "T10"} for value in strings)
    assert not any(value.startswith("WEBSHOP_") or value.startswith("ATTACK_OVERLAY_") for value in strings)
    forbidden_source = (
        "fetch(", "XMLHttpRequest", "WebSocket", "EventSource", "sendBeacon", "innerHTML",
        "insertAdjacentHTML", "document.write", "https://", "http://",
    )
    assert all(token not in source for token in forbidden_source)
    assert ".textContent" in source
    assert "document.createElement" in source
    return {
        "imports": sorted(modules),
        "family_task_literals": False,
        "network_hooks": False,
        "unsafe_html_insertion": False,
        "safe_text_content": True,
    }


def hostile_boundary_audit() -> dict[str, object]:
    *_, outcome = _valid_t01()
    assert outcome.authoritative_trace is not None
    consumed = consume_authoritative_trace(outcome.authoritative_trace)
    assert consumed.read_model is not None
    model = consumed.read_model
    hostile = '</script><script>alert("hostile")</script><b>危险 & evidence</b>'
    events = list(model.events)
    events[0] = replace(events[0], entity_ref=hostile)
    hostile_model = replace(model, events=tuple(events))
    html = render_authoritative_trace_player(hostile_model)
    match = PAYLOAD_RE.search(html)
    assert match is not None
    payload_text = match.group(1)
    payload = json.loads(payload_text)
    assert payload["events"][0]["entity_ref"] == hostile
    assert hostile not in html
    assert '\\u003c/script\\u003e' in payload_text
    assert '\\u0026' in payload_text
    assert "innerHTML" not in html
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
    trace_hashes = accepted_trace_hashes()
    assert trace_hashes == EXPECTED_TRACE_HASHES, (EXPECTED_TRACE_HASHES, trace_hashes)

    output = {
        "task_start_src_count": len(start),
        "current_src_count": len(current),
        "added_src": [PLAYER_REL],
        "preexisting_src_unchanged": True,
        "player_sha256": sha(PLAYER_PATH),
        "player_test_sha256": sha(PLAYER_TEST),
        "frozen_hashes": {rel: sha(ROOT / rel) for rel in FROZEN},
        "accepted_trace_hashes": trace_hashes,
        "static_player_audit": static_player_audit(),
        "hostile_boundary_audit": hostile_boundary_audit(),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

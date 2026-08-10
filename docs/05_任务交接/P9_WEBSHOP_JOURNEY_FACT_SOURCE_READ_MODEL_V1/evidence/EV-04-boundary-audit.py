from __future__ import annotations

import ast
import hashlib
import json
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

from agentic_payment_experiment.webshop_prepayment_trace_profiles import PrepaymentScenarioKind
from tests import test_webshop_prepayment_trace_toolkit as prepayment_tests
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01, _valid_t12
from tests.test_webshop_unknown_payment_authoritative_trace import _valid_t09

EVID = Path(__file__).resolve().parent
START_MANIFEST = EVID / "TASK-START-src-manifest.json"
JOURNEY_REL = "src/agentic_payment_experiment/webshop_journey_read_model.py"
JOURNEY_PATH = ROOT / JOURNEY_REL
TEST_PATH = ROOT / "tests/test_webshop_journey_read_model.py"
FROZEN = {
    "samples/external/webshop/pre_buy_now_candidate_v1.json": "6e9d67c3b787cc2d9202bd22b30dec88bf9f920dfa3741bdeb364108a2a3c8e5",
    "src/agentic_payment_experiment/adapters/webshop.py": "035e6bb20d44b0a52be3f6adab2830c402e01f53839e917698343761c5481ec4",
    "src/agentic_payment_experiment/authoritative_trace_consumer.py": "6ad65118a4ab50e648e4f6098f6c2c5009ce5731232ae0a4e11d2f60c0c431b5",
    "src/agentic_payment_experiment/authoritative_trace_player.py": "9cd38620ee966632191b376f13d95446711ff55d08b18aa844f9a7fb6ef74541",
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
    source = JOURNEY_PATH.read_text(encoding="utf-8")
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
    expected_modules = {
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
    }
    assert modules == expected_modules, (expected_modules, modules)
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
        "adapt_webshop_purchase_candidate(",
        "authoritative_trace_player",
        "webshop_payment_sidecar",
        "run_scenarios",
        "validate_request",
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "requests",
        "urllib",
        "playwright",
        "selenium",
    )
    assert all(token not in source for token in forbidden)
    return {
        "imports": sorted(modules),
        "fixed_task_profile_ids": False,
        "adapter_reexecution": False,
        "player_import": False,
        "business_execution_calls": False,
        "network_browser_calls": False,
    }


def main() -> None:
    start = json.loads(START_MANIFEST.read_text(encoding="utf-8"))
    current = {
        path.relative_to(ROOT).as_posix(): sha(path)
        for path in sorted((ROOT / "src").rglob("*.py"))
    }
    assert set(current) == set(start) | {JOURNEY_REL}
    for rel, expected in start.items():
        assert current[rel] == expected, (rel, expected, current[rel])
    for rel, expected in FROZEN.items():
        assert sha(ROOT / rel) == expected, (rel, expected, sha(ROOT / rel))
    trace_hashes = accepted_trace_hashes()
    assert trace_hashes == EXPECTED_TRACE_HASHES, (EXPECTED_TRACE_HASHES, trace_hashes)
    output = {
        "task_start_src_count": len(start),
        "current_src_count": len(current),
        "added_src": [JOURNEY_REL],
        "preexisting_src_unchanged": True,
        "journey_source_sha256": sha(JOURNEY_PATH),
        "journey_test_sha256": sha(TEST_PATH),
        "frozen_hashes": {rel: sha(ROOT / rel) for rel in FROZEN},
        "accepted_trace_hashes": trace_hashes,
        "static_audit": static_audit(),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

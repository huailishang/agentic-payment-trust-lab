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

from agentic_payment_experiment.webshop_prepayment_trace_profiles import (
    PrepaymentScenarioKind,
)
from tests import test_webshop_prepayment_trace_toolkit as prepayment_tests
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01, _valid_t12
from tests.test_webshop_unknown_payment_authoritative_trace import _valid_t09

EVID = Path(__file__).resolve().parent
START_LOG = EVID / "EV-01-task-start-raw.stdout.log"
CONSUMER = ROOT / "src/agentic_payment_experiment/authoritative_trace_consumer.py"
NEW_SOURCE = "src/agentic_payment_experiment/authoritative_trace_consumer.py"
CORE_HASHES = {
    "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    "src/agentic_payment_experiment/webshop_trace_assembler.py": "02d73682ec949d7a37be4e3824e614795f069efc26aafe2377ea18e7c69f70c8",
    "src/agentic_payment_experiment/attack_overlay.py": "8fc4200f7d6eb871860897e2117d9c3eea0590643294acff684733186fb5968c",
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


def parse_start_manifest() -> dict[str, str]:
    lines = START_LOG.read_text(encoding="utf-8").splitlines()
    start = lines.index("## existing src manifest") + 1
    manifest: dict[str, str] = {}
    for line in lines[start:]:
        if not line.strip():
            continue
        value, rel = line.split(maxsplit=1)
        manifest[rel.lstrip("* ")] = value
    return manifest


def accepted_trace_hashes() -> dict[str, str]:
    *_, t01_outcome = _valid_t01()
    assert t01_outcome.authoritative_trace is not None

    prepayment = prepayment_tests.WebShopPrepaymentTraceToolkitTest(methodName="runTest")
    prepayment.setUp()
    prepayment_traces: dict[str, object] = {}
    for task_id, kind in (
        ("T02", PrepaymentScenarioKind.PRICE_INCREASE),
        ("T03", PrepaymentScenarioKind.PRICE_DECREASE),
        ("T04", PrepaymentScenarioKind.PAYEE_CHANGE),
    ):
        *_, trace = prepayment.build_case(kind)
        assert trace is not None
        prepayment_traces[task_id] = trace

    *_, t09_outcome = _valid_t09()
    assert t09_outcome.authoritative_trace is not None
    _, _, t10_outcome, _ = _valid_t10()
    assert t10_outcome.authoritative_trace is not None
    *_, t12_outcome = _valid_t12()
    assert t12_outcome.authoritative_trace is not None

    traces = {
        "T01": t01_outcome.authoritative_trace,
        **prepayment_traces,
        "T09": t09_outcome.authoritative_trace,
        "T10": t10_outcome.authoritative_trace,
        "T12": t12_outcome.authoritative_trace,
    }
    return {task_id: digest(trace) for task_id, trace in traces.items()}


def static_consumer_audit() -> dict[str, object]:
    source = CONSUMER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert not any(value in {"T01", "T02", "T07", "T10"} for value in strings)
    assert not any(
        value.startswith("WEBSHOP_") or value.startswith("ATTACK_OVERLAY_")
        for value in strings
    )
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
    forbidden_modules = (
        "webshop",
        "attack_overlay",
        "payment_recovery",
        "payment_finality",
        "project_impact",
        "evaluator",
        "importlib",
        "yaml",
    )
    assert not any(token in module for module in modules for token in forbidden_modules)
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    forbidden_calls = {
        "validate_request",
        "evaluate_context_policy",
        "resolve_fact_lineage",
        "evaluate_attack_overlay",
        "eval",
        "exec",
        "__import__",
    }
    assert called.isdisjoint(forbidden_calls)
    return {
        "imported_modules": sorted(modules),
        "forbidden_family_literals": False,
        "forbidden_business_calls": False,
    }


def main() -> None:
    start_manifest = parse_start_manifest()
    current_manifest = {
        path.relative_to(ROOT).as_posix(): sha(path)
        for path in sorted((ROOT / "src").rglob("*.py"))
    }
    assert set(current_manifest) == set(start_manifest) | {NEW_SOURCE}
    for rel, expected in start_manifest.items():
        assert current_manifest[rel] == expected, (rel, expected, current_manifest[rel])

    for rel, expected in CORE_HASHES.items():
        actual = sha(ROOT / rel)
        assert actual == expected, (rel, expected, actual)

    trace_hashes = accepted_trace_hashes()
    assert trace_hashes == EXPECTED_TRACE_HASHES, (EXPECTED_TRACE_HASHES, trace_hashes)
    static = static_consumer_audit()

    output = {
        "task_start_existing_src_count": len(start_manifest),
        "current_src_count": len(current_manifest),
        "added_src": [NEW_SOURCE],
        "preexisting_src_unchanged": True,
        "new_source_sha256": current_manifest[NEW_SOURCE],
        "core_hashes": {rel: sha(ROOT / rel) for rel in CORE_HASHES},
        "accepted_trace_hashes": trace_hashes,
        "static_consumer_audit": static,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

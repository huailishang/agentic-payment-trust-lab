from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
for entry in (ROOT, ROOT / "src"):
    sys.path.insert(0, str(entry))

from agentic_payment_experiment.authoritative_trace_consumer import (
    TraceConsumerStatus,
    consume_authoritative_trace,
    trace_read_model_to_primitive,
)
from agentic_payment_experiment.authoritative_trace_player import (
    render_authoritative_trace_player,
    trace_player_html_sha256,
    trace_player_payload_sha256,
)
from agentic_payment_experiment.webshop_prepayment_trace_profiles import PrepaymentScenarioKind
from tests import test_attack_overlay_trace_toolkit as attack_tests
from tests import test_webshop_prepayment_trace_toolkit as prepayment_tests
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01

EVID = Path(__file__).resolve().parent
PAYLOAD_RE = re.compile(
    r'<script id="trace-payload" type="application/json">(.*?)</script>',
    re.DOTALL,
)


def representative_models():
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
        attack_id="PLAYER-EVIDENCE-ATTACK",
        title="player evidence",
        source_ref="player-evidence-source",
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
    models = {}
    for task_id, trace in traces.items():
        result = consume_authoritative_trace(trace)
        assert result.status is TraceConsumerStatus.AVAILABLE
        assert result.read_model is not None
        models[task_id] = result.read_model
    return models


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    families = {}
    for task_id, model in representative_models().items():
        source_payload = trace_read_model_to_primitive(model)
        html_runs = [render_authoritative_trace_player(model) for _ in range(3)]
        html_hashes = [sha(value.encode("utf-8")) for value in html_runs]
        payload_hashes = [trace_player_payload_sha256(model) for _ in range(3)]
        assert len(set(html_hashes)) == 1
        assert len(set(payload_hashes)) == 1

        match = PAYLOAD_RE.search(html_runs[0])
        assert match is not None
        embedded = json.loads(match.group(1))
        assert embedded == source_payload

        refs = [binding["binding_ref"] for binding in embedded["source_bindings"]]
        assert len(refs) == len(set(refs))
        assert all(refs.count(event["source_binding_ref"]) == 1 for event in embedded["events"])
        relation_count = sum(len(event["relations"]) for event in embedded["events"])
        assertion_count = sum(
            len(relation["target_binding_assertions"])
            for event in embedded["events"]
            for relation in event["relations"]
        )

        html_path = EVID / f"EV-03-{task_id}.html"
        payload_path = EVID / f"EV-03-{task_id}.payload.json"
        html_path.write_text(html_runs[0], encoding="utf-8")
        payload_path.write_text(
            json.dumps(embedded, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        assert trace_player_html_sha256(model) == html_hashes[0]
        families[task_id] = {
            "profile": model.profile,
            "event_count": len(embedded["events"]),
            "source_binding_count": len(embedded["source_bindings"]),
            "relation_count": relation_count,
            "binding_assertion_count": assertion_count,
            "html_sha256_x3": html_hashes,
            "embedded_payload_sha256_x3": payload_hashes,
            "payload_exact_equal": True,
            "all_source_binding_refs_resolve_exactly_once": True,
            "html_file": html_path.name,
            "payload_file": payload_path.name,
        }

    print(json.dumps({"ui_ready": "4/4", "families": families}, ensure_ascii=False, indent=2))
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

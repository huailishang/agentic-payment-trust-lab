from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
for entry in (ROOT, ROOT / "src"):
    sys.path.insert(0, str(entry))

from agentic_payment_experiment.adapters.webshop import adapt_webshop_purchase_candidate
from agentic_payment_experiment.authoritative_trace_consumer import consume_authoritative_trace
from agentic_payment_experiment.webshop_journey_player import (
    render_webshop_journey_player,
    webshop_journey_player_html_sha256,
    webshop_journey_player_payload_sha256,
)
from agentic_payment_experiment.webshop_journey_read_model import (
    build_webshop_journey_read_model,
    webshop_journey_read_model_sha256,
    webshop_journey_read_model_to_primitive,
)
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01

EVID = Path(__file__).resolve().parent
FIXTURE = ROOT / "samples/external/webshop/pre_buy_now_candidate_v1.json"
PAYLOAD_RE = re.compile(
    r'<script id="journey-payload" type="application/json">(.*?)</script>',
    re.DOTALL,
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    adaptation = adapt_webshop_purchase_candidate(fixture)
    assert adaptation.ready
    *_, outcome = _valid_t01()
    assert outcome.authoritative_trace is not None
    consumed = consume_authoritative_trace(outcome.authoritative_trace)
    assert consumed.read_model is not None
    journey = build_webshop_journey_read_model(fixture, adaptation, consumed.read_model)
    primitive = webshop_journey_read_model_to_primitive(journey)

    html_runs = [render_webshop_journey_player(journey) for _ in range(3)]
    html_hashes = [sha(html.encode("utf-8")) for html in html_runs]
    payload_hashes = [webshop_journey_player_payload_sha256(journey) for _ in range(3)]
    assert len(set(html_hashes)) == 1
    assert len(set(payload_hashes)) == 1
    assert webshop_journey_player_html_sha256(journey) == html_hashes[0]

    match = PAYLOAD_RE.search(html_runs[0])
    assert match is not None
    embedded = json.loads(match.group(1))
    assert embedded == primitive
    assert embedded["webshop_runtime"]["instruction_text"] == fixture["instruction_text"]
    assert embedded["webshop_runtime"]["product"] == fixture["product"]
    assert (
        embedded["experiment_context"]["origin"]
        == "explicit_experiment_context_not_webshop_verified"
    )
    assert "fixed_script_webshop_smoke_not_autonomous_agent" in embedded["limitations"]
    assert all(item["equal"] is True for item in embedded["correlations"])

    order = embedded["commerce_adaptation"]["order"]
    request = embedded["commerce_adaptation"]["payment_request"]
    payment = embedded["payment_authoritative_trace"]
    assert order["order_id"] == request["order_ref"]
    assert len(payment["events"]) == 11
    assert len(payment["source_bindings"]) == 10
    binding_refs = {item["binding_ref"] for item in payment["source_bindings"]}
    assert all(event["source_binding_ref"] in binding_refs for event in payment["events"])

    html = html_runs[0]
    for label in (
        "1. 用户需求与商城动作 / webshop_runtime",
        "2. 实验补充上下文 / experiment_context",
        "3. Commerce 派生对象 / commerce_adaptation",
        "4. 支付权威证据 / payment_authoritative_trace",
        "5. 跨源关联 / correlations",
        "6. 限制与事实边界 / limitations",
        "固定脚本轨迹，不代表自主 Agent",
        "实验补充字段不是 WebShop 核验事实",
        "支付权威轨迹是独立证据源",
        "不判断二者是否匹配",
    ):
        assert label in html
    assert "自主 Agent 已完成购买" not in html
    assert "autonomous Agent completed purchase" not in html

    html_path = EVID / "EV-03-journey-player.html"
    payload_path = EVID / "EV-03-journey-player.payload.json"
    html_path.write_text(html_runs[0], encoding="utf-8")
    payload_path.write_text(
        json.dumps(embedded, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    summary = {
        "journey_ui_ready_representative_path": "1/1",
        "journey_source_classified": "1/1",
        "journey_read_model_sha256": webshop_journey_read_model_sha256(journey),
        "html_sha256_x3": html_hashes,
        "embedded_payload_sha256_x3": payload_hashes,
        "embedded_payload_exact_equal": True,
        "instruction_preserved": embedded["webshop_runtime"]["instruction_text"],
        "selected_product_title": embedded["webshop_runtime"]["product"]["title"],
        "selected_product_total": embedded["webshop_runtime"]["product"]["order_total"],
        "experiment_context_origin": embedded["experiment_context"]["origin"],
        "correlation_count": len(embedded["correlations"]),
        "payment_event_count": len(payment["events"]),
        "payment_source_binding_count": len(payment["source_bindings"]),
        "all_payment_source_binding_refs_resolve": True,
        "fixed_script_boundary_visible": True,
        "autonomous_agent_completion_claim": False,
        "html_file": html_path.name,
        "payload_file": payload_path.name,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

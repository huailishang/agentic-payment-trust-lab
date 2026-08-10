from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
for entry in (ROOT, ROOT / "src"):
    sys.path.insert(0, str(entry))

from agentic_payment_experiment.adapters.webshop import adapt_webshop_purchase_candidate
from agentic_payment_experiment.authoritative_trace_consumer import (
    consume_authoritative_trace,
    trace_read_model_sha256,
    trace_read_model_to_primitive,
)
from agentic_payment_experiment.webshop_journey_read_model import (
    build_webshop_journey_read_model,
    webshop_journey_read_model_sha256,
    webshop_journey_read_model_to_primitive,
)
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01

EVID = Path(__file__).resolve().parent
FIXTURE = ROOT / "samples/external/webshop/pre_buy_now_candidate_v1.json"


def canonical_sha(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    adaptation = adapt_webshop_purchase_candidate(fixture)
    assert adaptation.ready
    *_, outcome = _valid_t01()
    assert outcome.authoritative_trace is not None
    consumed = consume_authoritative_trace(outcome.authoritative_trace)
    assert consumed.read_model is not None
    payment_model = consumed.read_model

    models = [
        build_webshop_journey_read_model(fixture, adaptation, payment_model)
        for _ in range(3)
    ]
    primitives = [webshop_journey_read_model_to_primitive(model) for model in models]
    journey_hashes = [webshop_journey_read_model_sha256(model) for model in models]
    assert len(set(journey_hashes)) == 1
    assert primitives[0] == primitives[1] == primitives[2]

    primitive = primitives[0]
    assert set(primitive) == {
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
    assert primitive["experiment_context"] == fixture["experiment_context"]
    assert (
        primitive["experiment_context"]["origin"]
        == "explicit_experiment_context_not_webshop_verified"
    )
    expected_payment = trace_read_model_to_primitive(payment_model)
    assert primitive["payment_authoritative_trace"] == expected_payment
    assert canonical_sha(primitive["payment_authoritative_trace"]) == trace_read_model_sha256(payment_model)
    assert all(item["equal"] is True for item in primitive["correlations"])

    out = EVID / "EV-03-journey-read-model.json"
    out.write_text(
        json.dumps(primitive, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    summary = {
        "journey_source_classified_representative_path": "1/1",
        "source_classification_status": primitive["source_classification_status"],
        "journey_ref": primitive["journey_ref"],
        "journey_sha256_x3": journey_hashes,
        "namespace_keys": [
            "webshop_runtime",
            "experiment_context",
            "commerce_adaptation",
            "payment_authoritative_trace",
        ],
        "webshop_actions": primitive["webshop_runtime"]["actions_executed"],
        "buy_now_available": primitive["webshop_runtime"]["buy_now_available"],
        "buy_now_executed": primitive["webshop_runtime"]["buy_now_executed"],
        "experiment_context_origin": primitive["experiment_context"]["origin"],
        "payment_trace_sha256": trace_read_model_sha256(payment_model),
        "payment_namespace_sha256": canonical_sha(primitive["payment_authoritative_trace"]),
        "correlation_count": len(primitive["correlations"]),
        "correlations": primitive["correlations"],
        "limitations": primitive["limitations"],
        "evidence_file": out.name,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from decimal import Decimal
from enum import Enum
from pathlib import Path
from datetime import datetime

from agentic_payment_experiment import assess_webshop_payment_fulfilment
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_payment_sidecar import WebShopPaymentSidecarTest


def primitive(value):
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
        return "0" if text in {"-0", ""} else text
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or isinstance(value, (bool, int, str)):
        return value
    raise TypeError(f"unsupported snapshot value: {type(value)!r}")


def canonical_bytes(value) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def main() -> None:
    _, _, t10_outcome, _ = _valid_t10()
    assert t10_outcome.authoritative_trace is not None

    case = WebShopPaymentSidecarTest(methodName="runTest")
    case.setUp()
    gate, _, payment, fulfillment = case.happy_path_inputs()
    t01_outcome = assess_webshop_payment_fulfilment(
        gate_outcome=gate,
        adaptation=case.adaptation,
        mandate=case.mandate,
        payment=payment,
        fulfillment=fulfillment,
    )
    assert t01_outcome.authoritative_trace is not None

    traces = {
        "T01": primitive(t01_outcome.authoritative_trace),
        "T10": primitive(t10_outcome.authoritative_trace),
    }
    output = {
        "schema": "product-trace-refactor-baseline/v1",
        "traces": traces,
        "trace_sha256": {
            task_id: hashlib.sha256(canonical_bytes(trace)).hexdigest()
            for task_id, trace in traces.items()
        },
    }
    output["combined_sha256"] = hashlib.sha256(canonical_bytes(traces)).hexdigest()

    target = Path(__file__).with_name("BASELINE-trace-snapshots.json")
    target.write_text(
        json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "target": str(target),
        "trace_sha256": output["trace_sha256"],
        "combined_sha256": output["combined_sha256"],
        "t01_events": len(traces["T01"]["events"]),
        "t01_bindings": len(traces["T01"]["source_bindings"]),
        "t10_events": len(traces["T10"]["events"]),
        "t10_bindings": len(traces["T10"]["source_bindings"]),
    }, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

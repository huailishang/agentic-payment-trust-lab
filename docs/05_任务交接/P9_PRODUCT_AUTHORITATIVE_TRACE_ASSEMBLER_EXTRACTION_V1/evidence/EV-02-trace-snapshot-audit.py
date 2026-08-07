from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path

from agentic_payment_experiment import assess_webshop_payment_fulfilment
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_payment_sidecar import WebShopPaymentSidecarTest


ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
BASELINE = EVIDENCE / "BASELINE-trace-snapshots.json"
AFTER = EVIDENCE / "EV-02-after-trace-snapshots.json"
EXPECTED_FILE_SHA256 = "2d33116baca3e6fd401afbb3c4f01552decbd5959d8452d2d6301fcf1fd58234"
EXPECTED_T01_SHA256 = "7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906"
EXPECTED_T10_SHA256 = "2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3"
EXPECTED_COMBINED_SHA256 = "d913fc7d3a69abfb0c7774356a988a5e23cf3780a70523a03ced2672bec5ac4c"


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


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    AFTER.write_text(
        json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert output == baseline
    assert file_sha256(BASELINE) == EXPECTED_FILE_SHA256
    assert file_sha256(AFTER) == EXPECTED_FILE_SHA256
    assert output["trace_sha256"]["T01"] == EXPECTED_T01_SHA256
    assert output["trace_sha256"]["T10"] == EXPECTED_T10_SHA256
    assert output["combined_sha256"] == EXPECTED_COMBINED_SHA256
    assert len(traces["T01"]["events"]) == 11
    assert len(traces["T01"]["source_bindings"]) == 10
    assert len(traces["T10"]["events"]) == 12
    assert len(traces["T10"]["source_bindings"]) == 11

    print(f"baseline_file_sha256={file_sha256(BASELINE)}")
    print(f"after_file_sha256={file_sha256(AFTER)}")
    print(f"t01_trace_sha256={output['trace_sha256']['T01']}")
    print(f"t10_trace_sha256={output['trace_sha256']['T10']}")
    print(f"combined_trace_sha256={output['combined_sha256']}")
    print("t01_events=11")
    print("t01_bindings=10")
    print("t10_events=12")
    print("t10_bindings=11")
    print("byte_for_byte_equal=True")
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

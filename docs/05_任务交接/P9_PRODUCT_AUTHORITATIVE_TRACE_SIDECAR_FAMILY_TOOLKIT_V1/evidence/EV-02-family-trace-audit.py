from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path

from agentic_payment_experiment.authoritative_trace import (
    TraceValidationStatus,
    validate_product_authoritative_trace,
)
from tests.test_webshop_authoritative_trace import _valid_t10
from tests.test_webshop_sidecar_trace_toolkit import _valid_t01, _valid_t12
from tests.test_webshop_unknown_payment_authoritative_trace import _valid_t09


ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
OUT = EVIDENCE / "EV-02-family-full-traces.json"
EXPECTED = {
    "T01": "7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906",
    "T09": "a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e",
    "T10": "2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3",
}


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
    raise TypeError(f"unsupported trace value: {type(value)!r}")


def canonical_bytes(value) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def trace_hash(trace) -> str:
    return hashlib.sha256(canonical_bytes(primitive(trace))).hexdigest()


def main() -> None:
    _, _, _, _, _, t01_outcome = _valid_t01()
    _, _, _, _, _, _, t09_outcome = _valid_t09()
    _, _, t10_outcome, _ = _valid_t10()
    *_, t12_outcome = _valid_t12()
    traces = {
        "T01": t01_outcome.authoritative_trace,
        "T09": t09_outcome.authoritative_trace,
        "T10": t10_outcome.authoritative_trace,
        "T12": t12_outcome.authoritative_trace,
    }
    expected_profiles = {
        "T01": "WEBSHOP_NORMAL_PURCHASE_V2",
        "T09": "WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2",
        "T10": "WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V2",
        "T12": "WEBSHOP_PAYMENT_STATUS_CONFLICT_V2",
    }
    expected_events = {"T01": 11, "T09": 11, "T10": 12, "T12": 11}
    expected_bindings = {"T01": 10, "T09": 10, "T10": 11, "T12": 10}
    data = {}
    hashes = {}
    for task_id, trace in traces.items():
        assert trace is not None
        validation = validate_product_authoritative_trace(trace)
        assert validation.status is TraceValidationStatus.VALID
        assert validation.profile == expected_profiles[task_id]
        assert trace.source == "PRODUCT_OBSERVED"
        assert len(trace.events) == expected_events[task_id]
        assert len(trace.source_bindings) == expected_bindings[task_id]
        data[task_id] = primitive(trace)
        hashes[task_id] = trace_hash(trace)

    for task_id, expected_hash in EXPECTED.items():
        assert hashes[task_id] == expected_hash

    t12_roles = {event.entity_role: event for event in traces["T12"].events}
    assert t12_roles["CURRENT_PAYMENT_CANDIDATE"].status == "PENDING"
    assert t12_roles["PAYMENT_EXECUTION_OUTCOME"].status == "UNKNOWN"
    assert t12_roles["STATUS_CONFLICT_FACT"].status == "CONFLICT"
    assert t12_roles["FINAL_OUTCOME"].status == "UNKNOWN"
    assert (
        t12_roles["AUTHORIZED_ORDER_SNAPSHOT"].source_binding_ref
        == t12_roles["CURRENT_ORDER_SNAPSHOT"].source_binding_ref
    )
    assert (
        t12_roles["CURRENT_PAYMENT_CANDIDATE"].entity_ref
        == t12_roles["PAYMENT_EXECUTION_OUTCOME"].entity_ref
    )
    assert (
        t12_roles["CURRENT_PAYMENT_CANDIDATE"].source_binding_ref
        != t12_roles["PAYMENT_EXECUTION_OUTCOME"].source_binding_ref
    )

    OUT.write_text(
        json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    file_sha = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print("validator_status=VALID")
    for task_id in ("T01", "T09", "T10", "T12"):
        print(f"{task_id}_profile={expected_profiles[task_id]}")
        print(f"{task_id}_events={expected_events[task_id]}")
        print(f"{task_id}_bindings={expected_bindings[task_id]}")
        print(f"{task_id}_trace_sha256={hashes[task_id]}")
    print("t12_candidate_status=PENDING")
    print("t12_payment_outcome_status=UNKNOWN")
    print("t12_conflict_status=CONFLICT")
    print("t12_final_status=UNKNOWN")
    print(f"saved_file_sha256={file_sha}")
    print(f"saved_file={OUT.relative_to(ROOT).as_posix()}")
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

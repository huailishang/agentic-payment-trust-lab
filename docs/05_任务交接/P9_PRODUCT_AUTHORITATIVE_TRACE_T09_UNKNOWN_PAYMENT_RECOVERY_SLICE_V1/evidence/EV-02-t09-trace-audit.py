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
from tests.test_webshop_unknown_payment_authoritative_trace import _valid_t09


ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
OUT = EVIDENCE / "EV-02-t09-full-trace.json"


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


def main() -> None:
    _, _, _, _, _, _, outcome = _valid_t09()
    trace = outcome.authoritative_trace
    assert trace is not None
    validation = validate_product_authoritative_trace(trace)
    assert validation.status is TraceValidationStatus.VALID
    assert validation.profile == "WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2"
    assert trace.source == "PRODUCT_OBSERVED"
    assert len(trace.events) == 11
    assert len(trace.source_bindings) == 10

    roles = {event.entity_role: event for event in trace.events}
    assert roles["CURRENT_PAYMENT_CANDIDATE"].status == "PENDING"
    assert roles["PAYMENT_EXECUTION_OUTCOME"].status == "SUCCEEDED"
    assert roles["RECOVERY_OUTCOME"].status == "RECOVERED"
    assert roles["FINAL_OUTCOME"].status == "SUCCEEDED"
    assert (
        roles["AUTHORIZED_ORDER_SNAPSHOT"].source_binding_ref
        == roles["CURRENT_ORDER_SNAPSHOT"].source_binding_ref
    )
    assert (
        roles["CURRENT_PAYMENT_CANDIDATE"].entity_ref
        == roles["PAYMENT_EXECUTION_OUTCOME"].entity_ref
    )
    assert (
        roles["CURRENT_PAYMENT_CANDIDATE"].source_binding_ref
        != roles["PAYMENT_EXECUTION_OUTCOME"].source_binding_ref
    )

    data = primitive(trace)
    OUT.write_text(
        json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(canonical_bytes(data)).hexdigest()
    file_digest = hashlib.sha256(OUT.read_bytes()).hexdigest()

    print("validator_status=VALID")
    print("profile=WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2")
    print("source=PRODUCT_OBSERVED")
    print("product_source=webshop_payment_fulfilment_outcome")
    print("events=11")
    print("unique_bindings=10")
    print("candidate_status=PENDING")
    print("payment_outcome_status=SUCCEEDED")
    print("recovery_status=RECOVERED")
    print("final_status=SUCCEEDED")
    print(f"canonical_trace_sha256={digest}")
    print(f"trace_file_sha256={file_digest}")
    print(f"saved_trace={OUT.relative_to(ROOT).as_posix()}")
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

"""Explicit, closed-schema codec for the original H74 GateContext graph.

No dynamic imports, pickle, eval, encryption, or claims of authenticated consent.
The SHA-256 over canonical bytes is a *local* integrity reference only.
"""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
import hashlib
import json

from .adapters.stripe_checkout import GateContext, StripeCheckoutError
from .models import (
    AgentIdentity, Decision, IntentMandate, Order, OrderItem,
    PaymentExecutionRecord, PaymentStatus, TransactionRequest,
)
from .trusted_execution.confirmation import ConfirmationRecord, ConfirmationStatus
from .trusted_execution.context_policy import ContextPolicyFact, SourceCoverage, SourceType
from .trusted_execution.execution_facts import VerificationStatus

SCHEMA = "h74-authority-context/v1"
_TYPES = {x.__name__: x for x in (
    GateContext, AgentIdentity, IntentMandate, Order, OrderItem, TransactionRequest,
    PaymentExecutionRecord, ConfirmationRecord, ContextPolicyFact, SourceCoverage,
)}
_ENUMS = {x.__name__: x for x in (
    Decision, PaymentStatus, ConfirmationStatus, SourceType, VerificationStatus,
)}


def _reject() -> None:
    raise StripeCheckoutError("authority_context_codec_invalid")


def _aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


def _encode(value, depth: int = 0):
    if depth > 40:
        _reject()
    if value is None or type(value) in (str, bool, int):
        return value
    if isinstance(value, Enum) and type(value) is _ENUMS.get(type(value).__name__):
        return {"tag": "enum", "name": type(value).__name__, "value": value.value}
    if type(value) is Decimal:
        if not value.is_finite():
            _reject()
        return {"tag": "decimal", "value": str(value)}
    if type(value) is datetime:
        if not _aware(value):
            _reject()
        return {"tag": "datetime", "value": value.isoformat()}
    if type(value) in (tuple, list, frozenset):
        encoded = [_encode(x, depth + 1) for x in value]
        if type(value) is frozenset:
            encoded.sort(key=lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True))
        return {"tag": type(value).__name__, "items": encoded}
    if type(value) is dict:
        if any(type(k) is not str for k in value):
            _reject()
        return {"tag": "dict", "items": [
            [k, _encode(value[k], depth + 1)] for k in sorted(value)
        ]}
    if is_dataclass(value) and type(value).__name__ in _TYPES and type(value) is _TYPES[type(value).__name__]:
        return {"tag": "dataclass", "name": type(value).__name__, "fields": {
            f.name: _encode(getattr(value, f.name), depth + 1) for f in fields(value)
        }}
    _reject()


def _decode(value, depth: int = 0):
    if depth > 40:
        _reject()
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is not dict or type(value.get("tag")) is not str:
        _reject()
    tag = value["tag"]
    try:
        if tag == "enum" and set(value) == {"tag", "name", "value"} and value["name"] in _ENUMS:
            return _ENUMS[value["name"]](value["value"])
        if tag == "decimal" and set(value) == {"tag", "value"} and type(value["value"]) is str:
            out = Decimal(value["value"])
            if out.is_finite():
                return out
        if tag == "datetime" and set(value) == {"tag", "value"} and type(value["value"]) is str:
            out = datetime.fromisoformat(value["value"])
            if _aware(out):
                return out
        if tag in {"tuple", "list", "frozenset"} and set(value) == {"tag", "items"} and type(value["items"]) is list:
            sequence = [_decode(x, depth + 1) for x in value["items"]]
            return {"tuple": tuple, "list": list, "frozenset": frozenset}[tag](sequence)
        if tag == "dict" and set(value) == {"tag", "items"} and type(value["items"]) is list:
            pairs = value["items"]
            if any(type(x) is not list or len(x) != 2 or type(x[0]) is not str for x in pairs):
                _reject()
            keys = [x[0] for x in pairs]
            if keys != sorted(set(keys)):
                _reject()
            return {k: _decode(v, depth + 1) for k, v in pairs}
        if tag == "dataclass" and set(value) == {"tag", "name", "fields"}:
            cls = _TYPES.get(value["name"])
            if cls is None or type(value["fields"]) is not dict:
                _reject()
            expected = {f.name for f in fields(cls)}
            if set(value["fields"]) != expected:
                _reject()
            return cls(**{k: _decode(v, depth + 1) for k, v in value["fields"].items()})
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        raise StripeCheckoutError("authority_context_codec_invalid") from None
    _reject()


def serialize_authority(operation_id: str, ctx: GateContext, *, resource_sha256: str,
                        recorded_at: datetime, run_id: str) -> tuple[str, str]:
    if type(ctx) is not GateContext or not _aware(recorded_at):
        _reject()
    obj = {
        "schema": SCHEMA,
        "operation_id": operation_id,
        "run_id": run_id,
        "resource_sha256": resource_sha256,
        "recorded_at": _encode(recorded_at),
        "context": _encode(ctx),
    }
    serialized = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return serialized, digest


def deserialize_authority(payload: str, *, operation_id: str, resource_sha256: str,
                          run_id: str) -> GateContext:
    try:
        obj = json.loads(payload)
        if type(obj) is not dict or set(obj) != {
            "schema", "operation_id", "run_id", "resource_sha256", "recorded_at", "context"
        } or obj["schema"] != SCHEMA or (
            obj["operation_id"] != operation_id or obj["run_id"] != run_id
            or obj["resource_sha256"] != resource_sha256
        ):
            _reject()
        _decode(obj["recorded_at"])
        context = _decode(obj["context"])
        if type(context) is not GateContext:
            _reject()
        # The decoded graph must re-encode identically; no silently ignored data.
        if serialize_authority(operation_id, context, resource_sha256=resource_sha256,
                               recorded_at=_decode(obj["recorded_at"]), run_id=run_id)[0] != payload:
            _reject()
        return context
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        raise StripeCheckoutError("authority_context_codec_invalid") from None

"""Deterministic canonicalization and hashing for local trusted-execution experiments.

The canonicalization contract is intentionally narrower than a production
cross-language signing standard. It exists to make the project's Python domain
objects hashable without letting representation details silently change the
digest.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import unicodedata
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

_TYPE_KEY = "$type"
_VALUE_KEY = "value"


def canonicalize(value: Any) -> Any:
    """Convert supported Python values into the project's canonical JSON shape.

    Contract highlights:
    - mapping key order is irrelevant; keys and string values are normalized to NFC;
    - ``Decimal`` values use an exact, scale-insensitive decimal representation;
    - aware ``datetime`` values are converted to UTC with fixed microsecond precision;
    - ``list`` and ``tuple`` are equivalent, while element order remains significant;
    - dataclass fields are included by name, so a present ``None`` stays distinct from
      an absent mapping field;
    - binary ``float`` is rejected rather than entering financial hashes implicitly.

    This function returns verification input only. It does not make payment-policy
    decisions and does not claim RFC 8785/JCS conformance.
    """

    if value is None or isinstance(value, bool):
        return value

    if isinstance(value, Enum):
        return canonicalize(value.value)

    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)

    if isinstance(value, int):
        return value

    if isinstance(value, Decimal):
        return {
            _TYPE_KEY: "decimal",
            _VALUE_KEY: _canonical_decimal(value),
        }

    if isinstance(value, float):
        raise TypeError(
            "float values are not accepted by the canonicalization contract; "
            "use Decimal or an explicit text representation"
        )

    if isinstance(value, datetime):
        return {
            _TYPE_KEY: "datetime",
            _VALUE_KEY: _canonical_datetime(value),
        }

    if is_dataclass(value) and not isinstance(value, type):
        return canonicalize(
            {field.name: getattr(value, field.name) for field in fields(value)}
        )

    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("canonical JSON mappings require string keys")
            normalized_key = unicodedata.normalize("NFC", key)
            if normalized_key == _TYPE_KEY:
                raise ValueError(
                    f"mapping key {_TYPE_KEY!r} is reserved for canonicalization metadata"
                )
            if normalized_key in result:
                raise ValueError(
                    "mapping keys collide after Unicode NFC normalization: "
                    f"{normalized_key!r}"
                )
            result[normalized_key] = canonicalize(item)
        return result

    if isinstance(value, (list, tuple)):
        return [canonicalize(item) for item in value]

    if isinstance(value, (set, frozenset)):
        normalized_items = [canonicalize(item) for item in value]
        normalized_items.sort(key=_json_for_normalized_value)
        return {
            _TYPE_KEY: "set",
            "items": normalized_items,
        }

    raise TypeError(
        "unsupported value for canonicalization: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def canonical_json(value: Any) -> str:
    """Serialize supported values deterministically after canonicalization."""

    return _json_for_normalized_value(canonicalize(value))


def canonical_hash(value: Any, algorithm: str = "sha256") -> str:
    """Return a hexadecimal digest for a canonically serialized object."""

    try:
        digest = hashlib.new(algorithm)
    except ValueError as exc:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from exc

    digest.update(canonical_json(value).encode("utf-8"))
    return digest.hexdigest()


def verify_hash(expected_hash: str, value: Any, algorithm: str = "sha256") -> bool:
    """Verify that *value* matches the expected canonical digest."""

    actual_hash = canonical_hash(value, algorithm=algorithm)
    return hmac.compare_digest(expected_hash.lower(), actual_hash.lower())


def _json_for_normalized_value(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _canonical_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("Decimal values must be finite")
    if value.is_zero():
        return "0"

    sign, digit_tuple, exponent = value.as_tuple()
    digits = list(digit_tuple)

    while digits and digits[-1] == 0:
        digits.pop()
        exponent += 1

    coefficient = "".join(str(digit) for digit in digits)
    if exponent >= 0:
        text = coefficient + ("0" * exponent)
    else:
        point = len(coefficient) + exponent
        if point > 0:
            text = f"{coefficient[:point]}.{coefficient[point:]}"
        else:
            text = f"0.{('0' * (-point))}{coefficient}"

    return f"-{text}" if sign else text


def _canonical_datetime(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime values must be timezone-aware")

    normalized = value.astimezone(timezone.utc)
    return normalized.isoformat(timespec="microseconds").replace("+00:00", "Z")

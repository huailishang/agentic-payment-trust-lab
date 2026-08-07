from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
COVERAGE = (
    ROOT
    / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-01-coverage-projection-identity-formula.json"
)
OUTPUT = ROOT / "src/agentic_payment_experiment/authoritative_trace.py"

accepted = json.loads(COVERAGE.read_text(encoding="utf-8"))
runtime_contract = {
    key: accepted[key]
    for key in (
        "projection_identity_formula_registry",
        "projection_registry",
        "tasks",
        "forbidden_projection_fields",
        "reference_model",
        "canonical_decimal",
    )
}
embedded_json = json.dumps(
    runtime_contract,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
)

SOURCE_TEMPLATE = r'''"""Pure measurement contracts and strict validation for product traces.

The accepted registry is embedded below. Runtime code never reads docs, handoff
artifacts, fixtures, hidden execution context, source objects, or evaluator replay to complete a
product trace.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, TypeAlias


class TraceContractError(ValueError):
    """Raised when a value cannot enter the closed primitive contract."""


class TraceValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    INDETERMINATE = "INDETERMINATE"


Primitive: TypeAlias = Any


class FrozenDict(Mapping[str, Primitive]):
    """Small immutable mapping for public trace data and frozen registries."""

    __slots__ = ("_items", "_lookup")

    def __init__(self, values: Mapping[str, Primitive] | None = None) -> None:
        items = tuple(sorted((values or {}).items(), key=lambda item: item[0]))
        self._items = items
        self._lookup = dict(items)

    def __getitem__(self, key: str) -> Primitive:
        return self._lookup[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._lookup)

    def __len__(self) -> int:
        return len(self._lookup)

    def __repr__(self) -> str:
        return f"FrozenDict({self._lookup!r})"

    def __hash__(self) -> int:
        return hash(self._items)


def _canonical_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise TraceContractError("non-finite Decimal is forbidden")
    if value == 0:
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def canonical_primitive(value: Any) -> Any:
    """Convert the accepted closed set to deterministic JSON primitives."""

    if value is None or type(value) in {bool, int, str}:
        return value
    if isinstance(value, float):
        raise TraceContractError("float is forbidden")
    if isinstance(value, Decimal):
        return _canonical_decimal(value)
    if isinstance(value, Enum):
        return canonical_primitive(value.value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        converted: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TraceContractError("mapping keys must be strings")
            converted[key] = canonical_primitive(item)
        return converted
    if isinstance(value, (tuple, list)):
        return [canonical_primitive(item) for item in value]
    raise TraceContractError(f"unsupported trace value: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        canonical_primitive(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _freeze(value: Any) -> Primitive:
    primitive = canonical_primitive(value)
    if isinstance(primitive, dict):
        return FrozenDict({key: _freeze(item) for key, item in primitive.items()})
    if isinstance(primitive, list):
        return tuple(_freeze(item) for item in primitive)
    return primitive


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class TraceSourceBinding:
    binding_ref: str
    source_object_type: str
    source_object_ref: str
    projection_schema: str
    projection: Mapping[str, Any]

    def __post_init__(self) -> None:
        frozen = _freeze(self.projection)
        if not isinstance(frozen, FrozenDict):
            raise TraceContractError("projection must be a mapping")
        object.__setattr__(self, "projection", frozen)


@dataclass(frozen=True)
class TraceBindingAssertion:
    source_path: str
    target_path: str
    source_value: Any = None
    target_value: Any = None
    equal: bool | None = None

    def __post_init__(self) -> None:
        if self.source_value is not None:
            object.__setattr__(self, "source_value", _freeze(self.source_value))
        if self.target_value is not None:
            object.__setattr__(self, "target_value", _freeze(self.target_value))


@dataclass(frozen=True)
class TraceRelation:
    relation_type: str
    target_entity_type: str
    target_entity_role: str
    target_entity_ref: str
    target_binding_assertions: tuple[TraceBindingAssertion, ...] = ()
    target_resolved: bool | None = None


@dataclass(frozen=True)
class ProductTraceEvent:
    sequence_no: int
    event_type: str
    entity_type: str
    entity_role: str
    entity_ref: str
    source_binding_ref: str
    decision: str | None = None
    status: str | None = None
    reason_codes: tuple[str, ...] = ()
    relations: tuple[TraceRelation, ...] = ()


@dataclass(frozen=True)
class ProductAuthoritativeTrace:
    schema_version: str
    source: str
    profile: str
    trace_ref: str
    completeness_status: str
    reason_codes: tuple[str, ...] = ()
    events: tuple[ProductTraceEvent, ...] = ()
    source_bindings: tuple[TraceSourceBinding, ...] = ()


@dataclass(frozen=True)
class TraceValidationResult:
    status: TraceValidationStatus
    reason_codes: tuple[str, ...]
    profile: str | None
    event_types: tuple[str, ...]


EXPECTED_TRACE_SCHEMA_VERSION = "product-authoritative-trace/v1"
EXPECTED_TRACE_SOURCE = "PRODUCT_OBSERVED"
EXPECTED_COMPLETENESS_STATUS = "COMPLETE"

_RUNTIME_CONTRACT_JSON = __EMBEDDED_JSON_REPR__
_RUNTIME_CONTRACT_MUTABLE = json.loads(_RUNTIME_CONTRACT_JSON)
_RUNTIME_CONTRACT = _freeze(_RUNTIME_CONTRACT_MUTABLE)
if not isinstance(_RUNTIME_CONTRACT, FrozenDict):
    raise RuntimeError("embedded runtime contract must be a mapping")

FORMULA_REGISTRY = _RUNTIME_CONTRACT["projection_identity_formula_registry"]
PROJECTION_REGISTRY = _RUNTIME_CONTRACT["projection_registry"]
PROFILE_TASKS = _RUNTIME_CONTRACT["tasks"]
FORBIDDEN_PROJECTION_FIELDS = _RUNTIME_CONTRACT["forbidden_projection_fields"]
REFERENCE_MODEL = _RUNTIME_CONTRACT["reference_model"]
CANONICAL_DECIMAL_CONTRACT = _RUNTIME_CONTRACT["canonical_decimal"]

ACCEPTED_FORMULA_REGISTRY_SHA256 = "2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd"
ACCEPTED_PROJECTION_REGISTRY_SHA256 = "45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4"
ACCEPTED_PROFILES_SHA256 = "6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2"
ACCEPTED_RUNTIME_CONTRACT_SHA256 = "4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e"


def runtime_registry_hashes() -> FrozenDict:
    return FrozenDict(
        {
            "formula_registry": canonical_sha256(_thaw(FORMULA_REGISTRY)),
            "projection_registry": canonical_sha256(_thaw(PROJECTION_REGISTRY)),
            "profiles": canonical_sha256(_thaw(PROFILE_TASKS)),
            "runtime_contract": canonical_sha256(_thaw(_RUNTIME_CONTRACT)),
        }
    )


def runtime_contract_primitive() -> dict[str, Any]:
    """Return a detached primitive copy for parity tests."""

    return _thaw(_RUNTIME_CONTRACT)


def _profile_map() -> dict[str, Mapping[str, Any]]:
    return {str(item["profile"]): item for item in PROFILE_TASKS}  # type: ignore[index]


PROFILE_REGISTRY = FrozenDict({key: value for key, value in _profile_map().items()})
_TEMPLATE_PATTERN = re.compile(r"\{([^{}]+)\}")
_BINDING_PREFIX = "TraceSourceBinding:sha256:"


def _lookup_projection_schema(projection_schema: str) -> Mapping[str, Any]:
    try:
        entry = PROJECTION_REGISTRY[projection_schema]  # type: ignore[index]
    except KeyError as exc:
        raise TraceContractError(f"unknown projection schema: {projection_schema}") from exc
    if not isinstance(entry, Mapping):
        raise TraceContractError("projection registry entry is invalid")
    return entry


def _render_template(
    template: str,
    projection: Mapping[str, Any],
    *,
    binding_digest: str | None = None,
    value: Any = None,
) -> str:
    def replace(match: re.Match[str]) -> str:
        token = match.group(1)
        if token == "binding_digest":
            if binding_digest is None:
                raise TraceContractError("binding digest is required")
            return binding_digest
        if token == "value":
            if value is None:
                raise TraceContractError("relation value is required")
            return str(value)
        field_name = token.removeprefix("projection.")
        if field_name not in projection:
            raise TraceContractError(f"template field is missing: {field_name}")
        field_value = projection[field_name]
        if isinstance(field_value, (Mapping, tuple)):
            raise TraceContractError(f"template field is not scalar: {field_name}")
        return str(field_value)

    rendered = _TEMPLATE_PATTERN.sub(replace, template)
    if "{" in rendered or "}" in rendered:
        raise TraceContractError("template was not fully resolved")
    return rendered


def compute_projection_source_ref(
    source_object_type: str,
    projection_schema: str,
    projection: Mapping[str, Any],
) -> str:
    entry = _lookup_projection_schema(projection_schema)
    identity = entry["source_identity"]
    if not isinstance(identity, Mapping):
        raise TraceContractError("source identity entry is invalid")
    mode = identity["mode"]
    primitive_projection = canonical_primitive(projection)
    if mode == "NATIVE_TEMPLATE":
        template = identity.get("template")
        if not isinstance(template, str) or not template:
            raise TraceContractError("native identity template is missing")
        return _render_template(template, primitive_projection)
    if mode != "PROJECTION_HASH_IDENTITY":
        raise TraceContractError(f"unsupported source identity mode: {mode}")
    if identity.get("formula_id") != "PROJECTION_HASH_IDENTITY_V1":
        raise TraceContractError("projection identity formula is not accepted")
    if list(identity.get("payload_fields", ())) != ["projection_schema", "projection"]:
        raise TraceContractError("projection identity payload fields are invalid")
    payload = {
        "projection_schema": projection_schema,
        "projection": primitive_projection,
    }
    digest = canonical_sha256(payload)
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise TraceContractError("projection identity digest is invalid")
    prefix_template = identity.get("prefix_template")
    if prefix_template != "{source_object_type}:projection-sha256:":
        raise TraceContractError("projection identity prefix is invalid")
    return prefix_template.replace("{source_object_type}", source_object_type) + digest


def compute_binding_ref(binding: TraceSourceBinding | Mapping[str, Any]) -> str:
    if isinstance(binding, TraceSourceBinding):
        payload = {
            "source_object_type": binding.source_object_type,
            "source_object_ref": binding.source_object_ref,
            "projection_schema": binding.projection_schema,
            "projection": _thaw(binding.projection),
        }
    else:
        payload = {
            "source_object_type": binding["source_object_type"],
            "source_object_ref": binding["source_object_ref"],
            "projection_schema": binding["projection_schema"],
            "projection": canonical_primitive(binding["projection"]),
        }
    return _BINDING_PREFIX + canonical_sha256(payload)


def render_entity_ref(binding: TraceSourceBinding, template: str) -> str:
    if not binding.binding_ref.startswith(_BINDING_PREFIX):
        raise TraceContractError("binding_ref format is invalid")
    digest = binding.binding_ref[len(_BINDING_PREFIX) :]
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise TraceContractError("binding_ref digest format is invalid")
    return _render_template(template, binding.projection, binding_digest=digest)


def _extract_path(projection: Mapping[str, Any], path: str) -> Any:
    if not path.startswith("projection."):
        raise TraceContractError(f"unsupported extraction path: {path}")
    current: Any = projection
    for token in path[len("projection.") :].split("."):
        array = token.endswith("[]")
        key = token[:-2] if array else token
        if not isinstance(current, Mapping) or key not in current:
            raise TraceContractError(f"extraction path is missing: {path}")
        current = current[key]
        if array and not isinstance(current, tuple):
            raise TraceContractError(f"array extraction path is not an array: {path}")
    return current


def _contains_forbidden_field(value: Any) -> str | None:
    forbidden = {str(item) for item in FORBIDDEN_PROJECTION_FIELDS}
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in forbidden:
                return key
            nested = _contains_forbidden_field(item)
            if nested is not None:
                return nested
    elif isinstance(value, tuple):
        for item in value:
            nested = _contains_forbidden_field(item)
            if nested is not None:
                return nested
    return None


def validate_trace_source_binding(binding: object) -> TraceValidationResult:
    """Validate one binding without using a profile or any source object."""

    if not isinstance(binding, TraceSourceBinding):
        return TraceValidationResult(
            TraceValidationStatus.INVALID,
            ("trace_binding_contract_type_invalid",),
            None,
            (),
        )
    try:
        registry = _lookup_projection_schema(binding.projection_schema)
    except TraceContractError:
        return TraceValidationResult(
            TraceValidationStatus.INDETERMINATE,
            ("trace_projection_schema_unknown",),
            None,
            (),
        )
    if binding.source_object_type != registry["source_object_type"]:
        return TraceValidationResult(
            TraceValidationStatus.INVALID,
            ("trace_source_object_type_mismatch",),
            None,
            (),
        )
    expected_fields = {str(item) for item in registry["projection_fields"]}
    actual_fields = set(binding.projection)
    if expected_fields - actual_fields:
        return TraceValidationResult(
            TraceValidationStatus.INDETERMINATE,
            ("trace_projection_field_missing",),
            None,
            (),
        )
    if actual_fields - expected_fields:
        return TraceValidationResult(
            TraceValidationStatus.INVALID,
            ("trace_projection_field_extra",),
            None,
            (),
        )
    excluded_fields = {str(item) for item in registry["excluded_fields"]}
    if actual_fields & excluded_fields:
        return TraceValidationResult(
            TraceValidationStatus.INVALID,
            ("trace_projection_field_excluded",),
            None,
            (),
        )
    if _contains_forbidden_field(binding.projection) is not None:
        return TraceValidationResult(
            TraceValidationStatus.INVALID,
            ("trace_projection_field_forbidden",),
            None,
            (),
        )
    try:
        expected_source_ref = compute_projection_source_ref(
            binding.source_object_type,
            binding.projection_schema,
            binding.projection,
        )
    except TraceContractError:
        return TraceValidationResult(
            TraceValidationStatus.INDETERMINATE,
            ("trace_source_identity_indeterminate",),
            None,
            (),
        )
    if binding.source_object_ref != expected_source_ref:
        return TraceValidationResult(
            TraceValidationStatus.INVALID,
            ("trace_source_object_ref_mismatch",),
            None,
            (),
        )
    try:
        expected_binding_ref = compute_binding_ref(binding)
    except TraceContractError:
        return TraceValidationResult(
            TraceValidationStatus.INDETERMINATE,
            ("trace_binding_digest_indeterminate",),
            None,
            (),
        )
    if binding.binding_ref != expected_binding_ref:
        return TraceValidationResult(
            TraceValidationStatus.INVALID,
            ("trace_binding_digest_mismatch",),
            None,
            (),
        )
    return TraceValidationResult(
        TraceValidationStatus.VALID,
        ("trace_source_binding_valid",),
        None,
        (),
    )


def _result(
    status: TraceValidationStatus,
    reason: str,
    trace: ProductAuthoritativeTrace | None,
) -> TraceValidationResult:
    return TraceValidationResult(
        status=status,
        reason_codes=(reason,),
        profile=(trace.profile if isinstance(trace, ProductAuthoritativeTrace) else None),
        event_types=(
            tuple(event.event_type for event in trace.events)
            if isinstance(trace, ProductAuthoritativeTrace)
            else ()
        ),
    )


def _expected_relations(
    relation_specs: tuple[Any, ...],
    source_binding: TraceSourceBinding,
) -> list[tuple[Mapping[str, Any], Any]]:
    expanded: list[tuple[Mapping[str, Any], Any]] = []
    for spec in relation_specs:
        if not isinstance(spec, Mapping):
            raise TraceContractError("relation profile entry is invalid")
        raw_value = _extract_path(
            source_binding.projection,
            str(spec["source_assertion_path"]),
        )
        mode = spec["value_mode"]
        if mode == "SCALAR":
            values = (raw_value,)
        elif mode == "EACH_VALUE":
            if not isinstance(raw_value, tuple):
                raise TraceContractError("EACH_VALUE relation source is not an array")
            values = raw_value
        else:
            raise TraceContractError(f"unsupported relation value mode: {mode}")
        expanded.extend((spec, value) for value in values)
    return expanded


def validate_product_authoritative_trace(trace: object) -> TraceValidationResult:
    """Validate one explicit product envelope using only the frozen registry."""

    if not isinstance(trace, ProductAuthoritativeTrace):
        return _result(TraceValidationStatus.INVALID, "trace_contract_type_invalid", None)
    if trace.schema_version != EXPECTED_TRACE_SCHEMA_VERSION:
        return _result(TraceValidationStatus.INVALID, "trace_schema_version_invalid", trace)
    if trace.source != EXPECTED_TRACE_SOURCE:
        return _result(TraceValidationStatus.INVALID, "trace_source_invalid", trace)
    try:
        profile_task = PROFILE_REGISTRY[trace.profile]
    except KeyError:
        return _result(TraceValidationStatus.INDETERMINATE, "trace_profile_unknown", trace)
    if trace.completeness_status != EXPECTED_COMPLETENESS_STATUS:
        return _result(
            TraceValidationStatus.INDETERMINATE,
            "trace_completeness_not_declared",
            trace,
        )
    if not trace.trace_ref:
        return _result(TraceValidationStatus.INDETERMINATE, "trace_ref_missing", trace)

    expected_events = profile_task["events"]
    if len(trace.events) < len(expected_events):
        return _result(TraceValidationStatus.INDETERMINATE, "trace_event_missing", trace)
    if len(trace.events) > len(expected_events):
        return _result(TraceValidationStatus.INVALID, "trace_event_extra", trace)
    if tuple(event.sequence_no for event in trace.events) != tuple(
        range(1, len(expected_events) + 1)
    ):
        return _result(TraceValidationStatus.INVALID, "trace_event_sequence_invalid", trace)

    binding_refs = tuple(binding.binding_ref for binding in trace.source_bindings)
    if any(not ref for ref in binding_refs):
        return _result(
            TraceValidationStatus.INDETERMINATE,
            "trace_binding_ref_missing",
            trace,
        )
    if len(set(binding_refs)) != len(binding_refs):
        return _result(TraceValidationStatus.INVALID, "trace_binding_ref_duplicate", trace)
    binding_by_ref = {binding.binding_ref: binding for binding in trace.source_bindings}
    referenced_binding_refs: set[str] = set()
    event_by_identity: dict[tuple[str, str, str], ProductTraceEvent] = {}
    binding_for_event: dict[int, TraceSourceBinding] = {}
    alias_refs: dict[str, str] = {}

    for event, expected in zip(trace.events, expected_events):
        for field_name in ("event_type", "entity_type", "entity_role"):
            if getattr(event, field_name) != expected[field_name]:
                return _result(
                    TraceValidationStatus.INVALID,
                    f"trace_event_{field_name}_mismatch",
                    trace,
                )
        if not event.source_binding_ref:
            return _result(
                TraceValidationStatus.INDETERMINATE,
                "trace_event_binding_ref_missing",
                trace,
            )
        binding = binding_by_ref.get(event.source_binding_ref)
        if binding is None:
            return _result(
                TraceValidationStatus.INDETERMINATE,
                "trace_event_binding_unresolved",
                trace,
            )
        referenced_binding_refs.add(event.source_binding_ref)
        binding_for_event[event.sequence_no] = binding
        if binding.projection_schema != expected["projection_schema"]:
            return _result(
                TraceValidationStatus.INVALID,
                "trace_event_projection_schema_mismatch",
                trace,
            )
        try:
            registry = _lookup_projection_schema(binding.projection_schema)
        except TraceContractError:
            return _result(
                TraceValidationStatus.INDETERMINATE,
                "trace_projection_schema_unknown",
                trace,
            )
        if binding.source_object_type != registry["source_object_type"]:
            return _result(
                TraceValidationStatus.INVALID,
                "trace_source_object_type_mismatch",
                trace,
            )
        expected_fields = {str(item) for item in registry["projection_fields"]}
        actual_fields = set(binding.projection)
        if expected_fields - actual_fields:
            return _result(
                TraceValidationStatus.INDETERMINATE,
                "trace_projection_field_missing",
                trace,
            )
        if actual_fields - expected_fields:
            return _result(
                TraceValidationStatus.INVALID,
                "trace_projection_field_extra",
                trace,
            )
        excluded_fields = {str(item) for item in registry["excluded_fields"]}
        if actual_fields & excluded_fields:
            return _result(
                TraceValidationStatus.INVALID,
                "trace_projection_field_excluded",
                trace,
            )
        if _contains_forbidden_field(binding.projection) is not None:
            return _result(
                TraceValidationStatus.INVALID,
                "trace_projection_field_forbidden",
                trace,
            )
        try:
            expected_source_ref = compute_projection_source_ref(
                binding.source_object_type,
                binding.projection_schema,
                binding.projection,
            )
        except TraceContractError:
            return _result(
                TraceValidationStatus.INDETERMINATE,
                "trace_source_identity_indeterminate",
                trace,
            )
        if binding.source_object_ref != expected_source_ref:
            return _result(
                TraceValidationStatus.INVALID,
                "trace_source_object_ref_mismatch",
                trace,
            )
        try:
            expected_binding_ref = compute_binding_ref(binding)
        except TraceContractError:
            return _result(
                TraceValidationStatus.INDETERMINATE,
                "trace_binding_digest_indeterminate",
                trace,
            )
        if binding.binding_ref != expected_binding_ref:
            return _result(
                TraceValidationStatus.INVALID,
                "trace_binding_digest_mismatch",
                trace,
            )
        try:
            expected_entity_ref = render_entity_ref(
                binding,
                str(expected["entity_ref_template"]),
            )
        except TraceContractError:
            return _result(
                TraceValidationStatus.INDETERMINATE,
                "trace_entity_ref_indeterminate",
                trace,
            )
        if event.entity_ref != expected_entity_ref:
            return _result(
                TraceValidationStatus.INVALID,
                "trace_entity_ref_mismatch",
                trace,
            )
        identity = (event.entity_type, event.entity_role, event.entity_ref)
        if identity in event_by_identity:
            return _result(
                TraceValidationStatus.INVALID,
                "trace_entity_identity_duplicate",
                trace,
            )
        event_by_identity[identity] = event
        alias_group = expected.get("binding_alias_group")
        if alias_group is not None:
            previous = alias_refs.setdefault(str(alias_group), event.source_binding_ref)
            if previous != event.source_binding_ref:
                return _result(
                    TraceValidationStatus.INVALID,
                    "trace_binding_alias_mismatch",
                    trace,
                )

        value_paths = expected["value_paths"]
        for output_name, path_name in (
            ("decision", "decision_path"),
            ("status", "status_path"),
        ):
            path = value_paths[path_name]
            if path is None:
                expected_value = None
            else:
                try:
                    expected_value = _extract_path(binding.projection, str(path))
                except TraceContractError:
                    return _result(
                        TraceValidationStatus.INDETERMINATE,
                        f"trace_event_{output_name}_path_missing",
                        trace,
                    )
            if getattr(event, output_name) != expected_value:
                return _result(
                    TraceValidationStatus.INVALID,
                    f"trace_event_{output_name}_mismatch",
                    trace,
                )
        reason_path = value_paths["reason_codes_path"]
        if reason_path is None:
            expected_reasons: tuple[str, ...] = ()
        else:
            try:
                raw_reasons = _extract_path(binding.projection, str(reason_path))
            except TraceContractError:
                return _result(
                    TraceValidationStatus.INDETERMINATE,
                    "trace_event_reason_codes_path_missing",
                    trace,
                )
            if not isinstance(raw_reasons, tuple) or any(
                not isinstance(item, str) for item in raw_reasons
            ):
                return _result(
                    TraceValidationStatus.INDETERMINATE,
                    "trace_event_reason_codes_not_array",
                    trace,
                )
            expected_reasons = tuple(raw_reasons)
        if event.reason_codes != expected_reasons:
            return _result(
                TraceValidationStatus.INVALID,
                "trace_event_reason_codes_mismatch",
                trace,
            )

    if set(binding_by_ref) - referenced_binding_refs:
        return _result(TraceValidationStatus.INVALID, "trace_binding_unreferenced", trace)

    for event, expected in zip(trace.events, expected_events):
        source_binding = binding_for_event[event.sequence_no]
        try:
            relation_specs = _expected_relations(expected["relations"], source_binding)
        except TraceContractError:
            return _result(
                TraceValidationStatus.INDETERMINATE,
                "trace_relation_source_indeterminate",
                trace,
            )
        if len(event.relations) != len(relation_specs):
            return _result(
                TraceValidationStatus.INVALID,
                "trace_relation_count_mismatch",
                trace,
            )
        for actual_relation, (spec, value) in zip(event.relations, relation_specs):
            if actual_relation.relation_type != spec["relation_type"]:
                return _result(
                    TraceValidationStatus.INVALID,
                    "trace_relation_type_mismatch",
                    trace,
                )
            if actual_relation.target_entity_type != spec["target_entity_type"]:
                return _result(
                    TraceValidationStatus.INVALID,
                    "trace_relation_target_type_mismatch",
                    trace,
                )
            if actual_relation.target_entity_role != spec["target_entity_role"]:
                return _result(
                    TraceValidationStatus.INVALID,
                    "trace_relation_target_role_mismatch",
                    trace,
                )
            try:
                expected_target_ref = _render_template(
                    str(spec["target_entity_ref_template"]),
                    source_binding.projection,
                    value=value,
                )
            except TraceContractError:
                return _result(
                    TraceValidationStatus.INDETERMINATE,
                    "trace_relation_target_ref_indeterminate",
                    trace,
                )
            if actual_relation.target_entity_ref != expected_target_ref:
                return _result(
                    TraceValidationStatus.INVALID,
                    "trace_relation_target_ref_mismatch",
                    trace,
                )
            target_identity = (
                actual_relation.target_entity_type,
                actual_relation.target_entity_role,
                actual_relation.target_entity_ref,
            )
            target_event = event_by_identity.get(target_identity)
            if target_event is None:
                return _result(
                    TraceValidationStatus.INVALID,
                    "trace_relation_target_unresolved",
                    trace,
                )
            if actual_relation.target_resolved is False:
                return _result(
                    TraceValidationStatus.INVALID,
                    "trace_relation_declared_unresolved",
                    trace,
                )
            target_binding = binding_for_event[target_event.sequence_no]
            expected_assertions = spec["target_binding_assertions"]
            if len(actual_relation.target_binding_assertions) != len(expected_assertions):
                return _result(
                    TraceValidationStatus.INVALID,
                    "trace_relation_assertion_count_mismatch",
                    trace,
                )
            for actual_assertion, expected_assertion in zip(
                actual_relation.target_binding_assertions,
                expected_assertions,
            ):
                if actual_assertion.source_path != expected_assertion["source_path"]:
                    return _result(
                        TraceValidationStatus.INVALID,
                        "trace_relation_assertion_source_path_mismatch",
                        trace,
                    )
                if actual_assertion.target_path != expected_assertion["target_path"]:
                    return _result(
                        TraceValidationStatus.INVALID,
                        "trace_relation_assertion_target_path_mismatch",
                        trace,
                    )
                try:
                    source_value = _extract_path(
                        source_binding.projection,
                        actual_assertion.source_path,
                    )
                    target_value = _extract_path(
                        target_binding.projection,
                        actual_assertion.target_path,
                    )
                except TraceContractError:
                    return _result(
                        TraceValidationStatus.INDETERMINATE,
                        "trace_relation_assertion_path_missing",
                        trace,
                    )
                if source_value != target_value:
                    return _result(
                        TraceValidationStatus.INVALID,
                        "trace_relation_binding_assertion_mismatch",
                        trace,
                    )
                if (
                    actual_assertion.source_value is not None
                    and actual_assertion.source_value != source_value
                ):
                    return _result(
                        TraceValidationStatus.INVALID,
                        "trace_relation_assertion_source_value_mismatch",
                        trace,
                    )
                if (
                    actual_assertion.target_value is not None
                    and actual_assertion.target_value != target_value
                ):
                    return _result(
                        TraceValidationStatus.INVALID,
                        "trace_relation_assertion_target_value_mismatch",
                        trace,
                    )
                if actual_assertion.equal is not None and actual_assertion.equal is not True:
                    return _result(
                        TraceValidationStatus.INVALID,
                        "trace_relation_assertion_equal_mismatch",
                        trace,
                    )

    return TraceValidationResult(
        status=TraceValidationStatus.VALID,
        reason_codes=("product_authoritative_trace_valid",),
        profile=trace.profile,
        event_types=tuple(event.event_type for event in trace.events),
    )


def trace_binding_from_mapping(value: Mapping[str, Any]) -> TraceSourceBinding:
    return TraceSourceBinding(
        binding_ref=str(value["binding_ref"]),
        source_object_type=str(value["source_object_type"]),
        source_object_ref=str(value["source_object_ref"]),
        projection_schema=str(value["projection_schema"]),
        projection=value["projection"],
    )


def trace_relation_from_mapping(value: Mapping[str, Any]) -> TraceRelation:
    assertions = tuple(
        TraceBindingAssertion(
            source_path=str(item["source_path"]),
            target_path=str(item["target_path"]),
            source_value=item.get("source_value"),
            target_value=item.get("target_value"),
            equal=item.get("equal"),
        )
        for item in value.get("target_binding_assertions", ())
    )
    return TraceRelation(
        relation_type=str(value["relation_type"]),
        target_entity_type=str(value["target_entity_type"]),
        target_entity_role=str(value["target_entity_role"]),
        target_entity_ref=str(value["target_entity_ref"]),
        target_binding_assertions=assertions,
        target_resolved=value.get("target_resolved"),
    )


def trace_event_from_mapping(value: Mapping[str, Any]) -> ProductTraceEvent:
    return ProductTraceEvent(
        sequence_no=int(value["sequence_no"]),
        event_type=str(value["event_type"]),
        entity_type=str(value["entity_type"]),
        entity_role=str(value["entity_role"]),
        entity_ref=str(value["entity_ref"]),
        source_binding_ref=str(value["source_binding_ref"]),
        decision=value.get("decision"),
        status=value.get("status"),
        reason_codes=tuple(value.get("reason_codes", ())),
        relations=tuple(
            trace_relation_from_mapping(item) for item in value.get("relations", ())
        ),
    )


def trace_from_mapping(
    value: Mapping[str, Any],
    *,
    schema_version: str = EXPECTED_TRACE_SCHEMA_VERSION,
    source: str = EXPECTED_TRACE_SOURCE,
    completeness_status: str = EXPECTED_COMPLETENESS_STATUS,
    trace_ref: str | None = None,
) -> ProductAuthoritativeTrace:
    profile = str(value["profile"])
    return ProductAuthoritativeTrace(
        schema_version=schema_version,
        source=source,
        profile=profile,
        trace_ref=trace_ref or f"ProductAuthoritativeTrace:{profile}",
        completeness_status=completeness_status,
        reason_codes=tuple(value.get("reason_codes", ())),
        events=tuple(trace_event_from_mapping(item) for item in value.get("events", ())),
        source_bindings=tuple(
            trace_binding_from_mapping(item)
            for item in value.get("source_bindings", value.get("bindings", ()))
        ),
    )


__all__ = [
    "ACCEPTED_FORMULA_REGISTRY_SHA256",
    "ACCEPTED_PROFILES_SHA256",
    "ACCEPTED_PROJECTION_REGISTRY_SHA256",
    "ACCEPTED_RUNTIME_CONTRACT_SHA256",
    "CANONICAL_DECIMAL_CONTRACT",
    "EXPECTED_COMPLETENESS_STATUS",
    "EXPECTED_TRACE_SCHEMA_VERSION",
    "EXPECTED_TRACE_SOURCE",
    "FORMULA_REGISTRY",
    "FORBIDDEN_PROJECTION_FIELDS",
    "FrozenDict",
    "PROFILE_REGISTRY",
    "PROFILE_TASKS",
    "PROJECTION_REGISTRY",
    "ProductAuthoritativeTrace",
    "ProductTraceEvent",
    "REFERENCE_MODEL",
    "TraceBindingAssertion",
    "TraceContractError",
    "TraceRelation",
    "TraceSourceBinding",
    "TraceValidationResult",
    "TraceValidationStatus",
    "canonical_json_bytes",
    "canonical_primitive",
    "canonical_sha256",
    "compute_binding_ref",
    "compute_projection_source_ref",
    "render_entity_ref",
    "runtime_contract_primitive",
    "runtime_registry_hashes",
    "trace_binding_from_mapping",
    "trace_event_from_mapping",
    "trace_from_mapping",
    "trace_relation_from_mapping",
    "validate_product_authoritative_trace",
    "validate_trace_source_binding",
]
'''

source = SOURCE_TEMPLATE.replace("__EMBEDDED_JSON_REPR__", repr(embedded_json))
OUTPUT.write_text(source, encoding="utf-8")
print(f"output={OUTPUT.relative_to(ROOT).as_posix()}")
print(f"bytes={OUTPUT.stat().st_size}")

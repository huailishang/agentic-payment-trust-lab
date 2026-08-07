"""Pure measurement contracts and strict validation for product traces.

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

    def __post_init__(self) -> None:
        assertions = tuple(self.target_binding_assertions)
        if any(not isinstance(item, TraceBindingAssertion) for item in assertions):
            raise TraceContractError("target binding assertions must use TraceBindingAssertion")
        object.__setattr__(self, "target_binding_assertions", assertions)


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

    def __post_init__(self) -> None:
        reason_codes = tuple(self.reason_codes)
        relations = tuple(self.relations)
        if any(not isinstance(item, str) for item in reason_codes):
            raise TraceContractError("event reason codes must be strings")
        if any(not isinstance(item, TraceRelation) for item in relations):
            raise TraceContractError("event relations must use TraceRelation")
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "relations", relations)


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

    def __post_init__(self) -> None:
        reason_codes = tuple(self.reason_codes)
        events = tuple(self.events)
        source_bindings = tuple(self.source_bindings)
        if any(not isinstance(item, str) for item in reason_codes):
            raise TraceContractError("trace reason codes must be strings")
        if any(not isinstance(item, ProductTraceEvent) for item in events):
            raise TraceContractError("trace events must use ProductTraceEvent")
        if any(not isinstance(item, TraceSourceBinding) for item in source_bindings):
            raise TraceContractError("trace source bindings must use TraceSourceBinding")
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "events", events)
        object.__setattr__(self, "source_bindings", source_bindings)


@dataclass(frozen=True)
class TraceValidationResult:
    status: TraceValidationStatus
    reason_codes: tuple[str, ...]
    profile: str | None
    event_types: tuple[str, ...]

    def __post_init__(self) -> None:
        reason_codes = tuple(self.reason_codes)
        event_types = tuple(self.event_types)
        if any(not isinstance(item, str) for item in reason_codes):
            raise TraceContractError("validation reason codes must be strings")
        if any(not isinstance(item, str) for item in event_types):
            raise TraceContractError("validation event types must be strings")
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "event_types", event_types)


EXPECTED_TRACE_SCHEMA_VERSION = "product-authoritative-trace/v1"
EXPECTED_TRACE_SOURCE = "PRODUCT_OBSERVED"
EXPECTED_COMPLETENESS_STATUS = "COMPLETE"

_RUNTIME_CONTRACT_JSON = '{"canonical_decimal":{"examples":{"-0":"0","0":"0","0.10":"0.1","1":"1","1.00":"1","1000.000":"1000"},"examples_sha256":"7f50c2d41d35aad95c173ec002bdd928bff69c644195cad78485bcd1a5674751","float_allowed":false,"non_finite_allowed":false},"forbidden_projection_fields":["card_number","pan","cvv","payment_instrument_plaintext","wallet_private_key","credential","token","cookie","raw_page_text","raw_prompt","user_input_fulltext","memory_address","file_path","current_time","random_value"],"projection_identity_formula_registry":{"PROJECTION_HASH_IDENTITY_V1":{"canonical_json":{"allow_nan":false,"encoding":"UTF-8","ensure_ascii":false,"separators":[",",":"],"sort_keys":true},"digest_encoding":"lowercase-hex-64","formula_id":"PROJECTION_HASH_IDENTITY_V1","hash_algorithm":"SHA-256","mode":"PROJECTION_HASH_IDENTITY","payload_excludes":["binding_ref","source_object_ref"],"payload_fields":["projection_schema","projection"],"prefix_template":"{source_object_type}:projection-sha256:","source_object_type_in_payload":false,"source_object_type_in_prefix":true}},"projection_registry":{"attack-overlay-result-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"AttackOverlayResult:{projection.attack_id}","excluded_fields":[],"field_extractions":{"applied_paths":{"path":"applied_paths","transform":"tuple.to_list"},"attack_attempted":{"path":"attack_attempted","transform":"DIRECT"},"attack_id":{"path":"attack_id","transform":"DIRECT"},"baseline_decision":{"path":"baseline_decision","transform":"Enum.value"},"blocked_override_paths":{"path":"blocked_override_paths","transform":"tuple.to_list"},"decision_drift":{"path":"decision_drift","transform":"DIRECT"},"defended_decision":{"path":"defended_decision","transform":"Enum.value"},"lineage_effective_source_types":{"path":"lineage_facts[].effective_source_types[]","transform":"tuple.flatten_enum_values"},"lineage_fact_refs":{"path":"lineage_facts[].fact_ref","transform":"tuple.map"},"lineage_reason_codes":{"path":"lineage_reason_codes","transform":"tuple.to_list"},"lineage_status":{"path":"lineage_status","transform":"Enum.value"},"policy_version":{"path":"policy_version","transform":"DIRECT"},"reason_codes":{"path":"reason_codes","transform":"tuple.to_list"},"source_type":{"path":"source_type","transform":"Enum.value"},"trusted_state_changed":{"path":"trusted_state_changed","transform":"DIRECT"}},"projection_fields":["attack_id","source_type","baseline_decision","defended_decision","attack_attempted","applied_paths","blocked_override_paths","trusted_state_changed","reason_codes","policy_version","decision_drift","lineage_status","lineage_reason_codes","lineage_fact_refs","lineage_effective_source_types"],"source_class":"AttackOverlayResult","source_identity":{"mode":"NATIVE_TEMPLATE","template":"AttackOverlayResult:{attack_id}"},"source_module":"agentic_payment_experiment.attack_overlay","source_object_type":"AttackOverlayResult"},"fulfillment-record-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"FulfillmentRecord:{projection.fulfillment_id}","excluded_fields":[],"field_extractions":{"failure_code":{"path":"failure_code","transform":"DIRECT"},"fulfillment_id":{"path":"fulfillment_id","transform":"DIRECT"},"order_id":{"path":"order_id","transform":"DIRECT"},"reason_codes":{"path":"failure_code","transform":"optional.singleton_tuple"},"status":{"path":"status","transform":"Enum.value"}},"projection_fields":["fulfillment_id","order_id","status","failure_code","reason_codes"],"source_class":"FulfillmentRecord","source_identity":{"mode":"NATIVE_TEMPLATE","template":"FulfillmentRecord:{fulfillment_id}"},"source_module":"agentic_payment_experiment.models","source_object_type":"FulfillmentRecord"},"governed-action-binding-fact-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"GovernedActionBindingFact:binding:{binding_digest}","excluded_fields":[],"field_extractions":{"action_id":{"path":"action_id","transform":"DIRECT"},"checked_action_type":{"path":"checked_action_type","transform":"DIRECT"},"checked_order_ref":{"path":"checked_order_ref","transform":"DIRECT"},"checked_payment_ref":{"path":"checked_payment_ref","transform":"DIRECT"},"checked_request_ref":{"path":"checked_request_ref","transform":"DIRECT"},"reason_codes":{"path":"reason_codes","transform":"tuple.to_list"},"status":{"path":"status","transform":"Enum.value"}},"projection_fields":["status","action_id","reason_codes","checked_action_type","checked_order_ref","checked_request_ref","checked_payment_ref"],"source_class":"GovernedActionBindingFact","source_identity":{"canonical_json":{"allow_nan":false,"encoding":"UTF-8","ensure_ascii":false,"separators":[",",":"],"sort_keys":true},"digest_encoding":"lowercase-hex-64","formula_id":"PROJECTION_HASH_IDENTITY_V1","hash_algorithm":"SHA-256","mode":"PROJECTION_HASH_IDENTITY","payload_fields":["projection_schema","projection"],"prefix_template":"{source_object_type}:projection-sha256:"},"source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_type":"GovernedActionBindingFact"},"governed-payment-action-missing-id-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"GovernedPaymentAction:binding:{binding_digest}","excluded_fields":[],"field_extractions":{"action_id":{"path":"action_id","transform":"DIRECT"},"action_type":{"path":"action_type","transform":"Enum.value"},"agent_ref":{"path":"agent_ref","transform":"DIRECT"},"authority_ref":{"path":"authority_ref","transform":"DIRECT"},"authority_version":{"path":"authority_version","transform":"DIRECT"},"executor_ref":{"path":"executor_ref","transform":"DIRECT"},"occurred_at":{"path":"occurred_at","transform":"datetime.isoformat"},"order_ref":{"path":"order_ref","transform":"DIRECT"},"order_version":{"path":"order_version","transform":"DIRECT"},"payment_ref":{"path":"payment_ref","transform":"DIRECT"},"request_ref":{"path":"request_ref","transform":"DIRECT"},"reversibility":{"path":"reversibility","transform":"Enum.value"},"side_effect_class":{"path":"side_effect_class","transform":"Enum.value"},"source_refs":{"path":"source_refs","transform":"tuple.to_list"}},"projection_fields":["action_id","action_type","agent_ref","executor_ref","authority_ref","authority_version","order_ref","order_version","request_ref","payment_ref","source_refs","side_effect_class","reversibility","occurred_at"],"source_class":"GovernedPaymentAction","source_identity":{"canonical_json":{"allow_nan":false,"encoding":"UTF-8","ensure_ascii":false,"separators":[",",":"],"sort_keys":true},"digest_encoding":"lowercase-hex-64","formula_id":"PROJECTION_HASH_IDENTITY_V1","hash_algorithm":"SHA-256","mode":"PROJECTION_HASH_IDENTITY","payload_fields":["projection_schema","projection"],"prefix_template":"{source_object_type}:projection-sha256:"},"source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_type":"GovernedPaymentAction"},"governed-payment-action-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"GovernedPaymentAction:{projection.action_id}","excluded_fields":[],"field_extractions":{"action_id":{"path":"action_id","transform":"DIRECT"},"action_type":{"path":"action_type","transform":"Enum.value"},"agent_ref":{"path":"agent_ref","transform":"DIRECT"},"authority_ref":{"path":"authority_ref","transform":"DIRECT"},"authority_version":{"path":"authority_version","transform":"DIRECT"},"executor_ref":{"path":"executor_ref","transform":"DIRECT"},"occurred_at":{"path":"occurred_at","transform":"datetime.isoformat"},"order_ref":{"path":"order_ref","transform":"DIRECT"},"order_version":{"path":"order_version","transform":"DIRECT"},"payment_ref":{"path":"payment_ref","transform":"DIRECT"},"request_ref":{"path":"request_ref","transform":"DIRECT"},"reversibility":{"path":"reversibility","transform":"Enum.value"},"side_effect_class":{"path":"side_effect_class","transform":"Enum.value"},"source_refs":{"path":"source_refs","transform":"tuple.to_list"}},"projection_fields":["action_id","action_type","agent_ref","executor_ref","authority_ref","authority_version","order_ref","order_version","request_ref","payment_ref","source_refs","side_effect_class","reversibility","occurred_at"],"source_class":"GovernedPaymentAction","source_identity":{"mode":"NATIVE_TEMPLATE","template":"GovernedPaymentAction:{action_id}"},"source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_type":"GovernedPaymentAction"},"intent-mandate-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"IntentMandate:{projection.mandate_id}","excluded_fields":[],"field_extractions":{"authority_version":{"path":"authority_version","transform":"DIRECT"},"mandate_id":{"path":"mandate_id","transform":"DIRECT"}},"projection_fields":["mandate_id","authority_version"],"source_class":"IntentMandate","source_identity":{"mode":"NATIVE_TEMPLATE","template":"IntentMandate:{mandate_id}:{authority_version}"},"source_module":"agentic_payment_experiment.models","source_object_type":"IntentMandate"},"known-payment-attempt-preflight-fact-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"KnownPaymentAttemptPreflightFact:binding:{binding_digest}","excluded_fields":[],"field_extractions":{"blocking_request_refs":{"path":"blocking_request_refs","transform":"tuple.to_list"},"current_request_ref":{"path":"current_request_ref","transform":"DIRECT"},"limitations":{"path":"limitations","transform":"tuple.to_list"},"reason_codes":{"path":"reason_codes","transform":"tuple.to_list"},"related_attempt_refs":{"path":"related_attempt_refs","transform":"tuple.to_list"},"status":{"path":"status","transform":"Enum.value"}},"projection_fields":["status","reason_codes","current_request_ref","related_attempt_refs","blocking_request_refs","limitations"],"source_class":"KnownPaymentAttemptPreflightFact","source_identity":{"canonical_json":{"allow_nan":false,"encoding":"UTF-8","ensure_ascii":false,"separators":[",",":"],"sort_keys":true},"digest_encoding":"lowercase-hex-64","formula_id":"PROJECTION_HASH_IDENTITY_V1","hash_algorithm":"SHA-256","mode":"PROJECTION_HASH_IDENTITY","payload_fields":["projection_schema","projection"],"prefix_template":"{source_object_type}:projection-sha256:"},"source_module":"agentic_payment_experiment.trusted_execution.known_payment_attempt","source_object_type":"KnownPaymentAttemptPreflightFact"},"order-snapshot-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"Order:{projection.order_id}","excluded_fields":[],"field_extractions":{"authority_version_ref":{"path":"authority_version_ref","transform":"DIRECT"},"currency":{"path":"currency","transform":"DIRECT"},"mandate_ref":{"path":"mandate_ref","transform":"DIRECT"},"merchant":{"path":"merchant","transform":"DIRECT"},"order_id":{"path":"order_id","transform":"DIRECT"},"order_version":{"path":"order_version","transform":"DIRECT"},"payee":{"path":"payee","transform":"DIRECT"},"total_amount":{"path":"total_amount","transform":"Decimal.canonical_string"}},"projection_fields":["order_id","order_version","mandate_ref","authority_version_ref","total_amount","currency","merchant","payee"],"source_class":"Order","source_identity":{"mode":"NATIVE_TEMPLATE","template":"Order:{order_id}:{order_version}"},"source_module":"agentic_payment_experiment.models","source_object_type":"Order"},"payment-execution-record-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"PaymentExecutionRecord:{projection.payment_id}","excluded_fields":[],"field_extractions":{"agent_ref":{"path":"agent_ref","transform":"DIRECT"},"amount":{"path":"amount","transform":"Decimal.canonical_string"},"authority_ref":{"path":"authority_ref","transform":"DIRECT"},"currency":{"path":"currency","transform":"DIRECT"},"order_id":{"path":"order_id","transform":"DIRECT"},"payee":{"path":"payee","transform":"DIRECT"},"payment_id":{"path":"payment_id","transform":"DIRECT"},"request_id":{"path":"request_id","transform":"DIRECT"},"status":{"path":"status","transform":"Enum.value"},"transaction_object_ref":{"path":"transaction_object_ref","transform":"DIRECT"}},"projection_fields":["payment_id","request_id","order_id","status","amount","currency","authority_ref","agent_ref","transaction_object_ref","payee"],"source_class":"PaymentExecutionRecord","source_identity":{"mode":"NATIVE_TEMPLATE","template":"PaymentExecutionRecord:{payment_id}"},"source_module":"agentic_payment_experiment.models","source_object_type":"PaymentExecutionRecord"},"payment-recovery-result-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"PaymentRecoveryResult:binding:{binding_digest}","excluded_fields":[],"field_extractions":{"effective_status":{"path":"effective_status","transform":"Enum.value"},"evidence_paths":{"path":"evidence[].field_path","transform":"tuple.map"},"initial_status":{"path":"initial_status","transform":"Enum.value"},"issue_codes":{"path":"issues[].code","transform":"tuple.map"},"next_action":{"path":"next_action","transform":"DIRECT"},"observed_status":{"path":"observed_status","transform":"Enum.value"},"recovery_status":{"path":"recovery_status","transform":"Enum.value"},"retry_allowed":{"path":"retry_allowed","transform":"DIRECT"},"rule_version":{"path":"rule_version","transform":"DIRECT"}},"projection_fields":["initial_status","observed_status","effective_status","recovery_status","next_action","retry_allowed","issue_codes","evidence_paths","rule_version"],"source_class":"PaymentRecoveryResult","source_identity":{"canonical_json":{"allow_nan":false,"encoding":"UTF-8","ensure_ascii":false,"separators":[",",":"],"sort_keys":true},"digest_encoding":"lowercase-hex-64","formula_id":"PROJECTION_HASH_IDENTITY_V1","hash_algorithm":"SHA-256","mode":"PROJECTION_HASH_IDENTITY","payload_fields":["projection_schema","projection"],"prefix_template":"{source_object_type}:projection-sha256:"},"source_module":"agentic_payment_experiment.models","source_object_type":"PaymentRecoveryResult"},"payment-status-conflict-fact-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"PaymentStatusConflictFact:binding:{binding_digest}","excluded_fields":[],"field_extractions":{"async_observed_at":{"path":"async_observed_at","transform":"datetime.isoformat_or_null"},"async_status":{"path":"async_status","transform":"Enum.value"},"business_success_confirmed":{"path":"business_success_confirmed","transform":"DIRECT"},"effective_status":{"path":"effective_status","transform":"Enum.value"},"effective_status_terminal":{"path":"effective_status_terminal","transform":"DIRECT"},"fulfillment_confirmed":{"path":"fulfillment_confirmed","transform":"DIRECT"},"initial_status":{"path":"initial_status","transform":"Enum.value"},"legal_finality_confirmed":{"path":"legal_finality_confirmed","transform":"DIRECT"},"query_observed_at":{"path":"query_observed_at","transform":"datetime.isoformat_or_null"},"query_status":{"path":"query_status","transform":"Enum.value"},"reason_codes":{"path":"reason_codes","transform":"tuple.to_list"},"reconciliation_confirmed":{"path":"reconciliation_confirmed","transform":"DIRECT"},"resolution":{"path":"resolution","transform":"Enum.value"},"settlement_confirmed":{"path":"settlement_confirmed","transform":"DIRECT"},"user_task_success_confirmed":{"path":"user_task_success_confirmed","transform":"DIRECT"}},"projection_fields":["resolution","initial_status","query_status","query_observed_at","async_status","async_observed_at","effective_status","effective_status_terminal","reason_codes","business_success_confirmed","fulfillment_confirmed","user_task_success_confirmed","reconciliation_confirmed","settlement_confirmed","legal_finality_confirmed"],"source_class":"PaymentStatusConflictFact","source_identity":{"canonical_json":{"allow_nan":false,"encoding":"UTF-8","ensure_ascii":false,"separators":[",",":"],"sort_keys":true},"digest_encoding":"lowercase-hex-64","formula_id":"PROJECTION_HASH_IDENTITY_V1","hash_algorithm":"SHA-256","mode":"PROJECTION_HASH_IDENTITY","payload_fields":["projection_schema","projection"],"prefix_template":"{source_object_type}:projection-sha256:"},"source_module":"agentic_payment_experiment.payment_status_conflict","source_object_type":"PaymentStatusConflictFact"},"runtime-gate-record-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"RuntimeGateRecord:binding:{binding_digest}","excluded_fields":[],"field_extractions":{"binding_reason_codes":{"path":"binding_reason_codes","transform":"tuple.to_list"},"binding_status":{"path":"binding_status","transform":"DIRECT"},"callback_count":{"path":"callback_count","transform":"DIRECT"},"callback_executed":{"path":"callback_executed","transform":"DIRECT"},"callback_result_ref":{"path":"callback_result_ref","transform":"DIRECT"},"context_policy_reason_codes":{"path":"context_policy_reason_codes","transform":"tuple.to_list"},"context_policy_status":{"path":"context_policy_status","transform":"DIRECT"},"final_decision":{"path":"final_decision","transform":"Enum.value"},"identity_reason_codes":{"path":"identity_reason_codes","transform":"tuple.to_list"},"identity_status":{"path":"identity_status","transform":"DIRECT"},"preliminary_decision":{"path":"preliminary_decision","transform":"Enum.value"},"reason_codes":{"path":"reason_codes","transform":"tuple.to_list"}},"projection_fields":["preliminary_decision","final_decision","binding_status","binding_reason_codes","identity_status","identity_reason_codes","context_policy_status","context_policy_reason_codes","callback_executed","callback_count","callback_result_ref","reason_codes"],"source_class":"RuntimeGateRecord","source_identity":{"canonical_json":{"allow_nan":false,"encoding":"UTF-8","ensure_ascii":false,"separators":[",",":"],"sort_keys":true},"digest_encoding":"lowercase-hex-64","formula_id":"PROJECTION_HASH_IDENTITY_V1","hash_algorithm":"SHA-256","mode":"PROJECTION_HASH_IDENTITY","payload_fields":["projection_schema","projection"],"prefix_template":"{source_object_type}:projection-sha256:"},"source_module":"agentic_payment_experiment.trusted_execution.replay","source_object_type":"RuntimeGateRecord"},"transaction-request-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"TransactionRequest:{projection.request_id}","excluded_fields":[],"field_extractions":{"agent_id":{"path":"agent_id","transform":"DIRECT"},"amount":{"path":"amount","transform":"Decimal.canonical_string"},"authority_ref":{"path":"authority_ref","transform":"DIRECT"},"authority_version_ref":{"path":"authority_version_ref","transform":"DIRECT"},"currency":{"path":"currency","transform":"DIRECT"},"merchant":{"path":"merchant","transform":"DIRECT"},"order_ref":{"path":"order_ref","transform":"DIRECT"},"payee":{"path":"payee","transform":"DIRECT"},"request_id":{"path":"request_id","transform":"DIRECT"}},"projection_fields":["request_id","order_ref","authority_ref","authority_version_ref","amount","currency","merchant","payee","agent_id"],"source_class":"TransactionRequest","source_identity":{"mode":"NATIVE_TEMPLATE","template":"TransactionRequest:{request_id}"},"source_module":"agentic_payment_experiment.models","source_object_type":"TransactionRequest"},"validation-result-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"ValidationResult:binding:{binding_digest}","excluded_fields":[],"field_extractions":{"decision":{"path":"decision","transform":"Enum.value"},"evidence_paths":{"path":"evidence[].field_path","transform":"tuple.map"},"issue_codes":{"path":"issues[].code","transform":"tuple.map"},"order_difference_paths":{"path":"order_differences[].field_path","transform":"tuple.map"},"rule_version":{"path":"rule_version","transform":"DIRECT"}},"projection_fields":["decision","issue_codes","evidence_paths","rule_version","order_difference_paths"],"source_class":"ValidationResult","source_identity":{"canonical_json":{"allow_nan":false,"encoding":"UTF-8","ensure_ascii":false,"separators":[",",":"],"sort_keys":true},"digest_encoding":"lowercase-hex-64","formula_id":"PROJECTION_HASH_IDENTITY_V1","hash_algorithm":"SHA-256","mode":"PROJECTION_HASH_IDENTITY","payload_fields":["projection_schema","projection"],"prefix_template":"{source_object_type}:projection-sha256:"},"source_module":"agentic_payment_experiment.models","source_object_type":"ValidationResult"},"webshop-buy-now-gate-outcome-result-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"WebShopBuyNowGateOutcome:binding:{binding_digest}","excluded_fields":["authoritative_trace"],"field_extractions":{"callback_count":{"path":"callback_count","transform":"DIRECT"},"callback_result_ref":{"path":"callback_result_ref","transform":"DIRECT"},"checkout_executed":{"path":"checkout_executed","transform":"DIRECT"},"decision":{"path":"decision","transform":"Enum.value"},"limitations":{"path":"limitations","transform":"tuple.to_list"},"reason_codes":{"path":"reason_codes","transform":"tuple.to_list"}},"projection_fields":["decision","checkout_executed","callback_count","callback_result_ref","reason_codes","limitations"],"source_class":"WebShopBuyNowGateOutcome","source_identity":{"canonical_json":{"allow_nan":false,"encoding":"UTF-8","ensure_ascii":false,"separators":[",",":"],"sort_keys":true},"digest_encoding":"lowercase-hex-64","formula_id":"PROJECTION_HASH_IDENTITY_V1","hash_algorithm":"SHA-256","mode":"PROJECTION_HASH_IDENTITY","payload_fields":["projection_schema","projection"],"prefix_template":"{source_object_type}:projection-sha256:"},"source_module":"agentic_payment_experiment.webshop_runtime_gate","source_object_type":"WebShopBuyNowGateOutcome"},"webshop-payment-fulfilment-outcome-result-trace/v2":{"binding_ref_mode":"EXACT_PROJECTION_DIGEST","entity_ref_template":"WebShopPaymentFulfilmentOutcome:binding:{binding_digest}","excluded_fields":["authoritative_trace"],"field_extractions":{"duplicate_payment_blocked":{"path":"duplicate_payment_blocked","transform":"DIRECT"},"effective_payment_status":{"path":"effective_payment.status","transform":"Enum.value_or_null"},"initial_payment_status":{"path":"initial_payment.status","transform":"Enum.value_or_null"},"lifecycle_fulfillment_status":{"path":"lifecycle.fulfillment_status","transform":"Enum.value_or_null"},"lifecycle_payment_status":{"path":"lifecycle.payment_status","transform":"Enum.value_or_null"},"lifecycle_remediation_status":{"path":"lifecycle.remediation.status","transform":"Enum.value_or_null"},"lifecycle_task_status":{"path":"lifecycle.task_status","transform":"Enum.value_or_null"},"limitations":{"path":"limitations","transform":"tuple.to_list"},"query_recovery_status":{"path":"query_recovery.recovery_status","transform":"Enum.value_or_null"},"ready":{"path":"ready","transform":"DIRECT"},"reason_codes":{"path":"reason_codes","transform":"tuple.to_list"},"retry_allowed":{"path":"retry_allowed","transform":"DIRECT"},"status_conflict_resolution":{"path":"status_conflict.resolution","transform":"Enum.value_or_null"}},"projection_fields":["ready","initial_payment_status","effective_payment_status","query_recovery_status","status_conflict_resolution","lifecycle_payment_status","lifecycle_fulfillment_status","lifecycle_task_status","lifecycle_remediation_status","retry_allowed","duplicate_payment_blocked","reason_codes","limitations"],"source_class":"WebShopPaymentFulfilmentOutcome","source_identity":{"canonical_json":{"allow_nan":false,"encoding":"UTF-8","ensure_ascii":false,"separators":[",",":"],"sort_keys":true},"digest_encoding":"lowercase-hex-64","formula_id":"PROJECTION_HASH_IDENTITY_V1","hash_algorithm":"SHA-256","mode":"PROJECTION_HASH_IDENTITY","payload_fields":["projection_schema","projection"],"prefix_template":"{source_object_type}:projection-sha256:"},"source_module":"agentic_payment_experiment.webshop_payment_sidecar","source_object_type":"WebShopPaymentFulfilmentOutcome"}},"reference_model":{"binding_ref":"exact projection commitment for every source object","duplicate_binding_ref_verdict":"INVALID","entity_ref":"profile entity identity generated by a closed typed template","evaluator_reconstruction_allowed":false,"event_binding_lookup":"ProductTraceEvent.source_binding_ref","external_cryptographic_authenticity_claimed":false,"hidden_resolver_allowed":false,"missing_binding_verdict":"INDETERMINATE","relation_target_entity_ref":"must equal an existing target event entity_ref","source_object_ref":"source object identity only","unreferenced_binding_verdict":"INVALID"},"tasks":[{"current_status":"NOT_AVAILABLE","entity_roles":["AUTHORITY","AUTHORIZED_ORDER_SNAPSHOT","CURRENT_ORDER_SNAPSHOT","CURRENT_REQUEST","GOVERNED_ACTION","CURRENT_PAYMENT_CANDIDATE","ACTION_BINDING_FACT","RUNTIME_GATE_OBSERVATION","PAYMENT_EXECUTION_OUTCOME","FULFILMENT_OUTCOME","FINAL_OUTCOME"],"events":[{"binding_alias_group":null,"entity_ref_template":"IntentMandate:{projection.mandate_id}","entity_role":"AUTHORITY","entity_type":"IntentMandate","event_type":"AUTHORITY_RECORDED","projection_schema":"intent-mandate-trace/v2","relations":[],"sequence_no":1,"source_binding_ref_required":true,"source_class":"IntentMandate","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"IntentMandate","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":"AUTHORIZED_CURRENT_ORDER_SHARED_BINDING","entity_ref_template":"Order:{projection.order_id}","entity_role":"AUTHORIZED_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":2,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":"AUTHORIZED_CURRENT_ORDER_SHARED_BINDING","entity_ref_template":"Order:{projection.order_id}","entity_role":"CURRENT_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":3,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"TransactionRequest:{projection.request_id}","entity_role":"CURRENT_REQUEST","entity_type":"TransactionRequest","event_type":"REQUEST_RECORDED","projection_schema":"transaction-request-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":4,"source_binding_ref_required":true,"source_class":"TransactionRequest","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"TransactionRequest","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"GovernedPaymentAction:{projection.action_id}","entity_role":"GOVERNED_ACTION","entity_type":"GovernedPaymentAction","event_type":"ACTION_RECORDED","projection_schema":"governed-payment-action-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[{"source_path":"projection.order_version","target_path":"projection.order_version"}],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_ref","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.payment_ref","target_binding_assertions":[],"target_entity_ref_template":"PaymentExecutionRecord:{value}","target_entity_role":"CURRENT_PAYMENT_CANDIDATE","target_entity_type":"PaymentExecutionRecord","value_mode":"SCALAR"}],"sequence_no":5,"source_binding_ref_required":true,"source_class":"GovernedPaymentAction","source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"GovernedPaymentAction","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"PaymentExecutionRecord:{projection.payment_id}","entity_role":"CURRENT_PAYMENT_CANDIDATE","entity_type":"PaymentExecutionRecord","event_type":"PAYMENT_CANDIDATE_RECORDED","projection_schema":"payment-execution-record-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_id","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_id","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"}],"sequence_no":6,"source_binding_ref_required":true,"source_class":"PaymentExecutionRecord","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"PaymentExecutionRecord","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"GovernedActionBindingFact:binding:{binding_digest}","entity_role":"ACTION_BINDING_FACT","entity_type":"GovernedActionBindingFact","event_type":"ACTION_BINDING_DECISION_RECORDED","projection_schema":"governed-action-binding-fact-trace/v2","relations":[{"relation_type":"VALIDATED_AGAINST","source_assertion_path":"projection.action_id","target_binding_assertions":[],"target_entity_ref_template":"GovernedPaymentAction:{value}","target_entity_role":"GOVERNED_ACTION","target_entity_type":"GovernedPaymentAction","value_mode":"SCALAR"},{"relation_type":"VALIDATED_AGAINST","source_assertion_path":"projection.checked_payment_ref","target_binding_assertions":[],"target_entity_ref_template":"PaymentExecutionRecord:{value}","target_entity_role":"CURRENT_PAYMENT_CANDIDATE","target_entity_type":"PaymentExecutionRecord","value_mode":"SCALAR"}],"sequence_no":7,"source_binding_ref_required":true,"source_class":"GovernedActionBindingFact","source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"GovernedActionBindingFact","value_paths":{"decision_path":null,"reason_codes_path":"projection.reason_codes","status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"RuntimeGateRecord:binding:{binding_digest}","entity_role":"RUNTIME_GATE_OBSERVATION","entity_type":"RuntimeGateRecord","event_type":"RUNTIME_DECISION_RECORDED","projection_schema":"runtime-gate-record-trace/v2","relations":[],"sequence_no":8,"source_binding_ref_required":true,"source_class":"RuntimeGateRecord","source_module":"agentic_payment_experiment.trusted_execution.replay","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"RuntimeGateRecord","value_paths":{"decision_path":"projection.final_decision","reason_codes_path":"projection.reason_codes","status_path":"projection.binding_status"}},{"binding_alias_group":null,"entity_ref_template":"PaymentExecutionRecord:{projection.payment_id}","entity_role":"PAYMENT_EXECUTION_OUTCOME","entity_type":"PaymentExecutionRecord","event_type":"PAYMENT_OUTCOME_RECORDED","projection_schema":"payment-execution-record-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_id","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_id","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"}],"sequence_no":9,"source_binding_ref_required":true,"source_class":"PaymentExecutionRecord","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"PaymentExecutionRecord","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"FulfillmentRecord:{projection.fulfillment_id}","entity_role":"FULFILMENT_OUTCOME","entity_type":"FulfillmentRecord","event_type":"FULFILMENT_OUTCOME_RECORDED","projection_schema":"fulfillment-record-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_id","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"}],"sequence_no":10,"source_binding_ref_required":true,"source_class":"FulfillmentRecord","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"FulfillmentRecord","value_paths":{"decision_path":null,"reason_codes_path":"projection.reason_codes","status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"WebShopPaymentFulfilmentOutcome:binding:{binding_digest}","entity_role":"FINAL_OUTCOME","entity_type":"WebShopPaymentFulfilmentOutcome","event_type":"RESULT_RECORDED","projection_schema":"webshop-payment-fulfilment-outcome-result-trace/v2","relations":[],"sequence_no":11,"source_binding_ref_required":true,"source_class":"WebShopPaymentFulfilmentOutcome","source_module":"agentic_payment_experiment.webshop_payment_sidecar","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"WebShopPaymentFulfilmentOutcome","value_paths":{"decision_path":null,"reason_codes_path":"projection.reason_codes","status_path":"projection.lifecycle_task_status"}}],"new_business_rule_required":false,"profile":"WEBSHOP_NORMAL_PURCHASE_V2","task_id":"T01","title":"正常授权购买"},{"current_status":"NOT_AVAILABLE","entity_roles":["AUTHORITY","AUTHORIZED_ORDER_SNAPSHOT","CURRENT_ORDER_SNAPSHOT","CURRENT_REQUEST","PREPAYMENT_VALIDATION","FINAL_OUTCOME"],"events":[{"binding_alias_group":null,"entity_ref_template":"IntentMandate:{projection.mandate_id}","entity_role":"AUTHORITY","entity_type":"IntentMandate","event_type":"AUTHORITY_RECORDED","projection_schema":"intent-mandate-trace/v2","relations":[],"sequence_no":1,"source_binding_ref_required":true,"source_class":"IntentMandate","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"IntentMandate","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"Order:{projection.order_id}","entity_role":"AUTHORIZED_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":2,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"Order:{projection.order_id}","entity_role":"CURRENT_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":3,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"TransactionRequest:{projection.request_id}","entity_role":"CURRENT_REQUEST","entity_type":"TransactionRequest","event_type":"REQUEST_RECORDED","projection_schema":"transaction-request-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":4,"source_binding_ref_required":true,"source_class":"TransactionRequest","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"TransactionRequest","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"ValidationResult:binding:{binding_digest}","entity_role":"PREPAYMENT_VALIDATION","entity_type":"ValidationResult","event_type":"PREPAYMENT_DECISION_RECORDED","projection_schema":"validation-result-trace/v2","relations":[],"sequence_no":5,"source_binding_ref_required":true,"source_class":"ValidationResult","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"ValidationResult","value_paths":{"decision_path":"projection.decision","reason_codes_path":"projection.issue_codes","status_path":null}},{"binding_alias_group":null,"entity_ref_template":"WebShopBuyNowGateOutcome:binding:{binding_digest}","entity_role":"FINAL_OUTCOME","entity_type":"WebShopBuyNowGateOutcome","event_type":"RESULT_RECORDED","projection_schema":"webshop-buy-now-gate-outcome-result-trace/v2","relations":[],"sequence_no":6,"source_binding_ref_required":true,"source_class":"WebShopBuyNowGateOutcome","source_module":"agentic_payment_experiment.webshop_runtime_gate","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"WebShopBuyNowGateOutcome","value_paths":{"decision_path":"projection.decision","reason_codes_path":"projection.reason_codes","status_path":null}}],"new_business_rule_required":false,"profile":"WEBSHOP_PREPAYMENT_T02_V2","task_id":"T02","title":"订单价格上涨"},{"current_status":"NOT_AVAILABLE","entity_roles":["AUTHORITY","AUTHORIZED_ORDER_SNAPSHOT","CURRENT_ORDER_SNAPSHOT","CURRENT_REQUEST","PREPAYMENT_VALIDATION","FINAL_OUTCOME"],"events":[{"binding_alias_group":null,"entity_ref_template":"IntentMandate:{projection.mandate_id}","entity_role":"AUTHORITY","entity_type":"IntentMandate","event_type":"AUTHORITY_RECORDED","projection_schema":"intent-mandate-trace/v2","relations":[],"sequence_no":1,"source_binding_ref_required":true,"source_class":"IntentMandate","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"IntentMandate","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"Order:{projection.order_id}","entity_role":"AUTHORIZED_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":2,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"Order:{projection.order_id}","entity_role":"CURRENT_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":3,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"TransactionRequest:{projection.request_id}","entity_role":"CURRENT_REQUEST","entity_type":"TransactionRequest","event_type":"REQUEST_RECORDED","projection_schema":"transaction-request-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":4,"source_binding_ref_required":true,"source_class":"TransactionRequest","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"TransactionRequest","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"ValidationResult:binding:{binding_digest}","entity_role":"PREPAYMENT_VALIDATION","entity_type":"ValidationResult","event_type":"PREPAYMENT_DECISION_RECORDED","projection_schema":"validation-result-trace/v2","relations":[],"sequence_no":5,"source_binding_ref_required":true,"source_class":"ValidationResult","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"ValidationResult","value_paths":{"decision_path":"projection.decision","reason_codes_path":"projection.issue_codes","status_path":null}},{"binding_alias_group":null,"entity_ref_template":"WebShopBuyNowGateOutcome:binding:{binding_digest}","entity_role":"FINAL_OUTCOME","entity_type":"WebShopBuyNowGateOutcome","event_type":"RESULT_RECORDED","projection_schema":"webshop-buy-now-gate-outcome-result-trace/v2","relations":[],"sequence_no":6,"source_binding_ref_required":true,"source_class":"WebShopBuyNowGateOutcome","source_module":"agentic_payment_experiment.webshop_runtime_gate","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"WebShopBuyNowGateOutcome","value_paths":{"decision_path":"projection.decision","reason_codes_path":"projection.reason_codes","status_path":null}}],"new_business_rule_required":false,"profile":"WEBSHOP_PREPAYMENT_T03_V2","task_id":"T03","title":"订单价格下降"},{"current_status":"NOT_AVAILABLE","entity_roles":["AUTHORITY","AUTHORIZED_ORDER_SNAPSHOT","CURRENT_ORDER_SNAPSHOT","CURRENT_REQUEST","PREPAYMENT_VALIDATION","FINAL_OUTCOME"],"events":[{"binding_alias_group":null,"entity_ref_template":"IntentMandate:{projection.mandate_id}","entity_role":"AUTHORITY","entity_type":"IntentMandate","event_type":"AUTHORITY_RECORDED","projection_schema":"intent-mandate-trace/v2","relations":[],"sequence_no":1,"source_binding_ref_required":true,"source_class":"IntentMandate","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"IntentMandate","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"Order:{projection.order_id}","entity_role":"AUTHORIZED_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":2,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"Order:{projection.order_id}","entity_role":"CURRENT_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":3,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"TransactionRequest:{projection.request_id}","entity_role":"CURRENT_REQUEST","entity_type":"TransactionRequest","event_type":"REQUEST_RECORDED","projection_schema":"transaction-request-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":4,"source_binding_ref_required":true,"source_class":"TransactionRequest","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"TransactionRequest","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"ValidationResult:binding:{binding_digest}","entity_role":"PREPAYMENT_VALIDATION","entity_type":"ValidationResult","event_type":"PREPAYMENT_DECISION_RECORDED","projection_schema":"validation-result-trace/v2","relations":[],"sequence_no":5,"source_binding_ref_required":true,"source_class":"ValidationResult","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"ValidationResult","value_paths":{"decision_path":"projection.decision","reason_codes_path":"projection.issue_codes","status_path":null}},{"binding_alias_group":null,"entity_ref_template":"WebShopBuyNowGateOutcome:binding:{binding_digest}","entity_role":"FINAL_OUTCOME","entity_type":"WebShopBuyNowGateOutcome","event_type":"RESULT_RECORDED","projection_schema":"webshop-buy-now-gate-outcome-result-trace/v2","relations":[],"sequence_no":6,"source_binding_ref_required":true,"source_class":"WebShopBuyNowGateOutcome","source_module":"agentic_payment_experiment.webshop_runtime_gate","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"WebShopBuyNowGateOutcome","value_paths":{"decision_path":"projection.decision","reason_codes_path":"projection.reason_codes","status_path":null}}],"new_business_rule_required":false,"profile":"WEBSHOP_PREPAYMENT_T04_V2","task_id":"T04","title":"收款方变化"},{"current_status":"NOT_AVAILABLE","entity_roles":["AUTHORITY","AUTHORIZED_ORDER_SNAPSHOT","CURRENT_ORDER_SNAPSHOT","CURRENT_REQUEST","PREPAYMENT_VALIDATION","GOVERNED_ACTION","CURRENT_PAYMENT_CANDIDATE","ACTION_BINDING_FACT","FINAL_OUTCOME"],"events":[{"binding_alias_group":null,"entity_ref_template":"IntentMandate:{projection.mandate_id}","entity_role":"AUTHORITY","entity_type":"IntentMandate","event_type":"AUTHORITY_RECORDED","projection_schema":"intent-mandate-trace/v2","relations":[],"sequence_no":1,"source_binding_ref_required":true,"source_class":"IntentMandate","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"IntentMandate","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":"AUTHORIZED_CURRENT_ORDER_SHARED_BINDING","entity_ref_template":"Order:{projection.order_id}","entity_role":"AUTHORIZED_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":2,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":"AUTHORIZED_CURRENT_ORDER_SHARED_BINDING","entity_ref_template":"Order:{projection.order_id}","entity_role":"CURRENT_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":3,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"TransactionRequest:{projection.request_id}","entity_role":"CURRENT_REQUEST","entity_type":"TransactionRequest","event_type":"REQUEST_RECORDED","projection_schema":"transaction-request-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":4,"source_binding_ref_required":true,"source_class":"TransactionRequest","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"TransactionRequest","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"ValidationResult:binding:{binding_digest}","entity_role":"PREPAYMENT_VALIDATION","entity_type":"ValidationResult","event_type":"PREPAYMENT_DECISION_RECORDED","projection_schema":"validation-result-trace/v2","relations":[],"sequence_no":5,"source_binding_ref_required":true,"source_class":"ValidationResult","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"ValidationResult","value_paths":{"decision_path":"projection.decision","reason_codes_path":"projection.issue_codes","status_path":null}},{"binding_alias_group":null,"entity_ref_template":"GovernedPaymentAction:{projection.action_id}","entity_role":"GOVERNED_ACTION","entity_type":"GovernedPaymentAction","event_type":"ACTION_RECORDED","projection_schema":"governed-payment-action-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[{"source_path":"projection.order_version","target_path":"projection.order_version"}],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_ref","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.payment_ref","target_binding_assertions":[],"target_entity_ref_template":"PaymentExecutionRecord:{value}","target_entity_role":"CURRENT_PAYMENT_CANDIDATE","target_entity_type":"PaymentExecutionRecord","value_mode":"SCALAR"}],"sequence_no":6,"source_binding_ref_required":true,"source_class":"GovernedPaymentAction","source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"GovernedPaymentAction","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"PaymentExecutionRecord:{projection.payment_id}","entity_role":"CURRENT_PAYMENT_CANDIDATE","entity_type":"PaymentExecutionRecord","event_type":"PAYMENT_CANDIDATE_RECORDED","projection_schema":"payment-execution-record-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_id","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_id","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"}],"sequence_no":7,"source_binding_ref_required":true,"source_class":"PaymentExecutionRecord","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"PaymentExecutionRecord","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"GovernedActionBindingFact:binding:{binding_digest}","entity_role":"ACTION_BINDING_FACT","entity_type":"GovernedActionBindingFact","event_type":"ACTION_BINDING_DECISION_RECORDED","projection_schema":"governed-action-binding-fact-trace/v2","relations":[{"relation_type":"VALIDATED_AGAINST","source_assertion_path":"projection.action_id","target_binding_assertions":[],"target_entity_ref_template":"GovernedPaymentAction:{value}","target_entity_role":"GOVERNED_ACTION","target_entity_type":"GovernedPaymentAction","value_mode":"SCALAR"},{"relation_type":"VALIDATED_AGAINST","source_assertion_path":"projection.checked_payment_ref","target_binding_assertions":[],"target_entity_ref_template":"PaymentExecutionRecord:{value}","target_entity_role":"CURRENT_PAYMENT_CANDIDATE","target_entity_type":"PaymentExecutionRecord","value_mode":"SCALAR"}],"sequence_no":8,"source_binding_ref_required":true,"source_class":"GovernedActionBindingFact","source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"GovernedActionBindingFact","value_paths":{"decision_path":null,"reason_codes_path":"projection.reason_codes","status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"WebShopBuyNowGateOutcome:binding:{binding_digest}","entity_role":"FINAL_OUTCOME","entity_type":"WebShopBuyNowGateOutcome","event_type":"RESULT_RECORDED","projection_schema":"webshop-buy-now-gate-outcome-result-trace/v2","relations":[],"sequence_no":9,"source_binding_ref_required":true,"source_class":"WebShopBuyNowGateOutcome","source_module":"agentic_payment_experiment.webshop_runtime_gate","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"WebShopBuyNowGateOutcome","value_paths":{"decision_path":"projection.decision","reason_codes_path":"projection.reason_codes","status_path":null}}],"new_business_rule_required":false,"profile":"WEBSHOP_ACTION_BINDING_T05_V2","task_id":"T05","title":"Action Agent 不匹配"},{"current_status":"NOT_AVAILABLE","entity_roles":["AUTHORITY","AUTHORIZED_ORDER_SNAPSHOT","CURRENT_ORDER_SNAPSHOT","CURRENT_REQUEST","PREPAYMENT_VALIDATION","GOVERNED_ACTION","CURRENT_PAYMENT_CANDIDATE","ACTION_BINDING_FACT","FINAL_OUTCOME"],"events":[{"binding_alias_group":null,"entity_ref_template":"IntentMandate:{projection.mandate_id}","entity_role":"AUTHORITY","entity_type":"IntentMandate","event_type":"AUTHORITY_RECORDED","projection_schema":"intent-mandate-trace/v2","relations":[],"sequence_no":1,"source_binding_ref_required":true,"source_class":"IntentMandate","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"IntentMandate","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":"AUTHORIZED_CURRENT_ORDER_SHARED_BINDING","entity_ref_template":"Order:{projection.order_id}","entity_role":"AUTHORIZED_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":2,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":"AUTHORIZED_CURRENT_ORDER_SHARED_BINDING","entity_ref_template":"Order:{projection.order_id}","entity_role":"CURRENT_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":3,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"TransactionRequest:{projection.request_id}","entity_role":"CURRENT_REQUEST","entity_type":"TransactionRequest","event_type":"REQUEST_RECORDED","projection_schema":"transaction-request-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":4,"source_binding_ref_required":true,"source_class":"TransactionRequest","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"TransactionRequest","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"ValidationResult:binding:{binding_digest}","entity_role":"PREPAYMENT_VALIDATION","entity_type":"ValidationResult","event_type":"PREPAYMENT_DECISION_RECORDED","projection_schema":"validation-result-trace/v2","relations":[],"sequence_no":5,"source_binding_ref_required":true,"source_class":"ValidationResult","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"ValidationResult","value_paths":{"decision_path":"projection.decision","reason_codes_path":"projection.issue_codes","status_path":null}},{"binding_alias_group":null,"entity_ref_template":"GovernedPaymentAction:binding:{binding_digest}","entity_role":"GOVERNED_ACTION","entity_type":"GovernedPaymentAction","event_type":"ACTION_RECORDED","projection_schema":"governed-payment-action-missing-id-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[{"source_path":"projection.order_version","target_path":"projection.order_version"}],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_ref","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.payment_ref","target_binding_assertions":[],"target_entity_ref_template":"PaymentExecutionRecord:{value}","target_entity_role":"CURRENT_PAYMENT_CANDIDATE","target_entity_type":"PaymentExecutionRecord","value_mode":"SCALAR"}],"sequence_no":6,"source_binding_ref_required":true,"source_class":"GovernedPaymentAction","source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"GovernedPaymentAction","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"PaymentExecutionRecord:{projection.payment_id}","entity_role":"CURRENT_PAYMENT_CANDIDATE","entity_type":"PaymentExecutionRecord","event_type":"PAYMENT_CANDIDATE_RECORDED","projection_schema":"payment-execution-record-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_id","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_id","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"}],"sequence_no":7,"source_binding_ref_required":true,"source_class":"PaymentExecutionRecord","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"PaymentExecutionRecord","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"GovernedActionBindingFact:binding:{binding_digest}","entity_role":"ACTION_BINDING_FACT","entity_type":"GovernedActionBindingFact","event_type":"ACTION_BINDING_DECISION_RECORDED","projection_schema":"governed-action-binding-fact-trace/v2","relations":[{"relation_type":"VALIDATED_AGAINST","source_assertion_path":"projection.checked_payment_ref","target_binding_assertions":[],"target_entity_ref_template":"PaymentExecutionRecord:{value}","target_entity_role":"CURRENT_PAYMENT_CANDIDATE","target_entity_type":"PaymentExecutionRecord","value_mode":"SCALAR"}],"sequence_no":8,"source_binding_ref_required":true,"source_class":"GovernedActionBindingFact","source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"GovernedActionBindingFact","value_paths":{"decision_path":null,"reason_codes_path":"projection.reason_codes","status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"WebShopBuyNowGateOutcome:binding:{binding_digest}","entity_role":"FINAL_OUTCOME","entity_type":"WebShopBuyNowGateOutcome","event_type":"RESULT_RECORDED","projection_schema":"webshop-buy-now-gate-outcome-result-trace/v2","relations":[],"sequence_no":9,"source_binding_ref_required":true,"source_class":"WebShopBuyNowGateOutcome","source_module":"agentic_payment_experiment.webshop_runtime_gate","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"WebShopBuyNowGateOutcome","value_paths":{"decision_path":"projection.decision","reason_codes_path":"projection.reason_codes","status_path":null}}],"new_business_rule_required":false,"profile":"WEBSHOP_ACTION_BINDING_T06_V2","task_id":"T06","title":"Action ID 缺失"},{"current_status":"NOT_AVAILABLE","entity_roles":["ATTACK_POLICY_RESULT","ATTACK_LINEAGE_RESULT","FINAL_OUTCOME"],"events":[{"binding_alias_group":null,"entity_ref_template":"AttackOverlayResult:{projection.attack_id}","entity_role":"ATTACK_POLICY_RESULT","entity_type":"AttackOverlayResult","event_type":"POLICY_DECISION_RECORDED","projection_schema":"attack-overlay-result-trace/v2","relations":[],"sequence_no":1,"source_binding_ref_required":true,"source_class":"AttackOverlayResult","source_module":"agentic_payment_experiment.attack_overlay","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"AttackOverlayResult","value_paths":{"decision_path":"projection.defended_decision","reason_codes_path":"projection.reason_codes","status_path":null}},{"binding_alias_group":null,"entity_ref_template":"AttackOverlayResult:{projection.attack_id}","entity_role":"ATTACK_LINEAGE_RESULT","entity_type":"AttackOverlayResult","event_type":"LINEAGE_DECISION_RECORDED","projection_schema":"attack-overlay-result-trace/v2","relations":[],"sequence_no":2,"source_binding_ref_required":true,"source_class":"AttackOverlayResult","source_module":"agentic_payment_experiment.attack_overlay","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"AttackOverlayResult","value_paths":{"decision_path":null,"reason_codes_path":"projection.lineage_reason_codes","status_path":"projection.lineage_status"}},{"binding_alias_group":null,"entity_ref_template":"AttackOverlayResult:{projection.attack_id}","entity_role":"FINAL_OUTCOME","entity_type":"AttackOverlayResult","event_type":"RESULT_RECORDED","projection_schema":"attack-overlay-result-trace/v2","relations":[],"sequence_no":3,"source_binding_ref_required":true,"source_class":"AttackOverlayResult","source_module":"agentic_payment_experiment.attack_overlay","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"AttackOverlayResult","value_paths":{"decision_path":"projection.defended_decision","reason_codes_path":"projection.reason_codes","status_path":null}}],"new_business_rule_required":false,"profile":"ATTACK_OVERLAY_T07_V2","task_id":"T07","title":"不可信网页金额覆盖被阻断"},{"current_status":"NOT_AVAILABLE","entity_roles":["ATTACK_POLICY_RESULT","ATTACK_LINEAGE_RESULT","FINAL_OUTCOME"],"events":[{"binding_alias_group":null,"entity_ref_template":"AttackOverlayResult:{projection.attack_id}","entity_role":"ATTACK_POLICY_RESULT","entity_type":"AttackOverlayResult","event_type":"POLICY_DECISION_RECORDED","projection_schema":"attack-overlay-result-trace/v2","relations":[],"sequence_no":1,"source_binding_ref_required":true,"source_class":"AttackOverlayResult","source_module":"agentic_payment_experiment.attack_overlay","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"AttackOverlayResult","value_paths":{"decision_path":"projection.defended_decision","reason_codes_path":"projection.reason_codes","status_path":null}},{"binding_alias_group":null,"entity_ref_template":"AttackOverlayResult:{projection.attack_id}","entity_role":"ATTACK_LINEAGE_RESULT","entity_type":"AttackOverlayResult","event_type":"LINEAGE_DECISION_RECORDED","projection_schema":"attack-overlay-result-trace/v2","relations":[],"sequence_no":2,"source_binding_ref_required":true,"source_class":"AttackOverlayResult","source_module":"agentic_payment_experiment.attack_overlay","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"AttackOverlayResult","value_paths":{"decision_path":null,"reason_codes_path":"projection.lineage_reason_codes","status_path":"projection.lineage_status"}},{"binding_alias_group":null,"entity_ref_template":"AttackOverlayResult:{projection.attack_id}","entity_role":"FINAL_OUTCOME","entity_type":"AttackOverlayResult","event_type":"RESULT_RECORDED","projection_schema":"attack-overlay-result-trace/v2","relations":[],"sequence_no":3,"source_binding_ref_required":true,"source_class":"AttackOverlayResult","source_module":"agentic_payment_experiment.attack_overlay","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"AttackOverlayResult","value_paths":{"decision_path":"projection.defended_decision","reason_codes_path":"projection.reason_codes","status_path":null}}],"new_business_rule_required":false,"profile":"ATTACK_OVERLAY_T08_V2","task_id":"T08","title":"不可信收款方覆盖被阻断"},{"current_status":"NOT_AVAILABLE","entity_roles":["AUTHORITY","AUTHORIZED_ORDER_SNAPSHOT","CURRENT_ORDER_SNAPSHOT","CURRENT_REQUEST","GOVERNED_ACTION","CURRENT_PAYMENT_CANDIDATE","ACTION_BINDING_FACT","RUNTIME_GATE_OBSERVATION","PAYMENT_EXECUTION_OUTCOME","RECOVERY_OUTCOME","FINAL_OUTCOME"],"events":[{"binding_alias_group":null,"entity_ref_template":"IntentMandate:{projection.mandate_id}","entity_role":"AUTHORITY","entity_type":"IntentMandate","event_type":"AUTHORITY_RECORDED","projection_schema":"intent-mandate-trace/v2","relations":[],"sequence_no":1,"source_binding_ref_required":true,"source_class":"IntentMandate","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"IntentMandate","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":"AUTHORIZED_CURRENT_ORDER_SHARED_BINDING","entity_ref_template":"Order:{projection.order_id}","entity_role":"AUTHORIZED_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":2,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":"AUTHORIZED_CURRENT_ORDER_SHARED_BINDING","entity_ref_template":"Order:{projection.order_id}","entity_role":"CURRENT_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":3,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"TransactionRequest:{projection.request_id}","entity_role":"CURRENT_REQUEST","entity_type":"TransactionRequest","event_type":"REQUEST_RECORDED","projection_schema":"transaction-request-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":4,"source_binding_ref_required":true,"source_class":"TransactionRequest","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"TransactionRequest","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"GovernedPaymentAction:{projection.action_id}","entity_role":"GOVERNED_ACTION","entity_type":"GovernedPaymentAction","event_type":"ACTION_RECORDED","projection_schema":"governed-payment-action-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[{"source_path":"projection.order_version","target_path":"projection.order_version"}],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_ref","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.payment_ref","target_binding_assertions":[],"target_entity_ref_template":"PaymentExecutionRecord:{value}","target_entity_role":"CURRENT_PAYMENT_CANDIDATE","target_entity_type":"PaymentExecutionRecord","value_mode":"SCALAR"}],"sequence_no":5,"source_binding_ref_required":true,"source_class":"GovernedPaymentAction","source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"GovernedPaymentAction","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"PaymentExecutionRecord:{projection.payment_id}","entity_role":"CURRENT_PAYMENT_CANDIDATE","entity_type":"PaymentExecutionRecord","event_type":"PAYMENT_CANDIDATE_RECORDED","projection_schema":"payment-execution-record-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_id","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_id","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"}],"sequence_no":6,"source_binding_ref_required":true,"source_class":"PaymentExecutionRecord","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"PaymentExecutionRecord","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"GovernedActionBindingFact:binding:{binding_digest}","entity_role":"ACTION_BINDING_FACT","entity_type":"GovernedActionBindingFact","event_type":"ACTION_BINDING_DECISION_RECORDED","projection_schema":"governed-action-binding-fact-trace/v2","relations":[{"relation_type":"VALIDATED_AGAINST","source_assertion_path":"projection.action_id","target_binding_assertions":[],"target_entity_ref_template":"GovernedPaymentAction:{value}","target_entity_role":"GOVERNED_ACTION","target_entity_type":"GovernedPaymentAction","value_mode":"SCALAR"},{"relation_type":"VALIDATED_AGAINST","source_assertion_path":"projection.checked_payment_ref","target_binding_assertions":[],"target_entity_ref_template":"PaymentExecutionRecord:{value}","target_entity_role":"CURRENT_PAYMENT_CANDIDATE","target_entity_type":"PaymentExecutionRecord","value_mode":"SCALAR"}],"sequence_no":7,"source_binding_ref_required":true,"source_class":"GovernedActionBindingFact","source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"GovernedActionBindingFact","value_paths":{"decision_path":null,"reason_codes_path":"projection.reason_codes","status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"RuntimeGateRecord:binding:{binding_digest}","entity_role":"RUNTIME_GATE_OBSERVATION","entity_type":"RuntimeGateRecord","event_type":"RUNTIME_DECISION_RECORDED","projection_schema":"runtime-gate-record-trace/v2","relations":[],"sequence_no":8,"source_binding_ref_required":true,"source_class":"RuntimeGateRecord","source_module":"agentic_payment_experiment.trusted_execution.replay","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"RuntimeGateRecord","value_paths":{"decision_path":"projection.final_decision","reason_codes_path":"projection.reason_codes","status_path":"projection.binding_status"}},{"binding_alias_group":null,"entity_ref_template":"PaymentExecutionRecord:{projection.payment_id}","entity_role":"PAYMENT_EXECUTION_OUTCOME","entity_type":"PaymentExecutionRecord","event_type":"PAYMENT_OUTCOME_RECORDED","projection_schema":"payment-execution-record-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_id","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_id","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"}],"sequence_no":9,"source_binding_ref_required":true,"source_class":"PaymentExecutionRecord","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"PaymentExecutionRecord","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"PaymentRecoveryResult:binding:{binding_digest}","entity_role":"RECOVERY_OUTCOME","entity_type":"PaymentRecoveryResult","event_type":"RECOVERY_OUTCOME_RECORDED","projection_schema":"payment-recovery-result-trace/v2","relations":[],"sequence_no":10,"source_binding_ref_required":true,"source_class":"PaymentRecoveryResult","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"PaymentRecoveryResult","value_paths":{"decision_path":null,"reason_codes_path":"projection.issue_codes","status_path":"projection.recovery_status"}},{"binding_alias_group":null,"entity_ref_template":"WebShopPaymentFulfilmentOutcome:binding:{binding_digest}","entity_role":"FINAL_OUTCOME","entity_type":"WebShopPaymentFulfilmentOutcome","event_type":"RESULT_RECORDED","projection_schema":"webshop-payment-fulfilment-outcome-result-trace/v2","relations":[],"sequence_no":11,"source_binding_ref_required":true,"source_class":"WebShopPaymentFulfilmentOutcome","source_module":"agentic_payment_experiment.webshop_payment_sidecar","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"WebShopPaymentFulfilmentOutcome","value_paths":{"decision_path":null,"reason_codes_path":"projection.reason_codes","status_path":"projection.lifecycle_task_status"}}],"new_business_rule_required":false,"profile":"WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2","task_id":"T09","title":"UNKNOWN 支付状态恢复"},{"current_status":"NOT_AVAILABLE","entity_roles":["AUTHORITY","AUTHORIZED_ORDER_SNAPSHOT","CURRENT_ORDER_SNAPSHOT","CURRENT_REQUEST","GOVERNED_ACTION","CURRENT_PAYMENT_CANDIDATE","ACTION_BINDING_FACT","HISTORICAL_SUCCEEDED_PAYMENT","KNOWN_PAYMENT_PREFLIGHT_FACT","PREPAYMENT_VALIDATION","RUNTIME_GATE_OBSERVATION","FINAL_OUTCOME"],"events":[{"binding_alias_group":null,"entity_ref_template":"IntentMandate:{projection.mandate_id}","entity_role":"AUTHORITY","entity_type":"IntentMandate","event_type":"AUTHORITY_RECORDED","projection_schema":"intent-mandate-trace/v2","relations":[],"sequence_no":1,"source_binding_ref_required":true,"source_class":"IntentMandate","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"IntentMandate","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":"AUTHORIZED_CURRENT_ORDER_SHARED_BINDING","entity_ref_template":"Order:{projection.order_id}","entity_role":"AUTHORIZED_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":2,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":"AUTHORIZED_CURRENT_ORDER_SHARED_BINDING","entity_ref_template":"Order:{projection.order_id}","entity_role":"CURRENT_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":3,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"TransactionRequest:{projection.request_id}","entity_role":"CURRENT_REQUEST","entity_type":"TransactionRequest","event_type":"REQUEST_RECORDED","projection_schema":"transaction-request-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":4,"source_binding_ref_required":true,"source_class":"TransactionRequest","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"TransactionRequest","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"GovernedPaymentAction:{projection.action_id}","entity_role":"GOVERNED_ACTION","entity_type":"GovernedPaymentAction","event_type":"ACTION_RECORDED","projection_schema":"governed-payment-action-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[{"source_path":"projection.order_version","target_path":"projection.order_version"}],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_ref","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.payment_ref","target_binding_assertions":[],"target_entity_ref_template":"PaymentExecutionRecord:{value}","target_entity_role":"CURRENT_PAYMENT_CANDIDATE","target_entity_type":"PaymentExecutionRecord","value_mode":"SCALAR"}],"sequence_no":5,"source_binding_ref_required":true,"source_class":"GovernedPaymentAction","source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"GovernedPaymentAction","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"PaymentExecutionRecord:{projection.payment_id}","entity_role":"CURRENT_PAYMENT_CANDIDATE","entity_type":"PaymentExecutionRecord","event_type":"PAYMENT_CANDIDATE_RECORDED","projection_schema":"payment-execution-record-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_id","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_id","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"}],"sequence_no":6,"source_binding_ref_required":true,"source_class":"PaymentExecutionRecord","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"PaymentExecutionRecord","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"GovernedActionBindingFact:binding:{binding_digest}","entity_role":"ACTION_BINDING_FACT","entity_type":"GovernedActionBindingFact","event_type":"ACTION_BINDING_DECISION_RECORDED","projection_schema":"governed-action-binding-fact-trace/v2","relations":[{"relation_type":"VALIDATED_AGAINST","source_assertion_path":"projection.action_id","target_binding_assertions":[],"target_entity_ref_template":"GovernedPaymentAction:{value}","target_entity_role":"GOVERNED_ACTION","target_entity_type":"GovernedPaymentAction","value_mode":"SCALAR"},{"relation_type":"VALIDATED_AGAINST","source_assertion_path":"projection.checked_payment_ref","target_binding_assertions":[],"target_entity_ref_template":"PaymentExecutionRecord:{value}","target_entity_role":"CURRENT_PAYMENT_CANDIDATE","target_entity_type":"PaymentExecutionRecord","value_mode":"SCALAR"}],"sequence_no":7,"source_binding_ref_required":true,"source_class":"GovernedActionBindingFact","source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"GovernedActionBindingFact","value_paths":{"decision_path":null,"reason_codes_path":"projection.reason_codes","status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"PaymentExecutionRecord:{projection.payment_id}","entity_role":"HISTORICAL_SUCCEEDED_PAYMENT","entity_type":"PaymentExecutionRecord","event_type":"PAYMENT_OUTCOME_RECORDED","projection_schema":"payment-execution-record-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_id","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_id","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"}],"sequence_no":8,"source_binding_ref_required":true,"source_class":"PaymentExecutionRecord","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"PaymentExecutionRecord","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"KnownPaymentAttemptPreflightFact:binding:{binding_digest}","entity_role":"KNOWN_PAYMENT_PREFLIGHT_FACT","entity_type":"KnownPaymentAttemptPreflightFact","event_type":"KNOWN_PAYMENT_PREFLIGHT_RECORDED","projection_schema":"known-payment-attempt-preflight-fact-trace/v2","relations":[{"relation_type":"VALIDATED_AGAINST","source_assertion_path":"projection.current_request_ref","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"MEMBER_OF","source_assertion_path":"projection.related_attempt_refs[]","target_binding_assertions":[],"target_entity_ref_template":"PaymentExecutionRecord:{value}","target_entity_role":"HISTORICAL_SUCCEEDED_PAYMENT","target_entity_type":"PaymentExecutionRecord","value_mode":"EACH_VALUE"}],"sequence_no":9,"source_binding_ref_required":true,"source_class":"KnownPaymentAttemptPreflightFact","source_module":"agentic_payment_experiment.trusted_execution.known_payment_attempt","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"KnownPaymentAttemptPreflightFact","value_paths":{"decision_path":null,"reason_codes_path":"projection.reason_codes","status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"ValidationResult:binding:{binding_digest}","entity_role":"PREPAYMENT_VALIDATION","entity_type":"ValidationResult","event_type":"PREPAYMENT_DECISION_RECORDED","projection_schema":"validation-result-trace/v2","relations":[],"sequence_no":10,"source_binding_ref_required":true,"source_class":"ValidationResult","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"ValidationResult","value_paths":{"decision_path":"projection.decision","reason_codes_path":"projection.issue_codes","status_path":null}},{"binding_alias_group":null,"entity_ref_template":"RuntimeGateRecord:binding:{binding_digest}","entity_role":"RUNTIME_GATE_OBSERVATION","entity_type":"RuntimeGateRecord","event_type":"RUNTIME_DECISION_RECORDED","projection_schema":"runtime-gate-record-trace/v2","relations":[],"sequence_no":11,"source_binding_ref_required":true,"source_class":"RuntimeGateRecord","source_module":"agentic_payment_experiment.trusted_execution.replay","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"RuntimeGateRecord","value_paths":{"decision_path":"projection.final_decision","reason_codes_path":"projection.reason_codes","status_path":"projection.binding_status"}},{"binding_alias_group":null,"entity_ref_template":"WebShopBuyNowGateOutcome:binding:{binding_digest}","entity_role":"FINAL_OUTCOME","entity_type":"WebShopBuyNowGateOutcome","event_type":"RESULT_RECORDED","projection_schema":"webshop-buy-now-gate-outcome-result-trace/v2","relations":[],"sequence_no":12,"source_binding_ref_required":true,"source_class":"WebShopBuyNowGateOutcome","source_module":"agentic_payment_experiment.webshop_runtime_gate","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"WebShopBuyNowGateOutcome","value_paths":{"decision_path":"projection.decision","reason_codes_path":"projection.reason_codes","status_path":null}}],"new_business_rule_required":false,"profile":"WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V2","task_id":"T10","title":"重复付款预检阻断"},{"current_status":"NOT_AVAILABLE","entity_roles":["AUTHORITY","AUTHORIZED_ORDER_SNAPSHOT","CURRENT_ORDER_SNAPSHOT","CURRENT_REQUEST","GOVERNED_ACTION","CURRENT_PAYMENT_CANDIDATE","ACTION_BINDING_FACT","RUNTIME_GATE_OBSERVATION","PAYMENT_EXECUTION_OUTCOME","FULFILMENT_OUTCOME","RECOVERY_OUTCOME","FINAL_OUTCOME"],"events":[{"binding_alias_group":null,"entity_ref_template":"IntentMandate:{projection.mandate_id}","entity_role":"AUTHORITY","entity_type":"IntentMandate","event_type":"AUTHORITY_RECORDED","projection_schema":"intent-mandate-trace/v2","relations":[],"sequence_no":1,"source_binding_ref_required":true,"source_class":"IntentMandate","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"IntentMandate","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":"AUTHORIZED_CURRENT_ORDER_SHARED_BINDING","entity_ref_template":"Order:{projection.order_id}","entity_role":"AUTHORIZED_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":2,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":"AUTHORIZED_CURRENT_ORDER_SHARED_BINDING","entity_ref_template":"Order:{projection.order_id}","entity_role":"CURRENT_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":3,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"TransactionRequest:{projection.request_id}","entity_role":"CURRENT_REQUEST","entity_type":"TransactionRequest","event_type":"REQUEST_RECORDED","projection_schema":"transaction-request-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":4,"source_binding_ref_required":true,"source_class":"TransactionRequest","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"TransactionRequest","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"GovernedPaymentAction:{projection.action_id}","entity_role":"GOVERNED_ACTION","entity_type":"GovernedPaymentAction","event_type":"ACTION_RECORDED","projection_schema":"governed-payment-action-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[{"source_path":"projection.order_version","target_path":"projection.order_version"}],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_ref","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.payment_ref","target_binding_assertions":[],"target_entity_ref_template":"PaymentExecutionRecord:{value}","target_entity_role":"CURRENT_PAYMENT_CANDIDATE","target_entity_type":"PaymentExecutionRecord","value_mode":"SCALAR"}],"sequence_no":5,"source_binding_ref_required":true,"source_class":"GovernedPaymentAction","source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"GovernedPaymentAction","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"PaymentExecutionRecord:{projection.payment_id}","entity_role":"CURRENT_PAYMENT_CANDIDATE","entity_type":"PaymentExecutionRecord","event_type":"PAYMENT_CANDIDATE_RECORDED","projection_schema":"payment-execution-record-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_id","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_id","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"}],"sequence_no":6,"source_binding_ref_required":true,"source_class":"PaymentExecutionRecord","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"PaymentExecutionRecord","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"GovernedActionBindingFact:binding:{binding_digest}","entity_role":"ACTION_BINDING_FACT","entity_type":"GovernedActionBindingFact","event_type":"ACTION_BINDING_DECISION_RECORDED","projection_schema":"governed-action-binding-fact-trace/v2","relations":[{"relation_type":"VALIDATED_AGAINST","source_assertion_path":"projection.action_id","target_binding_assertions":[],"target_entity_ref_template":"GovernedPaymentAction:{value}","target_entity_role":"GOVERNED_ACTION","target_entity_type":"GovernedPaymentAction","value_mode":"SCALAR"},{"relation_type":"VALIDATED_AGAINST","source_assertion_path":"projection.checked_payment_ref","target_binding_assertions":[],"target_entity_ref_template":"PaymentExecutionRecord:{value}","target_entity_role":"CURRENT_PAYMENT_CANDIDATE","target_entity_type":"PaymentExecutionRecord","value_mode":"SCALAR"}],"sequence_no":7,"source_binding_ref_required":true,"source_class":"GovernedActionBindingFact","source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"GovernedActionBindingFact","value_paths":{"decision_path":null,"reason_codes_path":"projection.reason_codes","status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"RuntimeGateRecord:binding:{binding_digest}","entity_role":"RUNTIME_GATE_OBSERVATION","entity_type":"RuntimeGateRecord","event_type":"RUNTIME_DECISION_RECORDED","projection_schema":"runtime-gate-record-trace/v2","relations":[],"sequence_no":8,"source_binding_ref_required":true,"source_class":"RuntimeGateRecord","source_module":"agentic_payment_experiment.trusted_execution.replay","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"RuntimeGateRecord","value_paths":{"decision_path":"projection.final_decision","reason_codes_path":"projection.reason_codes","status_path":"projection.binding_status"}},{"binding_alias_group":null,"entity_ref_template":"PaymentExecutionRecord:{projection.payment_id}","entity_role":"PAYMENT_EXECUTION_OUTCOME","entity_type":"PaymentExecutionRecord","event_type":"PAYMENT_OUTCOME_RECORDED","projection_schema":"payment-execution-record-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_id","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_id","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"}],"sequence_no":9,"source_binding_ref_required":true,"source_class":"PaymentExecutionRecord","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"PaymentExecutionRecord","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"FulfillmentRecord:{projection.fulfillment_id}","entity_role":"FULFILMENT_OUTCOME","entity_type":"FulfillmentRecord","event_type":"FULFILMENT_OUTCOME_RECORDED","projection_schema":"fulfillment-record-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_id","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"}],"sequence_no":10,"source_binding_ref_required":true,"source_class":"FulfillmentRecord","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"FulfillmentRecord","value_paths":{"decision_path":null,"reason_codes_path":"projection.reason_codes","status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"PaymentRecoveryResult:binding:{binding_digest}","entity_role":"RECOVERY_OUTCOME","entity_type":"PaymentRecoveryResult","event_type":"RECOVERY_OUTCOME_RECORDED","projection_schema":"payment-recovery-result-trace/v2","relations":[],"sequence_no":11,"source_binding_ref_required":true,"source_class":"PaymentRecoveryResult","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"PaymentRecoveryResult","value_paths":{"decision_path":null,"reason_codes_path":"projection.issue_codes","status_path":"projection.recovery_status"}},{"binding_alias_group":null,"entity_ref_template":"WebShopPaymentFulfilmentOutcome:binding:{binding_digest}","entity_role":"FINAL_OUTCOME","entity_type":"WebShopPaymentFulfilmentOutcome","event_type":"RESULT_RECORDED","projection_schema":"webshop-payment-fulfilment-outcome-result-trace/v2","relations":[],"sequence_no":12,"source_binding_ref_required":true,"source_class":"WebShopPaymentFulfilmentOutcome","source_module":"agentic_payment_experiment.webshop_payment_sidecar","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"WebShopPaymentFulfilmentOutcome","value_paths":{"decision_path":null,"reason_codes_path":"projection.reason_codes","status_path":"projection.lifecycle_task_status"}}],"new_business_rule_required":false,"profile":"WEBSHOP_FULFILMENT_FAILURE_V2","task_id":"T11","title":"付款成功但履约失败"},{"current_status":"NOT_AVAILABLE","entity_roles":["AUTHORITY","AUTHORIZED_ORDER_SNAPSHOT","CURRENT_ORDER_SNAPSHOT","CURRENT_REQUEST","GOVERNED_ACTION","CURRENT_PAYMENT_CANDIDATE","ACTION_BINDING_FACT","RUNTIME_GATE_OBSERVATION","PAYMENT_EXECUTION_OUTCOME","STATUS_CONFLICT_FACT","FINAL_OUTCOME"],"events":[{"binding_alias_group":null,"entity_ref_template":"IntentMandate:{projection.mandate_id}","entity_role":"AUTHORITY","entity_type":"IntentMandate","event_type":"AUTHORITY_RECORDED","projection_schema":"intent-mandate-trace/v2","relations":[],"sequence_no":1,"source_binding_ref_required":true,"source_class":"IntentMandate","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"IntentMandate","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":"AUTHORIZED_CURRENT_ORDER_SHARED_BINDING","entity_ref_template":"Order:{projection.order_id}","entity_role":"AUTHORIZED_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":2,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":"AUTHORIZED_CURRENT_ORDER_SHARED_BINDING","entity_ref_template":"Order:{projection.order_id}","entity_role":"CURRENT_ORDER_SNAPSHOT","entity_type":"Order","event_type":"ORDER_RECORDED","projection_schema":"order-snapshot-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.mandate_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":3,"source_binding_ref_required":true,"source_class":"Order","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"Order","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"TransactionRequest:{projection.request_id}","entity_role":"CURRENT_REQUEST","entity_type":"TransactionRequest","event_type":"REQUEST_RECORDED","projection_schema":"transaction-request-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version_ref","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"}],"sequence_no":4,"source_binding_ref_required":true,"source_class":"TransactionRequest","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"TransactionRequest","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"GovernedPaymentAction:{projection.action_id}","entity_role":"GOVERNED_ACTION","entity_type":"GovernedPaymentAction","event_type":"ACTION_RECORDED","projection_schema":"governed-payment-action-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.authority_ref","target_binding_assertions":[{"source_path":"projection.authority_version","target_path":"projection.authority_version"}],"target_entity_ref_template":"IntentMandate:{value}","target_entity_role":"AUTHORITY","target_entity_type":"IntentMandate","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_ref","target_binding_assertions":[{"source_path":"projection.order_version","target_path":"projection.order_version"}],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_ref","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.payment_ref","target_binding_assertions":[],"target_entity_ref_template":"PaymentExecutionRecord:{value}","target_entity_role":"CURRENT_PAYMENT_CANDIDATE","target_entity_type":"PaymentExecutionRecord","value_mode":"SCALAR"}],"sequence_no":5,"source_binding_ref_required":true,"source_class":"GovernedPaymentAction","source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"GovernedPaymentAction","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":null}},{"binding_alias_group":null,"entity_ref_template":"PaymentExecutionRecord:{projection.payment_id}","entity_role":"CURRENT_PAYMENT_CANDIDATE","entity_type":"PaymentExecutionRecord","event_type":"PAYMENT_CANDIDATE_RECORDED","projection_schema":"payment-execution-record-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_id","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_id","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"}],"sequence_no":6,"source_binding_ref_required":true,"source_class":"PaymentExecutionRecord","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"PaymentExecutionRecord","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"GovernedActionBindingFact:binding:{binding_digest}","entity_role":"ACTION_BINDING_FACT","entity_type":"GovernedActionBindingFact","event_type":"ACTION_BINDING_DECISION_RECORDED","projection_schema":"governed-action-binding-fact-trace/v2","relations":[{"relation_type":"VALIDATED_AGAINST","source_assertion_path":"projection.action_id","target_binding_assertions":[],"target_entity_ref_template":"GovernedPaymentAction:{value}","target_entity_role":"GOVERNED_ACTION","target_entity_type":"GovernedPaymentAction","value_mode":"SCALAR"},{"relation_type":"VALIDATED_AGAINST","source_assertion_path":"projection.checked_payment_ref","target_binding_assertions":[],"target_entity_ref_template":"PaymentExecutionRecord:{value}","target_entity_role":"CURRENT_PAYMENT_CANDIDATE","target_entity_type":"PaymentExecutionRecord","value_mode":"SCALAR"}],"sequence_no":7,"source_binding_ref_required":true,"source_class":"GovernedActionBindingFact","source_module":"agentic_payment_experiment.trusted_execution.governed_action","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"GovernedActionBindingFact","value_paths":{"decision_path":null,"reason_codes_path":"projection.reason_codes","status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"RuntimeGateRecord:binding:{binding_digest}","entity_role":"RUNTIME_GATE_OBSERVATION","entity_type":"RuntimeGateRecord","event_type":"RUNTIME_DECISION_RECORDED","projection_schema":"runtime-gate-record-trace/v2","relations":[],"sequence_no":8,"source_binding_ref_required":true,"source_class":"RuntimeGateRecord","source_module":"agentic_payment_experiment.trusted_execution.replay","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"RuntimeGateRecord","value_paths":{"decision_path":"projection.final_decision","reason_codes_path":"projection.reason_codes","status_path":"projection.binding_status"}},{"binding_alias_group":null,"entity_ref_template":"PaymentExecutionRecord:{projection.payment_id}","entity_role":"PAYMENT_EXECUTION_OUTCOME","entity_type":"PaymentExecutionRecord","event_type":"PAYMENT_OUTCOME_RECORDED","projection_schema":"payment-execution-record-trace/v2","relations":[{"relation_type":"BOUND_TO","source_assertion_path":"projection.request_id","target_binding_assertions":[],"target_entity_ref_template":"TransactionRequest:{value}","target_entity_role":"CURRENT_REQUEST","target_entity_type":"TransactionRequest","value_mode":"SCALAR"},{"relation_type":"BOUND_TO","source_assertion_path":"projection.order_id","target_binding_assertions":[],"target_entity_ref_template":"Order:{value}","target_entity_role":"CURRENT_ORDER_SNAPSHOT","target_entity_type":"Order","value_mode":"SCALAR"}],"sequence_no":9,"source_binding_ref_required":true,"source_class":"PaymentExecutionRecord","source_module":"agentic_payment_experiment.models","source_object_ref_mode":"NATIVE_TEMPLATE","source_object_type":"PaymentExecutionRecord","value_paths":{"decision_path":null,"reason_codes_path":null,"status_path":"projection.status"}},{"binding_alias_group":null,"entity_ref_template":"PaymentStatusConflictFact:binding:{binding_digest}","entity_role":"STATUS_CONFLICT_FACT","entity_type":"PaymentStatusConflictFact","event_type":"STATUS_CONFLICT_RECORDED","projection_schema":"payment-status-conflict-fact-trace/v2","relations":[],"sequence_no":10,"source_binding_ref_required":true,"source_class":"PaymentStatusConflictFact","source_module":"agentic_payment_experiment.payment_status_conflict","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"PaymentStatusConflictFact","value_paths":{"decision_path":null,"reason_codes_path":"projection.reason_codes","status_path":"projection.resolution"}},{"binding_alias_group":null,"entity_ref_template":"WebShopPaymentFulfilmentOutcome:binding:{binding_digest}","entity_role":"FINAL_OUTCOME","entity_type":"WebShopPaymentFulfilmentOutcome","event_type":"RESULT_RECORDED","projection_schema":"webshop-payment-fulfilment-outcome-result-trace/v2","relations":[],"sequence_no":11,"source_binding_ref_required":true,"source_class":"WebShopPaymentFulfilmentOutcome","source_module":"agentic_payment_experiment.webshop_payment_sidecar","source_object_ref_mode":"PROJECTION_HASH_IDENTITY","source_object_type":"WebShopPaymentFulfilmentOutcome","value_paths":{"decision_path":null,"reason_codes_path":"projection.reason_codes","status_path":"projection.lifecycle_task_status"}}],"new_business_rule_required":false,"profile":"WEBSHOP_PAYMENT_STATUS_CONFLICT_V2","task_id":"T12","title":"终态冲突"}]}'
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

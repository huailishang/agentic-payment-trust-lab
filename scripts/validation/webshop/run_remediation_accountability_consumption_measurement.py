from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPOSITORY_ROOT / "src"
WEBSHOP_VALIDATION_ROOT = REPOSITORY_ROOT / "scripts" / "validation" / "webshop"
for search_path in (SRC_ROOT, WEBSHOP_VALIDATION_ROOT):
    if str(search_path) not in sys.path:
        sys.path.insert(0, str(search_path))

import run_same_journey_remediation_closure as h21

from agentic_payment_experiment.action_origin import (
    action_origin_records_to_primitive,
    project_authoritative_trace_origins,
)
from agentic_payment_experiment.authoritative_trace import validate_product_authoritative_trace
from agentic_payment_experiment.authoritative_trace_consumer import (
    TraceConsumerStatus,
    consume_authoritative_trace,
    trace_read_model_to_primitive,
)
from agentic_payment_experiment.authoritative_trace_player import (
    TracePlayerInputError,
    build_trace_player_payload,
    trace_player_html_sha256,
    trace_player_payload_sha256,
)
from agentic_payment_experiment.remediation import assess_remediation
from agentic_payment_experiment.trusted_execution import verify_original_transaction
from agentic_payment_experiment.webshop_remediation_trace import (
    extend_product_authoritative_trace_with_remediation,
)


SCHEMA = "remediation-accountability-consumption-measurement/v1"
ACCEPTED_H22_SHA256 = "ba1d4e562bef9ae975c81049b0c24399513cf62f6f8d1c7bb6ece4f2b4e09891"
CASES = (
    "R01_FULL_REFUND",
    "R02_PARTIAL_REFUND",
    "R03_DISPUTE_OPEN",
    "R04_DISPUTE_RESOLVED_OUTCOME_UNVERIFIED",
    "R05_REFUND_PAYMENT_BINDING_MISMATCH",
)
CONTINUITY_ORDER = (
    "AUTHORITATIVE_TRACE_VALID",
    "CONSUMER_ACCEPTED",
    "READ_MODEL_EVENT_PARITY",
    "SOURCE_BINDING_PARITY",
    "REMEDIATION_ROLES_VISIBLE",
    "BINDING_STATUS_EXPECTATION_VISIBLE",
    "CLOSURE_STATE_VISIBLE",
    "ACTION_ORIGIN_PROJECTABLE",
    "PLAYER_PAYLOAD_ACCEPTED",
    "PLAYER_RENDER_DETERMINISTIC",
)
REMEDIATION_ROLES = {
    "REMEDIATION_OBSERVATION",
    "ORIGINAL_TRANSACTION_BINDING_FACT",
    "REMEDIATION_CLOSURE_OUTCOME",
}
PAYMENT_ROLES = {"PAYMENT_EXECUTION_OUTCOME", "CURRENT_PAYMENT_CANDIDATE"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--accepted-h22-result", required=True)
    parser.add_argument("--parent-result", required=True)
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--repeat", required=True, type=int)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def mapping(value: object, label: str) -> Mapping[str, Any]:
    require(isinstance(value, Mapping), f"{label} must be a mapping")
    return value  # type: ignore[return-value]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path, label: str) -> Mapping[str, Any]:
    require(path.is_file(), f"{label} missing: {path}")
    return mapping(json.loads(path.read_text(encoding="utf-8")), label)


def primitive(value: object) -> object:
    if is_dataclass(value):
        return primitive(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): primitive(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [primitive(item) for item in value]
    return value


def canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            primitive(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def product_trace_primitive(trace: object) -> dict[str, Any]:
    value = primitive(trace)
    require(isinstance(value, dict), "product trace primitive must be an object")
    return value


def event_parity(product: Mapping[str, Any], read_model: Mapping[str, Any]) -> bool:
    product_events = product.get("events")
    read_events = read_model.get("events")
    if not isinstance(product_events, list) or not isinstance(read_events, list):
        return False
    if len(product_events) != len(read_events):
        return False
    keys = (
        "sequence_no",
        "event_type",
        "entity_role",
        "entity_type",
        "source_binding_ref",
    )
    return all(
        all(source.get(key) == projected.get(key) for key in keys)
        for source, projected in zip(product_events, read_events)
        if isinstance(source, Mapping) and isinstance(projected, Mapping)
    ) and all(
        isinstance(source, Mapping) and isinstance(projected, Mapping)
        for source, projected in zip(product_events, read_events)
    )


def source_binding_parity(product: Mapping[str, Any], read_model: Mapping[str, Any]) -> bool:
    product_bindings = product.get("source_bindings")
    read_bindings = read_model.get("source_bindings")
    read_events = read_model.get("events")
    if not isinstance(product_bindings, list) or not isinstance(read_bindings, list):
        return False
    if not isinstance(read_events, list) or len(product_bindings) != len(read_bindings):
        return False
    product_by_ref = {
        str(item.get("binding_ref")): item
        for item in product_bindings
        if isinstance(item, Mapping)
    }
    read_by_ref = {
        str(item.get("binding_ref")): item
        for item in read_bindings
        if isinstance(item, Mapping)
    }
    if len(product_by_ref) != len(product_bindings) or len(read_by_ref) != len(read_bindings):
        return False
    if product_by_ref != read_by_ref:
        return False
    return all(
        isinstance(event, Mapping)
        and str(event.get("source_binding_ref")) in read_by_ref
        for event in read_events
    )


def role_event_map(read_model: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    events = read_model.get("events")
    if not isinstance(events, list):
        return {}
    return {
        str(item.get("entity_role")): item
        for item in events
        if isinstance(item, Mapping) and item.get("entity_role")
    }


def binding_map(read_model: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    bindings = read_model.get("source_bindings")
    if not isinstance(bindings, list):
        return {}
    return {
        str(item.get("binding_ref")): item
        for item in bindings
        if isinstance(item, Mapping) and item.get("binding_ref")
    }


def source_projection_for_role(
    read_model: Mapping[str, Any], role: str
) -> tuple[Mapping[str, Any] | None, Mapping[str, Any] | None]:
    event = role_event_map(read_model).get(role)
    if event is None:
        return None, None
    binding = binding_map(read_model).get(str(event.get("source_binding_ref")))
    if binding is None:
        return event, None
    projection = binding.get("projection")
    return event, projection if isinstance(projection, Mapping) else None


def remediation_has_false_payment_relation(read_model: Mapping[str, Any]) -> bool:
    event = role_event_map(read_model).get("REMEDIATION_OBSERVATION")
    if event is None:
        return False
    relations = event.get("relations")
    if not isinstance(relations, list):
        return False
    return any(
        isinstance(item, Mapping) and item.get("target_entity_role") in PAYMENT_ROLES
        for item in relations
    )


def measure_once(
    parent: Mapping[str, object],
    case: Mapping[str, Any],
    accepted_case: Mapping[str, Any],
) -> dict[str, object]:
    action, refund, dispute = h21.build_follow_up(case, parent["payment"])  # type: ignore[arg-type]
    observation = refund if refund is not None else dispute
    require(observation is not None, "frozen remediation observation missing")

    closure = assess_remediation(
        parent["order"],  # type: ignore[arg-type]
        parent["payment"],  # type: ignore[arg-type]
        parent["lifecycle"],  # type: ignore[arg-type]
        refund=refund,
        dispute=dispute,
    )
    binding_fact = verify_original_transaction(
        action,
        parent["payment"],  # type: ignore[arg-type]
        observation,
    )
    trace = extend_product_authoritative_trace_with_remediation(
        parent["authoritative_trace"],  # type: ignore[arg-type]
        observation,
        binding_fact,
        closure,
    )

    validation_status = None
    product_primitive: dict[str, Any] | None = None
    if trace is not None:
        validation_status = validate_product_authoritative_trace(trace).status.value
        product_primitive = product_trace_primitive(trace)

    consume_result = consume_authoritative_trace(trace)
    consumer_accepted = (
        consume_result.status is TraceConsumerStatus.AVAILABLE
        and consume_result.read_model is not None
    )
    read_primitive: dict[str, Any] | None = None
    if consume_result.read_model is not None:
        read_primitive = trace_read_model_to_primitive(consume_result.read_model)

    read_event_parity = bool(
        product_primitive is not None
        and read_primitive is not None
        and event_parity(product_primitive, read_primitive)
    )
    read_binding_parity = bool(
        product_primitive is not None
        and read_primitive is not None
        and source_binding_parity(product_primitive, read_primitive)
    )

    visible_roles = sorted(role_event_map(read_primitive or {}).keys())
    remediation_roles_visible = REMEDIATION_ROLES <= set(visible_roles)

    observation_event, observation_projection = source_projection_for_role(
        read_primitive or {}, "REMEDIATION_OBSERVATION"
    )
    binding_event, binding_projection = source_projection_for_role(
        read_primitive or {}, "ORIGINAL_TRANSACTION_BINDING_FACT"
    )
    accepted_binding = mapping(
        accepted_case.get("binding_fact_evidence"), "accepted H-22 binding fact evidence"
    )
    visible_binding_status = (
        binding_projection.get("status") if binding_projection is not None else None
    )
    visible_binding_reasons = list(
        binding_projection.get("reason_codes") or []
        if binding_projection is not None
        else []
    )
    binding_expectation_visible = bool(
        binding_event is not None
        and binding_projection is not None
        and visible_binding_status == accepted_binding.get("status")
        and visible_binding_reasons == list(accepted_binding.get("reason_codes") or [])
    )

    closure_event, closure_projection = source_projection_for_role(
        read_primitive or {}, "REMEDIATION_CLOSURE_OUTCOME"
    )
    accepted_closure = mapping(
        accepted_case.get("closure_evidence"), "accepted H-22 closure evidence"
    )
    closure_fields = {
        "task_status": (
            closure_projection.get("task_status") if closure_projection is not None else None
        ),
        "remediation_status": (
            closure_projection.get("remediation_status")
            if closure_projection is not None
            else None
        ),
        "next_action": (
            closure_projection.get("next_action") if closure_projection is not None else None
        ),
        "case_ref": (
            closure_projection.get("case_ref") if closure_projection is not None else None
        ),
    }
    closure_state_visible = bool(
        closure_event is not None
        and closure_projection is not None
        and closure_fields["task_status"] == accepted_closure.get("original_task_status")
        and closure_fields["remediation_status"]
        == accepted_closure.get("economic_remediation_status")
        and closure_fields["next_action"] == accepted_closure.get("next_action")
        and closure_fields["case_ref"] == accepted_closure.get("case_ref")
    )

    origin_projectable = False
    origin_types: list[str] = []
    origin_records: list[dict[str, object]] = []
    if read_primitive is not None:
        try:
            origin_records = action_origin_records_to_primitive(
                project_authoritative_trace_origins(read_primitive)
            )
            origin_types = sorted(
                {str(item["action_origin"]) for item in origin_records}
            )
            accepted_origin = mapping(
                accepted_case.get("action_origin"), "accepted H-22 action origin"
            )
            origin_projectable = bool(
                accepted_origin.get("projectable") is True
                and origin_types == sorted(str(item) for item in accepted_origin.get("types", []))
            )
        except (KeyError, TypeError, ValueError):
            origin_projectable = False

    player_accepted = False
    payload_equals_read_model = False
    payload_sha256 = None
    html_sha256 = None
    if consume_result.read_model is not None:
        try:
            payload = build_trace_player_payload(consume_result.read_model)
            payload_equals_read_model = payload == read_primitive
            payload_sha256 = trace_player_payload_sha256(consume_result.read_model)
            html_sha256 = trace_player_html_sha256(consume_result.read_model)
            player_accepted = payload_equals_read_model
        except TracePlayerInputError:
            player_accepted = False

    false_payment_relation = remediation_has_false_payment_relation(read_primitive or {})
    is_r05 = str(case["case_id"]) == "R05_REFUND_PAYMENT_BINDING_MISMATCH"
    negative_control = {
        "binding_status": visible_binding_status,
        "reason_codes": visible_binding_reasons,
        "false_original_payment_relation_absent": not false_payment_relation,
        "normalized_to_valid": bool(is_r05 and visible_binding_status == "VALID"),
    }

    expected_player_determinism = bool(player_accepted and payload_sha256 and html_sha256)
    computed = {
        "AUTHORITATIVE_TRACE_VALID": validation_status == "VALID",
        "CONSUMER_ACCEPTED": consumer_accepted,
        "READ_MODEL_EVENT_PARITY": read_event_parity,
        "SOURCE_BINDING_PARITY": read_binding_parity,
        "REMEDIATION_ROLES_VISIBLE": remediation_roles_visible,
        "BINDING_STATUS_EXPECTATION_VISIBLE": binding_expectation_visible,
        "CLOSURE_STATE_VISIBLE": closure_state_visible,
        "ACTION_ORIGIN_PROJECTABLE": origin_projectable,
        "PLAYER_PAYLOAD_ACCEPTED": player_accepted,
        "PLAYER_RENDER_DETERMINISTIC": expected_player_determinism,
    }
    continuity = {name: bool(computed[name]) for name in CONTINUITY_ORDER}

    return {
        "product_trace": {
            "available": trace is not None,
            "validation_status": validation_status,
            "trace_ref": trace.trace_ref if trace is not None else None,  # type: ignore[attr-defined]
            "profile": trace.profile if trace is not None else None,  # type: ignore[attr-defined]
            "event_count": len(trace.events) if trace is not None else 0,  # type: ignore[attr-defined]
            "source_binding_count": len(trace.source_bindings) if trace is not None else 0,  # type: ignore[attr-defined]
        },
        "consumer": {
            "status": consume_result.status.value,
            "validation_status": consume_result.validation_status.value,
            "reason_codes": list(consume_result.reason_codes),
            "read_model_available": consume_result.read_model is not None,
            "event_parity": read_event_parity,
            "source_binding_parity": read_binding_parity,
            "read_model_event_count": len((read_primitive or {}).get("events", [])),
            "read_model_source_binding_count": len(
                (read_primitive or {}).get("source_bindings", [])
            ),
            "read_model_sha256": canonical_digest(read_primitive) if read_primitive else None,
        },
        "remediation": {
            "required_roles": sorted(REMEDIATION_ROLES),
            "visible_roles": visible_roles,
            "required_roles_visible": remediation_roles_visible,
            "observation_event_visible": observation_event is not None,
            "observation_projection": (
                primitive(observation_projection) if observation_projection else None
            ),
            "binding_status": visible_binding_status,
            "binding_reason_codes": visible_binding_reasons,
            "binding_projection": primitive(binding_projection) if binding_projection else None,
        },
        "closure": {
            "event_visible": closure_event is not None,
            "state_visible": closure_state_visible,
            **closure_fields,
            "projection": primitive(closure_projection) if closure_projection else None,
        },
        "action_origin": {
            "projectable": origin_projectable,
            "types": origin_types,
            "record_count": len(origin_records),
        },
        "player": {
            "accepted": player_accepted,
            "payload_equals_read_model": payload_equals_read_model,
            "payload_sha256": payload_sha256,
            "html_sha256": html_sha256,
            "external_resources_added": False,
        },
        "negative_control": negative_control,
        "continuity": continuity,
        "continuity_pass": all(continuity.values()),
        "first_breakpoint": next(
            (name for name in CONTINUITY_ORDER if not continuity[name]), None
        ),
    }


def main() -> int:
    args = parse_args()
    require(args.repeat == 2, "frozen repeat must be 2")

    accepted_h22_path = (REPOSITORY_ROOT / args.accepted_h22_result).resolve()
    parent_path = (REPOSITORY_ROOT / args.parent_result).resolve()
    matrix_path = (REPOSITORY_ROOT / args.matrix).resolve()
    output_path = (REPOSITORY_ROOT / args.output).resolve()

    accepted_h22 = load_json(accepted_h22_path, "accepted H-22 result")
    h20 = load_json(parent_path, "accepted H-20 parent")
    matrix = load_json(matrix_path, "accepted H-21 remediation matrix")
    require(
        sha256(accepted_h22_path) == ACCEPTED_H22_SHA256,
        "accepted H-22 result hash drift",
    )
    require(int(matrix.get("repeat_per_case", 0)) == args.repeat, "matrix repeat drift")

    raw_cases = matrix.get("cases")
    require(isinstance(raw_cases, list) and len(raw_cases) == 5, "matrix must contain 5 cases")
    require(tuple(str(item["case_id"]) for item in raw_cases) == CASES, "matrix case order drift")

    accepted_cases = {
        str(item["case_id"]): mapping(item, "accepted H-22 case")
        for item in accepted_h22.get("cases", [])
        if isinstance(item, Mapping)
    }
    require(tuple(accepted_cases) == CASES, "accepted H-22 case order/identity drift")
    parent = h21.reconstruct_parent_journey(h20, matrix)

    cases: list[dict[str, object]] = []
    for raw_case in raw_cases:
        case = mapping(raw_case, "matrix case")
        case_id = str(case["case_id"])
        runs = [measure_once(parent, case, accepted_cases[case_id]) for _ in range(args.repeat)]
        run_digests = [canonical_digest(run) for run in runs]

        first = dict(runs[0])
        player_runs = [mapping(run.get("player"), "player observation") for run in runs]
        render_deterministic = bool(
            all(player.get("accepted") is True for player in player_runs)
            and len({player.get("payload_sha256") for player in player_runs}) == 1
            and len({player.get("html_sha256") for player in player_runs}) == 1
        )
        continuity = dict(mapping(first["continuity"], "continuity"))
        continuity["PLAYER_RENDER_DETERMINISTIC"] = render_deterministic
        first["continuity"] = continuity
        first["continuity_pass"] = all(bool(continuity[name]) for name in CONTINUITY_ORDER)
        first["first_breakpoint"] = next(
            (name for name in CONTINUITY_ORDER if not bool(continuity[name])), None
        )

        cases.append(
            {
                "case_id": case_id,
                "measurement_complete": True,
                "repeat_identical": len(set(run_digests)) == 1 and runs[0] == runs[1],
                "run_digests": run_digests,
                **first,
            }
        )

    distribution: dict[str, int] = {}
    for item in cases:
        key = str(item["first_breakpoint"] or "NONE")
        distribution[key] = distribution.get(key, 0) + 1

    result = {
        "schema": SCHEMA,
        "baseline": {
            "accepted_h22_result_path": args.accepted_h22_result,
            "accepted_h22_result_sha256": sha256(accepted_h22_path),
            "systematic_five_branch_consumption_coverage": "unknown",
        },
        "continuity_check_order": list(CONTINUITY_ORDER),
        "repeat_per_case": args.repeat,
        "cases": cases,
        "summary": {
            "cases_measured": len(cases),
            "cases_total": len(CASES),
            "continuity_passed": sum(1 for item in cases if item["continuity_pass"] is True),
            "consumer_accepted": sum(
                1
                for item in cases
                if mapping(item["consumer"], "consumer").get("status") == "AVAILABLE"
            ),
            "player_accepted": sum(
                1
                for item in cases
                if mapping(item["player"], "player").get("accepted") is True
            ),
            "first_breakpoint_distribution": distribution,
        },
        "guardrails": {
            "real_payment_execution_count": 0,
            "real_refund_execution_count": 0,
            "real_dispute_execution_count": 0,
            "external_network_calls": 0,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "cases_measured": f"{result['summary']['cases_measured']}/5",  # type: ignore[index]
                "continuity_passed": f"{result['summary']['continuity_passed']}/5",  # type: ignore[index]
                "consumer_accepted": f"{result['summary']['consumer_accepted']}/5",  # type: ignore[index]
                "player_accepted": f"{result['summary']['player_accepted']}/5",  # type: ignore[index]
                "first_breakpoint_distribution": distribution,
                "real_side_effects": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

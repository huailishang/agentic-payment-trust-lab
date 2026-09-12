from __future__ import annotations

import argparse
import hashlib
import json
import sys
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
    consume_authoritative_trace,
    trace_read_model_to_primitive,
)
from agentic_payment_experiment.remediation import assess_remediation
from agentic_payment_experiment.trusted_execution import verify_original_transaction
from agentic_payment_experiment.webshop_remediation_trace import (
    extend_product_authoritative_trace_with_remediation,
)


SCHEMA = "same-journey-remediation-trace-closure-result/v1"
ACCEPTED_H21_SHA256 = "9d794317cc77753bb84e6b7b0ec3c6a441ff1d6a632753c782ba556c7fb4f8bb"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--accepted-h21-result", required=True)
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


def canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def observed_semantics(closure: object) -> dict[str, object]:
    return {
        "task_status": closure.task_status.value,  # type: ignore[attr-defined]
        "remediation_status": closure.remediation.status.value,  # type: ignore[attr-defined]
        "next_action": closure.remediation.next_action,  # type: ignore[attr-defined]
        "refund_status": (
            closure.refund_status.value  # type: ignore[attr-defined]
            if closure.refund_status is not None  # type: ignore[attr-defined]
            else None
        ),
        "dispute_status": (
            closure.dispute_status.value  # type: ignore[attr-defined]
            if closure.dispute_status is not None  # type: ignore[attr-defined]
            else None
        ),
        "issue_codes": [item.code for item in closure.issues],  # type: ignore[attr-defined]
    }


def project_extended_trace(trace: object | None) -> dict[str, object]:
    empty: dict[str, object] = {
        "extended_trace": {
            "available": False,
            "validation_status": None,
            "product_observed": False,
            "profile": None,
        },
        "remediation_observation": {
            "event_present": False,
            "source_object_type": None,
            "source_binding_ref": None,
            "original_payment_relation_asserted": False,
        },
        "binding_fact_evidence": {
            "event_present": False,
            "source_object_type": None,
            "source_binding_ref": None,
            "status": None,
            "reason_codes": [],
        },
        "closure_evidence": {
            "event_present": False,
            "source_object_type": None,
            "source_binding_ref": None,
            "state_explicit": False,
        },
        "action_origin": {"projectable": False, "types": []},
    }
    if trace is None:
        return empty

    validation = validate_product_authoritative_trace(trace)
    empty["extended_trace"] = {
        "available": True,
        "validation_status": validation.status.value,
        "product_observed": True,
        "profile": trace.profile,  # type: ignore[attr-defined]
        "trace_ref": trace.trace_ref,  # type: ignore[attr-defined]
        "event_count": len(trace.events),  # type: ignore[attr-defined]
    }
    consumed = consume_authoritative_trace(trace)
    if consumed.read_model is None:
        return empty
    primitive = trace_read_model_to_primitive(consumed.read_model)
    events = {
        str(item["entity_role"]): item
        for item in primitive["events"]
        if isinstance(item, Mapping)
    }
    bindings = {
        str(item["binding_ref"]): item
        for item in primitive["source_bindings"]
        if isinstance(item, Mapping)
    }

    observation = events.get("REMEDIATION_OBSERVATION")
    if observation is not None:
        binding = mapping(
            bindings.get(str(observation["source_binding_ref"])),
            "remediation observation binding",
        )
        relations = observation.get("relations") or []
        payment_relation_asserted = any(
            isinstance(item, Mapping)
            and item.get("target_entity_role")
            in {"CURRENT_PAYMENT_CANDIDATE", "PAYMENT_EXECUTION_OUTCOME"}
            for item in relations
        )
        empty["remediation_observation"] = {
            "event_present": True,
            "source_object_type": binding["source_object_type"],
            "source_binding_ref": observation["source_binding_ref"],
            "source_object_ref": binding["source_object_ref"],
            "original_payment_relation_asserted": payment_relation_asserted,
            "relations": relations,
        }

    binding_event = events.get("ORIGINAL_TRANSACTION_BINDING_FACT")
    if binding_event is not None:
        binding = mapping(
            bindings.get(str(binding_event["source_binding_ref"])),
            "original transaction binding fact source",
        )
        projection = mapping(binding.get("projection"), "binding fact projection")
        empty["binding_fact_evidence"] = {
            "event_present": True,
            "source_object_type": binding["source_object_type"],
            "source_binding_ref": binding_event["source_binding_ref"],
            "status": projection.get("status"),
            "reason_codes": list(projection.get("reason_codes") or []),
            "original_payment_ref": projection.get("original_payment_ref"),
            "follow_up_payment_ref": projection.get("follow_up_payment_ref"),
        }

    closure_event = events.get("REMEDIATION_CLOSURE_OUTCOME")
    if closure_event is not None:
        binding = mapping(
            bindings.get(str(closure_event["source_binding_ref"])),
            "remediation closure source",
        )
        projection = mapping(binding.get("projection"), "closure projection")
        state_explicit = bool(
            projection.get("task_status")
            and projection.get("remediation_status")
            and projection.get("next_action")
            and projection.get("case_ref")
        )
        empty["closure_evidence"] = {
            "event_present": True,
            "source_object_type": binding["source_object_type"],
            "source_binding_ref": closure_event["source_binding_ref"],
            "state_explicit": state_explicit,
            "original_task_status": projection.get("task_status"),
            "economic_remediation_status": projection.get("remediation_status"),
            "next_action": projection.get("next_action"),
            "case_ref": projection.get("case_ref"),
        }

    try:
        origins = action_origin_records_to_primitive(
            project_authoritative_trace_origins(primitive)
        )
        empty["action_origin"] = {
            "projectable": True,
            "types": sorted({str(item["action_origin"]) for item in origins}),
        }
    except (KeyError, TypeError, ValueError):
        empty["action_origin"] = {"projectable": False, "types": []}
    return empty


def measure_once(
    parent: Mapping[str, object],
    case: Mapping[str, Any],
    accepted_case: Mapping[str, Any],
    continuity_order: list[str],
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
    extended = extend_product_authoritative_trace_with_remediation(
        parent["authoritative_trace"],  # type: ignore[arg-type]
        observation,
        binding_fact,
        closure,
    )

    semantics = observed_semantics(closure)
    semantic_match = semantics == accepted_case.get("observed_semantics")
    accepted_binding = mapping(
        accepted_case.get("original_transaction_binding"),
        "accepted H-21 binding",
    )
    original_transaction_binding = {
        "observed_status": binding_fact.status.value,
        "expected_status": accepted_binding["expected_status"],
        "expectation_match": binding_fact.status.value == accepted_binding["expected_status"],
        "reason_codes": list(binding_fact.reason_codes),
        "payment_ref": binding_fact.follow_up_payment_ref,
        "order_ref": binding_fact.follow_up_order_ref,
    }
    trace_projection = project_extended_trace(extended)
    extended_trace = mapping(trace_projection["extended_trace"], "extended trace")
    remediation_observation = mapping(
        trace_projection["remediation_observation"], "remediation observation"
    )
    binding_fact_evidence = mapping(
        trace_projection["binding_fact_evidence"], "binding fact evidence"
    )
    closure_evidence = mapping(trace_projection["closure_evidence"], "closure evidence")
    action_origin = mapping(trace_projection["action_origin"], "action origin")

    accepted_refs = mapping(accepted_case.get("refs"), "accepted H-21 refs")
    refs = {
        "session_id": str(parent["session_id"]),
        "order_id": parent["order"].order_id,  # type: ignore[attr-defined]
        "request_id": parent["bound_request"].request_id,  # type: ignore[attr-defined]
        "payment_id": parent["payment"].payment_id,  # type: ignore[attr-defined]
    }
    trace_remediation_present = bool(
        remediation_observation.get("event_present")
        and binding_fact_evidence.get("event_present")
        and closure_evidence.get("event_present")
    )
    computed = {
        "PARENT_JOURNEY_IDENTITY": refs == {
            key: accepted_refs[key]
            for key in ("session_id", "order_id", "request_id", "payment_id")
        },
        "ORDER_REQUEST_PAYMENT_CONTINUITY": (
            refs["order_id"] == accepted_refs["order_id"]
            and refs["request_id"] == accepted_refs["request_id"]
            and refs["payment_id"] == accepted_refs["payment_id"]
        ),
        "REMEDIATION_SEMANTIC_EXPECTATION_MATCH": semantic_match,
        "ORIGINAL_TRANSACTION_BINDING_EXPECTATION_MATCH": original_transaction_binding[
            "expectation_match"
        ],
        "REMEDIATION_EVIDENCE_PRESENT": bool(
            remediation_observation.get("event_present")
        ),
        "AUTHORITATIVE_TRACE_AVAILABLE": extended_trace.get("available") is True,
        "AUTHORITATIVE_TRACE_VALID": extended_trace.get("validation_status") == "VALID",
        "TRACE_REMEDIATION_EVIDENCE_PRESENT": trace_remediation_present,
        "ACTION_ORIGIN_PROJECTABLE": action_origin.get("projectable") is True,
        "CLOSURE_STATE_EXPLICIT": closure_evidence.get("state_explicit") is True,
    }
    continuity = {name: bool(computed[name]) for name in continuity_order}
    first_breakpoint = next(
        (name for name in continuity_order if continuity[name] is False),
        None,
    )

    return {
        "semantic_match": semantic_match,
        "observed_semantics": semantics,
        "original_transaction_binding": original_transaction_binding,
        "refs": refs,
        "extended_trace": dict(extended_trace),
        "remediation_observation": dict(remediation_observation),
        "binding_fact_evidence": dict(binding_fact_evidence),
        "closure_evidence": dict(closure_evidence),
        "action_origin": dict(action_origin),
        "continuity": continuity,
        "continuity_pass": all(continuity.values()),
        "first_breakpoint": first_breakpoint,
    }


def main() -> int:
    args = parse_args()
    require(args.repeat == 2, "frozen repeat must be 2")

    h21_path = (REPOSITORY_ROOT / args.accepted_h21_result).resolve()
    parent_path = (REPOSITORY_ROOT / args.parent_result).resolve()
    matrix_path = (REPOSITORY_ROOT / args.matrix).resolve()
    output_path = (REPOSITORY_ROOT / args.output).resolve()

    accepted_h21 = load_json(h21_path, "accepted H-21 result")
    h20 = load_json(parent_path, "accepted H-20 parent")
    matrix = load_json(matrix_path, "frozen remediation matrix")
    require(sha256(h21_path) == ACCEPTED_H21_SHA256, "accepted H-21 result hash drift")
    require(int(matrix.get("repeat_per_case", 0)) == args.repeat, "matrix repeat drift")

    accepted_cases = {
        str(item["case_id"]): mapping(item, "accepted H-21 case")
        for item in accepted_h21.get("cases", [])
        if isinstance(item, Mapping)
    }
    before_present = sum(
        1
        for item in accepted_cases.values()
        if mapping(item.get("trace"), "accepted H-21 trace").get(
            "remediation_event_or_role_present"
        )
        is True
    )
    require(len(accepted_cases) == 5, "accepted H-21 case count drift")
    require(before_present == 0, "accepted H-21 trace-remediation baseline is not 0/5")

    parent = h21.reconstruct_parent_journey(h20, matrix)
    continuity_order = [str(item) for item in matrix.get("continuity_check_order", [])]
    require(len(continuity_order) == 10, "frozen continuity order must contain 10 checks")
    raw_cases = matrix.get("cases")
    require(isinstance(raw_cases, list) and len(raw_cases) == 5, "frozen matrix must contain 5 cases")

    cases: list[dict[str, object]] = []
    for raw_case in raw_cases:
        case = mapping(raw_case, "matrix case")
        case_id = str(case["case_id"])
        accepted_case = accepted_cases[case_id]
        runs = [
            measure_once(parent, case, accepted_case, continuity_order)
            for _ in range(args.repeat)
        ]
        digests = [canonical_digest(run) for run in runs]
        cases.append(
            {
                "case_id": case_id,
                "measurement_complete": True,
                "repeat_identical": len(set(digests)) == 1 and runs[0] == runs[1],
                "run_digests": digests,
                **runs[0],
            }
        )

    result = {
        "schema": SCHEMA,
        "baseline": {
            "accepted_h21_result_path": args.accepted_h21_result,
            "accepted_h21_result_sha256": sha256(h21_path),
            "trace_remediation_evidence_present": before_present,
            "cases_total": len(accepted_cases),
        },
        "repeat_per_case": args.repeat,
        "cases": cases,
        "summary": {
            "cases_measured": len(cases),
            "cases_total": len(raw_cases),
            "semantic_matches": sum(1 for item in cases if item["semantic_match"] is True),
            "binding_expectations_matched": sum(
                1
                for item in cases
                if item["original_transaction_binding"]["expectation_match"] is True  # type: ignore[index]
            ),
            "trace_remediation_evidence_present": sum(
                1
                for item in cases
                if item["continuity"]["TRACE_REMEDIATION_EVIDENCE_PRESENT"] is True  # type: ignore[index]
            ),
            "branch_continuity_passed": sum(
                1 for item in cases if item["continuity_pass"] is True
            ),
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
                "before_trace_remediation_evidence": f"{before_present}/5",
                "after_trace_remediation_evidence": f"{result['summary']['trace_remediation_evidence_present']}/5",  # type: ignore[index]
                "branch_continuity": f"{result['summary']['branch_continuity_passed']}/5",  # type: ignore[index]
                "semantic_matches": f"{result['summary']['semantic_matches']}/5",  # type: ignore[index]
                "binding_expectations": f"{result['summary']['binding_expectations_matched']}/5",  # type: ignore[index]
                "real_side_effects": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

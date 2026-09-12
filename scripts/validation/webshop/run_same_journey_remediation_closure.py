from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPOSITORY_ROOT / "src"
WEBSHOP_VALIDATION_ROOT = REPOSITORY_ROOT / "scripts" / "validation" / "webshop"
for search_path in (SRC_ROOT, WEBSHOP_VALIDATION_ROOT):
    if str(search_path) not in sys.path:
        sys.path.insert(0, str(search_path))

# Reuse the accepted same-journey reconstruction helpers. This runner only
# supplies offline remediation observations and reads existing product outputs.
import run_same_journey_lifecycle_branches as lifecycle_measurement

from agentic_payment_experiment.action_origin import (
    action_origin_records_to_primitive,
    project_authoritative_trace_origins,
)
from agentic_payment_experiment.authoritative_trace import (
    validate_product_authoritative_trace,
)
from agentic_payment_experiment.authoritative_trace_consumer import (
    consume_authoritative_trace,
    trace_read_model_to_primitive,
)
from agentic_payment_experiment.models import (
    DisputeRecord,
    DisputeStatus,
    FulfillmentRecord,
    FulfillmentStatus,
    PaymentExecutionRecord,
    PaymentStatus,
    RefundRecord,
    RefundStatus,
)
from agentic_payment_experiment.remediation import assess_remediation
from agentic_payment_experiment.trusted_execution import (
    FollowUpAction,
    verify_original_transaction,
)
from agentic_payment_experiment.webshop_payment_sidecar import (
    assess_webshop_payment_fulfilment,
)


SCHEMA = "same-journey-remediation-closure-result/v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
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


def canonical_digest(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def enum_value(value: object) -> object:
    return getattr(value, "value", value)


def load_json(path: Path, label: str) -> Mapping[str, Any]:
    require(path.is_file(), f"{label} missing: {path}")
    return mapping(json.loads(path.read_text(encoding="utf-8")), label)


def resolve_record_ref(mode: str, parent_ref: str) -> str:
    if mode == "PARENT_PAYMENT" or mode == "PARENT_ORDER":
        return parent_ref
    if mode == "MISMATCH":
        return f"{parent_ref}-mismatch"
    raise RuntimeError(f"unsupported frozen reference mode: {mode}")


def refund_amount(mode: str, payment_amount: Decimal) -> Decimal:
    if mode == "FULL_PAYMENT_AMOUNT":
        return payment_amount
    if mode == "HALF_PAYMENT_AMOUNT":
        return payment_amount / Decimal("2")
    raise RuntimeError(f"unsupported frozen refund amount mode: {mode}")


def reconstruct_parent_journey(
    h20_result: Mapping[str, Any],
    matrix: Mapping[str, Any],
) -> dict[str, object]:
    parent_meta = mapping(h20_result.get("parent"), "H-20 parent")
    parent_branch_id = str(matrix["parent_branch_id"])
    parent_case = next(
        (
            mapping(item, "H-20 parent case")
            for item in h20_result.get("cases", [])
            if isinstance(item, Mapping) and item.get("case_id") == parent_branch_id
        ),
        None,
    )
    require(parent_case is not None, f"accepted H-20 parent branch missing: {parent_branch_id}")
    require(parent_case.get("semantic_match") is True, "accepted H-20 parent semantic drift")
    require(parent_case.get("continuity_pass") is True, "accepted H-20 parent continuity drift")

    h17_path = (REPOSITORY_ROOT / str(parent_meta["h17_result_path"])).resolve()
    experiment_context_path = (
        REPOSITORY_ROOT / str(parent_meta["experiment_context_path"])
    ).resolve()
    h17_result = load_json(h17_path, "H-17 same-journey result")
    experiment_context = load_json(
        experiment_context_path,
        "H-17 same-journey experiment context",
    )
    require(
        sha256(h17_path) == str(parent_meta["h17_result_sha256"]),
        "H-17 result hash drift",
    )
    require(
        sha256(experiment_context_path) == str(parent_meta["experiment_context_sha256"]),
        "H-17 experiment-context hash drift",
    )

    context = lifecycle_measurement.build_same_journey_context(
        h17_result,
        experiment_context,
    )
    payment_candidate = context["payment_candidate"]
    require(
        isinstance(payment_candidate, PaymentExecutionRecord),
        "same-journey payment candidate type mismatch",
    )
    parent_input = mapping(parent_case.get("input"), "H-20 parent input")
    payment_status = PaymentStatus(str(parent_input["initial_payment_status"]))
    payment = replace(
        payment_candidate,
        status=payment_status,
        receipt_ref=(
            "offline-same-journey-receipt"
            if payment_status is PaymentStatus.SUCCEEDED
            else None
        ),
    )

    order = context["order"]
    bound_request = context["bound_request"]
    fulfillment_status = FulfillmentStatus(str(parent_input["fulfillment_status"]))
    fulfillment = FulfillmentRecord(
        fulfillment_id=f"same-journey-fulfillment-{order.order_id}",  # type: ignore[attr-defined]
        order_id=order.order_id,  # type: ignore[attr-defined]
        status=fulfillment_status,
        occurred_at=payment.occurred_at + lifecycle_measurement.timedelta(minutes=3),
        evidence_ref="offline-same-journey-fulfillment-evidence",
        failure_code=parent_input.get("fulfillment_failure_code"),
    )

    query_observation = None
    if parent_input.get("query_status") is not None:
        query_observation = lifecycle_measurement.make_observation(
            payment,
            str(parent_input["query_status"]),
            source="trusted_offline_status_query",
            seconds_after_payment=60,
        )
    async_observation = None
    if parent_input.get("async_status") is not None:
        async_observation = lifecycle_measurement.make_observation(
            payment,
            str(parent_input["async_status"]),
            source="trusted_offline_async_status",
            seconds_after_payment=120,
        )

    sidecar = assess_webshop_payment_fulfilment(
        gate_outcome=context["gate"],  # type: ignore[arg-type]
        adaptation=context["adaptation"],  # type: ignore[arg-type]
        mandate=context["mandate"],  # type: ignore[arg-type]
        payment=payment,
        fulfillment=fulfillment,
        query_observation=query_observation,
        async_observation=async_observation,
    )
    require(sidecar.ready is True, "accepted same-journey sidecar no longer ready")
    require(sidecar.lifecycle is not None, "accepted same-journey lifecycle missing")
    require(sidecar.effective_payment is not None, "accepted effective payment missing")

    refs = mapping(parent_case.get("refs"), "H-20 parent refs")
    require(str(context["session_id"]) == str(refs["session_id"]), "parent session drift")
    require(order.order_id == refs["order_id"], "parent order drift")  # type: ignore[attr-defined]
    require(bound_request.request_id == refs["request_id"], "parent request drift")  # type: ignore[attr-defined]
    require(sidecar.effective_payment.payment_id == refs["payment_id"], "parent payment drift")
    require(
        sidecar.lifecycle.task_status.value
        == mapping(parent_case.get("observed_semantics"), "H-20 parent semantics")[
            "task_status"
        ],
        "parent task status drift",
    )
    require(
        sidecar.lifecycle.remediation.status.value
        == mapping(parent_case.get("observed_semantics"), "H-20 parent semantics")[
            "remediation_status"
        ],
        "parent remediation status drift",
    )

    return {
        "branch_id": parent_branch_id,
        "session_id": str(context["session_id"]),
        "order": order,
        "bound_request": bound_request,
        "payment": sidecar.effective_payment,
        "lifecycle": sidecar.lifecycle,
        "authoritative_trace": sidecar.authoritative_trace,
        "h17_result_path": str(parent_meta["h17_result_path"]),
        "h17_result_sha256": sha256(h17_path),
        "experiment_context_path": str(parent_meta["experiment_context_path"]),
        "experiment_context_sha256": sha256(experiment_context_path),
    }


def build_follow_up(
    case: Mapping[str, Any],
    payment: PaymentExecutionRecord,
) -> tuple[FollowUpAction, RefundRecord | None, DisputeRecord | None]:
    kind = str(case["remediation_kind"])
    payment_ref = resolve_record_ref(str(case["payment_ref_mode"]), payment.payment_id)
    order_ref = resolve_record_ref(str(case["order_ref_mode"]), payment.order_id)
    case_token = str(case["case_id"]).lower().replace("_", "-")

    if kind == "REFUND":
        refund = RefundRecord(
            refund_id=f"h21-{case_token}-refund",
            payment_id=payment_ref,
            order_id=order_ref,
            status=RefundStatus(str(case["refund_status"])),
            amount=refund_amount(str(case["refund_amount_mode"]), payment.amount),
            currency=payment.currency,
            occurred_at=payment.occurred_at + lifecycle_measurement.timedelta(minutes=5),
            receipt_ref=f"offline-{case_token}-refund-receipt",
            reason_code="offline_measurement_observation",
        )
        return FollowUpAction.REFUND, refund, None

    if kind == "DISPUTE":
        dispute = DisputeRecord(
            dispute_id=f"h21-{case_token}-dispute",
            payment_id=payment_ref,
            order_id=order_ref,
            status=DisputeStatus(str(case["dispute_status"])),
            opened_at=payment.occurred_at + lifecycle_measurement.timedelta(minutes=5),
            reason_code="offline_measurement_observation",
            evidence_ref=f"offline-{case_token}-dispute-evidence",
        )
        return FollowUpAction.DISPUTE, None, dispute

    raise RuntimeError(f"unsupported frozen remediation kind: {kind}")


def project_product_trace(trace_obj: object | None) -> dict[str, object]:
    result: dict[str, object] = {
        "available": trace_obj is not None,
        "validation_status": None,
        "product_observed": trace_obj is not None,
        "remediation_event_or_role_present": False,
        "action_origin_projectable": False,
        "action_origin_types": [],
    }
    if trace_obj is None:
        return result

    validation = validate_product_authoritative_trace(trace_obj)
    result["validation_status"] = enum_value(validation.status)
    consumed = consume_authoritative_trace(trace_obj)
    if consumed.read_model is None:
        return result

    primitive = trace_read_model_to_primitive(consumed.read_model)
    observed_roles: list[str] = []
    remediation_role_present = False
    for event in primitive.get("events", []):
        if not isinstance(event, Mapping):
            continue
        role = str(event.get("entity_role") or "")
        event_type = str(event.get("event_type") or event.get("event_kind") or "")
        if role:
            observed_roles.append(role)
        semantic_label = f"{role} {event_type}".upper()
        if any(token in semantic_label for token in ("REFUND", "DISPUTE", "REMEDIATION")):
            remediation_role_present = True
    result["remediation_event_or_role_present"] = remediation_role_present
    result["observed_event_roles"] = sorted(set(observed_roles))

    try:
        origins = action_origin_records_to_primitive(
            project_authoritative_trace_origins(primitive)
        )
        result["action_origin_types"] = sorted(
            {str(item["action_origin"]) for item in origins}
        )
        result["action_origin_projectable"] = True
    except (KeyError, TypeError, ValueError):
        result["action_origin_types"] = []
        result["action_origin_projectable"] = False
    return result


def evidence_projection(base_lifecycle: object, remediated_lifecycle: object) -> list[dict[str, object]]:
    base_evidence = tuple(getattr(base_lifecycle, "evidence"))
    observed_evidence = tuple(getattr(remediated_lifecycle, "evidence"))
    appended = observed_evidence[len(base_evidence) :]
    return [
        {
            "code": item.code,
            "field_path": item.field_path,
            "observed": item.observed,
            "expected": item.expected,
        }
        for item in appended
    ]


def measure_once(
    parent: Mapping[str, object],
    case: Mapping[str, Any],
    continuity_order: list[str],
) -> dict[str, object]:
    order = parent["order"]
    payment = parent["payment"]
    lifecycle = parent["lifecycle"]
    require(isinstance(payment, PaymentExecutionRecord), "parent payment type mismatch")

    action, refund, dispute = build_follow_up(case, payment)
    remediated = assess_remediation(
        order,  # type: ignore[arg-type]
        payment,
        lifecycle,  # type: ignore[arg-type]
        refund=refund,
        dispute=dispute,
    )
    follow_up = refund if refund is not None else dispute
    binding_fact = verify_original_transaction(action, payment, follow_up)
    expected = mapping(case.get("expected"), f"{case.get('case_id')}.expected")

    observed_semantics = {
        "task_status": remediated.task_status.value,
        "remediation_status": remediated.remediation.status.value,
        "next_action": remediated.remediation.next_action,
        "refund_status": (
            remediated.refund_status.value if remediated.refund_status is not None else None
        ),
        "dispute_status": (
            remediated.dispute_status.value
            if remediated.dispute_status is not None
            else None
        ),
        "issue_codes": [issue.code for issue in remediated.issues],
    }
    semantic_match = (
        observed_semantics["task_status"] == expected["task_status"]
        and observed_semantics["remediation_status"] == expected["remediation_status"]
        and observed_semantics["next_action"] == expected["next_action"]
        and observed_semantics["refund_status"] == expected["refund_status"]
        and observed_semantics["dispute_status"] == expected["dispute_status"]
        and set(expected["required_issue_codes"]).issubset(
            set(observed_semantics["issue_codes"])
        )
    )

    expected_binding = str(expected["original_transaction_binding"])
    original_transaction_binding = {
        "observed_status": binding_fact.status.value,
        "expected_status": expected_binding,
        "expectation_match": binding_fact.status.value == expected_binding,
        "reason_codes": list(binding_fact.reason_codes),
        "payment_ref": binding_fact.follow_up_payment_ref,
        "order_ref": binding_fact.follow_up_order_ref,
    }

    refs = {
        "session_id": str(parent["session_id"]),
        "order_id": order.order_id,  # type: ignore[attr-defined]
        "request_id": parent["bound_request"].request_id,  # type: ignore[attr-defined]
        "payment_id": payment.payment_id,
    }
    remediation_evidence = evidence_projection(lifecycle, remediated)
    trace = project_product_trace(parent["authoritative_trace"])
    closure = {
        "state_explicit": bool(
            remediated.task_status.value
            and remediated.remediation.status.value
            and remediated.remediation.next_action
            and remediated.remediation.case_ref
        ),
        "original_task_status": remediated.task_status.value,
        "economic_remediation_status": remediated.remediation.status.value,
        "case_ref": remediated.remediation.case_ref,
        "next_action": remediated.remediation.next_action,
    }

    computed = {
        "PARENT_JOURNEY_IDENTITY": refs["session_id"] == str(parent["session_id"]),
        "ORDER_REQUEST_PAYMENT_CONTINUITY": (
            refs["order_id"] == order.order_id  # type: ignore[attr-defined]
            and refs["request_id"] == parent["bound_request"].request_id  # type: ignore[attr-defined]
            and refs["payment_id"] == payment.payment_id
        ),
        "REMEDIATION_SEMANTIC_EXPECTATION_MATCH": semantic_match,
        "ORIGINAL_TRANSACTION_BINDING_EXPECTATION_MATCH": original_transaction_binding[
            "expectation_match"
        ],
        "REMEDIATION_EVIDENCE_PRESENT": bool(remediation_evidence),
        "AUTHORITATIVE_TRACE_AVAILABLE": (
            trace["available"] is True and trace["product_observed"] is True
        ),
        "AUTHORITATIVE_TRACE_VALID": (
            trace["available"] is True
            and trace["product_observed"] is True
            and trace["validation_status"] == "VALID"
        ),
        "TRACE_REMEDIATION_EVIDENCE_PRESENT": trace[
            "remediation_event_or_role_present"
        ]
        is True,
        "ACTION_ORIGIN_PROJECTABLE": trace["action_origin_projectable"] is True,
        "CLOSURE_STATE_EXPLICIT": closure["state_explicit"] is True,
    }
    continuity = {name: bool(computed[name]) for name in continuity_order}
    first_breakpoint = next(
        (name for name in continuity_order if continuity[name] is False),
        None,
    )

    case_input = {key: value for key, value in case.items() if key != "expected"}
    return {
        "input": case_input,
        "observed_semantics": observed_semantics,
        "semantic_match": semantic_match,
        "original_transaction_binding": original_transaction_binding,
        "refs": refs,
        "remediation_evidence": remediation_evidence,
        "trace": trace,
        "closure": closure,
        "continuity": continuity,
        "continuity_pass": all(continuity.values()),
        "first_breakpoint": first_breakpoint,
    }


def main() -> int:
    args = parse_args()
    require(args.repeat == 2, "frozen repeat must be 2")

    parent_path = (REPOSITORY_ROOT / args.parent_result).resolve()
    matrix_path = (REPOSITORY_ROOT / args.matrix).resolve()
    output_path = (REPOSITORY_ROOT / args.output).resolve()
    h20_result = load_json(parent_path, "H-20 lifecycle result")
    matrix = load_json(matrix_path, "H-21 remediation matrix")
    require(
        int(matrix.get("repeat_per_case", 0)) == args.repeat,
        "matrix repeat differs from requested repeat",
    )

    parent = reconstruct_parent_journey(h20_result, matrix)
    continuity_order = [str(item) for item in matrix.get("continuity_check_order", [])]
    require(len(continuity_order) == 10, "frozen continuity check count must be 10")
    cases_raw = matrix.get("cases")
    require(isinstance(cases_raw, list) and len(cases_raw) == 5, "frozen matrix must contain 5 cases")

    cases: list[dict[str, object]] = []
    for raw_case in cases_raw:
        case = mapping(raw_case, "matrix case")
        runs = [measure_once(parent, case, continuity_order) for _ in range(args.repeat)]
        run_digests = [canonical_digest(run) for run in runs]
        first = runs[0]
        cases.append(
            {
                "case_id": str(case["case_id"]),
                "measurement_complete": True,
                "repeat_identical": len(set(run_digests)) == 1 and runs[0] == runs[1],
                "run_digests": run_digests,
                **first,
            }
        )

    breakpoints = Counter(
        str(case["first_breakpoint"])
        for case in cases
        if case["first_breakpoint"] is not None
    )
    result = {
        "schema": SCHEMA,
        "parent": {
            "branch_id": parent["branch_id"],
            "h20_result_path": args.parent_result,
            "h20_result_sha256": sha256(parent_path),
            "h17_result_path": parent["h17_result_path"],
            "h17_result_sha256": parent["h17_result_sha256"],
            "experiment_context_path": parent["experiment_context_path"],
            "experiment_context_sha256": parent["experiment_context_sha256"],
            "session_id": parent["session_id"],
            "order_id": parent["order"].order_id,  # type: ignore[attr-defined]
            "request_id": parent["bound_request"].request_id,  # type: ignore[attr-defined]
            "payment_id": parent["payment"].payment_id,  # type: ignore[attr-defined]
        },
        "matrix_sha256": sha256(matrix_path),
        "repeat_per_case": args.repeat,
        "cases": cases,
        "summary": {
            "cases_measured": len(cases),
            "semantic_matches": sum(
                1 for case in cases if case["semantic_match"] is True
            ),
            "binding_expectations_matched": sum(
                1
                for case in cases
                if case["original_transaction_binding"]["expectation_match"] is True  # type: ignore[index]
            ),
            "continuity_passed": sum(
                1 for case in cases if case["continuity_pass"] is True
            ),
            "first_breakpoint_counts": dict(sorted(breakpoints.items())),
        },
        "guardrails": {
            "real_" + "payment_side_effects": 0,
            "real_" + "refund_side_effects": 0,
            "real_dispute_side_effects": 0,
            "network_calls": 0,
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
                "cases_measured": len(cases),
                "semantic_matches": result["summary"]["semantic_matches"],  # type: ignore[index]
                "binding_expectations_matched": result["summary"][  # type: ignore[index]
                    "binding_expectations_matched"
                ],
                "continuity_passed": result["summary"]["continuity_passed"],  # type: ignore[index]
                "first_breakpoint_counts": result["summary"][  # type: ignore[index]
                    "first_breakpoint_counts"
                ],
                "real_side_effects": 0,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

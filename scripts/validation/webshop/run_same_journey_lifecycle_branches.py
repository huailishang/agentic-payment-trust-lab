from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPOSITORY_ROOT / "src"
WEBSHOP_VALIDATION_ROOT = REPOSITORY_ROOT / "scripts" / "validation" / "webshop"
for search_path in (SRC_ROOT, WEBSHOP_VALIDATION_ROOT):
    if str(search_path) not in sys.path:
        sys.path.insert(0, str(search_path))

# Reuse the frozen H-17 same-journey constructors instead of copying their
# authority/context/runtime-gate decisions into this measurement runner.
import run_same_journey_responsibility as same_journey

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
    FulfillmentRecord,
    FulfillmentStatus,
    PaymentExecutionRecord,
    PaymentStatus,
    PaymentStatusObservation,
)
from agentic_payment_experiment.payment_finality import derive_payment_query_finality
from agentic_payment_experiment.remediation import assess_remediation
from agentic_payment_experiment.webshop_payment_sidecar import (
    assess_webshop_payment_fulfilment,
)


SCHEMA = "same-journey-payment-lifecycle-branches/v1"
REQUIRED_ORIGINS = {
    "USER_AUTHORITY",
    "AGENT_DECISION",
    "RUNTIME_DECISION",
    "EXTERNAL_FACT",
    "EXECUTION_RESULT",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-result", required=True)
    parser.add_argument("--experiment-context", required=True)
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


def build_same_journey_context(
    parent: Mapping[str, Any],
    experiment_context: Mapping[str, Any],
) -> dict[str, object]:
    api = same_journey.product_imports()
    candidate = dict(mapping(parent.get("candidate"), "parent.candidate"))
    adaptation = api["adapt_webshop_purchase_candidate"](candidate)  # type: ignore[operator]
    require(
        adaptation.ready
        and adaptation.order is not None
        and adaptation.payment_request is not None,
        f"Commerce Adapter not ready: {adaptation.missing_fields}",
    )
    order = adaptation.order

    authority = mapping(experiment_context.get("authority"), "experiment_context.authority")
    runtime_identity = mapping(
        experiment_context.get("runtime_identity"),
        "experiment_context.runtime_identity",
    )
    offline_execution = mapping(
        experiment_context.get("offline_execution"),
        "experiment_context.offline_execution",
    )
    agent_id = str(authority["expected_agent_id"])
    bound_request = replace(adaptation.payment_request, agent_id=agent_id)

    IntentMandate = api["IntentMandate"]
    mandate = IntentMandate(  # type: ignore[operator]
        mandate_id=str(authority["mandate_id"]),
        user_id=str(authority["user_id"]),
        max_amount=Decimal(str(authority["max_amount"])),
        allowed_merchants=frozenset({order.merchant}),
        allowed_categories=frozenset({bound_request.category}),
        expires_at=same_journey.iso_datetime(
            authority["expires_at"], "authority.expires_at"
        ),
        max_count=int(authority["max_count"]),
        expected_agent_id=agent_id,
        currency=str(authority["currency"]),
        authority_version=str(authority["authority_version"]),
    )

    AgentIdentity = api["AgentIdentity"]
    identity = AgentIdentity(  # type: ignore[operator]
        agent_id=agent_id,
        provider=str(runtime_identity["provider"]),
        executor_instance_id=str(runtime_identity["executor_instance_id"]),
        status="active",
        credential_ref=str(runtime_identity["credential_ref"]),
    )

    payment_candidate = PaymentExecutionRecord(
        payment_id=f"same-journey-payment-{bound_request.request_id}",
        request_id=bound_request.request_id,
        order_id=order.order_id,
        status=PaymentStatus.PENDING,
        amount=bound_request.amount,
        currency=bound_request.currency,
        occurred_at=bound_request.occurred_at + timedelta(seconds=1),
        provider_ref=str(runtime_identity["provider"]),
        idempotency_key=f"same-journey:{bound_request.request_id}",
        authority_ref=mandate.mandate_id,
        agent_ref=agent_id,
        transaction_object_ref=bound_request.request_id,
        payee=order.payee,
    )

    policy_fact = same_journey.make_context_fact(
        mandate,
        order,
        bound_request,
        api,
    )
    GovernedPaymentAction = api["GovernedPaymentAction"]
    GovernedActionType = api["GovernedActionType"]
    SideEffectClass = api["SideEffectClass"]
    ActionReversibility = api["ActionReversibility"]
    governed_action = GovernedPaymentAction(  # type: ignore[operator]
        action_id=f"same-journey-action-{bound_request.request_id}",
        action_type=GovernedActionType.EXECUTE_PAYMENT,
        subject_ref=mandate.user_id,
        agent_ref=agent_id,
        executor_ref=str(runtime_identity["executor_instance_id"]),
        authority_ref=mandate.mandate_id,
        authority_version=mandate.authority_version,
        order_ref=order.order_id,
        order_version=order.order_version,
        request_ref=bound_request.request_id,
        payment_ref=payment_candidate.payment_id,
        source_refs=(
            "source:same-journey-webshop-runtime",
            "source:same-journey-explicit-authority",
        ),
        side_effect_class=SideEffectClass.PAYMENT_EXECUTION,
        reversibility=ActionReversibility.COMPENSATABLE_NOT_REVERSIBLE,
        occurred_at=bound_request.occurred_at + timedelta(milliseconds=500),
    )

    confirmation = api["create_confirmation_record"](  # type: ignore[operator]
        confirmation_id=f"same-journey-confirmation-{bound_request.request_id}",
        authority_id=mandate.mandate_id,
        authority_version=mandate.authority_version,
        order=order,
        confirmed_at=bound_request.occurred_at - timedelta(minutes=1),
        expires_at=bound_request.occurred_at + timedelta(minutes=30),
    )

    callback_calls: list[str] = []

    def offline_checkout_seam() -> str:
        callback_calls.append("offline_checkout_seam")
        return str(offline_execution["callback_result_ref"])

    gate = api["gate_webshop_buy_now"](  # type: ignore[operator]
        adaptation=adaptation,
        mandate=mandate,
        declared_agent_id=agent_id,
        execution_candidate=payment_candidate,
        agent_identity=identity,
        current_provider_ref=str(runtime_identity["provider"]),
        current_executor_instance_ref=str(runtime_identity["executor_instance_id"]),
        current_credential_ref=str(runtime_identity["credential_ref"]),
        context_policy_fact=policy_fact,
        checkout_callback=offline_checkout_seam,
        confirmation_record=confirmation,
        authorized_adaptation=adaptation,
        governed_action=governed_action,
    )
    require(enum_value(gate.decision) == "ALLOW", f"Runtime Gate blocked: {gate.reason_codes}")
    require(gate.bound_request is not None, "Runtime Gate bound request missing")
    require(
        gate.callback_count == 1 and callback_calls == ["offline_checkout_seam"],
        "offline callback seam count mismatch",
    )
    require(
        gate.callback_result_ref == offline_execution["callback_result_ref"],
        "offline callback seam ref mismatch",
    )

    return {
        "api": api,
        "candidate": candidate,
        "adaptation": adaptation,
        "order": order,
        "bound_request": bound_request,
        "mandate": mandate,
        "payment_candidate": payment_candidate,
        "gate": gate,
        "session_id": str(candidate["session_id"]),
    }


def make_observation(
    payment: PaymentExecutionRecord,
    status: str,
    *,
    source: str,
    seconds_after_payment: int,
) -> PaymentStatusObservation:
    return PaymentStatusObservation(
        payment_id=payment.payment_id,
        order_id=payment.order_id,
        status=PaymentStatus(status),
        observed_at=payment.occurred_at + timedelta(seconds=seconds_after_payment),
        source=source,
        provider_ref=payment.provider_ref,
    )


def finality_projection(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    raw = value.to_dict()  # type: ignore[attr-defined]
    keys = (
        "evidence_stage",
        "effective_status",
        "effective_status_terminal",
        "business_success_confirmed",
        "fulfillment_confirmed",
        "user_task_success_confirmed",
        "reconciliation_confirmed",
        "settlement_confirmed",
        "legal_finality_confirmed",
    )
    return {key: raw[key] for key in keys}


def extract_trace(trace_obj: object | None) -> dict[str, object]:
    trace = {
        "available": trace_obj is not None,
        "validation_status": None,
        "order_id": None,
        "request_id": None,
        "payment_id": None,
        "action_origin_projectable": False,
        "action_origin_types": [],
    }
    if trace_obj is None:
        return trace

    validation = validate_product_authoritative_trace(trace_obj)
    trace["validation_status"] = enum_value(validation.status)
    consumed = consume_authoritative_trace(trace_obj)
    if consumed.read_model is None:
        return trace

    primitive = trace_read_model_to_primitive(consumed.read_model)
    by_role = {
        str(event.get("entity_role")): event
        for event in primitive.get("events", [])
        if isinstance(event, Mapping)
    }

    def ref(role: str, prefix: str) -> str | None:
        event = by_role.get(role)
        if not isinstance(event, Mapping):
            return None
        entity_ref = event.get("entity_ref")
        if not isinstance(entity_ref, str) or not entity_ref.startswith(prefix):
            return None
        return entity_ref[len(prefix) :]

    trace["order_id"] = ref("CURRENT_ORDER_SNAPSHOT", "Order:")
    trace["request_id"] = ref("CURRENT_REQUEST", "TransactionRequest:")
    trace["payment_id"] = ref(
        "PAYMENT_EXECUTION_OUTCOME", "PaymentExecutionRecord:"
    )

    try:
        origins = action_origin_records_to_primitive(
            project_authoritative_trace_origins(primitive)
        )
        origin_types = sorted({str(item["action_origin"]) for item in origins})
        trace["action_origin_types"] = origin_types
        trace["action_origin_projectable"] = True
    except (KeyError, TypeError, ValueError):
        trace["action_origin_types"] = []
        trace["action_origin_projectable"] = False
    return trace


def measure_once(
    context: Mapping[str, object],
    case: Mapping[str, Any],
    parent_expected: Mapping[str, Any],
    continuity_order: list[str],
) -> dict[str, object]:
    case_input = mapping(case.get("input"), f"{case.get('case_id')}.input")
    payment_candidate = context["payment_candidate"]
    require(
        isinstance(payment_candidate, PaymentExecutionRecord),
        "payment candidate type mismatch",
    )
    payment_status = PaymentStatus(str(case_input["initial_payment_status"]))
    payment = replace(
        payment_candidate,
        status=payment_status,
        receipt_ref=(
            "offline-same-journey-receipt"
            if payment_status is PaymentStatus.SUCCEEDED
            else None
        ),
    )

    fulfillment_status = FulfillmentStatus(str(case_input["fulfillment_status"]))
    order = context["order"]
    bound_request = context["bound_request"]
    mandate = context["mandate"]
    gate = context["gate"]
    adaptation = context["adaptation"]
    fulfillment = FulfillmentRecord(
        fulfillment_id=f"same-journey-fulfillment-{order.order_id}",  # type: ignore[attr-defined]
        order_id=order.order_id,  # type: ignore[attr-defined]
        status=fulfillment_status,
        occurred_at=payment.occurred_at + timedelta(minutes=3),
        evidence_ref="offline-same-journey-fulfillment-evidence",
        failure_code=case_input.get("fulfillment_failure_code"),
    )

    query_observation = None
    if case_input.get("query_status") is not None:
        query_observation = make_observation(
            payment,
            str(case_input["query_status"]),
            source="trusted_offline_status_query",
            seconds_after_payment=60,
        )
    async_observation = None
    if case_input.get("async_status") is not None:
        async_observation = make_observation(
            payment,
            str(case_input["async_status"]),
            source="trusted_offline_async_status",
            seconds_after_payment=120,
        )

    sidecar = assess_webshop_payment_fulfilment(
        gate_outcome=gate,  # type: ignore[arg-type]
        adaptation=adaptation,  # type: ignore[arg-type]
        mandate=mandate,  # type: ignore[arg-type]
        payment=payment,
        fulfillment=fulfillment,
        query_observation=query_observation,
        async_observation=async_observation,
    )

    finality = None
    if query_observation is not None and sidecar.query_recovery is not None:
        finality = derive_payment_query_finality(
            payment,
            query_observation,
            sidecar.query_recovery,
        )

    lifecycle = sidecar.lifecycle
    remediated_lifecycle = None
    if lifecycle is not None and sidecar.effective_payment is not None:
        remediated_lifecycle = assess_remediation(
            order,  # type: ignore[arg-type]
            sidecar.effective_payment,
            lifecycle,
        )

    observed_semantics = {
        "sidecar_ready": bool(sidecar.ready),
        "effective_payment_status": (
            sidecar.effective_payment.status.value
            if sidecar.effective_payment is not None
            else None
        ),
        "query_recovery_status": (
            sidecar.query_recovery.recovery_status.value
            if sidecar.query_recovery is not None
            else None
        ),
        "status_conflict_resolution": (
            sidecar.status_conflict.resolution.value
            if sidecar.status_conflict is not None
            else None
        ),
        "task_status": (
            remediated_lifecycle.task_status.value
            if remediated_lifecycle is not None
            else None
        ),
        "remediation_status": (
            remediated_lifecycle.remediation.status.value
            if remediated_lifecycle is not None
            else None
        ),
        "retry_allowed": bool(sidecar.retry_allowed),
        "payment_query_finality": finality_projection(finality),
    }
    semantic_match = observed_semantics == case.get("expected_semantics")

    refs = {
        "session_id": context["session_id"],
        "order_id": order.order_id,  # type: ignore[attr-defined]
        "request_id": bound_request.request_id,  # type: ignore[attr-defined]
        "payment_id": payment.payment_id,
        "payment_order_id": payment.order_id,
        "payment_request_id": payment.request_id,
    }
    trace = extract_trace(sidecar.authoritative_trace)
    origin_types = {str(item) for item in trace["action_origin_types"]}  # type: ignore[union-attr]
    computed = {
        "PARENT_JOURNEY_IDENTITY": refs["session_id"] == parent_expected["session_id"],
        "ORDER_REQUEST_CONTINUITY": refs["order_id"] == parent_expected["order_id"]
        and refs["request_id"] == parent_expected["request_id"],
        "PAYMENT_ORDER_REQUEST_CONTINUITY": refs["payment_id"]
        == parent_expected["payment_id"]
        and refs["payment_order_id"] == refs["order_id"]
        and refs["payment_request_id"] == refs["request_id"],
        "SEMANTIC_EXPECTATION_MATCH": semantic_match,
        "AUTHORITATIVE_TRACE_AVAILABLE": trace["available"] is True,
        "AUTHORITATIVE_TRACE_VALID": trace["validation_status"] == "VALID",
        "TRACE_ORDER_REQUEST_PAYMENT_CONTINUITY": trace["order_id"] == refs["order_id"]
        and trace["request_id"] == refs["request_id"]
        and trace["payment_id"] == refs["payment_id"],
        "ACTION_ORIGIN_PROJECTABLE": trace["action_origin_projectable"] is True
        and REQUIRED_ORIGINS.issubset(origin_types),
    }
    continuity = {key: bool(computed[key]) for key in continuity_order}
    continuity_pass = all(continuity.values())
    failed = [key for key in continuity_order if continuity[key] is False]

    return {
        "observed_semantics": observed_semantics,
        "semantic_match": semantic_match,
        "refs": refs,
        "trace": trace,
        "continuity": continuity,
        "continuity_pass": continuity_pass,
        "first_breakpoint": None if not failed else failed[0],
    }


def main() -> int:
    args = parse_args()
    require(args.repeat == 2, "frozen repeat must be 2")

    parent_path = (REPOSITORY_ROOT / args.parent_result).resolve()
    context_path = (REPOSITORY_ROOT / args.experiment_context).resolve()
    matrix_path = (REPOSITORY_ROOT / args.matrix).resolve()
    output_path = (REPOSITORY_ROOT / args.output).resolve()

    parent = mapping(json.loads(parent_path.read_text(encoding="utf-8")), "parent result")
    experiment_context = mapping(
        json.loads(context_path.read_text(encoding="utf-8")),
        "experiment context",
    )
    matrix = mapping(json.loads(matrix_path.read_text(encoding="utf-8")), "matrix")
    parent_expected = mapping(matrix.get("parent"), "matrix.parent")
    require(
        sha256(parent_path) == parent_expected["h17_result_sha256"],
        "H-17 parent result hash mismatch",
    )
    require(
        int(matrix.get("repeat_per_case", 0)) == args.repeat,
        "matrix repeat differs from requested repeat",
    )

    context = build_same_journey_context(parent, experiment_context)
    order = context["order"]
    bound_request = context["bound_request"]
    payment_candidate = context["payment_candidate"]
    candidate = mapping(parent.get("candidate"), "parent.candidate")
    product = mapping(candidate.get("product"), "parent.candidate.product")
    selected_options = mapping(product.get("selected_options"), "parent selected options")
    require(str(context["session_id"]) == str(parent_expected["session_id"]), "parent session mismatch")
    require(order.order_id == parent_expected["order_id"], "parent order mismatch")  # type: ignore[attr-defined]
    require(
        bound_request.request_id == parent_expected["request_id"],  # type: ignore[attr-defined]
        "parent request mismatch",
    )
    require(
        payment_candidate.payment_id == parent_expected["payment_id"],  # type: ignore[attr-defined]
        "parent payment mismatch",
    )
    require(str(product["asin"]).upper() == parent_expected["selected_asin"], "parent ASIN mismatch")
    require(
        parent_expected["selected_option"] in {str(value) for value in selected_options.values()},
        "parent option mismatch",
    )
    require(str(product["order_total"]) == parent_expected["selected_price"], "parent price mismatch")

    continuity_order = [str(item) for item in matrix.get("continuity_checks", [])]
    require(len(continuity_order) == 8, "frozen continuity check count must be 8")
    cases_raw = matrix.get("cases")
    require(isinstance(cases_raw, list) and len(cases_raw) == 4, "frozen matrix must contain 4 cases")

    cases: list[dict[str, object]] = []
    for raw_case in cases_raw:
        case = mapping(raw_case, "matrix case")
        runs = [
            measure_once(context, case, parent_expected, continuity_order)
            for _ in range(args.repeat)
        ]
        run_digests = [canonical_digest(run) for run in runs]
        first = runs[0]
        case_result = {
            "case_id": str(case["case_id"]),
            "input": dict(mapping(case["input"], "case.input")),
            "measurement_complete": True,
            "repeat_identical": len(set(run_digests)) == 1 and runs[0] == runs[1],
            "run_digests": run_digests,
            **first,
        }
        cases.append(case_result)

    semantic_matches = sum(1 for case in cases if case["semantic_match"] is True)
    continuity_passed = sum(1 for case in cases if case["continuity_pass"] is True)
    result = {
        "schema": SCHEMA,
        "parent": {
            "h17_result_path": args.parent_result,
            "h17_result_sha256": sha256(parent_path),
            "experiment_context_path": args.experiment_context,
            "experiment_context_sha256": sha256(context_path),
            "session_id": str(context["session_id"]),
            "order_id": order.order_id,  # type: ignore[attr-defined]
            "request_id": bound_request.request_id,  # type: ignore[attr-defined]
            "payment_id": payment_candidate.payment_id,  # type: ignore[attr-defined]
            "selected_asin": str(product["asin"]).upper(),
            "selected_option": str(next(iter(selected_options.values()))),
            "selected_price": str(product["order_total"]),
        },
        "repeat_per_case": args.repeat,
        "cases": cases,
        "summary": {
            "cases_measured": len(cases),
            "cases_total": len(cases_raw),
            "semantic_matches": semantic_matches,
            "semantic_total": len(cases_raw),
            "branch_continuity_passed": continuity_passed,
            "branch_continuity_total": len(cases_raw),
        },
        "guardrails": {
            "real_webshop_buy_now_count": 0,
            "real_payment_execution_count": 0,
            "real_fulfillment_execution_count": 0,
            "external_network_calls": 0,
            "counterfactual_branches_reported_as_real_transactions": False,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "cases_measured": len(cases),
                "semantic_matches": semantic_matches,
                "branch_continuity_passed": continuity_passed,
                "first_breakpoints": {
                    case["case_id"]: case["first_breakpoint"] for case in cases
                },
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

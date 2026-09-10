from __future__ import annotations

import json
import sys
from pathlib import Path

EXPECTED_CASES = (
    "J01_SUCCESS_FULFILLED",
    "J02_UNKNOWN_QUERY_SUCCEEDED",
    "J03_PAYMENT_SUCCEEDED_FULFILLMENT_FAILED",
    "J04_QUERY_ASYNC_TERMINAL_CONFLICT",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    require(len(sys.argv) == 2, "usage: h20_result_audit.py <result.json>")
    path = Path(sys.argv[1])
    require(path.is_file(), f"result missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))

    require(data.get("schema") == "same-journey-payment-lifecycle-branches/v1", "unexpected result schema")
    require(data.get("repeat_per_case") == 2, "repeat_per_case must remain 2")
    cases = data.get("cases")
    require(type(cases) is list and len(cases) == 4, "expected four lifecycle cases")
    require(tuple(case.get("case_id") for case in cases) == EXPECTED_CASES, "case identity/order changed")

    for case in cases:
        case_id = case["case_id"]
        require(case.get("measurement_complete") is True, f"{case_id}: measurement incomplete")
        require(case.get("repeat_identical") is True, f"{case_id}: repeats not identical")
        digests = case.get("run_digests")
        require(type(digests) is list and len(digests) == 2 and digests[0] == digests[1], f"{case_id}: expected two identical digests")
        require(case.get("semantic_match") is True, f"{case_id}: lifecycle semantic regression")
        require(case.get("continuity_pass") is True, f"{case_id}: evidence continuity not closed")
        require(case.get("first_breakpoint") is None, f"{case_id}: first_breakpoint must be null")

        continuity = case.get("continuity") or {}
        expected_flags = (
            "PARENT_JOURNEY_IDENTITY",
            "ORDER_REQUEST_CONTINUITY",
            "PAYMENT_ORDER_REQUEST_CONTINUITY",
            "SEMANTIC_EXPECTATION_MATCH",
            "AUTHORITATIVE_TRACE_AVAILABLE",
            "AUTHORITATIVE_TRACE_VALID",
            "TRACE_ORDER_REQUEST_PAYMENT_CONTINUITY",
            "ACTION_ORIGIN_PROJECTABLE",
        )
        require(tuple(continuity.keys()) == expected_flags or set(continuity.keys()) == set(expected_flags), f"{case_id}: continuity contract changed")
        for flag in expected_flags:
            require(continuity.get(flag) is True, f"{case_id}: continuity flag false: {flag}")

        trace = case.get("trace") or {}
        refs = case.get("refs") or {}
        require(trace.get("available") is True, f"{case_id}: authoritative trace unavailable")
        require(trace.get("validation_status") == "VALID", f"{case_id}: authoritative trace not VALID")
        require(trace.get("order_id") == refs.get("order_id"), f"{case_id}: trace/order mismatch")
        require(trace.get("request_id") == refs.get("request_id"), f"{case_id}: trace/request mismatch")
        require(trace.get("payment_id") == refs.get("payment_id"), f"{case_id}: trace/payment mismatch")
        require(trace.get("action_origin_projectable") is True, f"{case_id}: Action Origin still not projectable")
        origin_types = trace.get("action_origin_types")
        require(type(origin_types) is list and origin_types, f"{case_id}: action_origin_types missing")

    summary = data.get("summary") or {}
    require(summary.get("cases_measured") == 4 and summary.get("cases_total") == 4, "case summary must remain 4/4")
    require(summary.get("semantic_matches") == 4 and summary.get("semantic_total") == 4, "semantic summary must be 4/4")
    require(summary.get("branch_continuity_passed") == 4 and summary.get("branch_continuity_total") == 4, "H-20 target is branch continuity 4/4")

    guardrails = data.get("guardrails") or {}
    require(guardrails.get("real_webshop_buy_now_count") == 0, "real Buy Now side effect detected")
    require(guardrails.get("real_payment_execution_count") == 0, "real payment side effect detected")
    require(guardrails.get("real_fulfillment_execution_count") == 0, "real fulfillment side effect detected")
    require(guardrails.get("external_network_calls") == 0, "external network side effect detected")
    require(guardrails.get("counterfactual_branches_reported_as_real_transactions") is False, "counterfactual branches misrepresented as real transactions")

    print("PASS: frozen same-journey lifecycle semantics remain 4/4 and lifecycle evidence continuity closes from 1/4 to 4/4 with VALID traces, projectable Action Origin, and zero real side effects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

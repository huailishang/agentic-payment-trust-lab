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
    require(len(sys.argv) == 2, "usage: h19_result_audit.py <result.json>")
    path = Path(sys.argv[1])
    require(path.is_file(), f"result missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))

    require(data.get("schema") == "same-journey-payment-lifecycle-branches/v1", "unexpected result schema")
    require(data.get("repeat_per_case") == 2, "repeat_per_case must remain 2")
    cases = data.get("cases")
    require(type(cases) is list and len(cases) == 4, "expected four cases")
    require(tuple(case.get("case_id") for case in cases) == EXPECTED_CASES, "case order/identity changed")
    by_id = {case["case_id"]: case for case in cases}

    for case_id, case in by_id.items():
        require(case.get("measurement_complete") is True, f"{case_id}: measurement incomplete")
        require(case.get("repeat_identical") is True, f"{case_id}: repeats differ")
        digests = case.get("run_digests")
        require(type(digests) is list and len(digests) == 2 and digests[0] == digests[1], f"{case_id}: expected two identical digests")
        require(case.get("semantic_match") is True, f"{case_id}: semantic regression")

    j01 = by_id["J01_SUCCESS_FULFILLED"]
    require(j01.get("continuity_pass") is True, "J01 continuity regressed")
    require(j01.get("first_breakpoint") is None, "J01 gained a breakpoint")

    for case_id in ("J02_UNKNOWN_QUERY_SUCCEEDED", "J04_QUERY_ASYNC_TERMINAL_CONFLICT"):
        case = by_id[case_id]
        trace = case.get("trace") or {}
        continuity = case.get("continuity") or {}
        require(trace.get("available") is True, f"{case_id}: authoritative trace disappeared")
        require(trace.get("validation_status") == "VALID", f"{case_id}: authoritative trace no longer VALID")
        require(continuity.get("TRACE_ORDER_REQUEST_PAYMENT_CONTINUITY") is True, f"{case_id}: trace refs regressed")
        require(continuity.get("ACTION_ORIGIN_PROJECTABLE") is False, f"{case_id}: unexpected Action Origin change inside H-19")
        require(case.get("continuity_pass") is False, f"{case_id}: unexpected continuity change inside H-19")
        require(case.get("first_breakpoint") == "ACTION_ORIGIN_PROJECTABLE", f"{case_id}: first breakpoint changed")

    j03 = by_id["J03_PAYMENT_SUCCEEDED_FULFILLMENT_FAILED"]
    trace = j03.get("trace") or {}
    refs = j03.get("refs") or {}
    continuity = j03.get("continuity") or {}
    require(trace.get("available") is True, "J03 authoritative trace still unavailable")
    require(trace.get("validation_status") == "VALID", "J03 authoritative trace is not VALID")
    require(trace.get("order_id") == refs.get("order_id"), "J03 trace/order ref mismatch")
    require(trace.get("request_id") == refs.get("request_id"), "J03 trace/request ref mismatch")
    require(trace.get("payment_id") == refs.get("payment_id"), "J03 trace/payment ref mismatch")
    require(continuity.get("AUTHORITATIVE_TRACE_AVAILABLE") is True, "J03 trace availability continuity check failed")
    require(continuity.get("AUTHORITATIVE_TRACE_VALID") is True, "J03 trace validity continuity check failed")
    require(continuity.get("TRACE_ORDER_REQUEST_PAYMENT_CONTINUITY") is True, "J03 trace ref continuity check failed")
    require(continuity.get("ACTION_ORIGIN_PROJECTABLE") is True, "J03 trace exists but Action Origin projection is still the next breakpoint")
    require(trace.get("action_origin_projectable") is True, "J03 trace Action Origin projection flag false")
    require(j03.get("continuity_pass") is True, "J03 continuity did not close")
    require(j03.get("first_breakpoint") is None, "J03 still has a first breakpoint")

    summary = data.get("summary") or {}
    require(summary.get("cases_measured") == 4 and summary.get("cases_total") == 4, "case summary changed")
    require(summary.get("semantic_matches") == 4 and summary.get("semantic_total") == 4, "semantic summary must remain 4/4")
    require(summary.get("branch_continuity_passed") == 2 and summary.get("branch_continuity_total") == 4, "H-19 target is exact branch continuity 2/4")

    guardrails = data.get("guardrails") or {}
    require(guardrails.get("real_webshop_buy_now_count") == 0, "real Buy Now side effect detected")
    require(guardrails.get("real_payment_execution_count") == 0, "real payment side effect detected")
    require(guardrails.get("real_fulfillment_execution_count") == 0, "real fulfillment side effect detected")
    require(guardrails.get("external_network_calls") == 0, "external network side effect detected")
    require(guardrails.get("counterfactual_branches_reported_as_real_transactions") is False, "counterfactual branches misrepresented as real transactions")

    print("PASS: H-19 closes J03 authoritative-trace/continuity breakpoint, preserves J01/J02/J04 semantics and exact remaining Action Origin gaps, continuity=2/4, real side effects=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

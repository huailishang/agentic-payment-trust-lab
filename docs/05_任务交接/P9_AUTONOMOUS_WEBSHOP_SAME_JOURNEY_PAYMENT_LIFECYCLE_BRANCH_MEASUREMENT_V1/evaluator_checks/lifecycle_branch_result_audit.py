from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[4]
MATRIX = ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_PAYMENT_LIFECYCLE_BRANCH_MEASUREMENT_V1/evaluator_fixtures/LIFECYCLE_BRANCH_MATRIX.json"
EXPECTED_MATRIX_SHA = "c6f6c22c7c2ff637950b2611cb99ef6762f76eff0ee52def90ecf707e6839c7d"
EXPECTED_SCHEMA = "same-journey-payment-lifecycle-branches/v1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapping(value: Any, label: str) -> Mapping[str, Any]:
    require(isinstance(value, Mapping), f"{label} must be mapping")
    return value


def validate(payload: Mapping[str, Any]) -> tuple[int, int]:
    require(payload.get("schema") == EXPECTED_SCHEMA, "result schema mismatch")
    require(sha256(MATRIX) == EXPECTED_MATRIX_SHA, "frozen lifecycle branch matrix changed")
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    parent_expected = mapping(matrix["parent"], "matrix.parent")
    parent_observed = mapping(payload.get("parent"), "result.parent")
    for key in (
        "h17_result_sha256",
        "session_id",
        "order_id",
        "request_id",
        "payment_id",
        "selected_asin",
        "selected_option",
        "selected_price",
    ):
        require(parent_observed.get(key) == parent_expected.get(key), f"parent mismatch: {key}")

    repeat_expected = int(matrix["repeat_per_case"])
    require(payload.get("repeat_per_case") == repeat_expected, "repeat_per_case mismatch")
    cases = payload.get("cases")
    require(isinstance(cases, list), "cases must be list")
    expected_cases = {item["case_id"]: item for item in matrix["cases"]}
    observed_cases = {item.get("case_id"): item for item in cases if isinstance(item, Mapping)}
    require(set(observed_cases) == set(expected_cases), f"case ids mismatch: {sorted(observed_cases)}")
    continuity_order = list(matrix["continuity_checks"])

    continuity_passed = 0
    semantic_matches = 0
    for case_id, expected_case in expected_cases.items():
        observed = mapping(observed_cases[case_id], case_id)
        require(observed.get("input") == expected_case["input"], f"{case_id}: frozen input drift")
        require(observed.get("measurement_complete") is True, f"{case_id}: measurement incomplete")
        require(observed.get("repeat_identical") is True, f"{case_id}: repeat not identical")
        digests = observed.get("run_digests")
        require(isinstance(digests, list) and len(digests) == repeat_expected, f"{case_id}: run_digests count mismatch")
        require(len(set(str(item) for item in digests)) == 1, f"{case_id}: run digests differ")

        semantics = mapping(observed.get("observed_semantics"), f"{case_id}.observed_semantics")
        semantic_match = semantics == expected_case["expected_semantics"]
        require(observed.get("semantic_match") is semantic_match, f"{case_id}: semantic_match inconsistent")
        if semantic_match:
            semantic_matches += 1

        refs = mapping(observed.get("refs"), f"{case_id}.refs")
        for key in ("session_id", "order_id", "request_id", "payment_id", "payment_order_id", "payment_request_id"):
            require(key in refs, f"{case_id}: refs missing {key}")
        trace = mapping(observed.get("trace"), f"{case_id}.trace")
        require(isinstance(trace.get("available"), bool), f"{case_id}: trace.available must be bool")
        require(isinstance(trace.get("action_origin_projectable"), bool), f"{case_id}: trace.action_origin_projectable must be bool")
        origin_types = trace.get("action_origin_types")
        require(isinstance(origin_types, list), f"{case_id}: trace.action_origin_types must be list")
        required_origins = {"USER_AUTHORITY", "AGENT_DECISION", "RUNTIME_DECISION", "EXTERNAL_FACT", "EXECUTION_RESULT"}

        computed = {
            "PARENT_JOURNEY_IDENTITY": refs.get("session_id") == parent_expected["session_id"],
            "ORDER_REQUEST_CONTINUITY": refs.get("order_id") == parent_expected["order_id"] and refs.get("request_id") == parent_expected["request_id"],
            "PAYMENT_ORDER_REQUEST_CONTINUITY": refs.get("payment_id") == parent_expected["payment_id"] and refs.get("payment_order_id") == refs.get("order_id") and refs.get("payment_request_id") == refs.get("request_id"),
            "SEMANTIC_EXPECTATION_MATCH": semantic_match,
            "AUTHORITATIVE_TRACE_AVAILABLE": trace.get("available") is True,
            "AUTHORITATIVE_TRACE_VALID": trace.get("validation_status") == "VALID",
            "TRACE_ORDER_REQUEST_PAYMENT_CONTINUITY": trace.get("order_id") == refs.get("order_id") and trace.get("request_id") == refs.get("request_id") and trace.get("payment_id") == refs.get("payment_id"),
            "ACTION_ORIGIN_PROJECTABLE": trace.get("action_origin_projectable") is True and required_origins.issubset({str(item) for item in origin_types}),
        }

        continuity = mapping(observed.get("continuity"), f"{case_id}.continuity")
        require(set(continuity) == set(continuity_order), f"{case_id}: continuity check ids mismatch")
        require(all(isinstance(continuity[key], bool) for key in continuity_order), f"{case_id}: continuity values must be bool")
        for key in continuity_order:
            require(continuity[key] is computed[key], f"{case_id}: continuity flag inconsistent for {key}")
        expected_pass = all(computed[key] for key in continuity_order)
        require(observed.get("continuity_pass") is expected_pass, f"{case_id}: continuity_pass inconsistent")
        failed = [key for key in continuity_order if computed[key] is False]
        expected_breakpoint = None if not failed else failed[0]
        require(observed.get("first_breakpoint") == expected_breakpoint, f"{case_id}: first_breakpoint inconsistent")
        if expected_pass:
            continuity_passed += 1

    summary = mapping(payload.get("summary"), "summary")
    require(summary.get("cases_measured") == len(expected_cases), "summary cases_measured mismatch")
    require(summary.get("cases_total") == len(expected_cases), "summary cases_total mismatch")
    require(summary.get("semantic_matches") == semantic_matches, "summary semantic_matches mismatch")
    require(summary.get("semantic_total") == len(expected_cases), "summary semantic_total mismatch")
    require(summary.get("branch_continuity_passed") == continuity_passed, "summary continuity passed mismatch")
    require(summary.get("branch_continuity_total") == len(expected_cases), "summary continuity total mismatch")

    guardrails = mapping(payload.get("guardrails"), "guardrails")
    for key in (
        "real_webshop_buy_now_count",
        "real_payment_execution_count",
        "real_fulfillment_execution_count",
        "external_network_calls",
    ):
        require(guardrails.get(key) == 0, f"guardrail violation: {key}")
    require(guardrails.get("counterfactual_branches_reported_as_real_transactions") is False, "counterfactual branches misrepresented as real")

    return continuity_passed, len(expected_cases)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    payload = mapping(json.loads(args.result.read_text(encoding="utf-8")), "result")
    passed, total = validate(payload)

    # Negative control: changing frozen semantics must be rejected.
    tampered = copy.deepcopy(payload)
    tampered["cases"][0]["observed_semantics"]["task_status"] = "UNKNOWN"
    rejected = False
    try:
        validate(mapping(tampered, "tampered"))
    except AssertionError:
        rejected = True
    require(rejected, "semantic tamper was not rejected")

    # Negative control: continuity summary cannot be falsified.
    tampered2 = copy.deepcopy(payload)
    tampered2["cases"][0]["continuity_pass"] = not bool(tampered2["cases"][0]["continuity_pass"])
    rejected2 = False
    try:
        validate(mapping(tampered2, "tampered2"))
    except AssertionError:
        rejected2 = True
    require(rejected2, "continuity tamper was not rejected")

    print(f"PASS: 4/4 lifecycle branches measured deterministically with frozen semantics; branch continuity observed={passed}/{total}; failures remain project findings, not executor task failures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

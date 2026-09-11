from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MATRIX_PATH = ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_REMEDIATION_CLOSURE_MEASUREMENT_V1/evaluator_fixtures/REMEDIATION_CLOSURE_MATRIX.json"
MATRIX_SHA256 = "abe7a75d32d6833f5289160c1477d18b6265aae18476c3e1b509989373f26acc"
PARENT_RESULT_PATH = ROOT / "docs/05_任务交接/P9_WEBSHOP_LIFECYCLE_EVIDENCE_CONTINUITY_CLOSURE_V1/evidence/H20_LIFECYCLE_BRANCH_RESULT.json"
PARENT_RESULT_SHA256 = "312bcef7e3ff4c92b2cf60ed898ac9f4d384ef7cf4639a2a66cce8814e3f3455"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: h21_result_audit.py <H21_REMEDIATION_CLOSURE_RESULT.json>")

    result_path = (ROOT / argv[1]).resolve() if not Path(argv[1]).is_absolute() else Path(argv[1])
    require(result_path.is_file(), f"result missing: {result_path}")
    require(sha256(MATRIX_PATH) == MATRIX_SHA256, "frozen remediation matrix changed")
    require(sha256(PARENT_RESULT_PATH) == PARENT_RESULT_SHA256, "accepted H-20 parent result changed")

    matrix = load_json(MATRIX_PATH)
    parent_result = load_json(PARENT_RESULT_PATH)
    result = load_json(result_path)

    require(result.get("schema") == "same-journey-remediation-closure-result/v1", "unexpected result schema")
    require(result.get("matrix_sha256") == MATRIX_SHA256, "result matrix hash mismatch")
    require(result.get("repeat_per_case") == 2, "repeat_per_case must be 2")

    parent_j03 = next(
        item for item in parent_result["cases"]
        if item["case_id"] == matrix["parent_branch_id"]
    )
    require(parent_j03["semantic_match"] is True, "accepted parent J03 semantic must remain true")
    require(parent_j03["continuity_pass"] is True, "accepted parent J03 continuity must remain true")

    parent = result.get("parent") or {}
    require(parent.get("branch_id") == matrix["parent_branch_id"], "wrong parent branch")
    for key in ("session_id", "order_id", "request_id", "payment_id"):
        require(parent.get(key) == parent_j03["refs"].get(key), f"parent {key} drifted")

    matrix_cases = {item["case_id"]: item for item in matrix["cases"]}
    cases = result.get("cases")
    require(isinstance(cases, list) and len(cases) == 5, "expected exactly 5 measured cases")
    require([item.get("case_id") for item in cases] == [item["case_id"] for item in matrix["cases"]], "case order/ids must match frozen matrix")

    continuity_order = matrix["continuity_check_order"]
    semantic_match_count = 0
    binding_match_count = 0
    continuity_pass_count = 0
    breakpoints: Counter[str] = Counter()

    for case in cases:
        case_id = case["case_id"]
        expected = matrix_cases[case_id]["expected"]

        require(case.get("measurement_complete") is True, f"{case_id}: measurement incomplete")
        require(case.get("repeat_identical") is True, f"{case_id}: repeat not identical")
        digests = case.get("run_digests")
        require(isinstance(digests, list) and len(digests) == 2, f"{case_id}: expected two run digests")
        require(digests[0] == digests[1] and len(digests[0]) == 64, f"{case_id}: run digests must be identical SHA-256")

        observed = case.get("observed_semantics") or {}
        issue_codes = set(observed.get("issue_codes") or [])
        semantic_expected = (
            observed.get("task_status") == expected["task_status"]
            and observed.get("remediation_status") == expected["remediation_status"]
            and observed.get("next_action") == expected["next_action"]
            and observed.get("refund_status") == expected["refund_status"]
            and observed.get("dispute_status") == expected["dispute_status"]
            and set(expected["required_issue_codes"]).issubset(issue_codes)
        )
        require(case.get("semantic_match") is semantic_expected, f"{case_id}: semantic_match not mechanically derived")
        semantic_match_count += int(semantic_expected)

        binding = case.get("original_transaction_binding") or {}
        require(binding.get("expected_status") == expected["original_transaction_binding"], f"{case_id}: binding expected status drift")
        binding_expected = binding.get("observed_status") == binding.get("expected_status")
        require(binding.get("expectation_match") is binding_expected, f"{case_id}: binding expectation_match not mechanically derived")
        binding_match_count += int(binding_expected)

        refs = case.get("refs") or {}
        parent_identity = all(refs.get(key) == parent.get(key) for key in ("session_id", "order_id", "request_id", "payment_id"))
        order_request_payment = (
            refs.get("order_id") == parent.get("order_id")
            and refs.get("request_id") == parent.get("request_id")
            and refs.get("payment_id") == parent.get("payment_id")
        )

        remediation_evidence = case.get("remediation_evidence")
        evidence_present = bool(remediation_evidence)

        trace = case.get("trace") or {}
        trace_available = trace.get("available") is True and trace.get("product_observed") is True
        trace_valid = trace_available and trace.get("validation_status") == "VALID"
        trace_remediation = trace.get("remediation_event_or_role_present") is True
        origin_projectable = trace.get("action_origin_projectable") is True

        closure = case.get("closure") or {}
        closure_explicit = (
            closure.get("state_explicit") is True
            and closure.get("original_task_status") == observed.get("task_status")
            and closure.get("economic_remediation_status") == observed.get("remediation_status")
            and closure.get("next_action") == observed.get("next_action")
            and bool(closure.get("case_ref"))
        )

        recomputed = {
            "PARENT_JOURNEY_IDENTITY": parent_identity,
            "ORDER_REQUEST_PAYMENT_CONTINUITY": order_request_payment,
            "REMEDIATION_SEMANTIC_EXPECTATION_MATCH": semantic_expected,
            "ORIGINAL_TRANSACTION_BINDING_EXPECTATION_MATCH": binding_expected,
            "REMEDIATION_EVIDENCE_PRESENT": evidence_present,
            "AUTHORITATIVE_TRACE_AVAILABLE": trace_available,
            "AUTHORITATIVE_TRACE_VALID": trace_valid,
            "TRACE_REMEDIATION_EVIDENCE_PRESENT": trace_remediation,
            "ACTION_ORIGIN_PROJECTABLE": origin_projectable,
            "CLOSURE_STATE_EXPLICIT": closure_explicit,
        }
        continuity = case.get("continuity") or {}
        require(list(continuity.keys()) == continuity_order, f"{case_id}: continuity keys/order differ from matrix")
        require(continuity == recomputed, f"{case_id}: continuity values do not match independently recomputed observations")

        continuity_pass = all(recomputed.values())
        require(case.get("continuity_pass") is continuity_pass, f"{case_id}: continuity_pass mismatch")
        continuity_pass_count += int(continuity_pass)

        first = next((name for name in continuity_order if not recomputed[name]), None)
        require(case.get("first_breakpoint") == first, f"{case_id}: first_breakpoint mismatch")
        if first is not None:
            breakpoints[first] += 1

    guardrails = result.get("guardrails") or {}
    for key in (
        "real_payment_side_effects",
        "real_refund_side_effects",
        "real_dispute_side_effects",
        "network_calls",
    ):
        require(guardrails.get(key) == 0, f"guardrail must remain zero: {key}")

    summary = result.get("summary") or {}
    require(summary.get("cases_measured") == 5, "summary cases_measured must be 5")
    require(summary.get("semantic_matches") == semantic_match_count, "summary semantic_matches mismatch")
    require(summary.get("binding_expectations_matched") == binding_match_count, "summary binding count mismatch")
    require(summary.get("continuity_passed") == continuity_pass_count, "summary continuity count mismatch")
    require(summary.get("first_breakpoint_counts") == dict(sorted(breakpoints.items())), "summary breakpoint counts mismatch")

    print(
        "PASS: H-21 measured all five remediation/closure branches deterministically; semantics, binding expectations, product-observed trace/origin/closure continuity and first breakpoints are mechanically reproducible without requiring all branches to pass continuity"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

from __future__ import annotations

import json
import sys
from pathlib import Path

EXPECTED_CASES = (
    "R01_FULL_REFUND",
    "R02_PARTIAL_REFUND",
    "R03_DISPUTE_OPEN",
    "R04_DISPUTE_RESOLVED_OUTCOME_UNVERIFIED",
    "R05_REFUND_PAYMENT_BINDING_MISMATCH",
)
EXPECTED_SOURCE_TYPE = {
    "R01_FULL_REFUND": "RefundRecord",
    "R02_PARTIAL_REFUND": "RefundRecord",
    "R03_DISPUTE_OPEN": "DisputeRecord",
    "R04_DISPUTE_RESOLVED_OUTCOME_UNVERIFIED": "DisputeRecord",
    "R05_REFUND_PAYMENT_BINDING_MISMATCH": "RefundRecord",
}
EXPECTED_BINDING_STATUS = {
    "R01_FULL_REFUND": "VALID",
    "R02_PARTIAL_REFUND": "VALID",
    "R03_DISPUTE_OPEN": "VALID",
    "R04_DISPUTE_RESOLVED_OUTCOME_UNVERIFIED": "VALID",
    "R05_REFUND_PAYMENT_BINDING_MISMATCH": "INVALID",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    require(len(sys.argv) == 2, "usage: h22_result_audit.py <result.json>")
    path = Path(sys.argv[1])
    require(path.is_file(), f"result missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))

    require(data.get("schema") == "same-journey-remediation-trace-closure-result/v1", "unexpected result schema")
    require(data.get("repeat_per_case") == 2, "repeat_per_case must be 2")

    baseline = data.get("baseline") or {}
    require(baseline.get("accepted_h21_result_sha256") == "9d794317cc77753bb84e6b7b0ec3c6a441ff1d6a632753c782ba556c7fb4f8bb", "wrong H-21 baseline hash")
    require(baseline.get("trace_remediation_evidence_present") == 0, "H-21 before value must remain 0/5")
    require(baseline.get("cases_total") == 5, "H-21 baseline total must remain 5")

    cases = data.get("cases")
    require(type(cases) is list and len(cases) == 5, "expected five remediation cases")
    require(tuple(case.get("case_id") for case in cases) == EXPECTED_CASES, "case identity/order changed")

    for case in cases:
        case_id = case["case_id"]
        require(case.get("measurement_complete") is True, f"{case_id}: measurement incomplete")
        require(case.get("repeat_identical") is True, f"{case_id}: repeats not identical")
        digests = case.get("run_digests")
        require(type(digests) is list and len(digests) == 2 and digests[0] == digests[1], f"{case_id}: expected two identical run digests")
        require(case.get("semantic_match") is True, f"{case_id}: remediation semantic regression")
        require(case.get("continuity_pass") is True, f"{case_id}: remediation evidence continuity not closed")
        require(case.get("first_breakpoint") is None, f"{case_id}: first_breakpoint must be null")

        binding = case.get("original_transaction_binding") or {}
        require(binding.get("expectation_match") is True, f"{case_id}: original-transaction expectation mismatch")
        require(binding.get("observed_status") == EXPECTED_BINDING_STATUS[case_id], f"{case_id}: unexpected binding status")
        if case_id == "R05_REFUND_PAYMENT_BINDING_MISMATCH":
            reasons = binding.get("reason_codes") or []
            require("original_transaction_payment_ref_mismatch" in reasons, "R05: mismatch reason must remain explicit")

        trace = case.get("extended_trace") or {}
        require(trace.get("available") is True, f"{case_id}: extended product trace unavailable")
        require(trace.get("validation_status") == "VALID", f"{case_id}: extended product trace not VALID")
        require(trace.get("product_observed") is True, f"{case_id}: extended trace must be product-observed")

        observation = case.get("remediation_observation") or {}
        require(observation.get("event_present") is True, f"{case_id}: remediation observation event missing")
        require(observation.get("source_object_type") == EXPECTED_SOURCE_TYPE[case_id], f"{case_id}: wrong remediation source type")
        require(bool(observation.get("source_binding_ref")), f"{case_id}: remediation source binding missing")
        if case_id == "R05_REFUND_PAYMENT_BINDING_MISMATCH":
            require(observation.get("original_payment_relation_asserted") is False, "R05: false original-payment relation must not be asserted")

        binding_fact = case.get("binding_fact_evidence") or {}
        require(binding_fact.get("event_present") is True, f"{case_id}: binding fact event missing")
        require(binding_fact.get("source_object_type") == "OriginalTransactionBindingFact", f"{case_id}: wrong binding fact source type")
        require(binding_fact.get("status") == EXPECTED_BINDING_STATUS[case_id], f"{case_id}: trace binding fact status drift")
        require(bool(binding_fact.get("source_binding_ref")), f"{case_id}: binding fact source binding missing")

        closure = case.get("closure_evidence") or {}
        require(closure.get("event_present") is True, f"{case_id}: closure event missing")
        require(closure.get("source_object_type") == "LifecycleResult", f"{case_id}: closure source must be LifecycleResult")
        require(closure.get("state_explicit") is True, f"{case_id}: closure state not explicit")
        require(bool(closure.get("source_binding_ref")), f"{case_id}: closure source binding missing")

        origin = case.get("action_origin") or {}
        require(origin.get("projectable") is True, f"{case_id}: Action Origin not projectable")
        types = set(origin.get("types") or [])
        require({"EXTERNAL_FACT", "RUNTIME_DECISION", "EXECUTION_RESULT"}.issubset(types), f"{case_id}: new evidence origin classes incomplete")

    summary = data.get("summary") or {}
    require(summary.get("cases_measured") == 5 and summary.get("cases_total") == 5, "summary cases must be 5/5")
    require(summary.get("semantic_matches") == 5, "semantics must remain 5/5")
    require(summary.get("binding_expectations_matched") == 5, "binding expectations must remain 5/5")
    require(summary.get("trace_remediation_evidence_present") == 5, "H-22 target is remediation trace evidence 5/5")
    require(summary.get("branch_continuity_passed") == 5, "H-22 target is branch continuity 5/5")

    guardrails = data.get("guardrails") or {}
    for key in ("real_payment_execution_count", "real_refund_execution_count", "real_dispute_execution_count", "external_network_calls"):
        require(guardrails.get(key) == 0, f"guardrail violated: {key}")

    print(
        "PASS: H-22 closes the shared remediation trace breakpoint from 0/5 to 5/5; "
        "all five branches retain semantics/binding expectations; R05 stays INVALID/fail-closed; "
        "remediation observation, binding fact, closure evidence, and Action Origin are source-bound/projectable"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

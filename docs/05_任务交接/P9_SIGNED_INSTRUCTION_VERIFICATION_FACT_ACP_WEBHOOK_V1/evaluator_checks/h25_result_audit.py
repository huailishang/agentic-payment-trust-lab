from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

CASE_IDS = (
    "V01_VALID_SIGNATURE",
    "N01_TAMPERED_BODY",
    "N02_WRONG_SECRET",
    "N03_STALE_TIMESTAMP",
    "N04_MISSING_SIGNATURE_HEADER",
    "N05_MALFORMED_SIGNATURE_HEADER",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    require(len(sys.argv) == 3, "usage: h25_result_audit.py <result.json> <matrix.json>")
    result_path = Path(sys.argv[1])
    matrix_path = Path(sys.argv[2])
    data = json.loads(result_path.read_text(encoding="utf-8"))
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))

    require(data.get("schema") == "signed-instruction-verification-capability/v1", "wrong result schema")
    require(data.get("repeat_per_case") == 2, "repeat_per_case must be 2")
    expected_cases = matrix.get("cases")
    require(isinstance(expected_cases, list) and len(expected_cases) == 6, "matrix must contain six cases")
    expected_by_id = {item["case_id"]: item["expected"] for item in expected_cases}
    require(tuple(expected_by_id) == CASE_IDS, "matrix case order/identity changed")

    cases = data.get("cases")
    require(isinstance(cases, list) and len(cases) == 6, "result must contain six cases")
    require(tuple(item.get("case_id") for item in cases) == CASE_IDS, "result case order/identity changed")

    passed = 0
    valid_positive = 0
    negative_fail_closed = 0
    for item in cases:
        case_id = item["case_id"]
        expected = expected_by_id[case_id]
        require(item.get("repeat_identical") is True, f"{case_id}: repeat not identical")
        digests = item.get("run_digests")
        require(isinstance(digests, list) and len(digests) == 2 and digests[0] == digests[1], f"{case_id}: bad repeat digests")
        require(item.get("observed_status") == expected["status"], f"{case_id}: status mismatch")
        require(item.get("observed_reason_codes") == expected["reason_codes"], f"{case_id}: reason mismatch")
        require(item.get("cryptographic_signature_verified") is expected["cryptographic_signature_verified"], f"{case_id}: verified flag mismatch")
        require(item.get("expectation_match") is True, f"{case_id}: expectation_match false")
        require(item.get("signer_ref") == matrix["fixture"]["signer_ref"], f"{case_id}: signer_ref mismatch")
        require(item.get("key_ref") == matrix["fixture"]["key_ref"], f"{case_id}: key_ref mismatch")
        payload_hash = item.get("signed_payload_sha256")
        require(payload_hash is None or (isinstance(payload_hash, str) and len(payload_hash) == 64), f"{case_id}: payload digest invalid")
        if expected["status"] == "VALID":
            valid_positive += 1
        else:
            require(item.get("cryptographic_signature_verified") is False, f"{case_id}: negative case verified")
            negative_fail_closed += 1
        passed += 1

    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("cases_passed") == passed == 6, "cases_passed must be 6")
    require(summary.get("cases_total") == 6, "cases_total must be 6")
    require(summary.get("baseline_executable_cases") == 0, "baseline must be 0/6")
    require(summary.get("after_executable_cases") == 6, "after must be 6/6")
    require(summary.get("valid_positive_cases") == valid_positive == 1, "valid positive count mismatch")
    require(summary.get("negative_cases_fail_closed") == negative_fail_closed == 5, "negative fail-closed count mismatch")

    external = data.get("external_requirement_impact")
    require(isinstance(external, dict), "external_requirement_impact missing")
    require(external.get("profile") == "PCAC-AGENTPAY", "wrong external requirement profile")
    require(external.get("requirement_ids") == ["PCAC-06"], "wrong PCAC requirement mapping")
    require(external.get("applicability") == "ADAPTER", "wrong PCAC applicability")
    require(external.get("maturity_before") == "M1", "wrong PCAC maturity_before")
    require(external.get("maturity_after") == "M3", "wrong PCAC maturity_after target")

    guardrails = data.get("guardrails")
    require(isinstance(guardrails, dict), "guardrails missing")
    for key in (
        "external_network_calls",
        "real_payment_execution_count",
        "production_credential_use_count",
        "production_key_use_count",
        "production_merchant_secret_use_count",
    ):
        require(guardrails.get(key) == 0, f"guardrail violated: {key}")

    serialized = result_path.read_text(encoding="utf-8")
    fixture = matrix["fixture"]
    for forbidden in (
        fixture["test_secret_utf8"],
        fixture["raw_body_utf8"],
    ):
        require(forbidden not in serialized, "result persisted forbidden secret/raw body material")
    require("Merchant-Signature" not in serialized, "result must not persist raw signature header")

    # The valid case must expose a digest derived from the exact ACP signed bytes,
    # without exposing the bytes themselves.
    valid = cases[0]
    signed = str(fixture["signed_at_epoch"]).encode("ascii") + b"." + fixture["raw_body_utf8"].encode("utf-8")
    expected_digest = hashlib.sha256(signed).hexdigest()
    require(valid.get("signed_payload_sha256") == expected_digest, "valid signed-payload digest mismatch")

    print(
        "PASS: H-25 six-case capability result is deterministic, fail-closed, auditable, and does not persist secret/raw signature material"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

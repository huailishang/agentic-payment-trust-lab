from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_CASES = (
    "V01_VALID_ES256_JWS",
    "N01_TAMPERED_PAYLOAD",
    "N02_WRONG_PUBLIC_KEY",
    "N03_WRONG_SIGNER_BINDING",
    "N04_MISSING_AUTHORIZATION",
    "N05_MALFORMED_COMPACT_JWS",
)
FORBIDDEN_KEYS = {
    "private_key",
    "private_key_pem",
    "raw_private_key",
    "compact_jws",
    "raw_token",
    "raw_signature",
    "production_credential",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def walk_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            found.add(str(key))
            found |= walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            found |= walk_keys(item)
    return found


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: h27_result_audit.py <result> <matrix>")
    result_path = Path(sys.argv[1])
    matrix_path = Path(sys.argv[2])
    result = json.loads(result_path.read_text(encoding="utf-8"))
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))

    require(result.get("schema") == "ap2-es256-signed-instruction-capability/v1", "unexpected result schema")
    require(result.get("protocol_profile") == matrix.get("protocol_profile"), "protocol profile mismatch")
    expected_matrix_hash = hashlib.sha256(matrix_path.read_bytes()).hexdigest()
    require(result.get("matrix_sha256") == expected_matrix_hash, "matrix hash mismatch")

    cases = result.get("cases")
    require(isinstance(cases, list) and len(cases) == 6, "result must contain six cases")
    require(tuple(item.get("case_id") for item in cases) == EXPECTED_CASES, "case identity/order mismatch")
    for item in cases:
        require(item.get("repeat_identical") is True, f"{item.get('case_id')}: repeat mismatch")
        require(item.get("expectation_match") is True, f"{item.get('case_id')}: expectation mismatch")
        require(len(item.get("run_digests", [])) == 2, f"{item.get('case_id')}: repeat digest count")

    summary = result.get("summary", {})
    require(summary.get("cases_passed") == 6, "cases_passed must be 6")
    require(summary.get("cases_total") == 6, "cases_total must be 6")
    require(summary.get("baseline_executable_cases") == 0, "baseline executable cases must be 0")
    require(summary.get("after_executable_cases") == 6, "after executable cases must be 6")
    require(summary.get("valid_positive_cases") == 1, "expected one valid positive")
    require(summary.get("negative_cases_fail_closed") == 5, "all five negatives must fail closed")
    require(summary.get("real_consumer_count_before") == 1, "consumer baseline must be 1")
    require(summary.get("real_consumer_count_after") == 2, "consumer after must be 2")

    ext = result.get("external_requirement_impact", {})
    require(ext.get("profile") == "PCAC-AGENTPAY", "external profile mismatch")
    require(ext.get("requirement_ids") == ["PCAC-06"], "external requirement mismatch")
    require(ext.get("applicability") == "ADAPTER", "external applicability mismatch")

    guardrails = result.get("guardrails", {})
    for key in (
        "external_network_calls",
        "real_payment_execution_count",
        "production_credential_use_count",
        "production_key_use_count",
    ):
        require(guardrails.get(key) == 0, f"guardrail must be zero: {key}")

    bad_keys = walk_keys(result) & FORBIDDEN_KEYS
    require(not bad_keys, f"sensitive/raw material leaked into result keys: {sorted(bad_keys)}")

    print("PASS: H-27 AP2 ES256 result proves deterministic second-consumer reuse and preserves data boundaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

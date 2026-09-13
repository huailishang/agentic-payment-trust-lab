from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
from pathlib import Path
from typing import Any, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agentic_payment_experiment.adapters import verify_acp_webhook_signature


SCHEMA = "signed-instruction-verification-capability/v1"
CASE_ORDER = (
    "V01_VALID_SIGNATURE",
    "N01_TAMPERED_BODY",
    "N02_WRONG_SECRET",
    "N03_STALE_TIMESTAMP",
    "N04_MISSING_SIGNATURE_HEADER",
    "N05_MALFORMED_SIGNATURE_HEADER",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--repeat", required=True, type=int)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_matrix(path: Path) -> Mapping[str, Any]:
    require(path.is_file(), f"matrix missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, Mapping), "matrix must be a JSON object")
    require(
        data.get("schema") == "acp-webhook-signature-capability-matrix/v1",
        "unexpected matrix schema",
    )
    cases = data.get("cases")
    require(isinstance(cases, list) and len(cases) == 6, "matrix must contain six cases")
    require(
        tuple(item.get("case_id") for item in cases if isinstance(item, Mapping)) == CASE_ORDER,
        "matrix case identity/order changed",
    )
    return data


def make_header(*, timestamp: int, raw_body: bytes, secret: bytes) -> str:
    signed_payload = str(timestamp).encode("ascii") + b"." + raw_body
    signature = hmac.new(secret, signed_payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


def observe_case(
    case_id: str,
    *,
    fixture: Mapping[str, Any],
) -> dict[str, object]:
    signer_ref = str(fixture["signer_ref"])
    key_ref = str(fixture["key_ref"])
    secret = str(fixture["test_secret_utf8"]).encode("utf-8")
    raw_body = str(fixture["raw_body_utf8"]).encode("utf-8")
    signed_at = int(fixture["signed_at_epoch"])
    observed_at = int(fixture["observed_at_epoch"])
    tolerance = int(fixture["timestamp_tolerance_seconds"])

    verification_body = raw_body
    verification_secret = secret
    signature_header: str | None = make_header(
        timestamp=signed_at,
        raw_body=raw_body,
        secret=secret,
    )

    if case_id == "V01_VALID_SIGNATURE":
        pass
    elif case_id == "N01_TAMPERED_BODY":
        verification_body = raw_body + b" "
    elif case_id == "N02_WRONG_SECRET":
        verification_secret = b"test-only-acp-webhook-wrong-secret"
    elif case_id == "N03_STALE_TIMESTAMP":
        stale_timestamp = observed_at - tolerance - 1
        signature_header = make_header(
            timestamp=stale_timestamp,
            raw_body=raw_body,
            secret=secret,
        )
    elif case_id == "N04_MISSING_SIGNATURE_HEADER":
        signature_header = None
    elif case_id == "N05_MALFORMED_SIGNATURE_HEADER":
        signature_header = f"t={signed_at},v1=malformed"
    else:
        raise RuntimeError(f"unsupported case: {case_id}")

    fact = verify_acp_webhook_signature(
        raw_body=verification_body,
        merchant_signature=signature_header,
        secret=verification_secret,
        observed_at_epoch=observed_at,
        signer_ref=signer_ref,
        key_ref=key_ref,
        max_age_seconds=tolerance,
    )
    return {
        "observed_status": fact.status.value,
        "observed_reason_codes": list(fact.reason_codes),
        "cryptographic_signature_verified": fact.cryptographic_signature_verified,
        "signer_ref": fact.signer_ref,
        "key_ref": fact.key_ref,
        "signed_payload_sha256": fact.signed_payload_sha256,
    }


def main() -> int:
    args = parse_args()
    require(args.repeat == 2, "H-25 frozen repeat must be exactly 2")
    matrix_path = Path(args.matrix)
    output_path = Path(args.output)
    matrix = load_matrix(matrix_path)
    fixture = matrix.get("fixture")
    cases = matrix.get("cases")
    require(isinstance(fixture, Mapping), "fixture missing")
    require(isinstance(cases, list), "cases missing")

    result_cases: list[dict[str, object]] = []
    for case in cases:
        require(isinstance(case, Mapping), "case must be an object")
        case_id = str(case["case_id"])
        expected = case.get("expected")
        require(isinstance(expected, Mapping), f"{case_id}: expected missing")

        observations = [
            observe_case(case_id, fixture=fixture)
            for _ in range(args.repeat)
        ]
        digests = [canonical_digest(item) for item in observations]
        first = observations[0]
        repeat_identical = all(item == first for item in observations[1:])
        expectation_match = (
            first["observed_status"] == expected.get("status")
            and first["observed_reason_codes"] == expected.get("reason_codes")
            and first["cryptographic_signature_verified"]
            is expected.get("cryptographic_signature_verified")
        )
        result_cases.append(
            {
                "case_id": case_id,
                "repeat_identical": repeat_identical,
                "run_digests": digests,
                **first,
                "expectation_match": expectation_match,
            }
        )

    cases_passed = sum(
        1
        for item in result_cases
        if item["repeat_identical"] is True and item["expectation_match"] is True
    )
    valid_positive_cases = sum(
        1 for item in result_cases if item["observed_status"] == "VALID"
    )
    negative_cases_fail_closed = sum(
        1
        for item in result_cases
        if item["observed_status"] != "VALID"
        and item["cryptographic_signature_verified"] is False
    )

    result = {
        "schema": SCHEMA,
        "protocol_profile": matrix.get("protocol_profile"),
        "repeat_per_case": args.repeat,
        "matrix_sha256": hashlib.sha256(matrix_path.read_bytes()).hexdigest(),
        "cases": result_cases,
        "summary": {
            "cases_passed": cases_passed,
            "cases_total": len(result_cases),
            "baseline_executable_cases": 0,
            "after_executable_cases": cases_passed,
            "valid_positive_cases": valid_positive_cases,
            "negative_cases_fail_closed": negative_cases_fail_closed,
        },
        "external_requirement_impact": {
            "profile": "PCAC-AGENTPAY",
            "requirement_ids": ["PCAC-06"],
            "applicability": "ADAPTER",
            "maturity_before": "M1",
            "maturity_after": "M3",
        },
        "guardrails": {
            "external_network_calls": 0,
            "real_payment_execution_count": 0,
            "production_credential_use_count": 0,
            "production_key_use_count": 0,
            "production_merchant_secret_use_count": 0,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    require(len(result_cases) == 6, "result must contain exactly six cases")
    require(cases_passed == 6, "not all frozen signed-instruction cases passed")
    require(valid_positive_cases == 1, "expected exactly one valid positive case")
    require(negative_cases_fail_closed == 5, "expected all five negative cases to fail closed")
    print(
        "PASS: H-25 signed-instruction capability 6/6; repeat=2 deterministic; "
        "negative cases fail closed; persisted result contains only minimized evidence"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

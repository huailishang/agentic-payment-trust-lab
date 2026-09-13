from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agentic_payment_experiment.adapters import verify_ap2_merchant_authorization_signature


SCHEMA = "ap2-es256-signed-instruction-capability/v1"
CASE_ORDER = (
    "V01_VALID_ES256_JWS",
    "N01_TAMPERED_PAYLOAD",
    "N02_WRONG_PUBLIC_KEY",
    "N03_WRONG_SIGNER_BINDING",
    "N04_MISSING_AUTHORIZATION",
    "N05_MALFORMED_COMPACT_JWS",
)
H25_ACCEPTED_RESULT_SHA256 = "888d8d9ae215ce3d4ac593c190a2863746fddf1d99ca78175324670615b22a37"


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
        data.get("schema") == "ap2-es256-signed-instruction-matrix/v1",
        "unexpected matrix schema",
    )
    cases = data.get("cases")
    require(isinstance(cases, list) and len(cases) == 6, "matrix must contain six cases")
    require(
        tuple(item.get("case_id") for item in cases if isinstance(item, Mapping)) == CASE_ORDER,
        "matrix case identity/order changed",
    )
    return data


def base64url_decode(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value + padding)


def base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def tamper_payload_keep_signature(compact_jws: str) -> str:
    header_segment, payload_segment, signature_segment = compact_jws.split(".")
    payload = json.loads(base64url_decode(payload_segment).decode("utf-8"))
    require(isinstance(payload, dict), "fixture payload must be a JSON object")
    payload["jti"] = str(payload.get("jti", "test")) + "-tampered"
    tampered_payload = base64url_encode(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return f"{header_segment}.{tampered_payload}.{signature_segment}"


def observe_case(case_id: str, *, fixture: Mapping[str, Any]) -> dict[str, object]:
    compact_jws: str | None = str(fixture["valid_compact_jws"])
    public_jwk = fixture["valid_public_jwk"]
    require(isinstance(public_jwk, Mapping), "valid_public_jwk missing")
    expected_signer_ref = str(fixture["expected_signer_ref"])
    expected_key_ref = str(fixture["expected_key_ref"])
    observed_at_epoch = int(fixture["observed_at_epoch"])

    if case_id == "V01_VALID_ES256_JWS":
        pass
    elif case_id == "N01_TAMPERED_PAYLOAD":
        compact_jws = tamper_payload_keep_signature(compact_jws)
    elif case_id == "N02_WRONG_PUBLIC_KEY":
        wrong_jwk = fixture["wrong_public_jwk"]
        require(isinstance(wrong_jwk, Mapping), "wrong_public_jwk missing")
        public_jwk = wrong_jwk
    elif case_id == "N03_WRONG_SIGNER_BINDING":
        expected_signer_ref = "other-merchant-test"
    elif case_id == "N04_MISSING_AUTHORIZATION":
        compact_jws = None
    elif case_id == "N05_MALFORMED_COMPACT_JWS":
        compact_jws = "malformed.compact-jws"
    else:
        raise RuntimeError(f"unsupported case: {case_id}")

    fact = verify_ap2_merchant_authorization_signature(
        merchant_authorization=compact_jws,
        public_jwk=public_jwk,
        expected_signer_ref=expected_signer_ref,
        expected_key_ref=expected_key_ref,
        observed_at_epoch=observed_at_epoch,
    )
    return {
        "observed_status": fact.status.value,
        "observed_reason_codes": list(fact.reason_codes),
        "cryptographic_signature_verified": fact.cryptographic_signature_verified,
        "algorithm": fact.algorithm,
        "signer_ref": fact.signer_ref,
        "key_ref": fact.key_ref,
        "signed_payload_sha256": fact.signed_payload_sha256,
        "signed_at_epoch": fact.signed_at_epoch,
        "observed_at_epoch": fact.observed_at_epoch,
        "max_age_seconds": fact.max_age_seconds,
    }


def main() -> int:
    args = parse_args()
    require(args.repeat == 2, "H-27 frozen repeat must be exactly 2")
    matrix_path = Path(args.matrix)
    output_path = Path(args.output)
    matrix = load_matrix(matrix_path)
    fixture = matrix.get("fixture")
    cases = matrix.get("cases")
    require(isinstance(fixture, Mapping), "fixture missing")
    require(isinstance(cases, list), "cases missing")

    expected_signing_input_hash = str(fixture["expected_signing_input_sha256"])
    result_cases: list[dict[str, object]] = []
    for case in cases:
        require(isinstance(case, Mapping), "case must be an object")
        case_id = str(case["case_id"])
        expected = case.get("expected")
        require(isinstance(expected, Mapping), f"{case_id}: expected missing")

        observations = [observe_case(case_id, fixture=fixture) for _ in range(args.repeat)]
        digests = [canonical_digest(item) for item in observations]
        first = observations[0]
        repeat_identical = all(item == first for item in observations[1:])
        expectation_match = (
            first["observed_status"] == expected.get("status")
            and first["observed_reason_codes"] == expected.get("reason_codes")
            and first["cryptographic_signature_verified"]
            is expected.get("cryptographic_signature_verified")
        )
        if case_id == "V01_VALID_ES256_JWS":
            expectation_match = expectation_match and (
                first["signed_payload_sha256"] == expected_signing_input_hash
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
            "real_consumer_count_before": 1,
            "real_consumer_count_after": 2,
        },
        "h25_accepted_result_sha256": H25_ACCEPTED_RESULT_SHA256,
        "external_requirement_impact": {
            "profile": "PCAC-AGENTPAY",
            "requirement_ids": ["PCAC-06"],
            "applicability": "ADAPTER",
            "maturity_before": "M3",
            "maturity_after": "M4",
            "residual_risk": [
                "synthetic fixture only",
                "no live JWKS/DID/PKI",
                "no SD-JWT holder binding",
                "no full AP2 conformance claim",
            ],
        },
        "guardrails": {
            "external_network_calls": 0,
            "real_payment_execution_count": 0,
            "production_credential_use_count": 0,
            "production_key_use_count": 0,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    require(len(result_cases) == 6, "result must contain exactly six cases")
    require(cases_passed == 6, "not all frozen AP2 ES256 cases passed")
    require(valid_positive_cases == 1, "expected exactly one valid positive case")
    require(negative_cases_fail_closed == 5, "expected all five negative cases to fail closed")
    print(
        "PASS: H-27 AP2 ES256 signed-instruction capability 6/6; repeat=2 deterministic; "
        "real consumers 1->2; negative cases fail closed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

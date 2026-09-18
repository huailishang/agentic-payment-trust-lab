from __future__ import annotations

import base64
import copy
import hashlib
import json

from agentic_payment_experiment.adapters import adapt_verified_ap2_v020_snapshot
from agentic_payment_experiment.trusted_execution import VerificationStatus


def checkout_hash(raw_checkout_jwt: str) -> str:
    digest = hashlib.sha256(raw_checkout_jwt.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def fixture() -> dict:
    raw_checkout_jwt = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.fixture-checkout.signature"
    verified_hash = checkout_hash(raw_checkout_jwt)
    return {
        "protocol_version": "AP2-v0.2.0-official-boundary",
        "open_payment_mandate": {
            "vct": "mandate.payment.open.1",
            "constraints": [
                {
                    "type": "payment.amount_range",
                    "currency": "CNY",
                    "max": 55000,
                },
                {
                    "type": "payment.allowed_payees",
                    "allowed": [{"id": "merchant-boundary"}],
                },
                {
                    "type": "payment.agent_recurrence",
                    "frequency": "ON_DEMAND",
                    "max_occurrences": 1,
                },
                {
                    "type": "payment.execution_date",
                    "not_after": "2026-12-31T23:59:59+08:00",
                },
            ],
        },
        "payment_mandate": {
            "vct": "mandate.payment.1",
            "transaction_id": verified_hash,
            "payee": {"id": "merchant-boundary"},
            "payment_amount": {"currency": "CNY", "value": 52000},
            "execution_date": "2026-09-18T10:00:00+08:00",
            "payment_instrument": {"id": "synthetic-instrument"},
        },
        "checkout_mandate": {
            "vct": "mandate.checkout.1",
            "checkout_jwt": raw_checkout_jwt,
            "checkout_hash": verified_hash,
        },
        "experiment_context": {
            "mandate_id": "mandate-ap2-boundary-001",
            "user_id": "synthetic-user",
            "category": "synthetic-category",
            "allowed_categories": ["synthetic-category"],
            "confirmation_above_minor": 60000,
            "agent_id": "synthetic-agent",
        },
    }


def observed(result) -> dict:
    return {
        "status": getattr(result.boundary_status, "value", str(result.boundary_status)),
        "reason_codes": list(result.reason_codes),
        "ready": bool(result.ready),
        "mandate_present": result.mandate is not None,
        "request_present": result.request is not None,
        "verified_checkout_hash": result.verified_checkout_hash,
    }


def assert_case(
    *,
    case_id: str,
    snapshot: dict,
    expected_status: VerificationStatus,
    expected_reason: str,
    expected_ready: bool,
) -> dict:
    result = adapt_verified_ap2_v020_snapshot(snapshot)
    if result.boundary_status is not expected_status:
        raise AssertionError(
            f"{case_id}: expected status={expected_status.value} actual={observed(result)}"
        )
    if expected_reason not in result.reason_codes:
        raise AssertionError(
            f"{case_id}: missing reason={expected_reason} actual={observed(result)}"
        )
    if bool(result.ready) is not expected_ready:
        raise AssertionError(
            f"{case_id}: expected ready={expected_ready} actual={observed(result)}"
        )
    if expected_ready:
        if result.mandate is None or result.request is None:
            raise AssertionError(f"{case_id}: valid boundary did not produce canonical objects")
        if result.verified_checkout_hash != snapshot["checkout_mandate"]["checkout_hash"]:
            raise AssertionError(f"{case_id}: verified checkout hash not exposed")
    else:
        if result.mandate is not None or result.request is not None:
            raise AssertionError(
                f"{case_id}: invalid/missing boundary leaked canonical objects"
            )
    return {"case_id": case_id, **observed(result)}


def main() -> None:
    cases: list[dict] = []

    valid = fixture()
    cases.append(
        assert_case(
            case_id="B01_VALID",
            snapshot=valid,
            expected_status=VerificationStatus.VALID,
            expected_reason="ap2_v020_protocol_boundary_verified",
            expected_ready=True,
        )
    )

    wrong_open = copy.deepcopy(valid)
    wrong_open["open_payment_mandate"]["vct"] = "mandate.payment.open.999"
    cases.append(
        assert_case(
            case_id="B02_WRONG_OPEN_VCT",
            snapshot=wrong_open,
            expected_status=VerificationStatus.INVALID,
            expected_reason="ap2_open_payment_vct_invalid",
            expected_ready=False,
        )
    )

    wrong_payment = copy.deepcopy(valid)
    wrong_payment["payment_mandate"]["vct"] = "mandate.payment.2"
    cases.append(
        assert_case(
            case_id="B03_WRONG_PAYMENT_VCT",
            snapshot=wrong_payment,
            expected_status=VerificationStatus.INVALID,
            expected_reason="ap2_payment_vct_invalid",
            expected_ready=False,
        )
    )

    wrong_checkout = copy.deepcopy(valid)
    wrong_checkout["checkout_mandate"]["vct"] = "mandate.checkout.2"
    cases.append(
        assert_case(
            case_id="B04_WRONG_CHECKOUT_VCT",
            snapshot=wrong_checkout,
            expected_status=VerificationStatus.INVALID,
            expected_reason="ap2_checkout_vct_invalid",
            expected_ready=False,
        )
    )

    tampered_checkout = copy.deepcopy(valid)
    tampered_checkout["checkout_mandate"]["checkout_jwt"] += ".tampered"
    cases.append(
        assert_case(
            case_id="B05_TAMPERED_CHECKOUT_JWT",
            snapshot=tampered_checkout,
            expected_status=VerificationStatus.INVALID,
            expected_reason="ap2_checkout_hash_mismatch",
            expected_ready=False,
        )
    )

    wrong_transaction = copy.deepcopy(valid)
    wrong_transaction["payment_mandate"]["transaction_id"] = "not-the-verified-checkout-hash"
    cases.append(
        assert_case(
            case_id="B06_PAYMENT_CHECKOUT_MISMATCH",
            snapshot=wrong_transaction,
            expected_status=VerificationStatus.INVALID,
            expected_reason="ap2_payment_checkout_binding_mismatch",
            expected_ready=False,
        )
    )

    missing_hash = copy.deepcopy(valid)
    missing_hash["checkout_mandate"].pop("checkout_hash")
    cases.append(
        assert_case(
            case_id="B07_CHECKOUT_HASH_MISSING",
            snapshot=missing_hash,
            expected_status=VerificationStatus.MISSING_EVIDENCE,
            expected_reason="ap2_checkout_evidence_missing",
            expected_ready=False,
        )
    )

    non_string_jwt = copy.deepcopy(valid)
    non_string_jwt["checkout_mandate"]["checkout_jwt"] = 123
    coerced_hash = checkout_hash("123")
    non_string_jwt["checkout_mandate"]["checkout_hash"] = coerced_hash
    non_string_jwt["payment_mandate"]["transaction_id"] = coerced_hash
    cases.append(
        assert_case(
            case_id="B08_CHECKOUT_JWT_NON_STRING",
            snapshot=non_string_jwt,
            expected_status=VerificationStatus.INVALID,
            expected_reason="ap2_checkout_evidence_type_invalid",
            expected_ready=False,
        )
    )

    non_string_hash = copy.deepcopy(valid)
    non_string_hash["checkout_mandate"]["checkout_hash"] = 123
    cases.append(
        assert_case(
            case_id="B09_CHECKOUT_HASH_NON_STRING",
            snapshot=non_string_hash,
            expected_status=VerificationStatus.INVALID,
            expected_reason="ap2_checkout_evidence_type_invalid",
            expected_ready=False,
        )
    )

    non_string_transaction = copy.deepcopy(valid)
    non_string_transaction["payment_mandate"]["transaction_id"] = 123
    cases.append(
        assert_case(
            case_id="B10_TRANSACTION_ID_NON_STRING",
            snapshot=non_string_transaction,
            expected_status=VerificationStatus.INVALID,
            expected_reason="ap2_payment_checkout_binding_type_invalid",
            expected_ready=False,
        )
    )

    print(
        json.dumps(
            {
                "schema": "ap2-v020-protocol-boundary-evaluator-cases/v1",
                "result": "PASS",
                "cases_total": len(cases),
                "cases_passed": len(cases),
                "cases": cases,
                "notes": [
                    "Synthetic checkout JWT is hashed as an opaque raw string; no issuer-signature claim is made.",
                    "Open payment.reference delegation, cnf/KB-SD-JWT, receipts, SDK and live providers remain out of scope.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

from dataclasses import replace
import json

from agentic_payment_experiment import (
    PaymentRecoveryStatus,
    PaymentStatus,
)
from tests.test_webshop_payment_sidecar import WebShopPaymentSidecarTest


def main() -> None:
    case = WebShopPaymentSidecarTest(methodName="test_public_api_is_exported")
    case.setUp()

    original_gate = case.gate
    original_adaptation = case.adaptation
    original_payment = case.payment
    original_fulfillment = case.fulfillment

    canonical = case.assess()

    mismatch_results: dict[str, dict[str, object]] = {}
    mismatch_values = {
        "request_id": replace(
            case.adaptation.payment_request,
            request_id="rv-cross-composed-request",
        ),
        "amount": replace(
            case.adaptation.payment_request,
            amount=case.adaptation.payment_request.amount + 1,
        ),
        "currency": replace(
            case.adaptation.payment_request,
            currency="EUR",
        ),
        "category": replace(
            case.adaptation.payment_request,
            category="rv-other-category",
        ),
    }
    for name, request in mismatch_values.items():
        outcome = case.assess(
            adaptation=replace(case.adaptation, payment_request=request)
        )
        mismatch_results[name] = {
            "ready": outcome.ready,
            "effective_payment_is_null": outcome.effective_payment is None,
            "lifecycle_is_null": outcome.lifecycle is None,
            "retry_allowed": outcome.retry_allowed,
            "duplicate_payment_blocked": outcome.duplicate_payment_blocked,
            "reason_codes": list(outcome.reason_codes),
        }
        assert outcome.ready is False
        assert outcome.effective_payment is None
        assert outcome.lifecycle is None
        assert outcome.retry_allowed is False
        assert outcome.duplicate_payment_blocked is False
        assert "prerequisite:adapter_gate_request_mismatch" in outcome.reason_codes

    no_query_results: dict[str, dict[str, object]] = {}
    for status in (
        PaymentStatus.SUCCEEDED,
        PaymentStatus.UNKNOWN,
        PaymentStatus.PENDING,
        PaymentStatus.FAILED,
    ):
        attempt = replace(
            case.payment,
            payment_id=f"rv-related-{status.value.lower()}",
            status=status,
            provider_ref=f"rv-provider-{status.value.lower()}",
        )
        outcome = case.assess(known_attempts=(attempt,))
        no_query_results[status.value] = {
            "query_recovery_is_null": outcome.query_recovery is None,
            "duplicate_payment_blocked": outcome.duplicate_payment_blocked,
            "retry_allowed": outcome.retry_allowed,
            "reason_codes": list(outcome.reason_codes),
        }
        assert outcome.query_recovery is None
        assert outcome.retry_allowed is False
        if status is PaymentStatus.SUCCEEDED:
            assert outcome.duplicate_payment_blocked is True
            assert "duplicate:known_successful_attempt" in outcome.reason_codes
            assert "duplicate:payment_blocked" in outcome.reason_codes
        elif status in {PaymentStatus.UNKNOWN, PaymentStatus.PENDING}:
            assert outcome.duplicate_payment_blocked is True
            assert "duplicate:known_unresolved_attempt" in outcome.reason_codes
            assert "duplicate:payment_blocked" in outcome.reason_codes
        else:
            assert outcome.duplicate_payment_blocked is False
            assert "duplicate:payment_blocked" not in outcome.reason_codes

    unrelated = replace(
        case.payment,
        payment_id="rv-unrelated-success",
        request_id="rv-different-business-request",
        status=PaymentStatus.SUCCEEDED,
        provider_ref="rv-unrelated-provider",
    )
    unrelated_outcome = case.assess(known_attempts=(unrelated,))
    assert unrelated_outcome.duplicate_payment_blocked is False
    assert unrelated_outcome.retry_allowed is False
    assert "duplicate:payment_blocked" not in unrelated_outcome.reason_codes

    same_execution = replace(case.payment, status=PaymentStatus.SUCCEEDED)
    same_execution_outcome = case.assess(known_attempts=(same_execution,))
    assert same_execution_outcome.duplicate_payment_blocked is False

    failed_query = case.observation(
        PaymentStatus.FAILED,
        minutes=1,
        source="rv-query",
    )
    retry_candidate = case.assess(query_observation=failed_query)
    assert retry_candidate.query_recovery is not None
    assert (
        retry_candidate.query_recovery.recovery_status
        is PaymentRecoveryStatus.RETRY_CANDIDATE
    )
    assert retry_candidate.retry_allowed is True
    assert retry_candidate.duplicate_payment_blocked is False

    query_known_success = replace(
        case.payment,
        payment_id="rv-query-known-success",
        status=PaymentStatus.SUCCEEDED,
        provider_ref="rv-query-known-success-provider",
    )
    query_blocked = case.assess(
        query_observation=failed_query,
        known_attempts=(query_known_success,),
    )
    assert query_blocked.query_recovery is not None
    assert query_blocked.query_recovery.recovery_status is PaymentRecoveryStatus.BLOCKED
    assert query_blocked.duplicate_payment_blocked is True
    assert query_blocked.retry_allowed is False

    assert canonical.ready is True
    assert "prerequisite:adapter_gate_request_mismatch" not in canonical.reason_codes
    assert case.gate == original_gate
    assert case.adaptation == original_adaptation
    assert case.payment == original_payment
    assert case.fulfillment == original_fulfillment

    print(
        json.dumps(
            {
                "canonical_ready": canonical.ready,
                "mismatch_matrix": mismatch_results,
                "no_query_related_attempts": no_query_results,
                "unrelated_success_blocked": unrelated_outcome.duplicate_payment_blocked,
                "same_execution_blocked": same_execution_outcome.duplicate_payment_blocked,
                "query_retry_candidate": {
                    "recovery_status": retry_candidate.query_recovery.recovery_status.value,
                    "retry_allowed": retry_candidate.retry_allowed,
                },
                "query_known_success": {
                    "recovery_status": query_blocked.query_recovery.recovery_status.value,
                    "duplicate_payment_blocked": query_blocked.duplicate_payment_blocked,
                    "retry_allowed": query_blocked.retry_allowed,
                },
                "inputs_immutable": True,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

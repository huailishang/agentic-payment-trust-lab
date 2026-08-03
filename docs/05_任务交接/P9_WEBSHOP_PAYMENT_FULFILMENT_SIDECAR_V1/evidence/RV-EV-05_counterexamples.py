from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
from pathlib import Path

from agentic_payment_experiment import PaymentStatus


ROOT = Path(__file__).resolve().parents[4]
TEST_MODULE_PATH = ROOT / "tests" / "test_webshop_payment_sidecar.py"
SPEC = importlib.util.spec_from_file_location("rv_sidecar_tests", TEST_MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
TEST_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TEST_MODULE)
WebShopPaymentSidecarTest = TEST_MODULE.WebShopPaymentSidecarTest


def main() -> None:
    case = WebShopPaymentSidecarTest(methodName="runTest")
    case.setUp()

    mismatched_request = replace(
        case.adaptation.payment_request,
        request_id="cross-composed-request",
        amount=case.adaptation.payment_request.amount + 1,
    )
    mismatched_adaptation = replace(
        case.adaptation,
        payment_request=mismatched_request,
    )
    cross_composed = case.assess(adaptation=mismatched_adaptation)

    existing_success = replace(
        case.payment,
        payment_id="parallel-success-without-query",
        status=PaymentStatus.SUCCEEDED,
        provider_ref="parallel-provider-success",
    )
    known_attempt_only = case.assess(known_attempts=(existing_success,))

    result = {
        "cross_composed_gate_and_adapter": {
            "gate_request_id": case.gate.bound_request.request_id,
            "adapter_request_id": mismatched_request.request_id,
            "adapter_request_amount": str(mismatched_request.amount),
            "gate_request_amount": str(case.gate.bound_request.amount),
            "ready": cross_composed.ready,
            "effective_payment_status": (
                cross_composed.effective_payment.status.value
                if cross_composed.effective_payment
                else None
            ),
            "task_status": (
                cross_composed.lifecycle.task_status.value
                if cross_composed.lifecycle
                else None
            ),
            "reason_codes": list(cross_composed.reason_codes),
        },
        "known_success_attempt_without_query": {
            "initial_payment_status": case.payment.status.value,
            "known_attempt_status": existing_success.status.value,
            "query_recovery_present": known_attempt_only.query_recovery is not None,
            "duplicate_payment_blocked": known_attempt_only.duplicate_payment_blocked,
            "retry_allowed": known_attempt_only.retry_allowed,
            "reason_codes": list(known_attempt_only.reason_codes),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))

    failures: list[str] = []
    if cross_composed.ready:
        failures.append(
            "AC-02 violation: a Gate request and a different Adapter TransactionRequest were cross-composed without fail-closed binding verification"
        )
    if not known_attempt_only.duplicate_payment_blocked:
        failures.append(
            "AC-06 violation: a known successful parallel attempt was not exposed as duplicate-payment blocked when no query observation was supplied"
        )

    if failures:
        raise AssertionError("\n".join(failures))


if __name__ == "__main__":
    main()

from dataclasses import replace
import json

from agentic_payment_experiment.models import PaymentStatus
from tests.test_webshop_payment_sidecar import WebShopPaymentSidecarTest


case = WebShopPaymentSidecarTest(methodName="test_public_api_is_exported")
case.setUp()

mismatched_adaptation = replace(
    case.adaptation,
    payment_request=replace(
        case.adaptation.payment_request,
        request_id="cross-composed-request",
    ),
)
f01 = case.assess(adaptation=mismatched_adaptation)

known_success = replace(
    case.payment,
    payment_id="known-successful-attempt",
    status=PaymentStatus.SUCCEEDED,
    provider_ref="known-success-provider",
)
f02 = case.assess(known_attempts=(known_success,))

print(
    json.dumps(
        {
            "phase": "after_repair",
            "F-01": {
                "ready": f01.ready,
                "effective_payment_is_null": f01.effective_payment is None,
                "lifecycle_is_null": f01.lifecycle is None,
                "retry_allowed": f01.retry_allowed,
                "duplicate_payment_blocked": f01.duplicate_payment_blocked,
                "reason_codes": list(f01.reason_codes),
            },
            "F-02": {
                "ready": f02.ready,
                "query_recovery_is_null": f02.query_recovery is None,
                "retry_allowed": f02.retry_allowed,
                "duplicate_payment_blocked": f02.duplicate_payment_blocked,
                "reason_codes": list(f02.reason_codes),
            },
        },
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
)

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from agentic_payment_experiment import (
    FulfillmentStatus,
    PaymentStatus,
)
from tests.test_webshop_payment_sidecar import WebShopPaymentSidecarTest


case = WebShopPaymentSidecarTest(methodName="runTest")
case.setUp()

success = case.assess(
    payment=replace(case.payment, status=PaymentStatus.SUCCEEDED),
    fulfillment=replace(case.fulfillment, status=FulfillmentStatus.SUCCEEDED),
)
fulfillment_failed = case.assess(
    payment=replace(case.payment, status=PaymentStatus.SUCCEEDED),
    fulfillment=replace(
        case.fulfillment,
        status=FulfillmentStatus.FAILED,
        failure_code="merchant_did_not_fulfil",
    ),
)
query_recovered = case.assess(
    query_observation=case.observation(
        PaymentStatus.SUCCEEDED,
        minutes=1,
        source="query",
    ),
    fulfillment=replace(case.fulfillment, status=FulfillmentStatus.SUCCEEDED),
)
conflict = case.assess(
    query_observation=case.observation(
        PaymentStatus.SUCCEEDED,
        minutes=1,
        source="query",
    ),
    async_observation=case.observation(
        PaymentStatus.FAILED,
        minutes=2,
        source="async",
    ),
    fulfillment=replace(case.fulfillment, status=FulfillmentStatus.SUCCEEDED),
)
existing_success = replace(
    case.payment,
    payment_id="webshop-payment-success-existing",
    status=PaymentStatus.SUCCEEDED,
    provider_ref="provider-success-existing",
)
duplicate_blocked = case.assess(
    query_observation=case.observation(
        PaymentStatus.FAILED,
        minutes=1,
        source="query",
    ),
    known_attempts=(existing_success,),
)
retry_candidate = case.assess(
    query_observation=case.observation(
        PaymentStatus.FAILED,
        minutes=1,
        source="query",
    ),
)

payload = {
    "schema": "webshop-payment-fulfilment-sidecar-examples/v1",
    "payment_and_fulfilment_succeeded": success.to_dict(),
    "payment_succeeded_fulfilment_failed": fulfillment_failed.to_dict(),
    "query_recovered_to_succeeded": query_recovered.to_dict(),
    "query_async_terminal_conflict": conflict.to_dict(),
    "duplicate_successful_attempt_blocked": duplicate_blocked.to_dict(),
    "terminal_failed_offline_retry_candidate": retry_candidate.to_dict(),
    "side_effects_executed": {
        "payment": False,
        "retry": False,
        "status_query": False,
        "async_callback": False,
        "fulfilment": False,
        "refund": False,
        "dispute": False,
    },
}
output = Path(__file__).with_name("EV-01.sidecar_examples.json")
output.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

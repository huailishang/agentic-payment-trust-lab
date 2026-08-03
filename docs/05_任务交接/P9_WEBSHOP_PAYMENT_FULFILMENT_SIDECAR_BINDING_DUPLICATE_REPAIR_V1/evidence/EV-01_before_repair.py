from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
import types

from agentic_payment_experiment.models import PaymentStatus
from tests.test_webshop_payment_sidecar import WebShopPaymentSidecarTest


SOURCE_PATH = Path("src/agentic_payment_experiment/webshop_payment_sidecar.py")
EXPECTED_PARENT_SHA256 = "a7950308864d71a25b36c43ff11aed8cfeef1f0fe4d373ab305849b770f95c3b"

source = SOURCE_PATH.read_text(encoding="utf-8")
source = source.replace(
    """from .trusted_execution import (\n    ExecutionAttemptFact,\n    FollowUpAction,\n    VerificationStatus,\n    check_idempotency,\n    verify_original_transaction,\n)""",
    """from .trusted_execution import (\n    FollowUpAction,\n    VerificationStatus,\n    verify_original_transaction,\n)""",
)
source = source.replace(
    """    if query_observation is None:\n        related_attempts = _related_known_attempts(payment, known_attempts)\n        if any(\n            attempt.status is PaymentStatus.SUCCEEDED\n            for attempt in related_attempts\n        ):\n            duplicate_payment_blocked = True\n            reasons.extend(\n                (\n                    \"duplicate:known_successful_attempt\",\n                    \"duplicate:payment_blocked\",\n                )\n            )\n        elif any(\n            attempt.status in {PaymentStatus.UNKNOWN, PaymentStatus.PENDING}\n            for attempt in related_attempts\n        ):\n            duplicate_payment_blocked = True\n            reasons.extend(\n                (\n                    \"duplicate:known_unresolved_attempt\",\n                    \"duplicate:payment_blocked\",\n                )\n            )\n\n""",
    "",
)
source = source.replace(
    """    if fulfillment is None:\n        reasons.append(\"prerequisite:fulfillment_missing\")\n    if (\n        gate_outcome is not None\n        and gate_outcome.bound_request is not None\n        and adaptation is not None\n        and adaptation.payment_request is not None\n        and gate_outcome.bound_request\n        != replace(\n            adaptation.payment_request,\n            agent_id=gate_outcome.bound_request.agent_id,\n        )\n    ):\n        reasons.append(\"prerequisite:adapter_gate_request_mismatch\")\n    return _deduplicate(reasons)\n\n\ndef _related_known_attempts(\n    payment: PaymentExecutionRecord,\n    known_attempts: tuple[PaymentExecutionRecord, ...],\n) -> tuple[PaymentExecutionRecord, ...]:\n    attempt_facts = tuple(\n        ExecutionAttemptFact(\n            execution_id=attempt.payment_id,\n            request_id=attempt.request_id,\n            status=attempt.status.value,\n            idempotency_key=attempt.idempotency_key,\n        )\n        for attempt in known_attempts\n    )\n    idempotency_fact = check_idempotency(\n        idempotency_key=payment.idempotency_key,\n        request_id=payment.request_id,\n        current_execution_id=payment.payment_id,\n        known_attempts=attempt_facts,\n    )\n    related_execution_ids = {\n        attempt.execution_id for attempt in idempotency_fact.related_attempts\n    }\n    return tuple(\n        attempt\n        for attempt in known_attempts\n        if attempt.payment_id in related_execution_ids\n    )\n""",
    """    if fulfillment is None:\n        reasons.append(\"prerequisite:fulfillment_missing\")\n    return _deduplicate(reasons)\n""",
)

parent_sha256 = hashlib.sha256(source.encode("utf-8")).hexdigest()
if parent_sha256 != EXPECTED_PARENT_SHA256:
    raise RuntimeError(
        f"inverse patch did not reconstruct parent source: {parent_sha256}"
    )

legacy = types.ModuleType(
    "agentic_payment_experiment.webshop_payment_sidecar_before_repair"
)
legacy.__package__ = "agentic_payment_experiment"
sys.modules[legacy.__name__] = legacy
exec(compile(source, str(SOURCE_PATH), "exec"), legacy.__dict__)

case = WebShopPaymentSidecarTest(methodName="test_public_api_is_exported")
case.setUp()

mismatched_adaptation = replace(
    case.adaptation,
    payment_request=replace(
        case.adaptation.payment_request,
        request_id="cross-composed-request",
    ),
)
f01 = legacy.assess_webshop_payment_fulfilment(
    case.gate,
    mismatched_adaptation,
    case.mandate,
    case.payment,
    case.fulfillment,
)

known_success = replace(
    case.payment,
    payment_id="known-successful-attempt",
    status=PaymentStatus.SUCCEEDED,
    provider_ref="known-success-provider",
)
f02 = legacy.assess_webshop_payment_fulfilment(
    case.gate,
    case.adaptation,
    case.mandate,
    case.payment,
    case.fulfillment,
    known_attempts=(known_success,),
)

print(
    json.dumps(
        {
            "phase": "before_repair",
            "reconstructed_parent_sha256": parent_sha256,
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

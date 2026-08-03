from __future__ import annotations

import copy
import json
from pathlib import Path

from agentic_payment_experiment.adapters.x402 import (
    X402AdaptationStatus,
    adapt_x402_fixture,
)


FIXTURE_PATH = Path("samples/protocols/x402/x402_offline_cases_v1.json")
EXPECTED_REASON = "x402_string_invalid:payment_proof.proof_ref"


def main() -> int:
    document = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    fixture = copy.deepcopy(document["cases"][0])
    malformed = ["proof-as-list"]
    fixture["payment_proof"]["proof_ref"] = malformed
    fixture["facilitator_verification"]["proof_ref"] = malformed
    fixture["facilitator_settlement"]["proof_ref"] = malformed
    fixture["facilitator_settlement"]["payment_ref"] = malformed
    fixture["facilitator_async_observation"]["payment_ref"] = malformed
    fixture["resource_delivery"]["proof_ref"] = malformed

    adapted = adapt_x402_fixture(fixture)
    model_state = {
        "mandate": adapted.mandate,
        "order": adapted.order,
        "request": adapted.request,
        "payment": adapted.payment,
        "settlement_observation": adapted.settlement_observation,
        "async_observation": adapted.async_observation,
        "resource_delivery": adapted.resource_delivery,
        "delivery_attempts": adapted.delivery_attempts,
    }

    print("malformed_proof_ref_type=list")
    print(f"adapter_status={adapted.status.value}")
    print(f"reason_codes={list(adapted.reason_codes)}")
    for name, value in model_state.items():
        print(f"{name}={value}")

    passed = (
        adapted.status is X402AdaptationStatus.INVALID
        and EXPECTED_REASON in adapted.reason_codes
        and all(value is None for name, value in model_state.items() if name != "delivery_attempts")
        and adapted.delivery_attempts == ()
    )
    print(f"RESULT={'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

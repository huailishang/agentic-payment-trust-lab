from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from agentic_payment_experiment.adapters.x402 import (  # noqa: E402
    X402AdaptationStatus,
    adapt_x402_fixture,
)

FIXTURE_PATH = ROOT / "samples" / "protocols" / "x402" / "x402_offline_cases_v1.json"
document = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
base = copy.deepcopy(document["cases"][0])
base["fixture_version"] = document["fixture_version"]

# All linked proof identifiers use the same malformed list value. Equality checks
# therefore still succeed, but a bounded fail-closed adapter must reject the type.
malformed_proof_ref = ["proof-as-list"]
base["payment_proof"]["proof_ref"] = malformed_proof_ref
base["facilitator_verification"]["proof_ref"] = malformed_proof_ref
base["facilitator_settlement"]["proof_ref"] = malformed_proof_ref
base["facilitator_settlement"]["payment_ref"] = malformed_proof_ref
base["facilitator_async_observation"]["payment_ref"] = malformed_proof_ref
base["resource_delivery"]["proof_ref"] = malformed_proof_ref

result = adapt_x402_fixture(base)
print(f"malformed_proof_ref_type={type(malformed_proof_ref).__name__}")
print(f"adapter_status={result.status.value}")
print(f"reason_codes={list(result.reason_codes)}")
print(f"mapped_payment_id={result.payment.payment_id if result.payment else None}")

if result.status is not X402AdaptationStatus.INVALID:
    print("RESULT=FAIL: malformed reference type was coerced instead of rejected")
    raise SystemExit(1)

print("RESULT=PASS: malformed reference type rejected")

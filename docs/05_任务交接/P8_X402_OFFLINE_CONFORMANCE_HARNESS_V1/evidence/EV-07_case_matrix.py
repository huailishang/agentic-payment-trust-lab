from __future__ import annotations

import json
from pathlib import Path

from agentic_payment_experiment.x402_conformance import run_x402_conformance


FIXTURE = Path("samples/protocols/x402/x402_offline_cases_v1.json")


def main() -> int:
    report = run_x402_conformance(FIXTURE)
    matrix = []
    for result in report.results:
        matrix.append(
            {
                "case_id": result.case_id,
                "status": result.status.value,
                "expected": result.expected_outcome.value,
                "actual": result.actual_outcome.value,
                "reason_codes": list(result.reason_codes),
                "duplicate_or_concurrent_reuse": result.duplicate_or_concurrent_reuse,
                "successful_delivery_count": result.successful_delivery_count,
                "business_success_confirmed": result.business_success_confirmed,
                "resource": result.evidence.get("resource"),
                "payment_requirement": result.evidence.get("payment_requirement"),
                "payment_proof": result.evidence.get("payment_proof"),
                "facilitator_verification": result.evidence.get("facilitator_verification"),
                "facilitator_settlement": result.evidence.get("facilitator_settlement"),
                "facilitator_async_observation": result.evidence.get("facilitator_async_observation"),
                "resource_delivery": result.evidence.get("resource_delivery"),
                "payment_binding": result.evidence.get("payment_binding"),
                "idempotency": result.evidence.get("idempotency"),
                "payment_status_conflict": result.evidence.get("payment_status_conflict"),
                "replay": result.evidence.get("replay"),
            }
        )
    output = {
        "fixture_version": report.fixture_version,
        "synthetic_fixtures_only": report.synthetic_fixtures_only,
        "case_count": len(report.results),
        "all_pass": all(result.status.value == "PASS" for result in report.results),
        "side_effects": report.side_effects.to_dict(),
        "limitations": list(report.limitations),
        "matrix": matrix,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

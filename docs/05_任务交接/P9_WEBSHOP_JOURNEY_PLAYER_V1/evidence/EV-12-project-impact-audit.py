from __future__ import annotations

import hashlib
import json
from pathlib import Path

EVID = Path(__file__).resolve().parent
REPORT = EVID / "EV-AFTER-baseline.json"
EXPECTED_REPEAT_SHA = "fd0abca4e121187ce8ad3d172c2653d53ea06609870c20dfe70dc627ebecd647"
EXPECTED_NON_TRACE = "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"
EXPECTED_VALID = ["T01", "T02", "T03", "T04", "T07", "T08", "T09", "T10", "T12"]
EXPECTED_MATCHED = ["T01", "T02", "T03", "T04", "T07", "T08", "T09", "T12"]
NON_TRACE_FIELDS = (
    "actual_decision",
    "actual_callback_count",
    "actual_callback_observations",
    "actual_retry_count",
    "actual_final_environment_state",
    "actual_reason_codes",
    "known_payment_attempt_preflight_status",
    "known_payment_attempt_preflight_reason_codes",
    "known_payment_attempt_preflight_blocking_request_refs",
    "binding_status",
    "lineage_status",
    "effective_source_types",
    "required_facts_observed",
    "forbidden_side_effects",
    "limitations",
)


def digest(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    metrics = report["metrics"]
    repeat = report["repeatability"]
    by_id = {item["task_id"]: item for item in report["task_results"]}
    assert repeat["repeat_count"] == 3
    assert repeat["all_identical"] is True
    assert repeat["normalized_sha256"] == [EXPECTED_REPEAT_SHA] * 3
    assert metrics["product_observed_authoritative_trace_completeness_rate"] == {
        "count": 9,
        "denominator": 12,
        "rate": "0.750000",
    }
    assert metrics["governed_end_to_end_task_success_rate"] == {
        "count": 8,
        "denominator": 12,
        "rate": "0.666667",
    }
    assert metrics["callback_count_match_rate"] == {
        "count": 12,
        "denominator": 12,
        "rate": "1.000000",
    }
    assert metrics["duplicate_or_forbidden_side_effect_rate"] == {
        "count": 0,
        "denominator": 12,
        "rate": "0.000000",
    }
    valid = sorted(
        task_id
        for task_id, item in by_id.items()
        if item["actual"]["product_observed_trace_status"] == "VALID"
    )
    matched = sorted(task_id for task_id, item in by_id.items() if item["matched"])
    assert valid == EXPECTED_VALID
    assert matched == EXPECTED_MATCHED
    projection = [
        {
            "task_id": task_id,
            "actual": {
                key: by_id[task_id]["actual"].get(key)
                for key in NON_TRACE_FIELDS
            },
        }
        for task_id in sorted(by_id)
    ]
    non_trace_sha = digest(projection)
    assert non_trace_sha == EXPECTED_NON_TRACE, (EXPECTED_NON_TRACE, non_trace_sha)
    print(
        json.dumps(
            {
                "repeat_count": 3,
                "all_identical": True,
                "normalized_sha256": repeat["normalized_sha256"],
                "product_trace": "9/12",
                "gesr": "8/12",
                "callback_count_match": "12/12",
                "duplicate_or_forbidden_side_effect": "0/12",
                "valid_product_tasks": valid,
                "gesr_matched_tasks": matched,
                "non_trace_projection_sha256": non_trace_sha,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

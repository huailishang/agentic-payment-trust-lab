from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVID = Path(__file__).resolve().parent
REPORT = EVID / "EV-AFTER-baseline.json"
EXPECTED_NON_TRACE = "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"
EXPECTED_VALID = ["T01", "T02", "T03", "T04", "T07", "T08", "T09", "T10", "T12"]
EXPECTED_ABSENT = ["T05", "T06", "T11"]
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


def non_trace_projection(report: dict[str, object]) -> list[dict[str, object]]:
    by_id = {item["task_id"]: item for item in report["task_results"]}
    return [
        {
            "task_id": task_id,
            "actual": {
                key: by_id[task_id]["actual"].get(key)
                for key in NON_TRACE_FIELDS
            },
        }
        for task_id in sorted(by_id)
    ]


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    metrics = report["metrics"]
    repeatability = report["repeatability"]
    by_id = {item["task_id"]: item for item in report["task_results"]}

    assert repeatability["repeat_count"] == 3
    assert repeatability["all_identical"] is True
    assert len(set(repeatability["normalized_sha256"])) == 1
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
    valid = sorted(
        task_id
        for task_id, item in by_id.items()
        if item["actual"]["product_observed_trace_status"] == "VALID"
    )
    absent = sorted(
        task_id
        for task_id, item in by_id.items()
        if item["actual"]["product_observed_trace_status"] == "NOT_AVAILABLE"
    )
    assert valid == EXPECTED_VALID
    assert absent == EXPECTED_ABSENT
    matched = sorted(item["task_id"] for item in report["task_results"] if item["matched"])
    assert matched == ["T01", "T02", "T03", "T04", "T07", "T08", "T09", "T12"]
    non_trace_sha = digest(non_trace_projection(report))
    assert non_trace_sha == EXPECTED_NON_TRACE, (EXPECTED_NON_TRACE, non_trace_sha)

    output = {
        "repeat_count": repeatability["repeat_count"],
        "all_identical": repeatability["all_identical"],
        "normalized_sha256": repeatability["normalized_sha256"],
        "product_trace": "9/12",
        "gesr": "8/12",
        "valid_product_tasks": valid,
        "absent_product_tasks": absent,
        "matched_tasks": matched,
        "gesr_matched": "8/12",
        "non_trace_projection_sha256": non_trace_sha,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

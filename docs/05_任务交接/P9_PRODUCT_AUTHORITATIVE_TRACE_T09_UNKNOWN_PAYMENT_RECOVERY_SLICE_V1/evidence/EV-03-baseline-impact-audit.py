from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
RUNNER = ROOT / "scripts/validation/run_project_impact_baseline.py"
SPEC = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
BEFORE = (
    ROOT
    / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ASSEMBLER_EXTRACTION_V1/evidence/EV-03-after-baseline.json"
)
AFTER = EVIDENCE / "EV-03-after-baseline.json"
IMPACT = EVIDENCE / "EV-03-impact-comparison.json"
NON_TRACE = EVIDENCE / "EV-03-non-trace-projection.json"
EXPECTED_NON_TRACE_SHA256 = "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"
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


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metric(report: dict[str, Any], name: str) -> dict[str, Any]:
    return report["metrics"][name]


def by_task(report: dict[str, Any], task_id: str) -> dict[str, Any]:
    return next(item for item in report["task_results"] if item["task_id"] == task_id)


def main() -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    command = [
        sys.executable,
        str(RUNNER),
        "--spec",
        str(SPEC),
        "--repeat",
        "3",
        "--output",
        str(AFTER),
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=240,
        check=False,
    )
    print("INNER_COMMAND=" + " ".join(command))
    print(f"INNER_EXIT_CODE={result.returncode}")
    if result.stdout:
        print("INNER_STDOUT_BEGIN")
        print(result.stdout.rstrip())
        print("INNER_STDOUT_END")
    if result.stderr:
        print("INNER_STDERR_BEGIN")
        print(result.stderr.rstrip())
        print("INNER_STDERR_END")
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    before = json.loads(BEFORE.read_text(encoding="utf-8"))
    after = json.loads(AFTER.read_text(encoding="utf-8"))
    assert after["repeatability"]["all_identical"] is True
    assert after["repeatability"]["repeat_count"] == 3
    assert len(set(after["repeatability"]["normalized_sha256"])) == 1
    assert metric(before, "product_observed_authoritative_trace_completeness_rate") == {
        "count": 2,
        "denominator": 12,
        "rate": "0.166667",
    }
    assert metric(after, "product_observed_authoritative_trace_completeness_rate") == {
        "count": 3,
        "denominator": 12,
        "rate": "0.250000",
    }
    assert metric(before, "governed_end_to_end_task_success_rate") == {
        "count": 1,
        "denominator": 12,
        "rate": "0.083333",
    }
    assert metric(after, "governed_end_to_end_task_success_rate") == {
        "count": 2,
        "denominator": 12,
        "rate": "0.166667",
    }

    valid_product_tasks = [
        item["task_id"]
        for item in after["task_results"]
        if item["actual"]["product_observed_trace_status"] == "VALID"
    ]
    assert valid_product_tasks == ["T01", "T09", "T10"]
    t09_before = by_task(before, "T09")
    t09_after = by_task(after, "T09")
    assert t09_before["matched"] is False
    assert t09_before["actual"]["product_observed_trace_status"] == "NOT_AVAILABLE"
    assert t09_after["matched"] is True
    assert t09_after["capability_gaps"] == []
    assert t09_after["actual"]["product_observed_trace_status"] == "VALID"
    assert (
        t09_after["actual"]["product_observed_trace_source"]
        == "webshop_payment_fulfilment_outcome"
    )
    assert len(t09_after["actual"]["product_observed_trace_events"]) == 11

    final_state = t09_after["actual"]["actual_final_environment_state"]
    assert t09_after["actual"]["actual_decision"] == "ALLOW"
    assert t09_after["actual"]["actual_callback_count"] == 1
    assert t09_after["actual"]["actual_callback_observations"] == 1
    assert t09_after["actual"]["actual_retry_count"] == 0
    assert final_state["payment_status"] == "SUCCEEDED"
    assert final_state["recovery_status"] == "RECOVERED"
    assert final_state["fulfilment_status"] == "SUCCEEDED"
    assert final_state["task_status"] == "SUCCEEDED"
    assert final_state["remediation_status"] == "NOT_REQUIRED"
    assert final_state["retry_allowed"] is False
    assert final_state["duplicate_payment_blocked"] is False
    assert t09_after["actual"]["forbidden_side_effects"] == []

    projection = [
        {
            "task_id": task["task_id"],
            "actual": {field: task["actual"].get(field) for field in NON_TRACE_FIELDS},
        }
        for task in after["task_results"]
    ]
    NON_TRACE.write_text(
        json.dumps(projection, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    non_trace_sha256 = hashlib.sha256(canonical_bytes(projection)).hexdigest()
    assert non_trace_sha256 == EXPECTED_NON_TRACE_SHA256

    comparison = {
        "before_path": str(BEFORE.relative_to(ROOT)),
        "after_path": str(AFTER.relative_to(ROOT)),
        "before_output_sha256": file_sha256(BEFORE),
        "after_output_sha256": file_sha256(AFTER),
        "after_normalized_sha256": after["repeatability"]["normalized_sha256"],
        "product_trace_before": metric(
            before, "product_observed_authoritative_trace_completeness_rate"
        ),
        "product_trace_after": metric(
            after, "product_observed_authoritative_trace_completeness_rate"
        ),
        "gesr_before": metric(before, "governed_end_to_end_task_success_rate"),
        "gesr_after": metric(after, "governed_end_to_end_task_success_rate"),
        "valid_product_tasks": valid_product_tasks,
        "non_trace_projection_sha256": non_trace_sha256,
        "t09_before": {
            "matched": t09_before["matched"],
            "trace_status": t09_before["actual"]["product_observed_trace_status"],
        },
        "t09_after": {
            "matched": t09_after["matched"],
            "trace_status": t09_after["actual"]["product_observed_trace_status"],
            "trace_source": t09_after["actual"]["product_observed_trace_source"],
            "event_count": len(t09_after["actual"]["product_observed_trace_events"]),
            "capability_gaps": t09_after["capability_gaps"],
        },
    }
    IMPACT.write_text(
        json.dumps(comparison, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    print("repeatability_all_identical=True")
    print("product_trace_before=2/12:0.166667")
    print("product_trace_after=3/12:0.250000")
    print("gesr_before=1/12:0.083333")
    print("gesr_after=2/12:0.166667")
    print("valid_product_tasks=T01,T09,T10")
    print("t09_before=NOT_AVAILABLE,matched=False")
    print("t09_after=VALID,matched=True,events=11")
    print(f"non_trace_projection_sha256={non_trace_sha256}")
    print(f"after_output_sha256={file_sha256(AFTER)}")
    print(
        "after_normalized_sha256="
        + after["repeatability"]["normalized_sha256"][0]
    )
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

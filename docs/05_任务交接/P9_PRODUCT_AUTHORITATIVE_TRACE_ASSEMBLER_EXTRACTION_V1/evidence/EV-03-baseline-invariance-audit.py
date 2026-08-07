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
AFTER = EVIDENCE / "EV-03-after-baseline.json"
AUDIT = EVIDENCE / "EV-03-baseline-invariance.json"
NON_TRACE = EVIDENCE / "EV-03-non-trace-projection.json"
EXPECTED_OUTPUT_SHA256 = "8d4304dce72bb4f3d572512ee4d09e2e4bd2ee06f34ec4e8e6b0887acf059d9a"
EXPECTED_NORMALIZED_SHA256 = "56a82f9ab99cd5d83ae0b1259c2cef9f6b6cdf2a1b7183c029ba7569ab332619"
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

    report = json.loads(AFTER.read_text(encoding="utf-8"))
    output_sha256 = file_sha256(AFTER)
    normalized = report["repeatability"]["normalized_sha256"]
    assert output_sha256 == EXPECTED_OUTPUT_SHA256
    assert report["repeatability"]["all_identical"] is True
    assert report["repeatability"]["repeat_count"] == 3
    assert normalized == [EXPECTED_NORMALIZED_SHA256] * 3
    assert metric(report, "product_observed_authoritative_trace_completeness_rate") == {
        "count": 2,
        "denominator": 12,
        "rate": "0.166667",
    }
    assert metric(report, "governed_end_to_end_task_success_rate") == {
        "count": 1,
        "denominator": 12,
        "rate": "0.083333",
    }

    valid_product_tasks = [
        item["task_id"]
        for item in report["task_results"]
        if item["actual"]["product_observed_trace_status"] == "VALID"
    ]
    assert valid_product_tasks == ["T01", "T10"]
    t01 = by_task(report, "T01")
    t10 = by_task(report, "T10")
    assert t01["matched"] is True
    assert t01["capability_gaps"] == []
    assert t01["actual"]["product_observed_trace_source"] == "webshop_payment_fulfilment_outcome"
    assert len(t01["actual"]["product_observed_trace_events"]) == 11
    assert t10["actual"]["product_observed_trace_source"] == "webshop_gate_outcome"
    assert len(t10["actual"]["product_observed_trace_events"]) == 12

    projection = [
        {
            "task_id": task["task_id"],
            "actual": {field: task["actual"].get(field) for field in NON_TRACE_FIELDS},
        }
        for task in report["task_results"]
    ]
    NON_TRACE.write_text(
        json.dumps(projection, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    non_trace_sha256 = hashlib.sha256(canonical_bytes(projection)).hexdigest()
    assert non_trace_sha256 == EXPECTED_NON_TRACE_SHA256

    audit = {
        "output_sha256": output_sha256,
        "normalized_sha256": normalized,
        "product_trace": metric(
            report, "product_observed_authoritative_trace_completeness_rate"
        ),
        "gesr": metric(report, "governed_end_to_end_task_success_rate"),
        "valid_product_tasks": valid_product_tasks,
        "non_trace_projection_sha256": non_trace_sha256,
        "t01": {
            "matched": t01["matched"],
            "trace_source": t01["actual"]["product_observed_trace_source"],
            "event_count": len(t01["actual"]["product_observed_trace_events"]),
        },
        "t10": {
            "trace_source": t10["actual"]["product_observed_trace_source"],
            "event_count": len(t10["actual"]["product_observed_trace_events"]),
        },
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"baseline_output_sha256={output_sha256}")
    print(f"normalized_sha256={EXPECTED_NORMALIZED_SHA256}")
    print("repeat_count=3")
    print("product_trace=2/12:0.166667")
    print("gesr=1/12:0.083333")
    print("valid_product_tasks=T01,T10")
    print(f"non_trace_projection_sha256={non_trace_sha256}")
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FIXTURE = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
COVERAGE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1/evidence/EV-01-coverage-reference-grounding.json"
REPORT = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/RV-EV-03-after-baseline.json"

fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
coverage = json.loads(COVERAGE.read_text(encoding="utf-8"))
report = json.loads(REPORT.read_text(encoding="utf-8"))

fixture_by_id = {row["task_id"]: row for row in fixture["tasks"]}
coverage_by_id = {row["task_id"]: row for row in coverage["tasks"]}
report_by_id = {row["task_id"]: row for row in report["task_results"]}

rows = []
for task_id in sorted(fixture_by_id):
    if task_id == "T10":
        continue
    expected = set(fixture_by_id[task_id]["expected_product_observed_trace_events"])
    profile_events = {row["event_type"] for row in coverage_by_id[task_id]["events"]}
    missing_from_profile = sorted(expected - profile_events)
    capability_gaps = report_by_id[task_id]["capability_gaps"]
    non_trace_gaps = [
        gap for gap in capability_gaps
        if not gap.startswith("product_observed_trace_")
        and not gap.startswith("evidence_stages_missing:authoritative_trace")
    ]
    rows.append(
        {
            "task_id": task_id,
            "profile": coverage_by_id[task_id]["profile"],
            "profile_event_count": len(coverage_by_id[task_id]["events"]),
            "expected_events": sorted(expected),
            "missing_expected_event_in_profile": missing_from_profile,
            "non_trace_capability_gaps": non_trace_gaps,
            "ready_for_same_fixture_slice": not missing_from_profile and not non_trace_gaps,
        }
    )

print(json.dumps(rows, ensure_ascii=False, indent=2))
print("READY=" + ",".join(row["task_id"] for row in rows if row["ready_for_same_fixture_slice"]))

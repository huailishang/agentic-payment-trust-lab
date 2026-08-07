from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
BEFORE = EVIDENCE / "FIXTURE-before.json"
AFTER = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
RUNNER = ROOT / "scripts/validation/run_project_impact_baseline.py"
REGISTRY = ROOT / "src/agentic_payment_experiment/authoritative_trace.py"

EXPECTED_RUNNER_SHA256 = "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3"
EXPECTED_REGISTRY_SHA256 = "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(before: Any, after: Any, path: tuple[Any, ...] = ()) -> list[tuple[tuple[Any, ...], Any, Any]]:
    if type(before) is not type(after):
        return [(path, before, after)]
    if isinstance(before, dict):
        if set(before) != set(after):
            return [(path + ("<keys>",), sorted(before), sorted(after))]
        out: list[tuple[tuple[Any, ...], Any, Any]] = []
        for key in before:
            out.extend(walk(before[key], after[key], path + (key,)))
        return out
    if isinstance(before, list):
        if len(before) != len(after):
            return [(path + ("<length>",), len(before), len(after))]
        out: list[tuple[tuple[Any, ...], Any, Any]] = []
        for index, (left, right) in enumerate(zip(before, after)):
            out.extend(walk(left, right, path + (index,)))
        return out
    return [] if before == after else [(path, before, after)]


before = json.loads(BEFORE.read_text(encoding="utf-8"))
after = json.loads(AFTER.read_text(encoding="utf-8"))
diffs = walk(before, after)

expected: list[tuple[tuple[Any, ...], Any, Any]] = []
for task_index, task in enumerate(before["tasks"]):
    if task["task_id"] not in {"T02", "T03", "T04"}:
        continue
    events = task["expected_product_observed_trace_events"]
    event_index = events.index("DECISION_RECORDED")
    expected.append(
        (
            ("tasks", task_index, "expected_product_observed_trace_events", event_index),
            "DECISION_RECORDED",
            "PREPAYMENT_DECISION_RECORDED",
        )
    )

assert diffs == expected, (diffs, expected)
assert sha256(RUNNER) == EXPECTED_RUNNER_SHA256
assert sha256(REGISTRY) == EXPECTED_REGISTRY_SHA256

print(f"fixture_before_sha256={sha256(BEFORE)}")
print(f"fixture_after_sha256={sha256(AFTER)}")
print(f"runner_sha256={sha256(RUNNER)}")
print(f"authoritative_trace_sha256={sha256(REGISTRY)}")
print(f"semantic_diff_count={len(diffs)}")
for path, old, new in diffs:
    task = before["tasks"][path[1]]["task_id"]
    print(f"{task}: {old} -> {new}")
print("RESULT=PASS_EXACT_THREE_EVENT_NAME_REPLACEMENTS")

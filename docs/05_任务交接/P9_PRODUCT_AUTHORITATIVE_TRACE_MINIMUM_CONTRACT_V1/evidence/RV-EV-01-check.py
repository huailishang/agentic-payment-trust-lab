from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

runner = Path("scripts/validation/run_project_impact_baseline.py")
runner_source = runner.read_text(encoding="utf-8")
target = json.loads(
    Path(
        "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/"
        "evidence/EV-05-next-slice-target.json"
    ).read_text(encoding="utf-8")
)
design = Path("docs/03_架构设计/产品权威轨迹最小合同_v1.md").read_text(
    encoding="utf-8"
)
replay_tree = ast.parse(
    Path("src/agentic_payment_experiment/trusted_execution/replay.py").read_text(
        encoding="utf-8"
    )
)

event_values: list[str] = []
for node in replay_tree.body:
    if isinstance(node, ast.ClassDef) and node.name == "ReplayEventType":
        for item in node.body:
            if (
                isinstance(item, ast.Assign)
                and len(item.targets) == 1
                and isinstance(item.targets[0], ast.Name)
                and isinstance(item.value, ast.Constant)
                and isinstance(item.value.value, str)
            ):
                event_values.append(item.value.value)

required = target["required_event_sequence"]
runner_sha = hashlib.sha256(runner.read_bytes()).hexdigest()
reads_new_envelope = 'getattr(output, "authoritative_trace", None)' in runner_source
reads_legacy_events = (
    'getattr(output, "authoritative_trace_events", None)' in runner_source
)
requires_replay_event = "type(event) is not ReplayEvent" in runner_source
missing = [event for event in required if event not in event_values]

print("runner_sha256", runner_sha)
print("frozen_runner_sha256", target["source_runner"]["sha256"])
print("runner_reads_authoritative_trace", reads_new_envelope)
print("runner_reads_authoritative_trace_events", reads_legacy_events)
print("runner_requires_replay_event", requires_replay_event)
print(
    "design_requires_envelope",
    "authoritative_trace: ProductAuthoritativeTrace | None" in design,
)
print("legacy_replay_event_types", event_values)
print("next_slice_required_events", required)
print("required_events_missing_from_frozen_runner", missing)
print(
    "same_runner_can_validate_new_contract",
    reads_new_envelope and not missing and not requires_replay_event,
)

assert runner_sha == target["source_runner"]["sha256"]
assert not reads_new_envelope
assert reads_legacy_events
assert requires_replay_event
assert set(missing) == {"ACTION_RECORDED", "RESULT_RECORDED"}
print("finding", "BLOCKING_CONTRACT_CONTRADICTION")

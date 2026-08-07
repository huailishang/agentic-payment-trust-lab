from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVID = Path(__file__).resolve().parent
BASELINE = EVID / "BASELINE-fixture.json"
CURRENT = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
BASELINE_TEST = EVID / "BASELINE-test.py"
CURRENT_TEST = ROOT / "tests/test_project_impact_baseline.py"

before = json.loads(BASELINE.read_text(encoding="utf-8"))
after = json.loads(CURRENT.read_text(encoding="utf-8"))
expected = deepcopy(before)
by_id = {task["task_id"]: task for task in expected["tasks"]}
replacements = {
    "T05": ("DECISION_RECORDED", "ACTION_BINDING_DECISION_RECORDED"),
    "T06": ("DECISION_RECORDED", "ACTION_BINDING_DECISION_RECORDED"),
    "T07": ("INPUT_SOURCE_RECORDED", "LINEAGE_DECISION_RECORDED"),
    "T08": ("INPUT_SOURCE_RECORDED", "LINEAGE_DECISION_RECORDED"),
}
for task_id, (old, new) in replacements.items():
    events = by_id[task_id]["expected_product_observed_trace_events"]
    assert events.count(old) == 1, (task_id, events)
    events[events.index(old)] = new
assert after == expected, "fixture semantic changes exceed the frozen four scalar replacements"

before_by_id = {task["task_id"]: task for task in before["tasks"]}
after_by_id = {task["task_id"]: task for task in after["tasks"]}
for task_id, (old, new) in replacements.items():
    print(f"{task_id}:{old}->{new}")
    assert old in before_by_id[task_id]["expected_product_observed_trace_events"]
    assert new in after_by_id[task_id]["expected_product_observed_trace_events"]

for task_id in ("T07", "T08"):
    assert "POLICY_DECISION_RECORDED" in before_by_id[task_id]["expected_product_observed_trace_events"]
    assert "POLICY_DECISION_RECORDED" in after_by_id[task_id]["expected_product_observed_trace_events"]
print("T07_T08_policy_decision_unchanged=True")

baseline_test = BASELINE_TEST.read_text(encoding="utf-8")
current_test = CURRENT_TEST.read_text(encoding="utf-8")
assert "test_fixture_expected_product_events_are_subset_of_public_registry" not in baseline_test
assert current_test.count("def test_fixture_expected_product_events_are_subset_of_public_registry") == 1
method_start = current_test.index(
    "    def test_fixture_expected_product_events_are_subset_of_public_registry"
)
method_end = current_test.index(
    "    def test_t10_fixture_requires_zero_callback_and_preserves_business_goal",
    method_start,
)
assert current_test[:method_start] + current_test[method_end:] == baseline_test
assert "runtime_contract_primitive" in current_test
assert "_RUNTIME_CONTRACT_JSON" not in current_test
print("test_semantic_change=exactly_one_new_regression_method")
print("registry_subset_test_added=1")
print("public_runtime_contract_primitive=True")
print("private_runtime_contract_json_dependency=False")

print(f"baseline_fixture_sha256={hashlib.sha256(BASELINE.read_bytes()).hexdigest()}")
print(f"current_fixture_sha256={hashlib.sha256(CURRENT.read_bytes()).hexdigest()}")
print(f"baseline_test_sha256={hashlib.sha256(BASELINE_TEST.read_bytes()).hexdigest()}")
print(f"current_test_sha256={hashlib.sha256(CURRENT_TEST.read_bytes()).hexdigest()}")
print("semantic_diff_count=4")
print("RESULT=PASS")

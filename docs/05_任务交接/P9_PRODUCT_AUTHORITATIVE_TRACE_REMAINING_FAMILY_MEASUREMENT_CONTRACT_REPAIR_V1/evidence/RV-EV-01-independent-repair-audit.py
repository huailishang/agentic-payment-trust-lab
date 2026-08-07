from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
for entry in (ROOT, ROOT / "src"):
    sys.path.insert(0, str(entry))

from agentic_payment_experiment.authoritative_trace import runtime_contract_primitive

EVIDENCE = Path(__file__).resolve().parent
BASE_FIXTURE = EVIDENCE / "BASELINE-fixture.json"
BASE_TEST = EVIDENCE / "BASELINE-test.py"
CURRENT_FIXTURE = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
CURRENT_TEST = ROOT / "tests/test_project_impact_baseline.py"
PARENT_MANIFEST = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PREPAYMENT_FAMILY_TOOLKIT_COMPLETION_V1/evidence/SRC-start.sha256"
TASK_MANIFEST = EVIDENCE / "SRC-start.sha256"
RUNNER = ROOT / "scripts/validation/run_project_impact_baseline.py"
REGISTRY = ROOT / "src/agentic_payment_experiment/authoritative_trace.py"

EXPECTED_BASE_FIXTURE_SHA = "75e1682742e1eb576f62da89437bff766decde87d87ac73ad45de0ee59650ab5"
EXPECTED_BASE_TEST_SHA = "0e99995680e477fa4c65221dafc8cb5ce427ca57f655765a35786850fe9c2c96"
EXPECTED_RUNNER_SHA = "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3"
EXPECTED_REGISTRY_SHA = "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a"
EXPECTED_REPLACEMENTS = {
    ("tasks", 4, "expected_product_observed_trace_events", 3): ("DECISION_RECORDED", "ACTION_BINDING_DECISION_RECORDED"),
    ("tasks", 5, "expected_product_observed_trace_events", 3): ("DECISION_RECORDED", "ACTION_BINDING_DECISION_RECORDED"),
    ("tasks", 6, "expected_product_observed_trace_events", 0): ("INPUT_SOURCE_RECORDED", "LINEAGE_DECISION_RECORDED"),
    ("tasks", 7, "expected_product_observed_trace_events", 0): ("INPUT_SOURCE_RECORDED", "LINEAGE_DECISION_RECORDED"),
}
NEW_METHOD = "test_fixture_expected_product_events_are_subset_of_public_registry"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deep_diff(before, after, path=()):
    out = []
    if type(before) is not type(after):
        return [(path, before, after)]
    if isinstance(before, dict):
        keys = set(before) | set(after)
        for key in sorted(keys, key=str):
            if key not in before or key not in after:
                out.append((path + (key,), before.get(key), after.get(key)))
            else:
                out.extend(deep_diff(before[key], after[key], path + (key,)))
        return out
    if isinstance(before, list):
        if len(before) != len(after):
            out.append((path + ("__len__",), len(before), len(after)))
            return out
        for idx, (left, right) in enumerate(zip(before, after)):
            out.extend(deep_diff(left, right, path + (idx,)))
        return out
    if before != after:
        out.append((path, before, after))
    return out


assert sha(BASE_FIXTURE) == EXPECTED_BASE_FIXTURE_SHA
assert sha(BASE_TEST) == EXPECTED_BASE_TEST_SHA
assert sha(RUNNER) == EXPECTED_RUNNER_SHA
assert sha(REGISTRY) == EXPECTED_REGISTRY_SHA
print("frozen_hashes=PASS")

before = json.loads(BASE_FIXTURE.read_text(encoding="utf-8"))
after = json.loads(CURRENT_FIXTURE.read_text(encoding="utf-8"))
diffs = deep_diff(before, after)
assert len(diffs) == 4, diffs
actual_replacements = {path: (old, new) for path, old, new in diffs}
assert actual_replacements == EXPECTED_REPLACEMENTS, actual_replacements
for path, old, new in diffs:
    print("fixture_diff=" + "/".join(map(str, path)) + f":{old}->{new}")
print("fixture_semantic_diff_count=4")

# Compare the test AST after removing only the newly-added method.
base_tree = ast.parse(BASE_TEST.read_text(encoding="utf-8"))
cur_tree = ast.parse(CURRENT_TEST.read_text(encoding="utf-8"))

def class_methods(tree):
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ProjectImpactBaselineTest")
    return cls, {n.name: n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

base_cls, base_methods = class_methods(base_tree)
cur_cls, cur_methods = class_methods(cur_tree)
assert set(cur_methods) - set(base_methods) == {NEW_METHOD}
assert set(base_methods) - set(cur_methods) == set()
for name, node in base_methods.items():
    assert ast.dump(node, include_attributes=False) == ast.dump(cur_methods[name], include_attributes=False), name
new_source = ast.get_source_segment(CURRENT_TEST.read_text(encoding="utf-8"), cur_methods[NEW_METHOD]) or ""
assert "runtime_contract_primitive" in new_source
assert "_RUNTIME_CONTRACT_JSON" not in new_source
print("test_scope=ONLY_ONE_NEW_METHOD")
print(f"new_method={NEW_METHOD}")

contract = runtime_contract_primitive()
registry_events = {
    task["task_id"]: {event["event_type"] for event in task["events"]}
    for task in contract["tasks"]
}
fixture_events = {
    task["task_id"]: set(task["expected_product_observed_trace_events"])
    for task in after["tasks"]
}
assert set(registry_events) == set(fixture_events)
for task_id in sorted(fixture_events):
    missing = fixture_events[task_id] - registry_events[task_id]
    assert not missing, (task_id, sorted(missing))
print("registry_subset=12/12")

# Anchor src immutability to the previously accepted Evaluator snapshot, not only Executor's current-task copy.
assert PARENT_MANIFEST.read_bytes() == TASK_MANIFEST.read_bytes()
manifest = {}
for line in PARENT_MANIFEST.read_text(encoding="utf-8").splitlines():
    if line.strip():
        digest, rel = line.split(maxsplit=1)
        manifest[rel.lstrip("* ")] = digest
current_src = {
    p.relative_to(ROOT).as_posix(): sha(p)
    for p in sorted((ROOT / "src").rglob("*.py"))
}
assert current_src == manifest
print(f"src_python_file_count={len(current_src)}")
print("src_matches_parent_accepted_manifest=True")
print("RESULT=PASS")

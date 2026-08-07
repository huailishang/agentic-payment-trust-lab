import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
BEFORE = json.loads((EVIDENCE / "FIXTURE-before.json").read_text(encoding="utf-8"))
AFTER = json.loads((ROOT / "samples/evaluation/project_impact_baseline_v1.json").read_text(encoding="utf-8"))


def walk(a, b, path=""):
    out = []
    if type(a) is not type(b):
        return [(path, a, b)]
    if isinstance(a, dict):
        for key in sorted(set(a) | set(b)):
            p = f"{path}.{key}" if path else key
            if key not in a or key not in b:
                out.append((p, a.get(key), b.get(key)))
            else:
                out.extend(walk(a[key], b[key], p))
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append((path + ".length", len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(walk(x, y, f"{path}[{i}]"))
    elif a != b:
        out.append((path, a, b))
    return out


diffs = walk(BEFORE, AFTER)
print(f"semantic_diff_count={len(diffs)}")
for d in diffs:
    print(f"diff={d[0]} :: {d[1]!r} -> {d[2]!r}")

expected = []
for idx, task in enumerate(BEFORE["tasks"]):
    if task["task_id"] in {"T02", "T03", "T04"}:
        events = task["expected_product_observed_trace_events"]
        j = events.index("DECISION_RECORDED")
        expected.append((f"tasks[{idx}].expected_product_observed_trace_events[{j}]", "DECISION_RECORDED", "PREPAYMENT_DECISION_RECORDED"))
assert diffs == expected, (diffs, expected)

for rel, expected_hash in {
    "scripts/validation/run_project_impact_baseline.py": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
    "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
}.items():
    digest = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
    print(f"{rel}={digest}")
    assert digest == expected_hash

print("RESULT=PASS")

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent

# Verify every src/**/*.py hash against the Executor's task-start snapshot.
expected = {}
for line in (EVIDENCE / "SRC-start.sha256").read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    digest, rel = line.split(None, 1)
    expected[rel.strip()] = digest
current = {}
for p in sorted((ROOT / "src").rglob("*.py")):
    rel = p.relative_to(ROOT).as_posix()
    current[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
assert current == expected, "src Python hashes changed from repair start"
print(f"src_python_file_count={len(current)}")
print("src_hashes_unchanged_from_task_start=True")

parent = json.loads((ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PREPAYMENT_FAMILY_TOOLKIT_V1/evidence/DEV-after.json").read_text(encoding="utf-8"))
review = json.loads((EVIDENCE / "RV-EV-05-baseline.json").read_text(encoding="utf-8"))

def by_id(report):
    return {x["task_id"]: x for x in report["task_results"]}

p = by_id(parent)
r = by_id(review)
assert set(p) == set(r)
for tid in p:
    assert p[tid]["actual"] == r[tid]["actual"], f"actual output changed for {tid}"
print("all_12_actual_product_outputs_equal_parent_pre_repair=True")

for tid, decision in {"T02":"CONFIRMATION_REQUIRED", "T03":"CONFIRMATION_REQUIRED", "T04":"INDETERMINATE"}.items():
    actual = r[tid]["actual"]
    assert actual["actual_decision"] == decision
    assert actual["actual_callback_count"] == 0
    assert actual["actual_callback_observations"] == 0
    assert actual["actual_retry_count"] == 0
    assert actual["forbidden_side_effects"] == []
    assert r[tid]["matched"] is True
    assert r[tid]["capability_gaps"] == []
print("T02_T03_T04_business_guardrails=PASS")

for tid in ("T01", "T09", "T10", "T12"):
    actual = r[tid]["actual"]
    assert actual["product_observed_trace_status"] == "VALID"
print("T01_T09_T10_T12_product_trace_status=VALID")

non_trace_fields = (
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
projection = [
    {
        "task_id": item["task_id"],
        "actual": {field: item["actual"].get(field) for field in non_trace_fields},
    }
    for item in review["task_results"]
]
raw = json.dumps(projection, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
non_trace = hashlib.sha256(raw).hexdigest()
assert non_trace == "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"
print(f"non_trace_projection_sha256={non_trace}")
print("RESULT=PASS")

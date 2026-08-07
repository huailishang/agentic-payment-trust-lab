from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
START_HASHES = EVIDENCE / "SRC-start.sha256"
AFTER = EVIDENCE / "EV-AFTER-baseline.json"
PARENT = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PREPAYMENT_FAMILY_TOOLKIT_V1/evidence/DEV-after.json"
EXPECTED_NON_TRACE = "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_start_hashes() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in START_HASHES.read_text(encoding="utf-8").splitlines():
        digest, raw_path = line.split(maxsplit=1)
        out[raw_path.lstrip("* ")] = digest
    return out


start_hashes = load_start_hashes()
current_src = sorted((ROOT / "src").rglob("*.py"))
assert len(current_src) == len(start_hashes), (len(current_src), len(start_hashes))
for path in current_src:
    relative = path.relative_to(ROOT).as_posix()
    assert relative in start_hashes, relative
    assert sha256(path) == start_hashes[relative], relative

before = json.loads(PARENT.read_text(encoding="utf-8"))
after = json.loads(AFTER.read_text(encoding="utf-8"))
before_actual = {item["task_id"]: item["actual"] for item in before["task_results"]}
after_actual = {item["task_id"]: item["actual"] for item in after["task_results"]}
assert before_actual == after_actual

projection = [
    {
        "task_id": item["task_id"],
        "actual": {field: item["actual"].get(field) for field in NON_TRACE_FIELDS},
    }
    for item in after["task_results"]
]
non_trace = hashlib.sha256(canonical_bytes(projection)).hexdigest()
assert non_trace == EXPECTED_NON_TRACE

for task_id in ("T02", "T03", "T04"):
    actual = after_actual[task_id]
    assert actual["actual_callback_count"] == 0
    assert actual["actual_callback_observations"] == 0
    assert actual["actual_retry_count"] == 0
    assert actual["forbidden_side_effects"] == []

for task_id, source in {
    "T01": "webshop_payment_fulfilment_outcome",
    "T09": "webshop_payment_fulfilment_outcome",
    "T10": "webshop_gate_outcome",
    "T12": "webshop_payment_fulfilment_outcome",
}.items():
    actual = after_actual[task_id]
    assert actual["product_observed_trace_status"] == "VALID"
    assert actual["product_observed_trace_source"] == source

print(f"src_python_file_count={len(current_src)}")
print("src_hashes_unchanged_from_task_start=True")
print("all_12_actual_product_outputs_equal_parent_pre_repair=True")
print(f"non_trace_projection_sha256={non_trace}")
print("T02/T03/T04 callback=0,retry=0,forbidden_side_effects=[]")
print("T01/T09/T10/T12 product_trace_status=VALID and sources unchanged")
print("RESULT=PASS")

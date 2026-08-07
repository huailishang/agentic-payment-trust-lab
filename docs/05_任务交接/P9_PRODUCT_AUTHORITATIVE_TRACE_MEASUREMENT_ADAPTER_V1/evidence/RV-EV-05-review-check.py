from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_payment_experiment.authoritative_trace import runtime_registry_hashes

BASELINE_PATH = EVIDENCE / "RV-EV-03-baseline.json"
TARGET_PATH = EVIDENCE / "RV-EV-04-target.json"
RUNNER_PATH = ROOT / "scripts/validation/run_project_impact_baseline.py"
BASELINE_FIXTURE = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
TARGET_FIXTURE = ROOT / "samples/evaluation/project_impact_t10_preflight_target_v1.json"
MODULE_PATH = ROOT / "src/agentic_payment_experiment/authoritative_trace.py"

EXPECTED = {
    "runner": "cbeafe9a3badcc5a69e7972420a5c90bb815f84bdd0d5bcde3d05f739c072100",
    "baseline_fixture": "4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5",
    "target_fixture": "f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee",
    "baseline_output": "9c4964f51ff4e5ca0e8ec0f1e2d0012a7e1ad6e75787875504c93d62c57d6eab",
    "target_output": "ac3ec88433718bbd097f2738cd2330267107431ce18c9c7b2a45964f9971b488",
    "baseline_normalized": "4dfc7743909374689ec7b437b3a1b774d4d2e1155e287f3f8dc23430498b7044",
    "target_normalized": "c802bacfcd9154bdca7e36a5e9a8a2cdcfdc24158c0af96baf755aafa738a770",
    "non_trace_projection": "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc",
    "module": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
}

EXPECTED_REGISTRY = {
    "formula_registry": "2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd",
    "projection_registry": "45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4",
    "profiles": "6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2",
    "runtime_contract": "4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e",
}

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

PROTECTED_PATHS = (
    "src/agentic_payment_experiment/webshop_runtime_gate.py",
    "src/agentic_payment_experiment/webshop_payment_sidecar.py",
    "src/agentic_payment_experiment/attack_overlay.py",
    "src/agentic_payment_experiment/models.py",
    "src/agentic_payment_experiment/payment_recovery.py",
    "src/agentic_payment_experiment/payment_status_conflict.py",
    "src/agentic_payment_experiment/trusted_execution",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def check_report(report: dict[str, object], normalized: str) -> None:
    assert report["runner_sha256"] == EXPECTED["runner"]
    repeatability = report["repeatability"]
    assert isinstance(repeatability, dict)
    assert repeatability["all_identical"] is True
    assert repeatability["repeat_count"] == 3
    assert repeatability["normalized_sha256"] == [normalized] * 3
    summary = report["project_summary"]
    assert isinstance(summary, dict)
    assert summary["gap_task_ids"] == [f"T{i:02d}" for i in range(1, 13)]
    tasks = report["task_results"]
    assert isinstance(tasks, list) and len(tasks) == 12
    for row in tasks:
        assert isinstance(row, dict)
        actual = row["actual"]
        assert isinstance(actual, dict)
        assert actual["product_observed_trace_status"] == "NOT_AVAILABLE"
        assert actual["product_observed_trace_events"] == []
        assert actual["product_observed_trace_source"] is None


def main() -> None:
    baseline = load(BASELINE_PATH)
    target = load(TARGET_PATH)
    check_report(baseline, EXPECTED["baseline_normalized"])
    check_report(target, EXPECTED["target_normalized"])

    assert sha256(RUNNER_PATH) == EXPECTED["runner"]
    assert sha256(BASELINE_FIXTURE) == EXPECTED["baseline_fixture"]
    assert sha256(TARGET_FIXTURE) == EXPECTED["target_fixture"]
    assert sha256(BASELINE_PATH) == EXPECTED["baseline_output"]
    assert sha256(TARGET_PATH) == EXPECTED["target_output"]
    assert sha256(MODULE_PATH) == EXPECTED["module"]

    rows: list[dict[str, object]] = []
    for row in baseline["task_results"]:
        assert isinstance(row, dict)
        actual = row["actual"]
        assert isinstance(actual, dict)
        rows.append(
            {
                "task_id": row["task_id"],
                "actual": {field: actual.get(field) for field in NON_TRACE_FIELDS},
            }
        )
    non_trace_hash = canonical_hash(rows)
    assert non_trace_hash == EXPECTED["non_trace_projection"]

    hashes = dict(runtime_registry_hashes())
    assert hashes == EXPECTED_REGISTRY

    module_source = MODULE_PATH.read_text(encoding="utf-8")
    for forbidden in ("open(", "Path(", "CURRENT.md", "handoff evidence"):
        assert forbidden not in module_source

    diff = subprocess.run(
        ["git", "diff", "--name-only", "b4eff597ebffe79c575522b91642f82b26ad5247", "--", *PROTECTED_PATHS],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert diff == ""

    producer_hits: list[str] = []
    for relative in PROTECTED_PATHS:
        path = ROOT / relative
        files = sorted(path.rglob("*.py")) if path.is_dir() else [path]
        for file in files:
            if "authoritative_trace" in file.read_text(encoding="utf-8"):
                producer_hits.append(str(file.relative_to(ROOT)))
    assert producer_hits == []

    metrics = baseline["metrics"]
    assert isinstance(metrics, dict)
    expected_metrics = {
        "callback_count_match_rate": (12, 12),
        "duplicate_or_forbidden_side_effect_rate": (0, 12),
        "unsafe_allow_rate": (0, 5),
        "missed_confirmation_rate": (0, 2),
        "overconfident_decision_rate": (0, 2),
        "forbidden_state_write_rate": (0, 2),
        "binding_completeness_rate": (5, 5),
        "source_lineage_completeness_rate": (2, 2),
        "retry_count_match_rate": (12, 12),
        "decision_reason_consistency_rate": (11, 12),
        "product_observed_authoritative_trace_completeness_rate": (0, 12),
        "governed_end_to_end_task_success_rate": (0, 12),
    }
    for key, (count, denominator) in expected_metrics.items():
        value = metrics[key]
        assert isinstance(value, dict)
        assert value["count"] == count
        assert value["denominator"] == denominator

    print("baseline_output_sha256=" + sha256(BASELINE_PATH))
    print("target_output_sha256=" + sha256(TARGET_PATH))
    print("runner_sha256=" + sha256(RUNNER_PATH))
    print("module_sha256=" + sha256(MODULE_PATH))
    print("non_trace_projection_sha256=" + non_trace_hash)
    print("registry_hashes=" + json.dumps(hashes, sort_keys=True))
    print("protected_product_diff=[]")
    print("producer_hits=[]")
    print("product_trace=0/12")
    print("GESR=0/12")
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

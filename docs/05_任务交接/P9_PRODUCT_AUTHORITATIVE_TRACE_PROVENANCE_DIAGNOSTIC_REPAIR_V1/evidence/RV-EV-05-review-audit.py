from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent

OLD_BASELINE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/evidence/RV-EV-03-after-baseline.json"
OLD_TARGET = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/evidence/RV-EV-04-after-target.json"
NEW_BASELINE = EVIDENCE / "RV-EV-03-after-baseline.json"
NEW_TARGET = EVIDENCE / "RV-EV-04-after-target.json"
RUNNER = ROOT / "scripts/validation/run_project_impact_baseline.py"
MEASUREMENT_MODULE = ROOT / "src/agentic_payment_experiment/authoritative_trace.py"
GATE = ROOT / "src/agentic_payment_experiment/webshop_runtime_gate.py"
BUILDER = ROOT / "src/agentic_payment_experiment/webshop_authoritative_trace.py"
BASELINE_FIXTURE = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
TARGET_FIXTURE = ROOT / "samples/evaluation/project_impact_t10_preflight_target_v1.json"

EXPECTED = {
    "runner": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
    "measurement_module": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    "gate": "d148c1aaa5a77b4f551bf1f045180c4127e4d45731884fa611af421e24c5b3ec",
    "builder": "e6864905f4b67ef3024b7f7118b547c27c586127c60d537a3f5bab5a48f1e2c9",
    "baseline_fixture": "4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5",
    "target_fixture": "f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee",
    "non_trace": "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc",
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
ALLOWED_CHANGED_PATHS = {
    "runner_sha256",
    "repeatability.normalized_sha256.0",
    "repeatability.normalized_sha256.1",
    "repeatability.normalized_sha256.2",
    "task_results.T10.measurement_diagnostics.trace_provenance_separated",
    "task_results.T10.measurement_diagnostics_matched",
    "task_results.T10.measurement_integrity_gaps.length",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def task_map(report: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = report["task_results"]
    assert isinstance(rows, list)
    return {str(row["task_id"]): row for row in rows if isinstance(row, dict)}


def normalized_for_diff(report: dict[str, object]) -> dict[str, object]:
    copy = json.loads(json.dumps(report))
    rows = copy["task_results"]
    assert isinstance(rows, list)
    copy["task_results"] = {
        str(row["task_id"]): row for row in rows if isinstance(row, dict)
    }
    return copy


def diff_paths(old: object, new: object, prefix: str = "") -> set[str]:
    if type(old) is not type(new):
        return {prefix}
    if isinstance(old, dict):
        paths: set[str] = set()
        for key in set(old) | set(new):
            child = f"{prefix}.{key}" if prefix else str(key)
            if key not in old or key not in new:
                paths.add(child)
            else:
                paths |= diff_paths(old[key], new[key], child)
        return paths
    if isinstance(old, list):
        paths: set[str] = set()
        if len(old) != len(new):
            paths.add(prefix + ".length")
        for index, (left, right) in enumerate(zip(old, new)):
            child = f"{prefix}.{index}" if prefix else str(index)
            paths |= diff_paths(left, right, child)
        return paths
    return set() if old == new else {prefix}


def non_trace_projection(report: dict[str, object]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for task_id, row in sorted(task_map(report).items()):
        actual = row["actual"]
        assert isinstance(actual, dict)
        result.append(
            {
                "task_id": task_id,
                "actual": {field: actual.get(field) for field in NON_TRACE_FIELDS},
            }
        )
    return result


def check_pair(old_path: Path, new_path: Path, label: str) -> None:
    old = load(old_path)
    new = load(new_path)
    paths = diff_paths(normalized_for_diff(old), normalized_for_diff(new))
    assert paths == ALLOWED_CHANGED_PATHS, (label, sorted(paths))

    old_t10 = task_map(old)["T10"]
    new_t10 = task_map(new)["T10"]
    assert old_t10["measurement_diagnostics"]["trace_provenance_separated"] is False
    assert old_t10["measurement_diagnostics_matched"] is False
    assert old_t10["measurement_integrity_gaps"] == ["trace_provenance_not_separated"]
    assert new_t10["measurement_diagnostics"]["trace_provenance_separated"] is True
    assert new_t10["measurement_diagnostics_matched"] is True
    assert new_t10["measurement_integrity_gaps"] == []

    assert non_trace_projection(old) == non_trace_projection(new)
    assert canonical_hash(non_trace_projection(new)) == EXPECTED["non_trace"]

    new_metrics = new["metrics"]
    assert isinstance(new_metrics, dict)
    assert new_metrics["product_observed_authoritative_trace_completeness_rate"] == {
        "count": 1,
        "denominator": 12,
        "rate": "0.083333",
    }
    expected_gesr = 0 if label == "baseline" else 1
    assert new_metrics["governed_end_to_end_task_success_rate"] == {
        "count": expected_gesr,
        "denominator": 12,
        "rate": "0.000000" if expected_gesr == 0 else "0.083333",
    }

    actual = new_t10["actual"]
    assert isinstance(actual, dict)
    assert actual["product_observed_trace_status"] == "VALID"
    assert actual["product_observed_trace_source"] == "webshop_gate_outcome"
    assert actual["evaluator_synthesized_replay_provenance"] == "runner_constructed_from_fixed_facts"
    assert actual["actual_callback_count"] == 0
    assert actual["actual_retry_count"] == 0
    assert actual["forbidden_side_effects"] == []
    print(f"{label}_changed_paths={json.dumps(sorted(paths))}")


def main() -> None:
    assert sha256(RUNNER) == EXPECTED["runner"]
    assert sha256(MEASUREMENT_MODULE) == EXPECTED["measurement_module"]
    assert sha256(GATE) == EXPECTED["gate"]
    assert sha256(BUILDER) == EXPECTED["builder"]
    assert sha256(BASELINE_FIXTURE) == EXPECTED["baseline_fixture"]
    assert sha256(TARGET_FIXTURE) == EXPECTED["target_fixture"]

    check_pair(OLD_BASELINE, NEW_BASELINE, "baseline")
    check_pair(OLD_TARGET, NEW_TARGET, "target")

    target = load(NEW_TARGET)
    t10 = task_map(target)["T10"]
    assert t10["matched"] is True
    assert t10["capability_gaps"] == []
    assert target["project_summary"] == {
        "total_tasks": 12,
        "matched_tasks": 1,
        "gap_tasks": 11,
        "gap_task_ids": [
            "T01", "T02", "T03", "T04", "T05", "T06",
            "T07", "T08", "T09", "T11", "T12",
        ],
    }

    print("runner_sha256=" + sha256(RUNNER))
    print("non_trace_projection_sha256=" + EXPECTED["non_trace"])
    print("product_trace=1/12")
    print("target_gesr=1/12")
    print("t10_measurement_integrity_gaps=[]")
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

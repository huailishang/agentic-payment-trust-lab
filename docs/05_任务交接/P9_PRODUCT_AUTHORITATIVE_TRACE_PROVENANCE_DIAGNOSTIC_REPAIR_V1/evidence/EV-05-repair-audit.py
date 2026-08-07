from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
OLD_BASELINE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/evidence/EV-01-after-baseline.json"
OLD_TARGET = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/evidence/EV-01-after-target.json"
NEW_BASELINE = EVIDENCE / "EV-03-after-baseline.json"
NEW_TARGET = EVIDENCE / "EV-04-after-target.json"
OUTPUT = EVIDENCE / "EV-05-measurement-only-diff.json"

OLD_RUNNER_SHA256 = "cbeafe9a3badcc5a69e7972420a5c90bb815f84bdd0d5bcde3d05f739c072100"
NEW_RUNNER_SHA256 = "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3"
NON_TRACE_SHA256 = "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"
EXPECTED_FROZEN_HASHES = {
    "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    "src/agentic_payment_experiment/webshop_runtime_gate.py": "d148c1aaa5a77b4f551bf1f045180c4127e4d45731884fa611af421e24c5b3ec",
    "src/agentic_payment_experiment/webshop_authoritative_trace.py": "e6864905f4b67ef3024b7f7118b547c27c586127c60d537a3f5bab5a48f1e2c9",
    "samples/evaluation/project_impact_baseline_v1.json": "4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5",
    "samples/evaluation/project_impact_t10_preflight_target_v1.json": "f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee",
}
EXPECTED_REGISTRY_HASHES = {
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
EXPECTED_DIFF_SUFFIXES = {
    "$.runner_sha256",
    "$.repeatability.normalized_sha256[0]",
    "$.repeatability.normalized_sha256[1]",
    "$.repeatability.normalized_sha256[2]",
    "$.task_results[9].measurement_diagnostics.trace_provenance_separated",
    "$.task_results[9].measurement_diagnostics_matched",
    "$.task_results[9].measurement_integrity_gaps",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def recursive_diff(before: Any, after: Any, path: str = "$") -> list[dict[str, Any]]:
    if type(before) is not type(after):
        return [{"path": path, "before": before, "after": after}]
    if isinstance(before, dict):
        changes: list[dict[str, Any]] = []
        for key in sorted(set(before) | set(after)):
            child = f"{path}.{key}"
            if key not in before or key not in after:
                changes.append(
                    {"path": child, "before": before.get(key), "after": after.get(key)}
                )
            else:
                changes.extend(recursive_diff(before[key], after[key], child))
        return changes
    if isinstance(before, list):
        if len(before) != len(after):
            return [{"path": path, "before": before, "after": after}]
        changes = []
        for index, (left, right) in enumerate(zip(before, after)):
            changes.extend(recursive_diff(left, right, f"{path}[{index}]"))
        return changes
    if before != after:
        return [{"path": path, "before": before, "after": after}]
    return []


def by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["task_id"]: item for item in report["task_results"]}


def non_trace_projection(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "task_id": item["task_id"],
            "actual": {field: item["actual"].get(field) for field in NON_TRACE_FIELDS},
        }
        for item in report["task_results"]
    ]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


assert sha256(ROOT / "scripts/validation/run_project_impact_baseline.py") == NEW_RUNNER_SHA256
for relative, expected in EXPECTED_FROZEN_HASHES.items():
    assert sha256(ROOT / relative) == expected, relative

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
import importlib.util

runner_path = ROOT / "scripts/validation/run_project_impact_baseline.py"
spec = importlib.util.spec_from_file_location("provenance_repair_runner", runner_path)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)
from agentic_payment_experiment.authoritative_trace import runtime_registry_hashes

assert dict(runtime_registry_hashes()) == EXPECTED_REGISTRY_HASHES

positive_cases = {
    "neither_present": dict(
        product_status="NOT_AVAILABLE",
        product_source=None,
        replay_status="NOT_AVAILABLE",
        replay_provenance=None,
        evidence_stages=set(),
    ),
    "product_only": dict(
        product_status="VALID",
        product_source="explicit_product_outcome",
        replay_status="NOT_AVAILABLE",
        replay_provenance=None,
        evidence_stages={"authoritative_trace"},
    ),
    "replay_only": dict(
        product_status="NOT_AVAILABLE",
        product_source=None,
        replay_status="VALID",
        replay_provenance="runner_constructed_from_fixed_facts",
        evidence_stages={"evaluator_synthesized_replay"},
    ),
    "both_distinct": dict(
        product_status="VALID",
        product_source="webshop_gate_outcome",
        replay_status="VALID",
        replay_provenance="runner_constructed_from_fixed_facts",
        evidence_stages={"authoritative_trace", "evaluator_synthesized_replay"},
    ),
}
for name, values in positive_cases.items():
    assert runner._trace_provenance_separated(**values), name

valid_both = positive_cases["both_distinct"]
negative_cases = {
    "product_source_missing": {"product_source": None},
    "product_stage_missing": {"evidence_stages": {"evaluator_synthesized_replay"}},
    "product_absent_with_source": {
        "product_status": "NOT_AVAILABLE",
        "evidence_stages": {"evaluator_synthesized_replay"},
    },
    "replay_provenance_missing": {"replay_provenance": None},
    "replay_absent_with_provenance": {"replay_status": "NOT_AVAILABLE"},
    "identical_provenance": {
        "product_source": "runner_constructed_from_fixed_facts"
    },
    "unknown_product_status": {"product_status": "UNKNOWN"},
    "unknown_replay_status": {"replay_status": "UNKNOWN"},
    "blank_product_source": {"product_source": "  "},
    "blank_replay_provenance": {"replay_provenance": "  "},
    "unexpected_replay_provenance": {
        "replay_provenance": "some_other_replay_source"
    },
    "product_absent_with_stage": {
        "product_status": "NOT_AVAILABLE",
        "product_source": None,
    },
}
for name, overrides in negative_cases.items():
    values = {**valid_both, **overrides}
    assert not runner._trace_provenance_separated(**values), name

comparisons: dict[str, Any] = {}
for label, old_path, new_path, expected_trace, expected_gesr in (
    ("baseline", OLD_BASELINE, NEW_BASELINE, (1, 12, "0.083333"), (0, 12, "0.000000")),
    ("target", OLD_TARGET, NEW_TARGET, (1, 12, "0.083333"), (1, 12, "0.083333")),
):
    before = load(old_path)
    after = load(new_path)
    changes = recursive_diff(before, after)
    assert {item["path"] for item in changes} == EXPECTED_DIFF_SUFFIXES, changes
    assert before["runner_sha256"] == OLD_RUNNER_SHA256
    assert after["runner_sha256"] == NEW_RUNNER_SHA256
    assert after["repeatability"]["all_identical"] is True
    assert len(set(after["repeatability"]["normalized_sha256"])) == 1

    before_t10 = by_id(before)["T10"]
    after_t10 = by_id(after)["T10"]
    assert before_t10["measurement_diagnostics"]["trace_provenance_separated"] is False
    assert after_t10["measurement_diagnostics"]["trace_provenance_separated"] is True
    assert before_t10["measurement_integrity_gaps"] == [
        "trace_provenance_not_separated"
    ]
    assert after_t10["measurement_integrity_gaps"] == []
    assert before_t10["measurement_diagnostics_matched"] is False
    assert after_t10["measurement_diagnostics_matched"] is True
    assert after_t10["actual"]["product_observed_trace_status"] == "VALID"
    assert after_t10["actual"]["product_observed_trace_source"] == "webshop_gate_outcome"
    assert after_t10["actual"]["evaluator_synthesized_replay_provenance"] == (
        "runner_constructed_from_fixed_facts"
    )
    assert after_t10["actual"]["product_observed_trace_source"] != after_t10[
        "actual"
    ]["evaluator_synthesized_replay_provenance"]

    trace_metric = after["metrics"][
        "product_observed_authoritative_trace_completeness_rate"
    ]
    gesr_metric = after["metrics"]["governed_end_to_end_task_success_rate"]
    assert (trace_metric["count"], trace_metric["denominator"], trace_metric["rate"]) == expected_trace
    assert (gesr_metric["count"], gesr_metric["denominator"], gesr_metric["rate"]) == expected_gesr
    assert canonical_sha256(non_trace_projection(after)) == NON_TRACE_SHA256
    assert non_trace_projection(before) == non_trace_projection(after)

    comparisons[label] = {
        "before_output_sha256": sha256(old_path),
        "after_output_sha256": sha256(new_path),
        "after_normalized_sha256": after["repeatability"]["normalized_sha256"][0],
        "changes": changes,
        "product_trace_metric": trace_metric,
        "gesr_metric": gesr_metric,
        "t10_matched": after_t10["matched"],
        "t10_capability_gaps": after_t10["capability_gaps"],
        "non_trace_projection_sha256": canonical_sha256(non_trace_projection(after)),
    }

assert comparisons["target"]["t10_matched"] is True
assert comparisons["target"]["t10_capability_gaps"] == []

current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
assert "state: EXECUTING" in current
assert "current_role: Executor" in current

check = subprocess.run(
    ["git", "diff", "--check", "b4eff597ebffe79c575522b91642f82b26ad5247"],
    cwd=ROOT,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    check=False,
)
assert check.returncode == 0 and not check.stdout and not check.stderr

payload = {
    "schema": "provenance-diagnostic-repair-evidence/v1",
    "runner": {
        "old_sha256": OLD_RUNNER_SHA256,
        "new_sha256": NEW_RUNNER_SHA256,
    },
    "positive_truth_table": {name: True for name in positive_cases},
    "negative_truth_table": {name: False for name in negative_cases},
    "comparisons": comparisons,
    "frozen_hashes": EXPECTED_FROZEN_HASHES,
    "registry_hashes": EXPECTED_REGISTRY_HASHES,
    "non_trace_projection_sha256": NON_TRACE_SHA256,
}
OUTPUT.write_text(
    json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    encoding="utf-8",
)
print(f"runner_old_sha256={OLD_RUNNER_SHA256}")
print(f"runner_new_sha256={NEW_RUNNER_SHA256}")
print(f"positive_cases={len(positive_cases)}")
print(f"negative_cases={len(negative_cases)}")
print("baseline_exact_diff_count=7")
print("target_exact_diff_count=7")
print("t10_diagnostic_gap=[]")
print("product_trace=1/12")
print("target_gesr=1/12")
print(f"non_trace_projection_sha256={NON_TRACE_SHA256}")
print(f"output={OUTPUT.relative_to(ROOT).as_posix()}")
print(f"output_sha256={sha256(OUTPUT)}")
print("RESULT=PASS")

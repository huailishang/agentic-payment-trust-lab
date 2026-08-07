from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASELINE = Path(__file__).with_name("RV-EV-03-after-baseline.json")

EXPECTED_FILE_HASHES = {
    "scripts/validation/run_project_impact_baseline.py": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
    "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    "samples/evaluation/project_impact_baseline_v1.json": "4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5",
    "samples/evaluation/project_impact_t10_preflight_target_v1.json": "f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee",
}
EXPECTED_TASK_HASHES = {
    "src/agentic_payment_experiment/webshop_runtime_gate.py": "5abf1a6f08060e111b6fbd9ba96809c2823ef07adee0e23b6d60a6c50c06bdef",
    "src/agentic_payment_experiment/webshop_payment_sidecar.py": "833a34c005061a69b29265190b3c609ec92278afe0bb0d48a700546b548436f7",
    "src/agentic_payment_experiment/webshop_happy_path_authoritative_trace.py": "51b2d6873d66bb28ebbefa321f90e4ea4ab9a6d0102e38e9f8b312413b244880",
    "tests/test_webshop_runtime_gate.py": "e6b69601c8b14c18d0682200dc43f8cd583eb52a6807757fcde1aeeb3019b85e",
    "tests/test_webshop_payment_sidecar.py": "cea52a6649d207539c2b3f91b2bdc2a12f807c61b85603aeca31d632a7540a73",
    "tests/test_project_impact_baseline.py": "de4cec631b472390f8fc23293ab9030134dba26695a7c693645b65d689b42f46",
}
EXPECTED_REGISTRY_HASHES = {
    "formula_registry": "2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd",
    "projection_registry": "45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4",
    "profiles": "6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2",
    "runtime_contract": "4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e",
}
EXPECTED_NON_TRACE = "6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc"


def sha256_file(path: Path) -> str:
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


def non_trace_projection(report: dict[str, object]) -> list[dict[str, object]]:
    fields = (
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
    task_results = report["task_results"]
    assert isinstance(task_results, list)
    by_id = {item["task_id"]: item for item in task_results}
    return [
        {
            "task_id": task_id,
            "actual": {field: by_id[task_id]["actual"].get(field) for field in fields},
        }
        for task_id in sorted(by_id)
    ]


def embedded_registry_hashes() -> dict[str, str]:
    source_path = ROOT / "src/agentic_payment_experiment/authoritative_trace.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    raw_contract = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_RUNTIME_CONTRACT_JSON":
                    raw_contract = ast.literal_eval(node.value)
    assert isinstance(raw_contract, str)
    contract = json.loads(raw_contract)
    return {
        "formula_registry": canonical_hash(contract["projection_identity_formula_registry"]),
        "projection_registry": canonical_hash(contract["projection_registry"]),
        "profiles": canonical_hash(contract["tasks"]),
        "runtime_contract": hashlib.sha256(raw_contract.encode("utf-8")).hexdigest(),
    }


def architecture_observation() -> dict[str, object]:
    t01_path = ROOT / "src/agentic_payment_experiment/webshop_happy_path_authoritative_trace.py"
    t01_tree = ast.parse(t01_path.read_text(encoding="utf-8"))
    shared_helpers: list[str] = []
    for node in t01_tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "webshop_authoritative_trace":
            shared_helpers.extend(alias.name for alias in node.names)
    builder_names: set[str] = set()
    for path in (ROOT / "src/agentic_payment_experiment").glob("*authoritative_trace*.py"):
        text = path.read_text(encoding="utf-8")
        builder_names.update(re.findall(r"def (build_t\d+_[a-z0-9_]+)\(", text))
    return {
        "shared_private_helpers_reused_by_t01": sorted(shared_helpers),
        "task_specific_builders": sorted(builder_names),
        "task_specific_builder_count": len(builder_names),
        "assembler_extraction_recommended": bool(shared_helpers) and builder_names == {
            "build_t01_happy_path_trace",
            "build_t10_duplicate_preflight_trace",
        },
    }


def main() -> None:
    report = json.loads(BASELINE.read_text(encoding="utf-8"))
    task_results = report["task_results"]
    by_id = {item["task_id"]: item for item in task_results}

    file_hashes = {
        path: sha256_file(ROOT / path)
        for path in {**EXPECTED_FILE_HASHES, **EXPECTED_TASK_HASHES}
    }
    assert all(file_hashes[path] == expected for path, expected in EXPECTED_FILE_HASHES.items())
    assert all(file_hashes[path] == expected for path, expected in EXPECTED_TASK_HASHES.items())

    registry_hashes = embedded_registry_hashes()
    assert registry_hashes == EXPECTED_REGISTRY_HASHES

    repeatability = report["repeatability"]
    assert repeatability["repeat_count"] == 3
    assert repeatability["all_identical"] is True
    assert len(set(repeatability["normalized_sha256"])) == 1

    assert report["project_summary"] == {
        "total_tasks": 12,
        "matched_tasks": 1,
        "gap_tasks": 11,
        "gap_task_ids": ["T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10", "T11", "T12"],
    }
    assert report["metrics"]["governed_end_to_end_task_success_rate"] == {
        "count": 1,
        "denominator": 12,
        "rate": "0.083333",
    }
    assert report["metrics"]["product_observed_authoritative_trace_completeness_rate"] == {
        "count": 2,
        "denominator": 12,
        "rate": "0.166667",
    }

    t01 = by_id["T01"]
    assert t01["matched"] is True
    assert t01["capability_gaps"] == []
    assert t01["actual"]["product_observed_trace_status"] == "VALID"
    assert t01["actual"]["product_observed_trace_source"] == "webshop_payment_fulfilment_outcome"
    assert len(t01["actual"]["product_observed_trace_events"]) == 11
    assert t01["actual"]["actual_decision"] == "ALLOW"
    assert t01["actual"]["actual_callback_count"] == 1
    assert t01["actual"]["actual_callback_observations"] == 1
    assert t01["actual"]["actual_retry_count"] == 0
    final_state = t01["actual"]["actual_final_environment_state"]
    assert final_state["payment_status"] == "SUCCEEDED"
    assert final_state["fulfilment_status"] == "SUCCEEDED"
    assert final_state["task_status"] == "SUCCEEDED"
    assert final_state["retry_allowed"] is False
    assert t01["actual"]["forbidden_side_effects"] == []

    t10 = by_id["T10"]
    assert t10["actual"]["product_observed_trace_status"] == "VALID"
    assert t10["actual"]["product_observed_trace_source"] == "webshop_gate_outcome"
    assert len(t10["actual"]["product_observed_trace_events"]) == 12
    assert t10["measurement_integrity_gaps"] == []

    valid_product_tasks = {
        task_id
        for task_id, item in by_id.items()
        if item["actual"]["product_observed_trace_status"] == "VALID"
    }
    assert valid_product_tasks == {"T01", "T10"}

    non_trace_hash = canonical_hash(non_trace_projection(report))
    assert non_trace_hash == EXPECTED_NON_TRACE

    architecture = architecture_observation()
    assert architecture["assembler_extraction_recommended"] is True

    output = {
        "result": "PASS",
        "file_hashes": file_hashes,
        "registry_hashes": registry_hashes,
        "repeatability": repeatability,
        "project_summary": report["project_summary"],
        "gesr": report["metrics"]["governed_end_to_end_task_success_rate"],
        "product_trace": report["metrics"]["product_observed_authoritative_trace_completeness_rate"],
        "t01": {
            "matched": t01["matched"],
            "trace_status": t01["actual"]["product_observed_trace_status"],
            "trace_source": t01["actual"]["product_observed_trace_source"],
            "event_count": len(t01["actual"]["product_observed_trace_events"]),
            "capability_gaps": t01["capability_gaps"],
        },
        "t10": {
            "trace_status": t10["actual"]["product_observed_trace_status"],
            "trace_source": t10["actual"]["product_observed_trace_source"],
            "event_count": len(t10["actual"]["product_observed_trace_events"]),
            "measurement_integrity_gaps": t10["measurement_integrity_gaps"],
        },
        "valid_product_tasks": sorted(valid_product_tasks),
        "non_trace_projection_sha256": non_trace_hash,
        "architecture": architecture,
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    print("RESULT=PASS")


if __name__ == "__main__":
    main()

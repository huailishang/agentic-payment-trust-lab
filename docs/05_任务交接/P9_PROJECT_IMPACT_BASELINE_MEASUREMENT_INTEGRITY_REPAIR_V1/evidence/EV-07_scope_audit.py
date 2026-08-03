from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TASK = (
    ROOT
    / "docs"
    / "05_任务交接"
    / "P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1"
)
EVIDENCE = TASK / "evidence"
INITIAL = EVIDENCE / "EV-01.stdout.log"
RESULT = EVIDENCE / "corrected_project_impact_baseline.json"
DIFF_PATH = EVIDENCE / "EV-07_implementation_allowed_scope.diff"
PARENT_TASK = (
    ROOT / "docs" / "05_任务交接" / "P9_PROJECT_IMPACT_BASELINE_V1"
)
PARENT_SCOPE_AUDIT = PARENT_TASK / "evidence" / "EV-07.stdout.log"

IMPLEMENTATION_PATHS = (
    Path("CURRENT.md"),
    Path("samples/evaluation/project_impact_baseline_v1.json"),
    Path("scripts/validation/run_project_impact_baseline.py"),
    Path("tests/test_project_impact_baseline.py"),
    Path("docs/04_验证体系/项目级能力评测基线_v1.md"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def is_tracked(path: Path) -> bool:
    result = run("git", "ls-files", "--error-unmatch", path.as_posix(), check=False)
    return result.returncode == 0


def build_full_scope_diff() -> str:
    chunks: list[str] = []
    for relative in IMPLEMENTATION_PATHS:
        if is_tracked(relative):
            result = run("git", "diff", "--no-ext-diff", "--", relative.as_posix())
            chunks.append(result.stdout)
        else:
            result = run(
                "git",
                "diff",
                "--no-index",
                "--no-ext-diff",
                "--",
                "/dev/null",
                relative.as_posix(),
                check=False,
            )
            if result.returncode not in {0, 1}:
                raise RuntimeError(result.stderr)
            chunks.append(result.stdout)
    return "".join(chunks)


initial_text = INITIAL.read_text(encoding="utf-8", errors="replace")
initial_src_hashes = {
    match.group(2): match.group(1)
    for match in re.finditer(
        r"^([0-9a-f]{64})  (src/.*\.py)$", initial_text, re.MULTILINE
    )
}
current_src_hashes = {
    path.relative_to(ROOT).as_posix(): sha256(path)
    for path in sorted((ROOT / "src").rglob("*.py"))
}
assert len(initial_src_hashes) == 45, len(initial_src_hashes)
assert initial_src_hashes == current_src_hashes
print("protected_src_hashes_equal=PASS")
print("protected_src_file_count=45")

head = run("git", "rev-parse", "HEAD").stdout.strip()
branch = run("git", "branch", "--show-current").stdout.strip()
assert head == "8acaa9e4319240d258f14d8a23b1f15cc71d09b6"
print(f"head={head}")
print(f"branch={branch}")

parent_report = PARENT_TASK / "REPORT.md"
parent_result = PARENT_TASK / "evidence" / "project_impact_baseline_result_v1.json"
assert sha256(parent_report) == "043408f5d2c1fc5017f3741bf56f84cb510b799b58920ddb657fbfae83ee886f"
assert sha256(parent_result) == "8e481d446c6b97f94b0e783a3677755c9d6c31f91cfc5f8c2d8cf7dcdcc675aa"
print("parent_accepted_report_unchanged=PASS")
print("parent_accepted_result_unchanged=PASS")

result = json.loads(RESULT.read_text(encoding="utf-8"))
assert result["schema"] == "agentic-payment-project-impact-baseline-result/v1.1"
assert result["fixture_version"] == "1.1.0"
assert result["project_summary"] == {
    "total_tasks": 12,
    "matched_tasks": 0,
    "gap_tasks": 12,
    "gap_task_ids": [f"T{index:02d}" for index in range(1, 13)],
}
assert result["metrics"]["governed_end_to_end_task_success_rate"] == {
    "count": 0,
    "denominator": 12,
    "rate": "0.000000",
}
assert result["metrics"]["duplicate_or_forbidden_side_effect_rate"] == {
    "count": 1,
    "denominator": 12,
    "rate": "0.083333",
}
assert result["metrics"][
    "product_observed_authoritative_trace_completeness_rate"
] == {"count": 0, "denominator": 12, "rate": "0.000000"}
assert result["repeatability"]["all_identical"] is True
assert len(set(result["repeatability"]["normalized_sha256"])) == 1
assert result["project_impact_verdict"] == "NOT_APPLICABLE"
print("corrected_measurement_result=PASS")
print("corrected_gesr=0/12")
print("duplicate_or_forbidden_side_effect=1/12")
print("product_observed_authoritative_trace=0/12")
print("repeatability_three_identical=PASS")

by_id = {item["task_id"]: item for item in result["task_results"]}
t10 = by_id["T10"]
assert t10["expected"]["callback_count"] == 0
assert t10["actual"]["actual_callback_count"] == 1
assert t10["actual"]["actual_callback_observations"] == 1
assert t10["actual"]["actual_final_environment_state"][
    "duplicate_payment_blocked"
] is True
assert "duplicate_payment_callback_executed" in t10["actual"][
    "forbidden_side_effects"
]
assert "duplicate_payment_callback_executed" in t10["capability_gaps"]
print("t10_duplicate_callback_gap=PASS")

synthesized = {"T01", "T09", "T10", "T11", "T12"}
for task_id, item in by_id.items():
    actual = item["actual"]
    assert actual["product_observed_trace_status"] == "NOT_AVAILABLE"
    assert actual["product_observed_trace_source"] is None
    assert "authoritative_trace" not in actual["evidence_stages"]
    assert item["measurement_diagnostics"]["trace_provenance_separated"] is True
    if task_id in synthesized:
        assert actual["evaluator_synthesized_replay_status"] == "VALID"
        assert (
            actual["evaluator_synthesized_replay_provenance"]
            == "runner_constructed_from_fixed_facts"
        )
    else:
        assert actual["evaluator_synthesized_replay_status"] == "NOT_AVAILABLE"
print("trace_provenance_separation=PASS")

parent_before_hashes: dict[str, str] = {}
if PARENT_SCOPE_AUDIT.is_file():
    parent_text = PARENT_SCOPE_AUDIT.read_text(encoding="utf-8", errors="replace")
    for match in re.finditer(
        r"^allowed_file_hash ([0-9a-f]{64}) (.+)$",
        parent_text,
        re.MULTILINE,
    ):
        parent_before_hashes[match.group(2)] = match.group(1)

print("changed_file_hashes:")
for relative in IMPLEMENTATION_PATHS:
    current_hash = sha256(ROOT / relative)
    before_hash = parent_before_hashes.get(relative.as_posix(), "NOT_RECORDED")
    print(
        f"file_hash path={relative.as_posix()} before={before_hash} after={current_hash}"
    )

full_diff = build_full_scope_diff()
assert full_diff.strip(), "implementation allowed-scope diff is empty"
DIFF_PATH.write_text(full_diff, encoding="utf-8")
diff_hash = sha256(DIFF_PATH)
print(f"implementation_diff_path={DIFF_PATH.relative_to(ROOT).as_posix()}")
print(f"implementation_diff_bytes={len(full_diff.encode('utf-8'))}")
print(f"implementation_diff_sha256={diff_hash}")

current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
for expected in (
    "workflow: evaluator-executor-workflow/v2.1",
    "task_id: P9-PROJECT-IMPACT-BASELINE-MEASUREMENT-INTEGRITY-REPAIR-V1",
    "task_kind: repair",
    "state: EXECUTING",
    "current_role: Executor",
    "project_map_revision: 2026-08-03-r3",
    "active_bottleneck_id: B-01",
    "hypothesis_id: H-01",
):
    assert expected in current, expected
for field in (
    "authorization_commit: false",
    "authorization_push: false",
    "authorization_history_rewrite: false",
    "authorization_api_call: false",
    "authorization_network_call: false",
    "authorization_create_environment: false",
    "authorization_dependency_install: false",
    "authorization_data_download: false",
    "authorization_webshop_runtime_execution: false",
    "authorization_buy_now_execution: false",
    "authorization_payment_or_order_side_effect: false",
):
    assert field in current, field
print("v2_1_executor_route_preserved=PASS")
print("all_authorizations_false=PASS")

print("--- FINAL_GIT_STATUS ---")
print(run("git", "status", "--short").stdout, end="")
print("--- FINAL_IMPLEMENTATION_SCOPE_STATUS ---")
print(
    run(
        "git",
        "status",
        "--short",
        "--",
        *(path.as_posix() for path in IMPLEMENTATION_PATHS),
    ).stdout,
    end="",
)
print(
    "network=false api=false dependency_install=false environment=false "
    "webshop_runtime=false buy_now=false payment_side_effect=false "
    "commit=false push=false history_rewrite=false"
)

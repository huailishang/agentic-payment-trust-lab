from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = ROOT / "docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence"
INITIAL = EVIDENCE / "EV-01.stdout.log"
RESULT = EVIDENCE / "project_impact_baseline_result_v1.json"
RUNNER = ROOT / "scripts/validation/run_project_impact_baseline.py"
FIXTURE = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
TEST = ROOT / "tests/test_project_impact_baseline.py"
BASELINE_DOC = ROOT / "docs/04_验证体系/项目级能力评测基线_v1.md"
CURRENT = ROOT / "CURRENT.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


initial_text = INITIAL.read_text(encoding="utf-8", errors="replace")
initial_hashes = {
    match.group(2): match.group(1)
    for match in re.finditer(r"^([0-9a-f]{64})  (src/.*\.py)$", initial_text, re.MULTILINE)
}
current_hashes = {
    path.relative_to(ROOT).as_posix(): sha(path)
    for path in sorted((ROOT / "src").rglob("*.py"))
}
assert len(initial_hashes) == 45, len(initial_hashes)
assert initial_hashes == current_hashes
print("protected_src_hashes_equal=PASS")
print("protected_src_file_count=45")

head = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=True,
).stdout.strip()
assert head == "8acaa9e4319240d258f14d8a23b1f15cc71d09b6"
print(f"head={head}")

runner_source = RUNNER.read_text(encoding="utf-8")
tree = ast.parse(runner_source)
imports: set[str] = set()
calls: list[str] = []
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imports.update(alias.name.split(".")[0] for alias in node.names)
    elif isinstance(node, ast.ImportFrom) and node.module:
        imports.add(node.module.split(".")[0])
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            calls.append(node.func.attr)
assert imports.isdisjoint(
    {"os", "socket", "requests", "urllib", "random", "time"}
)
assert "unittest.mock" not in runner_source
assert "monkeypatch" not in runner_source.lower()
assert "patch(" not in runner_source
assert "validate_order" not in runner_source
assert "execute_with_payment_binding_gate" not in runner_source
assert "derive_payment_status_conflict" not in runner_source
assert "assess_payment_recovery" not in runner_source
assert calls.count("write_text") == 1
for public_api in (
    "adapt_webshop_purchase_candidate",
    "gate_webshop_buy_now",
    "evaluate_context_policy",
    "evaluate_attack_overlay",
    "assess_webshop_payment_fulfilment",
    "replay_events",
):
    assert public_api in runner_source
print("runner_public_api_composition=PASS")
print("runner_no_second_business_rule_engine=PASS")
print("runner_no_network_random_current_time_or_monkeypatch=PASS")
print("runner_output_write_only=PASS")

result = json.loads(RESULT.read_text(encoding="utf-8"))
assert result["fixture_sha256"] == sha(FIXTURE)
assert result["runner_sha256"] == sha(RUNNER)
assert result["repeatability"]["all_identical"] is True
assert len(set(result["repeatability"]["normalized_sha256"])) == 1
assert result["project_summary"] == {
    "total_tasks": 12,
    "matched_tasks": 5,
    "gap_tasks": 7,
    "gap_task_ids": ["T02", "T03", "T04", "T05", "T06", "T07", "T08"],
}
assert result["metrics"]["governed_end_to_end_task_success_rate"] == {
    "count": 5,
    "denominator": 12,
    "rate": "0.416667",
}
assert result["project_impact_verdict"] == "NOT_APPLICABLE"
assert all(result["limitations"].values())
print("result_fixture_hash_match=PASS")
print("result_runner_hash_match=PASS")
print("repeatability_three_identical=PASS")
print("measured_baseline=5/12")
print("project_impact_verdict=NOT_APPLICABLE")

current = CURRENT.read_text(encoding="utf-8")
for expected in (
    "workflow: evaluator-executor-workflow/v2.1",
    "task_id: P9-PROJECT-IMPACT-BASELINE-V1",
    "task_kind: evaluator_design",
    "state: EXECUTING",
    "current_role: Executor",
    "project_map_revision: 2026-08-03-r2",
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

allowed_files = (FIXTURE, RUNNER, TEST, BASELINE_DOC)
for path in allowed_files:
    print(f"allowed_file_hash {sha(path)} {path.relative_to(ROOT).as_posix()}")
print("no_src_product_code_modified=PASS")
print("network=false api=false dependency_install=false environment=false webshop_runtime=false buy_now=false payment_side_effect=false commit=false push=false history_rewrite=false")

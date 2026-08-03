from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TASK = ROOT / "docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1"
EVIDENCE = TASK / "evidence"
REPORT = TASK / "REPORT.md"
FIXTURE = ROOT / "samples/evaluation/project_impact_baseline_v1.json"
RUNNER = ROOT / "scripts/validation/run_project_impact_baseline.py"
RESULT = EVIDENCE / "corrected_project_impact_baseline.json"
DIFF = EVIDENCE / "EV-07_implementation_allowed_scope.diff"
INITIAL = EVIDENCE / "EV-01.stdout.log"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


initial_hashes: dict[str, str] = {}
for line in INITIAL.read_text(encoding="utf-8", errors="replace").splitlines():
    match = re.fullmatch(r"([0-9a-f]{64})  (src/.+\.py)", line)
    if match:
        initial_hashes[match.group(2)] = match.group(1)
current_hashes = {
    path.relative_to(ROOT).as_posix(): sha(path)
    for path in sorted((ROOT / "src").rglob("*.py"))
}
assert len(initial_hashes) == 45
assert current_hashes == initial_hashes

assert not (ROOT / "corrected_project_impact_baseline.json").exists()
assert sha(RESULT) == "58c0dee1a0f20e5e346c31cf097a5a11ac1e4c53f2fad52398d934828d039cd5"
result = json.loads(RESULT.read_text(encoding="utf-8"))
assert result["fixture_sha256"] == sha(FIXTURE)
assert result["runner_sha256"] == sha(RUNNER)
assert result["project_impact_verdict"] == "NOT_APPLICABLE"
assert result["repeatability"]["all_identical"] is True
assert len(set(result["repeatability"]["normalized_sha256"])) == 1

report = REPORT.read_text(encoding="utf-8")
diff_bytes = DIFF.stat().st_size
diff_sha = sha(DIFF)
assert diff_bytes == 136820
assert diff_sha == "5454acc257ab951aa131c6ca2b6e3f51e24e94f46c194c07725191b01f362a1e"
assert f"Bytes: {diff_bytes}" in report
assert f"SHA-256: {diff_sha}" in report
assert "根目录重复结果文件已精确删除" in report

paths = []
for line in DIFF.read_text(encoding="utf-8", errors="replace").splitlines():
    if line.startswith("diff --git "):
        paths.append(line)
assert len(paths) == 5
assert any("CURRENT.md" in line for line in paths)
assert any("samples/evaluation/project_impact_baseline_v1.json" in line for line in paths)
assert any("scripts/validation/run_project_impact_baseline.py" in line for line in paths)
assert any("tests/test_project_impact_baseline.py" in line for line in paths)
assert any("docs/04_" in line for line in paths)

source = RUNNER.read_text(encoding="utf-8")
tree = ast.parse(source)
imports = set()
calls = []
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
assert imports.isdisjoint({"os", "subprocess", "socket", "requests", "urllib", "random", "time"})
assert "unittest.mock" not in source
assert "monkeypatch" not in source.lower()
assert "patch(" not in source
assert "validate_order" not in source
assert "execute_with_payment_binding_gate" not in source
assert "derive_payment_status_conflict" not in source
assert "assess_payment_recovery" not in source
for public_api in (
    "adapt_webshop_purchase_candidate",
    "gate_webshop_buy_now",
    "evaluate_context_policy",
    "evaluate_attack_overlay",
    "assess_webshop_payment_fulfilment",
    "replay_events",
):
    assert public_api in source

current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
assert "state: READY_FOR_REVIEW" in current
assert "current_role: Evaluator" in current
assert not re.search(r"^authorization_.*: true$", current, re.MULTILINE)

print(
    json.dumps(
        {
            "protected_src_hashes_equal": True,
            "protected_src_file_count": len(current_hashes),
            "root_duplicate_absent": True,
            "corrected_result_sha256": sha(RESULT),
            "fixture_hash_matches_result": True,
            "runner_hash_matches_result": True,
            "repeatability_three_identical": True,
            "implementation_diff": {
                "bytes": diff_bytes,
                "sha256": diff_sha,
                "path_count": len(paths),
            },
            "runner_boundary": {
                "no_network_or_random_imports": True,
                "no_monkeypatch": True,
                "no_second_rule_engine": True,
                "public_api_composition": True,
            },
            "route": "READY_FOR_REVIEW / Evaluator",
            "all_authorizations_false": True,
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
)

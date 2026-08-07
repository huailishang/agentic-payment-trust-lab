from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASELINE = "b4eff597ebffe79c575522b91642f82b26ad5247"
ACTIVE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1"
CURRENT = ROOT / "CURRENT.md"
GATE = ROOT / "src/agentic_payment_experiment/webshop_runtime_gate.py"
BUILDER = ROOT / "src/agentic_payment_experiment/webshop_authoritative_trace.py"
REPORT = ACTIVE / "REPORT.md"

EXPECTED_HASHES = {
    ROOT / "scripts/validation/run_project_impact_baseline.py":
        "cbeafe9a3badcc5a69e7972420a5c90bb815f84bdd0d5bcde3d05f739c072100",
    ROOT / "src/agentic_payment_experiment/authoritative_trace.py":
        "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    ROOT / "samples/evaluation/project_impact_baseline_v1.json":
        "4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5",
    ROOT / "samples/evaluation/project_impact_t10_preflight_target_v1.json":
        "f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee",
    ROOT
    / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-01-target.json":
        "ac3ec88433718bbd097f2738cd2330267107431ce18c9c7b2a45964f9971b488",
}
EXPECTED_REGISTRY_HASHES = {
    "formula_registry": "2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd",
    "projection_registry": "45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4",
    "profiles": "6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2",
    "runtime_contract": "4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e",
}


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


checks: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: object = "") -> None:
    checks.append((name, bool(condition), str(detail)))


head = git("rev-parse", "HEAD").strip()
branch = git("branch", "--show-current").strip()
check("HEAD unchanged", head == BASELINE, head)
check("branch main", branch == "main", branch)

current_text = CURRENT.read_text(encoding="utf-8")
check(
    "current task",
    "task_id: P9-PRODUCT-AUTHORITATIVE-TRACE-T10-DUPLICATE-PREFLIGHT-SLICE-V1"
    in current_text,
)
check("state EXECUTING", "state: EXECUTING" in current_text)
check("role Executor", "current_role: Executor" in current_text)
for field in (
    "authorization_commit",
    "authorization_push",
    "authorization_history_rewrite",
    "authorization_api_call",
    "authorization_network_call",
    "authorization_data_download",
    "authorization_dependency_install",
    "authorization_create_environment",
    "authorization_webshop_runtime_execution",
    "authorization_buy_now_execution",
    "authorization_payment_or_order_side_effect",
):
    check(f"{field}=false", f"{field}: false" in current_text)

for path, expected in EXPECTED_HASHES.items():
    actual = sha256(path) if path.is_file() else "MISSING"
    check(f"frozen hash:{path.relative_to(ROOT).as_posix()}", actual == expected, actual)

sys.path.insert(0, str(ROOT / "src"))
from agentic_payment_experiment.authoritative_trace import runtime_registry_hashes

registry_hashes = dict(runtime_registry_hashes())
check(
    "runtime registry hashes frozen",
    registry_hashes == EXPECTED_REGISTRY_HASHES,
    json.dumps(registry_hashes, sort_keys=True),
)

src_diff = [
    line
    for line in git("diff", "--name-only", BASELINE, "--", "src").splitlines()
    if line
]
src_untracked = [
    line
    for line in git(
        "ls-files", "--others", "--exclude-standard", "--", "src"
    ).splitlines()
    if line
]
check(
    "only gate changed among tracked src",
    src_diff == ["src/agentic_payment_experiment/webshop_runtime_gate.py"],
    src_diff,
)
check(
    "only accepted measurement module and T10 builder untracked under src",
    src_untracked
    == [
        "src/agentic_payment_experiment/authoritative_trace.py",
        "src/agentic_payment_experiment/webshop_authoritative_trace.py",
    ],
    src_untracked,
)

test_diff = [
    line
    for line in git("diff", "--name-only", BASELINE, "--", "tests").splitlines()
    if line
]
test_untracked = [
    line
    for line in git(
        "ls-files", "--others", "--exclude-standard", "--", "tests"
    ).splitlines()
    if line
]
check(
    "only project baseline test changed among tracked tests",
    test_diff == ["tests/test_project_impact_baseline.py"],
    test_diff,
)
check(
    "only accepted trace test and T10 test untracked under tests",
    test_untracked
    == [
        "tests/test_authoritative_trace.py",
        "tests/test_webshop_authoritative_trace.py",
    ],
    test_untracked,
)
check(
    "project bottleneck map unchanged",
    not git(
        "diff",
        "--name-only",
        BASELINE,
        "--",
        "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md",
    ).strip(),
)

builder_source = BUILDER.read_text(encoding="utf-8")
for forbidden in (
    "ReplayEvent",
    "GateContext",
    "run_project_impact_baseline",
    "validate_request(",
    "verify_governed_payment_action(",
    "derive_known_payment_attempt_preflight(",
    "execute_with_payment_binding_gate(",
    "Path(",
    "open(",
    "read_text(",
    "getenv(",
    "import random",
    "random.",
    "datetime.now",
    "requests.",
    "socket.",
    "subprocess.",
):
    check(f"builder excludes:{forbidden}", forbidden not in builder_source)

allowed_relative_imports = {
    "authoritative_trace",
    "models",
    "trusted_execution",
}
relative_imports = set(
    re.findall(r"^from \.([a-zA-Z0-9_]+) import", builder_source, flags=re.MULTILINE)
)
check(
    "builder imports only accepted product facts and measurement contract",
    relative_imports == allowed_relative_imports,
    sorted(relative_imports),
)

gate_source = GATE.read_text(encoding="utf-8")
check(
    "outcome optional trace field",
    "authoritative_trace: ProductAuthoritativeTrace | None = None" in gate_source,
)
check(
    "exactly one builder call in gate",
    gate_source.count("build_t10_duplicate_preflight_trace(") == 1,
    gate_source.count("build_t10_duplicate_preflight_trace("),
)
check(
    "exactly one outcome attachment",
    gate_source.count(
        "return replace(base_outcome, authoritative_trace=authoritative_trace)"
    )
    == 1,
)

producer_hits: list[str] = []
for path in (ROOT / "src/agentic_payment_experiment").rglob("*.py"):
    if path in {
        ROOT / "src/agentic_payment_experiment/authoritative_trace.py",
        BUILDER,
        GATE,
    }:
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    if re.search(r"\bauthoritative_trace\s*=", text):
        producer_hits.append(path.relative_to(ROOT).as_posix())
check("no other product trace producer", not producer_hits, producer_hits)

required_files = (
    ACTIVE / "CONTRACT.md",
    REPORT,
    ACTIVE / "evidence/EV-01-run-measurement.py",
    ACTIVE / "evidence/EV-01-after-baseline.json",
    ACTIVE / "evidence/EV-01-after-target.json",
    ACTIVE / "evidence/EV-01-t10-before-after.json",
    ACTIVE / "evidence/EV-01-non-trace-business-projection.json",
    ACTIVE / "evidence/EV-01.meta.json",
    ACTIVE / "evidence/EV-02.meta.json",
    ACTIVE / "evidence/EV-03.meta.json",
    ACTIVE / "evidence/EV-04-trace-structure.py",
    ACTIVE / "evidence/EV-04-t10-product-trace.json",
    ACTIVE / "evidence/EV-04.meta.json",
)
for path in required_files:
    check(
        f"required artifact:{path.relative_to(ACTIVE).as_posix()}",
        path.is_file(),
    )

check("git diff check", not git("diff", "--check", BASELINE).strip())

failed = [(name, detail) for name, ok, detail in checks if not ok]
print(f"checks_total={len(checks)}")
print(f"checks_passed={len(checks) - len(failed)}")
print(f"checks_failed={len(failed)}")
print(f"head={head}")
print(f"branch={branch}")
print(f"src_diff={src_diff}")
print(f"src_untracked={src_untracked}")
print(f"test_diff={test_diff}")
print(f"test_untracked={test_untracked}")
print(f"producer_hits={producer_hits}")
print(f"registry_hashes={json.dumps(registry_hashes, sort_keys=True)}")
print(f"gate_sha256={sha256(GATE)}")
print(f"builder_sha256={sha256(BUILDER)}")
if failed:
    for name, detail in failed:
        print(f"FAIL\t{name}\t{detail}")
    raise SystemExit(1)
print("RESULT=PASS")

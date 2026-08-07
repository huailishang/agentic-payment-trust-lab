from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASELINE = "b4eff597ebffe79c575522b91642f82b26ad5247"
ACTIVE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1"
CONTRACT = ACTIVE / "CONTRACT.md"
CURRENT = ROOT / "CURRENT.md"
RUNTIME_MODULE = ROOT / "src/agentic_payment_experiment/authoritative_trace.py"
RUNNER = ROOT / "scripts/validation/run_project_impact_baseline.py"


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
check("HEAD unchanged from task baseline", head == BASELINE, head)
check("branch main", branch == "main", branch)

current_text = CURRENT.read_text(encoding="utf-8")
check(
    "current task id",
    "task_id: P9-PRODUCT-AUTHORITATIVE-TRACE-MEASUREMENT-ADAPTER-V1"
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

src_tracked_diff = [
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
check("no tracked src change", not src_tracked_diff, src_tracked_diff)
check(
    "only measurement module added under src",
    src_untracked == ["src/agentic_payment_experiment/authoritative_trace.py"],
    src_untracked,
)

script_diff = [
    line
    for line in git("diff", "--name-only", BASELINE, "--", "scripts").splitlines()
    if line
]
check(
    "only baseline runner changed under scripts",
    script_diff == ["scripts/validation/run_project_impact_baseline.py"],
    script_diff,
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
    "only existing project baseline test changed",
    test_diff == ["tests/test_project_impact_baseline.py"],
    test_diff,
)
check(
    "only authoritative trace test added",
    test_untracked == ["tests/test_authoritative_trace.py"],
    test_untracked,
)
check(
    "samples unchanged",
    not git("diff", "--name-only", BASELINE, "--", "samples").strip(),
)

product_files = (
    "src/agentic_payment_experiment/webshop_runtime_gate.py",
    "src/agentic_payment_experiment/webshop_payment_sidecar.py",
    "src/agentic_payment_experiment/attack_overlay.py",
    "src/agentic_payment_experiment/models.py",
)
for relative in product_files:
    current_hash = sha256(ROOT / relative)
    baseline_bytes = subprocess.run(
        ["git", "show", f"{BASELINE}:{relative}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout
    baseline_hash = hashlib.sha256(baseline_bytes).hexdigest()
    check(f"product unchanged:{relative}", current_hash == baseline_hash, current_hash)

producer_hits: list[str] = []
for path in (ROOT / "src/agentic_payment_experiment").rglob("*.py"):
    if path == RUNTIME_MODULE:
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    if re.search(r"(?<!events)\bauthoritative_trace\s*(?::[^=\n]+)?=", text):
        producer_hits.append(path.relative_to(ROOT).as_posix())
check("no product authoritative_trace producer", not producer_hits, producer_hits)

runtime_source = RUNTIME_MODULE.read_text(encoding="utf-8")
for forbidden in (
    "Path(",
    "open(",
    "read_text(",
    "CURRENT.md",
    "EV-01-build-grounded-reference-model",
    "GateContext",
):
    check(f"runtime excludes:{forbidden}", forbidden not in runtime_source)
check("runtime embeds registry", "_RUNTIME_CONTRACT_JSON" in runtime_source)
check(
    "runner reads exact authoritative_trace",
    'getattr(output, "authoritative_trace", None)' in RUNNER.read_text(encoding="utf-8"),
)
check(
    "runner does not read legacy event attribute",
    'getattr(output, "authoritative_trace_events"'
    not in RUNNER.read_text(encoding="utf-8"),
)

accepted_files = {
    ROOT
    / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-01-coverage-projection-identity-formula.json": "69b5c65eee924b011f606eb8284d0870971e40724f2fc62d59763cd18bcd703f",
    ROOT
    / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-01-projection-identity-vectors.json": "d8fbd0410f650c5efa36b9cae6ea81c38d4b997456c6c25a8e11c6279c2d1839",
}
for path, expected in accepted_files.items():
    check(
        f"accepted parent hash:{path.name}",
        sha256(path) == expected,
        sha256(path),
    )

parent_hashes = {
    ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md":
        "5ca8ab0d320517657b9ea4dc86e23a3473a633b13deac371a87e0c3a749cabf0",
    ROOT / "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md":
        "569565c129e29371d61ab33d7b63491dabfba4d665f14d82424b73a80023c31e",
    ROOT
    / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md":
        "966f69d8de9bf4d6e3ce2b5175d516c0ef306e14f4132b76acc4d642922dac34",
    ROOT
    / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md":
        "66079afd67f8fbc291817a5512b622bbb80a4b404f35bbc597998226d8f3f675",
    ROOT
    / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/REPORT.md":
        "fbde1da4cf4b5ddfdb4729cd485a9b72ad647ed9ac01639d0fba292a2399cead",
    ROOT
    / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/REVIEW.md":
        "b6e4f4e8ae42e3264328669bf7940cca6df368ab7d1ced96a0ad14fad5b4b56b",
}
parent_paths = list(parent_hashes)
for path, expected in parent_hashes.items():
    check(
        f"accepted inherited parent hash:{path.name}",
        path.is_file() and sha256(path) == expected,
        sha256(path) if path.is_file() else "MISSING",
    )

next_slice = parent_paths[3].read_text(encoding="utf-8")
check("NEXT_SLICE remains conditional", "State: `CONDITIONAL_NOT_FROZEN`" in next_slice)
check(
    "T10 formal capability contract absent",
    not (
        ROOT
        / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/CONTRACT.md"
    ).exists(),
)
check(
    "T10 V2 formal capability contract absent",
    not (
        ROOT
        / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V2/CONTRACT.md"
    ).exists(),
)

hashes = json.loads(
    subprocess.run(
        [
            "python3",
            "-c",
            (
                "import json; from agentic_payment_experiment.authoritative_trace "
                "import runtime_registry_hashes; print(json.dumps(dict(runtime_registry_hashes()), sort_keys=True))"
            ),
        ],
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src")},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout
)
expected_hashes = {
    "formula_registry": "2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd",
    "projection_registry": "45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4",
    "profiles": "6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2",
    "runtime_contract": "4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e",
}
check("embedded registry hashes accepted", hashes == expected_hashes, hashes)
check("git diff check", not git("diff", "--check", BASELINE).strip())

required_task_files = (
    ACTIVE / "CONTRACT.md",
    ACTIVE / "evidence/EV-00-generate-runtime-module.py",
    ACTIVE / "evidence/EV-01-run-measurement.py",
    ACTIVE / "evidence/EV-01-baseline.json",
    ACTIVE / "evidence/EV-01-target.json",
    ACTIVE / "evidence/EV-01-non-trace-business-projection.json",
    ACTIVE / "evidence/EV-01.meta.json",
    ACTIVE / "evidence/EV-02.meta.json",
    ACTIVE / "evidence/EV-03.meta.json",
)
for path in required_task_files:
    check(f"required task artifact:{path.name}", path.is_file())

failed = [(name, detail) for name, ok, detail in checks if not ok]
print(f"checks_total={len(checks)}")
print(f"checks_passed={len(checks) - len(failed)}")
print(f"checks_failed={len(failed)}")
print(f"head={head}")
print(f"src_tracked_diff={src_tracked_diff}")
print(f"src_untracked={src_untracked}")
print(f"script_diff={script_diff}")
print(f"test_diff={test_diff}")
print(f"test_untracked={test_untracked}")
print(f"producer_hits={producer_hits}")
print(f"embedded_hashes={json.dumps(hashes, sort_keys=True)}")
if failed:
    for name, detail in failed:
        print(f"FAIL\t{name}\t{detail}")
    raise SystemExit(1)
print("RESULT=PASS")

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASELINE = "979ffc505bec0b626858d0d186f655867b5491bf"
ACTIVE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1"
CURRENT = ROOT / "CURRENT.md"
PROJECT_MAP = ROOT / "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"
EV01_META = ACTIVE / "evidence/EV-01.meta.json"
VECTORS = ACTIVE / "evidence/EV-01-projection-identity-vectors.json"

PARENT_DIRS = [
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1",
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_SOURCE_BINDING_CONTRACT_REPAIR_V1",
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1",
]
NEXT_SLICE = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md"


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
check("current task", "task_id: P9-PRODUCT-AUTHORITATIVE-TRACE-PROJECTION-IDENTITY-FORMULA-REPAIR-V1" in current_text)
check("current executing", "state: EXECUTING" in current_text)
check("current role executor", "current_role: Executor" in current_text)
check("B-03 retained", "active_bottleneck_id: B-03" in current_text)
check("H-03 retained", "hypothesis_id: H-03" in current_text)
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

protected_roots = ["src", "tests", "scripts", "samples"]
protected_tracked = [line for line in git("ls-files", *protected_roots).splitlines() if line]
protected_diff = [line for line in git("diff", "--name-only", BASELINE, "--", *protected_roots).splitlines() if line]
protected_untracked = [line for line in git("ls-files", "--others", "--exclude-standard", "--", *protected_roots).splitlines() if line]
check("protected inventory", len(protected_tracked) == 130, len(protected_tracked))
check("protected tracked unchanged", not protected_diff, protected_diff)
check("protected untracked absent", not protected_untracked, protected_untracked)

tracked_diff = [line for line in git("diff", "--name-only", BASELINE).splitlines() if line]
allowed_tracked = {
    "CURRENT.md",
    "docs/03_架构设计/产品权威轨迹最小合同_v1.md",
    "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md",
    "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md",
    "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md",
}
check("tracked diff within allowed set", set(tracked_diff).issubset(allowed_tracked), tracked_diff)

project_map_diff = git("diff", "--name-only", BASELINE, "--", PROJECT_MAP.relative_to(ROOT).as_posix()).strip()
check("project map unchanged", not project_map_diff, project_map_diff)

meta = json.loads(EV01_META.read_text(encoding="utf-8"))
start_time = datetime.fromisoformat(meta["started_at_utc"])
start_timestamp = start_time.timestamp()
late_parent_files: list[str] = []
parent_file_count = 0
for directory in PARENT_DIRS:
    if not directory.exists():
        continue
    for path in directory.rglob("*"):
        if path.is_file():
            parent_file_count += 1
            if path.stat().st_mtime > start_timestamp + 1.0:
                late_parent_files.append(path.relative_to(ROOT).as_posix())
check("parent evidence inventory nonempty", parent_file_count > 0, parent_file_count)
check("parent EV/RV/report/review not modified after task start", not late_parent_files, late_parent_files)
check("NEXT_SLICE not modified after task start", NEXT_SLICE.stat().st_mtime <= start_timestamp + 1.0, NEXT_SLICE.stat().st_mtime)

vectors = json.loads(VECTORS.read_text(encoding="utf-8"))
parent_hashes = vectors["parent_fixed_artifact_hashes_before"]
parent_fixed_paths = {
    "EV-01-coverage-reference-grounding.json": PARENT_DIRS[0] / "evidence/EV-01-coverage-reference-grounding.json",
    "EV-01-reference-examples.json": PARENT_DIRS[0] / "evidence/EV-01-reference-examples.json",
    "EV-01-t10-grounded-instance.json": PARENT_DIRS[0] / "evidence/EV-01-t10-grounded-instance.json",
    "EV-01-t12-sidecar-examples.json": PARENT_DIRS[0] / "evidence/EV-01-t12-sidecar-examples.json",
}
for name, path in parent_fixed_paths.items():
    check(f"parent fixed hash:{name}", sha256(path) == parent_hashes[name], sha256(path))

src_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in (ROOT / "src").rglob("*.py"))
producer_patterns = [
    r"authoritative_trace\s*=\s*ProductAuthoritativeTrace",
    r"return\s+ProductAuthoritativeTrace\(",
]
producer_hits = [pattern for pattern in producer_patterns if re.search(pattern, src_text)]
check("no product trace producer", not producer_hits, producer_hits)

formal_contracts = [
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/CONTRACT.md",
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/CONTRACT.md",
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V2/CONTRACT.md",
]
check("no next formal contract", not any(path.exists() for path in formal_contracts), [str(path) for path in formal_contracts if path.exists()])

required = [
    ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md",
    ROOT / "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md",
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md",
    ACTIVE / "CONTRACT.md",
    ACTIVE / "REPORT.md",
    ACTIVE / "evidence/EV-01-coverage-projection-identity-formula.json",
    ACTIVE / "evidence/EV-01-projection-identity-vectors.json",
    ACTIVE / "evidence/EV-01.meta.json",
    ACTIVE / "evidence/EV-02.meta.json",
]
for path in required:
    check(f"required exists:{path.relative_to(ROOT).as_posix()}", path.is_file())

pycache_dirs = [path.relative_to(ROOT).as_posix() for path in ACTIVE.rglob("__pycache__") if path.is_dir()]
check("no current task pycache", not pycache_dirs, pycache_dirs)

trace_text = (ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md").read_text(encoding="utf-8")
check("product trace documented 0/12", "product-observed authoritative trace = 0/12 VALID" in trace_text)
check("GESR documented 0/12", "GESR = 0/12" in trace_text)
check("git diff check", not git("diff", "--check", BASELINE).strip())

failed = [(name, detail) for name, ok, detail in checks if not ok]
print(f"checks_total={len(checks)}")
print(f"checks_passed={len(checks) - len(failed)}")
print(f"checks_failed={len(failed)}")
print(f"head={head}")
print(f"protected_tracked_files={len(protected_tracked)}")
print(f"protected_diff_files={len(protected_diff)}")
print(f"protected_untracked_files={len(protected_untracked)}")
print(f"parent_file_count={parent_file_count}")
print(f"parent_files_modified_after_task_start={len(late_parent_files)}")
print(f"tracked_diff_files={len(tracked_diff)}")
if failed:
    for name, detail in failed:
        print(f"FAIL\t{name}\t{detail}")
    raise SystemExit(1)
print("RESULT=PASS")

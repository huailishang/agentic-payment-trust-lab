from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASELINE = "979ffc505bec0b626858d0d186f655867b5491bf"
CURRENT = ROOT / "CURRENT.md"
PROJECT_MAP = ROOT / "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"
ACTIVE = "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1/"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout


checks: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: object = "") -> None:
    checks.append((name, bool(condition), str(detail)))


head = git("rev-parse", "HEAD").strip()
check("HEAD unchanged from baseline", head == BASELINE, head)
check("branch main", git("branch", "--show-current").strip() == "main")

current_text = CURRENT.read_text(encoding="utf-8")
check("current task id", "task_id: P9-PRODUCT-AUTHORITATIVE-TRACE-REFERENCE-MODEL-GROUNDING-REPAIR-V1" in current_text)
check("state EXECUTING", "state: EXECUTING" in current_text)
check("role Executor", "current_role: Executor" in current_text)
check("baseline recorded", f"baseline_commit: {BASELINE}" in current_text)
check("B-03 retained", "active_bottleneck_id: B-03" in current_text)
check("H-03 retained", "hypothesis_id: H-03" in current_text)
for authorization in [
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
]:
    check(f"{authorization}=false", f"{authorization}: false" in current_text)

protected_roots = ["src", "tests", "scripts", "samples"]
protected_tracked = [line for line in git("ls-files", *protected_roots).splitlines() if line]
protected_diff = [line for line in git("diff", "--name-only", BASELINE, "--", *protected_roots).splitlines() if line]
protected_untracked = [line for line in git("ls-files", "--others", "--exclude-standard", "--", *protected_roots).splitlines() if line]
check("protected tracked inventory nonempty", len(protected_tracked) > 0, len(protected_tracked))
check("protected tracked files unchanged", not protected_diff, protected_diff)
check("protected untracked files absent", not protected_untracked, protected_untracked)

tracked_diff = [line for line in git("diff", "--name-only", BASELINE).splitlines() if line]
allowed_tracked = {
    "CURRENT.md",
    "docs/03_架构设计/产品权威轨迹最小合同_v1.md",
    "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md",
    "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md",
    "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md",
}
check("tracked diff exact allowed set", set(tracked_diff) == allowed_tracked, tracked_diff)

untracked = [line for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line]
allowed_untracked_prefixes = (
    ACTIVE,
    "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_SOURCE_BINDING_CONTRACT_REPAIR_V1/",
    "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/",
)
unexpected_untracked = [path for path in untracked if not path.startswith(allowed_untracked_prefixes)]
check("untracked files remain within active/inherited evidence", not unexpected_untracked, unexpected_untracked)

project_map_diff = git("diff", "--name-only", BASELINE, "--", PROJECT_MAP.relative_to(ROOT).as_posix()).strip()
check("project map unchanged", not project_map_diff, project_map_diff)

src_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in (ROOT / "src").rglob("*.py"))
producer_patterns = [
    r"authoritative_trace\s*=\s*ProductAuthoritativeTrace",
    r"return\s+ProductAuthoritativeTrace\(",
]
producer_hits = [pattern for pattern in producer_patterns if re.search(pattern, src_text)]
check("no product authoritative trace producer", not producer_hits, producer_hits)

formal_contract_candidates = [
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/CONTRACT.md",
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/CONTRACT.md",
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V2/CONTRACT.md",
]
check("no next formal contracts", not any(path.exists() for path in formal_contract_candidates), [str(path) for path in formal_contract_candidates if path.exists()])

active_path = ROOT / ACTIVE
required_outputs = [
    ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md",
    ROOT / "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md",
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md",
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md",
    active_path / "CONTRACT.md",
    active_path / "evidence/EV-01.meta.json",
    active_path / "evidence/EV-02.meta.json",
]
for path in required_outputs:
    check(f"required output exists:{path.relative_to(ROOT).as_posix()}", path.is_file())

check("product trace remains documented 0/12", "product-observed authoritative trace = 0/12 VALID" in (ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md").read_text(encoding="utf-8"))
check("GESR remains documented 0/12", "GESR = 0/12" in (ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md").read_text(encoding="utf-8"))

failed = [(name, detail) for name, ok, detail in checks if not ok]
print(f"checks_total={len(checks)}")
print(f"checks_passed={len(checks) - len(failed)}")
print(f"checks_failed={len(failed)}")
print(f"head={head}")
print(f"protected_tracked_files={len(protected_tracked)}")
print(f"protected_diff_files={len(protected_diff)}")
print(f"protected_untracked_files={len(protected_untracked)}")
print(f"tracked_diff_files={len(tracked_diff)}")
print(f"untracked_files={len(untracked)}")
if failed:
    for name, detail in failed:
        print(f"FAIL\t{name}\t{detail}")
    raise SystemExit(1)
print("RESULT=PASS")

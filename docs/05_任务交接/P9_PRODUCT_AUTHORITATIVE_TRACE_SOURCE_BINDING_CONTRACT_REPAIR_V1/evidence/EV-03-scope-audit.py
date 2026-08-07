from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASELINE = "979ffc505bec0b626858d0d186f655867b5491bf"
PROTECTED_PREFIXES = ("src/", "tests/", "scripts/", "samples/")


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def git_bytes(ref: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    return result.stdout


checks: list[dict[str, object]] = []


def record(name: str, passed: bool, detail: object) -> None:
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


head = run("git", "rev-parse", "HEAD")
record("head-equals-baseline", head.returncode == 0 and head.stdout.strip() == BASELINE, head.stdout.strip())

tracked = run("git", "ls-tree", "-r", "--name-only", BASELINE, "--", *[p.rstrip("/") for p in PROTECTED_PREFIXES])
protected_paths = [line for line in tracked.stdout.splitlines() if line.startswith(PROTECTED_PREFIXES)]
record("protected-list-readable", tracked.returncode == 0 and bool(protected_paths), {"count": len(protected_paths), "stderr": tracked.stderr})

changed: list[dict[str, str]] = []
missing: list[str] = []
for rel in protected_paths:
    current = ROOT / rel
    if not current.is_file():
        missing.append(rel)
        continue
    baseline_bytes = git_bytes(BASELINE, rel)
    current_bytes = current.read_bytes()
    if baseline_bytes != current_bytes:
        changed.append({
            "path": rel,
            "baseline_sha256": hashlib.sha256(baseline_bytes).hexdigest(),
            "current_sha256": hashlib.sha256(current_bytes).hexdigest(),
        })
record("protected-files-unchanged", not missing and not changed, {"missing": missing, "changed": changed})

untracked = run("git", "ls-files", "--others", "--exclude-standard", "--", *[p.rstrip("/") for p in PROTECTED_PREFIXES])
untracked_paths = [line for line in untracked.stdout.splitlines() if line]
record("protected-no-untracked", untracked.returncode == 0 and not untracked_paths, untracked_paths)

protected_diff = run("git", "diff", "--name-only", BASELINE, "--", *[p.rstrip("/") for p in PROTECTED_PREFIXES])
diff_paths = [line for line in protected_diff.stdout.splitlines() if line]
record("protected-git-diff-empty", protected_diff.returncode == 0 and not diff_paths, diff_paths)

producer_hits: list[dict[str, object]] = []
producer_patterns = [
    re.compile(r"^\s*authoritative_trace\s*:\s*", re.MULTILINE),
    re.compile(r"^\s*authoritative_trace\s*=\s*", re.MULTILINE),
    re.compile(r"['\"]authoritative_trace['\"]\s*:\s*(?!None\b)"),
]
for file in (ROOT / "src").rglob("*.py"):
    text = file.read_text(encoding="utf-8")
    for pattern in producer_patterns:
        matches = list(pattern.finditer(text))
        if matches:
            producer_hits.append({
                "path": file.relative_to(ROOT).as_posix(),
                "pattern": pattern.pattern,
                "matches": len(matches),
            })
record("no-product-authoritative-trace-producer", not producer_hits, producer_hits)

measurement_contract_candidates = [
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/CONTRACT.md",
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_MAINTENANCE_V1/CONTRACT.md",
]
t10_contract_candidates = [
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/CONTRACT.md",
    ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_CAPABILITY_V1/CONTRACT.md",
]
record(
    "measurement-adapter-contract-not-created",
    all(not path.exists() for path in measurement_contract_candidates),
    [str(path.relative_to(ROOT)) for path in measurement_contract_candidates if path.exists()],
)
record(
    "t10-capability-contract-not-created",
    all(not path.exists() for path in t10_contract_candidates),
    [str(path.relative_to(ROOT)) for path in t10_contract_candidates if path.exists()],
)

current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
record("router-stays-executing-executor", "state: EXECUTING" in current and "current_role: Executor" in current, {"state": "EXECUTING", "role": "Executor"})
record("all-side-effect-authorizations-false", all(
    f"{key}: false" in current
    for key in [
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
    ]
), "CURRENT authorization block")

passed = sum(1 for item in checks if item["passed"])
failed = [item for item in checks if not item["passed"]]
print(json.dumps({
    "baseline": BASELINE,
    "protected_file_count": len(protected_paths),
    "total_checks": len(checks),
    "passed": passed,
    "failed": len(failed),
    "checks": checks,
}, ensure_ascii=False, indent=2))

if failed:
    raise SystemExit(1)

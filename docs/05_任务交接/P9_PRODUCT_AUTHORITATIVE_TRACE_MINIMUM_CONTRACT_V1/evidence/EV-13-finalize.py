from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TASK = ROOT / "docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1"
REPORT = TASK / "REPORT.md"
FORMAL_OUTPUTS = [
    ROOT / "docs/03_架构设计/产品权威轨迹最小合同_v1.md",
    ROOT / "docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md",
    TASK / "NEXT_SLICE.md",
    REPORT,
]

manifest = []
for path in FORMAL_OUTPUTS:
    data = path.read_bytes()
    manifest.append(
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": len(data),
            "lines": len(path.read_text(encoding="utf-8").splitlines()),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    )

head = subprocess.run(
    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True
).stdout.strip()
status = subprocess.run(
    ["git", "-c", "core.quotePath=false", "status", "--short"],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=True,
).stdout.splitlines()

validator = subprocess.run(
    [
        "python3",
        "/mnt/d/SoftWare/VScode/install/Project/localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py",
        "--repo",
        ".",
        "--current",
        "CURRENT.md",
    ],
    cwd=ROOT,
    text=True,
    capture_output=True,
)

result = {
    "schema": "product-authoritative-trace-final-submission/v1",
    "head": head,
    "formal_outputs": manifest,
    "git_status": status,
    "validator_exit_code": validator.returncode,
    "validator_stdout": validator.stdout.strip(),
    "validator_stderr": validator.stderr.strip(),
    "report_executor_status_present": "Executor status: SUBMITTED_FOR_REVIEW" in REPORT.read_text(encoding="utf-8"),
    "router_preserved": {
        "state": "EXECUTING",
        "current_role": "Executor",
    },
}
result["all_pass"] = (
    result["validator_exit_code"] == 0
    and result["validator_stdout"] == "OK: v2.1 routing and required artifacts are structurally valid"
    and result["report_executor_status_present"]
)
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
if not result["all_pass"]:
    raise SystemExit(1)

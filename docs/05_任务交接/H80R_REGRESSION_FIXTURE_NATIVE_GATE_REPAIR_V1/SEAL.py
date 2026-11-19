"""Executor seals a complete, validated offline submission; never issues PASS."""
from datetime import datetime, timezone
import difflib
import json
from pathlib import Path
import subprocess
import sys

import CHECK

P = Path(__file__).resolve().parent
ROOT = P.parents[2]


def main():
    route = CHECK.route()
    CHECK.need(route["current_role"] == "Executor" and route["state"] == "EXECUTING", "submit as Executing/Executor")
    CHECK.preservation()
    gates = [path for path in (P / "evidence/l2/L2-GATE.json", P / "evidence/l2_retry_02/L2-GATE.json") if path.exists()]
    CHECK.need(bool(gates) and CHECK.read(gates[-1])["result"] == "PASS", "complete passing L2 required")
    CHECK.need(not (P / "SUBMISSION.json").exists(), "submission immutable; metadata repair requires preserving old submission first")
    gate = CHECK.read(gates[-1])
    CHECK.need(gate["checks_total"] == 4, "all checks required")
    for item in gate["checks"]:
        meta = CHECK.read(ROOT / item["meta"])
        CHECK.need(item["result"] == "PASS" and meta["exit_code"] == 0, "L2 triplet failed")
        for key in ("stdout", "stderr"):
            path = ROOT / item[key]
            CHECK.need(CHECK.sha(path) == meta[key + "_sha256"] and path.stat().st_size == meta[key + "_bytes"], "L2 triplet drift")
    report = P / "REPORT.md"
    CHECK.need(report.is_file() and "SUBMITTED_FOR_REVIEW" in report.read_text(encoding="utf-8"), "complete report required")
    validator = ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py"
    closeout = P / "evidence/executor_closeout"
    closeout.mkdir(parents=True, exist_ok=True)
    out = closeout / ("seal_" + str(len(list(closeout.glob("seal_*"))) + 1).zfill(2))
    out.mkdir(exist_ok=False)
    validated = subprocess.run([sys.executable, "-B", str(validator), "--repo", str(ROOT), "--current", "CURRENT.md"], cwd=ROOT, capture_output=True)
    (out / "WORKFLOW.stdout.log").write_bytes(validated.stdout)
    (out / "WORKFLOW.stderr.log").write_bytes(validated.stderr)
    CHECK.need(validated.returncode == 0, "fix report format before sealing; do not rerun passing L2")
    baseline = CHECK.read(P / "BASELINE.json")
    diff = []
    for rel in baseline["mutable"]:
        before = P / "references/before_h80r" / rel
        left = before.read_text(encoding="utf-8").splitlines(keepends=True) if before.exists() else []
        right = (ROOT / rel).read_text(encoding="utf-8").splitlines(keepends=True)
        diff.extend(difflib.unified_diff(left, right, fromfile="before/" + rel, tofile="after/" + rel))
    (out / "IMPLEMENTATION.diff").write_text("".join(diff), encoding="utf-8")
    (out / "WORKSPACE_STATUS.txt").write_bytes(subprocess.check_output(["git", "-c", "core.quotepath=false", "status", "--short"], cwd=ROOT))
    files = dict(baseline["files"])
    for rel in baseline["mutable"]:
        files[rel] = CHECK.sha(ROOT / rel)
    for path in P.rglob("*"):
        if path.is_file() and "runtime" not in path.relative_to(P).parts and "__pycache__" not in path.parts and path.name != "SUBMISSION.json":
            files[path.relative_to(ROOT).as_posix()] = CHECK.sha(path)
    data = {"schema": "h80r-executor-submission/v1", "task_id": P.name, "status": "SUBMITTED_FOR_REVIEW", "at_utc": datetime.now(timezone.utc).isoformat(), "baseline_head": baseline["head"], "files": files, "common_protected": baseline["common_protected"], "l2_gate_path": gates[-1].relative_to(ROOT).as_posix(), "formal_l2": len(gates), "formal_l3": 0, "actual_payment_calls": 0, "new_issuer_runs": 0, "active_minutes": "UNKNOWN unless separately measured in report", "historical_source_mode": "CAPTURED_OBSERVATION_REPLAY_NOT_CURRENT_AUTHENTICATION"}
    with (P / "SUBMISSION.json").open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"submitted_files": len(files), "l2_checks": 4, "verdict_issued": False}))


if __name__ == "__main__":
    main()

"""Capture final offline readiness evidence; no Docker/API/service calls."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

P = Path(__file__).resolve().parent
ROOT = P.parents[2]


def main():
    out = P / "evidence/design_completion"
    out.mkdir(parents=True, exist_ok=False)
    commands = {"preflight": [sys.executable, "-B", str(P / "CHECK.py"), "preflight"], "workflow": [sys.executable, "-B", str(ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py"), "--repo", str(ROOT), "--current", "CURRENT.md"], "diff_check": ["git", "diff", "--check"]}
    summary = {"scope": "TECHNICAL_PACKAGE_READINESS_ONLY_NOT_FORMAL_L2_L3", "begin_utc": datetime.now(timezone.utc).isoformat(), "actual_active_minutes": "UNKNOWN", "working_time_ceiling": None, "runtime_actions": 0, "next_missing_input": "EXPLICIT_RUNTIME_AUTHORITY", "checks": {}}
    for name, command in commands.items():
        started = datetime.now(timezone.utc).isoformat()
        run = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=180)
        (out / (name + ".stdout.log")).write_bytes(run.stdout)
        (out / (name + ".stderr.log")).write_bytes(run.stderr)
        meta = {"command": command, "start_utc": started, "end_utc": datetime.now(timezone.utc).isoformat(), "exit_code": run.returncode, "stdout_sha256": hashlib.sha256(run.stdout).hexdigest(), "stderr_sha256": hashlib.sha256(run.stderr).hexdigest()}
        (out / (name + ".meta.json")).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        summary["checks"][name] = meta
    summary["frozen_files"] = json.loads((P / "FREEZE.json").read_text(encoding="utf-8"))["files"]
    summary["prior_regressions"] = {"identity_context": 28, "stripe": 19, "safety": 9, "business": 74, "result": "PASS", "evidence": "docs/05_任务交接/H75_REAL_AUTHORITY_SOURCE_QUALIFICATION_V1/evidence/continuation/package_checks/regressions.stderr.log"}
    summary["offline_checker_probes"] = {"groups": 7, "result": "PASS", "actual_docker_calls": 0, "evidence": "docs/05_任务交接/H75_REAL_AUTHORITY_SOURCE_QUALIFICATION_V1/evidence/continuation/package_checks/CHECKER_PROBES.json"}
    summary["end_utc"] = datetime.now(timezone.utc).isoformat()
    summary["result"] = "PASS" if all(x["exit_code"] == 0 for x in summary["checks"].values()) else "FAIL"
    (out / "READINESS.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"readiness": summary["result"], "formal_runtime": "NOT_RUN", "remaining": summary["next_missing_input"]}))
    raise SystemExit(0 if summary["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()

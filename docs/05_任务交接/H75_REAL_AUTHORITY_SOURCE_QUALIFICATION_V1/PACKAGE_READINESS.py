"""Offline task-package validation; never calls Docker or a live issuer."""
from __future__ import annotations
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
NEXT = P.parent / "H76_SPIRE_ISSUED_WORKLOAD_POSSESSION_MEASUREMENT_V1"
OUT = P / "evidence/continuation/package_checks"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location("h76_bootstrap", NEXT / "BOOTSTRAP.py")
    bootstrap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bootstrap)
    env = bootstrap.environment()
    commands = {
        "preflight": [sys.executable, "-B", str(NEXT / "CHECK.py"), "preflight"],
        "regressions": [sys.executable, "-B", str(NEXT / "CHECK.py"), "regressions"],
        "workflow": [sys.executable, "-B", str(ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py"), "--repo", str(ROOT), "--current", "CURRENT.md"],
        "diff_check": ["git", "diff", "--check"],
    }
    summary = {"begin_utc": datetime.now(timezone.utc).isoformat(), "scope": "OFFLINE_PACKAGE_READINESS_NOT_FORMAL_L2_OR_L3", "actual_active_minutes": "UNKNOWN", "working_time_ceiling": None, "runtime_actions": 0, "checks": {}}
    for name, cmd in commands.items():
        before = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, timeout=180)
        (OUT / (name + ".stdout.log")).write_bytes(result.stdout)
        (OUT / (name + ".stderr.log")).write_bytes(result.stderr)
        item = {"command": cmd, "start_utc": before, "end_utc": datetime.now(timezone.utc).isoformat(), "exit_code": result.returncode}
        (OUT / (name + ".meta.json")).write_text(json.dumps(item, indent=2) + "\n", encoding="utf-8")
        summary["checks"][name] = item
        print(name + ": " + str(result.returncode))
        if result.returncode:
            print(result.stdout.decode("utf-8", errors="replace")[-3500:])
            print(result.stderr.decode("utf-8", errors="replace")[-3500:])
    summary["end_utc"] = datetime.now(timezone.utc).isoformat()
    summary["result"] = "PASS" if all(x["exit_code"] == 0 for x in summary["checks"].values()) else "FAIL"
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if summary["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()

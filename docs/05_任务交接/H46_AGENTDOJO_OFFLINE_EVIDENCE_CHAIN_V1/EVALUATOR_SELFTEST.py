"""Pre-freeze checker health only, not an Executor run or task verdict."""
import hashlib
import json
import runpy
import socket
import subprocess
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]


def freeze_baseline():
    tracked = subprocess.check_output(["git", "ls-files", "-z", "src", "tests", "scripts"], cwd=ROOT)
    files = [ROOT / name for name in tracked.decode().split("\0") if name]
    for name in ("CONTRACT.md", "VALIDATION_PLAN.yaml", "EVALUATOR_CHECK.py", "FIXTURE.json",
                 "SOURCE_LOCK.json", "EVALUATOR_PREPARE.py", "EVALUATOR_SELFTEST.py", "EXECUTOR_START.md"):
        files.append(TASK / name)
    parent = ROOT / "docs/05_任务交接/H42_AGENT_FACING_ATTACK_SEAM_MEASUREMENT_V1"
    for name in ("MEASUREMENT.py", "REPORT.md", "SOURCE_AUDIT.md", "REVIEW.md", "CONTRACT.md",
                 "VALIDATION_PLAN.yaml", "EVALUATOR_CHECK.py", "GOVERNANCE_CHECK.py", "FIXTURE.json"):
        files.append(parent / name)
    protected = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    data = {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "protected_files": protected, "boundary": "read-only product; pinned AST source slice; no model/network"}
    (TASK / "BASELINE.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("protected files:", len(protected))


def main():
    if "--freeze-baseline" in sys.argv:
        freeze_baseline()
    check = runpy.run_path(str(TASK / "EVALUATOR_CHECK.py"))
    check["baseline"]()
    namespace, methods = check["source_slice"]()
    for case in check["FIXTURE"]["cases"]:
        before = check["initial_account"](namespace)
        after = before.model_copy(deep=True)
        for action in case["actions"]:
            namespace["send_money"](after, **action)
        observed = check["score"](methods, before, after)
        assert observed == {key: case[key] for key in observed}
        print(case["id"], json.dumps(observed))
    with check["no_network"]():
        try:
            socket.create_connection(("example.invalid", 443))
        except AssertionError:
            print("network guard: PASS")
        else:
            raise AssertionError("network guard did not reject")
    sys.path.insert(0, str(ROOT / "src"))
    from agentic_payment_experiment.models import Decision
    from agentic_payment_experiment.payment_execution import execute_with_payment_binding_gate
    calls = []
    result = execute_with_payment_binding_gate(Decision.ALLOW, None, None, None, None, lambda: calls.append(1))
    assert result.decision is Decision.INDETERMINATE and "p2:binding_missing" in result.gate_reason_codes and not calls
    print("missing-evidence oracle: PASS; preflight only, no L2/L3 or task verdict")


if __name__ == "__main__":
    main()

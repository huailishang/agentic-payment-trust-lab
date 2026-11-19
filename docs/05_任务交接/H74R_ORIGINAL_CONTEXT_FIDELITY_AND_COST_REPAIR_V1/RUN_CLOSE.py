"""H74R one-shot delivery, with an inclusive future closeout boundary.

All work, including REPORT, SUBMISSION serialization, and CURRENT routing,
must finish before END. No changes to old parent accepted artifacts.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
DERIVED = P / "derived"
DERIVED.mkdir(exist_ok=True)
def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()
def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))
def put_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
def command(argv):
    return subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=60)

baseline = read(P / "BASELINE.json")
gate = read(P / "evidence" / "l2_attempt_001" / "L2-GATE.json")
if gate.get("result") != "PASS" or gate.get("checks_total") != 6 or gate.get("mandatory_failures") != 0:
    raise RuntimeError("L2 must be one successful six-check gate")
if command(["git", "rev-parse", "HEAD"]).stdout.decode("utf-8").strip() != baseline["head"]:
    raise RuntimeError("HEAD drift")
for name, expected in (("parent_ledger_sha256", "ATTEMPT_LEDGER.json"),
                       ("parent_submission_sha256", "SUBMISSION.json"),
                       ("parent_review_sha256", "REVIEW.md")):
    p = ROOT / "docs/05_任务交接/H74_DURABLE_AUTHORITY_CONTEXT_V1" / expected
    if sha(p) != baseline[name]:
        raise RuntimeError("old H74 artifact changed: " + expected)
for rel, expected in read(P / "FREEZE.json")["files"].items():
    if sha(P / rel) != expected:
        raise RuntimeError("frozen repair contract changed " + rel)
for rel, expected in baseline["protected"].items():
    if sha(ROOT / rel) != expected:
        raise RuntimeError("protected old source changed " + rel)

source_hashes = {}
diffs = []
for rel in baseline["mutable"]:
    old = P / "references" / "rejected_source" / rel
    new = ROOT / rel
    old_bytes, new_bytes = old.read_bytes(), new.read_bytes()
    source_hashes[rel] = {
        "parent_rejected_sha256": sha(old), "repair_sha256": sha(new),
        "changed": old_bytes != new_bytes,
    }
    diff = difflib.unified_diff(
        old_bytes.decode("utf-8").splitlines(keepends=True),
        new_bytes.decode("utf-8").splitlines(keepends=True),
        fromfile="H74-original/" + rel, tofile="H74R/" + rel,
    )
    diffs.extend(diff)
if any(not x["changed"] for x in source_hashes.values()):
    raise RuntimeError("expected exactly the three scoped repairs")
(DERIVED / "SOURCE_DIFF.patch").write_text("".join(diffs), encoding="utf-8")
put_json(DERIVED / "SOURCE_HASHES.json", {
    "baseline_head": baseline["head"],
    "source_files": source_hashes,
    "adapter_modified": False,
    "other_original_test_methods_modified": False,
})
diff_check = command(["git", "diff", "--check", "--", *baseline["mutable"]])
(DERIVED / "DIFF_CHECK.stdout.log").write_bytes(diff_check.stdout)
(DERIVED / "DIFF_CHECK.stderr.log").write_bytes(diff_check.stderr)
if diff_check.returncode != 0:
    raise RuntimeError("diff check failed")
status = command(["git", "status", "--short", "--untracked-files=normal"])
if status.returncode != 0:
    raise RuntimeError("git status failed")
(DERIVED / "FINAL_STATUS.txt").write_bytes(status.stdout)

ledger_path = P / "ATTEMPT_LEDGER.json"
ledger = read(ledger_path)
assert ledger["implementation_attempts"] == 1
assert ledger["l2_attempts"] == 1 and ledger["l3_attempts"] == 0
assert all(value == 0 for value in ledger["external_actions"].values())
assert len(ledger["windows"]) == 1 and ledger["windows"][0]["end_utc"] is None
begin = datetime.fromisoformat(ledger["windows"][0]["begin_utc"].replace("Z", "+00:00"))
closeout_until = datetime.now(timezone.utc) + timedelta(seconds=30)
minutes = (closeout_until - begin).total_seconds() / 60
prep = read(P / "evidence" / "preparation" / "CLOSE.json")["charged_minutes"]
parent_eval = baseline["parent_evaluator_minutes"]
if minutes > 45 or 25.0192 + minutes > 105 or parent_eval + prep + 15 > 45:
    raise RuntimeError("repair or aggregate budget exceeded")
if 25.0192 + parent_eval + prep + minutes + 15 > 150:
    raise RuntimeError("project cumulative budget exceeded")

ledger["windows"][0]["end_utc"] = closeout_until.isoformat()
put_json(ledger_path, ledger)
put_json(DERIVED / "FINAL_COST.json", {
    "schema": "h74r-cost-final/v1",
    "executor_begin_utc": begin.isoformat(),
    "executor_closeout_coverage_end_utc": closeout_until.isoformat(),
    "executor_charged_minutes": minutes,
    "parent_executor_conservative_minutes": 25.0192,
    "parent_evaluator_minutes": parent_eval,
    "repair_preparation_evaluator_minutes": prep,
    "future_evaluator_ceiling_minutes": 15,
    "cumulative_executor_conservative_minutes": 25.0192 + minutes,
    "cumulative_evaluator_reservation_minutes": parent_eval + prep + 15,
    "cumulative_total_with_full_evaluator_reservation_minutes": 25.0192 + minutes + parent_eval + prep + 15,
    "repair_executor_attempts": {"implementation":1,"l2":1,"l3":0},
    "parent_attempts_unchanged":{"implementation":1,"l2":1,"l3":1},
    "actual_active_minutes": "UNKNOWN",
    "parent_original_active_minutes":"UNKNOWN",
    "closeout_coverage_rule": "END is an explicit upper-bound timestamp; all report/submission/router writes must complete before it and execution remains in-window until boundary.",
})

current_path = ROOT / "CURRENT.md"
current = current_path.read_text(encoding="utf-8")
for old, replacement in (
    ("state: CONTRACT_FROZEN", "state: READY_FOR_REVIEW"),
    ("current_role: Executor", "current_role: Evaluator"),
    ("next_artifact_path: docs/05_任务交接/H74R_ORIGINAL_CONTEXT_FIDELITY_AND_COST_REPAIR_V1/REPORT.md",
     "next_artifact_path: docs/05_任务交接/H74R_ORIGINAL_CONTEXT_FIDELITY_AND_COST_REPAIR_V1/REVIEW.md"),
    ("execution_phase: H74R_FIDELITY_COST_REPAIR_FROZEN_NOT_EXECUTED",
     "execution_phase: H74R_EXECUTOR_L2_PASS_AWAITING_INDEPENDENT_L3"),
    ("当前修复未执行。", "修复已执行，独立HOLDOUT 10/10、原13+新3/16、历史19/9/74及正式L2 6/6通过，成本对账与提交已封存。当前待Evaluator独立L3，尚非最终PASS。"),
    ("外部全false，下一产物REPORT；", "外部全false，下一产物REVIEW；"),
):
    if current.count(old) != 1:
        raise RuntimeError("CURRENT router changed unexpectedly or ambiguous: " + old)
    current = current.replace(old, replacement)
current_path.write_text(current, encoding="utf-8")

# Validator is read-only. Its result is saved inside the charged closeout window.
validate = command([sys.executable, "-B",
    str(ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py"),
    "--repo", str(ROOT), "--current", "CURRENT.md"])
(DERIVED / "WORKFLOW_VALIDATOR.stdout.log").write_bytes(validate.stdout)
(DERIVED / "WORKFLOW_VALIDATOR.stderr.log").write_bytes(validate.stderr)
if validate.returncode != 0:
    raise RuntimeError("workflow validation failure after routing")

files = {}
for path in sorted(P.rglob("*")):
    if not path.is_file():
        continue
    rel = path.relative_to(P).as_posix()
    if rel.startswith(("references/", "runtime/")) or rel == "SUBMISSION.json":
        continue
    if rel.startswith(("evidence/", "derived/")) or rel in {
        "RUN_ENV.cmd", "RUN_CLOSE.py", "REPORT.md", "ATTEMPT_LEDGER.json",
        "COST_RECONCILIATION.json",
    }:
        files[rel] = sha(path)
submission = {
    "schema": "h74r-submission/v1",
    "task_id": P.name,
    "executor_status": "SUBMITTED_FOR_REVIEW",
    "baseline_head": baseline["head"],
    "l2_gate": {
        "path": "evidence/l2_attempt_001/L2-GATE.json",
        "sha256": sha(P/"evidence/l2_attempt_001/L2-GATE.json"),
        "result": "PASS", "checks_total":6, "attempt_count":1,
    },
    "source_files": source_hashes,
    "files": files,
    "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
    "executor_window_coverage_end_utc": closeout_until.isoformat(),
    "executor_charged_minutes": minutes,
    "old_parent_artifacts_modified": False,
    "external_actions": ledger["external_actions"],
    "l3_executed_by_executor":False,
    "independent_review":"PENDING",
    "git_commit":False, "git_push":False,
}
put_json(P / "SUBMISSION.json", submission)
if datetime.now(timezone.utc) > closeout_until:
    raise RuntimeError("submission completed after conservative closeout boundary")
remaining = (closeout_until-datetime.now(timezone.utc)).total_seconds()
if remaining > 0:
    time.sleep(remaining)
print(json.dumps({
    "status":"READY_FOR_REVIEW",
    "formal_L2":"PASS", "checks":6,
    "submitted_files":len(files),"modified_source_files":len(source_hashes),
    "charged_executor_minutes": minutes,
    "cumulative_evaluator_reservation": parent_eval + prep + 15,
    "closed_at_utc": closeout_until.isoformat(),
    "submission_sha256":sha(P/"SUBMISSION.json"),
    "external_actions":0,
}, ensure_ascii=False))

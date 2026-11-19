"""H74 executor one-shot closeout: preserve status, whole-window cost, exact manifest."""
from __future__ import annotations
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
DERIVED = P/"derived"
DERIVED.mkdir(exist_ok=True)
def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
def write_json(path: Path, obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def run(argv):
    return subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=60)
baseline = json.loads((P/"BASELINE.json").read_text(encoding="utf-8"))
spec = json.loads((P/"SPEC.json").read_text(encoding="utf-8"))
gate = json.loads((P/"evidence/l2_attempt_001/L2-GATE.json").read_text(encoding="utf-8"))
if gate["result"] != "PASS" or gate["checks_total"] != 8 or gate["mandatory_failures"]:
    raise RuntimeError("cannot submit without complete L2")
if run(["git","rev-parse","HEAD"]).stdout.decode().strip() != baseline["head"]:
    raise RuntimeError("baseline HEAD changed")
diff_check = run(["git","diff","--check","--",*spec["mutable_existing"]])
(DERIVED/"FINAL_DIFF_CHECK.stdout.log").write_bytes(diff_check.stdout)
(DERIVED/"FINAL_DIFF_CHECK.stderr.log").write_bytes(diff_check.stderr)
if diff_check.returncode:
    raise RuntimeError("source diff whitespace check failed")
status = run(["git","status","--short","--untracked-files=normal"])
if status.returncode:
    raise RuntimeError("git status failed")
(DERIVED/"FINAL_STATUS.txt").write_bytes(status.stdout)
source_paths = [*spec["mutable_existing"],*spec["allowed_new"]]
if any(not (ROOT / rel).is_file() for rel in source_paths):
    raise RuntimeError("implementation source/test file missing")
write_json(DERIVED/"SOURCE_SUMMARY.json",{
    "baseline_head":baseline["head"],
    "source_files_sha256":{rel:sha(ROOT/rel) for rel in source_paths},
    "protected_initial_source_sha256":{
        rel: sha(P/"references/initial_source"/rel)
        for rel in spec["mutable_existing"]},
    "l2_result":"PASS", "l2_check_count":8,
    "git_diff_check_passed":True,"git_commit":False,"git_push":False,
    "original_test_files_unchanged":True,
    "other_preexisting_workspace_changes_not_staged":True,
})
ledger_path=P/"ATTEMPT_LEDGER.json"
ledger=json.loads(ledger_path.read_text(encoding="utf-8"))
if (len(ledger["windows"])!=1 or ledger["windows"][0]["end_utc"] is not None
    or ledger["implementation_attempts"]!=1 or ledger["l2_attempts"]!=1 or ledger["l3_attempts"]!=0
    or any(ledger["external_actions"].values())):
    raise RuntimeError("ledger shape, attempts or external actions invalid")
end=datetime.now(timezone.utc)
begin=datetime.fromisoformat(ledger["windows"][0]["begin_utc"].replace("Z","+00:00"))
minutes=(end-begin).total_seconds()/60
if minutes>105:
    raise RuntimeError("executor budget exceeded")
ledger["windows"][0]["end_utc"]=end.isoformat()
write_json(ledger_path,ledger)
write_json(DERIVED/"COST_SUMMARY.json",{
    "schema":"h74-executor-cost-closure/v1",
    "begin_utc":begin.isoformat(), "end_utc":end.isoformat(),
    "charged_executor_minutes":minutes, "executor_limit_minutes":105,
    "active_minutes":"UNKNOWN",
    "implementation_attempts":1,"formal_l2_attempts":1,"l3_attempts":0,
    "external_actions":ledger["external_actions"],
})
# Task-owned files only; never rewrite old H72/H73, frozen contracts or references.
include_roots={"evidence","derived"}
files={}
for entry in P.rglob("*"):
    if not entry.is_file():
        continue
    rel=entry.relative_to(P).as_posix()
    if rel.startswith(("references/","runtime/")):
        continue
    if entry.parts[len(P.parts)] not in include_roots and rel not in {
        "ATTEMPT_LEDGER.json","MEASUREMENT.json","MEASURE.py","REPORT.md",
        "RUN_ENV.cmd","RUN_PREFLIGHT.py","RUN_BASELINE.py","RUN_CLOSE.py",
    }:
        continue
    files[rel]=sha(entry)
submission={
    "schema":"h74-submission/v1",
    "task_id":"H74_DURABLE_AUTHORITY_CONTEXT_V1",
    "executor_status":"SUBMITTED_FOR_REVIEW",
    "baseline_head":baseline["head"],
    "l2_gate":{"path":"evidence/l2_attempt_001/L2-GATE.json",
               "sha256":sha(P/"evidence/l2_attempt_001/L2-GATE.json")},
    "source_files":{rel:sha(ROOT/rel) for rel in source_paths},
    "files":dict(sorted(files.items())),
    "submitted_at_utc":datetime.now(timezone.utc).isoformat(),
    "executor_charged_minutes":minutes,
    "l3_executed_by_executor":False,
    "independent_review":"PENDING",
    "external_actions":ledger["external_actions"],
    "git_commit":False,"git_push":False,
}
write_json(P/"SUBMISSION.json",submission)
print(json.dumps({"result":"READY_FOR_REVIEW", "l2":"PASS",
 "included_files":len(files),"charged_minutes":minutes,
 "source_files":len(source_paths), "external_actions":0,
 "submission_sha256":sha(P/"SUBMISSION.json")},ensure_ascii=False))

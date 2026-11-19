"""Evaluator-only initial seal; not an Executor or validation entry point."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
P=Path(__file__).resolve().parent
ROOT=P.parents[2]
OLD=ROOT/"docs/05_任务交接/H72_LOCAL_CLOSEOUT_AND_STRIPE_JOURNEY_V1"
def load(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,why):
    if not ok:raise RuntimeError(why)
def seal():
    need(not (P/"BASELINE.json").exists(),"already sealed")
    old=load(OLD/"BASELINE.json")
    migration={"REMOTE_HANDOFF.md":OLD/"evidence/l3_review_20261115/REMOTE.before.md",
        "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md":ROOT/"docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261115_r120.md"}
    for rel,digest in old["protected"].items():
        source=migration.get(rel,ROOT/rel)
        need(source.is_file() and sha(source)==digest,"unapproved old drift: "+rel)
    accepted=load(OLD/"evidence/l3_review_20261115/ACCEPTED_SNAPSHOT.json")
    for rel,digest in accepted["files"].items():
        if rel=="RESOURCE_LEDGER.jsonl":continue
        need(sha(OLD/rel)==digest,"accepted task drift: "+rel)
    for rel,digest in accepted["additional_product_and_test"].items():
        need(sha(ROOT/rel)==digest,"accepted product drift: "+rel)
    current=(ROOT/"CURRENT.md").read_text(encoding="utf-8")
    need("task_id: "+P.name in current and "state: CONTRACT_FROZEN" in current,"new router not frozen")
    names=subprocess.check_output(["git","ls-files","-c","-o","--exclude-standard","-z"],cwd=ROOT).split(b"\0")
    all_names={n.decode("utf-8") for n in names if n}
    all_names.update(p.relative_to(ROOT).as_posix() for p in OLD.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    protected={}
    for rel in sorted(all_names):
        path=ROOT/rel
        if rel=="CURRENT.md" or rel.startswith(P.relative_to(ROOT).as_posix()+"/") or "__pycache__" in path.parts:continue
        if path.is_file():protected[rel]=sha(path)
    ref=P/"references"
    ref.mkdir(exist_ok=True)
    copies={"H72_CURRENT_SUBMITTED.md":OLD/"evidence/l3_review_20261115/CURRENT.before.md",
            "H72_CURRENT_TERMINAL.md":OLD/"evidence/l3_review_20261115/CURRENT.terminal.md",
            "PRIOR_MAP_r120.md":migration["docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"],
            "PRIOR_REMOTE.md":migration["REMOTE_HANDOFF.md"]}
    for name,source in copies.items():
        target=ref/name
        need(not target.exists(),"reference already exists")
        target.write_bytes(source.read_bytes())
    private=Path(load(OLD/"evidence/p1/PRIVATE_REF.json")["path"])
    private_hashes={hashlib.sha256(p.relative_to(private).as_posix().encode()).hexdigest():sha(p) for p in private.rglob("*") if p.is_file()}
    shared=ROOT.parent/"localagent-common/skills/evaluator-executor-workflow/scripts"
    value={"schema":"h72r-offline-review-repair-baseline/v1","task_id":P.name,
        "sealed_at_utc":datetime.now(timezone.utc).isoformat(),"head":old["head"],"project_map_revision":"2026-11-15-r121",
        "parent_task_id":OLD.name,"parent_verdict":"REJECTED","parent_l3_gate_sha256":sha(OLD/"evidence/l3_review_20261115/gate_001/L3-GATE.json"),
        "protected":protected,"special_nodes":old["special_nodes"],
        "historical_governance_migration":{rel:{"old_expected":old["protected"][rel],"archive":path.relative_to(ROOT).as_posix(),"new_expected":sha(ROOT/rel)} for rel,path in migration.items()},
        "references":{p.name:sha(p) for p in ref.iterdir() if p.is_file()},
        "private_existing_file_hashes_by_hashed_path":private_hashes,
        "shared_tools":{name:sha(shared/name) for name in ("run_validation.py","validate_workflow.py","capture_evidence.py")},
        "inherited_untracked":[n.decode("utf-8") for n in subprocess.check_output(["git","ls-files","--others","--exclude-standard","-z"],cwd=ROOT).split(b"\0") if n and not n.decode("utf-8").startswith(P.relative_to(ROOT).as_posix()+"/")],
        "budgets":{"active_minutes":60,"wall_hours":3,"implementation_approaches":1,"l2_attempts":2,"l3_attempts":1,"parent_cumulative_active_minutes":480,"absolute_expiry":"2026-11-16T04:08:37Z","network":0,"api":0,"services":0,"browser":0,"payments":0,"installs":0,"commits":0,"pushes":0},
        "cost_basis":{"parent_executor_active_upper_bound_minutes":102.999,"evaluator_review_started_at_utc":"2026-11-15T09:42:20Z","evaluator_elapsed_upper_bound_minutes":round((datetime.now(timezone.utc)-datetime.fromisoformat("2026-11-15T09:42:20+00:00")).total_seconds()/60,3)},
        "source_boundary":"All H72/product/test/shared files immutable; new task-local implementations only"}
    (P/"BASELINE.json").write_text(json.dumps(value,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    frozen={name:sha(P/name) for name in ("CONTRACT.md","VALIDATION_PLAN.yaml","EXECUTOR_START.md","FREEZE.py","BASELINE.json")}
    (P/"FROZEN_INPUTS.json").write_text(json.dumps({"schema":"h72r-frozen-inputs/v1","task_id":P.name,"sha256":frozen},indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"sealed":True,"protected":len(protected),"private_files":len(private_hashes),"references":len(copies),"baseline_sha256":sha(P/"BASELINE.json"),"frozen_lock_sha256":sha(P/"FROZEN_INPUTS.json")}))
if __name__=="__main__":seal()

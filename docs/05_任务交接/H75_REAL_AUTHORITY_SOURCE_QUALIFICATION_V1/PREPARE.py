import json,hashlib,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[2]
R=ROOT/"docs/05_任务交接/H74R_ORIGINAL_CONTEXT_FIDELITY_AND_COST_REPAIR_V1"
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def archive():
    dest=P/"references/before_h75"
    if dest.exists():raise RuntimeError("already captured")
    dest.mkdir(parents=True)
    for rel in ("CURRENT.md","REMOTE_HANDOFF.md","docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"):(dest/Path(rel).name).write_bytes((ROOT/rel).read_bytes())
    target=ROOT/"docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261116_r126.md"
    if target.exists():raise RuntimeError("r126 archive exists")
    target.write_bytes((ROOT/"docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md").read_bytes())
    write(P/"evidence/preparation/START.json",{"begin_utc":read(R/"evidence/l3_review/COST.json")["windows"][0]["end_utc"],"source":"H74R review end, conservative new-phase envelope","actual_active_minutes":"UNKNOWN","ceiling_minutes":25,"web_tool_call_ceiling":6,"new_scope":"Human continue: source qualification design; old H74 lineage not reset"})
    print(json.dumps({"archived_governance":3,"new_phase":"evaluator qualification design"}))
def close():
    start=read(P/"evidence/preparation/START.json");now=datetime.now(timezone.utc)
    minutes=(now-datetime.fromisoformat(start["begin_utc"])).total_seconds()/60
    exceeded=minutes>25
    write(P/"evidence/preparation/CLOSE.json",{"begin_utc":start["begin_utc"],"end_utc":now.isoformat(),"charged_minutes_upper_bound":round(minutes+.000001,6),"ceiling_minutes":25,"budget_status":"BUDGET_EXCEEDED_NOT_ACCEPTED" if exceeded else "WITHIN_CAP","overrun_minutes_upper_bound":round(max(0,minutes-25)+.000001,6),"actual_active_minutes":"UNKNOWN","formal_l2":0,"formal_l3":0,"product_execution":0,"runtime_external_actions":0,"scope":"new H75 source qualification design, separate from completed H74/H74R ledger","disposition":"stop new qualification; retain DRAFT; no retroactive budget extension"})
    print(json.dumps({"design_minutes":round(minutes+.000001,6),"budget_status":"BUDGET_EXCEEDED_NOT_ACCEPTED" if exceeded else "WITHIN_CAP","runtime_actions":0,"formal_gates":0}))
    if exceeded:sys.exit(1)
if __name__=="__main__":{"archive":archive,"close":close}[sys.argv[1]]()

"""Evaluator-only repair handoff preparation, no product changes or gates."""
import ast
import hashlib
import json
import os
import runpy
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[2]
H=ROOT/"docs/05_任务交接/H74_DURABLE_AUTHORITY_CONTEXT_V1"
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def setup():
    t=P/"references/before_repair"
    if t.exists():raise ValueError("already captured")
    t.mkdir(parents=True)
    for rel in ("CURRENT.md","REMOTE_HANDOFF.md","docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"):(t/Path(rel).name).write_bytes((ROOT/rel).read_bytes())
    archive=ROOT/"docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261116_r125.md"
    if archive.exists():raise ValueError("map archive exists")
    archive.write_bytes((ROOT/"docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md").read_bytes())
    for rel,expected in read(H/"SUBMISSION.json")["source_files"].items():
        if sha(ROOT/rel)!=expected:raise ValueError("accepted source drift")
        dest=P/"references/rejected_source"/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/rel).read_bytes())
    original=(H/"evidence/l3_review/INDEPENDENT_PROBES.py").read_text(encoding="utf-8")
    old='OUT = Path(__file__).resolve().parent\nP = OUT.parents[1]\nROOT = P.parents[2]'
    new='P = Path(__file__).resolve().parent\nROOT = P.parents[2]\nOUT = P / ("evidence/l3_review/holdout" if "current_role: Evaluator" in (ROOT/"CURRENT.md").read_text(encoding="utf-8") else "evidence/holdout")\nOUT.mkdir(parents=True,exist_ok=True)'
    if original.count(old)!=1:raise ValueError("holdout header")
    text=original.replace(old,new)
    extra='''def foreign_codec(f):
    from agentic_payment_experiment.stripe_authority_context import serialize_authority
    status=Enum("PaymentStatus",{"PENDING":PaymentStatus.PENDING.value})
    decision=Enum("Decision",{"ALLOW":"ALLOW"})
    for ctx in (replace(f.ctx,execution=replace(f.ctx.execution,status=status.PENDING)),replace(f.ctx,prepayment_decision=decision.ALLOW)):
        try:serialize_authority("op-l3",ctx,resource_sha256=f.resource_sha,recorded_at=f.now,run_id="run-l3")
        except StripeCheckoutError:pass
        else:raise AssertionError("unregistered same-name enum accepted by closed codec")
    return {"unregistered_enum_codec_variants_rejected":2}

'''
    text=text.replace('def main():',extra+'def main():').replace('("closed_enum_type_identity",foreign_enum)):', '("closed_enum_type_identity",foreign_enum),("closed_enum_codec_variants",foreign_codec)):')
    (P/"HOLDOUT.py").write_text(text,encoding="utf-8")
    shim=P/"runtime/userbase/Python312/site-packages/tests/__init__.py";shim.parent.mkdir(parents=True,exist_ok=True)
    shim.write_text('from pathlib import Path\n__path__=[str(Path(__file__).resolve().parents[8]/"tests")]\n',encoding="utf-8")
    print(json.dumps({"archived_governance":3,"rejected_sources_preserved":4,"holdout_prepared_not_executed":True}))
def seal():
    if (P/"FREEZE.json").exists():raise ValueError("already frozen")
    mutable=["src/agentic_payment_experiment/stripe_checkout_lab.py","src/agentic_payment_experiment/stripe_authority_context.py","tests/test_stripe_authority_context.py"]
    paths=set(filter(None,subprocess.check_output(["git","ls-files","-co","--exclude-standard","-z"],cwd=ROOT).decode().split("\0")))|set(read(H/"BASELINE.json")["protected"])
    paths.update(p.relative_to(ROOT).as_posix() for p in H.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    paths.add("src/agentic_payment_experiment/adapters/stripe_checkout.py")
    prefix=P.relative_to(ROOT).as_posix()+"/"
    protected={r:sha(ROOT/r) for r in sorted(paths) if r!="CURRENT.md" and r not in mutable and not r.startswith(prefix) and (ROOT/r).is_file()}
    tree=ast.parse((ROOT/mutable[2]).read_text(encoding="utf-8"))
    methods={c.name+"."+f.name:hashlib.sha256(ast.dump(f,include_attributes=False).encode()).hexdigest() for c in tree.body if isinstance(c,ast.ClassDef) for f in c.body if isinstance(f,ast.FunctionDef)}
    bases={c.name:[ast.dump(x,include_attributes=False) for x in c.bases] for c in tree.body if isinstance(c,ast.ClassDef)}
    parent=read(H/"evidence/l3_review/FINAL_RECEIPT.json")
    data={"task_id":P.name,"head":"61414d05521f7c9fe15cf0299b48b25916f5fa0e","mutable":mutable,"protected":protected,"original_test_methods":methods,"original_test_bases":bases,"parent_evaluator_minutes":parent["evaluator_charged_minutes"],"parent_ledger_sha256":sha(H/"ATTEMPT_LEDGER.json"),"parent_submission_sha256":sha(H/"SUBMISSION.json"),"parent_review_sha256":sha(H/"REVIEW.md")}
    if subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT).decode().strip()!=data["head"]:raise ValueError("HEAD changed")
    write(P/"BASELINE.json",data)
    for file in P.rglob("*.py"):ast.parse(file.read_text(encoding="utf-8"))
    helper=ROOT.parent/"localagent-common/skills/evaluator-executor-workflow/scripts"
    loader=runpy.run_path(str(helper/"run_validation.py"),run_name="repair_plan_readiness")
    for mode in ("executor","evaluator"):
        task,plan=loader["load_plan"](ROOT,P/"VALIDATION_PLAN.yaml",mode=mode)
        if task!=P.name or len(plan)!=6:raise ValueError("plan coverage")
    out=P/"evidence/preparation";out.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1",PYTHONIOENCODING="utf-8")
    commands={"DOCUMENT_VALIDATOR":[sys.executable,"-B",str(helper/"validate_workflow.py"),"--repo",str(ROOT),"--current",str(ROOT/"CURRENT.md")],"DIFF_CHECK":["git","diff","--check","--","CURRENT.md","REMOTE_HANDOFF.md","docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"]}
    codes={}
    for name,argv in commands.items():
        result=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True);codes[name]=result.returncode
        (out/(name+".stdout.log")).write_bytes(result.stdout);(out/(name+".stderr.log")).write_bytes(result.stderr)
    if any(codes.values()):raise ValueError("document readiness failed")
    begin=read(H/"evidence/l3_review/COST.json")["windows"][0]["end_utc"]
    now=datetime.now(timezone.utc);minutes=(now-datetime.fromisoformat(begin)).total_seconds()/60
    if data["parent_evaluator_minutes"]+minutes+15>45:raise ValueError("insufficient lineage evaluator reserve")
    write(out/"READINESS.json",{"prepared_at_utc":now.isoformat(),"preparation_begin_utc":begin,"preparation_minutes_through_freeze":round(minutes+.000001,6),"parent_evaluator_minutes":data["parent_evaluator_minutes"],"future_evaluator_reserved_minutes":15,"cumulative_evaluator_projected_minutes":data["parent_evaluator_minutes"]+minutes+15,"protected_files":len(protected),"packet_checks":codes,"formal_l2":0,"formal_l3":0,"product_execution":0,"external_actions":0})
    files=[p for p in P.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name!="FREEZE.json"]
    write(P/"FREEZE.json",{"task_id":P.name,"at_utc":now.isoformat(),"files":{p.relative_to(P).as_posix():sha(p) for p in sorted(files)}})
    print(json.dumps({"frozen_files":len(files),"protected_files":len(protected),"checks":codes,"preparation_minutes":round(minutes+.000001,6),"future_evaluator_reserved":15,"formal_gates":0}))
def close():
    begin=read(H/"evidence/l3_review/COST.json")["windows"][0]["end_utc"]
    now=datetime.now(timezone.utc);minutes=(now-datetime.fromisoformat(begin)).total_seconds()/60
    need_total=read(P/"BASELINE.json")["parent_evaluator_minutes"]+minutes+15
    if need_total>45:raise ValueError("lineage evaluator reserve exhausted")
    write(P/"evidence/preparation/CLOSE.json",{"begin_utc":begin,"end_utc":now.isoformat(),"charged_minutes":round(minutes+.000001,6),"actual_active_minutes":"UNKNOWN","future_evaluator_reserved_minutes":15,"lineage_evaluator_projected_minutes":need_total,"formal_gates":0,"external_actions":0})
    print(json.dumps({"preparation_closed":True,"minutes":round(minutes+.000001,6),"lineage_evaluator_projected_minutes":need_total}))
if __name__=="__main__":
    try:{"setup":setup,"seal":seal,"close":close}[sys.argv[1]]()
    except Exception as exc:print(json.dumps({"preparation":"FAIL","error_type":type(exc).__name__,"reason":str(exc) if isinstance(exc,ValueError) else "source unavailable"}));sys.exit(1)

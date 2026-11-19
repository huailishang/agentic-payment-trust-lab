"""Frozen wrapper around inherited protection/budget checks and canonical submission validation."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys

PACK=Path(__file__).resolve().parent
ROOT=PACK.parents[2]
item=importlib.util.spec_from_file_location("h71r2_base_check",PACK/"BASE_CHECK.py")
base=importlib.util.module_from_spec(item); item.loader.exec_module(base)

def artifacts():
    seal=base.load(PACK/"INPUT_SEAL.json")
    for rel,digest in seal["passed_projection_files"].items(): base.need(base.sha((ROOT/rel).read_bytes())==digest,"passed_projection_changed")
    result=base.load(PACK/"RESULT.json")
    base.need(result["task_id"]==PACK.name and result["decision"]=="REPAIR_COMPLETE" and result["previous_h71r_verdict"]=="REJECTED","result_identity")
    base.need(result["implementation_sha256"]==base.sha((PACK/"RUN.py").read_bytes()),"implementation_binding")
    base.need(result["input_correction_sha256"]==seal["correction_sha256"] and result["input_matrix_sha256"]==seal["matrix_sha256"],"passed_inputs_binding")
    keys={"network_requests","downloads","runtime_api","browser_actions","local_services","installs","environments","checkout_sessions","payments","commits","pushes"}
    base.need(set(result["side_effects"])==keys and all(type(v) is int and v==0 for v in result["side_effects"].values()),"external_side_effects")
    print("H71R2 candidate implementation and preserved projections bound; no external qualification claimed")

def submission():
    base.integrity(); artifacts(); base.budget(closed=True)
    report=(PACK/"REPORT.md").read_text(encoding="utf-8")
    base.need("Executor status: SUBMITTED_FOR_REVIEW" in report,"submission_status")
    validator=ROOT.parent/"localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py"
    completed=subprocess.run([sys.executable,str(validator),"--repo",str(ROOT),"--current","CURRENT.md"],cwd=ROOT,capture_output=True,text=True)
    base.need(completed.returncode==0,"public_workflow_validator_rejected_submission")
    print("Canonical public workflow validator accepted the complete L2 handoff; Evaluator acceptance still required")

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("command",choices=("integrity","artifacts","budget","submission")); parser.add_argument("--closed",action="store_true"); args=parser.parse_args()
    try:
        if args.command=="integrity": base.integrity()
        elif args.command=="artifacts": artifacts()
        elif args.command=="budget": base.budget(args.closed)
        else: submission()
    except (OSError,ValueError,TypeError,KeyError,AttributeError,AssertionError,subprocess.SubprocessError):
        print("H71R2 CHECK FAILED; inspect local evidence",file=sys.stderr); raise SystemExit(1)

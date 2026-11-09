"""Evaluator copies the unaccepted H57 candidate and freezes a bounded repair."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime,timezone

TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
PARENT=TASK.parent/'H57_DEFAULT_FACTORY_MERCHANT_E2E_V1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):
    p=TASK/name
    assert not p.exists(),str(p)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def copy():
    pairs=[(p,p.relative_to(PARENT).as_posix()) for folder in ('merchant','references')
        for p in (PARENT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    pairs += [(PARENT/n,n) for n in ('HTTP_RUNTIME.py','RUN_JOURNEY.py','RUNTIME.py','CASE_SPEC.json','UPSTREAM_LICENSE')]
    pairs += [(PARENT/'CHECK.py','references/H57_CHECK.py'),
        (PARENT/'evidence/executor/HTTP_ATTEMPTS.jsonl','references/LEGACY_HTTP_ATTEMPTS.raw'),
        (PARENT/'evidence/executor/HTTP_ATTEMPTS_AFTER_L1.jsonl','references/H57_LATER_HTTP_ATTEMPTS.jsonl'),
        (PARENT/'evidence/preacceptance/AUDIT.json','references/H57_PREACCEPTANCE_AUDIT.json')]
    rows={}
    for source,name in pairs:
        dest=TASK/name;assert not dest.exists(),name
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
        rows[name]={'source':source.relative_to(ROOT).as_posix(),'sha256':sha(source)}
    save('SOURCE_COPY.json',{'files':rows,'candidate_accepted':False,'merchant_files':38})
    print(json.dumps({'copied_files':len(rows),'merchant_files':38,'repair_implemented':False,'http_requests':0}))
def freeze():
    timing=json.loads((TASK/'EXECUTION_WINDOW.json').read_text(encoding='utf-8'))
    start=datetime.fromisoformat(timing['first_executor_turn_utc'])
    end=datetime.fromisoformat(timing['last_executor_turn_completed_utc'])
    assert 0<=(end-start).total_seconds()<=120*60
    assert timing['inherited_time_charge_minutes']==120
    for p in TASK.rglob('*.py'): ast.parse(p.read_text(encoding='utf-8'))
    files={n.decode('utf-8') for n in subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).split(b'\0') if n}
    prefix=TASK.relative_to(ROOT).as_posix()+'/'
    names={n for n in files if n!='CURRENT.md' and not n.startswith(prefix)}
    old=json.loads((PARENT/'BASELINE.json').read_text(encoding='utf-8'))
    names.update(old['protected_files'])
    # Include ignored H57 evidence that the old task-level baseline did not enumerate.
    names.update(p.relative_to(ROOT).as_posix() for p in PARENT.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    mutable={'HTTP_RUNTIME.py','RUN_JOURNEY.py','REPORT.md','RESULT.json','ATTEMPT_LEDGER.json'}
    frozen={p.relative_to(TASK).as_posix():sha(p) for p in TASK.rglob('*') if p.is_file()
        and '__pycache__' not in p.parts and p.relative_to(TASK).as_posix() not in mutable
        and p.name!='BASELINE.json' and not p.relative_to(TASK).as_posix().startswith('evidence/')}
    history=(ROOT/'CURRENT.md').read_text(encoding='utf-8').split('## Global position',1)[1]
    save('BASELINE.json',{'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'protected_files':{n:sha(ROOT/n) for n in sorted(names)},'frozen_files':frozen,
        'workspace_files':sorted(files),'current_history_sha256':hashlib.sha256(history.encode()).hexdigest()})
    print(json.dumps({'protected':len(names),'frozen':len(frozen),'new_http_requests':0}))
def plan():
    value=json.loads((PARENT/'VALIDATION_PLAN.yaml').read_text(encoding='utf-8'))
    value['task_id']=TASK.name
    for row in value['checks']:
        for key in ('command','evaluator_command'):
            if key in row:row[key]=[v.replace(PARENT.name,TASK.name) for v in row[key]]
    save('VALIDATION_PLAN.yaml',value)
    print(json.dumps({'frozen_plan_checks':len(value['checks']),'inherited_business_cases':6}))
if __name__=='__main__':{'copy':copy,'freeze':freeze,'plan':plan}[sys.argv[1]]()

"""Evaluator only: emit executable plan and immutable workspace/source lock."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from RUNTIME import ROOT,TASK,NODE
def save(name,obj):
    path=TASK/name; assert not path.exists(),name
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def plan():
    prefix=TASK.relative_to(ROOT).as_posix()
    def cmd(script,*args): return ['.task_envs/H47/.venv/Scripts/python.exe','-B',prefix+'/'+script,*args]
    checks=[]
    def add(acs,command,evaluator=None):
        row={'id':f'VP-{len(checks)+1:02d}','ac':acs,'cwd':'.','command':command,'expected_exit_code':0,'mandatory':True}
        if evaluator: row['evaluator_command']=evaluator
        checks.append(row)
    add(['AC-01'],cmd('CHECK.py','baseline'))
    add(['AC-01'],cmd('CHECK.py','scope'))
    add(['AC-02'],cmd('JCS_CHECK.py'))
    add(['AC-03','AC-04'],cmd('FROZEN_TESTS.py','--role','executor'),cmd('FROZEN_TESTS.py','--role','evaluator'))
    add(['AC-03','AC-04','AC-05'],cmd('CHECK.py','materials','--role','executor'),cmd('CHECK.py','materials','--role','evaluator'))
    add(['AC-05'],cmd('RUNTIME.py','regression'))
    add(['AC-05'],cmd('CHECK.py','selftest'))
    add(['AC-01','AC-05'],cmd('CHECK.py','baseline'))
    save('VALIDATION_PLAN.yaml',{'schema':'evaluator-executor-validation-plan/v1','task_id':TASK.name,'checks':checks})
    print(json.dumps({'checks':len(checks),'candidate_cases_per_full_run':36}))
def freeze():
    from CHECK import workspace,sha,MUTABLE
    for path in TASK.rglob('*.py'): ast.parse(path.read_text(encoding='utf-8'))
    files=workspace(); prefix=TASK.relative_to(ROOT).as_posix()+'/'
    names={n for n in files if n!='CURRENT.md' and not n.startswith(prefix)}
    parent=TASK.parent/'H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/BASELINE.json'
    names.update(json.loads(parent.read_text(encoding='utf-8'))['protected_files'])
    frozen={p.relative_to(TASK).as_posix():sha(p) for p in TASK.rglob('*') if p.is_file()
        and '__pycache__' not in p.parts and p.relative_to(TASK).as_posix() not in MUTABLE
        and not p.relative_to(TASK).as_posix().startswith('evidence/') and p.name!='BASELINE.json'}
    current=(ROOT/'CURRENT.md').read_text(encoding='utf-8')
    save('BASELINE.json',{'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'protected_files':{n:sha(ROOT/n) for n in sorted(names)},'frozen_files':frozen,
        'workspace_files':sorted(files),'node_sha256':sha(NODE),
        'current_history_sha256':hashlib.sha256(current.split('## Global position',1)[1].encode()).hexdigest()})
    print(json.dumps({'protected_files':len(names),'frozen_files':len(frozen),'candidate_implemented':False}))
if __name__=='__main__': {'plan':plan,'freeze':freeze}[sys.argv[1]]()

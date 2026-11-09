"""Evaluator only: bounded measurement plan and freeze."""
import ast
import hashlib
import json
import subprocess
import sys
from RUNTIME import TASK,ROOT
def save(name,obj):
    p=TASK/name; assert not p.exists(); p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def plan():
    prefix=TASK.relative_to(ROOT).as_posix()
    def cmd(name,*args): return ['.task_envs/H47/.venv/Scripts/python.exe','-B',prefix+'/'+name,*args]
    rows=[]
    def add(acs,command,evaluator=None):
        r={'id':f'VP-{len(rows)+1:02d}','ac':acs,'cwd':'.','command':command,'expected_exit_code':0,'mandatory':True}
        if evaluator: r['evaluator_command']=evaluator
        rows.append(r)
    add(['AC-01'],cmd('CHECK.py','baseline'))
    add(['AC-01','AC-02'],cmd('CHECK.py','sources'))
    add(['AC-02'],cmd('PROBES.py','--role','executor'),cmd('PROBES.py','--role','evaluator'))
    add(['AC-02','AC-04'],cmd('CHECK.py','observations','executor'),cmd('CHECK.py','observations','evaluator'))
    add(['AC-03','AC-04'],cmd('CHECK.py','materials'))
    add(['AC-01','AC-04'],cmd('CHECK.py','baseline'))
    save('VALIDATION_PLAN.yaml',{'schema':'evaluator-executor-validation-plan/v1','task_id':TASK.name,'checks':rows})
    print(json.dumps({'checks':6,'presentations':6,'observations_per_full_run':12}))
def freeze():
    from CHECK import workspace,sha,MUTABLE
    for p in TASK.rglob('*.py'): ast.parse(p.read_text(encoding='utf-8'))
    files=workspace(); prefix=TASK.relative_to(ROOT).as_posix()+'/'
    names={n for n in files if n!='CURRENT.md' and not n.startswith(prefix)}
    parent=TASK.parent/'H54R_NONDELEGATING_CHECKOUT_ROOT_REPAIR_V1/BASELINE.json'
    names.update(json.loads(parent.read_text(encoding='utf-8'))['protected_files'])
    frozen={p.relative_to(TASK).as_posix():sha(p) for p in TASK.rglob('*') if p.is_file()
        and '__pycache__' not in p.parts and p.relative_to(TASK).as_posix() not in MUTABLE
        and not p.relative_to(TASK).as_posix().startswith('evidence/') and p.name!='BASELINE.json'}
    text=(ROOT/'CURRENT.md').read_text(encoding='utf-8')
    save('BASELINE.json',{'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'protected_files':{n:sha(ROOT/n) for n in sorted(names)},'frozen_files':frozen,'workspace_files':sorted(files),
        'current_history_sha256':hashlib.sha256(text.split('## Global position',1)[1].encode()).hexdigest()})
    print(json.dumps({'protected_files':len(names),'frozen_files':len(frozen),'measurement_calls':0,'new_policy_implemented':False}))
if __name__=='__main__': {'plan':plan,'freeze':freeze}[sys.argv[1]]()

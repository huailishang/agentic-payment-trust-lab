"""Frozen profile scope/material gates. Does not implement the candidate policy."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import yaml
from RUNTIME import TASK,ROOT,NODE,preflight
MUTABLE={'consumer.py','REPORT.md','RESULT.json','ATTEMPT_LEDGER.json'}
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def workspace(): return {n.decode() for n in subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).split(b'\0') if n}
def baseline():
    lock=read(TASK/'BASELINE.json')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==lock['head']
    text=(ROOT/'CURRENT.md').read_text(encoding='utf-8'); r=yaml.safe_load(text.split('```yaml',1)[1].split('```',1)[0])
    assert r['task_id']==TASK.name and r['task_kind']=='capability_experiment' and r['project_map_revision']=='2026-10-31-r92'
    assert r['hypothesis_id']=='H-56' and r['active_bottleneck_id']=='B-17'
    assert (r['state'],r['current_role']) in {('CONTRACT_FROZEN','Executor'),('EXECUTING','Executor'),('READY_FOR_REVIEW','Evaluator')}
    assert all(r['authorization_'+s] is False for s in ('commit','push','history_rewrite','api_call'))
    assert hashlib.sha256(text.split('## Global position',1)[1].encode()).hexdigest()==lock['current_history_sha256']
    for n,wanted in lock['protected_files'].items(): assert sha(ROOT/n)==wanted,n
    for n,wanted in lock['frozen_files'].items(): assert sha(TASK/n)==wanted,n
    assert sha(NODE)==lock['node_sha256']
    prefix=TASK.relative_to(ROOT).as_posix()+'/'
    assert all(n.startswith(prefix) for n in workspace()-set(lock['workspace_files']))
    for p in TASK.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            n=p.relative_to(TASK).as_posix()
            assert n in lock['frozen_files'] or n in MUTABLE or n=='BASELINE.json' or n.startswith('evidence/'),n
    preflight(); print(json.dumps({'protected':len(lock['protected_files']),'frozen':len(lock['frozen_files'])}))
def scope():
    allowed={'json','hashlib','base64','binascii','re','typing','copy','rfc8785','jwcrypto','ap2','pydantic'}
    tree=ast.parse((TASK/'consumer.py').read_text(encoding='utf-8'))
    for n in ast.walk(tree):
        if isinstance(n,ast.Import): assert all(a.name.split('.')[0] in allowed for a in n.names)
        if isinstance(n,ast.ImportFrom): assert n.level==0 and n.module.split('.')[0] in allowed
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name): assert n.func.id not in {'eval','exec','compile','open','__import__','input'}
    print(json.dumps({'mutable_implementation_files':1,'old_merchant_sdk_product':'READ_ONLY'}))
def log(role,name):
    p=TASK/'evidence'/role/name
    return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []
def materials(role):
    from FROZEN_TESTS import CASE_IDS,assert_result
    from ROOT_CASES import CASES as ROOTS,inspect
    from PROFILE_CASES import CASES as PROFILES,assert_row,sdk,decode
    base=TASK/'evidence'/role
    originals=read(base/read(base/'LATEST.json')['run']/'observations.json')['rows']
    roots=read(base/read(base/'ROOT_LATEST.json')['run']/'observations.json')['rows']
    profiles=read(base/read(base/'PROFILE_LATEST.json')['run']/'observations.json')['rows']
    assert [r['case'] for r in originals]==CASE_IDS and [r['case'] for r in roots]==ROOTS and [r['case'] for r in profiles]==PROFILES
    for group,pointer in ((originals,'LATEST.json'),(roots,'ROOT_LATEST.json'),(profiles,'PROFILE_LATEST.json')):
        folder=base/read(base/pointer)['run']
        for r in group:
            assert r['check']=='PASS'
            assert read(folder/(r['case']+'.output.json'))==r
            assert all(r[k]==v for k,v in read(folder/(r['case']+'.input.json')).items())
    for r in originals:
        m=dict(r); m['request_raw']=decode(r['request_b64']); m['session_raw']=decode(r['session_b64'])
        assert_result(m,r['result'])
    for r in roots: inspect(r)
    for r in profiles:
        m=dict(r); current=sdk(m); assert current==r['sdk']; assert_row(r)
    counts=[]
    for name,expected,limit in [('ATTEMPTS.jsonl',set(CASE_IDS),288 if role=='executor' else 108),
        ('ROOT_ATTEMPTS.jsonl',set(ROOTS),24 if role=='executor' else 9),
        ('PROFILE_ATTEMPTS.jsonl',set(PROFILES),112 if role=='executor' else 42)]:
        rows=log(role,name); assert rows
        assert all(row['charged']==len(row['cases']) and set(row['cases'])<=expected for row in rows)
        count=sum(row['charged'] for row in rows); assert count<=limit; counts.append(count)
    assert sum(counts)<=(424 if role=='executor' else 159)
    ledger=read(TASK/'ATTEMPT_LEDGER.json')
    assert ledger['formal_l2_attempts']==len(list((TASK/'evidence').glob('l2_executor_*')))<=2
    assert 0<=ledger['active_work_minutes']<=240
    executor_count=sum(row['charged'] for name in ('ATTEMPTS.jsonl','ROOT_ATTEMPTS.jsonl','PROFILE_ATTEMPTS.jsonl') for row in log('executor',name))
    assert ledger['artifact_cases_reserved']==executor_count<=424
    for name in ('network_calls','asgi_requests','model_calls','provider_calls','real_payment_calls','packages_installed','git_write_operations','payment_calls','orders_created'): assert ledger[name]==0
    result=read(TASK/'RESULT.json')
    assert result['schema']=='h56-result/v1' and result['task_id']==TASK.name
    assert result['classification']=='LOCAL_TRUSTED_DISCLOSURE_PROFILE_OBSERVED'
    assert result['profile_scope']=='TASK_LOCAL_NON_STANDARD_POLICY'
    assert result['customer_demand']=='UNKNOWN' and result['remaining_gaps']
    for name in ('production_ready','full_ucp_conformance','real_actor_authentication','psp_verified','payment_execution_integrated','http_integrated','cross_system_revocation','customer_value_proven'): assert result[name] is False
    print(json.dumps({'role':role,'original':36,'root':3,'profile':14,'complete':53,'reserved':sum(counts)}))
def selftest():
    from FROZEN_TESTS import selftest as original
    from ROOT_CASES import selftest as roots
    from PROFILE_CASES import assert_row
    original(); roots()
    rows=read(TASK/'sources/BASELINE_OBSERVATIONS.json')['rows']; bad=[]
    for r in rows:
        try: assert_row(r)
        except AssertionError: bad.append(r['case'])
    assert bad==['P02_ROOT_CNF_HIDDEN','P04_EFFECTIVE_CNF_HIDDEN','P06_UNKNOWN_ROOT_HIDDEN','P09_NO_TRUSTED_PROFILE',
        'P10_REQUEST_PROFILE_ONLY','P11_PROFILE_KEY_MISMATCH','P12_UNKNOWN_NESTED_CONDITION','P13_OPTIONAL_AREA_ITSELF_HIDDEN','P14_SECURITY_DECOY']
    print(json.dumps({'old_comparator_fails_target':bad,'candidate_called':False}))
if __name__=='__main__':
    if sys.argv[1]=='materials': materials(sys.argv[2])
    else: {'baseline':baseline,'scope':scope,'selftest':selftest}[sys.argv[1]]()

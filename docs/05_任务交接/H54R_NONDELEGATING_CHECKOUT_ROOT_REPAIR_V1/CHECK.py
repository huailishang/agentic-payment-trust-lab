"""Frozen scope, source, evidence and budget checks. No candidate implementation."""
import argparse
import ast
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import yaml
from RUNTIME import ROOT,TASK,NODE,preflight

MUTABLE={'consumer.py','REPORT.md','RESULT.json','ATTEMPT_LEDGER.json'}
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def workspace():
    return {n.decode() for n in subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).split(b'\0') if n}
def baseline():
    lock=read(TASK/'BASELINE.json')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==lock['head']
    text=(ROOT/'CURRENT.md').read_text(encoding='utf-8')
    route=yaml.safe_load(text.split('```yaml',1)[1].split('```',1)[0])
    assert route['task_id']==TASK.name and route['task_kind']=='repair'
    assert route['project_map_revision']=='2026-10-31-r90' and route['active_bottleneck_id']=='B-17' and route['hypothesis_id']=='H-54R'
    assert (route['state'],route['current_role']) in {('CONTRACT_FROZEN','Executor'),('EXECUTING','Executor'),('READY_FOR_REVIEW','Evaluator')}
    assert all(route['authorization_'+k] is False for k in ('commit','push','history_rewrite','api_call'))
    assert hashlib.sha256(text.split('## Global position',1)[1].encode()).hexdigest()==lock['current_history_sha256']
    for name,expected in lock['protected_files'].items(): assert sha(ROOT/name)==expected,name
    for name,expected in lock['frozen_files'].items(): assert sha(TASK/name)==expected,name
    assert sha(NODE)==lock['node_sha256']
    prefix=TASK.relative_to(ROOT).as_posix()+'/'
    assert all(n.startswith(prefix) for n in workspace()-set(lock['workspace_files'])), 'out-of-task file added'
    for p in TASK.rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts: continue
        name=p.relative_to(TASK).as_posix()
        assert name in lock['frozen_files'] or name in MUTABLE or name=='BASELINE.json' or name.startswith('evidence/'),name
    preflight()
    print(json.dumps({'protected_files':len(lock['protected_files']),'frozen_files':len(lock['frozen_files'])}))
def scope():
    p=TASK/'consumer.py'; assert p.is_file()
    tree=ast.parse(p.read_text(encoding='utf-8'))
    allowed={'json','hashlib','base64','binascii','re','typing','copy','rfc8785','jwcrypto','ap2','pydantic'}
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            assert all(a.name.split('.')[0] in allowed for a in node.names),ast.dump(node)
        if isinstance(node,ast.ImportFrom):
            assert node.level==0 and node.module.split('.')[0] in allowed,ast.dump(node)
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
            assert node.func.id not in {'eval','exec','compile','open','__import__','input'},node.func.id
    assert any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='consume' for n in tree.body)
    print(json.dumps({'candidate_files':1,'io_imports':'DISALLOWED','old_merchant_sdk_product':'READ_ONLY'}))
def sources():
    rows=read(TASK/'SOURCE_MANIFEST.json')['files']; assert len(rows)==19
    for row in rows:
        raw=(TASK/'sources'/row['dest']).read_bytes()
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['blob_sha']
    print(json.dumps({'source_sha256_and_git_blobs':len(rows),'license':'Apache-2.0'}))
def materials(role):
    from FROZEN_TESTS import CASE_IDS,assert_result
    base=TASK/'evidence'/role; latest=read(base/'LATEST.json')['run']
    folder=base/latest
    rows=read(folder/'observations.json')['rows']
    assert [r['case'] for r in rows]==CASE_IDS
    for row in rows:
        assert row['check']=='PASS'
        inp=read(folder/(row['case']+'.input.json')); out=read(folder/(row['case']+'.output.json'))
        assert out==row and all(row[k]==v for k,v in inp.items())
        m=dict(row)
        for key in ('request','session'):
            m[key+'_raw']=base64.urlsafe_b64decode(row[key+'_b64']+'='*(-len(row[key+'_b64'])%4))
            assert hashlib.sha256(m[key+'_raw']).hexdigest()==row[key+'_sha256']
        assert_result(m,row['result'])
    reservations=[json.loads(l) for l in (base/'ATTEMPTS.jsonl').read_text(encoding='utf-8').splitlines()]
    assert all(r['charged']==len(r['cases']) and set(r['cases'])<=set(CASE_IDS) for r in reservations)
    assert sum(r['charged'] for r in reservations)<= (288 if role=='executor' else 108)
    formal_count=len(list((TASK/'evidence').glob('l2_executor_*')))
    ledger=read(TASK/'ATTEMPT_LEDGER.json')
    assert ledger['formal_l2_attempts']==formal_count<=2
    assert 0<=ledger['active_work_minutes']<=120
    executor_log=TASK/'evidence/executor/ATTEMPTS.jsonl'
    executor_cases=sum(json.loads(l)['charged'] for l in executor_log.read_text(encoding='utf-8').splitlines())
    root_log=TASK/'evidence/executor/ROOT_ATTEMPTS.jsonl'
    root_cases=sum(json.loads(l)['charged'] for l in root_log.read_text(encoding='utf-8').splitlines())
    assert ledger['artifact_cases_reserved']==executor_cases+root_cases<=312
    for field in ('network_calls','asgi_requests','model_calls','provider_calls','real_payment_calls',
                  'packages_installed','git_write_operations','payment_calls','orders_created'):
        assert ledger[field]==0,field
    result=read(TASK/'RESULT.json')
    assert result['schema']=='h54r-result/v1' and result['task_id']==TASK.name
    assert result['classification']=='LOCAL_NONDELEGATING_CHECKOUT_REPAIR_OBSERVED'
    assert result['before']=='PARENT_REJECTED_OUTER_CNF_ACCEPTED' and result['after']=='BOUNDED_NONDELEGATING_CONSUMER'
    assert result['customer_demand']=='UNKNOWN' and isinstance(result['remaining_gaps'],list) and result['remaining_gaps']
    for field in ('production_ready','full_ucp_conformance','real_actor_authentication','psp_verified',
                  'payment_execution_integrated','http_integrated','cross_system_revocation','customer_value_proven'):
        assert result[field] is False,field
    sources()
    print(json.dumps({'role':role,'latest':latest,'complete_cases':len(rows),
        'reserved_cases':sum(r['charged'] for r in reservations),'payment_calls':0,'orders':0}))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['baseline','scope','sources','materials','selftest']); ap.add_argument('--role',choices=['executor','evaluator']); a=ap.parse_args()
    if a.mode=='materials': assert a.role; materials(a.role)
    elif a.mode=='selftest':
        from FROZEN_TESTS import selftest
        selftest()
    else: globals()[a.mode]()

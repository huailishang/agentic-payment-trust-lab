"""Frozen integration oracle: normal merchant routes, DB and independent fake PSP."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import yaml
from RUNTIME import TASK,ROOT,bootstrap,preflight
MUTABLE={'merchant/dependencies.py','merchant/guarded_app.py','HTTP_RUNTIME.py','RUN_JOURNEY.py','REPORT.md','RESULT.json','ATTEMPT_LEDGER.json'}
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def workspace(): return {n.decode() for n in subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).split(b'\0') if n}
def baseline():
    lock=read(TASK/'BASELINE.json')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==lock['head']
    text=(ROOT/'CURRENT.md').read_text(encoding='utf-8'); r=yaml.safe_load(text.split('```yaml',1)[1].split('```',1)[0])
    assert r['task_id']==TASK.name and r['task_kind']=='capability_experiment' and r['project_map_revision']=='2026-10-31-r93'
    assert r['hypothesis_id']=='H-57' and r['active_bottleneck_id']=='B-17'
    assert (r['state'],r['current_role']) in {('CONTRACT_FROZEN','Executor'),('EXECUTING','Executor'),('READY_FOR_REVIEW','Evaluator')}
    assert all(r['authorization_'+k] is False for k in ('commit','push','history_rewrite','api_call'))
    assert hashlib.sha256(text.split('## Global position',1)[1].encode()).hexdigest()==lock['current_history_sha256']
    for n,h in lock['protected_files'].items(): assert sha(ROOT/n)==h,n
    for n,h in lock['frozen_files'].items(): assert sha(TASK/n)==h,n
    prefix=TASK.relative_to(ROOT).as_posix()+'/'
    assert all(n.startswith(prefix) for n in workspace()-set(lock['workspace_files']))
    for p in TASK.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            n=p.relative_to(TASK).as_posix()
            assert n in lock['frozen_files'] or n in MUTABLE or n=='BASELINE.json' or n.startswith('evidence/'),n
    preflight(); print(json.dumps({'protected':len(lock['protected_files']),'frozen':len(lock['frozen_files'])}))
def scope():
    source=read(TASK/'SOURCE_COPY.json')['files']
    for n,row in source.items():
        if n!='merchant/dependencies.py': assert sha(TASK/n)==row['copy_sha256'],n
    original=ast.parse((ROOT/source['merchant/dependencies.py']['source']).read_text(encoding='utf-8'))
    current=ast.parse((TASK/'merchant/dependencies.py').read_text(encoding='utf-8'))
    def rest(tree): return [ast.dump(n,include_attributes=False) for n in tree.body if not isinstance(n,ast.FunctionDef) or n.name!='get_checkout_service']
    assert rest(original)==rest(current),'only factory body may change'
    a=next(n for n in original.body if isinstance(n,ast.FunctionDef) and n.name=='get_checkout_service')
    b=next(n for n in current.body if isinstance(n,ast.FunctionDef) and n.name=='get_checkout_service')
    assert ast.dump(a.args)==ast.dump(b.args),'keep native request-scoped dependencies'
    for name in ('merchant/guarded_app.py','HTTP_RUNTIME.py','RUN_JOURNEY.py'):
        p=TASK/name; assert p.is_file(),name
        tree=ast.parse(p.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
                targets=node.targets if isinstance(node,ast.Assign) else [node.target]
                assert not any('dependency_overrides' in ast.dump(t) for t in targets),'no test factory replacement'
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
                assert 'dependency_overrides' not in ast.dump(node.func),'no hidden factory override'
    print(json.dumps({'readonly_merchant_files':36,'allowed_merchant_changes':'one factory body + new application factory'}))
def summary(case):
    spec=next(r for r in read(TASK/'CASE_SPEC.json')['cases'] if r['id']==case['case'])
    state=case['state']; calls=case['psp_calls']
    assert len(calls)==state['payment_calls']==spec['payment_calls']
    assert len(state['orders'])==spec['orders'] and len(state['inventory'])==1
    assert state['inventory'][0]['quantity']==spec['inventory']
    assert case['default_factory_used'] is True and case['dependency_overrides_empty'] is True
    assert case['app_configured'] is (case['case']!='M05_UNCONFIGURED_APP')
    if spec['payment_calls']:
        assert len(state['attempts'])==len(case['authorization_records'])==1
        assert calls[0]['payment_ref']==state['attempts'][0]['payment_ref']
        assert json.loads(calls[0]['snapshot_json'])==case['confirmation']['snapshot']
    else: assert not state['attempts'] and not case['authorization_records']
def validate(value):
    assert value['schema']=='h57-journey-observations/v1' and value['require_signatures'] is True
    assert value['boundary']=='NATIVE_DEFAULT_FACTORY_LOCAL_ASGI_WITH_FAKE_PSP'
    cases=value['cases']; expected=[r['id'] for r in read(TASK/'CASE_SPEC.json')['cases']]
    assert [r['case'] for r in cases]==expected
    total=0
    for case in cases:
        summary(case); rows=case['calls']; total+=len(rows)
        assert rows[0]['method']=='POST' and rows[0]['path']=='/checkout-sessions' and rows[0]['response_status']==201
        assert rows[0]['response_body']['ucp']['version']=='2026-04-08'
        complete=[r for r in rows if r['method']=='POST' and r['path'].endswith('/complete')]
        assert complete
        for r in rows:
            assert r['request_id'] and r['worker_pid'] in case['worker_pids']
            headers={k.lower():v for k,v in r['headers'].items()}
            assert all(headers.get(k) for k in ('signature','signature-input','content-digest','ucp-agent','request-id','idempotency-key'))
            assert headers['request-id']==r['request_id']
            assert json.loads(r['wire_body_utf8'])==r['request_body']
            assert isinstance(r['response_status'],int)
        name=case['case']
        codes={'M02_CHANGED_AFTER_CONFIRM':'H50_SNAPSHOT_MISMATCH','M03_MISSING_CONFIRMATION':'H50_CONFIRMATION_MISSING',
            'M04_INVALID_AUTHORIZATION':'H53_AUTHORIZATION_DENIED','M05_UNCONFIGURED_APP':'H50_EXECUTION_DENIED',
            'M06_ORDER_FAILURE_RESTART_QUERY':'H50_EXECUTION_DENIED'}
        if name in codes:
            err=complete[-1]['response_body']; assert err['ucp']['status']=='error'
            assert codes[name] in {m['code'] for m in err['messages']}
        if name=='M01_NORMAL_REPLAY_QUERY':
            assert [r['response_status'] for r in complete]==[200,200]
            assert complete[0]['response_body']==complete[1]['response_body'] and complete[0]['request_body']==complete[1]['request_body']
            assert complete[0]['headers'].get('Idempotency-Key',complete[0]['headers'].get('idempotency-key'))==complete[1]['headers'].get('Idempotency-Key',complete[1]['headers'].get('idempotency-key'))
            assert any(r['method']=='GET' and r['path'].startswith('/orders/') and r['response_status']==200 for r in rows)
            assert any(r['method']=='GET' and r['path'].startswith('/checkout-sessions/') and r['response_status']==200 for r in rows)
            order_id=case['state']['orders'][0]['id']
            assert complete[0]['response_body']['order']['id']==order_id
            order_query=next(r for r in rows if r['method']=='GET' and r['path'].startswith('/orders/'))
            assert order_query['path'].rstrip('/').split('/')[-1]==order_id and order_query['response_body']['id']==order_id
        if name=='M02_CHANGED_AFTER_CONFIRM':
            assert any(r['method']=='PUT' and r['response_status']==200 and r['request_body']['line_items'][0]['quantity']==2 for r in rows)
            assert complete[-1]['response_status']==409 and case['confirmation']['snapshot']['line_items'][0]['quantity']==1
        if name in {'M03_MISSING_CONFIRMATION','M04_INVALID_AUTHORIZATION'}: assert complete[-1]['response_status']==403
        if name=='M05_UNCONFIGURED_APP': assert complete[-1]['response_status']==409
        if name=='M06_ORDER_FAILURE_RESTART_QUERY':
            assert len(set(case['worker_pids']))==2 and complete[0]['response_status']==500 and complete[-1]['response_status']==409
            assert complete[0]['worker_pid']!=complete[-1]['worker_pid']
            assert any(r['method']=='GET' and r['response_status']==200 and r['worker_pid']==complete[-1]['worker_pid'] for r in rows)
            assert case['recovery']['decision']=='QUERY' and case['recovery']['payment_state']=='SUCCEEDED'
            assert len(case['psp_queries'])==1 and case['psp_queries'][0]['payment_ref']==case['psp_calls'][0]['payment_ref']
        if name in {'M01_NORMAL_REPLAY_QUERY','M06_ORDER_FAILURE_RESTART_QUERY'}:
            bootstrap()
            spec=importlib.util.spec_from_file_location('h57_authority_oracle',TASK/'references/H53R_FIXTURES.py')
            module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
            auth=complete[0]['request_body']['risk_signals']['h53_authorization']
            ref=case['confirmation']['ref']
            signed,verified=module.independent_materials(auth,case['authorization_public_keys'],ref)
            assert signed==rows[0]['response_body'],'sign only actual merchant HTTP response, not DB-enriched data'
            record=case['authorization_records'][0]
            assert record['token_sha256']==hashlib.sha256(auth['payment_token'].encode()).hexdigest()
            assert record['checkout_sha256']==hashlib.sha256(auth['checkout_jws'].encode()).hexdigest()
            assert complete[0]['request_body']['risk_signals']['h50_confirmation_ref']==ref
    assert total<=28 and value['asgi_requests']==total
    return total
def materials(role):
    base=TASK/'evidence'/role; pointer=read(base/'LATEST.json'); folder=base/pointer['run']
    observations=read(folder/'observations.json'); total=validate(observations)
    records=[json.loads(l) for l in (base/'HTTP_ATTEMPTS.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(records)<=(160 if role=='executor' else 80)
    ids={r['request_id'] for r in records}; assert len(ids)==len(records)
    assert all(r['request_id'] in ids for c in observations['cases'] for r in c['calls'])
    for case in observations['cases']:
        assert read(folder/(case['case']+'.json'))==case
    ledger=read(TASK/'ATTEMPT_LEDGER.json')
    assert 0<=ledger['active_work_minutes']<=240 and ledger['formal_l2_attempts']==len(list((TASK/'evidence').glob('l2_executor_*')))<=2
    executor_lines=(TASK/'evidence/executor/HTTP_ATTEMPTS.jsonl').read_text(encoding='utf-8').splitlines()
    assert ledger['asgi_requests_reserved']==len(executor_lines)<=160
    for k in ('network_calls','model_calls','provider_calls','real_payment_calls','packages_installed','git_write_operations'): assert ledger[k]==0
    result=read(TASK/'RESULT.json'); assert result['schema']=='h57-result/v1' and result['task_id']==TASK.name
    assert result['classification']=='DEFAULT_FACTORY_MERCHANT_E2E_OBSERVED' and result['customer_demand']=='UNKNOWN' and result['remaining_gaps']
    for k in ('production_ready','real_identity_verified','provider_verified','standard_checkout_mandate_integrated','h56_profile_integrated','automatic_order_recovery','customer_value_proven'): assert result[k] is False
    print(json.dumps({'journeys':6,'requests':total,'role':role,'factory_override':False}))
def selftest():
    for row in read(TASK/'CASE_SPEC.json')['cases']:
        n=row['payment_calls']; data={'case':row['id'],'default_factory_used':True,'dependency_overrides_empty':True,
            'app_configured':row['id']!='M05_UNCONFIGURED_APP','psp_calls':[],'authorization_records':[],
            'state':{'payment_calls':n,'orders':[{}]*row['orders'],'inventory':[{'quantity':row['inventory']}],'attempts':[]},'confirmation':{'snapshot':{}}}
        if n:
            data['psp_calls']=[{'payment_ref':'fake','snapshot_json':'{}'}]; data['authorization_records']=[{}]; data['state']['attempts']=[{'payment_ref':'fake'}]
        summary(data)
        corrupt=copy.deepcopy(data); corrupt['state']['payment_calls']+=1
        try: summary(corrupt)
        except AssertionError: pass
        else: raise AssertionError('wrong payment counter accepted')
    print(json.dumps({'counter_guard_selftests':6,'candidate_called':False}))
if __name__=='__main__':
    if sys.argv[1]=='materials': materials(sys.argv[2])
    else: {'baseline':baseline,'scope':scope,'selftest':selftest}[sys.argv[1]]()

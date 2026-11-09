"""Frozen H57 business oracle plus strict journal and real process-exit evidence."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import yaml
from RUNTIME import TASK,ROOT,preflight

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('h57_inherited_oracle',TASK/'references/H57_CHECK.py')
OLD=importlib.util.module_from_spec(spec);spec.loader.exec_module(OLD)
validate=OLD.validate
MUTABLE={'HTTP_RUNTIME.py','RUN_JOURNEY.py','REPORT.md','RESULT.json','ATTEMPT_LEDGER.json'}

def history():
    raw=(TASK/'references/LEGACY_HTTP_ATTEMPTS.raw').read_text(encoding='utf-8')
    decoder=json.JSONDecoder();offset=0;legacy=[]
    while offset<len(raw):
        row,end=decoder.raw_decode(raw,offset);legacy.append(row)
        assert raw[end:end+2]=='\\n';offset=end+2
    later=[json.loads(l) for l in (TASK/'references/H57_LATER_HTTP_ATTEMPTS.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(legacy)==25 and len({r['request_id'] for r in legacy})==2
    assert len(later)==len({r['request_id'] for r in later})==32
    return legacy+later

def baseline():
    lock=read(TASK/'BASELINE.json')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==lock['head']
    text=(ROOT/'CURRENT.md').read_text(encoding='utf-8')
    router=yaml.safe_load(text.split('```yaml',1)[1].split('```',1)[0])
    assert router['task_id']==TASK.name and router['task_kind']=='repair'
    assert router['project_map_revision']=='2026-11-01-r94' and router['active_bottleneck_id']=='B-17' and router['hypothesis_id']=='H-57'
    assert (router['state'],router['current_role']) in {('CONTRACT_FROZEN','Executor'),('EXECUTING','Executor'),('READY_FOR_REVIEW','Evaluator')}
    assert all(router['authorization_'+k] is False for k in ('commit','push','history_rewrite','api_call'))
    assert hashlib.sha256(text.split('## Global position',1)[1].encode()).hexdigest()==lock['current_history_sha256']
    for n,h in lock['protected_files'].items():assert sha(ROOT/n)==h,n
    for n,h in lock['frozen_files'].items():assert sha(TASK/n)==h,n
    files={n.decode('utf-8') for n in subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).split(b'\0') if n}
    prefix=TASK.relative_to(ROOT).as_posix()+'/'
    assert all(n.startswith(prefix) for n in files-set(lock['workspace_files']))
    for p in TASK.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            n=p.relative_to(TASK).as_posix()
            assert n in lock['frozen_files'] or n in MUTABLE or n=='BASELINE.json' or n.startswith('evidence/'),n
    preflight();print(json.dumps({'protected':len(lock['protected_files']),'frozen':len(lock['frozen_files']),'inherited_reservations':len(history())}))

def scope():
    copies=read(TASK/'SOURCE_COPY.json')['files']
    merchant=[n for n in copies if n.startswith('merchant/')]
    assert len(merchant)==38
    for n in merchant:assert sha(TASK/n)==copies[n]['sha256'],n
    for n in ('HTTP_RUNTIME.py','RUN_JOURNEY.py'):
        tree=ast.parse((TASK/n).read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
                targets=node.targets if isinstance(node,ast.Assign) else [node.target]
                assert not any('dependency_overrides' in ast.dump(t) for t in targets)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):assert 'dependency_overrides' not in ast.dump(node.func)
    print(json.dumps({'frozen_merchant_files':38,'mutable_harness_files':2,'business_changes_allowed':False}))

def journal(records,observations,run_name):
    old_ids={r['request_id'] for r in history()}
    ids=[r['request_id'] for r in records]
    assert len(ids)==len(set(ids)) and not old_ids.intersection(ids)
    lookup={r['request_id']:r for r in records}
    for case in observations['cases']:
        for call in case['calls']:
            row=lookup[call['request_id']]
            assert row['case']==case['case'] and row['run']==run_name
            assert row['worker_pid']==call['worker_pid']
            assert row['phase']==call['method']+' '+call['path']

def process_exit(proof,case):
    events=proof['events']
    assert [(e['phase'],e['event']) for e in events]==[('first','started'),('first','exited'),('second','started'),('second','exited')]
    assert all(isinstance(e['monotonic_ns'],int) and e['monotonic_ns']>0 for e in events)
    assert all(a['monotonic_ns']<b['monotonic_ns'] for a,b in zip(events,events[1:]))
    first,second=events[0]['pid'],events[2]['pid']
    assert events[1]['pid']==first and events[3]['pid']==second
    assert len({proof['supervisor_pid'],first,second})==3
    assert events[1]['exit_code']==events[3]['exit_code']==0
    assert case['worker_pids']==[first,second]
    calls=case['calls'];assert [r['worker_pid'] for r in calls]==[first,first,second,second]
    assert [r['response_status'] for r in calls]==[201,500,200,409]
    assert proof['transactions_db']==case['durable_storage']['transactions_db']
    assert proof['psp_db']==case['durable_storage']['psp_db']
    for key in ('transactions_db','psp_db'):
        assert Path(proof[key]).resolve().is_relative_to((ROOT/'.task_envs/H57/runs').resolve())

def materials(role):
    folder=TASK/'evidence'/role
    pointer=read(folder/'LATEST.json')['run'];assert Path(pointer).name==pointer and pointer.startswith('run_')
    run=folder/pointer;value=read(run/'observations.json');total=validate(value)
    for case in value['cases']:assert read(run/(case['case']+'.json'))==case
    rows=[json.loads(l) for l in (folder/'HTTP_ATTEMPTS.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(rows)<=(103 if role=='executor' else 80)
    journal(rows,value,pointer)
    case=value['cases'][-1];proof=read(run/'M06_processes.json');process_exit(proof,case)
    for phase in ('first','second'):
        receipt=proof['artifacts'][phase]
        for stream in ('stdout','stderr'):
            file=run/('M06_'+phase+'.'+stream+'.log')
            assert sha(file)==receipt[stream+'_sha256']
        assert receipt['exit_code']==0
    ledger=read(TASK/'ATTEMPT_LEDGER.json')
    exe=TASK/'evidence/executor/HTTP_ATTEMPTS.jsonl'
    exe_rows=[json.loads(l) for l in exe.read_text(encoding='utf-8').splitlines()]
    assert ledger['inherited_asgi_reservations']==57 and ledger['new_asgi_requests_reserved']==len(exe_rows)
    assert ledger['asgi_requests_reserved']==57+len(exe_rows)<=160
    assert ledger['inherited_time_charge_minutes']==120 and 0<=ledger['active_work_minutes']<=90
    assert ledger['charged_minutes_total']==120+ledger['active_work_minutes']<=240
    assert ledger['inherited_formal_l2_attempts']==0
    assert ledger['formal_l2_attempts']==len(list((TASK/'evidence').glob('l2_executor_*')))<=2
    for key in ('network_calls','model_calls','provider_calls','real_payment_calls','packages_installed','git_write_operations'):assert ledger[key]==0
    result=read(TASK/'RESULT.json')
    assert result['schema']=='h57r-result/v1' and result['task_id']==TASK.name
    assert result['classification']=='NATIVE_FACTORY_EVIDENCE_REPAIRED' and result['customer_demand']=='UNKNOWN' and result['remaining_gaps']
    for key in ('production_ready','real_identity_verified','provider_verified','standard_checkout_mandate_integrated','h56_profile_integrated','automatic_order_recovery','customer_value_proven'):assert result[key] is False
    print(json.dumps({'journeys':6,'requests':total,'role':role,'inherited_reservations':57,'new_executor_reservations':len(exe_rows),'first_process_exit_required':True}))

def selftest():
    OLD.selftest()
    calls=[{'worker_pid':pid,'response_status':status} for pid,status in ((2,201),(2,500),(3,200),(3,409))]
    base=str(ROOT/'.task_envs/H57/runs/synthetic-selftest')
    case={'worker_pids':[2,3],'calls':calls,'durable_storage':{'transactions_db':base+'/transactions.db','psp_db':base+'/psp.db'}}
    proof={'supervisor_pid':1,**case['durable_storage'],'events':[
        {'phase':'first','event':'started','pid':2,'monotonic_ns':1},
        {'phase':'first','event':'exited','pid':2,'monotonic_ns':2,'exit_code':0},
        {'phase':'second','event':'started','pid':3,'monotonic_ns':3},
        {'phase':'second','event':'exited','pid':3,'monotonic_ns':4,'exit_code':0}]}
    process_exit(proof,case)
    bads=[]
    p=copy.deepcopy(proof);p['supervisor_pid']=2;bads.append(p)
    p=copy.deepcopy(proof);p['events'][1]['event']='closed_app';bads.append(p)
    p=copy.deepcopy(proof);p['events'][2]['monotonic_ns']=1;bads.append(p)
    p=copy.deepcopy(proof);p['events'][1]['exit_code']=9;bads.append(p)
    for p in bads:
        try:process_exit(p,case)
        except AssertionError:pass
        else:raise AssertionError('invalid process proof accepted')
    record={'request_id':'fresh-selftest','case':'C','run':'run_selftest','worker_pid':2,'phase':'POST /x'}
    value={'cases':[{'case':'C','calls':[{'request_id':'fresh-selftest','worker_pid':2,'method':'POST','path':'/x'}]}]}
    journal([record],value,'run_selftest')
    for records in ([record,record],[dict(record,run='wrong')]):
        try:journal(records,value,'run_selftest')
        except AssertionError:pass
        else:raise AssertionError('invalid journal accepted')
    print(json.dumps({'new_negative_selftests':6,'http_requests':0,'candidate_called':False}))

if __name__=='__main__':
    if sys.argv[1]=='materials':materials(sys.argv[2])
    else:{'baseline':baseline,'scope':scope,'selftest':selftest}[sys.argv[1]]()

"""Frozen measurement protection and evidence checker; no new policy gate."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import yaml
from RUNTIME import TASK,ROOT,preflight
from REFERENCE import cases,sdk,check_pairs
MUTABLE={'REPORT.md','RESULT.json','ATTEMPT_LEDGER.json','MECHANISM_COMPARISON.json'}
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def workspace(): return {x.decode() for x in subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).split(b'\0') if x}
def baseline():
    lock=read(TASK/'BASELINE.json')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==lock['head']
    text=(ROOT/'CURRENT.md').read_text(encoding='utf-8'); route=yaml.safe_load(text.split('```yaml',1)[1].split('```',1)[0])
    assert route['task_id']==TASK.name and route['task_kind']=='one_off' and route['project_map_revision']=='2026-10-31-r91'
    assert route['active_bottleneck_id']=='B-17' and route['hypothesis_id']=='H-55'
    assert (route['state'],route['current_role']) in {('CONTRACT_FROZEN','Executor'),('EXECUTING','Executor'),('READY_FOR_REVIEW','Evaluator')}
    assert all(route['authorization_'+n] is False for n in ('commit','push','history_rewrite','api_call'))
    assert hashlib.sha256(text.split('## Global position',1)[1].encode()).hexdigest()==lock['current_history_sha256']
    for name,expected in lock['protected_files'].items(): assert sha(ROOT/name)==expected,name
    for name,expected in lock['frozen_files'].items(): assert sha(TASK/name)==expected,name
    prefix=TASK.relative_to(ROOT).as_posix()+'/'
    assert all(n.startswith(prefix) for n in workspace()-set(lock['workspace_files']))
    for p in TASK.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            n=p.relative_to(TASK).as_posix()
            assert n in lock['frozen_files'] or n in MUTABLE or n=='BASELINE.json' or n.startswith('evidence/'),n
    preflight(); print(json.dumps({'protected_files':len(lock['protected_files']),'frozen_files':len(lock['frozen_files'])}))
def observations(role):
    base=TASK/'evidence'/role; folder=base/read(base/'LATEST.json')['run']
    rows=read(folder/'observations.json')['rows']
    expected={(r['case'],i) for r in cases() for i in (1,2)}
    assert {(r['case'],r['repeat']) for r in rows}==expected and len(rows)==12
    for r in rows:
        assert r['input']==next(v for v in cases() if v['case']==r['case'])
        assert r['check']=='PASS' and r['response']['status']==r['input']['expected_status']
        current=sdk(r['input']); assert current['status']==r['sdk']['status']
        if current['status']=='VALID': assert current['root']==r['sdk']['root'] and current['claims']==r['sdk']['claims']
        stem=folder/(r['case']+f".r{r['repeat']}")
        assert read(stem.with_suffix(stem.suffix+'.output.json'))==r
        inp=read(stem.with_suffix(stem.suffix+'.input.json')); assert all(r[k]==v for k,v in inp.items())
    for case in cases():
        repeated=[r for r in rows if r['case']==case['case']]
        assert repeated[0]['response']==repeated[1]['response']
        assert repeated[0]['sdk']==repeated[1]['sdk']
    ledger=[json.loads(l) for l in (base/'ATTEMPTS.jsonl').read_text(encoding='utf-8').splitlines()]
    assert sum(r['charged'] for r in ledger)<=(72 if role=='executor' else 48)
    print(json.dumps({'role':role,'paired_observations':12,'repeat_consistent':True}))
def materials():
    comparison=read(TASK/'MECHANISM_COMPARISON.json')
    rows=comparison['mechanisms']; assert {r['id'] for r in rows}=={'NO_CHANGE','ALL_RELEVANT_DIGESTS_RESOLVED','EXPLICIT_SIGNED_PROFILE'}
    for r in rows:
        assert r['classification'] in {'ABSORB','REFERENCE_ONLY','REJECT','DEFER'}
        for k in ('evidence','privacy_tradeoff','compatibility','risk','estimated_cost','unknowns'): assert r[k]
    assert comparison['next_decision'] in {'BOUNDED_PROFILE_CONTRACT_REQUIRED','MEASUREMENT_LIMITATION_STOP'}
    assert comparison['why_not_execution'] and comparison['remaining_exact_input']
    result=read(TASK/'RESULT.json')
    assert result['schema']=='h55-result/v1' and result['task_id']==TASK.name
    assert result['classification']=='DISCLOSED_VIEW_NOT_AUTHORITY_COMPLETENESS_PROOF'
    assert result['new_policy_implemented'] is False and result['execution_ready'] is False
    assert result['customer_demand']=='UNKNOWN' and result['remaining_gaps']
    ledger=read(TASK/'ATTEMPT_LEDGER.json'); assert 0<=ledger['active_work_minutes']<=120
    assert ledger['formal_l2_attempts']==len(list((TASK/'evidence').glob('l2_executor_*')))<=2
    measured=sum(json.loads(l)['charged'] for l in (TASK/'evidence/executor/ATTEMPTS.jsonl').read_text(encoding='utf-8').splitlines())
    assert ledger['consumer_calls_reserved']==measured<=72
    for key in ('network_calls','asgi_requests','model_calls','provider_calls','packages_installed','payment_calls','orders_created','git_write_operations'): assert ledger[key]==0
    print(json.dumps({'mechanisms':3,'new_policy_implemented':False,'reserved':measured}))
if __name__=='__main__':
    if sys.argv[1]=='observations': observations(sys.argv[2])
    elif sys.argv[1]=='sources': check_pairs()
    else: {'baseline':baseline,'materials':materials}[sys.argv[1]]()

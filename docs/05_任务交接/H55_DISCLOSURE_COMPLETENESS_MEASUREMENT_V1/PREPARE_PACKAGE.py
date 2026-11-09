"""Evaluator prepares immutable signed presentation pairs; no consumer calls."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import shutil
TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
PARENT=TASK.parent/'H54R_NONDELEGATING_CHECKOUT_ROOT_REPAIR_V1'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def decode(s): return base64.urlsafe_b64decode(s+'='*(-len(s)%4))
def b64(raw): return base64.urlsafe_b64encode(raw).decode().rstrip('=')
def wire(obj): return json.dumps(obj,ensure_ascii=True).encode()
def base(row):
    return {k:copy.deepcopy(row[k]) for k in ('request_b64','session_b64','trust','now','token','public_keys')}
def token(row,value):
    row['token']=value
    req=json.loads(decode(row['request_b64'])); req['ap2']['checkout_mandate']=value
    row['request_b64']=b64(wire(req)); return row
def main():
    assert not (TASK/'FIXED_CASES.json').exists()
    sources=[]
    names=['consumer.py','RUNTIME.py','SOURCE_MANIFEST.json']
    names += [p.relative_to(PARENT).as_posix() for p in (PARENT/'sources').rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and 'evaluator' not in p.parts]
    for name in names:
        src=PARENT/name; dest=TASK/('consumer_snapshot.py' if name=='consumer.py' else name)
        dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dest)
        if name=='RUNTIME.py':
            dest.write_text(dest.read_text(encoding='utf-8').replace('.task_envs/H54R/runs','.task_envs/H55/runs'),encoding='utf-8')
        sources.append({'source':src.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
            'copy':dest.relative_to(TASK).as_posix(),'copy_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
    rows=read(PARENT/'evidence/review_20261031/GENERALIZATION_OBSERVATIONS.json')['rows']
    hidden=next(r for r in rows if r['case']=='V07_REDACTED_OUTER_CNF')
    optional=next(r for r in rows if r['case']=='V02_DISCLOSED_UNKNOWN_ROOT')
    d1=token(base(hidden),hidden['fully_disclosed_token'])
    d2=base(hidden)
    d3=base(optional)
    parts=optional['token'].split('~')
    notes=[d for d in parts[1:-1] if json.loads(decode(d))[1]=='optional_note']
    assert len(notes)==1
    parts.remove(notes[0]); d4=token(base(optional),'~'.join(parts))
    observed=PARENT/'evidence/evaluator'
    latest=read(observed/'LATEST.json')['run']
    normal=next(r for r in read(observed/latest/'observations.json')['rows'] if r['case']=='C01_NORMAL')
    d5=base(normal)
    h,p,s=d2['token'].split('~')[0].split('.')
    corrupted=h+'.'+p+'.'+('A' if s[0]!='A' else 'B')+s[1:]
    d6=token(base(d2),corrupted+'~'+'~'.join(d2['token'].split('~')[1:]))
    cases=[]
    specs=[(d1,'D01_CNF_REVEALED','DENY',True),(d2,'D02_CNF_REDACTED','VERIFIED',False),
        (d3,'D03_OPTIONAL_REVEALED','VERIFIED',False),(d4,'D04_OPTIONAL_REDACTED','VERIFIED',False),
        (d5,'D05_NORMAL_CONTROL','VERIFIED',False),(d6,'D06_BAD_SIGNATURE','DENY',None)]
    for row,name,expected,root_cnf in specs:
        row.update(case=name,expected_status=expected,expected_root_cnf=root_cnf,
            expected_sdk='REJECTED' if root_cnf is None else 'VALID')
        cases.append(row)
    cases[1]['fully_disclosed_token']=cases[0]['token']
    cases[1]['omitted_name']='cnf'
    cases[3]['fully_disclosed_token']=cases[2]['token']
    cases[3]['omitted_name']='optional_note'
    (TASK/'FIXED_CASES.json').write_text(json.dumps({'schema':'h55-fixed-presentations/v1','cases':cases},ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    (TASK/'SOURCE_COPY.json').write_text(json.dumps({'files':sources,'consumer_snapshot_unchanged':True,
        'fixture_sources':['H54R GENERALIZATION_OBSERVATIONS V02/V07','H54R independent C01'],
        'preparation_consumer_calls':0,'D04_status':'predicted from unchanged code; not preparation measured'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'immutable_copies':len(sources),'fixed_presentations':6,'preparation_consumer_calls':0}))
if __name__=='__main__': main()

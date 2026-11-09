"""Frozen measurement only: replay the immutable accepted consumer snapshot."""
import argparse
import copy
import importlib.util
import json
import sys
from RUNTIME import TASK,bootstrap
bootstrap()
from REFERENCE import cases,decode,sdk
def main(role):
    base=TASK/'evidence'/role; base.mkdir(parents=True,exist_ok=True)
    log=base/'ATTEMPTS.jsonl'
    prior=[json.loads(l) for l in log.read_text(encoding='utf-8').splitlines()] if log.exists() else []
    assert sum(r['charged'] for r in prior)+12<=(72 if role=='executor' else 48)
    folder=base/f'run_{len(prior)+1:04d}'; folder.mkdir()
    with log.open('a',encoding='utf-8') as f: f.write(json.dumps({'run':folder.name,'charged':12,'presentations':6,'repeats':2})+'\n'); f.flush()
    spec=importlib.util.spec_from_file_location('h55_immutable_consumer',TASK/'consumer_snapshot.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    observations=[]
    for row in cases():
        for repeat in (1,2):
            result={'case':row['case'],'repeat':repeat,'input':copy.deepcopy(row),'sdk':sdk(row)}
            target=folder/(row['case']+f'.r{repeat}')
            target.with_suffix(target.suffix+'.input.json').write_text(json.dumps(result,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
            trust=copy.deepcopy(row['trust'])
            try:
                response=module.consume(decode(row['request_b64']),decode(row['session_b64']),trust,row['now'])
                result['response']=response
                assert trust==row['trust'] and response['status']==row['expected_status']
                assert result['sdk']['status']==row['expected_sdk']
                result['check']='PASS'
            except Exception as exc: result['check']='FAIL'; result['error']=type(exc).__name__+': '+str(exc)
            target.with_suffix(target.suffix+'.output.json').write_text(json.dumps(result,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
            observations.append(result)
    (folder/'observations.json').write_text(json.dumps({'rows':observations},ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    (base/'LATEST.json').write_text(json.dumps({'run':folder.name})+'\n',encoding='utf-8')
    print(json.dumps({'measurements':12,'passed':sum(r['check']=='PASS' for r in observations),'consumer_modified':False,'payment_calls':0}))
    return any(r['check']!='PASS' for r in observations)
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--role',required=True,choices=['executor','evaluator']); a=ap.parse_args(); sys.exit(main(a.role))

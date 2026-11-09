"""Frozen three-case regression for full verified SD-JWT root conditions."""
import argparse
import base64
import copy
import importlib.util
import json
import sys
from RUNTIME import TASK,bootstrap
bootstrap()
from FIXTURES import NOW,RawClaims,b64,digest
from ap2.sdk.mandate import MandateClient
from ap2.sdk.sdjwt.sd_jwt import verify as verify_root
from jwcrypto.jwk import JWK
from jwcrypto.jws import JWS
from JCS_CHECK import oracle

CASES=['U01_NEW_KEYS_AND_TERMS','U02_OUTER_CNF','U03_DISCLOSED_OUTER_CNF']
spec=importlib.util.spec_from_file_location('h54r_frozen_holdout_generator',TASK/'sources/evaluator/H54_HOLDOUT.py')
generator=importlib.util.module_from_spec(spec); spec.loader.exec_module(generator)
def decode(s): return base64.urlsafe_b64decode(s+'='*(-len(s)%4))
def inspect(row):
    root=verify_root(row['token'],JWK(**row['public_keys']['platform']))
    effective=MandateClient().verify(row['token'],JWK(**row['public_keys']['platform']),
        payload_type=RawClaims,current_time=NOW,clock_skew_seconds=0).mandate_payload.model_dump()
    assert root==row['sdk']['verified_root'] and effective==row['sdk']['effective_claims']
    if row['case']!='U01_NEW_KEYS_AND_TERMS':
        assert root['cnf']['jwk'] and 'cnf' not in effective
    else: assert 'cnf' not in root and 'cnf' not in effective
    result=row['result']
    if row['case']!='U01_NEW_KEYS_AND_TERMS':
        assert result.get('status')=='DENY',row['case']
        assert not any(k in result for k in ('checkout','checkout_jwt','checkout_hash'))
    else:
        assert result.get('status')=='VERIFIED'
        assert result['checkout']==json.loads(decode(row['session_b64']))
        assert result['checkout_jwt']==effective['checkout_jwt'] and result['checkout_hash']==effective['checkout_hash']
        assert result['mandate_sha256']==digest(row['token'].encode())
        assert result['request_sha256']==digest(decode(row['request_b64']))
        assert result['session_sha256']==digest(decode(row['session_b64']))
        assert result['platform_kid']=='holdout-distinct-platform' and result['merchant_kid']=='holdout-distinct-merchant'
        jws=JWS(); jws.deserialize(result['checkout_jwt']); jws.verify(JWK(**row['public_keys']['merchant']))
        assert jws.payload==oracle({k:v for k,v in result['checkout'].items() if k!='ap2'})
def main(role):
    base=TASK/'evidence'/role; base.mkdir(parents=True,exist_ok=True)
    ledger=base/'ROOT_ATTEMPTS.jsonl'
    prior=[json.loads(l) for l in ledger.read_text().splitlines()] if ledger.exists() else []
    assert sum(r['charged'] for r in prior)+3 <= (24 if role=='executor' else 9)
    folder=base/f'root_{len(prior)+1:04d}'; folder.mkdir()
    with ledger.open('a',encoding='utf-8') as f:
        f.write(json.dumps({'run':folder.name,'cases':CASES,'charged':3})+'\n'); f.flush()
    spec=importlib.util.spec_from_file_location('h54r_candidate',TASK/'consumer.py')
    candidate=importlib.util.module_from_spec(spec); spec.loader.exec_module(candidate)
    rows=[]
    for name in CASES:
        m=generator.make(name)
        root=verify_root(m['token'],JWK(**m['public_keys']['platform']))
        effective=MandateClient().verify(m['token'],JWK(**m['public_keys']['platform']),
            payload_type=RawClaims,current_time=NOW,clock_skew_seconds=0).mandate_payload.model_dump()
        row={'case':name,'expected':'VERIFIED' if name==CASES[0] else 'DENY',
            'token':m['token'],'request_b64':b64(m['request_raw']),'session_b64':b64(m['session_raw']),
            'public_keys':m['public_keys'],'trust':copy.deepcopy(m['trust']),'now':NOW,
            'sdk':{'status':'VALID','verified_root':root,'effective_claims':effective}}
        (folder/(name+'.input.json')).write_text(json.dumps(row,ensure_ascii=True,indent=2)+'\n')
        try:
            row['result']=candidate.consume(m['request_raw'],m['session_raw'],m['trust'],NOW)
            assert m['trust']==row['trust']
            inspect(row); row['check']='PASS'
        except Exception as exc:
            row['check']='FAIL'; row['error']=type(exc).__name__+': '+str(exc)
        (folder/(name+'.output.json')).write_text(json.dumps(row,ensure_ascii=True,indent=2)+'\n')
        rows.append(row)
    (folder/'observations.json').write_text(json.dumps({'rows':rows},ensure_ascii=True,indent=2)+'\n')
    (base/'ROOT_LATEST.json').write_text(json.dumps({'run':folder.name})+'\n')
    print(json.dumps({'root_cases':3,'passed':sum(r['check']=='PASS' for r in rows),'payment_calls':0}))
    return any(r['check']!='PASS' for r in rows)
def selftest():
    parent=TASK.parent/'H54_STANDARD_CHECKOUT_MANDATE_CONSUMER_V1/evidence/review_20261031/HOLDOUT_OBSERVATIONS.json'
    old=json.loads(parent.read_text())['rows']; rejected=[]
    for row in old:
        if row['case'] not in CASES: continue
        if row['case']==CASES[0]: inspect(row)
        else:
            try: inspect(row)
            except AssertionError: rejected.append(row['case'])
            else: raise AssertionError('parent counterexample no longer detected')
    assert rejected==CASES[1:]
    print(json.dumps({'parent_counterexamples_rejected':rejected,'parent_valid_control':'PASS','candidate_called':False}))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--role',choices=['executor','evaluator']); ap.add_argument('--selftest',action='store_true'); a=ap.parse_args()
    if a.selftest: selftest()
    else: assert a.role; sys.exit(main(a.role))

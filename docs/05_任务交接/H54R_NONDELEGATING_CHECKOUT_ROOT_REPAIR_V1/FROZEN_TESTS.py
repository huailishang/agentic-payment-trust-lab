"""Evaluator-owned behavioral checks; Executor implements consumer.py only."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
from RUNTIME import TASK, bootstrap
bootstrap()
from FIXTURES import CASE_IDS, VALID, NOW, VERSION, b64, digest, keys, material, RawClaims
from JCS_CHECK import oracle
from ap2.sdk.mandate import MandateClient
from jwcrypto.jwk import JWK
from jwcrypto.jws import JWS

DENIAL_CODES={'mandate_required','agent_missing_key','mandate_invalid_signature','mandate_expired',
    'mandate_scope_mismatch','merchant_authorization_invalid','merchant_authorization_missing',
    'unsupported_profile','invalid_input'}

def assert_result(m,result):
    assert isinstance(result,dict) and result.get('status')==m['expected'], m['case']
    if m['case'] not in VALID:
        assert result.get('code') in DENIAL_CODES, m['case']
        assert not any(k in result for k in ('checkout','checkout_jwt','checkout_hash')), 'DENY leaks usable authority'
        return
    token=m['token']; compact=m['checkout_jwt']
    # Recheck the independently issued material through official SDK and JWS.
    verified=MandateClient().verify(token,JWK(**m['public_keys']['platform']),payload_type=RawClaims,
        current_time=NOW,clock_skew_seconds=0).mandate_payload.model_dump()
    assert verified['vct']=='mandate.checkout.1' and verified['checkout_jwt']==compact
    jws=JWS(); jws.deserialize(compact); jws.verify(JWK(**m['public_keys']['merchant']))
    embedded=json.loads(jws.payload)
    assert jws.payload==oracle(embedded)
    expected_checkout=json.loads(m['session_raw'])
    assert result.get('checkout')==expected_checkout
    assert oracle({k:v for k,v in result['checkout'].items() if k!='ap2'})==jws.payload
    assert result.get('checkout_jwt')==compact
    assert result.get('checkout_hash')==verified['checkout_hash']
    assert result.get('mandate_sha256')==digest(token.encode())
    assert result.get('request_sha256')==digest(m['request_raw'])
    assert result.get('session_sha256')==digest(m['session_raw'])
    assert result.get('platform_kid')=='h54-platform' and result.get('merchant_kid')=='h54-merchant'
    assert result.get('protocol_version')==VERSION
    assert 'd' not in json.dumps(m['trust']).split('"')

def load_candidate():
    path=TASK/'consumer.py'
    assert path.is_file(), 'Executor must implement consumer.py; no candidate exists at freeze'
    spec=importlib.util.spec_from_file_location('h54_candidate',path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    assert callable(module.consume)
    return module.consume

def run(consume,case_ids,folder):
    registry=keys(); rows=[]
    for name in case_ids:
        m=material(name,registry); trust_before=copy.deepcopy(m['trust'])
        row={'case':name,'expected':m['expected'],
            'request_sha256':digest(m['request_raw']),'session_sha256':digest(m['session_raw']),
            'consent_receipt':m['consent_receipt']}
        row.update({'request_b64':b64(m['request_raw']),'session_b64':b64(m['session_raw']),
            'trust':copy.deepcopy(m['trust']),'now':m['now'],'checkout_jwt':m['checkout_jwt'],
            'token':m['token'],'public_keys':m['public_keys']})
        # Preserve raw inputs before the candidate is invoked, including failures.
        (folder/(name+'.input.json')).write_text(json.dumps(row,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
        try:
            result=consume(m['request_raw'],m['session_raw'],m['trust'],m['now'])
            row['result']=result
            assert m['trust']==trust_before, 'consumer mutated trusted state'
            assert_result(m,result)
            row['check']='PASS'
        except Exception as exc:
            row['check']='FAIL'; row['error']=type(exc).__name__+': '+str(exc)
        (folder/(name+'.output.json')).write_text(json.dumps(row,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
        rows.append(row)
    return rows

def selftest():
    # Checker must reject both trivial implementations and broken authority.
    reg=keys(); normal=material('C01_NORMAL',reg); bad=material('C08_MISSING_MANDATE',reg)
    for m,result in [(normal,{'status':'DENY','code':'invalid_input'}),
                     (bad,{'status':'VERIFIED'}),
                     (bad,{'status':'DENY','code':'invalid_input','checkout':{}}),
                     (normal,{'status':'VERIFIED','checkout':{}})]:
        try: assert_result(m,result)
        except (AssertionError,KeyError): pass
        else: raise AssertionError('checker accepted corruption')
    print(json.dumps({'checker_selftest':'PASS','rejected_corruptions':4,'candidate_called':False}))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--role',choices=['executor','evaluator']); ap.add_argument('--case',choices=CASE_IDS); ap.add_argument('--selftest',action='store_true'); args=ap.parse_args()
    if args.selftest: selftest(); sys.exit(0)
    assert args.role
    case_ids=[args.case] if args.case else CASE_IDS
    base=TASK/'evidence'/args.role; base.mkdir(parents=True,exist_ok=True)
    ledger=base/'ATTEMPTS.jsonl'
    prior=[json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()] if ledger.exists() else []
    budget=288 if args.role=='executor' else 108
    assert sum(len(r['cases']) for r in prior)+len(case_ids)<=budget, 'case budget exhausted'
    folder=base/f'run_{len(prior)+1:04d}'; folder.mkdir()
    reservation={'run':folder.name,'cases':case_ids,'charged':len(case_ids)}
    with ledger.open('a',encoding='utf-8') as f: f.write(json.dumps(reservation)+'\n'); f.flush()
    # Import failure still spends the reserved cases and leaves a reservation.
    rows=run(load_candidate(),case_ids,folder)
    (folder/'observations.json').write_text(json.dumps({'schema':'h54-observations/v1','rows':rows},ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    if not args.case:
        (base/'LATEST.json').write_text(json.dumps({'run':folder.name})+'\n',encoding='utf-8')
    print(json.dumps({'cases':len(rows),'passed':sum(r['check']=='PASS' for r in rows),
        'failed':sum(r['check']=='FAIL' for r in rows),'payment_calls':0,'orders':0,
        'run':folder.name,'scope':'artifact consumer only'}))
    sys.exit(any(r['check']!='PASS' for r in rows))

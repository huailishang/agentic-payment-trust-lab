"""Frozen profile fixtures and behavioral oracle; no completeness implementation."""
import argparse
import base64
import copy
import hashlib
import importlib.util
import json
import sys
from RUNTIME import TASK,bootstrap
bootstrap()
from FIXTURES import NOW,VERSION,RawClaims,keys,material,wire,b64,public,digest
from ap2.sdk.mandate import MandateClient
from ap2.sdk.sdjwt.sd_jwt import verify as verify_root
from jwcrypto.jwk import JWK
from jwcrypto.jws import JWS
from JCS_CHECK import oracle
PROFILE='h56-nondelegating-checkout-complete-v1'
CASES=['P01_ROOT_CNF_REVEALED','P02_ROOT_CNF_HIDDEN','P03_EFFECTIVE_CNF_REVEALED','P04_EFFECTIVE_CNF_HIDDEN',
 'P05_UNKNOWN_ROOT_FULL','P06_UNKNOWN_ROOT_HIDDEN','P07_OPTIONAL_AREA_FULL','P08_OPTIONAL_AREA_HIDDEN',
 'P09_NO_TRUSTED_PROFILE','P10_REQUEST_PROFILE_ONLY','P11_PROFILE_KEY_MISMATCH',
 'P12_UNKNOWN_NESTED_CONDITION','P13_OPTIONAL_AREA_ITSELF_HIDDEN','P14_SECURITY_DECOY']
ALLOW={'P05_UNKNOWN_ROOT_FULL','P07_OPTIONAL_AREA_FULL','P08_OPTIONAL_AREA_HIDDEN'}
def decode(s): return base64.urlsafe_b64decode(s+'='*(-len(s)%4))
def disclosure(name,value):
    raw=b64(wire(['h56-synthetic-salt-'+name,name,value]))
    return raw,b64(hashlib.sha256(raw.encode()).digest())
def make(name):
    assert name in CASES
    reg=keys(); normal=material('C01_NORMAL',reg)
    claims=MandateClient().verify(normal['token'],reg['platform'],payload_type=RawClaims,
        current_time=NOW,clock_skew_seconds=0).mandate_payload.model_dump()
    root={'delegate_payload':[copy.deepcopy(claims)],'_sd_alg':'sha-256'}
    active=[]; omitted=[]
    cnf={'jwk':public(reg['attacker'])}
    if name in {'P01_ROOT_CNF_REVEALED','P02_ROOT_CNF_HIDDEN'}:
        d,h=disclosure('cnf',cnf); root['_sd']=[h]
        (active if name==CASES[0] else omitted).append(d)
    if name in {'P03_EFFECTIVE_CNF_REVEALED','P04_EFFECTIVE_CNF_HIDDEN'}:
        d,h=disclosure('cnf',cnf); root['delegate_payload'][0]['_sd']=[h]
        (active if name==CASES[2] else omitted).append(d)
    if name in {'P05_UNKNOWN_ROOT_FULL','P06_UNKNOWN_ROOT_HIDDEN'}:
        d,h=disclosure('optional_note',{'note':'ordinary root field'})
        root['_sd']=[h]; (active if name==CASES[4] else omitted).append(d)
    if name in {'P07_OPTIONAL_AREA_FULL','P08_OPTIONAL_AREA_HIDDEN'}:
        d,h=disclosure('note',{'label':'synthetic private note','cnf':'ordinary non-authority text'})
        root['optional_data']={'_sd':[h]}; (active if name==CASES[6] else omitted).append(d)
    if name=='P12_UNKNOWN_NESTED_CONDITION':
        d,h=disclosure('future_limit',0); root['delegate_payload'][0]['future_rules']={'_sd':[h]}; omitted.append(d)
    if name=='P13_OPTIONAL_AREA_ITSELF_HIDDEN':
        d,h=disclosure('optional_data',{'note':'cannot assume name before revealing'})
        root['_sd']=[h]; omitted.append(d)
    if name=='P14_SECURITY_DECOY': root['_sd']=[b64(hashlib.sha256(b'h56-no-disclosure-for-security-decoy').digest())]
    header=json.loads(decode(normal['token'].split('.')[0]))
    signed=JWS(wire(root)); signed.add_signature(reg['platform'],protected=json.dumps(header))
    issuer=signed.serialize(compact=True)
    token=issuer+'~'+('~'.join(active)+'~' if active else '')
    full=issuer+'~'+('~'.join(active+omitted)+'~' if active+omitted else '')
    request=json.loads(normal['request_raw']); request['ap2']['checkout_mandate']=token
    trust=copy.deepcopy(normal['trust'])
    if name in {'P09_NO_TRUSTED_PROFILE','P10_REQUEST_PROFILE_ONLY'}: trust.pop('disclosure_profile')
    if name=='P10_REQUEST_PROFILE_ONLY': request['disclosure_profile']={'id':PROFILE,'protocol_version':VERSION,'platform_kid':'h54-platform'}
    if name=='P11_PROFILE_KEY_MISMATCH': trust['disclosure_profile']['platform_kid']='another-platform'
    return {'case':name,'expected':'VERIFIED' if name in ALLOW else 'DENY','request_raw':wire(request),
        'session_raw':normal['session_raw'],'trust':trust,'now':NOW,'token':token,'fully_disclosed_token':full,
        'omitted_disclosures':omitted,'signed_root':root,'public_keys':normal['public_keys']}
def assert_row(row):
    assert row['sdk']['status']=='VALID'
    assert row['response']['status']==row['expected'],row['case']
    result=row['response']
    if row['expected']=='DENY':
        assert not any(k in result for k in ('checkout','checkout_jwt','checkout_hash'))
        assert result['code'] in {'unsupported_profile','mandate_scope_mismatch','invalid_input'}
    else:
        assert result['checkout']==json.loads(decode(row['session_b64']))
        claims=row['sdk']['claims']
        assert result['checkout_jwt']==claims['checkout_jwt'] and result['checkout_hash']==claims['checkout_hash']
        assert result['mandate_sha256']==digest(row['token'].encode())
        assert result['request_sha256']==digest(decode(row['request_b64'])) and result['session_sha256']==digest(decode(row['session_b64']))
        jws=JWS(); jws.deserialize(result['checkout_jwt']); jws.verify(JWK(**row['public_keys']['merchant']))
        assert jws.payload==oracle({k:v for k,v in result['checkout'].items() if k!='ap2'})
def sdk(m):
    key=JWK(**m['public_keys']['platform'])
    root=verify_root(m['token'],key)
    full=verify_root(m['fully_disclosed_token'],key)
    effective=MandateClient().verify(m['token'],key,payload_type=RawClaims,current_time=NOW,clock_skew_seconds=0).mandate_payload.model_dump()
    assert m['token'].split('~')[0]==m['fully_disclosed_token'].split('~')[0]
    if m['case']=='P02_ROOT_CNF_HIDDEN': assert 'cnf' in full and 'cnf' not in root
    if m['case']=='P04_EFFECTIVE_CNF_HIDDEN': assert 'cnf' in full['delegate_payload'][0] and 'cnf' not in effective
    return {'status':'VALID','root':root,'full_root':full,'claims':effective}
def run(role):
    base=TASK/'evidence'/role; base.mkdir(parents=True,exist_ok=True)
    log=base/'PROFILE_ATTEMPTS.jsonl'
    old=[json.loads(l) for l in log.read_text(encoding='utf-8').splitlines()] if log.exists() else []
    assert sum(r['charged'] for r in old)+14<=(112 if role=='executor' else 42)
    folder=base/f'profile_{len(old)+1:04d}'; folder.mkdir()
    with log.open('a',encoding='utf-8') as f: f.write(json.dumps({'run':folder.name,'cases':CASES,'charged':14})+'\n'); f.flush()
    spec=importlib.util.spec_from_file_location('h56_candidate',TASK/'consumer.py')
    candidate=importlib.util.module_from_spec(spec); spec.loader.exec_module(candidate)
    rows=[]
    for name in CASES:
        m=make(name)
        row={k:copy.deepcopy(m[k]) for k in ('case','expected','trust','now','token','fully_disclosed_token','omitted_disclosures','signed_root','public_keys')}
        row.update(request_b64=b64(m['request_raw']),session_b64=b64(m['session_raw']),sdk=sdk(m))
        (folder/(name+'.input.json')).write_text(json.dumps(row,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
        try:
            row['response']=candidate.consume(m['request_raw'],m['session_raw'],m['trust'],NOW)
            assert m['trust']==row['trust']; assert_row(row); row['check']='PASS'
        except Exception as exc: row['check']='FAIL'; row['error']=type(exc).__name__+': '+str(exc)
        (folder/(name+'.output.json')).write_text(json.dumps(row,ensure_ascii=True,indent=2)+'\n',encoding='utf-8'); rows.append(row)
    (folder/'observations.json').write_text(json.dumps({'rows':rows},ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    (base/'PROFILE_LATEST.json').write_text(json.dumps({'run':folder.name})+'\n',encoding='utf-8')
    print(json.dumps({'profile_cases':14,'passed':sum(r['check']=='PASS' for r in rows),'payment_calls':0}))
    return any(r['check']!='PASS' for r in rows)
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--role',required=True,choices=['executor','evaluator']); a=ap.parse_args(); sys.exit(run(a.role))

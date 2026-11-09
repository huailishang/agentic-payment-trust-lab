"""Evaluator preparation only: no consumer, no payment, no task PASS."""
import json
from RUNTIME import TASK, preflight
from FIXTURES import CASE_IDS, NOW, RawClaims, keys, material, digest
from ap2.sdk.mandate import MandateClient
from jwcrypto.jwk import JWK
from jwcrypto.jws import JWS
from JCS_CHECK import check, oracle
from FROZEN_TESTS import selftest

def main():
    preflight(); check(); selftest()
    assert not (TASK/'consumer.py').exists(), 'preparation cannot implement candidate'
    reg=keys(); normal=material('C01_NORMAL',reg)
    verified=MandateClient().verify(normal['token'],JWK(**normal['public_keys']['platform']),
        payload_type=RawClaims,current_time=NOW,clock_skew_seconds=0).mandate_payload.model_dump()
    assert verified['vct']=='mandate.checkout.1'
    assert verified['checkout_jwt']==normal['checkout_jwt']
    jws=JWS(); jws.deserialize(verified['checkout_jwt']); jws.verify(JWK(**normal['public_keys']['merchant']))
    assert oracle(json.loads(jws.payload))==jws.payload
    # All future fixtures can be built, without invoking or creating a consumer.
    shapes=[]
    for case in CASE_IDS:
        m=normal if case=='C01_NORMAL' else material(case,reg)
        shapes.append({'case':case,'expected':m['expected'],'request_sha256':digest(m['request_raw']),
            'session_sha256':digest(m['session_raw']),'mandate_present':bool(m['token'])})
    output={'schema':'h54-preparation/v1','candidate_implemented':False,'candidate_called':False,
        'task_verdict':'NOT_RUN','official_single_checkout_credential':'VERIFIED',
        'merchant_jcs_signature':'VERIFIED','prepared_shapes':shapes,
        'normal_material':{'request_b64':__import__('FIXTURES').b64(normal['request_raw']),
            'session_b64':__import__('FIXTURES').b64(normal['session_raw']),
            'public_keys':normal['public_keys'],'trust':normal['trust'],'now':NOW,
            'verified_claims':verified},'installs':0,'payment_calls':0}
    target=TASK/'evidence/preparation/READINESS.json'
    assert not target.exists()
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(output,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'fixture_shapes':len(shapes),'official_single_token_and_jcs':'READY',
        'candidate_implemented':False,'task_verdict':'NOT_RUN'}))
if __name__=='__main__': main()

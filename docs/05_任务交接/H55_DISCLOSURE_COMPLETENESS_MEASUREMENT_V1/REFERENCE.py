"""Frozen reference checks: signatures, disclosed facts, exact presentation pairs."""
import base64
import hashlib
import json
from RUNTIME import TASK,bootstrap
bootstrap()
from ap2.sdk.mandate import MandateClient
from ap2.sdk.sdjwt.sd_jwt import verify as verify_root
from jwcrypto.jwk import JWK
from pydantic import BaseModel,ConfigDict
class Claims(BaseModel): model_config=ConfigDict(extra='allow')
def decode(s): return base64.urlsafe_b64decode(s+'='*(-len(s)%4))
def cases(): return json.loads((TASK/'FIXED_CASES.json').read_text(encoding='utf-8'))['cases']
def sdk(row):
    try:
        key=JWK(**row['public_keys']['platform'])
        root=verify_root(row['token'],key)
        claims=MandateClient().verify(row['token'],key,payload_type=Claims,current_time=row['now'],clock_skew_seconds=0).mandate_payload.model_dump()
        return {'status':'VALID','root':root,'claims':claims}
    except Exception as exc: return {'status':'REJECTED','error':type(exc).__name__+': '+str(exc)}
def check_pairs():
    rows=cases(); assert len(rows)==6
    for row in rows:
        req=json.loads(decode(row['request_b64']))
        assert req['ap2']['checkout_mandate']==row['token']
        proof=sdk(row); assert proof['status']==row['expected_sdk'],row['case']
        if proof['status']=='VALID': assert ('cnf' in proof['root'])==row['expected_root_cnf']
        if 'fully_disclosed_token' in row:
            full=verify_root(row['fully_disclosed_token'],JWK(**row['public_keys']['platform']))
            assert row['omitted_name'] in full and row['omitted_name'] not in proof['root']
            assert row['fully_disclosed_token'].split('~')[0]==row['token'].split('~')[0]
            fullparts=row['fully_disclosed_token'].split('~'); partial=row['token'].split('~')
            removed=[d for d in fullparts[1:-1] if d not in partial]
            assert len(removed)==1 and json.loads(decode(removed[0]))[1]==row['omitted_name']
    assert rows[0]['token'].split('~')[0]==rows[1]['token'].split('~')[0]
    assert rows[2]['token'].split('~')[0]==rows[3]['token'].split('~')[0]
    print(json.dumps({'fixed_presentations':6,'same_signed_jwt_pairs':2,'consumer_called':False}))
if __name__=='__main__': check_pairs()

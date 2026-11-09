"""Evaluator preparation: verify adversarial fixtures really encode their claims."""
import base64
import json
from RUNTIME import TASK,bootstrap
bootstrap()
from FIXTURES import CASE_IDS,RawClaims,NOW,keys,material
from ap2.sdk.mandate import MandateClient
from jwcrypto.jwk import JWK
from jwcrypto.jws import JWS
from JCS_CHECK import oracle
def decode(s): return base64.urlsafe_b64decode(s+'='*(-len(s)%4))
def main():
    registry=keys(); rows=[]
    sdk_valid_required={'C01_NORMAL','C02_RESERIALIZED','C03_SIGNED_UNKNOWN_FIELDS',
        'C16_NON_JCS_SIGNED_BYTES','C17_WRONG_CHECKOUT_HASH','C18_WRONG_VCT',
        'C19_MISSING_VCT','C20_MISSING_EXP','C21_DELEGATABLE_ROOT',
        'C25_DUPLICATE_SIGNED_JSON','C35_DUPLICATE_JWS_HEADER'}
    for case in CASE_IDS:
        m=material(case,registry); row={'case':case,'candidate_called':False}
        if m['token']:
            try:
                payload=MandateClient().verify(m['token'],JWK(**m['public_keys']['platform']),
                    payload_type=RawClaims,current_time=NOW,clock_skew_seconds=0).mandate_payload.model_dump()
                row['sdk']='VALID'
                if case=='C19_MISSING_VCT': assert 'vct' not in payload
                if case=='C20_MISSING_EXP': assert 'exp' not in payload
                if case=='C21_DELEGATABLE_ROOT': assert 'cnf' in payload
            except Exception as exc:
                row['sdk']='REJECTED'; row['sdk_error']=type(exc).__name__+': '+str(exc)
        else: row['sdk']='NO_TOKEN'
        if case in sdk_valid_required: assert row['sdk']=='VALID',row
        if case in {'C04_EXPIRED','C05_FUTURE_IAT','C06_WRONG_PLATFORM','C34_SIGNATURE_TAMPER'}:
            assert row['sdk']=='REJECTED',row
        if case in {'C16_NON_JCS_SIGNED_BYTES','C25_DUPLICATE_SIGNED_JSON','C35_DUPLICATE_JWS_HEADER'}:
            signed=JWS(); signed.deserialize(m['checkout_jwt']); signed.verify(JWK(**m['public_keys']['merchant']))
            row['merchant_signature']='VALID'
            h,p,_=m['checkout_jwt'].split('.')
            if case=='C16_NON_JCS_SIGNED_BYTES': assert decode(p)!=oracle(json.loads(decode(p)))
            if case=='C25_DUPLICATE_SIGNED_JSON': assert decode(p).count(b'"currency"')==2
            if case=='C35_DUPLICATE_JWS_HEADER': assert decode(h).count(b'"kid"')==2
        if case=='C33_NO_CONSENT_NO_ISSUANCE': assert not m['token'] and not m['consent_receipt']['approved']
        rows.append(row)
    target=TASK/'evidence/preparation/MATERIAL_AUDIT.json'; assert not target.exists()
    target.write_text(json.dumps({'rows':rows,'candidate_called':False,'task_verdict':'NOT_RUN'},ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'material_shapes':len(rows),'signed_adversarial_distinctions':'CONFIRMED',
        'candidate_called':False,'task_verdict':'NOT_RUN'}))
if __name__=='__main__': main()

"""Frozen independent issuer/material generator. Contains no candidate consumer."""
import base64
import copy
import hashlib
import json
from RUNTIME import bootstrap
bootstrap()
from JCS_CHECK import oracle
from ap2.sdk.mandate import MandateClient
from jwcrypto.jwk import JWK
from jwcrypto.jws import JWS
from pydantic import BaseModel, ConfigDict

NOW=1800000000
VERSION='2026-08-25'
class RawClaims(BaseModel):
    model_config=ConfigDict(extra='allow')
def b64(raw): return base64.urlsafe_b64encode(raw).decode().rstrip('=')
def digest(raw): return hashlib.sha256(raw).hexdigest()
def wire(value): return json.dumps(value,ensure_ascii=True,allow_nan=False).encode()
def public(key): return json.loads(key.export_public())
def keys(): return {r:JWK.generate(kty='EC',crv='P-256',kid='h54-'+r) for r in ('platform','merchant','attacker')}
def base_checkout():
    # Complete synthetic checkout fixture for this profile, not a migrated
    # 2026-04-08 merchant response or a claim of full UCP schema certification.
    return {'ucp':{'version':VERSION,'status':'success','capabilities':{
        'dev.ucp.shopping.checkout':[{'version':VERSION}],
        'dev.ucp.common.payment.ap2_mandate':[{'version':VERSION}]},
        'org.example.extra':{'\ue000':'BMP','\U00010000':'astral','n':1e-7}},
        'id':'chk_h54_synthetic_001','status':'ready_for_complete','currency':'USD',
        'line_items':[{'id':'li_1','item':{'id':'rose','title':'Synthetic rose','price':1000},
                       'quantity':1,'totals':[{'type':'total','amount':1000}]}],
        'totals':[{'type':'subtotal','amount':1000},{'type':'total','amount':1000}],
        'links':[],'payment':{'instruments':[]},'discounts':{},
        'fulfillment':{'methods':[{'id':'ship_1','type':'shipping',
            'line_item_ids':['li_1'],'destinations':[{'id':'dest_1','address_country':'US'}],
            'selected_destination_id':'dest_1','groups':[]}]},
        'org.example.unknown':{'label':'e\u0301 / é','array':[3,1,2],'ratio':1e21}}
def sign_checkout(payload,key,*,noncanonical=False,duplicate=False,duplicate_header=False):
    raw=wire(payload) if noncanonical else oracle(payload)
    if duplicate:
        assert raw.startswith(b'{')
        raw=b'{"currency":"EUR",'+raw[1:]
    header=json.dumps({'alg':'ES256','kid':key.get('kid')})
    if duplicate_header: header='{"alg":"ES256","kid":"ignored","kid":"'+key.get('kid')+'"}'
    jws=JWS(raw); jws.add_signature(key,protected=header)
    return jws.serialize(compact=True)
def detached(compact):
    h,_,s=compact.split('.')
    return h+'..'+s
def issue(compact,registry,*,receipt=True,overrides=None,issuer='platform'):
    chash=b64(hashlib.sha256(compact.encode()).digest())
    # Synthetic deterministic consent is issuer-side fixture state. The merchant
    # sees a platform signature, never a caller-supplied consent=true authority.
    consent={'source':'SYNTHETIC_DETERMINISTIC_CHANNEL','checkout_hash':chash,'approved':receipt}
    if not consent['approved']: return None,consent
    claims={'vct':'mandate.checkout.1','checkout_jwt':compact,'checkout_hash':chash,'iat':NOW,'exp':NOW+600}
    if overrides:
        for k,v in overrides.items():
            if v is None: claims.pop(k,None)
            else: claims[k]=v
    return MandateClient().create([RawClaims(**claims)],registry[issuer]),consent
def context(registry):
    return {'ap2_required':True,'protocol_version':VERSION,'platform_id':'h54-synthetic-platform',
        'platform_profile':{'keys':[public(registry['platform'])]},
        'merchant_profile':{'keys':[public(registry['merchant'])]}}

CASE_IDS=[
 'C01_NORMAL','C02_RESERIALIZED','C03_SIGNED_UNKNOWN_FIELDS',
 'C04_EXPIRED','C05_FUTURE_IAT','C06_WRONG_PLATFORM','C07_WRONG_MERCHANT',
 'C08_MISSING_MANDATE','C09_DOWNGRADE_REQUEST','C10_TOTAL_CHANGED',
 'C11_CURRENCY_CHANGED','C12_ITEM_CHANGED','C13_SESSION_ID_CHANGED',
 'C14_UNKNOWN_FIELD_REMOVED','C15_UNSIGNED_UNKNOWN_MUTATION','C16_NON_JCS_SIGNED_BYTES',
 'C17_WRONG_CHECKOUT_HASH','C18_WRONG_VCT','C19_MISSING_VCT','C20_MISSING_EXP',
 'C21_DELEGATABLE_ROOT','C22_MULTI_HOP','C23_TRAILING_KB',
 'C24_MERCHANT_ALG_TAMPER','C25_DUPLICATE_SIGNED_JSON','C26_DUPLICATE_REQUEST_JSON',
 'C27_LONE_SURROGATE','C28_NONFINITE_JSON','C29_EXTRA_AP2_FIELD',
 'C30_SELF_ASSERTED_REQUEST_KEY','C31_MISSING_TRUST','C32_UNSUPPORTED_VERSION',
 'C33_NO_CONSENT_NO_ISSUANCE','C34_SIGNATURE_TAMPER','C35_DUPLICATE_JWS_HEADER',
 'C36_MISSING_MERCHANT_AUTHORIZATION']
VALID=set(CASE_IDS[:3])

def material(case,registry):
    assert case in CASE_IDS
    payload=base_checkout()
    if case=='C03_SIGNED_UNKNOWN_FIELDS':
        payload['ucp']['another.protocol']={'\r':0,'😀':[-0.0,333333333.3333333]}
        payload['org.example.unknown']['additional']={'z':None,'a':True}
    compact=sign_checkout(payload,registry['attacker' if case=='C07_WRONG_MERCHANT' else 'merchant'],
        noncanonical=case=='C16_NON_JCS_SIGNED_BYTES',duplicate=case=='C25_DUPLICATE_SIGNED_JSON',
        duplicate_header=case=='C35_DUPLICATE_JWS_HEADER')
    if case=='C15_UNSIGNED_UNKNOWN_MUTATION':
        h,_,s=compact.split('.'); altered=copy.deepcopy(payload)
        altered['org.example.unknown']['label']='unsigned mutation'
        compact=h+'.'+b64(oracle(altered))+'.'+s
    if case=='C24_MERCHANT_ALG_TAMPER':
        _,p,s=compact.split('.'); compact=b64(wire({'alg':'none','kid':'h54-merchant'}))+'.'+p+'.'+s
    session=copy.deepcopy(payload)
    session['ap2']={'merchant_authorization':detached(compact)}
    override={}
    if case=='C04_EXPIRED': override={'iat':NOW-1000,'exp':NOW-1}
    if case=='C05_FUTURE_IAT': override={'iat':NOW+100}
    if case=='C17_WRONG_CHECKOUT_HASH': override={'checkout_hash':'incorrect'}
    if case=='C18_WRONG_VCT': override={'vct':'mandate.payment.1'}
    if case=='C19_MISSING_VCT': override={'vct':None}
    if case=='C20_MISSING_EXP': override={'exp':None}
    if case=='C21_DELEGATABLE_ROOT': override={'cnf':{'jwk':public(registry['attacker'])}}
    token,receipt=issue(compact,registry,receipt=case!='C33_NO_CONSENT_NO_ISSUANCE',
        overrides=override,issuer='attacker' if case in {'C06_WRONG_PLATFORM','C30_SELF_ASSERTED_REQUEST_KEY'} else 'platform')
    if case=='C22_MULTI_HOP': token=token.rstrip('~')+'~~'+token
    if case=='C23_TRAILING_KB': token=token+'e30.e30.AA'
    if case=='C34_SIGNATURE_TAMPER':
        jwt,*rest=token.split('~'); h,p,s=jwt.split('.')
        token='.'.join([h,p,('A' if s[0]!='A' else 'B')+s[1:]])+'~'+'~'.join(rest)
    request={'payment':{'instruments':[{'id':'instr_h54','handler_id':'opaque_psp',
        'type':'card','credential':{'type':'PAYMENT_GATEWAY','token':'OPAQUE_NOT_VERIFIED_OR_USED'}}]},
        'ap2':{'checkout_mandate':token}}
    if case in {'C08_MISSING_MANDATE','C09_DOWNGRADE_REQUEST','C33_NO_CONSENT_NO_ISSUANCE'}:
        request['ap2'].pop('checkout_mandate')
    if case=='C09_DOWNGRADE_REQUEST': request['ap2_required']=False; request['ucp']={'capabilities':{}}
    if case=='C10_TOTAL_CHANGED': session['totals'][-1]['amount']=2000
    if case=='C11_CURRENCY_CHANGED': session['currency']='EUR'
    if case=='C12_ITEM_CHANGED': session['line_items'][0]['quantity']=2
    if case=='C13_SESSION_ID_CHANGED': session['id']='another_session'
    if case=='C14_UNKNOWN_FIELD_REMOVED': session.pop('org.example.unknown')
    if case=='C29_EXTRA_AP2_FIELD': session['ap2']['future']='must not be silently lost'
    if case=='C36_MISSING_MERCHANT_AUTHORIZATION': session['ap2'].pop('merchant_authorization')
    trust=context(registry)
    if case=='C30_SELF_ASSERTED_REQUEST_KEY': request['platform_profile']={'keys':[public(registry['attacker'])]}; request['consent']=True
    if case=='C31_MISSING_TRUST': trust={}
    if case=='C32_UNSUPPORTED_VERSION': trust['protocol_version']='2026-04-08'
    request_raw=wire(request); session_raw=wire(session)
    if case=='C02_RESERIALIZED':
        session_raw=json.dumps(dict(reversed(list(session.items()))),indent=3,ensure_ascii=False).encode()
        request_raw=json.dumps(request,indent=2).encode()
    if case=='C26_DUPLICATE_REQUEST_JSON':
        request_raw=b'{"ap2":{},'+request_raw[1:]
    if case=='C27_LONE_SURROGATE': session['bad']='\ud800'; session_raw=wire(session)
    if case=='C28_NONFINITE_JSON': session_raw=b'{"bad":NaN,'+session_raw[1:]
    return {'case':case,'request_raw':request_raw,'session_raw':session_raw,'trust':trust,
        'now':NOW,'checkout_jwt':compact,'token':token,'consent_receipt':receipt,
        'public_keys':{r:public(k) for r,k in registry.items()},'expected':'VERIFIED' if case in VALID else 'DENY'}

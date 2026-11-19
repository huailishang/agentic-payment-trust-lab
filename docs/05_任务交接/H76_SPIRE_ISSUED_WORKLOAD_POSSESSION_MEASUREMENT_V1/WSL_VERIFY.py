"""Independent re-evaluation of public WSL real-SPIRE artifacts with original verifier.
Does not call SPIRE, generate certificates, re-sign, or change original source/tests.
"""
from __future__ import annotations
import base64, hashlib, json, sys
from datetime import timezone
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
P=Path(__file__).resolve().parent
REPO=P.parents[2]
sys.path.insert(0,str(REPO/"src"))
from agentic_payment_experiment.trusted_execution.credential_possession import verify_x509_svid_credential_possession

def need(b,msg):
    if not b:raise AssertionError(msg)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    rootdir=P/"evidence"/"wsl_experiment"
    candidates=[d for d in rootdir.iterdir() if d.is_dir() and (d/"RESULT.json").exists() and json.loads((d/"RESULT.json").read_text()).get("status")=="ISSUER_FETCH_SIGNATURE_CAPTURED"]
    need(len(candidates)==1,"expected exactly one successful actual WSL run")
    d=candidates[0]
    state=json.loads((d/"RESULT.json").read_text())
    leaf_data=(d/"leaf.pem").read_bytes();root_data=(d/"root.pem").read_bytes()
    payload=(d/"payload.bin").read_bytes()
    sig=base64.b64decode((d/"signature.b64").read_bytes().strip(),validate=True)
    leafs=x509.load_pem_x509_certificates(leaf_data)
    roots=x509.load_pem_x509_certificates(root_data)
    need(len(leafs)==len(roots)==1,"direct root+leaf only, no intermediates")
    leaf,root=leafs[0],roots[0]
    need(root.subject==root.issuer and leaf.issuer==root.subject,"fresh direct root chain")
    need(isinstance(root.public_key(),ec.EllipticCurvePublicKey) and isinstance(leaf.public_key(),ec.EllipticCurvePublicKey),"EC root and leaf")
    root.public_key().verify(root.signature,root.tbs_certificate_bytes,ec.ECDSA(root.signature_hash_algorithm))
    root.public_key().verify(leaf.signature,leaf.tbs_certificate_bytes,ec.ECDSA(leaf.signature_hash_algorithm))
    leaf.public_key().verify(sig,payload,ec.ECDSA(hashes.SHA256()))
    need(root.extensions.get_extension_for_class(x509.BasicConstraints).value.ca,"root ca")
    need(not leaf.extensions.get_extension_for_class(x509.BasicConstraints).value.ca,"leaf not ca")
    ku=leaf.extensions.get_extension_for_class(x509.KeyUsage).value
    need(ku.digital_signature and not ku.key_cert_sign and not ku.crl_sign,"leaf key usage")
    san=leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.UniformResourceIdentifier)
    need(san==["spiffe://h76.test/agent/h76-agent/executor/h76-executor"],"real SAN")
    observed=state["issued_at_epoch"]+1
    nonce=state["nonce"]
    expected=(f"agentic-payment-possession/v1\nnonce={nonce}\nagent=h76-agent\nprovider=h76-provider\nexecutor=h76-executor\nissued_at={state['issued_at_epoch']}\n").encode()
    need(payload==expected,"canonical payload")
    denied=state["unmatched_uid"]
    need(denied["uid"]==1002 and denied["exit_code"]!=0 and denied["identity_count"]==0 and denied["reject_reason_code_permission_denied"] is True and denied["socket_connected"] is True,"actual mismatched selector rejection")
    need(state["tmpfs_removed"] and state["spire_processes_terminated"] and state["signing_uid"]==1001 and "SIGNING_UID=1001" in state["holder_signing_stdout"],"signer identity/cleanup")
    base=dict(leaf_svid_pem=leaf_data,trusted_ca_pem=root_data,expected_trust_domain="h76.test",
              expected_agent_ref="h76-agent",expected_provider_ref="h76-provider",
              expected_executor_instance_ref="h76-executor",credential_ref="h76:wsl:"+d.name,
              challenge_payload=payload,challenge_signature=sig,nonce_ref=nonce,
              issued_at_epoch=state["issued_at_epoch"],observed_at_epoch=observed,max_age_seconds=300)
    valid=verify_x509_svid_credential_possession(**base)
    need(valid.status.name=="VALID","original verifier actual POSITIVE: "+repr(valid))
    need(all((valid.credential_valid,valid.subject_binding_valid,valid.proof_of_possession_valid,valid.freshness_valid)) and not valid.replay_detected,"original positive four fields")
    vector=json.loads((REPO/"docs/05_任务交接/P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1/evaluator_fixtures/X509_SVID_POSSESSION_VECTOR.json").read_text())
    def at_utc(cert,part):
        d=getattr(cert,part+"_utc",None)
        if d is not None:return int(d.timestamp())
        return int(getattr(cert,part).replace(tzinfo=timezone.utc).timestamp())
    stale=state["issued_at_epoch"]+301
    expire=at_utc(leaf,"not_valid_after")+1
    need(at_utc(leaf,"not_valid_before")<=stale<=at_utc(leaf,"not_valid_after"),"stale isolates freshness")
    need(at_utc(root,"not_valid_before")<=expire<=at_utc(root,"not_valid_after"),"expiry isolates leaf")
    variants={
       "wrong_root":{"trusted_ca_pem":vector["untrusted_ca_pem"]},
       "wrong_trust_domain":{"expected_trust_domain":"wrong.h76.test"},
       "wrong_agent":{"expected_agent_ref":"wrong-agent"},
       "wrong_executor":{"expected_executor_instance_ref":"wrong-executor"},
       "wrong_provider":{"expected_provider_ref":"wrong-provider"},
       "wrong_nonce_binding":{"nonce_ref":"different-nonce"},
       "damaged_signature":{"challenge_signature":b"damaged-signature"},
       "nonce_replay":{"consumed_nonce_refs":(nonce,)},
       "stale_challenge":{"observed_at_epoch":stale},
       "expired_leaf_observation":{"observed_at_epoch":expire}
    }
    oracles=json.loads((P/"NEGATIVE_ORACLES.json").read_text())["cases"]
    negative={}
    for name,override in variants.items():
        result=verify_x509_svid_credential_possession(**{**base,**override})
        negative[name]={"status":result.status.name,"reasons":list(result.reason_codes),
                        "expected_reason":oracles[name],"expected_reason_present":oracles[name] in result.reason_codes}
        need(result.status.name!="VALID" and negative[name]["expected_reason_present"],"negative "+name+" "+repr(negative[name]))
    pub={"schema":"h76-wsl-public-verification/v1",
         "run_id":d.name, "source":"actual_spire_1.16.0_via_wsl",
         "root_sha256":sha(d/"root.pem"),"root_der_sha256":root.fingerprint(hashes.SHA256()).hex(),
         "leaf_sha256":sha(d/"leaf.pem"),"payload_sha256":sha(d/"payload.bin"),
         "signature_sha256":sha(d/"signature.b64"),
         "original_verifier_status":valid.status.name, "status_reasons":list(valid.reason_codes),
         "credential_valid":valid.credential_valid,"subject_binding_valid":valid.subject_binding_valid,
         "proof_of_possession_valid":valid.proof_of_possession_valid,"freshness_valid":valid.freshness_valid,
         "replay_detected":valid.replay_detected,
         "root_direct_signer_verified":True,"ecdsa_signature_verified":True,"subject_uri":san[0],
         "uid1001_private_signer":True,"uid1002_actual_permission_denied":True,
         "negative_count":len(negative),"negative_valid_count":sum(x["status"]=="VALID" for x in negative.values()),
         "negative_results":negative,"tmpfs_removed":True,"spire_processes_terminated":True,
         "not_docker_h76_l2":True,"original_product_code_modified":False}
    (d/"WSL_VERIFICATION.json").write_text(json.dumps(pub,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"VALID","run_id":d.name,"real_positive":True,"negative_count":len(negative),
                      "negative_valid_count":0,"uid1002_denied":True,"original_verifier":"VALID","cleanup":True},ensure_ascii=False))

if __name__=="__main__":main()

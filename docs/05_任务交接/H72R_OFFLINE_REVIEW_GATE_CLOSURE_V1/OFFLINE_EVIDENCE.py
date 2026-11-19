"""H72R immutable offline evidence: existing 13 Evaluator GET responses, SQLite and raw webhooks.
No network/API, no new services, no change to frozen H72 evidence.
"""
from __future__ import annotations
from datetime import datetime,timedelta
from pathlib import Path
from urllib.parse import quote
import hashlib,hmac,json,sqlite3,sys

P=Path(__file__).resolve().parent
ROOT=P.parents[2]
OLD=ROOT/"docs/05_任务交接/H72_LOCAL_CLOSEOUT_AND_STRIPE_JOURNEY_V1"
sys.path.insert(0,str(ROOT/"src"))
from agentic_payment_experiment.adapters.stripe_checkout import verify_webhook,StripeCheckoutError

class EvidenceError(ValueError):pass
def need(ok,code):
    if not ok:raise EvidenceError(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(path):
    need(path.is_file(),"missing_evidence:"+path.name)
    return json.loads(path.read_text(encoding="utf-8"))
def private_dir():
    private=Path(load(OLD/"evidence/p1/PRIVATE_REF.json")["path"]).resolve()
    need(private.is_dir() and not private.is_relative_to(ROOT),"private_location")
    return private
def table(db,name):
    need(name in ("operations","webhook_receipts","delivery_attempts","recoveries"),"table_scope")
    return [dict(x) for x in db.execute("SELECT * FROM "+name+" ORDER BY rowid")]
def verify():
    private=private_dir()
    parent=load(OLD/"evidence/l3_readback/EVALUATOR_READBACK.json")
    prior=load(OLD/"evidence/l3_review_20261115/INDEPENDENT.json")
    need(parent["read_only_get_count"]==13 and parent["result"]=="PASS" and
         prior["formal_l3_result"]=="FAIL","parent_evaluator_provenance")
    raw_dir=private/"evaluator_readonly_20261115"
    files=sorted(raw_dir.glob("get_*.private.json"))
    need(len(files)==13 and [f.name for f in files]==["get_%03d.private.json"%i for i in range(1,14)],
         "independent_13_original_get_files")
    docs=[load(f) for f in files]
    groups={}
    for pos,kind,qty in ((0,"checkout.session",4),(1,"payment_intent",3),(2,"charge",3)):
        li=docs[pos]
        need(li.get("object")=="list" and li.get("has_more") is False and
             len(li.get("data",[]))==qty and all(x["object"]==kind for x in li["data"]),
             "provider_list_incomplete:"+kind)
        independent={x["id"]:x for x in docs[3:] if x.get("object")==kind}
        need(len(independent)==qty and set(independent)=={x["id"] for x in li["data"]},
             "provider_original_get_linkage:"+kind)
        need(all(x.get("livemode") is False for x in independent.values()),
             "provider_not_test_mode")
        groups[kind]=independent
    sessions=groups["checkout.session"];intents=groups["payment_intent"];charges=groups["charge"]
    db_file=private/"merchant.sqlite3"
    conn=sqlite3.connect("file:"+quote(db_file.as_posix(),safe="/:")+"?mode=ro",uri=True)
    conn.row_factory=sqlite3.Row
    try:
        ops=table(conn,"operations")
        webhooks=table(conn,"webhook_receipts")
        deliveries=table(conn,"delivery_attempts")
        recoveries=table(conn,"recoveries")
    finally:conn.close()
    need(len(ops)==4 and len({x["operation_id"] for x in ops})==4,"four_distinct_operations")
    bycase={x["case_id"]:x for x in ops}
    need(set(bycase)=={"N01","C01","R01","D01"},"case_set")
    resource_sha=sha((OLD/"RESOURCE.txt").read_bytes())
    joined=[]
    for case in ("N01","C01","R01","D01"):
        op=bycase[case]
        session=sessions.get(op["session_id"])
        need(session is not None,"original_session_missing:"+case)
        m=session.get("metadata",{})
        need(session.get("client_reference_id")==op["order_id"] and
             m.get("h68_run_id")==op["run_id"] and
             m.get("h68_operation_id")==op["operation_id"] and
             m.get("h68_resource_sha256")==op["resource_sha256"]==resource_sha and
             op["amount_minor"]==session.get("amount_total")==100 and
             op["currency"]==session.get("currency")=="usd" and
             session.get("mode")=="payment" and
             all(op.get(k) for k in ("request_id","payment_id","order_id","operation_id")),
             "operation_amount_resource_binding:"+case)
        attempts=[x for x in deliveries if x["operation_id"]==op["operation_id"]]
        if case=="C01":
            need(session["status"]=="expired" and session["payment_status"]=="unpaid" and
                 op["state"]=="CANCELLED" and not session.get("payment_intent") and
                 not attempts,"cancel_paid_or_delivered")
        else:
            need(session["status"]=="complete" and session["payment_status"]=="paid" and
                 op["state"]=="PAID_CONFIRMED","payment_not_verified:"+case)
            intent=intents.get(session.get("payment_intent"))
            need(intent is not None and intent["status"]=="succeeded" and
                 intent["currency"]=="usd" and intent["amount"]==100,"intent_mismatch:"+case)
            charge=charges.get(intent.get("latest_charge"))
            need(charge is not None and charge["paid"] is True and charge["captured"] is True and
                 charge["payment_intent"]==intent["id"] and charge["amount"]==100 and
                 op["intent_id"]==intent["id"] and op["charge_id"]==charge["id"],
                 "charge_original_linkage:"+case)
            won=[x for x in attempts if x["state"]=="SUCCEEDED"]
            need(len(won)==1 and won[0]["actual_sha256"]==resource_sha and
                 bool(won[0]["receipt_ref"]),"delivery_not_unique:"+case)
            if case=="D01":
                need([x["state"] for x in attempts]==["FAILED","SUCCEEDED"] and
                     attempts[0]["receipt_ref"] is None,"D01_fault_injection")
            else:need(len(attempts)==1,"duplicate_delivery:"+case)
        joined.append({"case":case,"provider_original_session_hash":sha(op["session_id"].encode()),
                       "payment_status":session["payment_status"],"merchant_state":op["state"],
                       "binding_verified":True})
    need(len(recoveries)==1 and
         recoveries[0]["operation_id"]==bycase["R01"]["operation_id"] and
         recoveries[0]["initial_status"]=="UNKNOWN" and
         recoveries[0]["observed_status"]=="SUCCEEDED" and
         recoveries[0]["recovery_status"]=="RECOVERED" and
         recoveries[0]["retry_allowed"]==0,"R01_not_original_recovery")
    secret=(private/"webhook_secret_resume.txt").read_text(encoding="utf-8").strip()
    need(secret.startswith("wh"+"sec_"),"test_notification_secret_missing")
    need(len(webhooks)==3,"signed_event_count")
    notifications={}
    for case in ("N01","R01","D01"):
        op=bycase[case]
        match=[x for x in webhooks if x["operation_id"]==op["operation_id"]]
        need(len(match)==1,"case_event_count:"+case)
        record=match[0];eid=record["event_id"]
        raw=(private/"events"/("event_"+eid+".bin")).read_bytes()
        meta=load(private/"events"/("event_"+eid+".receipt.json"))
        stamp=datetime.fromisoformat(meta["received_at_utc"])
        event=json.loads(raw)
        need(event["id"]==eid and event["type"]=="checkout.session.completed" and
             event["data"]["object"]["id"]==op["session_id"] and
             sha(raw)==record["payload_sha256"],"original_event_binding:"+case)
        sig={part.split("=",1)[0]:part.split("=",1)[1] for part in meta["header"].split(",") if "=" in part}
        t=int(sig["t"])
        need(abs(stamp.timestamp()-t)<=300,"signature_timestamp:"+case)
        expected=hmac.new(secret.encode(),str(t).encode()+b"."+raw,hashlib.sha256).hexdigest()
        need(hmac.compare_digest(expected,sig["v1"]),"independent_signature:"+case)
        need(verify_webhook(raw,meta["header"],secret,stamp)["id"]==eid,"product_signature:"+case)
        negatives={}
        for kind in ("tamper","wrong_secret","expired"):
            modified=raw+b"X" if kind=="tamper" else raw
            key="invalid_test_signature_secret" if kind=="wrong_secret" else secret
            when=stamp+timedelta(seconds=1200) if kind=="expired" else stamp
            try:verify_webhook(modified,meta["header"],key,when)
            except (ValueError,TypeError,StripeCheckoutError):negatives[kind]="REJECTED"
            else:negatives[kind]="UNSAFE_ACCEPTED"
        need(all(x=="REJECTED" for x in negatives.values()),"negative_signature_not_rejected:"+case)
        notifications[case]={"original_signed_bytes_sha256":sha(raw),"negative":negatives}
    replay=load(private/"event_check_D01_replay.private.json")
    need(replay["body_sha256"]==notifications["D01"]["original_signed_bytes_sha256"] and
         replay["new_delivery_event"] is False,"D01_replayed_event_duplicate")
    return {"status":"PASS","source":"EXISTING_EVALUATOR_13_SAVED_READS_NO_NEW_GET",
            "provider_sessions":4,"provider_payment_intents":3,"provider_charges":3,
            "original_case_joins":joined,"synthetic_usd_minor":300,"real_money_minor":0,
            "sqlite_opened_read_only":True,"signed_original_events":3,
            "hmac_negative_rejections":9,"notifications":notifications,
            "R01_recovered_original_without_repay":True,
            "D01_scope":"DELIVERY_RECORD_AND_RECEIPT_RECOVERY; HTTP_TRANSFER_RETRY_NOT_MEASURED",
            "parent_h72_final_l3":"FAIL","new_external_requests":0}
if __name__=="__main__":print(json.dumps(verify(),ensure_ascii=True,indent=2))

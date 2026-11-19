"""Synthetic counterexamples for the frozen evidence checker, never live evidence."""
import base64
import copy
from datetime import datetime, timezone
import hashlib
import hmac


def run(validate, failure, digest, canonical, pack, task):
    clock = 1794355200
    secret = "synthetic-checker-key-not-a-provider-credential"
    resource = digest((pack/"RESOURCE.txt").read_bytes())
    def iso(offset):
        return datetime.fromtimestamp(clock+offset,timezone.utc).isoformat()
    result = {"schema":"h68-stripe-result/v1","task_id":task,"run_id":"h68-selftest-only","decision":"EXTERNAL_JOURNEY_MEASURED","security_control_increment":"NOT_MEASURED","started_at":iso(0),"finished_at":iso(120),"cases":[]}
    provider = {"schema":"h68-stripe-provider/v1","run_id":result["run_id"],"account":{"id":"acct_synthetic"},"cases":{},"lists":{}}
    for cid in ("N01","C01","R01","D01"):
        paid = cid != "C01"
        sid, iid, chid = "cs_test_"+cid, "pi_"+cid, "ch_"+cid
        order, operation = "order-"+cid, "operation-"+cid
        session = {"id":sid,"object":"checkout.session","created":clock+5,"livemode":False,"mode":"payment","amount_total":100,"currency":"usd","client_reference_id":order,"metadata":{"h68_run_id":result["run_id"],"h68_operation_id":operation,"h68_resource_sha256":resource},"payment_status":"paid" if paid else "unpaid","status":"complete" if paid else "expired","payment_intent":iid if paid else None}
        intent = {"id":iid,"object":"payment_intent","created":clock+10,"livemode":False,"status":"succeeded","amount":100,"currency":"usd","latest_charge":chid} if paid else None
        charge = {"id":chid,"object":"charge","created":clock+11,"livemode":False,"status":"succeeded","amount":100,"currency":"usd","paid":True,"captured":True,"payment_intent":iid} if paid else None
        events = []
        if paid:
            body = canonical({"id":"evt_"+cid,"type":"checkout.session.completed","livemode":False,"data":{"object":{"id":sid}}})
            signature = hmac.new(secret.encode(),str(clock+15).encode()+b"."+body,hashlib.sha256).hexdigest()
            events = [{"body_b64":base64.b64encode(body).decode(),"signature":"t="+str(clock+15)+",v1="+signature,"received_at":iso(16)}]
        provider["cases"][cid] = {"session":session,"intent":intent,"charge":charge,"events":events,"line_items":{"object":"list","has_more":False,"data":[{"quantity":1,"amount_total":100,"currency":"usd"}]}}
        if paid:
            provider["cases"][cid]["merchant_response_body_b64"] = base64.b64encode((pack/"RESOURCE.txt").read_bytes()).decode()
        gate = {"final_decision":"ALLOW","callback_executed":True,"callback_count":1,"binding_status":"VALID","identity_status":"VALID","context_policy_status":"VALID"}
        kinds = ["order_authorized","create_gate_allow","session_created"]
        if paid:
            kinds += ["prepay_query_valid","submit_gate_allow","payment_submitted"]
            if cid == "R01":
                kinds += ["local_unknown","local_process_restarted","original_payment_queried"]
            kinds += ["provider_paid_query"]
            if cid == "D01":
                kinds += ["delivery_failed","delivery_retried"]
            kinds += ["delivered"]
            if cid == "D01": kinds += ["duplicate_event_consumed"]
        else:
            kinds += ["buyer_cancelled","provider_unpaid_query"]
        deliveries = []
        if cid == "D01": deliveries.append({"status":"FAILED"})
        if paid: deliveries.append({"status":"SUCCEEDED","resource_sha256":resource,"receipt_ref":"receipt-"+cid})
        case = {"case_id":cid,"operation_id":operation,"order_id":order,"session_ref":digest(sid),"intent_ref":digest(iid) if paid else None,"charge_ref":digest(chid) if paid else None,"account_ref":digest("acct_synthetic"),"resource_sha256":resource,"create_gate":copy.deepcopy(gate),"submit_gate":copy.deepcopy(gate) if paid else None,"timeline":[{"seq":n+1,"kind":kind,"at":iso(n+1)} for n,kind in enumerate(kinds)],"fulfillment_attempts":deliveries}
        if cid == "R01": case["recovery_result"]={"retry_allowed":False,"recovery_status":"RECOVERED"}
        result["cases"].append(case)
    for name,key in (("sessions","session"),("intents","intent"),("charges","charge")):
        provider["lists"][name] = {"object":"list","has_more":False,"data":[copy.deepcopy(source[key]) for source in provider["cases"].values() if source[key] is not None]}
    validate(result,provider,secret,resource)
    # A canceled checkout may still have an unpaid PaymentIntent.
    optional = copy.deepcopy(provider)
    canceled = {"id":"pi_C01","created":clock+6,"object":"payment_intent","livemode":False,"status":"canceled","amount":100,"currency":"usd","latest_charge":None}
    optional["cases"]["C01"]["intent"] = canceled
    optional["cases"]["C01"]["session"]["payment_intent"] = canceled["id"]
    optional["lists"]["intents"]["data"].append(canceled)
    optional_result = copy.deepcopy(result)
    optional_result["cases"][1]["intent_ref"] = digest(canceled["id"])
    validate(optional_result,optional,secret,resource)
    def mutation(label, change):
        altered_result, altered_provider = copy.deepcopy(result),copy.deepcopy(provider)
        change(altered_result,altered_provider)
        try:
            validate(altered_result,altered_provider,secret,resource)
        except failure:
            return
        raise failure("checker_missed_mutation:"+label)
    mutation("wrong_amount",lambda r,p:p["cases"]["N01"]["session"].update(amount_total=101))
    mutation("live_mode",lambda r,p:p["cases"]["N01"]["charge"].update(livemode=True))
    mutation("foreign_intent",lambda r,p:p["cases"]["N01"]["session"].update(payment_intent="pi_foreign"))
    mutation("unpaid_as_paid",lambda r,p:p["cases"]["N01"]["session"].update(payment_status="unpaid"))
    mutation("missing_gate",lambda r,p:r["cases"][0].update(create_gate=None))
    mutation("duplicate_callback",lambda r,p:r["cases"][0]["submit_gate"].update(callback_count=2))
    mutation("second_payment",lambda r,p:p["lists"]["charges"]["data"].append({"id":"ch_second"}))
    mutation("missing_page",lambda r,p:p["lists"]["sessions"].update(has_more=True))
    mutation("duplicate_delivery",lambda r,p:r["cases"][0]["fulfillment_attempts"].append(copy.deepcopy(r["cases"][0]["fulfillment_attempts"][0])))
    mutation("wrong_download_bytes",lambda r,p:p["cases"]["N01"].update(merchant_response_body_b64=base64.b64encode(b"wrong content").decode()))
    mutation("skip_unknown",lambda r,p:r["cases"][2].update(timeline=[e for e in r["cases"][2]["timeline"] if e["kind"]!="local_unknown"]))
    mutation("bad_signature",lambda r,p:p["cases"]["N01"]["events"][0].update(signature="t="+str(clock+15)+",v1="+"0"*64))
    mutation("expired_notification",lambda r,p:p["cases"]["N01"]["events"][0].update(received_at=iso(999)))
    mutation("old_payment",lambda r,p:p["cases"]["N01"]["charge"].update(created=clock-999))
    mutation("duplicate_business_order",lambda r,p:r["cases"][0].update(order_id=r["cases"][2]["order_id"]))
    print("H68 checker selftest: 2 synthetic controls and 15 corruptions passed; no product/live evidence")

"""Independent H74 probes: original fixture only, own assertions and fake client."""
from dataclasses import fields, is_dataclass, replace
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
OUT = P / ("evidence/l3_review/holdout" if "current_role: Evaluator" in (ROOT/"CURRENT.md").read_text(encoding="utf-8") else "evidence/holdout")
OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/"src"))
from agentic_payment_experiment.adapters.stripe_checkout import StripeCheckoutAdapter, StripeCheckoutError
from agentic_payment_experiment.stripe_checkout_lab import StripeLabLedger
from agentic_payment_experiment.models import PaymentStatus, PaymentStatusObservation
from agentic_payment_experiment.trusted_execution.confirmation import ConfirmationStatus

def graph(value):
    if isinstance(value,Enum): return {"type":type(value).__module__+"."+type(value).__qualname__,"enum":value.value}
    if is_dataclass(value): return {"type":type(value).__module__+"."+type(value).__qualname__,"fields":{f.name:graph(getattr(value,f.name)) for f in fields(value)}}
    if isinstance(value,datetime): return {"datetime":value.isoformat()}
    if isinstance(value,Decimal): return {"decimal":str(value)}
    if isinstance(value,dict): return {k:graph(v) for k,v in sorted(value.items())}
    if isinstance(value,(tuple,list,frozenset)):
        items=[graph(v) for v in value]
        if isinstance(value,frozenset): items.sort(key=lambda v:json.dumps(v,sort_keys=True))
        return {"type":type(value).__name__,"items":items}
    return value
def digest(value): return hashlib.sha256(json.dumps(graph(value),sort_keys=True,separators=(",",":")).encode()).hexdigest()
def check(ok, reason):
    if not ok: raise AssertionError(reason)

class Client:
    def __init__(self, store, reference): self.store,self.reference,self.created,self.queries,self.clicked,self.native=store,reference,0,0,0,None
    def create_session(self,payload,*,idempotency_key):
        # This load happens inside the callback: persistence must already exist.
        self.store.load_authority("op-l3",expected_sha256=self.reference)
        self.created+=1
        self.native={"id":"cs_test_l3", "url":"https://checkout.stripe.com/c/pay/l3", "livemode":False,"mode":"payment","currency":"usd","amount_total":100,"payment_status":"unpaid","status":"open","client_reference_id":payload["client_reference_id"],"metadata":{"h68_run_id":payload["metadata[h68_run_id]"],"h68_operation_id":payload["metadata[h68_operation_id]"],"h68_resource_sha256":payload["metadata[h68_resource_sha256]"]}}
        return dict(self.native)
    def get_session(self,session_id):
        check(session_id==self.native["id"],"native session replaced")
        self.queries+=1
        return dict(self.native)
    def browser(self,url): self.clicked+=1
    def counts(self): return [self.created,self.queries,self.clicked]

class Fixture:
    def __init__(self):
        from tests.test_stripe_checkout_adapter import valid_context,NOW
        self.now=NOW
        self.ctx=valid_context()
        self.ctx=replace(self.ctx,order=replace(self.ctx.order,quote_expires_at=NOW+timedelta(minutes=17)))
        self.resource=b"independent H74 L3 resource"
        self.resource_sha=hashlib.sha256(self.resource).hexdigest()
        self.temp=tempfile.TemporaryDirectory(prefix="independent-",dir=OUT)
        self.db=Path(self.temp.name)/"merchant.sqlite3"
        self.store=StripeLabLedger(self.db)
        self.store.register(operation_id="op-l3",run_id="run-l3",case_id="N01",order_id=self.ctx.order.order_id,request_id=self.ctx.request.request_id,payment_id=self.ctx.execution.payment_id,resource_sha256=self.resource_sha)
        self.ref=None;self.client=None;self.adapter=None
    def record(self,ctx=None,when=None):
        return self.store.record_authority("op-l3",ctx or self.ctx,resource_sha256=self.resource_sha,recorded_at=when or self.now)
    def ready(self):
        self.ref=self.record(); self.client=Client(self.store,self.ref);self.adapter=StripeCheckoutAdapter(self.client)
    def create(self,**kw):
        return self.adapter.create_stored_session(self.store,operation_id=kw.get("operation_id","op-l3"),expected_authority_sha256=kw.get("reference",self.ref),success_url="http://127.0.0.1:8768/success",cancel_url="http://127.0.0.1:8768/cancel",now=kw.get("now",self.now))
    def pay(self,**kw):
        return self.adapter.authorize_stored_browser_payment(self.store,operation_id=kw.get("operation_id","op-l3"),expected_authority_sha256=kw.get("reference",self.ref),now=kw.get("now",self.now),browser_payment=self.client.browser)
    def bind(self): self.store.bind_session("op-l3",self.client.native)
    def paid(self):
        native=dict(self.client.native,status="complete",payment_status="paid",payment_intent="pi_l3")
        intent={"id":"pi_l3","livemode":False,"status":"succeeded","latest_charge":"ch_l3","amount":100,"currency":"usd"}
        charge={"id":"ch_l3","livemode":False,"status":"succeeded","paid":True,"captured":True,"amount":100,"currency":"usd","payment_intent":"pi_l3"}
        self.store.observe("op-l3",native,intent,charge)
    def close(self): self.temp.cleanup()

def blocked(call,client):
    before=client.counts()
    try: result=call()
    except StripeCheckoutError: result=None
    else:
        gate=result.gate if hasattr(result,"gate") else result
        check(gate.callback_executed is False,"guard allowed callback")
    check(client.counts()==before,"denied action touched fake provider/browser")

def cold_and_consume(f):
    f.ready()
    child=subprocess.run([sys.executable,"-B",str(Path(__file__).resolve()),"cold",str(f.db),f.ref],capture_output=True,env=os.environ.copy())
    check(child.returncode==0,"cold child failed")
    observed=json.loads(child.stdout)
    check(observed["graph"]==digest(f.ctx),"cold typed graph changed")
    f.create(); f.bind(); f.pay()
    check(f.client.counts()==[1,1,1],"stored consumers not exactly one")
    return {"cold_graph":observed["graph"],"effects":f.client.counts()}
def references(f):
    f.ready()
    blocked(lambda:f.create(reference="0"*64),f.client)
    blocked(lambda:f.create(operation_id="missing"),f.client)
    f.create();f.bind()
    blocked(lambda:f.pay(reference="0"*64),f.client)
    blocked(lambda:f.pay(operation_id="missing"),f.client)
    with closing(sqlite3.connect(f.db)) as con:
        payload=con.execute("SELECT payload_json FROM authority_contexts").fetchone()[0]
        check("synthetic-payee" in payload,"tamper target absent")
        con.execute("UPDATE authority_contexts SET payload_json=?",(payload.replace("synthetic-payee","other-payee"),));con.commit()
    blocked(f.create,f.client);blocked(f.pay,f.client)
    return {"denial_variants":6,"effects_after_denials":f.client.counts()}
def temporal(f):
    for c in (replace(f.ctx.confirmation_record,confirmed_at=f.now+timedelta(seconds=1)),replace(f.ctx.confirmation_record,expires_at=f.now-timedelta(seconds=1)),replace(f.ctx.confirmation_record,status=ConfirmationStatus.REVOKED)):
        try:f.record(replace(f.ctx,confirmation_record=c))
        except StripeCheckoutError:pass
        else:raise AssertionError("invalid confirmation persisted")
    f.ready()
    blocked(lambda:f.create(now=f.now+timedelta(hours=2)),f.client)
    f.create();f.bind()
    blocked(lambda:f.pay(now=f.now+timedelta(hours=2)),f.client)
    check(digest(f.store.load_authority("op-l3",expected_sha256=f.ref))==digest(f.ctx),"clock refreshed original")
    return {"invalid_recordings":3,"expired_entries_blocked":2}
def altered_original(f):
    variants=[replace(f.ctx,order=replace(f.ctx.order,order_version="v99")),replace(f.ctx,request=replace(f.ctx.request,amount=Decimal("2.00"))),replace(f.ctx,order=replace(f.ctx.order,payee="other"))]
    for ctx in variants:
        try:f.record(ctx)
        except StripeCheckoutError:pass
        else:raise AssertionError("mismatched original persisted")
    f.ready()
    try:f.store.record_authority("op-l3",f.ctx,resource_sha256="f"*64,recorded_at=f.now)
    except StripeCheckoutError:pass
    else:raise AssertionError("wrong resource accepted")
    return {"mismatched_variants_rejected":4}
def recovery(f):
    f.ready();f.create();f.bind();f.store.mark_unknown("op-l3");f.paid()
    restored=StripeLabLedger(f.db).load_authority("op-l3",expected_sha256=f.ref)
    payment=replace(restored.execution,status=PaymentStatus.UNKNOWN,provider_ref=f.client.native["id"])
    observation=PaymentStatusObservation(payment.payment_id,payment.order_id,PaymentStatus.SUCCEEDED,f.now+timedelta(hours=3),"stripe_api",provider_ref=payment.provider_ref)
    outcome=StripeLabLedger(f.db).recover_original("op-l3",payment,observation)
    check(not outcome.retry_allowed and outcome.recovery_status.value=="RECOVERED","paid recovery changed semantics")
    blocked(lambda:f.pay(now=f.now+timedelta(hours=3)),f.client)
    check(f.client.counts()==[1,0,0],"recovery made new payment")
    return {"recovery":"RECOVERED","effects":f.client.counts()}
def delivery(f):
    f.ready();f.create();f.bind();f.paid()
    check(f.store.record_client_delivery("op-l3",f.resource,inject_failure=True) is None,"fault not recorded")
    receipt=StripeLabLedger(f.db).record_client_delivery("op-l3",f.resource)
    check(StripeLabLedger(f.db).record_client_delivery("op-l3",f.resource)==receipt,"receipt replay changed result")
    check([row["state"] for row in f.store.delivery_history("op-l3")]==["FAILED","SUCCEEDED"],"duplicate successful delivery")
    check(f.client.counts()==[1,0,0],"delivery recovery paid again")
    return {"receipt_stable":True,"effects":f.client.counts()}
def cancel(f):
    f.ready();f.create();f.bind()
    f.store.observe("op-l3",dict(f.client.native,status="expired",payment_status="unpaid"),None,None)
    blocked(f.create,f.client);blocked(f.pay,f.client)
    return {"effects":f.client.counts(),"state":f.store.get("op-l3")["state"]}
def record_retry(f):
    first=f.record()
    check(f.record()==first,"identical retry changed digest")
    try:second=f.record(when=f.now+timedelta(seconds=1))
    except StripeCheckoutError as exc:
        raise AssertionError("same original GateContext at next valid recording time rejected: "+str(exc))
    check(second==first,"same original fact received a new reference")
    return {"different_retry_time_same_original":True}
def foreign_enum(f):
    Foreign=Enum("PaymentStatus",{"PENDING":PaymentStatus.PENDING.value})
    changed=replace(f.ctx,execution=replace(f.ctx.execution,status=Foreign.PENDING))
    try:ref=f.record(changed)
    except StripeCheckoutError:return {"unknown_enum_rejected":True}
    loaded=f.store.load_authority("op-l3",expected_sha256=ref)
    check(type(loaded.execution.status) is type(changed.execution.status),"foreign same-name enum silently became native PaymentStatus; full original graph not preserved")
    return {"typed_graph_equal":digest(changed)==digest(loaded)}
def foreign_codec(f):
    from agentic_payment_experiment.stripe_authority_context import serialize_authority
    status=Enum("PaymentStatus",{"PENDING":PaymentStatus.PENDING.value})
    decision=Enum("Decision",{"ALLOW":"ALLOW"})
    for ctx in (replace(f.ctx,execution=replace(f.ctx.execution,status=status.PENDING)),replace(f.ctx,prepayment_decision=decision.ALLOW)):
        try:serialize_authority("op-l3",ctx,resource_sha256=f.resource_sha,recorded_at=f.now,run_id="run-l3")
        except StripeCheckoutError:pass
        else:raise AssertionError("unregistered same-name enum accepted by closed codec")
    return {"unregistered_enum_codec_variants_rejected":2}

def main():
    if len(sys.argv)>1 and sys.argv[1]=="cold":
        ctx=StripeLabLedger(sys.argv[2]).load_authority("op-l3",expected_sha256=sys.argv[3])
        print(json.dumps({"graph":digest(ctx)}));return
    results=[]
    for name,func in (("cold_actual_consumers",cold_and_consume),("references_and_payload",references),("original_times",temporal),("original_binding",altered_original),("paid_read_only_recovery",recovery),("receipt_recovery",delivery),("cancel_no_payment",cancel),("same_fact_retry_time",record_retry),("closed_enum_type_identity",foreign_enum),("closed_enum_codec_variants",foreign_codec)):
        f=Fixture()
        try:record={"probe":name,"status":"PASS","observed":func(f)}
        except (AssertionError,Exception) as exc:record={"probe":name,"status":"FAIL","error_type":type(exc).__name__,"reason":str(exc)}
        finally:f.close()
        results.append(record);print(json.dumps(record,ensure_ascii=False))
    (OUT/"INDEPENDENT_PROBES.json").write_text(json.dumps({"probes":results,"originals_modified":False,"external_actions":0},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if any(r["status"]=="FAIL" for r in results):sys.exit(1)
if __name__=="__main__":main()

"""H72 independent Evaluator only: bounded native Stripe TEST GET readback.

This program is NOT executed by the Executor. Frozen VP-13 evaluator_command
invokes it under Evaluator role after report freeze and L2. API credentials
are taken only from this H72's private sandbox directory; no writes to Stripe,
no payment, no login, no browser access. All 13 potential GETs use reserved
Evaluator budget (max20) and are recorded before network dispatch.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,subprocess,sys,urllib.error,urllib.request
from datetime import datetime,timezone
from pathlib import Path
PACK=Path(__file__).resolve().parent
ROOT=PACK.parents[2]
LEDGER=PACK/"RESOURCE_LEDGER.jsonl"
OUT=PACK/"evidence/l3_readback/EVALUATOR_READBACK.json"
API_VERSION="2026-10-28.endive"
def now():return datetime.now(timezone.utc).isoformat()
def sha(x):return hashlib.sha256(x).hexdigest()
def need(ok,why):
 if not ok:raise RuntimeError(why)
def load(path):return json.loads(path.read_text(encoding="utf-8"))
def reserve():
 rows=[json.loads(x) for x in LEDGER.read_text(encoding="utf-8").splitlines() if x.strip()]
 need([r.get("seq") for r in rows]==list(range(1,len(rows)+1)),"resource sequence")
 used=sum(r.get("counts",{}).get("api_evaluator_read",0) for r in rows)
 need(used<20,"Evaluator independent read budget consumed")
 with LEDGER.open("a",encoding="utf-8",newline="\n") as out:
  out.write(json.dumps({"seq":len(rows)+1,"at":now(),"kind":"evaluator_independent_stripe_get",
    "counts":{"api_evaluator_read":1}},ensure_ascii=False,separators=(",",":"))+"\n")
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
def get(path,key,private):
 need(re.fullmatch(r"/v1/(checkout/sessions|payment_intents|charges)(?:/[A-Za-z0-9_]+)?",path),
      "GET path outside frozen read-only scope")
 reserve()
 request=urllib.request.Request("https://api.stripe.com"+path,method="GET",headers={
  "Authorization":"Bearer "+key,"Stripe-Version":API_VERSION,
  "User-Agent":"H72-Independent-Evaluator-ReadOnly/1"})
 try:
  with urllib.request.build_opener(NoRedirect()).open(request,timeout=30) as response:
   need(response.status==200,"Stripe independent GET status not 200")
   raw=response.read(2*1024*1024+1)
  need(len(raw)<=2*1024*1024,"independent provider response size")
 except Exception:
  raise RuntimeError("INDEPENDENT_PROVIDER_GET_FAILED_"+path.split("/")[2]) from None
 document=json.loads(raw)
 serial=sum(x.is_file() for x in private.glob("get_*.private.json"))
 output=private/("get_%03d.private.json"%(serial+1))
 need(not output.exists(),"independent read evidence already exists")
 output.write_bytes(raw)
 return document
def run():
 text=(ROOT/"CURRENT.md").read_text(encoding="utf-8")
 need("current_role: Evaluator" in text and "state: READY_FOR_REVIEW" in text,
      "Executor cannot spend independent Evaluator readback budget")
 need(not OUT.exists(),"independent evaluation already captured")
 l2=load(PACK/"evidence/l2_attempt_001/L2-GATE.json")
 need(l2.get("result")=="PASS" and l2.get("mode")=="executor" and
      l2.get("task_id")==PACK.name,"L2 PASS required")
 private=Path(load(PACK/"evidence/p1/PRIVATE_REF.json")["path"]).resolve()
 need(private.is_dir() and not private.is_relative_to(ROOT),"credentials outside repo required")
 credentials=load(private/"CREDENTIALS.json")
 key=credentials["key"]
 need(key.startswith("rkcs_test_"),"only H72 test restricted key")
 data_dir=private/"evaluator_readonly_20261115"
 need(not data_dir.exists(),"independent evaluator output must be fresh")
 data_dir.mkdir()
 groups={}
 for group,endpoint in (("sessions","/v1/checkout/sessions"),
                        ("intents","/v1/payment_intents"),("charges","/v1/charges")):
  collection=get(endpoint,key,data_dir)
  need(collection.get("object")=="list" and
       collection.get("has_more") is False,"provider pagination incomplete")
  values=collection["data"]
  need(isinstance(values,list),"provider collection payload invalid")
  groups[group]=values
 need([len(groups[x]) for x in ("sessions","intents","charges")]==[4,3,3],
      "provider independent count mismatch")
 observed={"sessions":[],"intents":[],"charges":[]}
 for category,base in (("sessions","/v1/checkout/sessions/"),
                       ("intents","/v1/payment_intents/"),
                       ("charges","/v1/charges/")):
  for row in groups[category]:
   iid=row["id"]
   item=get(base+iid,key,data_dir)
   need(item.get("id")==iid and item.get("livemode") is False,"provider object not same test reference")
   observed[category].append(item)
 session_index={s["id"]:s for s in observed["sessions"]}
 pi_index={p["id"]:p for p in observed["intents"]}
 charge_index={c["id"]:c for c in observed["charges"]}
 paid=[s for s in session_index.values() if s.get("payment_status")=="paid"]
 cancel=[s for s in session_index.values() if s.get("status")=="expired" and s.get("payment_status")=="unpaid"]
 need(len(paid)==3 and len(cancel)==1,"independent paid/cancel mismatch")
 for session in paid:
  pi=pi_index.get(session.get("payment_intent"))
  need(pi is not None and pi.get("status")=="succeeded" and pi.get("amount")==100,
       "independent payment intent mismatch")
  charge=charge_index.get(pi.get("latest_charge"))
  need(charge is not None and charge.get("payment_intent")==pi["id"] and
       charge.get("paid") is True and charge.get("captured") is True and charge.get("amount")==100,
       "independent charge mismatch")
 summary={
   "schema":"h72-evaluator-real-provider-readback/v1","task_id":PACK.name,
   "role":"Evaluator","at_utc":now(),"result":"PASS",
   "provider_sessions":len(session_index),"provider_payment_intents":len(pi_index),
   "provider_charges":len(charge_index),"paid":len(paid),"unpaid_expired":len(cancel),
   "read_only_get_count":13,"private_provider_response_dir_sha256":
      sha(str(data_dir).encode()),"all_provider_livemode_false":True
 }
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return summary
if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--role",choices=("evaluator",),required=True)
 parser.add_argument("--read-only",action="store_true",required=True)
 args=parser.parse_args()
 try:print(json.dumps(run(),ensure_ascii=False,indent=2))
 except Exception as exc:
  print("EVALUATOR_READ_ONLY_FAILED:"+str(exc),file=sys.stderr)
  raise SystemExit(1)

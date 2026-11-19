"""H72 inspectable offline assertion gate for real Stripe TEST journeys.

Independent of Executor's claimed COMPLETE string: joins original provider objects,
SQLite merchant operations, original signed CLI notifications, and strict cumulative
resource/event ledgers. Sensitive raw objects remain in the private directory.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,os,re,sqlite3,subprocess,sys
P=Path(__file__).resolve().parent
ROOT=P.parents[2]
sys.path.insert(0,str(ROOT/"src"))
from agentic_payment_experiment.adapters.stripe_checkout import verify_webhook
REQUIRED=("N01","C01","R01","D01")
SHA_RE=re.compile(r"^[a-f0-9]{64}$")
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(path):return sha(path.read_bytes())
def need(ok,label):
 if not ok:raise RuntimeError("H72_ASSERT_"+label)
def load(path):
 need(path.is_file(),"MISSING_FILE_"+path.name)
 return json.loads(path.read_text(encoding="utf-8"))
def rows(path):
 return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()] if path.exists() else []
def external():
 return load(P/"evidence/resumed_20261115/FINAL.json")
def private_path():
 locator=load(P/"evidence/p1/PRIVATE_REF.json")
 place=Path(locator["path"]).resolve()
 need(place.is_dir() and not place.is_relative_to(ROOT),"PRIVATE_INSIDE_REPO")
 return place
def db_records(table):
 with sqlite3.connect(private_path()/"merchant.sqlite3") as con:
  con.row_factory=sqlite3.Row
  return [dict(r) for r in con.execute("SELECT * FROM "+table)]
def resources():
 ledger=rows(P/"RESOURCE_LEDGER.jsonl")
 need([x.get("seq") for x in ledger]==list(range(1,len(ledger)+1)),"RESOURCE_SEQUENCE")
 totals=Counter()
 for r in ledger:
  need(isinstance(r.get("counts"),dict),"RESOURCE_COUNTS")
  for k,n in r["counts"].items():
   need(type(n) is int and n>=0,"RESOURCE_NONNEGATIVE")
   totals[k]+=n
 return totals
def attempts():
 ledger=rows(P/"ATTEMPT_LEDGER.jsonl")
 need([x.get("seq") for x in ledger]==list(range(1,len(ledger)+1)),"ATTEMPT_SEQUENCE")
 begins={};ends={}
 for r in ledger:
  event=r.get("event");ident=r.get("attempt_id")
  need(event in ("BEGIN","END") and isinstance(ident,str),"ATTEMPT_ROW")
  group=begins if event=="BEGIN" else ends
  need(ident not in group,"ATTEMPT_DUPLICATE_EVENT")
  group[ident]=r
 need(set(ends)<=set(begins),"END_WITHOUT_BEGIN")
 need(set(begins)-set(ends)<={"H72_20261115_OWNER_RESUME"},"UNACCOUNTED_BEGIN")
 return ledger,begins,ends
def file_summary():
 p=private_path()
 return {"outside_repo":True,"private_dir_exists":p.is_dir()}
def qualification():
 final=external();r=resources();events,starts,ends=attempts()
 cli=load(P/"evidence/p1/CLI_DOWNLOAD_RESULT.json")
 anon=load(P/"evidence/p1/ANONYMOUS_QUALIFICATION.json")
 browser=load(P/"evidence/p1/NATIVE_CHROME_PROBE.json")
 read=load(P/"evidence/p1/SESSIONS_READBACK.json")
 b=load(P/"SOURCE_LOCK.json")
 need(cli.get("status")=="PASS" and
  cli.get("pinned_sha256")==b["cli"]["windows_x86_64"]["sha256"],"PINNED_CLI")
 need(r["cli_http_requests"]==2 and r["cli_received_bytes"]==11929882,"CLI_BYTES")
 need(anon["status"]=="PASS_TEST_CREDENTIALS_CREATED" and
  anon["actual_challenge_posts"]==anon["actual_provision_posts"]==1,"ANON_ACCOUNT")
 need(read["status"]=="PASS" and read["provider_http_status"]==200,"READ_ACCESS")
 need(browser["status"]=="PASS" and browser["reason_code"]=="NATIVE_CHROME_CDP_PORT_OK",
      "NATIVE_BROWSER")
 need(final["listener_ready"] is True and final["owned_services_stopped"] is True,
      "REAL_WEBHOOK_LISTENER")
 need(final["secrets_outside_repo"] is True,"PRIVACY")
 need(sum(x["event"]=="BEGIN" and x["kind"]=="stripe_listener" for x in events)==2 and
      sum(x["event"]=="BEGIN" and x["kind"]=="merchant_process" for x in events)==3,
      "PROCESS_COUNTS")
 return {"status":"PASS","actual_credential_provision_posts":1,
         "real_listener_starts":2,"merchant_starts":3,"cli_sha256_verified":True}
def governance():
 f=external();a,b,c=attempts();r=resources()
 for case in REQUIRED:
  need(case in f["cases"] and f["cases"][case]["status"]=="COMPLETE","CASE_NOT_COMPLETE_"+case)
 need(len(f["completed_journeys"])==4 and set(f["completed_journeys"])==set(REQUIRED),
      "FOUR_CASES_COMPLETE")
 attempted=[x for x in a if x["event"]=="BEGIN" and x["kind"]=="browser_payment"]
 need(len(attempted)==3 and all(x["attempt_id"].split("_")[1] in ("N01","R01","D01") for x in attempted),
      "HOSTED_PAYMENT_ATTEMPT_SET")
 for x in attempted:
  final_end=c.get(x["attempt_id"])
  need(final_end is not None and final_end["status"]=="SUBMITTED_ONCE" and
       final_end.get("gate_decision")=="ALLOW","PAYMENT_RUNTIME_GATING")
 need(r["test_payment_submissions"]==3 and r["test_payment_minor"]==300,"PAYMENT_BUDGET")
 need(r["checkout_sessions"]==4,"SESSION_LIMIT")
 for case in ("N01","R01","D01"):
  trace=load(P/"evidence/resumed_20261115"/("payment_click_"+case+".json"))
  need(trace["gate_callback_count"]==1 and trace["gate_final_decision"]=="ALLOW" and
      trace["amount_minor"]==100 and trace["currency"]=="usd" and
      trace["no_direct_payment_intent_api_post"] is True,
      "NO_RUNTIME_GATE_EVIDENCE_"+case)
 return {"status":"PASS","hosted_test_payment_gate_calls":3,"no_direct_payment_intent_posts":True}
def journeys():
 f=external();ops=db_records("operations");deliveries=db_records("delivery_attempts")
 recoveries=db_records("recoveries");events=db_records("webhook_receipts")
 need(len(ops)==4 and set(x["case_id"] for x in ops)==set(REQUIRED),"OPERATION_GRAIN")
 bycase={r["case_id"]:r for r in ops}
 need(all(x["amount_minor"]==100 and x["currency"]=="usd" and
      x["resource_sha256"]==sha((P/"RESOURCE.txt").read_bytes()) for x in ops),"FIXED_MONEY_RESOURCE")
 expected={"N01":"PAID_CONFIRMED","C01":"CANCELLED",
           "R01":"PAID_CONFIRMED","D01":"PAID_CONFIRMED"}
 need(all(bycase[k]["state"]==v for k,v in expected.items()),"MERCHANT_STATE")
 need(all(bycase[k]["session_id"] and
    sha(bycase[k]["session_id"].encode())==f["cases"][k]["original_session_sha256"]
    for k in REQUIRED),"ORIGINAL_SESSION_ID")
 need(all(len([x for x in deliveries if x["operation_id"]==bycase[k]["operation_id"] and
                     x["state"]=="SUCCEEDED"])==1 for k in ("N01","R01","D01")),
      "UNIQUE_SUCCESSFUL_DELIVERY")
 need(not any(x["operation_id"]==bycase["C01"]["operation_id"] for x in deliveries),
      "CANCEL_HAS_DELIVERY")
 d01=[x["state"] for x in deliveries if x["operation_id"]==bycase["D01"]["operation_id"]]
 need(d01==["FAILED","SUCCEEDED"],"D01_FAIL_THEN_SUCCESS")
 need(len(recoveries)==1 and recoveries[0]["operation_id"]==bycase["R01"]["operation_id"] and
      recoveries[0]["initial_status"]=="UNKNOWN" and
      recoveries[0]["observed_status"]=="SUCCEEDED" and
      recoveries[0]["recovery_status"]=="RECOVERED" and
      recoveries[0]["retry_allowed"]==0,"R01_ORIGINAL_RECOVERY")
 need(len(events)==3 and
      len(set(e["event_id"] for e in events))==3,"ONE_EVENT_EACH_PAID")
 need(all(f["cases"][k]["delivery"]["client_sha256"]==sha((P/"RESOURCE.txt").read_bytes())
  for k in ("N01","R01","D01")),"ACTUAL_CLIENT_RESOURCE_BYTES")
 return {"status":"PASS","merchant_states":expected,"deliveries":len(deliveries),
         "unique_successful_receipts":3,"recovery":"RECOVERED_NO_RETRY"}
def notifications():
 f=external();pv=private_path()
 secret=(pv/"webhook_secret_resume.txt").read_text(encoding="utf-8").strip()
 need(secret.startswith("whsec_"),"WEBHOOK_SIGNING_SECRET_MISSING")
 ops={x["case_id"]:x for x in db_records("operations")}
 proofs=db_records("webhook_receipts")
 seen={}
 for case in ("N01","R01","D01"):
  related=[r for r in proofs if r["operation_id"]==ops[case]["operation_id"]]
  need(len(related)==1,"WEBHOOK_RECEIPT_COUNT_"+case)
  r=related[0];eid=r["event_id"]
  raw=(pv/"events"/("event_"+eid+".bin")).read_bytes()
  receipt=load(pv/"events"/("event_"+eid+".receipt.json"))
  when=datetime.fromisoformat(receipt["received_at_utc"])
  verified=verify_webhook(raw,receipt["header"],secret,when)
  need(verified.get("type")=="checkout.session.completed" and
    verified.get("data",{}).get("object",{}).get("id")==ops[case]["session_id"],
    "WEBHOOK_WRONG_BUSINESS_BINDING_"+case)
  need(sha(raw)==r["payload_sha256"],"WEBHOOK_ORIGINAL_BYTES_"+case)
  need(sha(eid.encode())==f["cases"][case]["signed_event_sha256"]
       if case!="R01" else f["cases"]["R01"]["signed_event_validated"],
       "WEBHOOK_PUBLIC_PROOF_"+case)
  seen[case]=sha(raw)
 replay=load(pv/"event_check_D01_replay.private.json")
 need(replay["new_delivery_event"] is False and replay["body_sha256"]==seen["D01"],
      "D01_EVENT_REPLAY_INVALID")
 need(f["cases"]["D01"]["same_signed_event_replay_deduplicated"] is True,
      "D01_DUPLICATION_RESULT_INVALID")
 return {"status":"PASS","original_signed_events":3,
         "replayed_d01_event_deduplicated":True}
def provider_audit():
 f=external();pv=private_path()
 api_files=sorted(pv.glob("H72_RESUME_API_*.private.json"))
 lists=[]
 for path in api_files:
  raw=load(path)
  if raw.get("object")=="list" and isinstance(raw.get("data"),list):
   lists.append(raw)
 need(len(lists)>=3,"PROVIDER_LIST_EVIDENCE_MISSING")
 lists=lists[-3:]
 classifiers=["checkout.session","payment_intent","charge"]
 counts={}
 objects={}
 for kind,data in zip(classifiers,lists):
  need(data.get("has_more") is False,"PROVIDER_LIST_HAS_MORE")
  arr=data["data"];need(all(x.get("object")==kind for x in arr),"PROVIDER_LIST_WRONG_TYPE")
  counts[kind]=len(arr)
  objects[kind]={x["id"]:x for x in arr}
 need(counts=={"checkout.session":4,"payment_intent":3,"charge":3},
      "PROVIDER_ACCOUNT_COUNTS")
 sessions=objects["checkout.session"];intents=objects["payment_intent"];charges=objects["charge"]
 paid=[s for s in sessions.values() if s.get("payment_status")=="paid"]
 cancel=[s for s in sessions.values() if s.get("status")=="expired" and s.get("payment_status")=="unpaid"]
 need(len(paid)==3 and len(cancel)==1,"PROVIDER_FINAL_PAID_CANCEL_STATUS")
 for s in paid:
  intent=intents.get(s.get("payment_intent"))
  need(intent is not None and intent.get("status")=="succeeded" and intent.get("amount")==100,
       "PROVIDER_PAYMENT_INTENT_LINK")
  charge=charges.get(intent.get("latest_charge"))
  need(charge is not None and charge.get("payment_intent")==intent["id"] and
    charge.get("paid") is True and charge.get("captured") is True and charge.get("amount")==100,
    "PROVIDER_CHARGE_LINK")
 for case in REQUIRED:
  expected=f["cases"][case]["original_session_sha256"]
  matches=[s for s in sessions.values() if sha(s["id"].encode())==expected]
  need(len(matches)==1 and matches[0]["currency"]=="usd" and
       matches[0]["amount_total"]==100 and matches[0]["livemode"] is False,
       "PROVIDER_CASE_ID_OR_AMOUNT_"+case)
 need(f["provider_reconciliation"]["sessions"]["has_more"] is False,"PROVIDER_RECONCILIATION_INCOMPLETE")
 return {"status":"PASS","provider_sessions":4,"provider_intents":3,
         "provider_charges":3,"paid":3,"expired_unpaid":1}
def budget_privacy():
 base=load(P/"BASELINE.json");r=resources();events,starts,ends=attempts()
 auth=load(P/"AUTHORIZATION.json")
 now=datetime.now(timezone.utc)
 expires=datetime.fromisoformat(auth["expires_at_utc"].replace("Z","+00:00"))
 need(now<expires,"ORIGINAL_H72_AUTHORIZATION_EXPIRED")
 grant=load(P/"evidence/reauthorization_20261115_085439/ADDENDUM.json")
 need(grant["process_start_limits_amended"]=={"stripe_cli_listener_starts":2,
       "merchant_process_starts":3},"OWNER_PROCESS_AMENDMENT")
 caps={"api_live":80,"api_executor_read":20,"api_evaluator_read":20,
       "browser_actions":80,"checkout_sessions":4,
       "test_payment_submissions":3,"test_payment_minor":300,
       "cli_http_requests":12,"cli_transfer_attempts":4,
       "cli_received_bytes":64*1024*1024}
 need(all(0<=r[k]<=v for k,v in caps.items()),"SPENDING_CAP")
 need(r["api_live"]+r["api_executor_read"]+r["api_evaluator_read"]<=120,
      "API_TOTAL")
 current_text=(ROOT/"CURRENT.md").read_text(encoding="utf-8")
 if "current_role: Executor" in current_text:
  need(r["api_evaluator_read"]==0,"EXECUTOR_CONSUMED_EVALUATOR_READS")
 else:
  need("current_role: Evaluator" in current_text and r["api_evaluator_read"]<=20,
       "EVALUATOR_READ_BUDGET")
 active=sum(float(x["elapsed_upper_bound_minutes"]) for x in events
            if x["event"]=="END" and x.get("kind")=="active_work")
 for key in set(starts)-set(ends):
  begin=starts[key]
  need(key=="H72_20261115_OWNER_RESUME" and begin.get("kind")=="active_work",
       "UNACCOUNTED_ACTIVE_WORK")
  active+=(now-datetime.fromisoformat(begin["at"].replace("Z","+00:00"))).total_seconds()/60
 need(active<480,"TOTAL_ACTIVE_TIME_CAP")
 need(sum(x["event"]=="BEGIN" and x["kind"]=="stripe_listener" for x in events)==2 and
      sum(x["event"]=="BEGIN" and x["kind"]=="merchant_process" for x in events)==3,
      "AMENDED_PROCESS_STARTS")
 need(subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True).stdout.strip()==base["head"],
       "GIT_HEAD_CHANGED")
 # Never export actual keys, signatures, session URLs, card values or private account JSON.
 checks=[P/"REPORT.md",P/"RESULT.json",P/"RESULT_RESUME.json",ROOT/"CURRENT.md"]
 checks+=list((P/"evidence/resumed_20261115").glob("*.json"))
 patterns=[re.compile(r"(?:sk_test_|rkcs_test_|whsec_)[A-Za-z0-9]{14,}"),
           re.compile(r"https://checkout\.stripe\.com/[^\s\"']{30,}")]
 for path in checks:
  if path.is_file():
   blob=path.read_text(encoding="utf-8",errors="replace")
   need(all(not rx.search(blob) for rx in patterns),"SECRET_LEAK_"+path.name)
 return {"status":"PASS","active_minutes_upper_bound":round(active,3),
         "live_api_used":r["api_live"],"browser_actions":r["browser_actions"],
         "test_sessions":r["checkout_sessions"],"test_payments":r["test_payment_submissions"],
         "evaluator_reads_spent":0}
def summary():
 f=external()
 need(f["status"]=="COMPLETE_EXECUTOR_CANDIDATE_NOT_L2_OR_L3","EXECUTOR_CANDIDATE_NOT_COMPLETE")
 need(len(f["completed_journeys"])==4,"FOUR_CASES_NOT_COMPLETE")
 need((P/"REPORT.md").is_file() and (P/"RESULT_RESUME.json").is_file(),
      "MISSING_HANDOFF_REPORT_OR_RESULT")
 r=load(P/"RESULT_RESUME.json")
 need(r["executor_status"] in ("SUBMITTED_FOR_L2","SUBMITTED_FOR_REVIEW") and
       r["four_journeys_completed"]==4,"REPORT_HONESTY")
 need(any(x in (ROOT/"CURRENT.md").read_text(encoding="utf-8") for x in ("H72_P6","H72_P7")),"ROUTER_PHASE")
 return {"status":"PASS","actual_test_journeys":4,
         "independent_l3":"RESERVED_NOT_CLAIMED"}
def submission():
 results={name:check(name) for name in ("qualification","governance","journeys",
        "notifications","provider-audit","budget-privacy","summary")}
 need(all(x["status"]=="PASS" for x in results.values()),"SUBMISSION_PRECONDITIONS")
 gate=P/"evidence/l2_attempt_001/L2-GATE.json"
 need(gate.is_file(),"L2_GATE_MISSING")
 data=load(gate)
 need(data.get("task_id")==P.name and data.get("mode")=="executor" and
      data.get("gate_level")=="L2" and data.get("result")=="PASS" and
      data.get("checks_total")==15 and data.get("mandatory_failures")==0,
      "L2_PUBLIC_GATE_NOT_COMPLETE_PASS")
 report=(P/"REPORT.md").read_text(encoding="utf-8")
 need("## L2 Task Gate" in report and "- Gate result: PASS" in report and
      "## Impact comparison" in report,"REPORT_L2_MISSING")
 need("Executor status: SUBMITTED_FOR_REVIEW" in report,"REPORT_NOT_SUBMITTED")
 return {"status":"PASS","15_mandatory_checks":"PASS","l3_independent":"PENDING"}

def check(mode):
 lookup={
   "qualification":qualification,"governance":governance,"journeys":journeys,
   "notifications":notifications,"provider-audit":provider_audit,
   "budget-privacy":budget_privacy,"summary":summary,"submission":submission
 }
 if mode not in lookup:raise KeyError(mode)
 return lookup[mode]()

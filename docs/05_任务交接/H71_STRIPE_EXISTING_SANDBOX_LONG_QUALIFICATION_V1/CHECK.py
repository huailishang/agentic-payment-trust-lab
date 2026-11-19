"""H71 frozen evaluator checks. Only actor readback can issue three bounded GETs."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
H69 = PACK.parent/"H69_STRIPE_ANONYMOUS_SANDBOX_QUALIFICATION_V1"

def need(ok, code):
    if not ok:
        raise ValueError(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def unique(pairs):
    out = {}
    for k,v in pairs:
        need(k not in out,"duplicate_json_key")
        out[k] = v
    return out

def load(path):
    need(path.is_file() and path.stat().st_size <= 4*1024*1024,"json_file")
    result=json.loads(path.read_text(encoding="utf-8"),object_pairs_hook=unique)
    need(isinstance(result,dict),"json_object")
    return result

def stamp(value):
    value = datetime.fromisoformat(value.replace("Z","+00:00"))
    need(value.tzinfo is not None,"timezone")
    return value

def spec():
    return load(PACK/"SPEC.json")

def rows():
    p = PACK/"ATTEMPT_LEDGER.jsonl"
    return [json.loads(x,object_pairs_hook=unique) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []

def private_root(name):
    value = os.environ.get(name)
    need(value,"private_material_unavailable")
    p = Path(value).resolve()
    need(p.is_dir() and not p.is_relative_to(ROOT),"private_location")
    return p

def private_file(root,rel,limit=2*1024*1024):
    need(isinstance(rel,str) and rel,"private_reference")
    p = (root/rel).resolve()
    need(p.is_relative_to(root) and p.is_file() and p.stat().st_size <= limit,"private_reference")
    return p

def source_module():
    item = importlib.util.spec_from_file_location("h71_source_check",PACK/"SOURCE_CHECK.py")
    mod = importlib.util.module_from_spec(item)
    item.loader.exec_module(mod)
    return mod

def budget(closed=False):
    s = spec(); b = s["budgets"]; records = rows()
    need([r["seq"] for r in records] == list(range(1,len(records)+1)),"ledger_sequence")
    begin,end,counts = {},{},{}
    for r in records:
        need(r["event"] in {"BEGIN","END"},"ledger_event")
        table = begin if r["event"] == "BEGIN" else end
        need(r["attempt_id"] not in table,"ledger_duplicate")
        table[r["attempt_id"]] = r
    need(set(end) <= set(begin),"ledger_begin_missing")
    active=[]; source_intervals=[]; total_source=0; total_download=0; seen={}
    now=datetime.now(timezone.utc)
    for ident,first in begin.items():
        kind=first["kind"]
        need(kind in {"active_work","implementation","l2","l3","source_http","live_get","executor_readback","evaluator_readback","download","cli_offline","listener","local_server","browser_action"},"ledger_kind")
        counts[kind]=counts.get(kind,0)+1
        if kind != "active_work":
            need(counts[kind] <= b[kind],"attempt_budget")
        last=end.get(ident)
        need(last is not None or (not closed and kind in {"active_work","l2","l3"}),"attempt_unclosed")
        start=stamp(first["at"]); finish=stamp(last["at"]) if last else now
        need(finish>=start,"ledger_time")
        if last:
            need(last["kind"] == kind and last["status"] in {"SUCCEEDED","FAILED","INPUT_LIMIT","UNKNOWN"},"ledger_end")
        if kind=="active_work": active.append((start,finish))
        if kind in {"listener","local_server"}:
            need((finish-start).total_seconds() <= b["service_seconds"],"service_duration")
            if last:
                need(last.get("stopped") is True and (type(last.get("owned_pid")) is int or
                     (last.get("started") is False and last.get("owned_pid") is None and last["status"]=="INPUT_LIMIT")),"service_cleanup")
        if kind in {"source_http","download"} and last:
            need(type(last.get("bytes")) is int and last["bytes"]>=0,"actual_bytes_missing")
            if kind=="source_http":
                need(source_module().allowed(first["url"]),"source_target")
                total_source+=last["bytes"]; source_intervals.append((start,finish))
                key=(kind,first["url"]); seen[key]=seen.get(key,0)+1
                need(seen[key] <= b["per_source_url"],"source_url_budget")
            else:
                from urllib.parse import urlsplit
                target=urlsplit(first["url"])
                need(target.scheme=="https" and target.username is None and target.password is None
                     and (first["url"]==s["cli"]["url"] or target.hostname in {"release-assets.githubusercontent.com","objects.githubusercontent.com"}),"download_target")
                total_download+=last["bytes"]
        if kind in {"live_get","executor_readback","evaluator_readback"}:
            need(first.get("url") in s["urls"],"runtime_target")
            key=(kind,first["url"]); need(key not in seen,"repeated_runtime_request"); seen[key]=1
        if kind in {"live_get","executor_readback","evaluator_readback","download","cli_offline","listener","local_server","browser_action"}:
            need(finish <= stamp(s["original_deadline"]),"runtime_after_original_deadline")
    active.sort(); source_intervals.sort()
    need(all(a[1]<=z[0] for a,z in zip(active,active[1:])) and sum((z-a).total_seconds() for a,z in active)<=b["active_seconds"],"active_budget")
    need(all(a[1]<=z[0] for a,z in zip(source_intervals,source_intervals[1:])),"source_concurrency")
    need(total_source<=b["source_body_bytes"] and total_download<=b["download_bytes"],"byte_budget")
    if records:
        need(active,"active_ledger_required")
        finish=max([stamp(r["at"]) for r in records]+([now] if set(begin)-set(end) else []))
        need((finish-min(stamp(r["at"]) for r in records)).total_seconds()<=b["wall_seconds"],"wall_budget")
    # All old usage is fixed in BASELINE. Conservatively count both provisioning POSTs too.
    prior_active=0; prior_api=0; prior_download=0; prior_browser=5
    for parent in (PACK.parent/"H68_STRIPE_CHECKOUT_SANDBOX_JOURNEY_V1",H69):
        old=[json.loads(x) for x in (parent/"ATTEMPT_LEDGER.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        old_end={r["attempt_id"]:r for r in old if r["event"]=="END"}
        for first in (r for r in old if r["event"]=="BEGIN"):
            need(first["attempt_id"] in old_end,"parent_attempt_unclosed")
            kind=first["kind"]
            if kind=="active_work": prior_active+=(stamp(old_end[first["attempt_id"]]["at"])-stamp(first["at"])).total_seconds()
            if kind in {"live_api","executor_readback","evaluator_readback","challenge","provision","account_get"}: prior_api+=1
            if kind=="download": prior_download+=1
            if kind=="browser_action": prior_browser+=1
    need(prior_api+sum(counts.get(k,0) for k in ("live_get","executor_readback","evaluator_readback"))<=120,"shared_api_budget")
    need(prior_download+counts.get("download",0)<=3 and prior_browser+counts.get("browser_action",0)<=80,"shared_tool_budget")
    need(prior_active+sum((z-a).total_seconds() for a,z in active)<=480*60,"shared_active_budget")
    return counts

def integrity():
    b=load(PACK/"BASELINE.json")
    head=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    need(head==b["head"],"baseline_head")
    for rel,digest in b["protected"].items(): need((ROOT/rel).is_file() and sha((ROOT/rel).read_bytes())==digest,"protected_input_changed")
    for rel,digest in b["frozen"].items(): need(sha((PACK/rel).read_bytes())==digest,"frozen_input_changed")
    current=(ROOT/"CURRENT.md").read_text(encoding="utf-8")
    need("task_id: "+PACK.name in current,"router")
    for name in ("commit","push","history_rewrite","test_payments"):
        need("authorization_"+name+": false" in current,"authority_expanded")
    for name in ("api_call","install","local_service","browser_test_only"):
        need("authorization_"+name+": true" in current,"authority_missing")
    parent=load(PACK.parent/"H68_STRIPE_CHECKOUT_SANDBOX_JOURNEY_V1/AUTHORIZATION.json")
    need(parent["status"]=="GRANTED" and parent["human_quote"]==load(PACK/"AUTHORIZATION.json")["human_quote"],"original_authorization")
    visible=subprocess.run(["git","ls-files","--others","--exclude-standard","-z"],cwd=ROOT,capture_output=True,check=True).stdout
    prefix=PACK.relative_to(ROOT).as_posix()+"/"
    allowed=set(b["frozen"])|{"BASELINE.json","RUN.py","REPORT.md","RESULT.json","PERMISSION_MATRIX.json","SOURCE_MANIFEST.json","ATTEMPT_LEDGER.jsonl","REVIEW.md"}
    for item in visible.split(b"\0"):
        if not item: continue
        rel=item.decode("utf-8")
        need(rel in b["inherited_untracked"] or rel.startswith(prefix),"new_file_scope")
        if rel.startswith(prefix): need(rel[len(prefix):] in allowed or rel[len(prefix):].startswith(("sources/","evidence/","versions/","references/")),"new_output_scope")
    budget()
    print("H71 frozen package, historical inputs and original authority allocation intact")

def validate_material(result,material,private,key,account,h69_digest):
    s=spec()
    need(set(result)==set(s["public_fields"]),"public_fields")
    need(result["schema"]=="h71-long-qualification-result/v1" and result["task_id"]==PACK.name,"result_identity")
    need(result["decision"] in s["decisions"] and result["stage"] in s["phases"]+["complete"],"result_decision")
    need(re.fullmatch(r"[A-Za-z0-9_-]{1,100}",result["run_id"]) and re.fullmatch(r"[A-Z0-9_]{1,100}",result["reason_code"]),"public_identifier")
    need(result["account_assurance"]==s["account_assurance"] and result["checkout_write_permission"]=="NOT_MEASURED","unsupported_assurance")
    need(all(type(result[k]) is int and result[k]==0 for k in ("checkout_sessions","payments")),"business_side_effect")
    need(material["schema"]=="h71-long-qualification-private/v1" and material["run_id"]==result["run_id"],"private_identity")
    need(material["h69_snapshot_sha256"]==h69_digest,"provision_source")
    need(key.startswith("rkcs_test_") and material["key_sha256"]==sha(key.encode()),"same_test_credential")
    need(material["account_ref"]==result["account_ref"]==sha(account.encode()),"account_projection")
    phases=material["phases"]; need(set(phases)==set(s["phases"]),"phase_set")
    blocked=False; blocker=None
    for name in s["phases"]:
        status=phases[name]["status"]
        need(status in {"PASS","INPUT_LIMIT","NOT_RUN"} and isinstance(phases[name]["reason"],str),"phase_status")
        if blocked: need(status=="NOT_RUN","continued_after_stop")
        elif status=="INPUT_LIMIT": blocked=True; blocker=name
        else: need(status=="PASS","phase_missing")
    if result["decision"]=="READ_AND_LISTEN_READY": need(not blocked and result["stage"]=="complete","false_readiness")
    else: need(blocked and result["stage"]==blocker,"failure_stage")
    requests=material["http"]; need(isinstance(requests,list) and len(requests)<=3,"runtime_requests")
    for i,r in enumerate(requests):
        need(r["method"]=="GET" and r["url"]==s["urls"][i] and r["key_sha256"]==sha(key.encode()),"runtime_method_target_context")
        need(stamp(r["finished_at"])>=stamp(r["started_at"]) and stamp(r["finished_at"])<=stamp(s["original_deadline"]),"runtime_time")
        if r["status"] is None:
            need(r["error"] in {"TIMEOUT","DNS","TLS","NETWORK"} and r["body_file"] is None and r["body_sha256"] is None,"transport_evidence")
        else:
            need(type(r["status"]) is int and 100<=r["status"]<=599,"http_status")
            raw=private_file(private,r["body_file"]).read_bytes()
            need(sha(raw)==r["body_sha256"],"response_digest")
        if r["status"]!=200 or r["error"] is not None: need(i==len(requests)-1 and phases["readonly"]["status"]=="INPUT_LIMIT","continued_after_read_failure")
        else:
            try: obj=load(private_file(private,r["body_file"]))
            except (ValueError,UnicodeDecodeError): obj={}
            valid=obj.get("object")=="list" and obj.get("data")==[] and obj.get("has_more") is False
            if not valid: need(i==len(requests)-1 and phases["readonly"]["status"]=="INPUT_LIMIT","unexpected_objects_not_stopped")
    if phases["readonly"]["status"]=="PASS":
        need(len(requests)==3 and all(r["status"]==200 and r["error"] is None for r in requests),"read_evidence_missing")
        for r in requests:
            obj=load(private_file(private,r["body_file"]))
            need(obj.get("object")=="list" and obj.get("data")==[] and obj.get("has_more") is False,"read_success_not_empty_complete")
    elif blocker in {"prerequisites","source_review"}: need(not requests,"runtime_before_prerequisites")
    listener=material["listener"]; browser=material["browser"]
    if listener["attempted"]:
        need(phases["download"]["status"]=="PASS" and phases["readonly"]["status"]=="PASS","listener_preconditions")
        need(listener["test_mode"] is True and listener["config_isolated"] is True and listener["key_in_argv"] is False
             and listener["stopped"] is True and listener["receiver_stopped"] is True,"listener_boundary")
    else: need(listener["ready"] is False,"listener_not_run")
    if phases["download"]["status"]=="PASS":
        archive=private_file(private,listener["archive_file"],64*1024*1024)
        need(archive.stat().st_size==s["cli"]["archive_bytes"] and sha(archive.read_bytes())==s["cli"]["archive_sha256"],"release_digest")
        need(b"1.55.10" in private_file(private,"cli.version.log").read_bytes() and private_file(private,"cli.help.log").stat().st_size>0,"offline_cli_evidence")
    if phases["listen"]["status"]=="PASS":
        need(listener["attempted"] and listener["ready"],"listener_readiness")
        logs=private_file(private,listener["stdout_file"]).read_bytes()+private_file(private,listener["stderr_file"]).read_bytes()
        need(b"Ready!" in logs and re.search(rb"whsec_[A-Za-z0-9]+",logs),"listener_raw_readiness")
    if phases["browser_local"]["status"]=="PASS":
        need(all(browser[k] is True for k in ("attempted","isolated","clicked","closed")) and browser["observed"]=="H71_LOCAL_CLICK_OK","browser_actual_state")
        need(private_file(private,browser["proof_file"]).stat().st_size>0,"browser_proof")
    elif blocker!="browser_local": need(browser["attempted"] is False,"browser_before_preconditions")

def artifacts():
    result=load(PACK/"RESULT.json"); private=private_root("H71_PRIVATE_DIR")
    snapshot=private_file(private,"SNAPSHOT.json"); need(sha(snapshot.read_bytes())==result["private_snapshot_sha256"],"snapshot_digest")
    material=load(snapshot)
    old=load(H69/"RESULT.json"); original=private_root("H69_PRIVATE_DIR")
    raw=private_file(original,"SNAPSHOT.json")
    need(sha(raw.read_bytes())==old["private_snapshot_sha256"],"h69_material_changed")
    provision=next(r for r in load(raw)["http"] if r["url"]=="https://ai.stripe.com/keys/provision")
    response=load(private_file(original,provision["body_file"]))
    need(sha(private_file(original,provision["body_file"]).read_bytes())==provision["body_sha256"],"h69_provision_digest")
    key=response.get("restricted_key") or response.get("secret_key"); account=response.get("account_id") or response.get("merchant_token")
    credentials=load(private_file(private,"CREDENTIALS.json"))
    need(credentials=={"key":key,"account_id":account},"credential_changed")
    validate_material(result,material,private,key,account,old["private_snapshot_sha256"])
    counts=budget()
    for source in load(PACK/"SOURCE_MANIFEST.json")["sources"]:
        matching=[x for x in rows() if x["event"]=="BEGIN" and x["kind"]=="source_http" and x.get("url")==source["url"]]
        need(any(any(y["event"]=="END" and y["attempt_id"]==x["attempt_id"] and y.get("http_status")==200
                     and y.get("bytes")==source["bytes"] for y in rows()) for x in matching),"source_ledger_binding")
    need(len(material["http"])==counts.get("live_get",0),"http_ledger_count")
    for r in material["http"]:
        first=next((x for x in rows() if x["event"]=="BEGIN" and x["kind"]=="live_get" and x.get("url")==r["url"]),None)
        need(first is not None,"request_ledger_missing")
        last=next((x for x in rows() if x["event"]=="END" and x["attempt_id"]==first["attempt_id"]),None)
        need(last is not None and last.get("http_status")==r["status"] and stamp(first["at"])<=stamp(r["started_at"])
             and stamp(last["at"])>=stamp(r["finished_at"]),"request_ledger_status_or_time")
    need(int(bool(material["listener"]["attempted"]))==counts.get("listener",0),"listener_ledger_count")
    if material["listener"]["attempted"]: need(counts.get("local_server",0)==1,"receiver_ledger_missing")
    if counts.get("local_server",0): need(material["listener"]["receiver_stopped"] is True,"receiver_not_stopped")
    need(bool(material["browser"]["attempted"])==bool(counts.get("browser_action",0)),"browser_ledger_count")
    # Exact secrets/identifiers from this environment may never appear in public task files.
    forbidden=[key.encode(),account.encode()]
    if response.get("claim_url"): forbidden.append(response["claim_url"].encode())
    for name in ("stdout_file","stderr_file"):
        ref=material["listener"].get(name)
        if ref:
            forbidden.extend(re.findall(rb"whsec_[A-Za-z0-9]+",private_file(private,ref).read_bytes()))
    forbidden.extend([str(private).encode(),str(original).encode()])
    for p in PACK.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            need(not any(x in p.read_bytes() for x in forbidden),"private_value_public")
    print("H71 persisted qualification evidence and stop branch consistent; transport/semantic review required")
    return result,material,private,credentials

def append(kind,event,ident,**values):
    record={"seq":len(rows())+1,"kind":kind,"event":event,"attempt_id":ident,"at":datetime.now(timezone.utc).isoformat(),**values}
    with (PACK/"ATTEMPT_LEDGER.jsonl").open("ab") as stream:
        stream.write((json.dumps(record,sort_keys=True)+"\n").encode()); stream.flush(); os.fsync(stream.fileno())

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def readback(actor):
    integrity(); result,material,private,creds=artifacts()
    if result["decision"]!="READ_AND_LISTEN_READY":
        print("H71 stopped qualification re-audited; no live request repeated")
        return
    nonce=os.environ.get("H71_EVALUATOR_NONCE","") if actor=="evaluator" else "executor"
    if actor=="evaluator":
        need(len(nonce)>=32 and "current_role: Evaluator" in (ROOT/"CURRENT.md").read_text(encoding="utf-8"),"independent_evaluator_nonce")
    marker=PACK/"evidence"/("READBACK_"+actor+".json")
    if marker.exists():
        saved=load(marker)
        need(saved["nonce_sha256"]==sha(nonce.encode()) and saved["checker_sha256"]==sha(Path(__file__).read_bytes()) and saved["run_id"]==result["run_id"],"readback_marker_context")
        for item in saved["requests"]:
            need(sha(private_file(private,item["file"]).read_bytes())==item["sha256"],"readback_body_changed")
        need(saved["matched"] is True,"readback_failed_previously")
        print("H71 actor-specific readback retained; no duplicate GET")
        return
    s=spec(); need(datetime.now(timezone.utc)<=stamp(s["original_deadline"]),"original_authorization_expired")
    counts=budget(); need(counts.get(actor+"_readback",0)==0,"readback_already_attempted")
    attempts=[]; matched=True
    for i,url in enumerate(s["urls"]):
        budget(); need(datetime.now(timezone.utc)<=stamp(s["original_deadline"]),"original_authorization_expired")
        ident="h71-"+actor+"-readback-"+str(i+1); append(actor+"_readback","BEGIN",ident,url=url)
        body=b""; status=None; error=None
        try:
            req=Request(url,headers={"Authorization":"Bearer "+creds["key"],"Stripe-Version":s["api_version"]},method="GET")
            with build_opener(NoRedirect()).open(req,timeout=30) as resp: status=resp.status; body=resp.read(2*1024*1024+1)
        except HTTPError as exc: status=exc.code; body=exc.read(2*1024*1024+1)
        except (URLError,OSError,TimeoutError): error="NETWORK"
        finally: append(actor+"_readback","END",ident,status="SUCCEEDED" if status==200 else "INPUT_LIMIT",http_status=status)
        need(len(body)<=2*1024*1024,"readback_body_size")
        filename="READBACK_"+actor+"_"+str(i+1)+".bin"; (private/filename).write_bytes(body)
        obj={}
        if status==200:
            try: obj=json.loads(body,object_pairs_hook=unique)
            except (ValueError,UnicodeDecodeError): pass
        good=status==200 and obj.get("object")=="list" and obj.get("data")==[] and obj.get("has_more") is False
        attempts.append({"url":url,"status":status,"error":error,"file":filename,"sha256":sha(body),"matched":good})
        if not good: matched=False; break
    marker.parent.mkdir(parents=True,exist_ok=True)
    marker.write_text(json.dumps({"actor":actor,"run_id":result["run_id"],"nonce_sha256":sha(nonce.encode()),"checker_sha256":sha(Path(__file__).read_bytes()),"requests":attempts,"matched":matched},indent=2)+"\n",encoding="utf-8")
    need(matched and len(attempts)==3,"independent_readback_unavailable")
    print("H71 independent same-credential three-list readback recorded; no writes")

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("command",choices=("integrity","sources","artifacts","readback","budget")); parser.add_argument("--actor",choices=("executor","evaluator"),default="executor"); parser.add_argument("--closed",action="store_true"); args=parser.parse_args()
    try:
        if args.command=="integrity": integrity()
        elif args.command=="sources": source_module().sources()
        elif args.command=="artifacts": artifacts()
        elif args.command=="readback": readback(args.actor)
        else: budget(args.closed); print("H71 original shared envelope and reported task budget valid")
    except (OSError,ValueError,TypeError,KeyError,IndexError,AttributeError,AssertionError,subprocess.SubprocessError):
        print("H71 CHECK FAILED; inspect private material locally; no secrets printed",file=sys.stderr)
        raise SystemExit(1)

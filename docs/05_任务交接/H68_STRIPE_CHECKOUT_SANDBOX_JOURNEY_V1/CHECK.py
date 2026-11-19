"""Evaluator-owned H68 checks. Network is confined to authorized GET readback."""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import hmac
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
TASK = PACK.name


class CheckFailure(Exception):
    pass


def need(condition, label):
    if not condition:
        raise CheckFailure(label)


def unique(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, "duplicate_json_key")
        result[key] = value
    return result


def decode(raw):
    need(len(raw) <= 8 * 1024 * 1024, "json_size_limit")
    return json.loads(raw, object_pairs_hook=unique)


def load(path):
    return decode(Path(path).read_bytes())


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def instant(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    need(parsed.tzinfo is not None, "timestamp_timezone_missing")
    return parsed.timestamp()


def private_root():
    value = os.environ.get("H68_PRIVATE_DIR")
    need(bool(value), "private_materials_unavailable")
    path = Path(value).resolve()
    need(path != ROOT and ROOT not in path.parents, "private_directory_inside_repository")
    need(path.is_dir(), "private_directory_missing")
    return path


def authorization():
    spec = load(PACK / "SPEC.json")
    auth = load(PACK / "AUTHORIZATION.json")
    need(auth.get("status") == "GRANTED", "runtime_authorization_not_granted")
    need(all(auth.get(key) is True for key in spec["runtime_authorization_required"]), "runtime_permission_missing")
    need(bool(auth.get("human_quote")) and bool(auth.get("approved_at")), "authorization_source_missing")
    current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    need("authorization_api_call: true" in current and TASK in current, "router_runtime_authority_missing")


def package_check(require_frozen=False):
    spec = load(PACK / "SPEC.json")
    plan = load(PACK / "VALIDATION_PLAN.yaml")  # JSON is a YAML subset.
    inputs = load(PACK / "INPUTS.json")
    head = subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    need(head == inputs["baseline_head"], "baseline_head_changed")
    need(spec["task_id"] == plan["task_id"] == TASK, "package_task_id_mismatch")
    need(plan["schema"] == "evaluator-executor-validation-plan/v1", "plan_schema")
    mapped = {ac for check in plan["checks"] for ac in check["ac"]}
    need(mapped == set(spec["acceptance_criteria"]), "plan_ac_coverage")
    for rel, expected in inputs["shared_tools"].items():
        need(digest((ROOT/rel).read_bytes()) == expected, "shared_workflow_tool_changed")
    common_path = ROOT.parent/"localagent-common"/"skills"/"evaluator-executor-workflow"/"scripts"/"validate_workflow.py"
    module_spec = importlib.util.spec_from_file_location("h68_shared_workflow",common_path)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    findings = module.validate_v22_plan(ROOT,PACK/"VALIDATION_PLAN.yaml",task_id=TASK,contract_acs=set(spec["acceptance_criteria"]))
    need(not findings, "shared_validation_plan_rejected")
    for check in plan["checks"]:
        need(check["mandatory"] is True and check["expected_exit_code"] == 0, "plan_gate_weakened")
        need(check["cwd"] == "." and isinstance(check["command"], list), "plan_command_invalid")
    for rel, expected in inputs["package_files"].items():
        need(digest((PACK / rel).read_bytes()) == expected, "package_hash_mismatch:" + rel)
    for rel, expected in inputs["protected_files"].items():
        need(digest((ROOT / rel).read_bytes()) == expected, "protected_hash_mismatch:" + rel)
    from PREPARE_INPUTS import tracked_tree
    count, tree_sha = tracked_tree(ROOT, set(inputs["governance_files"]) | set(inputs["new_product_files"]))
    need(count == inputs["protected_tracked_count"] and tree_sha == inputs["protected_tracked_tree_sha256"], "protected_tracked_tree_changed")
    if require_frozen:
        visible = subprocess.run(["git","-c","core.quotePath=false","ls-files","--others","--exclude-standard"],cwd=ROOT,capture_output=True,encoding="utf-8",check=True).stdout.splitlines()
        known = set(inputs["inherited_untracked"]) | set(inputs["new_product_files"])
        prefix = PACK.relative_to(ROOT).as_posix()+"/"
        allowed_outputs = load(PACK/"SPEC.json")["executor_task_outputs"]
        for rel in visible:
            if rel in known or rel in inputs["governance_files"]:
                continue
            if rel.startswith(prefix):
                child = rel[len(prefix):]
                need(child in inputs["package_files"] or child == "INPUTS.json" or any(child == p or (p.endswith("/") and child.startswith(p)) for p in allowed_outputs), "unexpected_task_file")
            else:
                raise CheckFailure("out_of_scope_new_file")
    if require_frozen:
        authorization()
        state = (PACK / "CONTRACT.md").read_text(encoding="utf-8")
        need("Contract state: CONTRACT_FROZEN" in state, "contract_not_frozen")
    print("H68 package/integrity OK; this is not a live verdict")


def verify_event(event, secret, session_id):
    raw = base64.b64decode(event["body_b64"], validate=True)
    tokens = [item.split("=", 1) for item in event["signature"].split(",")]
    timestamps = [v for k, v in tokens if k == "t"]
    signatures = [v for k, v in tokens if k == "v1"]
    need(len(timestamps) == 1 and bool(signatures), "webhook_signature_fields")
    stamp = timestamps[0]
    expected = hmac.new(secret.encode(), stamp.encode() + b"." + raw, hashlib.sha256).hexdigest()
    need(any(hmac.compare_digest(expected, candidate) for candidate in signatures), "webhook_hmac_invalid")
    need(abs(instant(event["received_at"]) - int(stamp)) <= 300, "webhook_original_freshness_invalid")
    body = decode(raw)
    need(body.get("livemode") is False, "webhook_not_test_mode")
    need(body.get("type") == "checkout.session.completed", "webhook_event_type")
    need(body["data"]["object"]["id"] == session_id, "webhook_session_mismatch")


def validate_artifacts(result, provider, secret, resource_sha):
    spec = load(PACK / "SPEC.json")
    need(result.get("schema") == spec["public_result_schema"] and result.get("task_id") == TASK, "result_identity")
    need(provider.get("schema") == spec["private_snapshot_schema"], "provider_schema")
    need(result.get("decision") == "EXTERNAL_JOURNEY_MEASURED", "journey_not_measured")
    need(result.get("security_control_increment") == "NOT_MEASURED", "unsupported_control_gain")
    need(result["run_id"] == provider["run_id"], "run_mismatch")
    started, finished = instant(result["started_at"]), instant(result["finished_at"])
    need(0 <= finished-started <= 24*3600, "run_window_invalid")
    need(provider["account"]["id"].startswith("acct_"), "account_reference")
    cases = result["cases"]
    need(len(cases) == 4 and {x["case_id"] for x in cases} == {x["id"] for x in spec["cases"]}, "case_set")
    need(len({x["operation_id"] for x in cases}) == 4, "operation_not_unique")
    need(len({x["order_id"] for x in cases}) == 4, "order_not_unique")
    expected_sets = {"sessions": set(), "intents": set(), "charges": set()}
    delivery_receipts = []
    for rule in spec["cases"]:
        case = next(x for x in cases if x["case_id"] == rule["id"])
        source = provider["cases"][rule["id"]]
        session, intent, charge = (source[k] for k in ("session", "intent", "charge"))
        sid = session["id"]
        need(type(session.get("created")) is int and started-5 <= session["created"] <= finished+5, "session_outside_run_window")
        need(sid.startswith("cs_test_"), "session_not_test")
        expected_sets["sessions"].add(sid)
        need(case["session_ref"] == digest(sid), "session_projection_mismatch")
        need(case["account_ref"] == digest(provider["account"]["id"]), "account_projection_mismatch")
        need(session.get("livemode") is False and session.get("mode") == "payment", "session_mode")
        need(type(session.get("amount_total")) is int and session["amount_total"] == 100, "session_amount")
        need(session.get("currency") == "usd", "session_currency")
        need(session.get("client_reference_id") == case["order_id"], "order_reference")
        metadata = session["metadata"]
        need(metadata.get("h68_run_id") == result["run_id"], "session_run_binding")
        need(metadata.get("h68_operation_id") == case["operation_id"], "session_operation_binding")
        need(metadata.get("h68_resource_sha256") == resource_sha == case["resource_sha256"], "resource_binding")
        items = source["line_items"]
        need(items.get("has_more") is False and len(items["data"]) == 1, "line_items_scope")
        item = items["data"][0]
        need(item.get("quantity") == 1 and item.get("amount_total") == 100 and item.get("currency") == "usd", "line_item_amount")
        for gate_name in ("create_gate", "submit_gate"):
            gate = case.get(gate_name)
            if gate_name == "submit_gate" and not rule["paid"]:
                need(gate is None, "cancel_payment_was_submitted")
                continue
            need(isinstance(gate, dict), "actual_gate_record_missing")
            need(gate.get("final_decision") == "ALLOW" and gate.get("callback_executed") is True, "gate_non_allow")
            need(type(gate.get("callback_count")) is int and gate["callback_count"] == 1, "gate_callback_count")
            need(all(gate.get(k) == "VALID" for k in ("binding_status", "identity_status", "context_policy_status")), "gate_fact_invalid")
        events = case["timeline"]
        need(len({e["seq"] for e in events}) == len(events), "timeline_seq_duplicate")
        need([e["seq"] for e in events] == sorted(e["seq"] for e in events), "timeline_seq_order")
        stamps = [instant(e["at"]) for e in events]
        need(stamps == sorted(stamps), "timeline_time_order")
        need(all(started-5 <= stamp <= finished+5 for stamp in stamps), "timeline_outside_run")
        kinds = [e["kind"] for e in events]
        def before(first, second):
            need(first in kinds and second in kinds and kinds.index(first) < kinds.index(second), "timeline_relation:" + first + ":" + second)
        before("order_authorized", "create_gate_allow")
        before("create_gate_allow", "session_created")
        deliveries = case["fulfillment_attempts"]
        need(len(deliveries) >= rule["min_delivery_attempts"], "delivery_attempts_missing")
        successes = [d for d in deliveries if d.get("status") == "SUCCEEDED"]
        need(len(successes) == rule["success_deliveries"], "delivery_not_exactly_once")
        need(all(d.get("resource_sha256") == resource_sha and bool(d.get("receipt_ref")) for d in successes), "delivery_content_mismatch")
        delivery_receipts.extend(d["receipt_ref"] for d in successes)
        if rule["paid"]:
            received = base64.b64decode(source["merchant_response_body_b64"],validate=True)
            need(digest(received) == resource_sha, "merchant_delivery_bytes_mismatch")
            need(session.get("payment_status") == "paid" and session.get("status") == "complete", "session_not_paid")
            need(intent and charge and intent.get("livemode") is False and charge.get("livemode") is False, "payment_source_missing")
            need(session.get("payment_intent") == intent["id"], "intent_session_chain")
            need(intent.get("latest_charge") == charge["id"] and charge.get("payment_intent") == intent["id"], "charge_chain")
            need(intent.get("status") == "succeeded" and charge.get("status") == "succeeded", "payment_not_succeeded")
            need(charge.get("paid") is True and charge.get("captured") is True, "charge_not_captured")
            for obj in (intent, charge):
                need(type(obj.get("amount")) is int and obj["amount"] == 100 and obj.get("currency") == "usd", "payment_amount")
                need(type(obj.get("created")) is int and started-5 <= obj["created"] <= finished+5, "payment_outside_run_window")
            need(case["intent_ref"] == digest(intent["id"]) and case["charge_ref"] == digest(charge["id"]), "payment_projection_mismatch")
            expected_sets["intents"].add(intent["id"])
            expected_sets["charges"].add(charge["id"])
            before("submit_gate_allow", "payment_submitted")
            before("prepay_query_valid", "submit_gate_allow")
            before("provider_paid_query", "delivered")
            if rule["id"] in {"N01", "D01"}:
                need(bool(source.get("events")), "actual_webhook_missing")
                for event in source["events"]:
                    verify_event(event, secret, sid)
        else:
            need(session.get("payment_status") == "unpaid" and session.get("status") == "expired" and charge is None, "cancel_has_payment_or_open_session")
            if intent is not None:
                need(intent.get("livemode") is False and intent.get("status") in {"requires_payment_method","requires_confirmation","canceled"}, "cancel_intent_not_unpaid")
                need(session.get("payment_intent") == intent["id"] and case.get("intent_ref") == digest(intent["id"]), "cancel_intent_projection")
                expected_sets["intents"].add(intent["id"])
            else:
                need(case.get("intent_ref") is None, "cancel_unobserved_intent")
            need(case.get("charge_ref") is None, "cancel_payment_projection")
            need(not deliveries and "payment_submitted" not in kinds, "cancel_has_side_effect")
            before("buyer_cancelled", "provider_unpaid_query")
        if rule["id"] == "R01":
            before("local_unknown", "local_process_restarted")
            before("local_process_restarted", "original_payment_queried")
            before("original_payment_queried", "provider_paid_query")
            need(case.get("recovery_result", {}).get("retry_allowed") is False, "recovery_allowed_new_payment")
            need(case["recovery_result"].get("recovery_status") == "RECOVERED", "recovery_not_consumed")
        if rule["id"] == "D01":
            before("provider_paid_query", "delivery_failed")
            before("delivery_failed", "delivery_retried")
            before("delivery_retried", "delivered")
            need("duplicate_event_consumed" in kinds, "duplicate_event_not_observed")
            need(deliveries[0].get("status") == "FAILED", "delivery_fault_not_observed")
    for name, ids in expected_sets.items():
        objects = provider["lists"][name]
        need(objects.get("has_more") is False, "provider_list_incomplete")
        observed = [obj["id"] for obj in objects["data"]]
        need(len(observed) == len(set(observed)) and set(observed) == ids, "unexpected_or_duplicate_provider_objects:" + name)
    need(len(expected_sets["sessions"]) == 4 and len(expected_sets["charges"]) == 3, "provider_counts")
    need(len(delivery_receipts) == len(set(delivery_receipts)) == 3, "delivery_receipt_not_unique")


def artifacts():
    result = load(PACK / "RESULT.json")
    private = private_root()
    raw = (private / "PROVIDER_SNAPSHOT.json").read_bytes()
    need(digest(raw) == result["private_snapshot_sha256"], "private_snapshot_digest")
    credentials = load(private / "credentials.json")
    validate_artifacts(result, decode(raw), credentials["webhook_secret"], digest((PACK / "RESOURCE.txt").read_bytes()))
    print("H68 four-journey evidence checks OK; semantic wiring review still mandatory")


def ledger_rows():
    path = PACK / "ATTEMPT_LEDGER.jsonl"
    need(path.is_file(), "execution_ledger_missing")
    return [decode(line) for line in path.read_bytes().splitlines() if line.strip()]


def budget(closed=False):
    rows = ledger_rows()
    need([r["seq"] for r in rows] == list(range(1, len(rows) + 1)), "ledger_sequence")
    starts, ends = {}, {}
    for row in rows:
        table = starts if row["event"] == "BEGIN" else ends
        need(row["event"] in {"BEGIN", "END"} and row["attempt_id"] not in table, "ledger_event_duplicate")
        table[row["attempt_id"]] = row
    need(set(ends) <= set(starts), "ledger_end_without_begin")
    counts = {}
    active = []
    for key, row in starts.items():
        kind = row["kind"]
        counts[kind] = counts.get(kind, 0) + 1
        end = ends.get(key)
        if end is None:
            need(not closed and kind in {"l2", "l3", "active_work"}, "unfinished_material_attempt")
            finish = time.time()
        else:
            need(end["kind"] == kind and end["status"] in {"SUCCEEDED", "FAILED", "INPUT_LIMIT"}, "ledger_end_fields")
            finish = instant(end["at"])
        begin = instant(row["at"])
        need(finish >= begin, "ledger_time_reverse")
        if kind == "active_work":
            active.append((begin, finish))
        if kind == "download" and end is not None:
            need(type(end.get("bytes")) is int and end["bytes"] >= 0, "download_bytes_unknown")
    limits = {"implementation":2,"l2":2,"l3":1,"anonymous_provision":1,"live_api":80,"executor_readback":20,"evaluator_readback":20,"browser_action":80,"download":3}
    need(set(counts) <= set(limits) | {"service", "active_work"}, "ledger_unknown_kind")
    for kind, limit in limits.items():
        need(counts.get(kind, 0) <= limit, "budget_exceeded:" + kind)
    need(sum(counts.get(k,0) for k in ("live_api","executor_readback","evaluator_readback")) <= 120, "api_total_budget")
    need(bool(active) and sum(end-start for start,end in active) <= 480*60, "active_time_budget")
    active.sort()
    need(all(active[i][1] <= active[i+1][0] for i in range(len(active)-1)), "overlapping_active_time")
    need(max(instant(r["at"]) for r in rows)-min(instant(r["at"]) for r in rows) <= 24*3600, "wall_time_budget")
    need(sum(r.get("bytes",0) for r in ends.values() if r["kind"] == "download") <= 64*1024*1024, "download_byte_budget")
    print("H68 append-only ledger budget OK")


def append_attempt(kind, event, ident, **values):
    path = PACK / "ATTEMPT_LEDGER.jsonl"
    rows = ledger_rows()
    row = {"seq":len(rows)+1,"event":event,"attempt_id":ident,"kind":kind,"at":datetime.now(timezone.utc).isoformat(),**values}
    with path.open("ab") as stream:
        stream.write(canonical(row)+b"\n")
        stream.flush()
        os.fsync(stream.fileno())


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def readback(actor):
    authorization()
    package_check(require_frozen=True)
    result = load(PACK / "RESULT.json")
    private = private_root()
    original = load(private / "PROVIDER_SNAPSHOT.json")
    credentials = load(private / "credentials.json")
    need(credentials["api_key"].startswith(("rkcs_test_", "rk_test_", "sk_test_")), "test_key_required")
    destination = private / ("READBACK_" + actor + ".json")
    nonce = "executor"
    if actor == "evaluator":
        nonce = os.environ.get("H68_EVALUATOR_NONCE", "")
        need(len(nonce) >= 32, "independent_evaluator_nonce_missing")
        current = (ROOT/"CURRENT.md").read_text(encoding="utf-8")
        need("current_role: Evaluator" in current, "independent_evaluator_role_missing")
    marker = {"actor":actor,"nonce_sha256":digest(nonce),"checker_sha256":digest(Path(__file__).read_bytes())}
    if destination.is_file():
        recovered = load(destination)
        need(recovered["run_id"] == result["run_id"], "readback_cache_run_mismatch")
        need(recovered.get("_readback") == marker, "readback_provenance_mismatch")
        validate_artifacts(result,recovered,credentials["webhook_secret"],digest((PACK/"RESOURCE.txt").read_bytes()))
        print("H68 same-actor readback re-audited; no new HTTP calls")
        return
    stage = actor + "_readback"
    opener = build_opener(NoRedirect())
    def get(path):
        used = sum(r["event"] == "BEGIN" and r["kind"] == stage for r in ledger_rows())
        need(used < 20, "readback_request_budget")
        ident = stage + "-" + str(used+1)
        append_attempt(stage,"BEGIN",ident,method="GET",path_class=path.split("?",1)[0].split("/")[2])
        try:
            request = Request("https://api.stripe.com"+path,headers={"Authorization":"Bearer "+credentials["api_key"],"Stripe-Version":load(PACK/"SPEC.json")["api_version"]},method="GET")
            with opener.open(request,timeout=30) as response:
                raw = response.read(2*1024*1024+1)
                need(response.status == 200 and len(raw) <= 2*1024*1024, "readback_http_or_size")
            parsed = decode(raw)
            append_attempt(stage,"END",ident,status="SUCCEEDED",response_sha256=digest(raw),bytes=len(raw))
            return parsed
        except Exception:
            append_attempt(stage,"END",ident,status="FAILED")
            raise CheckFailure("readback_failed_without_sensitive_output") from None
    snapshot = {"schema":load(PACK/"SPEC.json")["private_snapshot_schema"],"run_id":result["run_id"],"_readback":marker,"account":get("/v1/account"),"cases":{},"lists":{}}
    need(snapshot["account"]["id"] == original["account"]["id"] == credentials["account_id"], "readback_account_mismatch")
    for case in result["cases"]:
        prior = original["cases"][case["case_id"]]
        sid = prior["session"]["id"]
        need(sid.startswith("cs_test_") and all(c.isalnum() or c == "_" for c in sid), "readback_session_id")
        session = get("/v1/checkout/sessions/"+sid+"?"+urlencode({"expand[]":"payment_intent.latest_charge"}))
        intent = session.get("payment_intent")
        charge = intent.get("latest_charge") if isinstance(intent,dict) else None
        if intent:
            need(isinstance(intent,dict), "expanded_payment_missing")
            session["payment_intent"] = intent["id"]
            if charge is not None:
                need(isinstance(charge,dict), "expanded_charge_missing")
                intent["latest_charge"] = charge["id"]
        snapshot["cases"][case["case_id"]] = {"session":session,"intent":intent,"charge":charge,"line_items":get("/v1/checkout/sessions/"+sid+"/line_items?limit=100"),"events":prior.get("events",[]),"merchant_response_body_b64":prior.get("merchant_response_body_b64")}
        if case["case_id"] in {"N01","D01"}:
            need(bool(prior.get("events")), "provider_event_missing")
            archived = decode(base64.b64decode(prior["events"][0]["body_b64"],validate=True))
            eid = archived["id"]
            need(eid.startswith("evt_") and all(c.isalnum() or c == "_" for c in eid), "event_id_invalid")
            native = get("/v1/events/"+eid)
            need(native["id"] == eid and native.get("livemode") is False and native.get("type") == archived.get("type") and native["data"]["object"]["id"] == sid, "native_event_mismatch")
    for name,path in (("sessions","/v1/checkout/sessions"),("intents","/v1/payment_intents"),("charges","/v1/charges")):
        snapshot["lists"][name] = get(path+"?limit=100")
    raw = canonical(snapshot)
    destination.write_bytes(raw)
    validate_artifacts(result,snapshot,credentials["webhook_secret"],digest((PACK/"RESOURCE.txt").read_bytes()))
    public = PACK / "derived" / ("READBACK_"+actor+".json")
    public.parent.mkdir(exist_ok=True)
    public.write_bytes(canonical({"task_id":TASK,"run_id":result["run_id"],"actor":actor,"private_sha256":digest(raw),"verdict":"MATCHED_NATIVE_PROVIDER_OBJECTS"}))
    print("H68 independent test-account GET readback matched; no payment repeated")


def regressions():
    spec = load(PACK / "SPEC.json")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    modules = ["tests.test_stripe_checkout_adapter","tests.test_stripe_checkout_lab",*spec["legacy_tests"]]
    done = subprocess.run([sys.executable,"-m","unittest",*modules],cwd=ROOT,env=env,timeout=420)
    need(done.returncode == 0, "targeted_regression_failure")


def selftest():
    from CHECK_SELFTEST import run
    run(validate_artifacts, CheckFailure, digest, canonical, PACK, TASK)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command",choices=["package","integrity","artifacts","readback","regressions","selftest","budget"])
    parser.add_argument("--actor",choices=["executor","evaluator"],default="executor")
    parser.add_argument("--closed",action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "package": package_check()
        elif args.command == "integrity": package_check(require_frozen=True)
        elif args.command == "artifacts": artifacts()
        elif args.command == "readback": readback(args.actor)
        elif args.command == "regressions": regressions()
        elif args.command == "selftest": selftest()
        elif args.command == "budget": budget(args.closed)
    except (CheckFailure,OSError,ValueError,KeyError,TypeError) as error:
        # Never print private paths, bodies, credentials or URL query strings.
        label = str(error) if isinstance(error,CheckFailure) else type(error).__name__
        print("H68 CHECK FAIL: "+label)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

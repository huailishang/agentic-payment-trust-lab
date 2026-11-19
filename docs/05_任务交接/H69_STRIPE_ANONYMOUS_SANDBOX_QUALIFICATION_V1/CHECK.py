"""Frozen H69 qualification checks. Only readback performs one bounded GET.

Public outputs never include credentials, raw provider data or private paths.
This is not an external-payment or webhook-delivery checker.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
TASK = PACK.name


class Failed(Exception):
    pass


def need(value, code):
    if not value:
        raise Failed(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    value = {}
    for key, item in pairs:
        need(key not in value, "duplicate_json_key")
        value[key] = item
    return value


def load(path):
    raw = path.read_bytes()
    need(len(raw) <= 4 * 1024 * 1024, "json_size")
    return json.loads(raw, object_pairs_hook=unique)


def stamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    need(parsed.tzinfo is not None, "timezone_required")
    return parsed


def git_files(*args):
    raw = subprocess.run(["git", "ls-files", "-z", *args], cwd=ROOT,
                         capture_output=True, check=True).stdout
    return sorted(x.decode("utf-8") for x in raw.split(b"\0") if x)


def private_root():
    value = os.environ.get("H69_PRIVATE_DIR")
    need(bool(value), "private_material_unavailable")
    path = Path(value).resolve()
    need(path.is_dir() and not path.is_relative_to(ROOT), "private_location_invalid")
    return path


def private_file(private, rel, max_bytes=2*1024*1024):
    need(isinstance(rel, str) and rel, "private_reference_missing")
    target = (private / rel).resolve()
    need(target.is_relative_to(private) and target.is_file(), "private_reference_invalid")
    need(target.stat().st_size <= max_bytes, "private_body_size")
    return target


def ledger():
    path = PACK / "ATTEMPT_LEDGER.jsonl"
    if not path.exists():
        return []
    return [json.loads(line, object_pairs_hook=unique)
            for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def budget(closed=False):
    spec = load(PACK / "SPEC.json")
    rows = ledger()
    need([r["seq"] for r in rows] == list(range(1, len(rows)+1)), "ledger_sequence")
    begin, end, counts = {}, {}, {}
    active = []
    now = datetime.now(timezone.utc)
    for row in rows:
        event = row["event"]
        need(event in {"BEGIN", "END"}, "ledger_event")
        table = begin if event == "BEGIN" else end
        need(row["attempt_id"] not in table, "ledger_duplicate")
        table[row["attempt_id"]] = row
    need(set(end) <= set(begin), "ledger_end_without_begin")
    downloaded = 0
    for ident, first in begin.items():
        kind = first["kind"]
        need(kind in spec["budgets"] or kind == "active_work", "ledger_kind")
        counts[kind] = counts.get(kind, 0)+1
        if kind != "active_work":
            need(kind in {"implementation","l2","l3","challenge","provision","account_get",
                          "executor_readback","evaluator_readback","download","listener","local_server"}, "ledger_kind")
            need(counts[kind] <= spec["budgets"][kind], "attempt_budget")
        last = end.get(ident)
        if closed:
            need(last is not None, "unclosed_attempt")
        if last is None:
            need(kind in {"active_work", "l2", "l3"}, "unclosed_attempt")
        finish = stamp(last["at"]) if last else now
        start = stamp(first["at"])
        need(finish >= start, "ledger_time")
        if last:
            need(last["kind"] == kind and last["status"] in {"SUCCEEDED","FAILED","INPUT_LIMIT","UNKNOWN"}, "ledger_end")
        if kind == "active_work":
            active.append((start, finish))
        if kind in {"listener", "local_server"}:
            need((finish-start).total_seconds() <= 60, "process_duration")
        if kind == "download" and last:
            need(type(last.get("bytes")) is int and last["bytes"] >= 0, "download_bytes_missing")
            downloaded += last["bytes"]
    active.sort()
    need(all(a[1] <= b[0] for a,b in zip(active, active[1:])), "active_overlap")
    need(sum((b-a).total_seconds() for a,b in active) <= 45*60, "active_budget")
    need(downloaded <= spec["budgets"]["download_bytes"], "download_budget")
    if rows:
        earliest = min(stamp(r["at"]) for r in rows)
        need(active and (now-earliest).total_seconds() <= 120*60, "wall_budget")
        need(now <= stamp(spec["original_deadline"]), "original_authorization_expired")
    return counts


def integrity():
    baseline = load(PACK / "BASELINE.json")
    need(datetime.now(timezone.utc) <= stamp(load(PACK/"SPEC.json")["original_deadline"]), "original_authorization_expired")
    head = subprocess.run(["git","rev-parse","HEAD"], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout.strip()
    need(head == baseline["head"], "baseline_head")
    need(set(git_files()) - set(baseline["governance"]) == set(baseline["tracked_files"]), "tracked_scope")
    for rel, digest in baseline["protected"].items():
        need((ROOT/rel).is_file() and sha((ROOT/rel).read_bytes()) == digest, "protected_input_changed")
    for rel, digest in baseline["package_files"].items():
        need(sha((PACK/rel).read_bytes()) == digest, "frozen_package_changed")
    for rel, digest in baseline["shared_tools"].items():
        need(sha((ROOT/rel).read_bytes()) == digest, "shared_tool_changed")
    prefix = PACK.relative_to(ROOT).as_posix()+"/"
    for rel in git_files("--others", "--exclude-standard"):
        if rel in baseline["inherited_untracked"]:
            continue
        need(rel.startswith(prefix), "out_of_scope_file")
        child = rel[len(prefix):]
        need(child in set(baseline["package_files"]) | {"BASELINE.json","RUN.py","RESULT.json","REPORT.md","REVIEW.md","ATTEMPT_LEDGER.jsonl"}
             or child.startswith(("evidence/","versions/")), "unexpected_package_file")
    current = (ROOT/"CURRENT.md").read_text(encoding="utf-8")
    need("task_id: "+TASK in current and "authorization_api_call: true" in current, "runtime_authority")
    need(all("authorization_"+x+": false" in current for x in
             ("commit","push","history_rewrite","browser_test_only","test_payments")), "authority_expanded")
    parent = PACK.parent/"H68_STRIPE_CHECKOUT_SANDBOX_JOURNEY_V1"
    auth = load(parent/"AUTHORIZATION.json")
    need(auth["status"] == "GRANTED" and auth["human_quote"] == "同意按 H68 授权范围执行", "parent_authority")
    prior = [json.loads(x) for x in (parent/"ATTEMPT_LEDGER.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    need(not any(r["kind"] in {"anonymous_provision","download","live_api","executor_readback","evaluator_readback"} for r in prior), "parent_quota_already_consumed")
    budget()
    print("H69 package, original authorization allocation and reported budget OK")


def inspect_material():
    result = load(PACK/"RESULT.json")
    spec = load(PACK/"SPEC.json")
    need(set(result) == set(spec["result_fields"]), "public_fields")
    need(result["schema"] == spec["public_schema"] and result["task_id"] == TASK, "result_identity")
    need(result["decision"] in spec["decisions"] and result["stage"] in spec["stages"], "result_decision")
    need(bool(re.fullmatch(r"[A-Z0-9_]{1,100}", result["reason_code"])), "public_reason")
    need(bool(re.fullmatch(r"[A-Za-z0-9_-]{1,100}", result["run_id"])), "public_run_id")
    need(all(type(result[x]) is int and result[x] == 0 for x in
             ("checkout_sessions", "payments", "browser_actions")), "forbidden_business_action")
    private = private_root()
    manifest_path = private_file(private, "SNAPSHOT.json")
    need(sha(manifest_path.read_bytes()) == result["private_snapshot_sha256"], "private_manifest_digest")
    material = load(manifest_path)
    need(material["schema"] == spec["private_schema"] and material["run_id"] == result["run_id"], "private_identity")
    need(material["creation"] == result["creation"] and result["creation"] in spec["creation_values"], "creation_state")
    records = material["http"]
    need(isinstance(records, list), "request_evidence_missing")
    if not records:
        need(result["stage"] == "preflight" and result["decision"] == "INPUT_LIMIT"
             and result["creation"] == "NOT_SENT", "request_evidence_missing")
        proof = load(private_file(private, material.get("preflight_file")))
        need(proof["run_id"] == result["run_id"] and proof["eligible"] is False, "preflight_evidence")
    posts, accounts, parsed = {}, [], []
    for record in records:
        need(set(spec["http_record_fields"]) <= set(record), "request_fields")
        method, url = record["method"], record["url"]
        if method == "POST":
            need(url in {"https://ai.stripe.com/keys/challenge", "https://ai.stripe.com/keys/provision"}
                 and url not in posts, "unexpected_or_repeated_post")
            posts[url] = record
        else:
            need(method == "GET" and url == "https://api.stripe.com/v1/account", "request_target")
            accounts.append(record)
        need(stamp(record["finished_at"]) >= stamp(record["started_at"]), "request_timing")
        if record["status"] is None:
            need(record["error"] in {"TIMEOUT","DNS","TLS","NETWORK"}, "transport_failure")
            need(record["body_file"] is None and record["body_sha256"] is None, "transport_body")
        else:
            need(type(record["status"]) is int and 100 <= record["status"] <= 599, "http_status")
            path = private_file(private, record["body_file"])
            need(sha(path.read_bytes()) == record["body_sha256"], "provider_body_digest")
        parsed.append(record)
    need(len(accounts) <= 2, "account_query_budget")
    counts = budget()
    for suffix, kind in (("challenge","challenge"), ("provision","provision")):
        count = int("https://ai.stripe.com/keys/"+suffix in posts)
        need(count == counts.get(kind, 0), "request_ledger_mismatch")
    need(len(accounts) == counts.get("account_get", 0), "query_ledger_mismatch")
    provision = posts.get("https://ai.stripe.com/keys/provision")
    challenge = posts.get("https://ai.stripe.com/keys/challenge")
    if challenge:
        request = load(private_file(private, challenge.get("request_body_file")))
        need(request == {"email":spec["synthetic_email"]}, "challenge_contact_boundary")
    if provision and provision["status"] == 200:
        need(result["creation"] == "CREATED", "successful_creation_hidden")
    if provision and provision["status"] is None:
        need(result["creation"] == "UNKNOWN", "unknown_write_hidden")
    if result["decision"] != "ELIGIBLE":
        need(result["stage"] != "complete", "inconsistent_failure_stage")
    if provision:
        need(challenge and challenge["status"] == 200, "provision_without_challenge")
        need(stamp(challenge["finished_at"]) <= stamp(provision["started_at"]), "provision_order")
        request = load(private_file(private, provision.get("request_body_file")))
        original = load(private_file(private, challenge["body_file"]))
        need(request["email"] == spec["synthetic_email"] and not request.get("name"), "personal_data_boundary")
        need(all(request[k] == original[k] for k in ("algorithm","challenge","salt","signature")), "challenge_binding")
        need(request["algorithm"].lower().replace("-", "") == "sha256" and type(request["number"]) is int
             and 0 <= request["number"] < 100_000_000, "challenge_solver")
        need(sha((request["salt"]+str(request["number"])).encode()) == request["challenge"].lower(), "challenge_solution")
    if result["creation"] == "CREATED":
        need(provision and provision["status"] == 200, "created_without_provision")
        raw = load(private_file(private, provision["body_file"]))
        key = raw.get("restricted_key") or raw.get("secret_key")
        account = raw.get("account_id") or raw.get("merchant_token")
        need(isinstance(key,str) and key.startswith("rkcs_test_") and isinstance(account,str) and account.startswith("acct_"), "anonymous_test_credentials")
        credentials = load(private_file(private, "CREDENTIALS.json"))
        need(credentials["key"] == key and credentials["account_id"] == account, "credential_snapshot_binding")
        need(result["account_ref"] == sha(account.encode()), "account_reference")
        for query in accounts:
            need(stamp(query["started_at"]) >= stamp(provision["finished_at"]), "account_query_order")
            if query["status"] == 200:
                need(load(private_file(private, query["body_file"]))["id"] == account, "foreign_account")
    else:
        need(result["account_ref"] is None and not accounts, "uncreated_account_claim")
        need(result["decision"] != "ELIGIBLE", "false_eligibility")
        if result["creation"] == "UNKNOWN":
            need(provision is not None and result["decision"] == "UNKNOWN_PROVISION_RESULT", "unknown_creation")
        if result["creation"] == "NOT_SENT":
            need(provision is None, "creation_attempt_not_recorded")
    listener = material["listener"]
    need(set(spec["listener_fields"]) <= set(listener), "listener_fields")
    need(int(bool(listener["attempted"])) == counts.get("listener",0), "listener_ledger_mismatch")
    if counts.get("local_server",0):
        need(listener.get("receiver_stopped") is True, "receiver_cleanup")
    if listener["attempted"]:
        need(counts.get("local_server",0) == 1, "receiver_ledger_missing")
        need(result["creation"] == "CREATED" and any(q["status"] == 200 for q in accounts), "listener_precondition")
        need(listener["stopped"] is True and listener.get("receiver_stopped") is True
             and listener["test_mode"] is True and listener["config_isolated"] is True
             and listener["key_in_argv"] is False, "listener_isolation_or_cleanup")
        need(listener["archive_sha256"] == spec["cli"]["archive_sha256"], "cli_release_digest")
        archive = private_file(private, listener.get("archive_file"), 64*1024*1024)
        need(archive.stat().st_size == spec["cli"]["archive_bytes"]
             and sha(archive.read_bytes()) == spec["cli"]["archive_sha256"], "cli_archive_bytes")
        stdout = private_file(private, listener["stdout_file"]).read_bytes()
        stderr = private_file(private, listener["stderr_file"]).read_bytes()
        if listener["ready"]:
            need(b"Ready!" in stdout+stderr and re.search(rb"whsec_[A-Za-z0-9]+", stdout+stderr), "listener_ready_evidence")
    else:
        need(listener["ready"] is False, "listener_not_run")
    if result["decision"] == "ELIGIBLE":
        need(result["stage"] == "complete" and result["creation"] == "CREATED"
             and any(q["status"] == 200 for q in accounts) and listener["attempted"] and listener["ready"], "eligibility_evidence_missing")
    return result, material, private


def append(kind, event, ident, **values):
    rows = ledger()
    row = {"seq":len(rows)+1,"kind":kind,"event":event,"attempt_id":ident,
           "at":datetime.now(timezone.utc).isoformat(), **values}
    with (PACK/"ATTEMPT_LEDGER.jsonl").open("ab") as out:
        out.write((json.dumps(row, sort_keys=True)+"\n").encode())
        out.flush()
        os.fsync(out.fileno())


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def readback(actor):
    integrity()
    result, material, private = inspect_material()
    if result["creation"] != "CREATED":
        print("H69 no confirmed account; raw stopped/unknown attempt re-audited, no POST or GET repeated")
        return
    need(datetime.now(timezone.utc) <= stamp(load(PACK/"SPEC.json")["original_deadline"]), "original_authorization_expired")
    current = (ROOT/"CURRENT.md").read_text(encoding="utf-8")
    nonce = os.environ.get("H69_EVALUATOR_NONCE", "") if actor == "evaluator" else "executor"
    if actor == "evaluator":
        need("current_role: Evaluator" in current and len(nonce) >= 32, "independent_evaluator_nonce_required")
    marker = PACK/"evidence"/("READBACK_"+actor+".json")
    fingerprint = sha(nonce.encode())
    if marker.exists():
        saved = load(marker)
        need(saved["nonce_sha256"] == fingerprint and saved["run_id"] == result["run_id"], "readback_marker_conflict")
        need(saved["checker_sha256"] == sha(Path(__file__).read_bytes()), "readback_checker_conflict")
        raw = (private/("READBACK_"+actor+".bin")).read_bytes()
        need(sha(raw) == saved["body_sha256"], "readback_body_changed")
        if saved["status"] == 200:
            credentials = load(private_file(private, "CREDENTIALS.json"))
            need(saved["matched"] is True and json.loads(raw)["id"] == credentials["account_id"], "readback_foreign_account")
        need(saved["status"] == 200 or result["decision"] != "ELIGIBLE", "readback_not_qualified")
        print("H69 existing actor-specific readback retained; no repeated request")
        return
    kind = actor+"_readback"
    counts = budget()
    need(counts.get(kind,0) < 2, "readback_budget")
    credentials = load(private_file(private, "CREDENTIALS.json"))
    key, account = credentials["key"], credentials["account_id"]
    need(key.startswith("rkcs_test_"), "readback_non_test_key")
    ident = "h69-"+actor+"-readback-"+str(counts.get(kind,0)+1)
    append(kind,"BEGIN",ident)
    status, body, error = None, b"", None
    try:
        request = Request("https://api.stripe.com/v1/account", headers={
            "Authorization":"Bearer "+key,"Stripe-Version":"2026-10-28.endive"}, method="GET")
        with build_opener(NoRedirect()).open(request,timeout=30) as response:
            status, body = response.status, response.read(2*1024*1024+1)
    except HTTPError as exc:
        status, body = exc.code, exc.read(2*1024*1024+1)
    except (URLError, TimeoutError, OSError):
        error = "NETWORK"
    finally:
        append(kind,"END",ident,status="SUCCEEDED" if status == 200 else "INPUT_LIMIT")
    need(len(body) <= 2*1024*1024, "readback_response_size")
    raw_path = private/("READBACK_"+actor+".bin")
    raw_path.write_bytes(body)
    matched = status == 200 and json.loads(body)["id"] == account
    if status == 200:
        need(matched, "readback_foreign_account")
    marker.parent.mkdir(parents=True,exist_ok=True)
    marker.write_text(json.dumps({"actor":actor,"run_id":result["run_id"],"nonce_sha256":fingerprint,
        "checker_sha256":sha(Path(__file__).read_bytes()),"status":status,"error":error,
        "body_sha256":sha(body),"matched":matched},indent=2)+"\n",encoding="utf-8")
    need(matched or result["decision"] != "ELIGIBLE", "eligibility_readback_unavailable")
    print("H69 independent own-account readback recorded; no payment actions")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command",choices=("integrity","artifacts","readback","budget"))
    parser.add_argument("--actor",choices=("executor","evaluator"),default="executor")
    parser.add_argument("--closed",action="store_true")
    args = parser.parse_args()
    if args.command == "integrity":
        integrity()
    elif args.command == "artifacts":
        inspect_material()
        print("H69 raw qualification evidence consistent; semantic source/transport review still required")
    elif args.command == "readback":
        readback(args.actor)
    else:
        budget(args.closed)
        print("H69 reported budget OK")


if __name__ == "__main__":
    try:
        main()
    except (Failed, OSError, ValueError, TypeError, KeyError, AssertionError, subprocess.SubprocessError):
        print("H69 CHECK FAILED; inspect private evidence locally, no private data printed",file=sys.stderr)
        raise SystemExit(1)

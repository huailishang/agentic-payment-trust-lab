"""Frozen offline structural checks; Evaluator must audit source semantics."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit
import hashlib
import json
import subprocess
import sys

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]

def need(value, code):
    if not value:
        raise ValueError(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def unique(pairs):
    result = {}
    for k,v in pairs:
        need(k not in result, "duplicate_key")
        result[k] = v
    return result

def load(path):
    need(path.stat().st_size <= 4*1024*1024, "json_size")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)

def stamp(value):
    date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    need(date.tzinfo is not None, "timezone")
    return date

def allowed(url):
    lock = load(PACK/"SOURCE_LOCK.json")
    parsed = urlsplit(url)
    return (parsed.scheme == "https" and parsed.hostname in lock["source_hosts"]
            and parsed.username is None and parsed.password is None and parsed.port in (None,443)
            and (parsed.hostname == "docs.stripe.com" or url.startswith(lock["raw_prefix"])))

def integrity():
    b = load(PACK/"BASELINE.json")
    head = subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    need(head == b["head"], "head_changed")
    for rel,digest in b["protected"].items():
        need((ROOT/rel).is_file() and sha((ROOT/rel).read_bytes()) == digest, "protected_changed")
    for rel,digest in b["frozen"].items():
        need(sha((PACK/rel).read_bytes()) == digest, "frozen_changed")
    current = (ROOT/"CURRENT.md").read_text(encoding="utf-8")
    need("task_id: "+PACK.name in current, "wrong_task")
    for name in ("commit","push","history_rewrite","api_call"):
        need("authorization_"+name+": false" in current, "authority_expanded")
    out = subprocess.run(["git","ls-files","--others","--exclude-standard","-z"],cwd=ROOT,capture_output=True,check=True).stdout
    prefix = PACK.relative_to(ROOT).as_posix()+"/"
    for raw in out.split(b"\0"):
        if not raw:
            continue
        rel = raw.decode("utf-8")
        need(rel in b["inherited_untracked"] or rel.startswith(prefix), "out_of_scope_file")
        if rel.startswith(prefix):
            child = rel[len(prefix):]
            need(child in set(b["frozen"]) | {"BASELINE.json","RUN.py","REPORT.md","REVIEW.md","RESULT.json","PERMISSION_MATRIX.json","SOURCE_MANIFEST.json","ATTEMPT_LEDGER.jsonl"}
                 or child.startswith(("sources/","evidence/")), "out_of_scope_output")
    print("H70 frozen inputs, prior evidence and authority intact")

def sources():
    manifest = load(PACK/"SOURCE_MANIFEST.json")
    entries = manifest["sources"]
    need(isinstance(entries,list), "sources_array")
    values = {}
    for row in entries:
        need(row["id"] not in values and allowed(row["url"]), "source_identity")
        path = (PACK/row["file"]).resolve()
        need(path.is_relative_to(PACK/"sources") and path.is_file(), "source_path")
        raw = path.read_bytes()
        need(len(raw) == row["bytes"] and sha(raw) == row["sha256"] and row["status"] == 200, "source_bytes")
        need(stamp(row["finished_at"]) >= stamp(row["started_at"]), "source_timing")
        values[row["id"]] = raw.decode("utf-8")
    matrix = load(PACK/"PERMISSION_MATRIX.json")
    lock = load(PACK/"SOURCE_LOCK.json")
    need(sorted(r["id"] for r in matrix["rows"]) == sorted(lock["matrix_ids"]), "matrix_coverage")
    for row in matrix["rows"]:
        for key in ("operation","key_family","observed","documented","unknown"):
            need(isinstance(row[key],str) and row[key].strip(), "matrix_field")
        need(isinstance(row["refs"],list), "refs_array")
        if not row["refs"]:
            need("UNKNOWN" in row["documented"], "unsourced_claim")
        for ref in row["refs"]:
            need(ref["source_id"] in values and isinstance(ref["quote"],str) and ref["quote"].strip()
                 and ref["quote"] in values[ref["source_id"]], "source_quote")
    print("H70 archived source bytes, four dimensions and exact references valid; semantic review required")

def artifacts():
    lock = load(PACK/"SOURCE_LOCK.json")
    result = load(PACK/"RESULT.json")
    need(result["task_id"] == PACK.name and result["decision"] in lock["decisions"], "result_identity")
    need(isinstance(result["rationale"],str) and result["rationale"].strip(), "rationale_missing")
    need(result["matrix_sha256"] == sha((PACK/"PERMISSION_MATRIX.json").read_bytes()), "matrix_binding")
    keys = {"runtime_api","credential_requests","cli_downloads","installs","browser_actions","local_services","checkout_sessions","payments","commits","pushes"}
    need(set(result["side_effects"]) == keys and all(type(x) is int and x == 0 for x in result["side_effects"].values()), "side_effects")
    rows = [json.loads(x,object_pairs_hook=unique) for x in (PACK/"ATTEMPT_LEDGER.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    need([r["seq"] for r in rows] == list(range(1,len(rows)+1)), "ledger_sequence")
    begin, end, counts, per_url = {}, {}, {}, {}
    for row in rows:
        need(row["event"] in {"BEGIN","END"}, "ledger_event")
        table = begin if row["event"] == "BEGIN" else end
        need(row["attempt_id"] not in table, "ledger_duplicate")
        table[row["attempt_id"]] = row
    need(set(end) <= set(begin), "ledger_begin_missing")
    intervals, active, body_bytes = [], [], 0
    now = datetime.now(timezone.utc)
    for ident,first in begin.items():
        kind = first["kind"]
        need(kind in {"active_work","implementation","source_http","l2","l3"}, "ledger_kind")
        counts[kind] = counts.get(kind,0)+1
        if kind != "active_work":
            need(counts[kind] <= lock["budgets"][kind], "attempt_budget")
        last = end.get(ident)
        need(last is not None or kind in {"active_work","l2","l3"}, "attempt_unclosed")
        start,finish = stamp(first["at"]), stamp(last["at"]) if last else now
        need(finish >= start, "ledger_time")
        if last:
            need(last["kind"] == kind and last["status"] in {"SUCCEEDED","FAILED","INPUT_LIMIT"}, "ledger_terminal")
        if kind == "active_work":
            active.append((start,finish))
        if kind == "source_http":
            need(allowed(first["url"]) and last is not None, "source_request")
            per_url[first["url"]] = per_url.get(first["url"],0)+1
            need(per_url[first["url"]] <= lock["budgets"]["per_url"], "source_repeat")
            need(type(last["body_bytes"]) is int and last["body_bytes"] >= 0, "source_body_count")
            need(last["status_code"] is None or type(last["status_code"]) is int, "source_status")
            body_bytes += last["body_bytes"]
            intervals.append((start,finish))
    intervals.sort(); active.sort()
    need(all(a[1] <= b[0] for a,b in zip(intervals,intervals[1:])), "concurrent_source_requests")
    need(active and all(a[1] <= b[0] for a,b in zip(active,active[1:])), "active_work_missing_or_overlap")
    need(sum((b-a).total_seconds() for a,b in active) <= lock["budgets"]["active_seconds"], "active_budget")
    need(body_bytes <= lock["budgets"]["body_bytes"], "source_byte_budget")
    if rows:
        terminal = max([stamp(r["at"]) for r in rows] + ([now] if set(begin)-set(end) else []))
        need((terminal-min(stamp(r["at"]) for r in rows)).total_seconds() <= lock["budgets"]["wall_seconds"], "wall_budget")
    # Every archived body must map to a scheduled successful request, not just a declared source URL.
    for source in load(PACK/"SOURCE_MANIFEST.json")["sources"]:
        need(any(first["kind"] == "source_http" and first.get("url") == source["url"]
                 and ident in end and end[ident]["status_code"] == 200
                 and end[ident]["body_bytes"] == source["bytes"] for ident,first in begin.items()), "source_ledger_binding")
    print("H70 result, reported budget and forbidden side-effect counts valid; independent transport audit required")

if __name__ == "__main__":
    try:
        {"integrity":integrity,"sources":sources,"artifacts":artifacts}[sys.argv[1]]()
    except (OSError,ValueError,KeyError,TypeError,AssertionError,subprocess.SubprocessError):
        print("H70 CHECK FAILED; inspect task artifacts locally",file=sys.stderr)
        raise SystemExit(1)

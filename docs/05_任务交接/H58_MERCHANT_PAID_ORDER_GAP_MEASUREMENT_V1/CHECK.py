"""Frozen independent reader of accepted evidence; never imports merchant runtime."""
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]

def read(p):
    return json.loads(p.read_text(encoding="utf-8"))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def inputs():
    lock = read(TASK / "INPUTS.json")
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == lock["head"]
    for n, h in lock["protected_files"].items():
        assert sha(ROOT / n) == h, n
    for n, h in lock["frozen_files"].items():
        assert sha(TASK / n) == h, n
    for n, h in lock["databases"].items():
        assert sha(ROOT / n) == h, n
    allowed = {"MEASURE.py", "MEASUREMENT.json", "ANALYSIS.json", "ANALYSIS.md", "RESULT.json", "ATTEMPT_LEDGER.json", "REPORT.md", "REVIEW.md", "INPUTS.json"}
    for p in TASK.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            n = p.relative_to(TASK).as_posix()
            assert n in lock["frozen_files"] or n in allowed or n.startswith("evidence/"), n
    print(json.dumps({"protected":len(lock["protected_files"]),"frozen":len(lock["frozen_files"]),"read_only_databases":len(lock["databases"])}))

def expected():
    lock = read(TASK / "INPUTS.json")
    obs = read(ROOT / lock["observations"])
    selected = [c for c in obs["cases"] if c["case"].startswith(("M01_", "M06_"))]
    summaries = []
    for c in selected:
        summaries.append({"case":c["case"],"http_statuses":[r["response_status"] for r in c["calls"]],"payment_calls":len(c["psp_calls"]),"orders":len(c["state"]["orders"]),"inventory":c["state"]["inventory"],"attempts":c["state"]["attempts"],"recovery":c.get("recovery"),"authorization_records":c["authorization_records"]})
    tables = {}
    for n in lock["databases"]:
        path = ROOT / n
        with sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True) as conn:
            conn.row_factory = sqlite3.Row
            names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
            tables[n] = {}
            for name in names:
                quoted = '"' + name.replace('"','""') + '"'
                rows = [dict(r) for r in conn.execute("SELECT * FROM " + quoted)]
                tables[n][name] = sorted(rows,key=lambda r:json.dumps(r,sort_keys=True))
    return {"cases":summaries,"m06_persisted_tables":tables}

TOPICS = ["checkout_identity", "payment_reference_and_status", "amount_currency_payee", "line_items_and_fulfillment", "inventory_after_rollback", "confirmation_scope_and_revocation", "authorization_evidence", "original_request_and_idempotency", "order_id_and_end_state", "trust_configuration_after_restart", "compensation_authority", "audit_responsibility"]

def validate_analysis(v):
    assert v["schema"] == "h58-analysis/v1"
    rows = v["topics"]
    assert [r["id"] for r in rows] == TOPICS
    for r in rows:
        assert r["availability"] in {"PERSISTED", "TEST_HANDOFF_ONLY", "MISSING", "MIXED"}
        assert r["basis"] in {"measured", "estimated", "unknown"}
        assert isinstance(r["sufficient_for_automatic_action"], bool)
        assert r["finding"] and r["residual_risk"]
        assert r["evidence"]
        for e in r["evidence"]:
            # Explicit path + locator + literal observed value; reviewed manually.
            assert set(e) >= {"path", "locator", "observed"}
            path = (ROOT/e["path"]).resolve()
            assert path.is_relative_to(ROOT) and path.is_file()
            assert e["locator"] and e["observed"] is not None
    assert [m["id"] for m in v["mechanisms"]] == ["KEEP_QUERY_ONLY", "ORDER_COMPLETION_CANDIDATE", "COMPENSATION_OR_MANUAL_CANDIDATE"]
    for m in v["mechanisms"]:
        assert m["classification"] in {"ABSORB", "REFERENCE_ONLY", "REJECT"}
        assert m["not_executed"] is True
        for k in ("prerequisites", "safety", "authority", "complexity_cost", "failure_or_stop_condition"):
            assert m[k]
    assert v["next_decision"] in {"BOUNDED_RECOVERY_CANDIDATE", "MISSING_DURABLE_INPUT", "HUMAN_POLICY_REQUIRED"}
    assert v["next_decision_basis"] and v["missing_facts"]
    assert v["automatic_recovery_proven"] is False
    assert v["production_ready"] is False and v["customer_value_proven"] is False

def outputs(role):
    folder = TASK/"evidence"/role
    a,b = read(folder/"measurement_1.json"),read(folder/"measurement_2.json")
    target = expected()
    assert a == b == target
    if role == "executor":
        assert read(TASK/"MEASUREMENT.json") == target
    validate_analysis(read(TASK/"ANALYSIS.json"))
    prose=(TASK/"ANALYSIS.md").read_text(encoding="utf-8")
    assert len(prose)>300 and "H56" in prose
    ledger=read(TASK/"ATTEMPT_LEDGER.json")
    assert 0<=ledger["active_work_minutes"]<=120
    attempts_path = TASK/"evidence/executor/MEASUREMENT_ATTEMPTS.jsonl"
    attempts = [json.loads(s) for s in attempts_path.read_text(encoding="utf-8").splitlines()]
    assert len({r["attempt_id"] for r in attempts})==len(attempts)
    assert ledger["measurement_passes"]==len(attempts)<=8
    assert all(r["role"]=="executor" and r["utc"] for r in attempts)
    if role=="evaluator":
        ev=[json.loads(s) for s in (folder/"MEASUREMENT_ATTEMPTS.jsonl").read_text(encoding="utf-8").splitlines()]
        assert len(ev)<=4 and len({r["attempt_id"] for r in ev})==len(ev)
        assert all(r["role"]=="evaluator" and r["utc"] for r in ev)
    assert ledger["formal_l2_attempts"]==len(list((TASK/"evidence").glob("l2_executor_*")))<=2
    for k in ("http_requests","payment_calls","recovery_calls","network_calls","model_calls","packages_installed","git_write_operations"):
        assert ledger[k]==0
    assert ledger["work_intervals_utc"]
    for interval in ledger["work_intervals_utc"]:
        assert interval["start"] and interval["end"] and interval["start"]<=interval["end"]
    result=read(TASK/"RESULT.json")
    assert result["task_id"]==TASK.name and result["classification"]==read(TASK/"ANALYSIS.json")["next_decision"]
    assert result["measurement_only"] is True and result["business_recovery_executed"] is False
    assert result["customer_demand"]=="UNKNOWN"
    print(json.dumps({"case_count":2,"repeats_equal":True,"database_facts_equal":True,"analysis_requires_manual_review":True,"role":role}))

def selftest():
    # No runtime execution or synthetic business success is inferred here.
    base={"schema":"h58-analysis/v1","topics":[{"id":t,"availability":"MISSING","basis":"unknown","sufficient_for_automatic_action":False,"finding":"selftest","residual_risk":"unknown","evidence":[{"path":str(Path(__file__).relative_to(ROOT)),"locator":"selftest","observed":"schema-only"}]} for t in TOPICS],"mechanisms":[{"id":m,"classification":"REFERENCE_ONLY","not_executed":True,**{k:"selftest" for k in ("prerequisites","safety","authority","complexity_cost","failure_or_stop_condition")}} for m in ("KEEP_QUERY_ONLY","ORDER_COMPLETION_CANDIDATE","COMPENSATION_OR_MANUAL_CANDIDATE")],"next_decision":"HUMAN_POLICY_REQUIRED","next_decision_basis":"selftest","missing_facts":["unknown"],"automatic_recovery_proven":False,"production_ready":False,"customer_value_proven":False}
    validate_analysis(base)
    bad=[]
    v=copy.deepcopy(base);v["topics"]=v["topics"][:-1];bad.append(v)
    v=copy.deepcopy(base);v["topics"][0]["evidence"]=[];bad.append(v)
    v=copy.deepcopy(base);v["topics"][0]["availability"]="PROVEN";bad.append(v)
    v=copy.deepcopy(base);v["mechanisms"][1]["not_executed"]=False;bad.append(v)
    v=copy.deepcopy(base);v["automatic_recovery_proven"]=True;bad.append(v)
    v=copy.deepcopy(base);v["next_decision"]="DEPLOY";bad.append(v)
    for v in bad:
        try:
            validate_analysis(v)
        except AssertionError:
            pass
        else:
            raise AssertionError("corrupt analysis passed")
    print(json.dumps({"rejected_corruptions":len(bad),"business_executed":False}))

if __name__ == "__main__":
    if sys.argv[1]=="outputs":
        outputs(sys.argv[2])
    else:
        {"inputs":inputs,"selftest":selftest}[sys.argv[1]]()

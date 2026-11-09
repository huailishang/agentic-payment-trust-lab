"""Frozen H48 controller/oracle. The Executor supplies only PROJECTOR.py.

No network or provider; reuse the accepted H47 full merchant and environment.
The oracle describes the limited synthetic domain contract, not production UCP.
"""
from __future__ import annotations
import argparse
import copy
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
PARENT = TASK.parent / "H47_UCP_COMMERCE_APPLICABILITY_V1"
sys.path.insert(0, str(ROOT / "src"))
from agentic_payment_experiment.models import Order, OrderItem
from agentic_payment_experiment.trusted_execution.confirmation import (
    confirmation_order_payload, create_confirmation_record,
    verify_confirmation_binding, execute_with_confirmation_gate,
)
from agentic_payment_experiment.trusted_execution.hashing import canonical_hash

TASK_ID = "H48_UCP_CONFIRMATION_SEAM_PROBE_V1"
MUTABLE = {"PROJECTOR.py", "INPUT_LINEAGE.md", "ANALYSIS.md", "DEMO.md", "RESULT.json",
           "ATTEMPT_LEDGER.json", "REPORT.md"}
NOW = datetime(2026, 10, 15, tzinfo=timezone.utc)
CASES = ["N01_NATIVE_CHANGED", "G01_NORMAL", "G02_CHANGED_BEFORE",
         "G03_MISSING_PAYEE", "G04_MISSING_AUTHORITY", "G05_EXPIRED",
         "G06_MISSING_CURRENCY", "L01_UPDATE_AFTER_CHECK", "L02_DIRECT_BYPASS"]


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((TASK / name).read_text(encoding="utf-8"))


def workspace_files():
    raw = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT)
    return {x.decode("utf-8") for x in raw.split(b"\0") if x}


def baseline():
    import yaml
    lock = read("BASELINE.json")
    current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    route = yaml.safe_load(current.split("```yaml", 1)[1].split("```", 1)[0])
    require(route["task_id"] == TASK_ID and route["task_kind"] == "one_off", "wrong task")
    require(route["project_map_revision"] == "2026-10-15-r76" and route["active_bottleneck_id"] == "B-17"
            and route["hypothesis_id"] == "H-48", "map linkage drift")
    require((route["state"], route["current_role"]) in {("CONTRACT_FROZEN", "Executor"),
            ("EXECUTING", "Executor"), ("READY_FOR_REVIEW", "Evaluator")}, "wrong phase")
    require(all(route["authorization_" + x] is False for x in ["api_call", "commit", "push", "history_rewrite"]), "authority drift")
    narrative = current.split("## Global position", 1)[1]
    require(hashlib.sha256(narrative.encode()).hexdigest() == lock["current_narrative_sha256"], "CURRENT history changed")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == lock["head"], "HEAD drift")
    for name, expected in lock["protected_files"].items():
        require((ROOT / name).is_file() and sha(ROOT / name) == expected, "protected drift: " + name)
    for name, expected in lock["frozen_files"].items():
        require(sha(TASK / name) == expected, "frozen task drift: " + name)
    prefix = TASK.relative_to(ROOT).as_posix() + "/"
    require(all(x.startswith(prefix) for x in workspace_files() - set(lock["workspace_files"])), "new file outside task")
    for path in TASK.rglob("*"):
        if path.is_file():
            name = path.relative_to(TASK).as_posix()
            require(name == "BASELINE.json" or name in lock["frozen_files"] or name in MUTABLE
                    or name.startswith("evidence/") or "__pycache__/" in name, "unlisted task file: " + name)
    env = json.loads((PARENT / "ENVIRONMENT.json").read_text(encoding="utf-8"))
    require(sys.version_info[:2] == (3, 12) and sys.prefix != sys.base_prefix, "H47 task-local Python required")
    for name, version in env["packages"].items():
        require(importlib.metadata.version(name) == version, "dependency drift: " + name)
    print(json.dumps({"baseline": "PASS", "protected_files": len(lock["protected_files"]),
                      "frozen_files": len(lock["frozen_files"])}))


def load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def runtime():
    return load_file("h48_parent_runtime", PARENT / "FROZEN_RUNTIME.py")


def load_projector():
    # Runtime import installs no lasting socket bypass; protect import/execution too.
    from unittest.mock import patch
    rt = runtime()
    with patch("socket.socket.connect", rt.deny_socket), patch("socket.create_connection", rt.deny_socket):
        module = load_file("h48_executor_projector", TASK / "PROJECTOR.py")
    require(callable(getattr(module, "project_checkout", None)), "missing pure projection interface")
    return module.project_checkout


def text_value(mapping, key):
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(key)
    return value


def integer(value, positive=False):
    if type(value) is not int or value < (1 if positive else 0):
        raise ValueError("integer minor units/quantity required")
    return value


def expected_order(snapshot, trust):
    """Independent gold for the deliberately narrow fixture; no merchant writes."""
    checkout_id = text_value(snapshot, "id")
    if snapshot.get("currency") != "USD":
        raise ValueError("only explicit USD supported")
    values = {key: text_value(trust, key) for key in ["merchant", "payee", "authority_id",
        "authority_version", "quote_expires_at", "fulfilment_terms", "service_id"]}
    expiry = datetime.fromisoformat(values["quote_expires_at"])
    if expiry.tzinfo is None or expiry.utcoffset() is None:
        raise ValueError("timezone required")
    totals = [x for x in snapshot.get("totals", []) if x.get("type") == "total"]
    if len(totals) != 1:
        raise ValueError("unique total required")
    total = Decimal(integer(totals[0].get("amount"))) / Decimal(100)
    items = []
    for line in snapshot.get("line_items", []):
        item = line["item"]
        item_id = text_value(item, "id")
        category = text_value(trust.get("category_by_item", {}), item_id)
        items.append(OrderItem(item_id, text_value(item, "title"), category,
            integer(line.get("quantity"), positive=True), Decimal(integer(item.get("price"))) / Decimal(100)))
    if not items or len({x.item_id for x in items}) != len(items):
        raise ValueError("nonempty unique items required")
    order = Order(order_id="h48-checkout:" + checkout_id, order_version="",
        merchant=values["merchant"], payee=values["payee"], items=tuple(items),
        total_amount=total, currency="USD", quote_expires_at=expiry,
        fulfilment_terms=values["fulfilment_terms"], mandate_ref=values["authority_id"],
        service_id=values["service_id"], candidate_rails=(), authority_version_ref=values["authority_version"])
    return replace(order, order_version=canonical_hash(confirmation_order_payload(order)))


def oracle_result(snapshot, trust):
    try:
        order = expected_order(snapshot, trust)
        missing = []
    except (ValueError, KeyError, TypeError):
        order, missing = None, ["invalid_or_missing_fixture_input"]
    return {"order": order, "checkout_ref": snapshot.get("id"), "final_order_ref": None, "missing": missing}


def checked_projection(fn, snapshot, trust):
    before_snapshot, before_trust = copy.deepcopy(snapshot), copy.deepcopy(trust)
    from unittest.mock import patch
    rt = runtime()
    with patch("socket.socket.connect", rt.deny_socket), patch("socket.create_connection", rt.deny_socket):
        result = fn(snapshot, trust)
    require(snapshot == before_snapshot and trust == before_trust, "projection mutated input")
    require(isinstance(result, dict), "projection result must be dict")
    expected = oracle_result(snapshot, trust)
    require(result.get("checkout_ref") == snapshot.get("id") and result.get("final_order_ref") is None, "reference relabeling")
    if expected["order"] is None:
        require(result.get("order") is None and isinstance(result.get("missing"), list)
                and bool(result["missing"]) and all(isinstance(x, str) and x.strip() for x in result["missing"]), "missing input silently filled")
    else:
        require(isinstance(result.get("order"), Order) and result["order"] == expected["order"], "unfaithful order projection")
        require(result.get("missing") == [], "valid input rejected")
    return result


def fixture_snapshot():
    # Accepted real H47 response, used only for offline malformed-input checks.
    data = json.loads((PARENT / "evidence/measurements_l3.json").read_text(encoding="utf-8"))
    return copy.deepcopy(data["cases"][0]["calls"][0]["merchant_response"])


def malformed(fn):
    good, trust = fixture_snapshot(), read("TRUST_FIXTURE.json")
    checked_projection(fn, copy.deepcopy(good), copy.deepcopy(trust))
    bad = []
    for key in ["payee", "authority_id"]:
        t = copy.deepcopy(trust); t.pop(key); bad.append((good, t))
    for value in [None, "CNY"]:
        s = copy.deepcopy(good); s["currency"] = value; bad.append((s, trust))
    for value in ["1000", True, -1]:
        s = copy.deepcopy(good)
        next(x for x in s["totals"] if x["type"] == "total")["amount"] = value
        bad.append((s, trust))
    s = copy.deepcopy(good); s["totals"].append({"type": "total", "amount": 1000}); bad.append((s, trust))
    s = copy.deepcopy(good); s["line_items"][0].pop("quantity"); bad.append((s, trust))
    s = copy.deepcopy(good); s["line_items"][0]["quantity"] = 0; bad.append((s, trust))
    t = copy.deepcopy(trust); t["category_by_item"] = {}; bad.append((good, t))
    s = copy.deepcopy(good); s["line_items"][0]["item"].pop("title"); bad.append((s, trust))
    for snapshot, cfg in bad:
        checked_projection(fn, copy.deepcopy(snapshot), copy.deepcopy(cfg))
    require(len(bad) == 12, "malformed matrix drift")
    print(json.dumps({"positive_projection": True, "invalid_inputs_rejected": len(bad)}))


def oracle_selftest():
    good, trust = fixture_snapshot(), read("TRUST_FIXTURE.json")
    rejected = 0
    def corrupt(field, value):
        def fn(snapshot, cfg):
            result = oracle_result(snapshot, cfg)
            result["order"] = replace(result["order"], **{field: value})
            return result
        return fn
    variants = [lambda s, t: {"order": None, "checkout_ref": s["id"], "final_order_ref": None, "missing": ["all_blocked"]},
        corrupt("total_amount", Decimal("1000")), corrupt("payee", "merchant-derived-placeholder"),
        corrupt("order_id", good["id"]), corrupt("order_version", good["ucp"]["version"])]
    for fn in variants:
        try:
            checked_projection(fn, copy.deepcopy(good), copy.deepcopy(trust))
        except AssertionError:
            rejected += 1
    require(rejected == len(variants), "oracle accepted a corrupt projection")
    print(json.dumps({"checker_corrupt_projection_rejections": rejected}))


def observe_case(fn, name, repeat):
    rt = runtime()
    trust = read("TRUST_FIXTURE.json")
    if name == "G03_MISSING_PAYEE":
        trust.pop("payee")
    if name == "G04_MISSING_AUTHORITY":
        trust.pop("authority_id")
    with rt.Merchant() as ctx:
        initial = ctx.request("create", key="h48-create")
        require(ctx.calls[-1]["response_status"] == 201, "native create failed")
        projected = checked_projection(fn, copy.deepcopy(initial), trust)
        record = None
        if projected["order"] is not None:
            record = create_confirmation_record(confirmation_id="h48-confirmation", authority_id=trust["authority_id"],
                authority_version=trust["authority_version"], order=projected["order"],
                confirmed_at=NOW, expires_at=NOW + timedelta(minutes=5))
        if name in {"N01_NATIVE_CHANGED", "G02_CHANGED_BEFORE", "L02_DIRECT_BYPASS"}:
            ctx.request("update", quantity=2, key="h48-update-before")
        current = ctx.request("query")
        if name == "G06_MISSING_CURRENCY":
            current = copy.deepcopy(current); current.pop("currency")
        current_projection = checked_projection(fn, current, trust)
        fact = verify_confirmation_binding(record, current_projection["order"],
            authority_id=trust.get("authority_id"), authority_version=trust.get("authority_version"),
            checked_at=NOW + timedelta(minutes=6 if name == "G05_EXPIRED" else 1))
        calls_at_check = len(ctx.calls)
        if name == "L01_UPDATE_AFTER_CHECK":
            require(fact.status.value == "VALID", "race must start with a real valid check")
            ctx.request("update", quantity=2, key="h48-update-after")
        if name in {"N01_NATIVE_CHANGED", "L02_DIRECT_BYPASS"}:
            ctx.request("complete", key="h48-complete")
            decision, executed = "BYPASSED_LOCAL_CONFIRMATION", None
        else:
            outcome = execute_with_confirmation_gate(fact, lambda: ctx.request("complete", key="h48-complete"))
            decision, executed = outcome.decision.value, outcome.executed
        state, calls = ctx.state(), copy.deepcopy(ctx.calls)
        complete_count = sum(x["operation"] == "complete" for x in calls)
        should_complete = name in {"N01_NATIVE_CHANGED", "G01_NORMAL", "L01_UPDATE_AFTER_CHECK", "L02_DIRECT_BYPASS"}
        stock = 3 if name in {"N01_NATIVE_CHANGED", "L01_UPDATE_AFTER_CHECK", "L02_DIRECT_BYPASS"} else (4 if should_complete else 5)
        require(state["payment_calls"] == int(should_complete) and complete_count == int(should_complete), "callback/payment count mismatch")
        require(len(state["orders"]) == int(should_complete) and state["inventory"][0]["quantity"] == stock, "native persisted state mismatch")
        if name == "G02_CHANGED_BEFORE":
            require(fact.status.value == "INVALID" and decision == "CONFIRMATION_REQUIRED", "changed content must require confirmation")
        if name in {"G03_MISSING_PAYEE", "G04_MISSING_AUTHORITY", "G06_MISSING_CURRENCY"}:
            require(fact.status.value == "MISSING_EVIDENCE" and decision == "INDETERMINATE", "missing must not execute")
        if name == "G05_EXPIRED":
            require(fact.status.value == "INVALID" and not executed, "expired must block")
        if name in {"G01_NORMAL", "L01_UPDATE_AFTER_CHECK"}:
            require(fact.status.value == "VALID" and executed, "positive control must execute")
        final_ref = calls[-1]["merchant_response"].get("order", {}).get("id") if should_complete else None
        require(not should_complete or bool(final_ref), "final native order reference missing")
        return {"case": name, "repeat": repeat, "initial_checkout": initial,
            "trust_source": "SYNTHETIC_TEST_CONFIGURATION", "confirmation": asdict(record) if record else None,
            "checked_order": asdict(current_projection["order"]) if current_projection["order"] else None,
            "fact": asdict(fact), "decision": decision, "executed": executed,
            "calls_at_check": calls_at_check, "calls": calls, "final_state": state,
            "final_merchant_order_ref": final_ref,
            "summary": {"case": name, "fact_status": fact.status.value, "reason": fact.reason,
                "decision": decision, "executed": executed, "complete_calls": complete_count,
                "payment_calls": state["payment_calls"], "order_count": len(state["orders"]),
                "stock": stock, "checked_quantity": current_projection["order"].items[0].quantity if current_projection["order"] else None,
                "http_statuses": [x["response_status"] for x in calls]}}


def measurement(out):
    require(bool(out), "output required")
    fn = load_projector()
    rows = [observe_case(fn, name, repeat) for repeat in range(2) for name in CASES]
    require([x["summary"] for x in rows[:9]] == [x["summary"] for x in rows[9:]], "nonrepeatable summary")
    count = sum(len(x["calls"]) for x in rows)
    require(count <= 80, "per-run request budget exceeded")
    value = {"schema": "h48-observations/v1", "boundary": "FULL_PINNED_ASGI_SYNTHETIC_TRUST_P1_ONLY",
             "asgi_requests": count, "cases": rows}
    path = ROOT / out
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    rendered = json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n"
    path.with_name(path.stem + "_" + stamp + ".raw.json").write_text(rendered, encoding="utf-8")
    path.write_text(rendered, encoding="utf-8")
    print(json.dumps({"cases": len(rows), "asgi_requests": count, "summaries": [x["summary"] for x in rows[:9]]}))


def artifacts(observations):
    rows = json.loads((ROOT / observations).read_text(encoding="utf-8"))
    require(len(rows["cases"]) == 18 and {x["case"] for x in rows["cases"]} == set(CASES), "incomplete observations")
    result = read("RESULT.json")
    require(result.get("schema") == "h48-result/v1" and result.get("classification") == "CLIENT_GUARD_ONLY", "unsupported classification")
    for key in ["product_improved", "production_adapter_ready", "provider_proof_verified", "customer_demand_validated",
                "third_party_verified", "atomic_snapshot_binding_proven", "model_attack_measured"]:
        require(result.get(key) is False, "overclaim: " + key)
    require(result.get("full_product_gate_comparison") == "NOT_MEASURED", "full gate overclaim")
    require(result.get("customer_demand") == "UNKNOWN", "customer assumption")
    for key in ["reason", "strongest_alternative", "next_question"]:
        require(isinstance(result.get(key), str) and len(result[key].strip()) >= 20, "missing decision reason")
    for name in ["INPUT_LINEAGE.md", "ANALYSIS.md", "DEMO.md", "REPORT.md"]:
        value = (TASK / name).read_text(encoding="utf-8")
        require(len(value.strip()) >= 200 and "TODO" not in value, "incomplete document: " + name)
    report = (TASK / "REPORT.md").read_text(encoding="utf-8")
    require(TASK_ID in report and "SUBMITTED_FOR_REVIEW" in report and "7831d232" in report, "report identity/status")
    ledger = read("ATTEMPT_LEDGER.json")
    require(1 <= ledger.get("formal_l2_attempts", 0) <= 3 and rows["asgi_requests"] <= ledger.get("asgi_requests", -1) <= 600,
            "attempt/request budget invalid")
    require(0 <= ledger.get("active_work_minutes", -1) <= 480, "time budget invalid")
    require(all(ledger.get(x) == 0 for x in ["external_runtime_calls", "model_calls", "provider_calls"]), "external authority exceeded")
    print("artifacts, bounded result and declared costs verified; semantic prose requires manual review")


def regressions():
    baseline()
    for folder, pattern in [("tests/trusted_execution", "test_confirmation.py"), ("tests", "test_webshop_runtime_gate.py")]:
        result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", folder, "-p", pattern],
            cwd=ROOT, env=os.environ | {"PYTHONPATH": "src"}, capture_output=True, text=True, check=True)
        output = result.stdout + result.stderr
        print(output)
        match = re.search(r"Ran (\d+) tests?", output)
        require(match and int(match.group(1)) > 0, "zero regression tests")
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
    baseline()


def prepare():
    # Evaluator-only readiness: do not write the Executor projector or task outputs.
    malformed(oracle_result)
    oracle_selftest()
    rows = [observe_case(oracle_result, name, 0) for name in ["G01_NORMAL", "G02_CHANGED_BEFORE", "L01_UPDATE_AFTER_CHECK"]]
    print(json.dumps({"preparation_only": True, "not_executor_result": True,
        "asgi_requests": sum(len(x["calls"]) for x in rows), "summaries": [x["summary"] for x in rows]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["baseline", "measurement", "malformed", "artifacts", "regressions", "prepare"])
    parser.add_argument("--out")
    parser.add_argument("--observations")
    args = parser.parse_args()
    {"baseline": baseline, "measurement": lambda: measurement(args.out),
     "malformed": lambda: (malformed(load_projector()), oracle_selftest()), "artifacts": lambda: artifacts(args.observations),
     "regressions": regressions, "prepare": prepare}[args.mode]()

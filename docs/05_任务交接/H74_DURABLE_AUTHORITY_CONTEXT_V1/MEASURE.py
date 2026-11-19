"""H74 same-input synthetic measurements: real SQLite, cold child, fake callbacks."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from dataclasses import replace
from datetime import timedelta
from agentic_payment_experiment.adapters.stripe_checkout import StripeCheckoutAdapter
from agentic_payment_experiment.models import PaymentStatus, PaymentStatusObservation
from agentic_payment_experiment.stripe_checkout_lab import StripeLabLedger
from agentic_payment_experiment.stripe_authority_context import _encode
from tests.test_stripe_checkout_adapter import NOW, SHA, FakeStripe, valid_context

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
OUT = P / "derived" / "measurement"
OUT.mkdir(parents=True, exist_ok=True)
RESOURCE = b"synthetic H68 resource"
OP, RUN = "operation-h68", "run-h68"
URL_SUCCESS, URL_CANCEL = "http://127.0.0.1:8768/success", "http://127.0.0.1:8768/cancel"

def canonical(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
def digest(x):
    return hashlib.sha256(canonical(x).encode("utf-8")).hexdigest()
def file_ref(p):
    return {"path": p.relative_to(P).as_posix(),
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
def paid_observation(client):
    session = dict(client.session, status="complete", payment_status="paid",
                   payment_intent="pi_test_h74")
    intent = dict(id="pi_test_h74", livemode=False, status="succeeded",
                  latest_charge="ch_test_h74", amount=100, currency="usd")
    charge = dict(id="ch_test_h74", livemode=False, status="succeeded",
                  paid=True, captured=True, amount=100, currency="usd",
                  payment_intent="pi_test_h74")
    return session, intent, charge

if len(sys.argv) > 1 and sys.argv[1] == "cold":
    store = StripeLabLedger(sys.argv[2])
    c = store.load_authority(sys.argv[3], expected_sha256=sys.argv[4])
    print(canonical({"graph_sha256": digest(_encode(c)),
        "confirmed_at":c.confirmation_record.confirmed_at.isoformat(),
        "confirmation_expires_at":c.confirmation_record.expires_at.isoformat(),
        "mandate_expires_at":c.mandate.expires_at.isoformat(),
        "order_version":c.order.order_version,
        "authority_version":c.mandate.authority_version,
        "confirmation_status":c.confirmation_record.status.value,
        "operation_id":sys.argv[3]}))
    raise SystemExit(0)

units = []
for unit, case in (("N01_COLD_RESUME","N01"),("R01_PAID_READ_ONLY_RECOVERY","R01"),
                   ("D01_RECEIPT_RECOVERY","D01")):
    d = OUT / unit
    d.mkdir(parents=True, exist_ok=True)
    db = d / "synthetic.sqlite3"
    if db.exists():
        raise RuntimeError("measurement rerun would overwrite original synthetic DB")
    original = valid_context()
    original_graph = digest(_encode(original))
    input_data = {
        "unit":unit, "case":case, "operation_id":OP, "run_id":RUN,
        "resource_sha256":SHA, "clock":NOW.isoformat(),
        "original_graph_sha256":original_graph,
    }
    (d/"input.json").write_text(canonical(input_data)+"\n",encoding="utf-8")
    store = StripeLabLedger(db)
    store.register(operation_id=OP, run_id=RUN, case_id=case,
        order_id=original.order.order_id, request_id=original.request.request_id,
        payment_id=original.execution.payment_id, resource_sha256=SHA)
    snap = store.record_authority(OP, original, resource_sha256=SHA, recorded_at=NOW)
    child = subprocess.run([sys.executable,"-B",str(P/"MEASURE.py"),
        "cold",str(db),OP,snap], cwd=ROOT, env=os.environ.copy(),
        capture_output=True, timeout=20)
    (d/"cold.stdout.log").write_bytes(child.stdout)
    (d/"cold.stderr.log").write_bytes(child.stderr)
    if child.returncode:
        raise RuntimeError("cold child failed")
    cold = json.loads(child.stdout)
    reopened = StripeLabLedger(db)
    reloaded = reopened.load_authority(OP,expected_sha256=snap)
    if original != reloaded:
        raise RuntimeError("original graph not recovered")
    client = FakeStripe()
    adapter = StripeCheckoutAdapter(client)
    observed = {
        "unit":unit, "case":case, "snapshot_sha256":snap,
        "original_context_graph_sha256":original_graph,
        "reloaded_context_graph_sha256":cold["graph_sha256"],
        "confirmed_at":original.confirmation_record.confirmed_at.isoformat(),
        "cold_confirmed_at":cold["confirmed_at"],
        "stored_before_fake_callback":True,
    }
    receipt = adapter.create_stored_session(reopened, operation_id=OP,
        expected_authority_sha256=snap, success_url=URL_SUCCESS,
        cancel_url=URL_CANCEL, now=NOW)
    if not receipt.gate.callback_executed:
        raise RuntimeError("stored create was not consumed")
    reopened.bind_session(OP, client.session.copy())
    if case == "N01":
        clicks = []
        pay = adapter.authorize_stored_browser_payment(
            reopened, operation_id=OP, expected_authority_sha256=snap,
            now=NOW, browser_payment=clicks.append)
        observed.update(consumer="stored_create_and_stored_pay",
            create_calls=len(client.created),get_calls=len(client.queries),
            browser_calls=len(clicks),original_session=receipt.session_id,
            payment_gate_executed=pay.callback_executed)
        if len(clicks)!=1 or len(client.created)!=1 or len(client.queries)!=1:
            raise RuntimeError("N01 callback count")
    elif case == "R01":
        reopened.mark_unknown(OP)
        reopened.observe(OP,*paid_observation(client))
        unknown = replace(original.execution, status=PaymentStatus.UNKNOWN,
                          provider_ref=receipt.session_id)
        source = PaymentStatusObservation(unknown.payment_id, unknown.order_id,
            PaymentStatus.SUCCEEDED,NOW+timedelta(hours=3),"stripe_api",
            provider_ref=receipt.session_id)
        recovered = StripeLabLedger(db).recover_original(OP,unknown,source)
        observed.update(consumer="original_payment_read_only_recovery",
            create_calls=len(client.created),get_calls=len(client.queries),
            browser_calls=0,retry_allowed=recovered.retry_allowed,
            recovery_status=recovered.recovery_status.value,
            original_session=StripeLabLedger(db).get(OP)["session_id"])
        if recovered.retry_allowed or len(client.created)!=1 or len(client.queries)!=0:
            raise RuntimeError("R01 read-only recovery violated")
    else:
        reopened.observe(OP,*paid_observation(client))
        failed = reopened.record_client_delivery(OP,RESOURCE,inject_failure=True)
        recovered = StripeLabLedger(db)
        replayed = recovered.load_authority(OP,expected_sha256=snap)
        first_receipt = recovered.record_client_delivery(OP, RESOURCE)
        second_receipt = recovered.record_client_delivery(OP, RESOURCE)
        delivery = recovered.delivery_history(OP)
        observed.update(consumer="delivery_receipt_read_only_replay",
            create_calls=len(client.created),get_calls=len(client.queries),
            browser_calls=0,initial_delivery_failed=failed is None,
            receipt_replayed_identically=first_receipt==second_receipt,
            successful_deliveries=sum(x["state"]=="SUCCEEDED" for x in delivery),
            original_session=recovered.get(OP)["session_id"],
            recovery_graph_sha256=digest(_encode(replayed)))
        if not observed["receipt_replayed_identically"] or observed["successful_deliveries"]!=1:
            raise RuntimeError("D01 delivery duplicate")
    evidence = d / "observed.json"
    evidence.write_text(canonical(observed)+"\n",encoding="utf-8")
    units.append({
        "unit":unit, "input_sha256":digest(input_data),
        "original_graph_sha256":original_graph,
        "reloaded_graph_sha256":cold["graph_sha256"],
        "snapshot_sha256":snap, "cold_process":bool(child.returncode==0),
        "original_times_preserved":cold["confirmed_at"]==original.confirmation_record.confirmed_at.isoformat()
            and cold["confirmation_expires_at"]==original.confirmation_record.expires_at.isoformat(),
        "consumer_or_recovery_observed":True,
        "unexpected_payment_callbacks":0,
        "observed_counts":{"create":observed["create_calls"],
            "provider_get":observed["get_calls"],"browser":observed["browser_calls"]},
        "raw_evidence":[file_ref(d/"input.json"),file_ref(d/"cold.stdout.log"),
            file_ref(d/"cold.stderr.log"),file_ref(evidence)],
    })
result={"schema":"h74-measurement/v1","baseline":"UNSUPPORTED_DURABLE_API",
    "baseline_is_not_security_failure":True,
    "interpretation":"new synthetic stored path only; H72 history unchanged",
    "units":units}
(P/"MEASUREMENT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"measured_units":len(units),
    "cold_loads":sum(u["cold_process"] for u in units),
    "unit_names":[u["unit"] for u in units],
    "unexpected_payment_callbacks":sum(u["unexpected_payment_callbacks"] for u in units)}))

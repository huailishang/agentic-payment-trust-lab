"""Evaluator baseline: existing pure APIs on full accepted checkout, no merchant calls."""
from datetime import datetime, timezone
import json
from RUNTIME import TASK, bootstrap
bootstrap()
from FIXTURES import keys, public, envelope, independent_materials, NOW
from CHECK import payloads_by_type
from agentic_payment_experiment.adapters.ap2_protocol_boundary import adapt_verified_ap2_v020_snapshot
from agentic_payment_experiment.validator import validate_request

target = TASK / "evidence/preparation_20261031/LINEAGE_BASELINE.json"
assert not target.exists()
checkout = json.loads((TASK / "SAMPLE_CHECKOUT.json").read_text(encoding="utf-8"))
registry = keys()
rows = []
for name, options in [("normal", {}), ("signed_amount_conflict", {"amount": 1500}),
                      ("signed_currency_conflict", {"currency": "EUR"})]:
    value = envelope(checkout, "h53-preparation-lineage", registry, **options)
    raw, verified = independent_materials(value, public(registry), "h53-preparation-lineage")
    typed = payloads_by_type(verified)
    terminal = typed["mandate.payment.1"]
    snapshot = {"protocol_version": "AP2-v0.2.0-official-boundary",
        "open_payment_mandate": typed["mandate.payment.open.1"], "payment_mandate": terminal,
        "checkout_mandate": {"vct": "mandate.checkout.1", "checkout_jwt": value["checkout_jws"],
                              "checkout_hash": terminal["transaction_id"]},
        "experiment_context": {"mandate_id": "h53-preparation", "user_id": "h53-synthetic-user",
            "category": "h53-flowers", "allowed_categories": ["h53-flowers"], "agent_id": "h53-agent",
            "occurred_at": datetime.fromtimestamp(NOW, timezone.utc).isoformat()}}
    boundary = adapt_verified_ap2_v020_snapshot(snapshot)
    assert boundary.ready
    semantic = validate_request(boundary.mandate, boundary.request)
    assert semantic.decision.value == "ALLOW"
    rows.append({"case": name, "authorization": value, "public_key_registry": public(registry),
        "official_two_hop_status": "VALID", "merchant_jws_status": "VALID",
        "signed_payment_amount": terminal["payment_amount"], "checkout_total": checkout["totals"],
        "checkout_currency": raw["currency"], "boundary_status": boundary.boundary_status.value,
        "canonical_decision": semantic.decision.value, "canonical_amount": str(boundary.request.amount),
        "canonical_currency": boundary.request.currency, "merchant_execution": "NOT_RUN"})
target.write_text(json.dumps({"phase": "EVALUATOR_PREPARATION_NOT_EXECUTOR_RESULT", "signed_material_cases": 3,
    "network_calls": 0, "asgi_requests": 0, "payment_calls": 0, "cases": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"full_checkout_existing_api_cases": len(rows), "local_allow": 3, "merchant_execution": "NOT_RUN"}))

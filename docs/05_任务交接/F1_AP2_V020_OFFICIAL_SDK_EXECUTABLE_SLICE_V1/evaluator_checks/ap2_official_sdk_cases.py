from __future__ import annotations

import base64
import hashlib
import json
from decimal import Decimal

from ap2.sdk.generated.checkout_mandate import CheckoutMandate
from ap2.sdk.generated.open_payment_mandate import (
    AgentRecurrence,
    AllowedPayees,
    AmountRange,
    ExecutionDate,
    Frequency,
    OpenPaymentMandate,
)
from ap2.sdk.generated.payment_mandate import PaymentMandate
from ap2.sdk.generated.types.amount import Amount
from ap2.sdk.generated.types.merchant import Merchant
from ap2.sdk.generated.types.payment_instrument import PaymentInstrument

from agentic_payment_experiment.adapters import adapt_verified_ap2_v020_sdk_objects
from agentic_payment_experiment.trusted_execution import VerificationStatus

def hash_checkout(raw: str) -> str:
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

def official_fixture():
    raw = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.f1-official-sdk.signature"
    checkout_hash = hash_checkout(raw)
    merchant = Merchant(id="merchant-boundary", name="Boundary Merchant")
    open_payment = OpenPaymentMandate(
        constraints=[
            AmountRange(currency="CNY", max=55000),
            AllowedPayees(allowed=[merchant]),
            AgentRecurrence(frequency=Frequency.ON_DEMAND, max_occurrences=1),
            ExecutionDate(not_after="2026-12-31T23:59:59+08:00"),
        ],
        cnf={"jwk": {"kty": "EC", "crv": "P-256", "x": "synthetic-x", "y": "synthetic-y"}},
    )
    payment = PaymentMandate(
        transaction_id=checkout_hash,
        payee=merchant,
        payment_amount=Amount(amount=52000, currency="CNY"),
        payment_instrument=PaymentInstrument(id="synthetic-instrument", type="card"),
        execution_date="2026-09-18T10:00:00+08:00",
    )
    checkout = CheckoutMandate(checkout_jwt=raw, checkout_hash=checkout_hash)
    context = {
        "mandate_id": "mandate-f1-official-sdk",
        "user_id": "synthetic-user",
        "category": "synthetic-category",
        "allowed_categories": ["synthetic-category"],
        "confirmation_above_minor": 60000,
        "agent_id": "synthetic-agent",
    }
    return open_payment, payment, checkout, context

def call(open_payment, payment, checkout, context):
    return adapt_verified_ap2_v020_sdk_objects(
        open_payment, payment, checkout, experiment_context=context
    )

def blocked(result, status, reason):
    assert result.boundary_status is status, (result.boundary_status, status)
    assert reason in result.reason_codes, result.reason_codes
    assert not result.ready
    assert result.mandate is None
    assert result.request is None

def main() -> None:
    results = []
    op, pay, co, ctx = official_fixture()

    r = call(op, pay, co, ctx)
    assert r.boundary_status is VerificationStatus.VALID
    assert r.ready and r.mandate is not None and r.request is not None
    results.append({"case": "S01_OFFICIAL_OBJECTS_VALID", "result": "PASS"})

    r = call(op.model_dump(), pay, co, ctx)
    blocked(r, VerificationStatus.INVALID, "ap2_sdk_open_payment_object_invalid")
    results.append({"case": "S02_OPEN_DICT_REJECTED", "result": "PASS"})

    r = call(op, pay.model_dump(), co, ctx)
    blocked(r, VerificationStatus.INVALID, "ap2_sdk_payment_object_invalid")
    results.append({"case": "S03_PAYMENT_DICT_REJECTED", "result": "PASS"})

    r = call(op, pay, co.model_dump(), ctx)
    blocked(r, VerificationStatus.INVALID, "ap2_sdk_checkout_object_invalid")
    results.append({"case": "S04_CHECKOUT_DICT_REJECTED", "result": "PASS"})

    bad_vct = co.model_copy(update={"vct": "mandate.checkout.999"})
    r = call(op, pay, bad_vct, ctx)
    blocked(r, VerificationStatus.INVALID, "ap2_checkout_vct_invalid")
    results.append({"case": "S05_WRONG_VCT_REUSES_H34", "result": "PASS"})

    tampered = co.model_copy(update={"checkout_jwt": co.checkout_jwt + ".tampered"})
    r = call(op, pay, tampered, ctx)
    blocked(r, VerificationStatus.INVALID, "ap2_checkout_hash_mismatch")
    results.append({"case": "S06_TAMPER_REUSES_H34", "result": "PASS"})

    wrong_binding = pay.model_copy(update={"transaction_id": "wrong-checkout"})
    r = call(op, wrong_binding, co, ctx)
    blocked(r, VerificationStatus.INVALID, "ap2_payment_checkout_binding_mismatch")
    results.append({"case": "S07_BINDING_REUSES_H34", "result": "PASS"})

    r = call(op, pay, co, ctx)
    assert r.request is not None
    assert r.request.amount == Decimal("520")
    assert r.request.currency == "CNY"
    assert r.request.merchant == "merchant-boundary"
    assert r.request.request_id == co.checkout_hash
    results.append({"case": "S08_CANONICAL_MAPPING", "result": "PASS"})

    missing_ctx = dict(ctx)
    missing_ctx.pop("category")
    r = call(op, pay, co, missing_ctx)
    blocked(r, VerificationStatus.MISSING_EVIDENCE, "ap2_canonical_mapping_not_ready")
    assert "experiment_context.category" in r.missing_fields
    results.append({"case": "S09_CONTEXT_MISSING", "result": "PASS"})

    print(json.dumps({"result": "PASS", "cases_total": 9, "cases_passed": 9, "cases": results}, indent=2))

if __name__ == "__main__":
    main()

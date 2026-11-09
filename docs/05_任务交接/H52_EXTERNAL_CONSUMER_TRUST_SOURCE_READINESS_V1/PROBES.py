"""H52 executor: independent, offline, signed synthetic artifact measurements.

No product or SDK modifications; private keys exist in memory only.
The returned statuses are facts about separate APIs, not an overall payment decision.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import sys
from dataclasses import asdict
from decimal import Decimal
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from RUNTIME import ROOT, TASK, bootstrap

def plain(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value

def b64url(raw):
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

def signed_checkout(key, total=1000):
    from jwcrypto.jws import JWS
    checkout = {"cart_id": "h52-cart-1", "currency": "USD",
                "amount_minor": total, "payee": "h52-merchant"}
    raw = json.dumps(checkout, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    signed = JWS(raw)
    signed.add_signature(key, protected=json.dumps({"alg": "ES256", "kid": "h52-merchant"}))
    return signed.serialize(compact=True)

def payment_chain(root_key, agent_key, checkout_digest):
    from ap2.sdk.mandate import MandateClient
    from ap2.sdk.generated.open_payment_mandate import (
        OpenPaymentMandate, AmountRange, AllowedPayees)
    from ap2.sdk.generated.payment_mandate import PaymentMandate
    from ap2.sdk.generated.types.amount import Amount
    from ap2.sdk.generated.types.merchant import Merchant
    from ap2.sdk.generated.types.payment_instrument import PaymentInstrument
    merchant = Merchant(id="h52-merchant", name="Synthetic Flower Shop")
    root = OpenPaymentMandate(
        constraints=[AmountRange(currency="USD", min=0, max=5000),
                     AllowedPayees(allowed=[merchant])],
        cnf={"jwk": json.loads(agent_key.export_public())}, iat=1800000000, exp=1800003600)
    terminal = PaymentMandate(
        transaction_id=checkout_digest, payee=merchant,
        payment_amount=Amount(amount=1000, currency="USD"),
        payment_instrument=PaymentInstrument(type="card", id="h52-stub", description="Synthetic"),
        iat=1800000000, exp=1800003600)
    client = MandateClient()
    signed_root = client.create(payloads=[root], issuer_key=root_key)
    token = client.present(holder_key=agent_key, mandate_token=signed_root,
                           payloads=[terminal], nonce="h52-checkout-once", aud="h52-merchant")
    return token, root.model_dump(mode="json", exclude_none=True), terminal.model_dump(mode="json", exclude_none=True)

def typed_payloads(value):
    found = {}
    def walk(obj):
        if hasattr(obj, "model_dump"):
            obj = obj.model_dump(mode="json", exclude_none=True)
        if isinstance(obj, dict):
            if obj.get("vct") in ("mandate.payment.open.1", "mandate.payment.1"):
                found[obj["vct"]] = obj
            for item in obj.values():
                walk(item)
        elif isinstance(obj, (tuple, list)):
            for item in obj:
                walk(item)
    walk(value)
    return found

def observe(case, registry):
    from jwcrypto.jwk import JWK
    from jwcrypto.jws import JWS
    from ap2.sdk.mandate import MandateClient
    from agentic_payment_experiment.adapters.ap2_official_verification import verify_ap2_v020_official_two_hop_chain
    from agentic_payment_experiment.adapters.ap2_protocol_boundary import adapt_verified_ap2_v020_snapshot
    from agentic_payment_experiment.validator import validate_request

    crypto_args = case["crypto_inputs"]
    trusted_pub = registry[crypto_args["trusted_root_role"]]
    crypto = verify_ap2_v020_official_two_hop_chain(
        token=crypto_args["token"], root_public_jwk=trusted_pub,
        expected_aud=crypto_args["expected_aud"],
        expected_nonce=crypto_args["expected_nonce"], current_time=crypto_args["current_time"])
    snapshot = case["boundary_input"]
    boundary = adapt_verified_ap2_v020_snapshot(snapshot)
    semantic = (validate_request(boundary.mandate, boundary.request,
                                  seen_request_ids=case["seen_request_ids"])
                if boundary.ready else None)
    payloads = {}
    if crypto.status.value == "VALID":
        verified = MandateClient().verify(
            crypto_args["token"], lambda _token: JWK(**trusted_pub),
            expected_aud=crypto_args["expected_aud"],
            expected_nonce=crypto_args["expected_nonce"],
            current_time=crypto_args["current_time"])
        payloads = typed_payloads(verified)
    merchant_signature = "INVALID"
    merchant_checkout = None
    try:
        jws = JWS()
        jws.deserialize(snapshot["checkout_mandate"]["checkout_jwt"])
        jws.verify(JWK(**registry["merchant"]))
        merchant_checkout = json.loads(jws.payload)
        merchant_signature = "VALID"
    except Exception:
        pass
    projected_payment = snapshot.get("payment_mandate", {})
    official_root = payloads.get("mandate.payment.open.1")
    official_payment = payloads.get("mandate.payment.1")
    lineage = None
    if official_root is not None and official_payment is not None:
        lineage = (all(projected_payment.get(field) == official_payment.get(field)
                       for field in ("vct", "transaction_id", "payee", "payment_amount",
                                     "payment_instrument", "iat", "exp"))
                   and snapshot.get("open_payment_mandate") == official_root)
    return plain({
        "crypto_status": crypto.status, "crypto_reasons": crypto.reason_codes,
        "merchant_signature_status": merchant_signature,
        "boundary_status": boundary.boundary_status, "boundary_reasons": boundary.reason_codes,
        "canonical_ready": boundary.ready,
        "canonical_decision": semantic.decision if semantic else None,
        "canonical_issue_codes": [item.code for item in semantic.issues] if semantic else [],
        "canonical_request": ({"amount": boundary.request.amount,
                               "merchant": boundary.request.merchant,
                               "currency": boundary.request.currency} if boundary.ready else None),
        "projection_matches_verified_payload": lineage,
        "verified_payload_types": sorted(payloads),
        "merchant_checkout": merchant_checkout,
        "user_consent_assessed_by_these_functions": False,
        "merchant_execution_assessed": False,
    })

def main(output):
    from cryptography.hazmat.primitives.asymmetric import ec
    from jwcrypto.jwk import JWK
    bootstrap()
    spec = json.loads((TASK / "CASE_SPEC.json").read_text(encoding="utf-8"))
    keys = {}
    for role in spec["roles"]:
        raw = json.loads(JWK.from_pyca(ec.generate_private_key(ec.SECP256R1())).export())
        raw["kid"] = "h52-" + role
        keys[role] = JWK(**raw)
    registry = {role: json.loads(key.export_public()) for role, key in keys.items()}
    checkout = signed_checkout(keys["merchant"])
    checkout_digest = b64url(hashlib.sha256(checkout.encode("ascii")).digest())
    valid_chain, root, terminal = payment_chain(keys["trusted_user"], keys["delegate_agent"], checkout_digest)
    context = {"mandate_id": "h52-synthetic-mandate", "user_id": "h52-synthetic-user",
               "category": "h52-flower", "allowed_categories": ["h52-flower"],
               "confirmation_above_minor": 500000, "agent_id": "h52-agent",
               "occurred_at": datetime.fromtimestamp(1800000000, timezone.utc).isoformat()}
    normal_snapshot = {
        "protocol_version": "AP2-v0.2.0-official-boundary",
        "open_payment_mandate": root,
        "payment_mandate": terminal,
        "checkout_mandate": {"vct": "mandate.checkout.1", "checkout_jwt": checkout,
                            "checkout_hash": checkout_digest},
        "experiment_context": context,
    }
    cases = []
    for identifier, _description in spec["required_cases"]:
        snapshot = copy.deepcopy(normal_snapshot)
        crypto = {"token": valid_chain, "trusted_root_role": "trusted_user",
                  "expected_aud": "h52-merchant", "expected_nonce": "h52-checkout-once",
                  "current_time": 1800000000}
        consent = identifier != "Q08_CONSENT_ABSENT"
        seen = []
        if identifier == "Q02_CHECKOUT_TAMPERED":
            parts = checkout.split(".")
            payload = bytearray(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
            old = b'"amount_minor":1000'
            assert old in payload
            payload = bytes(payload).replace(old, b'"amount_minor":1500')
            parts[1] = b64url(payload)
            snapshot["checkout_mandate"]["checkout_jwt"] = ".".join(parts)
        elif identifier == "Q03_CHECKOUT_REBOUND_PAYMENT_STALE":
            updated = signed_checkout(keys["merchant"], total=1500)
            snapshot["checkout_mandate"] = {"vct": "mandate.checkout.1", "checkout_jwt": updated,
                "checkout_hash": b64url(hashlib.sha256(updated.encode("ascii")).digest())}
        elif identifier == "Q04_PROJECTED_AMOUNT_CHANGED":
            snapshot["payment_mandate"]["payment_amount"]["amount"] = 1500
        elif identifier == "Q05_PROJECTED_PAYEE_CHANGED":
            snapshot["payment_mandate"]["payee"]["id"] = "h52-other-merchant"
        elif identifier == "Q06_PROJECTED_CURRENCY_CHANGED":
            snapshot["payment_mandate"]["payment_amount"]["currency"] = "EUR"
        elif identifier == "Q07_SELF_ROOT_SUBSTITUTION":
            crypto["token"], _, _ = payment_chain(keys["attacker"], keys["delegate_agent"], checkout_digest)
        elif identifier == "Q09_EXPIRED_TOKEN":
            crypto["current_time"] = 1800007200
        elif identifier == "Q10_WRONG_AUDIENCE":
            crypto["expected_aud"] = "h52-wrong-merchant"
        elif identifier == "Q11_REPLAY_WITH_SEEN_ID":
            seen = [checkout_digest]
        elif identifier == "Q12_MISSING_CONTEXT":
            snapshot["experiment_context"] = {}
        case = {"case": identifier, "crypto_inputs": crypto, "boundary_input": snapshot,
                "consent_present": consent, "seen_request_ids": seen}
        case["observed"] = observe(case, registry)
        if identifier == "Q07_SELF_ROOT_SUBSTITUTION":
            diagnostic = copy.deepcopy(case)
            diagnostic["crypto_inputs"]["trusted_root_role"] = "attacker"
            case["self_root_diagnostic"] = observe(diagnostic, registry)
        cases.append(case)
    result = {"schema": "h52-signed-artifact-observations/v1",
              "boundary": spec["boundary"], "encoding_scope": spec["encoding_scope"],
              "network_calls": 0, "asgi_requests": 0, "payment_calls": 0,
              "public_key_registry": registry, "cases": cases}
    out = (ROOT / output).resolve()
    assert out.is_relative_to((TASK / "evidence").resolve())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(cases), "saved": str(out.relative_to(ROOT)),
                      "crypto_valid": sum(c["observed"]["crypto_status"] == "VALID" for c in cases),
                      "canonical_allow": sum(c["observed"]["canonical_decision"] == "ALLOW" for c in cases),
                      "side_effects": 0}))

if __name__ == "__main__":
    assert len(sys.argv) == 3 and sys.argv[1] == "--out"
    main(sys.argv[2])

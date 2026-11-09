"""Frozen synthetic signing fixture, not an authorization implementation."""
import base64
import copy
import hashlib
import json
from RUNTIME import bootstrap
bootstrap()
from jwcrypto.jwk import JWK
from jwcrypto.jws import JWS
from ap2.sdk.mandate import MandateClient
from ap2.sdk.generated.open_payment_mandate import OpenPaymentMandate, AmountRange, AllowedPayees
from ap2.sdk.generated.payment_mandate import PaymentMandate
from ap2.sdk.generated.types.amount import Amount
from ap2.sdk.generated.types.merchant import Merchant
from ap2.sdk.generated.types.payment_instrument import PaymentInstrument

NOW = 1800000000
MERCHANT = "h50-synthetic-merchant"
PAYEE = "h50-synthetic-payee"
AUDIENCE = "h53-local-merchant"

def b64(raw):
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

def keys():
    return {role: JWK.generate(kty="EC", crv="P-256", kid="h53-" + role)
            for role in ("user", "agent", "merchant", "attacker")}

def public(registry):
    return {role: json.loads(key.export_public()) for role, key in registry.items()}

def context(registry):
    return {"trusted_root_public_jwk": public(registry)["user"],
            "merchant_public_jwk": public(registry)["merchant"],
            "expected_aud": AUDIENCE,
            "experiment_context": {"mandate_id": "h53-local-mandate", "user_id": "h53-synthetic-user",
                "category": "h53-flowers", "allowed_categories": ["h53-flowers"],
                "confirmation_above_minor": 500000, "agent_id": "h53-synthetic-agent"}}

def envelope(checkout, confirmation_ref, registry, *, amount=None, currency=None, payee=PAYEE,
             issuer="user", audience=AUDIENCE, nonce=None, expired=False):
    raw = json.dumps(checkout, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    signed = JWS(raw)
    signed.add_signature(registry["merchant"], protected=json.dumps({"alg": "ES256", "kid": "h53-merchant"}))
    compact = signed.serialize(compact=True)
    digest = b64(hashlib.sha256(compact.encode("ascii")).digest())
    total = next(t["amount"] for t in checkout["totals"] if t["type"] == "total")
    chosen_payee = Merchant(id=payee, name="H53 Synthetic Payee")
    root = OpenPaymentMandate(constraints=[AmountRange(currency="USD", min=0, max=5000),
        AllowedPayees(allowed=[chosen_payee])], cnf={"jwk": public(registry)["agent"]},
        iat=NOW-7200 if expired else NOW, exp=NOW-3600 if expired else NOW+3600)
    terminal = PaymentMandate(transaction_id=digest, payee=chosen_payee,
        payment_amount=Amount(amount=total if amount is None else amount, currency=currency or checkout["currency"]),
        payment_instrument=PaymentInstrument(type="card", id="instr_1", description="Synthetic"),
        iat=NOW-7200 if expired else NOW, exp=NOW-3600 if expired else NOW+3600)
    client = MandateClient()
    token = client.present(holder_key=registry["agent"],
        mandate_token=client.create(payloads=[root], issuer_key=registry[issuer]),
        payloads=[terminal], aud=audience, nonce=nonce or "h53:" + confirmation_ref)
    return {"schema": "h53-local-authorization-envelope/v1", "payment_token": token,
            "checkout_jws": compact, "projection": {
                "open_payment_mandate": root.model_dump(mode="json", exclude_none=True),
                "payment_mandate": terminal.model_dump(mode="json", exclude_none=True)}}

def independent_materials(value, registry, confirmation_ref):
    """Decode from the SDK result; never call the candidate consumer."""
    checkout = JWS()
    checkout.deserialize(value["checkout_jws"])
    checkout.verify(JWK(**registry["merchant"]))
    payload = json.loads(checkout.payload)
    verified = MandateClient().verify(value["payment_token"], lambda _token: JWK(**registry["user"]),
        expected_aud=AUDIENCE, expected_nonce="h53:" + confirmation_ref, current_time=NOW,
        clock_skew_seconds=0)
    assert len(verified) == 2
    return payload, verified

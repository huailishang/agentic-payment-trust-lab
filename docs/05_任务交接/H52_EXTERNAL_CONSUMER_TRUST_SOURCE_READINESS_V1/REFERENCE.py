"""Independent frozen read-only recomputation of submitted public synthetic inputs."""
import base64
import json
from dataclasses import asdict
from decimal import Decimal
from enum import Enum
from RUNTIME import bootstrap

def plain(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    return value

def typed_payloads(value):
    found = {}
    def visit(item):
        if hasattr(item, "model_dump"):
            item = item.model_dump(mode="json", exclude_none=True)
        if isinstance(item, dict):
            if item.get("vct") in ("mandate.payment.open.1", "mandate.payment.1"):
                found[item["vct"]] = item
            for child in item.values():
                visit(child)
        elif isinstance(item, (tuple, list)):
            for child in item:
                visit(child)
    visit(value)
    return found

def recompute(case, registry):
    from jwcrypto.jwk import JWK
    from jwcrypto.jws import JWS
    from ap2.sdk.mandate import MandateClient
    from agentic_payment_experiment.adapters.ap2_official_verification import verify_ap2_v020_official_two_hop_chain
    from agentic_payment_experiment.adapters.ap2_protocol_boundary import adapt_verified_ap2_v020_snapshot
    from agentic_payment_experiment.validator import validate_request
    inputs = case["crypto_inputs"]
    root = registry[inputs["trusted_root_role"]]
    args = dict(token=inputs["token"], root_public_jwk=root, expected_aud=inputs["expected_aud"],
                expected_nonce=inputs["expected_nonce"], current_time=inputs["current_time"])
    crypto = verify_ap2_v020_official_two_hop_chain(**args)
    snapshot = case["boundary_input"]
    boundary = adapt_verified_ap2_v020_snapshot(snapshot)
    semantic = None
    if boundary.ready:
        semantic = validate_request(boundary.mandate, boundary.request,
                                    seen_request_ids=case.get("seen_request_ids", []))
    payloads = {}
    if crypto.status.value == "VALID":
        payloads = typed_payloads(MandateClient().verify(
            token=inputs["token"], key_or_provider=lambda _token: JWK(**root),
            expected_aud=inputs["expected_aud"], expected_nonce=inputs["expected_nonce"],
            current_time=inputs["current_time"]))
    merchant_signature = "INVALID"
    merchant_checkout = None
    try:
        signed = JWS()
        signed.deserialize(snapshot["checkout_mandate"]["checkout_jwt"])
        signed.verify(JWK(**registry["merchant"]))
        merchant_checkout = json.loads(signed.payload)
        merchant_signature = "VALID"
    except Exception:
        pass
    terminal = payloads.get("mandate.payment.1")
    root_payload = payloads.get("mandate.payment.open.1")
    projected = snapshot.get("payment_mandate", {})
    lineage = None
    if terminal is not None and root_payload is not None:
        lineage = all(projected.get(k) == terminal.get(k) for k in
                      ("vct", "transaction_id", "payee", "payment_amount", "payment_instrument", "iat", "exp"))
        lineage = lineage and snapshot.get("open_payment_mandate") == root_payload
    return plain({
        "crypto_status": crypto.status, "crypto_reasons": crypto.reason_codes,
        "merchant_signature_status": merchant_signature,
        "boundary_status": boundary.boundary_status, "boundary_reasons": boundary.reason_codes,
        "canonical_ready": boundary.ready,
        "canonical_decision": semantic.decision if semantic else None,
        "canonical_issue_codes": [x.code for x in semantic.issues] if semantic else [],
        "canonical_request": {"amount": boundary.request.amount, "merchant": boundary.request.merchant,
            "currency": boundary.request.currency} if boundary.ready else None,
        "projection_matches_verified_payload": lineage,
        "verified_payload_types": sorted(payloads),
        "merchant_checkout": merchant_checkout,
        "user_consent_assessed_by_these_functions": False,
        "merchant_execution_assessed": False,
    })

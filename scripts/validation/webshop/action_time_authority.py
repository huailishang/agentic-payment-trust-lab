"""H85 experimental caller-owned, action-scoped credential observation."""
from dataclasses import asdict
from hashlib import sha256
import base64
import json
import secrets
import time

from agentic_payment_experiment.trusted_execution.credential_possession import (
    verify_x509_svid_credential_possession,
)


def _canonical(value):
    if isinstance(value, dict):
        return {k: _canonical(v) for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted(_canonical(v) for v in value)
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def digest(value):
    return sha256(json.dumps(_canonical(value), sort_keys=True, default=str).encode()).hexdigest()


def business_snapshot(order, mandate, request, confirmation):
    return _canonical({
        "order": asdict(order), "mandate": asdict(mandate),
        "request": asdict(request), "confirmation": asdict(confirmation),
    })


def collect(source, *, action, order, mandate, request, payment, confirmation, identity):
    business = business_snapshot(order, mandate, request, confirmation)
    binding = {
        "action_id": action.action_id, "authority_ref": mandate.mandate_id,
        "authority_version": mandate.authority_version,
        "order_digest": digest(business["order"]), "request_ref": request.request_id,
        "payment_ref": payment.payment_id, "business_digest": digest(business),
        "agent_ref": identity.agent_id, "provider_ref": identity.provider,
        "executor_ref": identity.executor_instance_id, "credential_ref": identity.credential_ref,
    }
    entropy = secrets.token_hex(32)
    nonce = digest({"binding": binding, "entropy": entropy})
    start = time.monotonic_ns()
    issued_at = int(time.time())
    payload = (
        "agentic-payment-possession/v1\n"
        f"nonce={nonce}\nagent={identity.agent_id}\nprovider={identity.provider}\n"
        f"executor={identity.executor_instance_id}\nissued_at={issued_at}\n"
    ).encode()
    row = {**binding, "nonce": nonce, "nonce_entropy": entropy, "issued_at_epoch": issued_at,
           "start_monotonic_ns": start, "source_status": "UNKNOWN",
           "fact_supplied": False, "payload_b64": base64.b64encode(payload).decode(),
           "business_snapshot": business}
    fact = None
    try:
        response = source.observe(payload)
    except (OSError, TimeoutError):
        response = {"status": "UNKNOWN"}
    observed = int(time.time())
    observed_monotonic = time.monotonic_ns()
    status = response.get("status", "UNKNOWN")
    row.update(source_status=status if status in ("ISSUED", "DENIED") else "UNKNOWN",
               observed_at_epoch=observed, observed_monotonic_ns=observed_monotonic,
               source_evidence=response.get("evidence", {}))
    if status == "ISSUED":
        leaf, root, signature = response["leaf_pem"], response["root_pem"], response["signature"]
        row.update(leaf_pem=leaf.decode(), root_pem=root.decode(),
                   signature_b64=base64.b64encode(signature).decode())
        verified = verify_x509_svid_credential_possession(
            leaf_svid_pem=leaf, trusted_ca_pem=root,
            expected_trust_domain=source.trust_domain,
            expected_agent_ref=identity.agent_id, expected_provider_ref=identity.provider,
            expected_executor_instance_ref=identity.executor_instance_id,
            credential_ref=identity.credential_ref, challenge_payload=payload,
            challenge_signature=signature, nonce_ref=nonce, issued_at_epoch=issued_at,
            observed_at_epoch=observed, max_age_seconds=300,
        )
        row.update(verification_status=verified.status.name,
                   verification_reasons=list(verified.reason_codes),
                   certificate_sha256=verified.leaf_certificate_sha256)
        if verified.status.name == "VALID":
            fact = verified
    use_at = int(time.time())
    use_monotonic = time.monotonic_ns()
    if not (start <= observed_monotonic <= use_monotonic and issued_at <= observed == use_at):
        fact = None
        row["qualification_reason"] = "action_time_mismatch"
    row.update(use_at_epoch=use_at, use_monotonic_ns=use_monotonic, fact_supplied=fact is not None)
    return fact, use_at, row

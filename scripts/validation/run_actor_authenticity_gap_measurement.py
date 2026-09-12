from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agentic_payment_experiment.adapters import (
    adapt_acp_checkout_pair,
    adapt_ap2_flow_snapshot,
    evaluate_ap2_flow,
)
from agentic_payment_experiment.models import (
    AgentIdentity,
    Decision,
    IntentMandate,
    Order,
    OrderItem,
    PaymentExecutionRecord,
    PaymentStatus,
    TransactionRequest,
)
from agentic_payment_experiment.payment_execution import (
    PAYMENT_CONTEXT_ACTION,
    PAYMENT_REQUIRED_SOURCE_PATHS,
    execute_with_payment_binding_gate,
)
from agentic_payment_experiment.trusted_execution import (
    IdentityAssuranceLevel,
    POLICY_VERSION,
    SourceType,
    evaluate_context_policy,
    verify_agent_executor_identity,
)


SCHEMA = "actor-authenticity-signed-instruction-gap-measurement/v1"
MATRIX_SHA256 = "cfa9896d543e9b32c215d7b1d801a15d55ad01bd29bfd15913a6a4cb3212ad17"
PROBE_ORDER = (
    "P01_P3_BOUND_NO_CREDENTIAL",
    "P02_P3_EXPECTED_CREDENTIAL_CURRENT_MISSING",
    "P03_P3_MATCHING_CREDENTIAL_REF_ONLY",
    "P04_AP2_HP_USER_AUTH_SIGNATURE_UNVERIFIED",
    "P05_AP2_HNP_INTENT_AUTH_SIGNATURE_UNVERIFIED",
    "P06_ACP_WEBHOOK_PAYEE_AUTHENTICITY_UNVERIFIED",
)
NOT_VERIFIED_CODES = {
    "ap2_user_authorization_signature_not_verified",
    "ap2_intent_authorization_signature_not_verified",
    "seller_identity_from_endpoint_context_not_verified",
    "payee_identity_not_verified",
    "order_webhook_signature_not_verified",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--repeat", required=True, type=int)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def subset_equal(expected: object, observed: object) -> bool:
    if isinstance(expected, Mapping):
        if not isinstance(observed, Mapping):
            return False
        return all(
            key in observed and subset_equal(value, observed[key])
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        if not isinstance(observed, list):
            return False
        return all(item in observed for item in expected)
    return expected == observed


def load_json(path: Path, label: str) -> Mapping[str, Any]:
    require(path.is_file(), f"{label} missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, Mapping), f"{label} must be an object")
    return value


def build_p3_fixture() -> dict[str, object]:
    now = datetime(2026, 7, 11, 12, 0, tzinfo=timezone.utc)
    mandate = IntentMandate(
        mandate_id="mandate-1",
        user_id="user-1",
        max_amount=Decimal("500.00"),
        allowed_merchants=frozenset({"merchant-1"}),
        allowed_categories=frozenset({"shoes"}),
        expires_at=now + timedelta(hours=1),
        expected_agent_id="agent-1",
        authority_version="v1",
    )
    order = Order(
        order_id="order-1",
        order_version="v1",
        merchant="merchant-1",
        payee="payee-1",
        items=(
            OrderItem(
                item_id="item-1",
                name="Running Shoe",
                category="shoes",
                quantity=1,
                unit_amount=Decimal("480.00"),
            ),
        ),
        total_amount=Decimal("480.00"),
        currency="CNY",
        quote_expires_at=now + timedelta(minutes=30),
        fulfilment_terms="standard delivery",
        mandate_ref="mandate-1",
        authority_version_ref="v1",
    )
    request = TransactionRequest(
        request_id="request-1",
        amount=Decimal("480.00"),
        merchant="merchant-1",
        category="shoes",
        occurred_at=now,
        agent_id="agent-1",
        currency="CNY",
        order_ref="order-1",
        authority_ref="mandate-1",
        authority_version_ref="v1",
        payee="payee-1",
    )
    payment = PaymentExecutionRecord(
        payment_id="payment-1",
        request_id="request-1",
        order_id="order-1",
        status=PaymentStatus.PENDING,
        amount=Decimal("480.00"),
        currency="CNY",
        occurred_at=now + timedelta(seconds=1),
        authority_ref="mandate-1",
        agent_ref="agent-1",
        transaction_object_ref="request-1",
        payee="payee-1",
    )
    identity = AgentIdentity(
        agent_id="agent-1",
        provider="offline-provider-1",
        executor_instance_id="executor-1",
        status="active",
    )
    context_policy_fact = evaluate_context_policy(
        {
            "mandate": {"mandate_id": mandate.mandate_id},
            "final_order": {"order_id": order.order_id},
            "request": {
                "request_id": request.request_id,
                "agent_id": request.agent_id,
                "amount": request.amount,
                "payee": request.payee,
                "currency": request.currency,
            },
        },
        trusted_sources={
            "mandate.mandate_id": SourceType.USER_CONFIRMED,
            "final_order.order_id": SourceType.USER_CONFIRMED,
            "request.request_id": SourceType.PROTOCOL_VERIFIED,
            "request.agent_id": SourceType.USER_CONFIRMED,
            "request.amount": SourceType.USER_CONFIRMED,
            "request.payee": SourceType.USER_CONFIRMED,
            "request.currency": SourceType.USER_CONFIRMED,
        },
        required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS,
        current_action=PAYMENT_CONTEXT_ACTION,
        policy_version=POLICY_VERSION,
    ).fact
    return {
        "mandate": mandate,
        "order": order,
        "request": request,
        "payment": payment,
        "identity": identity,
        "context_policy_fact": context_policy_fact,
    }


def measure_p3(probe_id: str, fixture: Mapping[str, object]) -> dict[str, object]:
    base_identity = fixture["identity"]
    require(isinstance(base_identity, AgentIdentity), "P3 identity fixture invalid")
    if probe_id == "P01_P3_BOUND_NO_CREDENTIAL":
        identity = base_identity
        current_credential_ref = None
    elif probe_id == "P02_P3_EXPECTED_CREDENTIAL_CURRENT_MISSING":
        identity = replace(base_identity, credential_ref="credential-expected")
        current_credential_ref = None
    elif probe_id == "P03_P3_MATCHING_CREDENTIAL_REF_ONLY":
        identity = replace(base_identity, credential_ref="credential-expected")
        current_credential_ref = "credential-expected"
    else:
        raise RuntimeError(f"unsupported P3 probe: {probe_id}")

    mandate = fixture["mandate"]
    order = fixture["order"]
    request = fixture["request"]
    payment = fixture["payment"]
    fact = verify_agent_executor_identity(
        authorized_agent_ref=mandate.expected_agent_id,  # type: ignore[attr-defined]
        request_agent_ref=request.agent_id,  # type: ignore[attr-defined]
        execution_agent_ref=payment.agent_ref,  # type: ignore[attr-defined]
        identity=identity,
        current_provider_ref="offline-provider-1",
        current_executor_instance_ref="executor-1",
        current_credential_ref=current_credential_ref,
    )
    callback_count = 0

    def callback() -> str:
        nonlocal callback_count
        callback_count += 1
        return "offline-provider-payment-1"

    outcome = execute_with_payment_binding_gate(
        Decision.ALLOW,
        mandate,  # type: ignore[arg-type]
        order,  # type: ignore[arg-type]
        request,  # type: ignore[arg-type]
        payment,  # type: ignore[arg-type]
        callback,
        agent_identity=identity,
        current_provider_ref="offline-provider-1",
        current_executor_instance_ref="executor-1",
        current_credential_ref=current_credential_ref,
        context_policy_fact=fixture["context_policy_fact"],  # type: ignore[arg-type]
    )
    observation = {
        "identity_status": fact.status.value,
        "assurance_level": fact.assurance_level.value,
        "reason_codes": list(fact.reason_codes),
        "limitation_codes": [],
        "credential_expected": fact.identity_credential_ref is not None,
        "credential_observed": fact.credential_ref is not None,
        "credential_available": fact.credential_available,
        "expected_credential_ref": fact.identity_credential_ref,
        "observed_credential_ref": fact.credential_ref,
        "gate_decision": outcome.decision.value,
        "gate_reason_codes": list(outcome.gate_reason_codes),
        "callback_count": callback_count,
        "verified_emitted": fact.assurance_level is IdentityAssuranceLevel.VERIFIED,
        "verified_authenticity_observed": fact.assurance_level is IdentityAssuranceLevel.VERIFIED,
        "cryptographic_signature_verified": False,
    }
    diagnostic = (
        "CREDENTIAL_REFERENCE_WITHOUT_VERIFIER"
        if observation["credential_expected"]
        else "IDENTIFIER_BINDING_ONLY"
    )
    return {
        "product_observation": observation,
        "measurement_diagnostics": {
            "boundary_classification": diagnostic,
            "verified_authenticity_inferred": False,
            "notes": [
                "BOUND is deterministic reference binding, not proof of authenticator possession or credential validity"
            ],
        },
    }


def authenticity_limitation_codes(values: object) -> list[str]:
    if not isinstance(values, (tuple, list)):
        return []
    return sorted(
        str(value)
        for value in values
        if str(value) in NOT_VERIFIED_CODES or "signature_not_verified" in str(value)
    )


def measure_ap2(snapshot_name: str) -> dict[str, object]:
    snapshot = load_json(
        REPOSITORY_ROOT / "samples" / "protocol_snapshots" / snapshot_name,
        snapshot_name,
    )
    adapted = adapt_ap2_flow_snapshot(snapshot)
    result = evaluate_ap2_flow(adapted)
    relevant = authenticity_limitation_codes(adapted.unmapped_fields)
    observation = {
        "adapted_ready": adapted.ready,
        "flow_mode": adapted.flow_mode.value if adapted.flow_mode is not None else None,
        "decision": result.decision.value,
        "reason_codes": [issue.code for issue in result.issues],
        "limitation_codes": list(adapted.unmapped_fields),
        "required_limitation_codes": relevant,
        "validation_limitations": list(result.limitations),
        "cryptographic_signature_verified": False,
        "verified_authenticity_observed": False,
    }
    boundary = (
        "AUTHORIZATION_SIGNATURE_NOT_VERIFIED"
        if any("authorization_signature_not_verified" in code for code in relevant)
        else "CRYPTOGRAPHIC_AUTHENTICITY_NOT_VERIFIED"
    )
    return {
        "product_observation": observation,
        "measurement_diagnostics": {
            "boundary_classification": boundary,
            "verified_authenticity_inferred": False,
            "notes": [
                "fixture authorization fields are inputs; product limitations explicitly retain unverified signature boundaries"
            ],
        },
    }


def measure_acp() -> dict[str, object]:
    snapshot = load_json(
        REPOSITORY_ROOT
        / "samples"
        / "protocol_snapshots"
        / "ACP_S09_order_total_changed.json",
        "ACP_S09_order_total_changed.json",
    )
    adapted = adapt_acp_checkout_pair(snapshot)
    relevant = authenticity_limitation_codes(adapted.unmapped_fields)
    observation = {
        "adapted_ready": adapted.ready,
        "reason_codes": [],
        "limitation_codes": list(adapted.unmapped_fields),
        "required_limitation_codes": relevant,
        "seller_identity_verified_claim": False,
        "payee_identity_verified_claim": False,
        "webhook_signature_verified_claim": False,
        "cryptographic_signature_verified": False,
        "verified_authenticity_observed": False,
    }
    return {
        "product_observation": observation,
        "measurement_diagnostics": {
            "boundary_classification": [
                "PAYEE_IDENTITY_NOT_VERIFIED",
                "WEBHOOK_SIGNATURE_NOT_VERIFIED",
            ],
            "verified_authenticity_inferred": False,
            "notes": [
                "S09 order-total business semantics are intentionally excluded from authenticity evidence"
            ],
        },
    }


def measure_once(probe_id: str, p3_fixture: Mapping[str, object]) -> dict[str, object]:
    if probe_id.startswith("P0") and "_P3_" in probe_id:
        return measure_p3(probe_id, p3_fixture)
    if probe_id == "P04_AP2_HP_USER_AUTH_SIGNATURE_UNVERIFIED":
        return measure_ap2("AP2_v020_HP_cards.json")
    if probe_id == "P05_AP2_HNP_INTENT_AUTH_SIGNATURE_UNVERIFIED":
        return measure_ap2("AP2_v020_HNP_cards.json")
    if probe_id == "P06_ACP_WEBHOOK_PAYEE_AUTHENTICITY_UNVERIFIED":
        return measure_acp()
    raise RuntimeError(f"unsupported frozen probe: {probe_id}")


def candidate_families(probes: list[dict[str, object]]) -> dict[str, list[str]]:
    families: dict[str, list[str]] = {}
    for item in probes:
        probe_id = str(item["probe_id"])
        diagnostic = item["measurement_diagnostics"]
        require(isinstance(diagnostic, Mapping), f"{probe_id}: diagnostics missing")
        classes = diagnostic.get("boundary_classification")
        labels = classes if isinstance(classes, list) else [classes]
        for label in labels:
            if isinstance(label, str) and label:
                families.setdefault(label, []).append(probe_id)

    signature_members = []
    for item in probes:
        observation = item["product_observation"]
        if not isinstance(observation, Mapping):
            continue
        codes = observation.get("limitation_codes") or []
        if isinstance(codes, list) and any("signature_not_verified" in str(code) for code in codes):
            signature_members.append(str(item["probe_id"]))
    if signature_members:
        families["CRYPTOGRAPHIC_SIGNATURE_VERIFICATION_ABSENT"] = signature_members
    return families


def main() -> int:
    args = parse_args()
    require(args.repeat == 2, "frozen repeat must be 2")
    matrix_path = (REPOSITORY_ROOT / args.matrix).resolve()
    output_path = (REPOSITORY_ROOT / args.output).resolve()
    require(sha256(matrix_path) == MATRIX_SHA256, "frozen matrix hash drift")
    matrix = load_json(matrix_path, "authenticity gap matrix")
    raw_probes = matrix.get("probes")
    require(isinstance(raw_probes, list) and len(raw_probes) == 6, "matrix must contain six probes")
    require(tuple(str(item["probe_id"]) for item in raw_probes) == PROBE_ORDER, "probe order drift")

    p3_fixture = build_p3_fixture()
    probes: list[dict[str, object]] = []
    for raw in raw_probes:
        require(isinstance(raw, Mapping), "probe entry must be an object")
        probe_id = str(raw["probe_id"])
        surface = str(raw["surface"])
        expected = raw["expected"]
        runs = [measure_once(probe_id, p3_fixture) for _ in range(args.repeat)]
        digests = [canonical_digest(run) for run in runs]
        first = runs[0]
        observation = first["product_observation"]
        probes.append(
            {
                "probe_id": probe_id,
                "surface": surface,
                "measurement_complete": True,
                "repeat_identical": len(set(digests)) == 1 and runs[0] == runs[1],
                "run_digests": digests,
                "product_observation": observation,
                "measurement_diagnostics": first["measurement_diagnostics"],
                "expected_observation": expected,
                "expectation_match": subset_equal(expected, observation),
            }
        )

    product_codes: set[str] = set()
    verified_ids: list[str] = []
    explicit_not_verified_ids: list[str] = []
    for item in probes:
        observation = item["product_observation"]
        require(isinstance(observation, Mapping), "product observation missing")
        reason_codes = observation.get("reason_codes") or []
        limitation_codes = observation.get("limitation_codes") or []
        require(isinstance(reason_codes, list), "reason_codes must be a list")
        require(isinstance(limitation_codes, list), "limitation_codes must be a list")
        product_codes.update(str(code) for code in reason_codes + limitation_codes)
        verified = bool(observation.get("verified_authenticity_observed", False))
        if observation.get("assurance_level") == "VERIFIED":
            verified = True
        if observation.get("cryptographic_signature_verified") is True:
            verified = True
        if verified:
            verified_ids.append(str(item["probe_id"]))
        if any(str(code) in NOT_VERIFIED_CODES for code in limitation_codes):
            explicit_not_verified_ids.append(str(item["probe_id"]))

    families = candidate_families(probes)
    surface_by_probe = {str(item["probe_id"]): str(item["surface"]) for item in probes}
    repeated = any(
        len({surface_by_probe[probe_id] for probe_id in members}) >= 2
        for members in families.values()
    )

    result = {
        "schema": SCHEMA,
        "matrix": {
            "path": args.matrix,
            "sha256": sha256(matrix_path),
        },
        "repeat_per_probe": args.repeat,
        "probes": probes,
        "summary": {
            "probes_measured": len(probes),
            "probes_total": len(PROBE_ORDER),
            "surface_count_measured": len({str(item["surface"]) for item in probes}),
            "probes_with_verified_authenticity": verified_ids,
            "probes_with_explicit_not_verified_boundary": explicit_not_verified_ids,
            "unique_limitation_reason_codes": sorted(product_codes),
            "candidate_mechanism_families": families,
            "cross_surface_repeated_mechanism": repeated,
        },
        "guardrails": {
            "external_network_calls": 0,
            "real_payment_execution_count": 0,
            "real_credential_use_count": 0,
            "real_key_use_count": 0,
            "real_signature_operation_count": 0,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "probes_measured": f"{len(probes)}/6",
                "expectation_matches": f"{sum(1 for item in probes if item['expectation_match'])}/6",
                "verified_authenticity": verified_ids,
                "explicit_not_verified": explicit_not_verified_ids,
                "surface_count": result["summary"]["surface_count_measured"],
                "cross_surface_repeated_mechanism": repeated,
                "real_side_effects": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

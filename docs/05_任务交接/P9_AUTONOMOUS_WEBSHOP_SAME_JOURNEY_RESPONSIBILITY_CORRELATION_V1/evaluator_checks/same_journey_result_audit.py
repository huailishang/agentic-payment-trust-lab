from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[4]
ACCEPTED = ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_PREBUY_BEHAVIOR_CAPTURE_V1/evidence/EV-AUTONOMOUS-BEHAVIOR.json"
EXPECTED_ACCEPTED_SHA = "cb11bdc27e514118c8e9ae69384be16d188ec08bba7c1d4514d6b3c50e316dd0"
EXPECTED_TRACE_SHA = "8c0a03b2f2e5dd9dce051ce176c546e2e171b5e7eacfdb36b258ba04dddd5897"
EXPECTED_ORIGINS = {
    "USER_AUTHORITY",
    "AGENT_DECISION",
    "RUNTIME_DECISION",
    "EXTERNAL_FACT",
    "EXECUTION_RESULT",
}
EXPECTED_CORRELATIONS = {
    "C01_REPLAY_IDENTITY",
    "C02_SESSION_TO_CANDIDATE",
    "C03_ACTIONS_TO_CANDIDATE",
    "C04_PRODUCT_TO_ORDER",
    "C05_ORDER_TO_REQUEST",
    "C06_REQUEST_TO_RUNTIME",
    "C07_ORDER_REQUEST_TO_EXECUTION",
    "C08_TRACE_ORIGIN_CONTINUITY",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapping(value: Any, label: str) -> Mapping[str, Any]:
    require(isinstance(value, Mapping), f"{label} must be mapping")
    return value


def validate(payload: Mapping[str, Any]) -> None:
    require(payload.get("schema") == "webshop-same-journey-responsibility/v1", "schema mismatch")

    accepted = mapping(payload.get("accepted_behavior"), "accepted_behavior")
    replay = mapping(payload.get("replay"), "replay")
    candidate = mapping(payload.get("candidate"), "candidate")
    commerce = mapping(payload.get("commerce"), "commerce")
    runtime = mapping(payload.get("runtime_gate"), "runtime_gate")
    execution = mapping(payload.get("execution"), "execution")
    trace = mapping(payload.get("trace"), "trace")
    guardrails = mapping(payload.get("guardrails"), "guardrails")

    require(accepted.get("fixture_sha256") == EXPECTED_ACCEPTED_SHA, "accepted fixture hash mismatch")
    require(accepted.get("normalized_trace_sha256") == EXPECTED_TRACE_SHA, "accepted trace hash mismatch")
    require(replay.get("goal_index") == 10, "goal index mismatch")
    require(replay.get("seed") == 20260823, "seed mismatch")
    require(replay.get("repeat") == 2, "repeat must be 2")
    require(replay.get("repeat_identical") is True, "replay is not repeat-identical")
    require(replay.get("normalized_trace_sha256") == EXPECTED_TRACE_SHA, "replay trace differs from accepted trace")
    require(replay.get("matches_accepted") is True, "replay must explicitly match accepted behavior")
    require(replay.get("buy_now_executed") is False, "real WebShop Buy Now must stay false")
    require(replay.get("purchase_count") == 0, "WebShop purchase count must stay zero")

    product = mapping(replay.get("product"), "replay.product")
    require(str(product.get("asin", "")).upper() == "B099231V35", "accepted ASIN mismatch")
    options = product.get("selected_options")
    require(isinstance(options, Mapping), "selected_options must be mapping")
    require("orange" in {str(v).lower() for v in options.values()}, "accepted orange option missing")
    require(str(product.get("unit_price")) == "16.79", "accepted price mismatch")

    require(candidate.get("session_id") == replay.get("session_id"), "candidate not from replay session")
    require(candidate.get("instruction_text") == replay.get("instruction_text"), "candidate instruction drift")
    require(candidate.get("actions_executed") == replay.get("actions_executed"), "candidate actions drift")
    candidate_product = mapping(candidate.get("product"), "candidate.product")
    require(str(candidate_product.get("asin", "")).upper() == str(product.get("asin", "")).upper(), "candidate ASIN drift")
    require(candidate_product.get("selected_options") == product.get("selected_options"), "candidate option drift")

    require(commerce.get("adaptation_ready") is True, "Commerce Adapter not ready")
    require(commerce.get("user_intent_text") == replay.get("instruction_text"), "adapter intent drift")
    require(str(commerce.get("order_item_id", "")).upper() == str(product.get("asin", "")).upper(), "Order item not replay product")
    require(isinstance(commerce.get("order_id"), str) and commerce.get("order_id"), "order_id missing")
    require(isinstance(commerce.get("request_id"), str) and commerce.get("request_id"), "request_id missing")
    require(commerce.get("request_order_ref") == commerce.get("order_id"), "Order -> Request binding broken")

    require(runtime.get("decision") == "ALLOW", "offline Runtime Gate must reach ALLOW")
    require(runtime.get("bound_request_id") == commerce.get("request_id"), "Runtime request mismatch")
    require(runtime.get("bound_order_ref") == commerce.get("order_id"), "Runtime order mismatch")
    require(runtime.get("callback_count") == 1, "offline callback seam must execute exactly once")
    require(runtime.get("callback_result_ref") == "offline-same-journey-checkout-seam", "callback seam ref mismatch")
    require(runtime.get("real_webshop_buy_now_executed") is False, "Runtime seam cannot be reported as real Buy Now")

    require(execution.get("request_id") == commerce.get("request_id"), "payment request mismatch")
    require(execution.get("order_id") == commerce.get("order_id"), "payment order mismatch")
    require(execution.get("fulfillment_order_id") == commerce.get("order_id"), "fulfillment order mismatch")
    require(execution.get("payment_status") == "SUCCEEDED", "offline payment status mismatch")
    require(execution.get("fulfillment_status") == "SUCCEEDED", "offline fulfillment status mismatch")
    require(execution.get("sidecar_ready") is True, "payment/fulfillment sidecar not ready")
    require(execution.get("real_payment_executed") is False, "must not claim real payment")
    require(execution.get("real_fulfillment_executed") is False, "must not claim real fulfillment")

    require(trace.get("validation_status") == "VALID", "same-journey authoritative trace is not VALID")
    origins = set(trace.get("action_origin_types") or [])
    require(EXPECTED_ORIGINS.issubset(origins), f"trace origin coverage incomplete: {sorted(origins)}")
    require(trace.get("order_id") == commerce.get("order_id"), "trace order mismatch")
    require(trace.get("request_id") == commerce.get("request_id"), "trace request mismatch")
    require(trace.get("payment_request_id") == commerce.get("request_id"), "trace payment request mismatch")
    require(trace.get("payment_order_id") == commerce.get("order_id"), "trace payment order mismatch")

    correlations = payload.get("correlations")
    require(isinstance(correlations, list), "correlations must be list")
    by_id = {item.get("correlation_id"): item for item in correlations if isinstance(item, Mapping)}
    require(set(by_id) == EXPECTED_CORRELATIONS, f"correlation ids mismatch: {sorted(by_id)}")
    for cid in sorted(EXPECTED_CORRELATIONS):
        item = mapping(by_id[cid], cid)
        require(item.get("equal") is True, f"{cid} is not equal")
        require(item.get("source_path") and item.get("target_path"), f"{cid} missing evidence paths")
        require(item.get("source_value") == item.get("target_value"), f"{cid} values do not match")

    require(guardrails.get("external_network_calls") == 0, "external network call detected")
    require(guardrails.get("real_webshop_buy_now_count") == 0, "real Buy Now detected")
    require(guardrails.get("real_payment_execution_count") == 0, "real payment detected")
    require(guardrails.get("real_fulfillment_execution_count") == 0, "real fulfillment detected")
    require(guardrails.get("instruction_promoted_to_authorization") is False, "instruction was promoted to authority")
    require(guardrails.get("experiment_context_promoted_to_webshop_fact") is False, "experiment context promoted to WebShop fact")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    require(sha256(ACCEPTED) == EXPECTED_ACCEPTED_SHA, "accepted autonomous evidence changed")
    payload = json.loads(args.result.read_text(encoding="utf-8"))
    validate(mapping(payload, "result"))

    # Mechanical negative control: one broken correlation must be rejected.
    tampered = copy.deepcopy(payload)
    tampered["correlations"][0]["target_value"] = "tampered-value"
    rejected = False
    try:
        validate(mapping(tampered, "tampered"))
    except AssertionError:
        rejected = True
    require(rejected, "tampered correlation was not rejected")

    print("PASS: 8/8 same-journey correlations are mechanically continuous; tampered correlation fails closed; no real side effects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

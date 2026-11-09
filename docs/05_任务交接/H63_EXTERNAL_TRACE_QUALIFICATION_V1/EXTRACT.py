"""H63 bounded offline CartTrace observation extractor.

Reads exactly six frozen JSONL previews; never invokes source tools, product code,
network, model, PSP, or payment actions. All positive facts cite original JSONL
line objects, using RFC6901 JSON pointers and canonical value SHA-256.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import uuid

TASK = Path(__file__).resolve().parent
LEDGER = TASK / "ATTEMPT_LEDGER.json"
OUTPUT = TASK / "MEASUREMENT.json"
SAMPLE_IDS = [f"S{i:02d}" for i in range(1, 7)]
FACT_KEYS = ("user_request", "explicit_confirmation", "checkout_snapshot",
             "payment_request", "payment_tool_result", "order_tool_result", "correlation")
PAYMENT_CALLS = {"pay", "request_payment", "shop_pay_payment_request"}
CHECKOUT_CALLS = {"create_checkout", "update_checkout", "complete_checkout"}
STARTED_AT = "2026-11-07T08:23:18Z"
ZERO_COSTS = dict(network_calls=0, model_calls=0, payment_calls=0,
                  installation_calls=0, product_calls=0)


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    # Write first to a temporary path and atomically replace the ledger/result.
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def citation(row, path="/message/content"):
    message = row["value"]["message"]
    if path == "/message/content":
        val = message["content"]
    elif path == "/message/toolCalls":
        val = message["toolCalls"]
    elif path == "/message/toolCallId":
        val = message["toolCallId"]
    else:
        raise ValueError("unsupported citation pointer")
    return {"line": row["line"], "pointer": path, "value_sha256": sha(val)}


def fact(status, reason, *citations):
    assert status in {"PRESENT", "ABSENT", "AMBIGUOUS"}
    assert (status != "ABSENT" or not citations)
    return {"status": status, "citations": list(citations), "reason": reason}


def parse_result(row):
    if not row:
        return None
    msg = row["value"]["message"]
    if msg.get("role") != "tool":
        return None
    try:
        result = json.loads(msg["content"])
    except (ValueError, TypeError, KeyError):
        return None
    if not isinstance(result, dict) or result.get("ucp", {}).get("status") == "error":
        return None
    return result


def get_events(rows):
    messages = [{"line": i + 1, "value": row} for i, row in enumerate(rows)
                if row.get("type") == "message"]
    requests = []
    results = {}
    for msg in messages:
        value = msg["value"]["message"]
        if value.get("role") == "assistant":
            for index, call in enumerate(value.get("toolCalls", [])):
                if not isinstance(call, dict):
                    continue
                func = call.get("function", {})
                if not isinstance(func, dict):
                    continue
                try:
                    args = json.loads(func.get("arguments", "{}"))
                except (ValueError, TypeError):
                    args = {}
                requests.append({"request": msg, "id": call.get("id"),
                                 "name": func.get("name"), "args": args})
        if value.get("role") == "tool" and value.get("toolCallId"):
            results.setdefault(value["toolCallId"], msg)
    pairs = []
    for request in requests:
        response = results.get(request["id"])
        pairs.append(dict(request, response=response, result=parse_result(response)))
    return messages, pairs


def checkout_id(result):
    if not isinstance(result, dict):
        return None
    for key in ("checkout_id", "id"):
        value = result.get(key)
        if isinstance(value, str) and value.startswith("checkout-"):
            return value
    return None


def source_sample(sample_id, index):
    relative = f"references/TRACE_{index:02d}.jsonl"
    source = TASK / relative
    rows = [json.loads(s) for s in source.read_text(encoding="utf-8").splitlines() if s.strip()]
    if not rows or rows[0]["type"] != "session" or not rows[0].get("id"):
        raise ValueError(f"invalid original source framing: {relative}")
    msgs, pairs = get_events(rows)
    users = [msg for msg in msgs if msg["value"]["message"].get("role") == "user"]
    if not users:
        raise ValueError(f"missing user request: {sample_id}")
    user = users[0]
    confirmation = [msg for msg in users[1:] if re.search(
        r"\b(place|placing) the order\b", msg["value"]["message"].get("content", ""), flags=re.I)]
    cart_consent = [msg for msg in users[1:] if re.search(
        r"\b(go ahead|yes, that one)\b", msg["value"]["message"].get("content", ""), flags=re.I)]

    checkout_pairs = [p for p in pairs if p["name"] in CHECKOUT_CALLS
                      and checkout_id(p["result"])]
    snapshot = checkout_pairs[-1] if checkout_pairs else None
    pay_requests = [p for p in pairs if p["name"] in PAYMENT_CALLS]
    pay_pair = next((p for p in reversed(pay_requests) if p["result"] is not None),
                    pay_requests[-1] if pay_requests else None)
    wallet_only = [p for p in pairs if p["name"] == "load_payment_data"
                   and p["result"] is not None]
    orders = [p for p in pairs if p["name"] == "get_order"
              and isinstance(p["result"], dict)
              and (p["result"].get("id") or p["result"].get("checkout_id"))]
    order = orders[-1] if orders else None
    observed_checkout_id = checkout_id(snapshot["result"]) if snapshot else None
    observed_order_checkout_id = order["result"].get("checkout_id") if order else None
    payment_bound_checkout = any(
        p["args"].get("checkout_id") == observed_checkout_id
        for p in pay_requests if isinstance(p["args"], dict)
    )
    # For direct 'pay' calls the checkout ID is in the tool response, not in pay args.
    payment_bound_checkout = payment_bound_checkout or bool(
        pay_pair and pay_pair["result"] and
        pay_pair["result"].get("checkout_id") == observed_checkout_id
    )
    full_chain = bool(observed_checkout_id and order and pay_pair and
                      pay_pair["result"] and payment_bound_checkout and
                      observed_order_checkout_id == observed_checkout_id)
    facts = {}
    facts["user_request"] = fact(
        "PRESENT", f"Original shopper intent at JSONL line {user['line']}; no authenticated identity inferred.",
        citation(user))
    if confirmation:
        yes = confirmation[-1]
        facts["explicit_confirmation"] = fact(
            "PRESENT", f"User explicitly asks to place an order at original line {yes['line']}; text is not a signed mandate.",
            citation(yes))
    elif cart_consent:
        yes = cart_consent[-1]
        facts["explicit_confirmation"] = fact(
            "AMBIGUOUS", f"User consent at line {yes['line']} is to a product/cart, not a priced payment execution.",
            citation(yes))
    else:
        facts["explicit_confirmation"] = fact(
            "ABSENT", "No separate user instruction explicitly consenting to a priced order/payment was found.")
    if snapshot:
        facts["checkout_snapshot"] = fact(
            "PRESENT", f"Store tool output at original line {snapshot['response']['line']} contains a checkout ID; transcript only.",
            citation(snapshot["response"]))
    else:
        facts["checkout_snapshot"] = fact(
            "ABSENT", "No successful checkout tool response with an identifiable checkout ID in this preview.")
    if pay_requests:
        p = pay_requests[-1]
        facts["payment_request"] = fact(
            "PRESENT", f"Agent invokes {p['name']} tool call {p['id']} at line {p['request']['line']}; tool invocation is not a PSP charge.",
            citation(p["request"], "/message/toolCalls"))
    else:
        facts["payment_request"] = fact(
            "ABSENT", "No direct pay/request_payment/shop_pay_payment_request invocation; wallet-data load and checkout completion are not direct charge proof.")
    if pay_pair and pay_pair["response"] and pay_pair["result"]:
        facts["payment_tool_result"] = fact(
            "PRESENT",
            f"Tool reply at line {pay_pair['response']['line']} matches payment-related call ID {pay_pair['id']}; a wallet token or receipt is only transcript evidence.",
            citation(pay_pair["response"]))
    elif wallet_only:
        wallet = wallet_only[-1]
        facts["payment_tool_result"] = fact(
            "AMBIGUOUS", f"Wallet-data response {wallet['id']} exists at line {wallet['response']['line']}, but no direct payment call/settlement evidence.",
            citation(wallet["response"]))
    else:
        facts["payment_tool_result"] = fact(
            "ABSENT", "No returned tool record tied by call ID to a direct payment invocation.")
    if order:
        facts["order_tool_result"] = fact(
            "PRESENT", f"get_order tool result {order['id']} at line {order['response']['line']}; not independent merchant backend state.",
            citation(order["response"]))
    else:
        facts["order_tool_result"] = fact(
            "ABSENT", "No get_order tool response in this preview; cart or checkout results do not establish an order.")
    if full_chain:
        facts["correlation"] = fact(
            "PRESENT", f"Checkout {observed_checkout_id}, payment-related tool call {pay_pair['id']} and get_order response {order['id']} link using call IDs and checkout ID; simulated transcript only.",
            citation(snapshot["response"]), citation(pay_pair["request"], "/message/toolCalls"),
            citation(pay_pair["response"]), citation(order["response"]))
    elif snapshot and order:
        facts["correlation"] = fact(
            "AMBIGUOUS", "Checkout and order are individually recorded, but no direct payment-call-to-order chain is observable.",
            citation(snapshot["response"]), citation(order["response"]))
    else:
        facts["correlation"] = fact(
            "ABSENT", "No complete checkout/payment/order identity chain with original call-id-linked tool results.")

    def mapping(status, keys, reason):
        return {"input_status": status, "fact_keys": keys, "reason": reason}
    seen = lambda *keys: [key for key in keys if facts[key]["status"] == "PRESENT"]
    contracts = {
        "P1": mapping("OBSERVABLE", ["user_request"], "User request is observable as transcript text; no user identity or delegated authority is verified."),
        "P2": mapping("PARTIAL" if facts["explicit_confirmation"]["status"] != "ABSENT" else "MISSING",
                      seen("explicit_confirmation", "checkout_snapshot"),
                      "Explicit priced-order consent plus checkout amount requires independent binding; variant/cart choice alone does not authorize payment."),
        "P3": mapping("PARTIAL" if snapshot and pay_pair else "MISSING",
                      seen("checkout_snapshot", "payment_request", "correlation"),
                      "Checkout and payment call may be compared within a session, but no signed mandate or durable binding is visible."),
        "P4": mapping("PARTIAL" if pay_pair and pay_pair["response"] else "MISSING",
                      seen("payment_request", "payment_tool_result"),
                      "Only tool invocation/result is present; independent provider settlement and charge side effects remain unproven."),
        "P5": mapping("PARTIAL" if order else "MISSING",
                      seen("order_tool_result", "correlation"),
                      "Order tool response can be read from transcript, not independently checked against merchant order/stock state."),
    }
    # Add machine-inspectable links, each grounded by the original-source citations above.
    links = [
        {"tool": p["name"], "call_id": p["id"], "call_line": p["request"]["line"],
         "result_line": p["response"]["line"] if p["response"] else None,
         "linked_by_exact_call_id": bool(p["response"])}
        for p in pairs if p["name"] in CHECKOUT_CALLS | PAYMENT_CALLS | {"get_order", "load_payment_data"}
    ]
    return {"sample_id": sample_id, "file": relative, "episode_id": rows[0]["id"],
            "evidence_level": "TRANSCRIPT_ONLY", "facts": facts, "contracts": contracts,
            "observations": {
                "checkout_id_from_tool_result": observed_checkout_id,
                "order_checkout_id_from_tool_result": observed_order_checkout_id,
                "full_transcript_correlation": full_chain,
                "payment_tool_name": pay_pair["name"] if pay_pair else None,
                "call_result_links": links,
            }}


def refresh_cost(ledger, data):
    start = datetime.fromisoformat(STARTED_AT.replace("Z", "+00:00"))
    end = datetime.now(timezone.utc)
    # conservative wall-clock envelope, including reading/checker maintenance
    minutes = max(1, math.ceil((end - start).total_seconds() / 60))
    if minutes > 120:
        raise ValueError("active time budget exceeded")
    ledger["active_minutes"] = max(int(ledger.get("active_minutes", 0)), minutes)
    ledger["work_intervals_utc"] = [{"start": STARTED_AT, "end": utc_now(),
                                     "basis": "conservative elapsed session envelope"}]
    data["cost"] = dict(active_minutes=ledger["active_minutes"], **ZERO_COSTS)
    write(LEDGER, ledger)
    write(OUTPUT, data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-cost", action="store_true")
    args = parser.parse_args()
    ledger = read(LEDGER)
    if args.refresh_cost:
        refresh_cost(ledger, read(OUTPUT))
        print(json.dumps({"refreshed_cost_minutes": ledger["active_minutes"]}))
        return
    if ledger["sample_attempts"]:
        raise ValueError("append-only reserved sample attempts exist; do not reset or repeat blindly")
    samples = []
    for i, sample_id in enumerate(SAMPLE_IDS, 1):
        if len(ledger["sample_attempts"]) >= 18:
            raise ValueError("sample budget exhausted")
        attempt = {"id": str(uuid.uuid4()), "sample_id": sample_id,
                   "started_at": utc_now(), "terminal_status": "STARTED"}
        ledger["sample_attempts"].append(attempt)
        write(LEDGER, ledger)  # durable reservation before reading this source
        try:
            samples.append(source_sample(sample_id, i))
            attempt["terminal_status"] = "SUCCEEDED"
        except BaseException as exc:
            attempt["terminal_status"] = "FAILED"
            attempt["error_type"] = type(exc).__name__
            raise
        finally:
            attempt["finished_at"] = utc_now()
            write(LEDGER, ledger)
    measurement = {
        "task_id": TASK.name, "samples": samples,
        "decision": {
            "candidate_classification": "REFERENCE_ONLY",
            "view_decision": "BOUNDED_READONLY_COMPARISON_CANDIDATE",
            "candidate_sample_ids": ["S02", "S03", "S06"],
            "question": "Can original shopper price confirmation be linked without assistant prose to checkout ID/amount, explicit payment tool call and its correlated result, and get_order identity across S03/S06, while treating S02's wallet-data/complete_checkout as an unverified direct-pay path?",
            "reason": "Two previews include user order consent plus direct payment tool calls and correlated order responses; a third has order completion with only wallet-data tools. This supports one bounded comparison of transcript observability, not an efficacy or safety conclusion.",
            "limits": ["preview_only", "not_unseen_holdout", "no_independent_backend_state",
                       "no_verified_actor_identity", "no_product_control_measurement",
                       "no_customer_value_evidence"],
            "missing_inputs": ["real user/delegate identity and signed scope",
                               "independent PSP authorization/capture record",
                               "independent merchant order and stock state",
                               "trusted policy/mandate and canonical money-unit context",
                               "out-of-sample provenance and production merchant context"],
        },
    }
    refresh_cost(ledger, measurement)
    print(json.dumps({"samples": len(samples), "attempts": len(ledger["sample_attempts"]),
                      "candidate": measurement["decision"]["view_decision"],
                      "minutes": ledger["active_minutes"]}))


if __name__ == "__main__":
    main()

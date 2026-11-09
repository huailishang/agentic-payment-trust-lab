"""H64 pure amount-cap observation over explicitly sourced input facts.

This module never establishes authorization, identity, settlement or control quality.
All absent, malformed, unordered or unlinked evidence is NOT_JUDGEABLE.
"""
def evaluate(record: dict) -> str:
    unknown = "NOT_JUDGEABLE"
    if not isinstance(record, dict) or record.get("exact_link") is not True:
        return unknown
    consent = record.get("consent")
    payment = record.get("payment")
    if not isinstance(consent, dict) or not isinstance(payment, dict):
        return unknown
    if consent.get("origin") != "user_message":
        return unknown
    if payment.get("origin") not in {"tool_response", "protocol_response", "backend_event"}:
        return unknown
    cc = consent.get("checkout_id")
    pc = payment.get("checkout_id")
    if not isinstance(cc, str) or not cc or cc != pc:
        return unknown
    if consent.get("currency") != "USD" or payment.get("currency") != "USD":
        return unknown
    for item in (consent, payment):
        if type(item.get("amount_minor")) is not int or item["amount_minor"] < 0:
            return unknown
        if type(item.get("seq")) is not int or item["seq"] < 0:
            return unknown
    if consent["seq"] >= payment["seq"]:
        return unknown
    return ("OVER_CAP_OBSERVED"
            if payment["amount_minor"] > consent["amount_minor"]
            else "WITHIN_CAP_OBSERVED")

"""Sanitized schema checks; these do not independently prove live execution."""
FIELDS = {
    "status", "provider", "method", "trade_no_sha256", "active",
    "binding_checks_requested", "binding_checks_passed",
    "provider_response_signature_verified", "reason_codes",
}
BINDINGS = {"trade_no", "out_trade_no", "resource_id", "amount"}


def string_set(value, allowed):
    if type(value) is not list or any(type(x) is not str for x in value):
        return None
    result = set(value)
    return result if len(result) == len(value) and result <= allowed else None


def validate(data, case):
    # Reject unknown fields and free text without echoing rejected input.
    if type(data) is not dict or set(data) != FIELDS:
        return "unexpected fact schema"
    if case not in {"valid", "tampered-proof"}:
        return "unknown case"
    if data["provider"] != "ALIPAY_AGENT_PAY_SANDBOX":
        return "wrong provider"
    if data["method"] != "alipay.aipay.agent.payment.verify":
        return "wrong method"
    digest = data["trade_no_sha256"]
    if type(digest) is not str or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        return "invalid trade digest"
    if data["provider_response_signature_verified"] is not True:
        return "provider signature not verified"
    if type(data["active"]) is not bool:
        return "invalid active type"
    requested = string_set(data["binding_checks_requested"], BINDINGS)
    passed = string_set(data["binding_checks_passed"], BINDINGS)
    if requested != BINDINGS or passed is None:
        return "all four binding dimensions must be requested"
    if case == "valid":
        if data["status"] != "VALID" or data["active"] is not True:
            return "valid case not active/VALID"
        if passed != BINDINGS or data["reason_codes"] != ["VERIFIED"]:
            return "valid case lacks complete binding evidence"
    else:
        if data["status"] != "INVALID" or data["active"] is not False:
            return "negative case not inactive/INVALID"
        reasons = string_set(data["reason_codes"], {"PROVIDER_REJECTED_PROOF", "PROVIDER_INACTIVE"})
        if not reasons:
            return "negative must reflect provider rejection, not local/network failure"
    return None


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result

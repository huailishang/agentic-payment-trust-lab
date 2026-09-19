from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

REQUIRED = {
    "status",
    "provider",
    "method",
    "trade_no_sha256",
    "active",
    "binding_checks_requested",
    "binding_checks_passed",
    "provider_response_signature_verified",
    "reason_codes",
}

FORBIDDEN_PATTERNS = (
    "private",
    "password",
    "payment_proof",
    "client_session",
    "raw_response",
    "secret",
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, choices=["valid", "tampered-proof"])
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    missing = sorted(REQUIRED - set(data))
    if missing:
        print("FAIL missing fields: " + ",".join(missing))
        return 1

    flat_keys = " ".join(str(k).lower() for k in data.keys())
    if any(p in flat_keys for p in FORBIDDEN_PATTERNS):
        print("FAIL sensitive/raw field name present in evidence")
        return 1

    if data["provider"] != "ALIPAY_AGENT_PAY_SANDBOX":
        print("FAIL wrong provider")
        return 1
    if data["method"] != "alipay.aipay.agent.payment.verify":
        print("FAIL wrong provider method")
        return 1
    if not SHA256_RE.match(str(data["trade_no_sha256"])):
        print("FAIL trade_no_sha256 is not a sha256 digest")
        return 1
    if data["provider_response_signature_verified"] is not True:
        print("FAIL provider response signature not verified")
        return 1

    requested = list(data["binding_checks_requested"])
    passed = list(data["binding_checks_passed"])
    if not requested:
        print("FAIL no binding checks requested")
        return 1

    if args.case == "valid":
        if data["status"] != "VALID" or data["active"] is not True:
            print("FAIL valid case did not produce VALID/active")
            return 1
        if set(passed) != set(requested):
            print("FAIL valid case did not pass every requested binding")
            return 1
    else:
        if data["status"] != "INVALID":
            print("FAIL tampered proof was not INVALID")
            return 1

    print(f"PASS live fact audit case={args.case}")
    print("secret/raw fields present=false")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

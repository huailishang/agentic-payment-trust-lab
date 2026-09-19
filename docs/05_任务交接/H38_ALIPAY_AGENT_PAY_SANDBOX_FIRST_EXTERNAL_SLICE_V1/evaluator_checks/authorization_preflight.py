from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CURRENT = (ROOT / "CURRENT.md").read_text(encoding="utf-8")

REQUIRED = [
    "AIPAY_APP_ID",
    "AIPAY_PRIVATE_PKCS_KEY",
    "AIPAY_ALIPAY_PUBLIC_KEY",
    "H38_TRADE_NO",
    "H38_PAYMENT_PROOF",
    "H38_EXPECTED_OUT_TRADE_NO",
    "H38_EXPECTED_AMOUNT",
    "H38_EXPECTED_RESOURCE_ID",
]

def main() -> int:
    if "task_id: H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1" not in CURRENT:
        print("FAIL wrong active task")
        return 1
    if "authorization_api_call: true" not in CURRENT:
        print("FAIL sandbox API authority is not enabled in CURRENT")
        return 1

    missing = [name for name in REQUIRED if not os.environ.get(name)]
    if missing:
        print("BLOCKED missing sandbox-only environment inputs:")
        for name in missing:
            print(name)
        print("No values were printed.")
        return 1

    gateway = os.environ.get(
        "AIPAY_GATEWAY",
        "https://openapi-sandbox.dl.alipaydev.com/gateway.do",
    )
    if gateway != "https://openapi-sandbox.dl.alipaydev.com/gateway.do":
        print("FAIL gateway must be the frozen Alipay sandbox gateway")
        return 1

    print("PASS authorization/secret preflight")
    print("sandbox credentials present=true")
    print("live fixture present=true")
    print("secret values printed=false")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

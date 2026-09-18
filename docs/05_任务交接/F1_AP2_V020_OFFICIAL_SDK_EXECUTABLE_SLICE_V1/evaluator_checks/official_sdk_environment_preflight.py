from __future__ import annotations

import importlib.metadata
import json

EXPECTED_PYDANTIC = "2.12.5"

def main() -> None:
    actual = importlib.metadata.version("pydantic")
    assert actual == EXPECTED_PYDANTIC, (actual, EXPECTED_PYDANTIC)

    from ap2.sdk.generated.open_payment_mandate import OpenPaymentMandate
    from ap2.sdk.generated.payment_mandate import PaymentMandate
    from ap2.sdk.generated.checkout_mandate import CheckoutMandate

    observed = {
        "OpenPaymentMandate": f"{OpenPaymentMandate.__module__}.{OpenPaymentMandate.__name__}",
        "PaymentMandate": f"{PaymentMandate.__module__}.{PaymentMandate.__name__}",
        "CheckoutMandate": f"{CheckoutMandate.__module__}.{CheckoutMandate.__name__}",
    }
    expected = {
        "OpenPaymentMandate": "ap2.sdk.generated.open_payment_mandate.OpenPaymentMandate",
        "PaymentMandate": "ap2.sdk.generated.payment_mandate.PaymentMandate",
        "CheckoutMandate": "ap2.sdk.generated.checkout_mandate.CheckoutMandate",
    }
    assert observed == expected, observed
    print(json.dumps({"result": "PASS", "pydantic": actual, "classes": observed}, sort_keys=True))

if __name__ == "__main__":
    main()

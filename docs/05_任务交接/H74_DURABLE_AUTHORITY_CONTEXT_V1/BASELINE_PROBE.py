"""Run only against the reconstructed, locked original src tree."""
import json
from agentic_payment_experiment.stripe_checkout_lab import StripeLabLedger
from agentic_payment_experiment.adapters.stripe_checkout import StripeCheckoutAdapter

names = [(StripeLabLedger, "record_authority"), (StripeLabLedger, "load_authority"), (StripeCheckoutAdapter, "create_stored_session"), (StripeCheckoutAdapter, "authorize_stored_browser_payment")]
present = {name: hasattr(owner, name) for owner, name in names}
if any(present.values()):
    raise RuntimeError("original baseline unexpectedly has durable API; stop and re-evaluate")
print(json.dumps({"schema": "h74-baseline-observation/v1", "baseline": "UNSUPPORTED_DURABLE_API", "api_present": present, "units": ["N01_COLD_RESUME", "R01_PAID_READ_ONLY_RECOVERY", "D01_RECEIPT_RECOVERY"], "security_failure_claimed": False, "external_actions": 0}))

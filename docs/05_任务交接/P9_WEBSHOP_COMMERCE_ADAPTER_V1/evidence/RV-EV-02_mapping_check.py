from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path
import json

from agentic_payment_experiment.adapters.webshop import (
    REQUIRED_LIMITATIONS,
    adapt_webshop_purchase_candidate,
)

snapshot = json.loads(
    Path("samples/external/webshop/pre_buy_now_candidate_v1.json").read_text(encoding="utf-8")
)
adapted = adapt_webshop_purchase_candidate(snapshot)
assert adapted.ready and adapted.order is not None and adapted.payment_request is not None
assert adapted.user_intent_text == snapshot["instruction_text"]
assert "cargo pants" in adapted.user_intent_text
assert "Console Table" in adapted.order.items[0].name
assert adapted.order.total_amount == Decimal("877.80")
assert adapted.order.order_id == adapted.payment_request.order_ref
assert adapted.order.total_amount == adapted.payment_request.amount
assert adapted.order.currency == adapted.payment_request.currency == "USD"
assert adapted.order.merchant == adapted.payment_request.merchant
assert adapted.order.payee == adapted.payment_request.payee
assert adapted.order.mandate_ref == adapted.payment_request.authority_ref
assert adapted.order.authority_version_ref == adapted.payment_request.authority_version_ref
assert set(REQUIRED_LIMITATIONS).issubset(adapted.limitations)
try:
    adapted.source_commit = "changed"  # type: ignore[misc]
    raise AssertionError("adaptation dataclass is mutable")
except FrozenInstanceError:
    pass
print(
    json.dumps(
        {
            "ready": adapted.ready,
            "instruction": adapted.user_intent_text,
            "selected_product": adapted.order.items[0].name,
            "order_id": adapted.order.order_id,
            "request_id": adapted.payment_request.request_id,
            "total": str(adapted.order.total_amount),
            "bindings_match": True,
            "limitations": list(adapted.limitations),
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
)

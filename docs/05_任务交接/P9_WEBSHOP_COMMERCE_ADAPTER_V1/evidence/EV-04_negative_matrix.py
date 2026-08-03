from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from agentic_payment_experiment.adapters import webshop as module
from agentic_payment_experiment.adapters.webshop import adapt_webshop_purchase_candidate

FIXTURE_PATH = ROOT / "samples/external/webshop/pre_buy_now_candidate_v1.json"
OUTPUT_PATH = Path(__file__).with_name("EV-04.negative_matrix.json")
fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def changed(path: tuple[str, ...], value: object, *, remove: bool = False) -> dict[str, object]:
    candidate = deepcopy(fixture)
    target = candidate
    for key in path[:-1]:
        target = target[key]
    if remove:
        target.pop(path[-1])
    else:
        target[path[-1]] = value
    return candidate


cases = [
    ("missing_instruction", changed(("instruction_text",), None, remove=True), "instruction_text"),
    ("missing_asin", changed(("product", "asin"), None, remove=True), "product.asin"),
    ("missing_title", changed(("product", "title"), None, remove=True), "product.title"),
    ("missing_price", changed(("product", "unit_price"), None, remove=True), "product.unit_price"),
    ("missing_currency", changed(("experiment_context", "currency"), None, remove=True), "experiment_context.currency"),
    ("missing_context_bridge", changed(("experiment_context", "merchant"), None, remove=True), "experiment_context.merchant"),
    ("malformed_price", changed(("product", "unit_price"), "not-money"), "product.unit_price"),
    ("negative_price", changed(("product", "unit_price"), "-1.00"), "product.unit_price"),
    ("zero_quantity", changed(("product", "quantity"), 0), "product.quantity"),
    ("negative_quantity", changed(("product", "quantity"), -1), "product.quantity"),
    ("noninteger_quantity", changed(("product", "quantity"), 1.5), "product.quantity"),
    ("total_inconsistent", changed(("product", "order_total"), "1.00"), "product.order_total"),
    ("missing_selected_options", changed(("product", "selected_options"), None, remove=True), "product.selected_options"),
    ("wrong_source_commit", changed(("source", "webshop_commit"), "0" * 40), "source.webshop_commit"),
    ("missing_provenance", changed(("source", "provenance"), None, remove=True), "source.provenance"),
    ("mutable_provenance", changed(("source", "provenance", "immutable"), False), "source.provenance.immutable"),
    ("wrong_smoke_hash", changed(("source", "smoke_result_sha256"), "0" * 64), "source.smoke_result_sha256"),
    (
        "wrong_asset_hash",
        changed(("source", "asset_hashes", "items_shuffle_1000.json"), "0" * 64),
        "source.asset_hashes.items_shuffle_1000.json",
    ),
    ("buy_now_unavailable", changed(("buy_now_available",), False), "buy_now_available"),
    ("buy_now_executed", changed(("buy_now_executed",), True), "buy_now_executed"),
]
forbidden_action = deepcopy(fixture)
forbidden_action["actions_executed"].append("click[buy now]")
cases.append(("buy_now_action_present", forbidden_action, "actions_executed.buy_now_forbidden"))

matrix: list[dict[str, object]] = []
for name, candidate, expected in cases:
    adapted = adapt_webshop_purchase_candidate(candidate)
    assert not adapted.ready
    assert adapted.order is None
    assert adapted.payment_request is None
    assert expected in adapted.missing_fields
    matrix.append(
        {
            "case": name,
            "ready": adapted.ready,
            "order_present": adapted.order is not None,
            "payment_request_present": adapted.payment_request is not None,
            "missing_fields": list(adapted.missing_fields),
            "expected_missing_field": expected,
        }
    )

baseline = adapt_webshop_purchase_candidate(fixture)
assert baseline.payment_request is not None
mismatched = replace(
    baseline.payment_request,
    amount=baseline.payment_request.amount + Decimal("1.00"),
)
with patch.object(module, "_build_transaction_request", return_value=mismatched):
    adapted = adapt_webshop_purchase_candidate(fixture)
assert not adapted.ready
assert adapted.order is None
assert adapted.payment_request is None
assert adapted.missing_fields == ("order_request_binding",)
matrix.append(
    {
        "case": "order_request_binding_mismatch",
        "ready": adapted.ready,
        "order_present": adapted.order is not None,
        "payment_request_present": adapted.payment_request is not None,
        "missing_fields": list(adapted.missing_fields),
        "expected_missing_field": "order_request_binding",
    }
)

unknown = deepcopy(fixture)
unknown["webshop_reward"] = 1.0
unknown["allow_purchase"] = True
adapted = adapt_webshop_purchase_candidate(unknown)
assert adapted.ready
assert adapted.unmapped_fields == (
    "top_level.allow_purchase",
    "top_level.webshop_reward",
)
matrix.append(
    {
        "case": "unknown_top_level_fields",
        "ready": adapted.ready,
        "order_present": adapted.order is not None,
        "payment_request_present": adapted.payment_request is not None,
        "missing_fields": list(adapted.missing_fields),
        "unmapped_fields": list(adapted.unmapped_fields),
    }
)

payload = {
    "case_count": len(matrix),
    "all_fail_closed_cases_passed": True,
    "cases": matrix,
}
OUTPUT_PATH.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

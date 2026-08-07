"""Compatibility entry point for the accepted happy-path product trace."""

from __future__ import annotations

from .adapters.webshop import WebShopCommerceAdaptation
from .authoritative_trace import ProductAuthoritativeTrace
from .models import FulfillmentRecord, IntentMandate, PaymentExecutionRecord
from .webshop_payment_sidecar import WebShopPaymentFulfilmentOutcome
from .webshop_runtime_gate import WebShopBuyNowGateOutcome
from .webshop_sidecar_trace_toolkit import build_sidecar_product_trace


T01_PROFILE = "WEBSHOP_NORMAL_PURCHASE_V2"


def build_t01_happy_path_trace(
    *,
    gate_outcome: WebShopBuyNowGateOutcome,
    adaptation: WebShopCommerceAdaptation,
    mandate: IntentMandate,
    payment: PaymentExecutionRecord,
    fulfillment: FulfillmentRecord,
    base_outcome: WebShopPaymentFulfilmentOutcome,
) -> ProductAuthoritativeTrace | None:
    """Delegate to the single Sidecar toolkit and retain the old API."""

    if base_outcome.initial_payment != payment:
        return None
    if base_outcome.effective_payment != payment:
        return None
    trace = build_sidecar_product_trace(
        gate_outcome=gate_outcome,
        adaptation=adaptation,
        mandate=mandate,
        fulfillment=fulfillment,
        base_outcome=base_outcome,
    )
    if trace is None or trace.profile != T01_PROFILE:
        return None
    return trace


__all__ = ["T01_PROFILE", "build_t01_happy_path_trace"]

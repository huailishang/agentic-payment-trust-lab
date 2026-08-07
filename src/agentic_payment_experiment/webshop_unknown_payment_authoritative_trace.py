"""Compatibility entry point for the accepted UNKNOWN-payment recovery trace."""

from __future__ import annotations

from .adapters.webshop import WebShopCommerceAdaptation
from .authoritative_trace import ProductAuthoritativeTrace
from .models import IntentMandate
from .webshop_payment_sidecar import WebShopPaymentFulfilmentOutcome
from .webshop_runtime_gate import WebShopBuyNowGateOutcome
from .webshop_sidecar_trace_toolkit import build_sidecar_product_trace


UNKNOWN_PAYMENT_RECOVERY_PROFILE = "WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2"


def build_unknown_payment_recovery_trace(
    *,
    gate_outcome: WebShopBuyNowGateOutcome,
    adaptation: WebShopCommerceAdaptation,
    mandate: IntentMandate,
    base_outcome: WebShopPaymentFulfilmentOutcome,
) -> ProductAuthoritativeTrace | None:
    """Delegate to the single Sidecar toolkit and retain the old API."""

    trace = build_sidecar_product_trace(
        gate_outcome=gate_outcome,
        adaptation=adaptation,
        mandate=mandate,
        fulfillment=None,
        base_outcome=base_outcome,
    )
    if trace is None or trace.profile != UNKNOWN_PAYMENT_RECOVERY_PROFILE:
        return None
    return trace


__all__ = [
    "UNKNOWN_PAYMENT_RECOVERY_PROFILE",
    "build_unknown_payment_recovery_trace",
]

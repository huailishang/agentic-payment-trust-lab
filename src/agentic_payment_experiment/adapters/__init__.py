"""Protocol adapters that translate external snapshots into neutral models."""

from .acp import ACPOrderAdaptation, adapt_acp_checkout_pair
from .acp_webhook import (
    ACP_WEBHOOK_DEFAULT_TOLERANCE_SECONDS,
    verify_acp_webhook_signature,
)
from .ap2 import (
    AP2Adaptation,
    AP2FlowAdaptation,
    AP2FlowMode,
    adapt_ap2_flow_snapshot,
    adapt_ap2_snapshot,
    evaluate_ap2_flow,
)
from .ap2_signed_instruction import verify_ap2_merchant_authorization_signature
from .webshop import WebShopCommerceAdaptation, adapt_webshop_purchase_candidate
from .x402 import (
    X402Adaptation,
    X402AdaptationStatus,
    X402DeliveryAttempt,
    X402SideEffectRecord,
    adapt_x402_fixture,
    compute_requirement_digest,
)

__all__ = [
    "ACPOrderAdaptation",
    "ACP_WEBHOOK_DEFAULT_TOLERANCE_SECONDS",
    "AP2Adaptation",
    "AP2FlowAdaptation",
    "AP2FlowMode",
    "adapt_acp_checkout_pair",
    "verify_acp_webhook_signature",
    "adapt_ap2_flow_snapshot",
    "adapt_ap2_snapshot",
    "evaluate_ap2_flow",
    "verify_ap2_merchant_authorization_signature",
    "WebShopCommerceAdaptation",
    "adapt_webshop_purchase_candidate",
    "X402Adaptation",
    "X402AdaptationStatus",
    "X402DeliveryAttempt",
    "X402SideEffectRecord",
    "adapt_x402_fixture",
    "compute_requirement_digest",
]

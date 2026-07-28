"""Protocol adapters that translate external snapshots into neutral models."""

from .acp import ACPOrderAdaptation, adapt_acp_checkout_pair
from .ap2 import (
    AP2Adaptation,
    AP2FlowAdaptation,
    AP2FlowMode,
    adapt_ap2_flow_snapshot,
    adapt_ap2_snapshot,
    evaluate_ap2_flow,
)

__all__ = [
    "ACPOrderAdaptation",
    "AP2Adaptation",
    "AP2FlowAdaptation",
    "AP2FlowMode",
    "adapt_acp_checkout_pair",
    "adapt_ap2_flow_snapshot",
    "adapt_ap2_snapshot",
    "evaluate_ap2_flow",
]

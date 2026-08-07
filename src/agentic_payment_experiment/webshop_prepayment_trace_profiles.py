"""Frozen declarative profiles for the WebShop prepayment trace family."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import Decision


class PrepaymentScenarioKind(str, Enum):
    PRICE_INCREASE = "PRICE_INCREASE"
    PRICE_DECREASE = "PRICE_DECREASE"
    PAYEE_CHANGE = "PAYEE_CHANGE"


@dataclass(frozen=True)
class PrepaymentTraceProfile:
    profile_name: str
    scenario_kind: PrepaymentScenarioKind
    expected_decision: Decision
    required_issue_codes: tuple[str, ...]
    required_difference_codes: tuple[str, ...]


_PRICE_CHANGE_CODES = (
    "order_item_unit_amount_changed",
    "order_total_changed",
)

PREPAYMENT_TRACE_PROFILES = (
    PrepaymentTraceProfile(
        profile_name="WEBSHOP_PREPAYMENT_T02_V2",
        scenario_kind=PrepaymentScenarioKind.PRICE_INCREASE,
        expected_decision=Decision.CONFIRMATION_REQUIRED,
        required_issue_codes=_PRICE_CHANGE_CODES,
        required_difference_codes=_PRICE_CHANGE_CODES,
    ),
    PrepaymentTraceProfile(
        profile_name="WEBSHOP_PREPAYMENT_T03_V2",
        scenario_kind=PrepaymentScenarioKind.PRICE_DECREASE,
        expected_decision=Decision.CONFIRMATION_REQUIRED,
        required_issue_codes=_PRICE_CHANGE_CODES,
        required_difference_codes=_PRICE_CHANGE_CODES,
    ),
    PrepaymentTraceProfile(
        profile_name="WEBSHOP_PREPAYMENT_T04_V2",
        scenario_kind=PrepaymentScenarioKind.PAYEE_CHANGE,
        expected_decision=Decision.INDETERMINATE,
        required_issue_codes=("order_payee_changed",),
        required_difference_codes=(),
    ),
)


__all__ = [
    "PREPAYMENT_TRACE_PROFILES",
    "PrepaymentScenarioKind",
    "PrepaymentTraceProfile",
]

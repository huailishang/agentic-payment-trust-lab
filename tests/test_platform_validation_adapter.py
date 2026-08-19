import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment import IntentMandate, TransactionRequest, validate_request
from agentic_payment_experiment.platform_validation_adapter import adapt_validation_result_to_platform


def _mandate_and_request(amount: str):
    now = datetime(2026, 7, 11, 12, 0, tzinfo=timezone(timedelta(hours=8)))
    mandate = IntentMandate(
        mandate_id="mandate-001",
        user_id="user-001",
        max_amount=Decimal("550.00"),
        confirmation_above=Decimal("500.00"),
        allowed_merchants=frozenset({"merchant-a"}),
        allowed_categories=frozenset({"shoes"}),
        expires_at=now + timedelta(hours=1),
        max_count=1,
        expected_agent_id="agent-shop-001",
    )
    request = TransactionRequest(
        request_id="request-001",
        amount=Decimal(amount),
        merchant="merchant-a",
        category="shoes",
        occurred_at=now,
        agent_id="agent-shop-001",
    )
    return mandate, request


def test_real_payment_deny_result_maps_to_platform_contract() -> None:
    mandate, request = _mandate_and_request("560.00")
    native = validate_request(mandate, request)

    result = adapt_validation_result_to_platform(native)

    assert result["schema_version"] == "validation-result-v0.1"
    assert result["verdict"] == "FAIL"
    assert result["validator_id"] == "payment.validator"
    assert result["validator_version"] == "mandate-rules-v0.1"
    assert any(item["code"] == "over_budget" for item in result["findings"])
    assert any(
        ref["ref"] == "request.amount" and ref["locator"] == "over_budget"
        for ref in result["evidence_refs"]
    )
    assert "metadata" not in result
    assert "context" not in result
    assert "extensions" not in result


def test_real_payment_confirmation_maps_to_blocked_not_runtime_action() -> None:
    mandate, request = _mandate_and_request("520.00")
    native = validate_request(mandate, request)

    result = adapt_validation_result_to_platform(native)

    assert result["verdict"] == "BLOCKED"
    assert any(item["code"] == "confirmation_threshold_exceeded" for item in result["findings"])
    assert "REQUEST_CONFIRMATION" not in str(result)

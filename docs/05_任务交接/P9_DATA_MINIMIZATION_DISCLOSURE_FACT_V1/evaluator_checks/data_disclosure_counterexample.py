from __future__ import annotations

from agentic_payment_experiment.data_disclosure import evaluate_data_disclosure
from agentic_payment_experiment.trusted_execution.execution_facts import VerificationStatus


def _assert_valid_minimization() -> None:
    fact = evaluate_data_disclosure(
        required_fields=("recipient_name", "destination_ref"),
        allowed_fields=(
            "recipient_name",
            "destination_ref",
            "birth_year",
            "profile_note",
        ),
        requested_fields=(
            "recipient_name",
            "destination_ref",
            "birth_year",
            "profile_note",
        ),
    )
    assert fact.status is VerificationStatus.VALID, fact
    assert set(fact.approved_fields) == {"recipient_name", "destination_ref"}, fact
    assert set(fact.blocked_fields) == {"birth_year", "profile_note"}, fact
    assert "data_disclosure_nonessential_field_blocked" in fact.reason_codes, fact


def _assert_missing_required_fails_closed() -> None:
    fact = evaluate_data_disclosure(
        required_fields=("account_ref", "delivery_ref"),
        allowed_fields=("account_ref", "delivery_ref"),
        requested_fields=("account_ref",),
    )
    assert fact.status is not VerificationStatus.VALID, fact
    assert "data_disclosure_required_field_missing" in fact.reason_codes, fact
    assert "delivery_ref" not in fact.approved_fields, fact


def _assert_required_not_allowed_fails_closed() -> None:
    fact = evaluate_data_disclosure(
        required_fields=("account_ref", "delivery_ref"),
        allowed_fields=("account_ref",),
        requested_fields=("account_ref", "delivery_ref"),
    )
    assert fact.status is not VerificationStatus.VALID, fact
    assert "data_disclosure_required_field_not_allowed" in fact.reason_codes, fact
    assert "delivery_ref" not in fact.approved_fields, fact


def main() -> None:
    _assert_valid_minimization()
    _assert_missing_required_fails_closed()
    _assert_required_not_allowed_fails_closed()
    print(
        "PASS: protocol-neutral data disclosure properties hold for synthetic field names; "
        "nonessential fields are blocked and required-field failures fail closed"
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

import unittest

from agentic_payment_experiment.data_disclosure import evaluate_data_disclosure
from agentic_payment_experiment.trusted_execution.execution_facts import VerificationStatus


class DataDisclosureTest(unittest.TestCase):
    def test_optional_fields_are_blocked_without_over_refusal(self) -> None:
        fact = evaluate_data_disclosure(
            required_fields=("name", "shipping_address", "payment_card_secure_field"),
            allowed_fields=(
                "name",
                "shipping_address",
                "payment_card_secure_field",
                "email",
                "date_of_birth",
            ),
            requested_fields=(
                "name",
                "shipping_address",
                "payment_card_secure_field",
                "date_of_birth",
                "about_you",
            ),
        )

        self.assertIs(VerificationStatus.VALID, fact.status)
        self.assertEqual(
            ("name", "shipping_address", "payment_card_secure_field"),
            fact.approved_fields,
        )
        self.assertEqual(("date_of_birth", "about_you"), fact.blocked_fields)
        self.assertIn("data_disclosure_nonessential_field_blocked", fact.reason_codes)

    def test_missing_required_field_fails_closed(self) -> None:
        fact = evaluate_data_disclosure(
            required_fields=("account_ref", "delivery_ref"),
            allowed_fields=("account_ref", "delivery_ref"),
            requested_fields=("account_ref",),
        )

        self.assertIs(VerificationStatus.INVALID, fact.status)
        self.assertEqual((), fact.approved_fields)
        self.assertIn("data_disclosure_required_field_missing", fact.reason_codes)

    def test_required_field_not_allowed_fails_closed(self) -> None:
        fact = evaluate_data_disclosure(
            required_fields=("account_ref", "delivery_ref"),
            allowed_fields=("account_ref",),
            requested_fields=("account_ref", "delivery_ref"),
        )

        self.assertIs(VerificationStatus.INVALID, fact.status)
        self.assertEqual((), fact.approved_fields)
        self.assertIn("data_disclosure_required_field_not_allowed", fact.reason_codes)

    def test_malformed_field_identifier_fails_closed(self) -> None:
        fact = evaluate_data_disclosure(
            required_fields=("account_ref", "bad field"),
            allowed_fields=("account_ref", "bad field"),
            requested_fields=("account_ref", "bad field"),
        )

        self.assertIs(VerificationStatus.INVALID, fact.status)
        self.assertEqual((), fact.approved_fields)
        self.assertEqual(("data_disclosure_invalid_evidence",), fact.reason_codes)


if __name__ == "__main__":
    unittest.main()

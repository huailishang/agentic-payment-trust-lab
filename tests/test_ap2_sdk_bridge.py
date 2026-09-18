from __future__ import annotations

import base64
import hashlib
import unittest
from decimal import Decimal

from agentic_payment_experiment.adapters import adapt_verified_ap2_v020_sdk_objects
from agentic_payment_experiment.trusted_execution import VerificationStatus

try:
    from ap2.sdk.generated.checkout_mandate import CheckoutMandate
    from ap2.sdk.generated.open_payment_mandate import (
        AgentRecurrence,
        AllowedPayees,
        AmountRange,
        ExecutionDate,
        Frequency,
        OpenPaymentMandate,
    )
    from ap2.sdk.generated.payment_mandate import PaymentMandate
    from ap2.sdk.generated.types.amount import Amount
    from ap2.sdk.generated.types.merchant import Merchant
    from ap2.sdk.generated.types.payment_instrument import PaymentInstrument

    SDK_AVAILABLE = True
except ModuleNotFoundError:
    SDK_AVAILABLE = False


def checkout_hash(raw_checkout_jwt: str) -> str:
    digest = hashlib.sha256(raw_checkout_jwt.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def fixture():
    raw_checkout_jwt = (
        "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.f1-official-sdk-test.signature"
    )
    verified_hash = checkout_hash(raw_checkout_jwt)
    merchant = Merchant(id="merchant-boundary", name="Boundary Merchant")
    open_payment = OpenPaymentMandate(
        constraints=[
            AmountRange(currency="CNY", max=55000),
            AllowedPayees(allowed=[merchant]),
            AgentRecurrence(
                frequency=Frequency.ON_DEMAND,
                max_occurrences=1,
            ),
            ExecutionDate(not_after="2026-12-31T23:59:59+08:00"),
        ],
        cnf={
            "jwk": {
                "kty": "EC",
                "crv": "P-256",
                "x": "synthetic-x",
                "y": "synthetic-y",
            }
        },
    )
    payment = PaymentMandate(
        transaction_id=verified_hash,
        payee=merchant,
        payment_amount=Amount(amount=52000, currency="CNY"),
        payment_instrument=PaymentInstrument(
            id="synthetic-instrument",
            type="card",
        ),
        execution_date="2026-09-18T10:00:00+08:00",
    )
    checkout = CheckoutMandate(
        checkout_jwt=raw_checkout_jwt,
        checkout_hash=verified_hash,
    )
    context = {
        "mandate_id": "mandate-f1-official-sdk-test",
        "user_id": "synthetic-user",
        "category": "synthetic-category",
        "allowed_categories": ["synthetic-category"],
        "confirmation_above_minor": 60000,
        "agent_id": "synthetic-agent",
    }
    return open_payment, payment, checkout, context


@unittest.skipUnless(SDK_AVAILABLE, "official AP2 SDK environment required")
class AP2SDKBridgeTests(unittest.TestCase):
    def call(self, open_payment, payment, checkout, context):
        return adapt_verified_ap2_v020_sdk_objects(
            open_payment,
            payment,
            checkout,
            experiment_context=context,
        )

    def assert_blocked(self, result, status, reason):
        self.assertIs(result.boundary_status, status)
        self.assertIn(reason, result.reason_codes)
        self.assertFalse(result.ready)
        self.assertIsNone(result.mandate)
        self.assertIsNone(result.request)

    def test_official_objects_reach_existing_boundary(self) -> None:
        open_payment, payment, checkout, context = fixture()
        result = self.call(open_payment, payment, checkout, context)

        self.assertIs(result.boundary_status, VerificationStatus.VALID)
        self.assertTrue(result.ready)
        self.assertIsNotNone(result.mandate)
        self.assertIsNotNone(result.request)

    def test_plain_dict_open_payment_is_rejected(self) -> None:
        open_payment, payment, checkout, context = fixture()
        result = self.call(open_payment.model_dump(), payment, checkout, context)
        self.assert_blocked(
            result,
            VerificationStatus.INVALID,
            "ap2_sdk_open_payment_object_invalid",
        )

    def test_plain_dict_payment_is_rejected(self) -> None:
        open_payment, payment, checkout, context = fixture()
        result = self.call(open_payment, payment.model_dump(), checkout, context)
        self.assert_blocked(
            result,
            VerificationStatus.INVALID,
            "ap2_sdk_payment_object_invalid",
        )

    def test_plain_dict_checkout_is_rejected(self) -> None:
        open_payment, payment, checkout, context = fixture()
        result = self.call(open_payment, payment, checkout.model_dump(), context)
        self.assert_blocked(
            result,
            VerificationStatus.INVALID,
            "ap2_sdk_checkout_object_invalid",
        )

    def test_wrong_checkout_vct_is_rejected_by_h34(self) -> None:
        open_payment, payment, checkout, context = fixture()
        bad_checkout = checkout.model_copy(update={"vct": "mandate.checkout.999"})
        result = self.call(open_payment, payment, bad_checkout, context)
        self.assert_blocked(
            result,
            VerificationStatus.INVALID,
            "ap2_checkout_vct_invalid",
        )

    def test_tampered_checkout_is_rejected_by_h34(self) -> None:
        open_payment, payment, checkout, context = fixture()
        tampered = checkout.model_copy(
            update={"checkout_jwt": checkout.checkout_jwt + ".tampered"}
        )
        result = self.call(open_payment, payment, tampered, context)
        self.assert_blocked(
            result,
            VerificationStatus.INVALID,
            "ap2_checkout_hash_mismatch",
        )

    def test_wrong_payment_checkout_binding_is_rejected_by_h34(self) -> None:
        open_payment, payment, checkout, context = fixture()
        wrong_payment = payment.model_copy(
            update={"transaction_id": "wrong-checkout"}
        )
        result = self.call(open_payment, wrong_payment, checkout, context)
        self.assert_blocked(
            result,
            VerificationStatus.INVALID,
            "ap2_payment_checkout_binding_mismatch",
        )

    def test_official_amount_and_merchant_map_to_canonical_request(self) -> None:
        open_payment, payment, checkout, context = fixture()
        result = self.call(open_payment, payment, checkout, context)

        self.assertIsNotNone(result.request)
        self.assertEqual(result.request.amount, Decimal("520"))
        self.assertEqual(result.request.currency, "CNY")
        self.assertEqual(result.request.merchant, "merchant-boundary")
        self.assertEqual(result.request.request_id, checkout.checkout_hash)

    def test_missing_context_field_stays_blocked_by_existing_mapping(self) -> None:
        open_payment, payment, checkout, context = fixture()
        missing_context = dict(context)
        missing_context.pop("category")
        result = self.call(open_payment, payment, checkout, missing_context)

        self.assert_blocked(
            result,
            VerificationStatus.MISSING_EVIDENCE,
            "ap2_canonical_mapping_not_ready",
        )
        self.assertIn("experiment_context.category", result.missing_fields)

    def test_non_mapping_context_fails_closed_at_bridge(self) -> None:
        open_payment, payment, checkout, _ = fixture()
        result = self.call(open_payment, payment, checkout, None)

        self.assert_blocked(
            result,
            VerificationStatus.MISSING_EVIDENCE,
            "ap2_sdk_experiment_context_invalid",
        )
        self.assertIn("experiment_context", result.missing_fields)


if __name__ == "__main__":
    unittest.main()

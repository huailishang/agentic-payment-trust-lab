from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agentic_payment_experiment.models import Order, OrderItem
from agentic_payment_experiment.trusted_execution import (
    BindingStatus,
    ConfirmationStatus,
    create_confirmation_record,
    execute_with_confirmation_gate,
    verify_confirmation_binding,
)


class ConfirmationBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 7, 30, tzinfo=timezone.utc)
        self.order = Order(
            order_id="order-1", order_version="v1", merchant="Nike 官方店", payee="Nike 官方店",
            items=(OrderItem("shoe-1", "鞋", "shoes", 1, Decimal("480.00")),),
            total_amount=Decimal("480.00"), currency="CNY", quote_expires_at=self.now + timedelta(hours=1),
            fulfilment_terms="standard", mandate_ref="mandate-1",
        )
        self.record = create_confirmation_record(
            confirmation_id="confirmation-1", authority_id="mandate-1", authority_version="v1",
            order=self.order, confirmed_at=self.now, expires_at=self.now + timedelta(minutes=10),
        )

    def verify(self, record="_default", order="_default", **changes):
        return verify_confirmation_binding(
            self.record if record == "_default" else record, self.order if order == "_default" else order,
            authority_id=changes.get("authority_id", "mandate-1"), authority_version=changes.get("authority_version", "v1"),
            checked_at=changes.get("checked_at", self.now + timedelta(minutes=1)),
        )

    def test_same_confirmed_content_is_valid_and_only_valid_can_execute(self) -> None:
        fact = self.verify()
        calls: list[str] = []
        outcome = execute_with_confirmation_gate(fact, lambda: calls.append("paid") or "payment-1")
        self.assertEqual(BindingStatus.VALID, fact.status)
        self.assertEqual("confirmation_binding_match", fact.reason)
        self.assertTrue(outcome.executed)
        self.assertEqual(["paid"], calls)

    def test_price_change_invalidates_confirmation_and_blocks_callback(self) -> None:
        changed = replace(self.order, total_amount=Decimal("490.00"))
        fact = self.verify(order=changed)
        calls: list[str] = []
        outcome = execute_with_confirmation_gate(fact, lambda: calls.append("paid"))
        self.assertEqual(BindingStatus.INVALID, fact.status)
        self.assertEqual("order_hash_mismatch", fact.reason)
        self.assertEqual("total_amount_changed", fact.invalidated_by)
        self.assertFalse(outcome.executed)
        self.assertEqual([], calls)

    def test_quantity_change_is_explained_and_requires_reconfirmation(self) -> None:
        changed_item = replace(self.order.items[0], quantity=2)
        fact = self.verify(order=replace(self.order, items=(changed_item,), total_amount=Decimal("960.00")))
        self.assertEqual(BindingStatus.INVALID, fact.status)
        self.assertEqual("items_changed", fact.invalidated_by)

    def test_missing_record_or_current_order_fails_closed(self) -> None:
        for record, order, reason in ((None, self.order, "confirmation_record_missing"), (self.record, None, "current_order_missing")):
            with self.subTest(reason=reason):
                fact = self.verify(record=record, order=order)
                calls: list[str] = []
                outcome = execute_with_confirmation_gate(fact, lambda: calls.append("paid"))
                self.assertEqual(BindingStatus.MISSING_EVIDENCE, fact.status)
                self.assertEqual(reason, fact.reason)
                self.assertFalse(outcome.executed)
                self.assertEqual([], calls)

    def test_expired_confirmation_and_version_change_are_invalid(self) -> None:
        expired = self.verify(checked_at=self.now + timedelta(minutes=11))
        version_changed = self.verify(order=replace(self.order, order_version="v2"))
        self.assertEqual((BindingStatus.INVALID, "confirmation_expired"), (expired.status, expired.invalidated_by))
        self.assertEqual((BindingStatus.INVALID, "order_version_changed"), (version_changed.status, version_changed.invalidated_by))

    def test_inactive_confirmation_cannot_be_reused(self) -> None:
        fact = self.verify(record=replace(self.record, status=ConfirmationStatus.INVALIDATED))
        self.assertEqual(BindingStatus.INVALID, fact.status)
        self.assertEqual("confirmation_status_changed", fact.invalidated_by)


if __name__ == "__main__":
    unittest.main()

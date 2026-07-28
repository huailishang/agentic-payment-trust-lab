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
    canonical_hash,
    canonical_json,
    canonicalize,
    verify_hash,
)


class HashingTests(unittest.TestCase):
    def test_canonical_json_ignores_dictionary_key_order(self) -> None:
        left = {"merchant": "A", "amount": "100.00"}
        right = {"amount": "100.00", "merchant": "A"}
        self.assertEqual(canonical_json(left), canonical_json(right))
        self.assertEqual(canonical_hash(left), canonical_hash(right))

    def test_modified_value_changes_hash(self) -> None:
        original = {"merchant": "A", "amount": "100.00"}
        modified = {"merchant": "A", "amount": "101.00"}
        self.assertNotEqual(canonical_hash(original), canonical_hash(modified))

    def test_verify_hash_detects_tampering(self) -> None:
        original = {"order_id": "O-1", "category": "shoes"}
        expected = canonical_hash(original)
        self.assertTrue(verify_hash(expected, original))
        self.assertFalse(verify_hash(expected, {"order_id": "O-1", "category": "membership"}))

    def test_unknown_algorithm_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonical_hash({"x": 1}, algorithm="not-a-real-hash")

    def test_decimal_equivalent_representations_share_one_canonical_value(self) -> None:
        values = (Decimal("100.00"), Decimal("100"), Decimal("1.0000E+2"))
        normalized = [canonicalize(value) for value in values]
        self.assertTrue(all(item == normalized[0] for item in normalized))
        self.assertEqual({"$type": "decimal", "value": "100"}, normalized[0])

    def test_decimal_and_text_do_not_collide(self) -> None:
        self.assertNotEqual(canonical_hash(Decimal("100.00")), canonical_hash("100"))

    def test_decimal_rejects_non_finite_values(self) -> None:
        for value in (Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    canonicalize(value)

    def test_aware_datetimes_for_same_instant_are_equivalent(self) -> None:
        utc = datetime(2026, 7, 27, 1, 2, 3, 4000, tzinfo=timezone.utc)
        plus_eight = utc.astimezone(timezone(timedelta(hours=8)))
        self.assertEqual(canonicalize(utc), canonicalize(plus_eight))
        self.assertEqual(
            {"$type": "datetime", "value": "2026-07-27T01:02:03.004000Z"},
            canonicalize(utc),
        )

    def test_naive_datetime_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonicalize(datetime(2026, 7, 27, 1, 2, 3))

    def test_list_and_tuple_are_equivalent_but_sequence_order_is_preserved(self) -> None:
        self.assertEqual(canonical_hash(["a", "b"]), canonical_hash(("a", "b")))
        self.assertNotEqual(canonical_hash(["a", "b"]), canonical_hash(["b", "a"]))

    def test_missing_field_and_null_are_distinct(self) -> None:
        self.assertNotEqual(canonical_hash({}), canonical_hash({"receipt_ref": None}))

    def test_unicode_canonical_equivalents_are_normalized_to_nfc(self) -> None:
        composed = "Café"
        decomposed = "Cafe\u0301"
        self.assertEqual(canonical_json({"name": composed}), canonical_json({"name": decomposed}))
        self.assertEqual(canonical_hash({"name": composed}), canonical_hash({"name": decomposed}))

    def test_unicode_key_collision_after_normalization_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonicalize({"é": 1, "e\u0301": 2})

    def test_reserved_type_key_is_rejected_for_input_mapping(self) -> None:
        with self.assertRaises(ValueError):
            canonicalize({"$type": "decimal", "value": "100"})

    def test_float_is_rejected_instead_of_silently_entering_financial_hashes(self) -> None:
        with self.assertRaises(TypeError):
            canonicalize(0.1)

    def test_real_order_dataclass_is_canonicalizable(self) -> None:
        order = self._order()
        normalized = canonicalize(order)
        self.assertEqual("order-1", normalized["order_id"])
        self.assertEqual({"$type": "decimal", "value": "480"}, normalized["total_amount"])
        self.assertEqual(
            {"$type": "datetime", "value": "2026-07-27T01:00:00.000000Z"},
            normalized["quote_expires_at"],
        )
        self.assertIsInstance(normalized["items"], list)

    def test_order_version_is_part_of_the_digest(self) -> None:
        order = self._order()
        changed_version = replace(order, order_version="v2")
        self.assertNotEqual(canonical_hash(order), canonical_hash(changed_version))

    def test_order_item_sequence_is_currently_part_of_the_digest(self) -> None:
        order = self._order(two_items=True)
        reordered = replace(order, items=tuple(reversed(order.items)))
        self.assertNotEqual(canonical_hash(order), canonical_hash(reordered))

    @staticmethod
    def _order(*, two_items: bool = False) -> Order:
        items = [
            OrderItem(
                item_id="shoe-1",
                name="Road Runner",
                category="shoes",
                quantity=1,
                unit_amount=Decimal("480.00"),
            )
        ]
        if two_items:
            items.append(
                OrderItem(
                    item_id="lace-1",
                    name="Laces",
                    category="shoes",
                    quantity=1,
                    unit_amount=Decimal("20.0"),
                )
            )
        return Order(
            order_id="order-1",
            order_version="v1",
            merchant="merchant-a",
            payee="merchant-a",
            items=tuple(items),
            total_amount=Decimal("480.00" if not two_items else "500.00"),
            currency="CNY",
            quote_expires_at=datetime(
                2026,
                7,
                27,
                9,
                0,
                tzinfo=timezone(timedelta(hours=8)),
            ),
            fulfilment_terms="standard delivery",
            mandate_ref="mandate-1",
            service_id="running-shoe-delivery",
            candidate_rails=("card",),
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sys
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agentic_payment_experiment.trusted_execution import (
    BindingStatus,
    canonical_hash,
    verify_binding,
)


class BindingTests(unittest.TestCase):
    def test_same_canonical_object_is_valid(self) -> None:
        authorized = {"amount": Decimal("100.00"), "items": ("a", "b")}
        expected = canonical_hash(authorized)

        result = verify_binding(
            expected,
            {"items": ["a", "b"], "amount": Decimal("100")},
        )

        self.assertEqual(BindingStatus.VALID, result.status)
        self.assertEqual("binding_match", result.reason_code)
        self.assertEqual(expected, result.expected_digest)
        self.assertEqual(expected, result.actual_digest)

    def test_changed_object_is_invalid_without_making_a_business_decision(self) -> None:
        expected = canonical_hash({"amount": Decimal("100")})
        result = verify_binding(expected, {"amount": Decimal("101")})

        self.assertEqual(BindingStatus.INVALID, result.status)
        self.assertEqual("binding_mismatch", result.reason_code)
        self.assertNotEqual(result.expected_digest, result.actual_digest)

    def test_missing_expected_digest_is_missing_evidence(self) -> None:
        for expected in (None, "", "   "):
            with self.subTest(expected=expected):
                result = verify_binding(expected, {"x": 1})
                self.assertEqual(BindingStatus.MISSING_EVIDENCE, result.status)
                self.assertEqual("expected_digest_missing", result.reason_code)

    def test_malformed_expected_digest_is_missing_evidence(self) -> None:
        result = verify_binding("not-a-sha256-digest", {"x": 1})
        self.assertEqual(BindingStatus.MISSING_EVIDENCE, result.status)
        self.assertEqual("expected_digest_invalid", result.reason_code)

    def test_missing_actual_object_is_missing_evidence(self) -> None:
        result = verify_binding(canonical_hash({"x": 1}), None)
        self.assertEqual(BindingStatus.MISSING_EVIDENCE, result.status)
        self.assertEqual("actual_object_missing", result.reason_code)

    def test_noncanonicalizable_actual_object_is_missing_evidence(self) -> None:
        expected = canonical_hash({"occurred_at": "2026-07-27T00:00:00Z"})
        result = verify_binding(expected, {"occurred_at": datetime(2026, 7, 27)})
        self.assertEqual(BindingStatus.MISSING_EVIDENCE, result.status)
        self.assertEqual("actual_object_not_canonicalizable", result.reason_code)

    def test_expected_digest_is_case_insensitive(self) -> None:
        value = {"x": 1}
        expected = canonical_hash(value).upper()
        result = verify_binding(expected, value)
        self.assertEqual(BindingStatus.VALID, result.status)

    def test_unknown_algorithm_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            verify_binding("00", {"x": 1}, algorithm="not-a-real-hash")


if __name__ == "__main__":
    unittest.main()

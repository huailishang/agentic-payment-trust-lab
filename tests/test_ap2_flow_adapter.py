from __future__ import annotations

import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path

from agentic_payment_experiment.adapters import (
    AP2FlowMode,
    adapt_ap2_flow_snapshot,
    evaluate_ap2_flow,
)
from agentic_payment_experiment.models import Decision


class AP2FlowAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.hp_snapshot = json.loads(
            (root / "samples" / "protocol_snapshots" / "AP2_v020_HP_cards.json").read_text(
                encoding="utf-8"
            )
        )
        self.hnp_snapshot = json.loads(
            (root / "samples" / "protocol_snapshots" / "AP2_v020_HNP_cards.json").read_text(
                encoding="utf-8"
            )
        )

    def test_human_present_confirmed_cart_maps_to_neutral_models_and_allows(self) -> None:
        adapted = adapt_ap2_flow_snapshot(self.hp_snapshot)

        self.assertTrue(adapted.ready)
        self.assertEqual(AP2FlowMode.HUMAN_PRESENT, adapted.flow_mode)
        self.assertTrue(adapted.realtime_confirmation_required)
        self.assertTrue(adapted.realtime_confirmation_satisfied)
        self.assertEqual(Decimal("120.0"), adapted.mandate.max_amount)
        self.assertEqual(Decimal("120.0"), adapted.request.amount)
        self.assertEqual("merchant-a", adapted.request.merchant)

        result = evaluate_ap2_flow(adapted)

        self.assertEqual(Decision.ALLOW, result.decision)
        self.assertIn("ap2_user_authorization_signature_not_verified", adapted.unmapped_fields)

    def test_human_present_without_user_authorization_requires_confirmation(self) -> None:
        snapshot = copy.deepcopy(self.hp_snapshot)
        snapshot["payment_mandate"]["user_authorization"] = None

        adapted = adapt_ap2_flow_snapshot(snapshot)
        result = evaluate_ap2_flow(adapted)

        self.assertTrue(adapted.ready)
        self.assertTrue(adapted.realtime_confirmation_required)
        self.assertFalse(adapted.realtime_confirmation_satisfied)
        self.assertEqual(Decision.CONFIRMATION_REQUIRED, result.decision)
        self.assertIn("ap2_user_confirmation_required", {issue.code for issue in result.issues})

    def test_human_not_present_with_preauthorization_and_trigger_allows(self) -> None:
        adapted = adapt_ap2_flow_snapshot(self.hnp_snapshot)
        result = evaluate_ap2_flow(adapted)

        self.assertTrue(adapted.ready)
        self.assertEqual(AP2FlowMode.HUMAN_NOT_PRESENT, adapted.flow_mode)
        self.assertFalse(adapted.realtime_confirmation_required)
        self.assertTrue(adapted.preauthorization_present)
        self.assertTrue(adapted.trigger_condition_satisfied)
        self.assertEqual(Decision.ALLOW, result.decision)
        self.assertIn("ap2_intent_authorization_signature_not_verified", adapted.unmapped_fields)

    def test_human_not_present_without_preauthorization_is_indeterminate(self) -> None:
        snapshot = copy.deepcopy(self.hnp_snapshot)
        snapshot["authorization_evidence"]["intent_mandate_user_signed"] = False

        adapted = adapt_ap2_flow_snapshot(snapshot)
        result = evaluate_ap2_flow(adapted)

        self.assertTrue(adapted.ready)
        self.assertFalse(adapted.preauthorization_present)
        self.assertEqual(Decision.INDETERMINATE, result.decision)
        self.assertIn("ap2_preauthorization_missing", {issue.code for issue in result.issues})

    def test_payment_mandate_must_bind_to_cart_payment_details(self) -> None:
        snapshot = copy.deepcopy(self.hp_snapshot)
        snapshot["payment_mandate"]["payment_mandate_contents"]["payment_details_id"] = "other-payment"

        adapted = adapt_ap2_flow_snapshot(snapshot)
        result = evaluate_ap2_flow(adapted)

        self.assertFalse(adapted.ready)
        self.assertIn("payment_details_id_mismatch", adapted.flow_errors)
        self.assertEqual(Decision.INDETERMINATE, result.decision)
        self.assertIn("ap2_flow_invalid", {issue.code for issue in result.issues})


if __name__ == "__main__":
    unittest.main()

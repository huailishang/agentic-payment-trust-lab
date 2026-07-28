import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment.adapters import adapt_acp_checkout_pair
from agentic_payment_experiment.scenario_loader import load_scenario
from agentic_payment_experiment.validator import validate_request


class ACPOrderAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.scenario = load_scenario(
            self.root / "samples" / "scenarios" / "S09_order_total_changed.json"
        )
        self.snapshot_path = (
            self.root
            / "samples"
            / "protocol_snapshots"
            / "ACP_S09_order_total_changed.json"
        )
        self.snapshot = json.loads(self.snapshot_path.read_text(encoding="utf-8"))

    def test_maps_fixed_acp_checkout_pair_to_exact_s09_neutral_orders(self) -> None:
        adapted = adapt_acp_checkout_pair(self.snapshot)

        self.assertTrue(adapted.ready)
        self.assertEqual("ACP-2026-04-17-teaching-fixture", adapted.protocol_version)
        self.assertEqual(self.scenario.authorized_order, adapted.authorized_order)
        self.assertEqual(self.scenario.final_order, adapted.final_order)
        self.assertEqual("480.00", format(adapted.authorized_order.total_amount, "f"))
        self.assertEqual("490.00", format(adapted.final_order.total_amount, "f"))

    def test_acp_path_and_neutral_path_produce_identical_s09_result(self) -> None:
        adapted = adapt_acp_checkout_pair(self.snapshot)
        self.assertTrue(adapted.ready)

        neutral_result = validate_request(
            self.scenario.mandate,
            self.scenario.request,
            seen_request_ids=self.scenario.seen_request_ids,
            authorized_order=self.scenario.authorized_order,
            final_order=self.scenario.final_order,
        )
        protocol_result = validate_request(
            self.scenario.mandate,
            self.scenario.request,
            seen_request_ids=self.scenario.seen_request_ids,
            authorized_order=adapted.authorized_order,
            final_order=adapted.final_order,
        )

        self.assertEqual(neutral_result.decision, protocol_result.decision)
        self.assertEqual(neutral_result.issues, protocol_result.issues)
        self.assertEqual(neutral_result.evidence, protocol_result.evidence)
        self.assertEqual(neutral_result.order_differences, protocol_result.order_differences)
        self.assertEqual(neutral_result.rule_version, protocol_result.rule_version)
        self.assertEqual(
            ["order_total_changed", "order_item_unit_amount_changed"],
            [item.code for item in protocol_result.order_differences],
        )

    def test_refuses_to_invent_missing_checkout_objects(self) -> None:
        adapted = adapt_acp_checkout_pair(
            {"protocol_version": "ACP-2026-04-17-teaching-fixture"}
        )

        self.assertFalse(adapted.ready)
        self.assertIn("authorized_checkout", adapted.missing_fields)
        self.assertIn("final_checkout", adapted.missing_fields)
        self.assertIn("experiment_context", adapted.missing_fields)

    def test_bridge_fields_and_unverified_boundaries_remain_explicit(self) -> None:
        adapted = adapt_acp_checkout_pair(self.snapshot)

        self.assertTrue(adapted.ready)
        for gap in (
            "seller_identity_from_endpoint_context_not_verified",
            "payee_identity_not_verified",
            "mandate_binding_from_experiment_context",
            "item_category_from_experiment_context",
            "quote_expiry_from_experiment_context",
            "payment_handler_not_mapped",
            "order_webhook_signature_not_verified",
            "no_live_acp_endpoint_or_conformance_test",
        ):
            with self.subTest(gap=gap):
                self.assertIn(gap, adapted.unmapped_fields)


if __name__ == "__main__":
    unittest.main()

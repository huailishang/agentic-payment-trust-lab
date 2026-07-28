import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment import Decision, validate_request
from agentic_payment_experiment.adapters import adapt_ap2_snapshot


class AP2AdapterTest(unittest.TestCase):
    def snapshot(self) -> dict:
        return {
            "protocol_version": "AP2-v0.2.0-fixture",
            "open_payment_mandate": {
                "vct": "mandate.payment.open.1",
                "constraints": [
                    {
                        "type": "payment.amount_range",
                        "currency": "CNY",
                        "max": 55000,
                    },
                    {
                        "type": "payment.allowed_payees",
                        "allowed": [{"id": "merchant-a"}],
                    },
                    {
                        "type": "payment.agent_recurrence",
                        "frequency": "ON_DEMAND",
                        "max_occurrences": 1,
                    },
                    {
                        "type": "payment.execution_date",
                        "not_after": "2026-07-12T12:00:00+08:00",
                    },
                ],
                "cnf": {"jwk": {"kid": "fixture-only"}},
            },
            "payment_mandate": {
                "vct": "mandate.payment.1",
                "transaction_id": "request-ap2-001",
                "payee": {"id": "merchant-a"},
                "payment_amount": {"currency": "CNY", "value": 52000},
                "execution_date": "2026-07-11T12:00:00+08:00",
                "payment_instrument": {"id": "mock-instrument"},
            },
            "experiment_context": {
                "mandate_id": "mandate-ap2-001",
                "user_id": "user-001",
                "category": "shoes",
                "allowed_categories": ["shoes"],
                "confirmation_above_minor": 50000,
                "agent_id": "agent-shop-001",
            },
        }

    def test_maps_snapshot_without_installing_ap2_sdk(self) -> None:
        adapted = adapt_ap2_snapshot(self.snapshot())
        self.assertTrue(adapted.ready)
        self.assertEqual(Decimal("550.00"), adapted.mandate.max_amount)
        self.assertEqual(Decimal("520.00"), adapted.request.amount)
        self.assertIn("sd_jwt_delegation_chain_not_verified", adapted.unmapped_fields)

        result = validate_request(adapted.mandate, adapted.request)
        self.assertEqual(Decision.CONFIRMATION_REQUIRED, result.decision)

    def test_refuses_to_invent_missing_protocol_objects(self) -> None:
        adapted = adapt_ap2_snapshot({"protocol_version": "AP2-v0.2.0-fixture"})
        self.assertFalse(adapted.ready)
        self.assertIn("open_payment_mandate", adapted.missing_fields)
        self.assertIn("payment_mandate", adapted.missing_fields)


if __name__ == "__main__":
    unittest.main()

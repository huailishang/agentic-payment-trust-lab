from __future__ import annotations

import unittest
from pathlib import Path

from agentic_payment_experiment.models import Decision
from agentic_payment_experiment.paybench_challenges import load_paybench_challenges
from agentic_payment_experiment.paybench_current_system import run_current_rules_on_paybench


class PayBenchCurrentSystemTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.challenge_set = load_paybench_challenges(
            root / "samples" / "external" / "paybench" / "phase1_selected_10.json"
        )

    def test_current_rules_execute_supported_six_and_expose_four_gaps(self) -> None:
        result = run_current_rules_on_paybench(self.challenge_set)

        self.assertEqual(10, result.total)
        self.assertEqual(6, result.supported)
        self.assertEqual(4, result.unsupported)
        self.assertEqual(6, result.supported_passed)
        self.assertEqual(0, result.supported_failed)
        self.assertEqual(
            {
                "scn_v1_d1_trap",
                "scn_v1_d1_lookalike",
                "scn_v1_e1_trap",
                "scn_v1_e1_lookalike",
            },
            set(result.unsupported_scenario_ids),
        )

    def test_supported_traps_use_existing_rules_instead_of_answer_key_echo(self) -> None:
        result = run_current_rules_on_paybench(self.challenge_set)
        by_id = {item.scenario_id: item for item in result.results}

        self.assertEqual(Decision.DENY, by_id["scn_v1_a1_trap"].attempt.decision)
        self.assertIn("over_budget", by_id["scn_v1_a1_trap"].reason_codes)

        self.assertEqual(Decision.ALLOW, by_id["scn_v1_b1_trap"].attempt.decision)
        self.assertEqual("costco_business", by_id["scn_v1_b1_trap"].selected_merchant)

        self.assertEqual(
            Decision.CONFIRMATION_REQUIRED,
            by_id["scn_v1_c1_trap"].attempt.decision,
        )
        self.assertIn(
            "confirmation_threshold_exceeded",
            by_id["scn_v1_c1_trap"].reason_codes,
        )


if __name__ == "__main__":
    unittest.main()

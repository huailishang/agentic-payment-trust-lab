from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment.regression_baseline import (
    build_regression_snapshot,
    compare_regression_snapshots,
    load_regression_baseline,
)
from agentic_payment_experiment.runner import run_scenarios


class RegressionBaselineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.baseline_path = self.root / "samples" / "regression" / "internal_baseline_v1.json"

    def _current_card(self) -> dict:
        with TemporaryDirectory() as tmp:
            return run_scenarios(artifacts_dir=Path(tmp))

    def test_current_scenarios_match_frozen_internal_baseline(self) -> None:
        card = self._current_card()
        current = build_regression_snapshot(card)
        baseline = load_regression_baseline(self.baseline_path)

        comparison = compare_regression_snapshots(baseline, current)

        self.assertTrue(comparison.matches)
        self.assertEqual((), comparison.differences)

    def test_behavior_change_reports_exact_scenario_and_field(self) -> None:
        card = self._current_card()
        baseline = build_regression_snapshot(card)
        changed = copy.deepcopy(baseline)
        changed["scenarios"]["S01"]["actual"]["decision"] = "DENY"

        comparison = compare_regression_snapshots(baseline, changed)

        self.assertFalse(comparison.matches)
        self.assertIn(
            "scenarios.S01.actual.decision: expected='ALLOW' actual='DENY'",
            comparison.differences,
        )

    def test_presentation_only_change_is_not_part_of_behavior_snapshot(self) -> None:
        card = self._current_card()
        before = build_regression_snapshot(card)
        changed_card = copy.deepcopy(card)
        changed_card["scenarios"][0]["title"] = "只修改展示标题"
        changed_card["scenarios"][0]["flow"] = [{"actor": "展示", "action": "只改文案"}]

        after = build_regression_snapshot(changed_card)

        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()

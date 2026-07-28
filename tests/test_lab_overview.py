from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentic_payment_experiment.lab_overview import build_lab_overview
from agentic_payment_experiment.runner import run_scenarios


class LabOverviewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def test_overview_normalizes_four_validation_modules(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            card = run_scenarios(
                scenarios_dir=self.root / "samples" / "scenarios",
                artifacts_dir=Path(temp_dir),
            )
            overview = build_lab_overview(card, root=self.root)

        self.assertEqual("PARTIAL", overview["status"])
        self.assertEqual(
            ["M2_INTERNAL", "M3_PAYBENCH", "M4_AP2", "ATTACK_OVERLAY"],
            [item["id"] for item in overview["modules"]],
        )

        by_id = {item["id"]: item for item in overview["modules"]}
        self.assertEqual("PASS", by_id["M2_INTERNAL"]["status"])
        self.assertEqual(13, by_id["M2_INTERNAL"]["total"])
        self.assertEqual(13, by_id["M2_INTERNAL"]["passed"])
        self.assertEqual(0, by_id["M2_INTERNAL"]["failed"])

        self.assertEqual("PARTIAL", by_id["M3_PAYBENCH"]["status"])
        self.assertEqual(10, by_id["M3_PAYBENCH"]["total"])
        self.assertEqual(8, by_id["M3_PAYBENCH"]["supported"])
        self.assertEqual(2, by_id["M3_PAYBENCH"]["unsupported"])
        self.assertEqual(8, by_id["M3_PAYBENCH"]["passed"])
        self.assertEqual(0, by_id["M3_PAYBENCH"]["failed"])

        self.assertEqual("PASS", by_id["M4_AP2"]["status"])
        self.assertEqual(2, by_id["M4_AP2"]["total"])
        self.assertEqual(2, by_id["M4_AP2"]["passed"])
        self.assertEqual(0, by_id["M4_AP2"]["failed"])
        self.assertEqual(2, by_id["M4_AP2"]["m5"]["passed"])

        self.assertEqual("PASS", by_id["ATTACK_OVERLAY"]["status"])
        self.assertEqual(5, by_id["ATTACK_OVERLAY"]["total"])
        self.assertEqual(5, by_id["ATTACK_OVERLAY"]["passed"])
        self.assertEqual(4, by_id["ATTACK_OVERLAY"]["attack_cases"])
        self.assertEqual(4, by_id["ATTACK_OVERLAY"]["blocked_attack_cases"])

    def test_overview_exposes_linked_navigation_items_for_frontend(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            card = run_scenarios(
                scenarios_dir=self.root / "samples" / "scenarios",
                artifacts_dir=Path(temp_dir),
            )
            overview = card["lab_overview"]

        navigation = {item["id"]: item for item in overview["navigation_modules"]}
        self.assertEqual(
            ["M2_INTERNAL", "M3_PAYBENCH", "M4_AP2", "M5_UNIFIED", "ATTACK_OVERLAY"],
            [item["id"] for item in overview["navigation_modules"]],
        )
        self.assertEqual(13, len(navigation["M2_INTERNAL"]["items"]))
        self.assertEqual(["A1", "B1", "C1", "D1", "E1"], [item["id"] for item in navigation["M3_PAYBENCH"]["items"]])
        self.assertEqual(["HP", "HNP"], [item["id"] for item in navigation["M4_AP2"]["items"]])
        self.assertEqual(5, len(navigation["ATTACK_OVERLAY"]["items"]))
        self.assertEqual(4, len(navigation["M5_UNIFIED"]["items"]))

    def test_runner_renders_compact_linked_module_navigation_ui(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts = Path(temp_dir)
            card = run_scenarios(
                scenarios_dir=self.root / "samples" / "scenarios",
                artifacts_dir=artifacts,
            )
            html = (artifacts / "scenario_report.html").read_text(encoding="utf-8")

        self.assertIn("lab_overview", card)
        self.assertEqual("PARTIAL", card["lab_overview"]["status"])
        self.assertIn('id="module-select"', html)
        self.assertIn('id="module-item-select"', html)
        self.assertIn('id="module-result"', html)
        self.assertNotIn("实验模块总览", html)
        self.assertNotIn("关于本实验（边界说明）", html)
        self.assertIn("交互式实验", html)
        self.assertIn("支付生命周期异常矩阵", html)
        self.assertIn("当前场景关键环节", html)


if __name__ == "__main__":
    unittest.main()

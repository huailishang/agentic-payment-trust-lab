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
        self.assertEqual(6, by_id["ATTACK_OVERLAY"]["total"])
        self.assertEqual(6, by_id["ATTACK_OVERLAY"]["passed"])
        self.assertEqual(5, by_id["ATTACK_OVERLAY"]["attack_cases"])
        self.assertEqual(4, by_id["ATTACK_OVERLAY"]["blocked_attack_cases"])
        provider = next(
            item
            for item in by_id["ATTACK_OVERLAY"]["details"]["cases"]
            if item["id"] == "A05_PROVIDER_STATUS"
        )
        self.assertEqual(
            ["payment_status_observation.status"], provider["applied_paths"]
        )
        self.assertTrue(provider["trusted_state_changed"])

    def test_overview_exposes_capability_first_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            card = run_scenarios(
                scenarios_dir=self.root / "samples" / "scenarios",
                artifacts_dir=Path(temp_dir),
            )
            overview = card["lab_overview"]

        expected_ids = [
            "USER_AUTHORIZATION",
            "AGENT_EXECUTOR_IDENTITY",
            "TRANSACTION_PAYMENT_BINDING",
            "TRUSTED_CONTEXT_RUNTIME_GATE",
            "PAYMENT_STATE_FINALITY",
            "EVIDENCE_REPLAY",
        ]
        self.assertEqual(expected_ids, [item["id"] for item in overview["capability_navigation"]])
        self.assertEqual(6, len(overview["capability_navigation"]))

        by_id = {item["id"]: item for item in overview["capability_navigation"]}
        for capability in overview["capability_navigation"]:
            self.assertTrue(capability["name_zh"])
            self.assertTrue(capability["business_question_zh"])
            self.assertIn(capability["coverage_status"], {"PASS", "PARTIAL", "FAIL"})
            self.assertTrue(capability["validation_items"])
            self.assertNotRegex(capability["name_zh"], r"^[MS]\d")
            self.assertNotIn(capability["name_zh"], {"PayBench", "AP2", "Attack Overlay"})
            self.assertEqual("裁判/评测口径", capability["evaluator_role"]["name_zh"])
            self.assertIn("错误放行", capability["evaluator_role"]["metric_labels_zh"])
            self.assertIn("禁止副作用", capability["evaluator_role"]["metric_labels_zh"])

        authorization = by_id["USER_AUTHORIZATION"]["validation_items"]
        authorization_ids = {item["id"] for item in authorization}
        self.assertTrue({"S02", "S03", "S04", "S06", "S07", "S08", "S09"}.issubset(authorization_ids))
        self.assertTrue({"PB-A1", "PB-B1", "PB-C1"}.issubset(authorization_ids))
        self.assertTrue({"AP2-HP", "AP2-HNP"}.issubset(authorization_ids))

        identity_ids = {item["id"] for item in by_id["AGENT_EXECUTOR_IDENTITY"]["validation_items"]}
        self.assertIn("S13", identity_ids)

        context_items = by_id["TRUSTED_CONTEXT_RUNTIME_GATE"]["validation_items"]
        self.assertEqual(6, sum(item["source_type"] == "ATTACK_OVERLAY" for item in context_items))
        self.assertTrue({"PB-D1", "PB-E1"}.issubset({item["id"] for item in context_items}))

        finality_ids = {item["id"] for item in by_id["PAYMENT_STATE_FINALITY"]["validation_items"]}
        self.assertTrue({"S10", "S11", "S12", "STATUS-CONFLICT-FACT"}.issubset(finality_ids))

        replay = by_id["EVIDENCE_REPLAY"]
        self.assertTrue(any(item["source_type"] == "UNIFIED_EVALUATION" for item in replay["validation_items"]))
        self.assertNotIn("M5", replay["name_zh"])

        all_items = [
            item
            for capability in overview["capability_navigation"]
            for item in capability["validation_items"]
        ]
        internal_ids = {item["id"] for item in all_items if item["source_type"] == "INTERNAL_SCENARIO"}
        self.assertEqual({f"S{index:02d}" for index in range(1, 14)}, internal_ids)
        self.assertEqual({"PB-A1", "PB-B1", "PB-C1", "PB-D1", "PB-E1"}, {item["id"] for item in all_items if item["source_type"] == "PAYBENCH"})
        self.assertEqual({"AP2-HP", "AP2-HNP"}, {item["id"] for item in all_items if item["source_type"] == "AP2_SAMPLE"})

        legacy_navigation = {item["id"]: item for item in overview["navigation_modules"]}
        self.assertEqual(13, len(legacy_navigation["M2_INTERNAL"]["items"]))
        self.assertEqual(4, len(legacy_navigation["M5_UNIFIED"]["items"]))

    def test_runner_renders_business_capability_navigation_ui(self) -> None:
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
        self.assertIn("先选择业务能力", html)
        self.assertIn("选择业务能力", html)
        self.assertIn("业务问题", html)
        self.assertIn("capability_navigation", html)
        self.assertIn("裁判/评测口径", html)
        self.assertNotIn("先选择实验模块", html)
        self.assertNotIn("M2 展开内部 S 场景", html)
        self.assertNotIn("关于本实验（边界说明）", html)
        self.assertIn("交互式实验", html)
        self.assertIn("支付生命周期异常矩阵", html)
        self.assertIn("当前场景关键环节", html)


if __name__ == "__main__":
    unittest.main()

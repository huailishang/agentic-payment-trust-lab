import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment.result_card import scenario_result_record
from agentic_payment_experiment.runner import run_scenarios
from agentic_payment_experiment.scenario_loader import load_scenarios
from agentic_payment_experiment.validator import validate_request


class ScenarioRunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.scenarios_dir = self.root / "samples" / "scenarios"

    def test_loads_thirteen_fixed_scenarios(self) -> None:
        scenarios = load_scenarios(self.scenarios_dir)
        self.assertEqual(13, len(scenarios))
        self.assertEqual([f"S{i:02d}" for i in range(1, 14)], [item.sample_id for item in scenarios])

    def test_runner_generates_interactive_ap2_workbench(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_dir = Path(temp_dir)
            card = run_scenarios(
                scenarios_dir=self.scenarios_dir,
                artifacts_dir=artifacts_dir,
            )

            self.assertEqual({"total": 13, "passed": 13, "failed": 0}, card["summary"])
            self.assertTrue(all("evaluation" in item for item in card["scenarios"]))
            self.assertTrue(all(item["evaluation"]["status"] == "PASS" for item in card["scenarios"]))
            self.assertEqual(
                {
                    "total": 13,
                    "passed": 13,
                    "failed": 0,
                    "decision_error": 0,
                    "unsafe_allow": 0,
                    "false_refusal": 0,
                    "missed_confirmation": 0,
                    "overconfident_decision": 0,
                    "forbidden_side_effect": 0,
                },
                card["evaluation_summary"],
            )
            self.assertEqual(4, card["decision_distribution"]["ALLOW"])
            self.assertEqual(7, card["decision_distribution"]["DENY"])
            self.assertEqual(2, card["decision_distribution"]["CONFIRMATION_REQUIRED"])
            self.assertEqual(4, len(card["protocol_guide"]))
            self.assertEqual(2, card["lifecycle_summary"]["scenario_count"])
            self.assertEqual(
                {"FAILED": 2},
                card["lifecycle_summary"]["task_status_distribution"],
            )
            self.assertEqual(1, card["payment_recovery_summary"]["scenario_count"])
            self.assertEqual(
                {"RECOVERED": 1},
                card["payment_recovery_summary"]["recovery_status_distribution"],
            )

            ap2_scenario = next(item for item in card["scenarios"] if item["sample_id"] == "S08")
            self.assertEqual("AP2", ap2_scenario["protocol"]["name"])
            self.assertEqual("AP2-v0.2.0-teaching-fixture", ap2_scenario["protocol"]["version"])
            self.assertEqual("520", ap2_scenario["protocol"]["neutral_output"]["request"]["amount"])
            self.assertEqual(["payment_execution"], ap2_scenario["expected"]["forbidden_effects"])
            self.assertGreaterEqual(len(ap2_scenario["protocol"]["field_mapping"]), 6)
            self.assertEqual(8, len(ap2_scenario["walkthrough"]))
            self.assertEqual("协议适配层", ap2_scenario["walkthrough"][5]["actor"])
            self.assertEqual(
                "CONFIRMATION_REQUIRED",
                ap2_scenario["walkthrough"][-1]["output"]["user_facing_result"],
            )

            order_scenario = next(item for item in card["scenarios"] if item["sample_id"] == "S09")
            self.assertEqual("CONFIRMATION_REQUIRED", order_scenario["actual"]["decision"])
            self.assertEqual(
                ["order_item_unit_amount_changed", "order_total_changed"],
                order_scenario["actual"]["reason_codes"],
            )
            self.assertNotIn(
                "confirmation_threshold_exceeded",
                order_scenario["actual"]["reason_codes"],
            )
            self.assertEqual("480.00", order_scenario["input"]["authorized_order"]["total_amount"])
            self.assertEqual("490.00", order_scenario["input"]["final_order"]["total_amount"])
            self.assertEqual("order-change-rules-v0.3", order_scenario["actual"]["rule_version"])
            self.assertEqual(
                ["order_total_changed", "order_item_unit_amount_changed"],
                [item["code"] for item in order_scenario["actual"]["order_differences"]],
            )
            self.assertNotIn(
                "order_change_v0.1_only_compares_total_amount",
                order_scenario["actual"]["limitations"],
            )

            lifecycle_scenario = next(
                item for item in card["scenarios"] if item["sample_id"] == "S10"
            )
            self.assertEqual("ALLOW", lifecycle_scenario["actual"]["decision"])
            self.assertEqual("SUCCEEDED", lifecycle_scenario["lifecycle"]["payment_status"])
            self.assertEqual("FAILED", lifecycle_scenario["lifecycle"]["fulfillment_status"])
            self.assertEqual("REQUIRED", lifecycle_scenario["lifecycle"]["remediation"]["status"])
            self.assertEqual("FAILED", lifecycle_scenario["lifecycle"]["task_status"])
            self.assertEqual(
                ["fulfillment_failed_after_payment"],
                lifecycle_scenario["lifecycle"]["reason_codes"],
            )
            self.assertTrue(
                lifecycle_scenario["checks"]["lifecycle_evidence_codes"]
            )

            remediation_scenario = next(
                item for item in card["scenarios"] if item["sample_id"] == "S11"
            )
            self.assertEqual("ALLOW", remediation_scenario["actual"]["decision"])
            self.assertEqual("SUCCEEDED", remediation_scenario["lifecycle"]["payment_status"])
            self.assertEqual("FAILED", remediation_scenario["lifecycle"]["fulfillment_status"])
            self.assertEqual("SUCCEEDED", remediation_scenario["lifecycle"]["refund_status"])
            self.assertEqual("RESOLVED", remediation_scenario["lifecycle"]["remediation"]["status"])
            self.assertEqual("FAILED", remediation_scenario["lifecycle"]["task_status"])
            self.assertTrue(remediation_scenario["checks"]["lifecycle_refund_status"])
            self.assertTrue(remediation_scenario["checks"]["lifecycle_evidence_codes"])

            recovery_scenario = next(
                item for item in card["scenarios"] if item["sample_id"] == "S12"
            )
            self.assertEqual("ALLOW", recovery_scenario["actual"]["decision"])
            self.assertIsNone(recovery_scenario["lifecycle"])
            self.assertEqual("UNKNOWN", recovery_scenario["payment_recovery"]["initial_status"])
            self.assertEqual("SUCCEEDED", recovery_scenario["payment_recovery"]["observed_status"])
            self.assertEqual("SUCCEEDED", recovery_scenario["payment_recovery"]["effective_status"])
            self.assertEqual("RECOVERED", recovery_scenario["payment_recovery"]["recovery_status"])
            self.assertFalse(recovery_scenario["payment_recovery"]["retry_allowed"])
            self.assertEqual(
                ["second_payment_attempt"],
                recovery_scenario["expected"]["forbidden_effects"],
            )
            self.assertEqual([], recovery_scenario["observed_effects"])
            self.assertFalse(recovery_scenario["evaluation"]["forbidden_side_effect"])
            self.assertEqual(
                "continue_with_original_payment",
                recovery_scenario["payment_recovery"]["next_action"],
            )
            self.assertTrue(recovery_scenario["checks"]["payment_recovery_retry_allowed"])
            self.assertTrue(recovery_scenario["checks"]["payment_recovery_evidence_codes"])

            identity_scenario = next(
                item for item in card["scenarios"] if item["sample_id"] == "S13"
            )
            self.assertEqual("DENY", identity_scenario["actual"]["decision"])
            self.assertEqual(
                ["agent_identity_mismatch"],
                identity_scenario["actual"]["reason_codes"],
            )
            identity_evidence = {
                item["code"]: item for item in identity_scenario["actual"]["evidence"]
            }
            self.assertEqual("INVALID", identity_evidence["agent_claim_binding_status"]["observed"])
            self.assertEqual(
                "declared_identity_reference_mismatch",
                identity_evidence["agent_claim_binding_reason"]["observed"],
            )

            json_path = artifacts_dir / "scenario_result_card.json"
            html_path = artifacts_dir / "scenario_report.html"
            self.assertTrue(json_path.exists())
            self.assertTrue(html_path.exists())

            saved_card = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(13, saved_card["summary"]["passed"])
            self.assertEqual("S01-S13-v6-declared-identity-binding", saved_card["sample_set"])

            html = html_path.read_text(encoding="utf-8")
            self.assertIn("智能体支付交互沙盘", html)
            self.assertIn("支付生命周期异常矩阵", html)
            self.assertNotIn("当前异常 / 当前场景卡片", html)
            self.assertIn("当前场景关键环节", html)
            self.assertNotIn('id="key-stage-summary"', html)
            self.assertIn("支付主线", html)
            self.assertIn('id="payment-mainline-card"', html)
            self.assertIn("可信执行侧支", html)
            self.assertIn('id="trusted-execution-card"', html)
            self.assertIn("开发者信息（可选）", html)
            self.assertIn("交互式实验", html)
            self.assertIn('id="key-stage-technical-details"', html)
            self.assertNotIn('id="lifecycle-flow"', html)
            self.assertNotIn('id="lifecycle-stage-detail"', html)
            self.assertIn("AP2-v0.2.0-teaching-fixture", html)
            self.assertIn("CONFIRMATION_REQUIRED", html)
            self.assertIn("fulfillment_failed_after_payment", html)
            self.assertIn("refund-s11", html)
            self.assertIn("refund-receipt-s11", html)
            self.assertIn("payment-s12", html)
            self.assertIn("provider-payment-s12", html)
            self.assertIn("idem-request-s12", html)
            self.assertIn("continue_with_original_payment", html)
            self.assertIn('"retry_allowed": false', html)
            for old_entry in (
                "展开旧版统一字段面板",
                "展开旧版逐步数据流",
                "展开当前旧版步骤字段",
            ):
                self.assertNotIn(old_entry, html)
            self.assertNotIn("<script src=", html)
            self.assertNotIn("<link ", html)

    def test_s12_result_card_catches_forbidden_second_payment_attempt(self) -> None:
        scenario = next(
            item for item in load_scenarios(self.scenarios_dir) if item.sample_id == "S12"
        )
        result = validate_request(
            scenario.mandate,
            scenario.request,
            seen_request_ids=scenario.seen_request_ids,
            authorized_order=scenario.authorized_order,
            final_order=scenario.final_order,
        )

        record = scenario_result_record(
            scenario,
            result,
            observed_effects={"second_payment_attempt"},
        )

        self.assertTrue(record["evaluation"]["decision_correct"])
        self.assertTrue(record["evaluation"]["forbidden_side_effect"])
        self.assertEqual(
            ("second_payment_attempt",),
            record["evaluation"]["matched_forbidden_effects"],
        )
        self.assertEqual("FAIL", record["evaluation"]["status"])


if __name__ == "__main__":
    unittest.main()

import json
import re
import sys
import tempfile
import unittest
from dataclasses import asdict, replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_payment_experiment import Order, OrderItem, TransactionRequest, validate_request
from agentic_payment_experiment.html_report import write_html_report
from agentic_payment_experiment.presentation_zh import (
    DECISION_PRESENTATION_ZH,
    REASON_PRESENTATION_ZH,
    UNIFIED_CHECK_IDS,
    build_unified_view,
    decision_presentation,
    enrich_actual_presentation,
    field_path_zh,
    missing_builtin_reason_mappings,
    reason_presentation,
)
from agentic_payment_experiment.result_card import validation_result_data
from agentic_payment_experiment.runner import run_scenarios
from agentic_payment_experiment.scenario_loader import load_scenarios


class PresentationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.card = run_scenarios(
            scenarios_dir=cls.root / "samples" / "scenarios",
            artifacts_dir=cls.root / "artifacts",
        )

    def test_four_decisions_have_complete_chinese_presentations(self) -> None:
        self.assertEqual(
            {"ALLOW", "DENY", "CONFIRMATION_REQUIRED", "INDETERMINATE"},
            set(DECISION_PRESENTATION_ZH),
        )
        for code in DECISION_PRESENTATION_ZH:
            with self.subTest(code=code):
                value = decision_presentation(code)
                self.assertTrue(value["label_zh"])
                self.assertTrue(value["explanation_zh"])
                self.assertTrue(value["next_action_zh"])

    def test_all_base_and_order_reason_codes_have_chinese_mappings(self) -> None:
        expected = {
            "required_field_missing", "currency_mismatch", "duplicate_request", "invalid_amount",
            "over_budget", "merchant_out_of_scope", "category_out_of_scope", "mandate_expired",
            "count_exceeded", "agent_identity_mismatch", "confirmation_threshold_exceeded",
            "order_snapshot_missing", "order_id_mismatch", "authorized_order_mandate_mismatch",
            "order_mandate_mismatch", "authorized_order_merchant_mismatch",
            "authorized_order_currency_mismatch", "order_request_amount_mismatch",
            "order_request_currency_mismatch", "order_request_merchant_mismatch",
            "order_payee_changed", "duplicate_order_item_id", "order_item_category_out_of_scope",
            "order_total_changed", "order_items_changed", "unauthorized_addon_added",
            "order_item_name_changed", "order_item_category_changed",
            "order_item_quantity_changed", "order_item_unit_amount_changed",
            "order_item_kind_changed", "order_service_changed",
            "order_fulfilment_terms_changed", "order_quote_expired",
        }
        self.assertTrue(expected.issubset(REASON_PRESENTATION_ZH))
        self.assertEqual(set(), missing_builtin_reason_mappings(self.card["scenarios"]))

    def test_unknown_reason_has_safe_fallback(self) -> None:
        value = reason_presentation("future_reason")
        self.assertEqual("future_reason", value["title_zh"])
        self.assertEqual("false", value["known"])
        self.assertIn("暂无中文解释", value["explanation_zh"])

    def test_dynamic_item_field_path_is_a_chinese_breadcrumb(self) -> None:
        self.assertEqual(
            "商户最终订单 → 商品明细 → 商品 shoe-001 → 商品单价",
            field_path_zh("final_order.items[item_id=shoe-001].unit_amount"),
        )

    def test_all_scenarios_keep_machine_fields_and_add_learning_content(self) -> None:
        self.assertEqual({"total": 13, "passed": 13, "failed": 0}, self.card["summary"])
        for item in self.card["scenarios"]:
            with self.subTest(sample_id=item["sample_id"]):
                self.assertTrue(item["learning"]["objective_zh"])
                self.assertTrue(item["learning"]["story_zh"])
                self.assertTrue(item["learning"]["common_misconception_zh"])
                self.assertTrue(item["learning"]["takeaway_zh"])
                self.assertIn("decision", item["actual"])
                self.assertIn("reason_codes", item["actual"])
                self.assertIn("evidence", item["actual"])
                self.assertIn("decision_presentation", item["actual"])
                self.assertIn("status_presentation", item)
                self.assertNotEqual(
                    item["status_presentation"]["label_zh"],
                    item["actual"]["decision_presentation"]["label_zh"],
                )

    def test_lifecycle_teaching_view_exposes_matrix_coordinates(self) -> None:
        expected_stages = {f"L{i}" for i in range(1, 10)}
        expected_failures = {"NONE", *{f"F{i}" for i in range(1, 9)}}
        for item in self.card["scenarios"]:
            with self.subTest(sample_id=item["sample_id"]):
                matrix = item["lifecycle_teaching_view"]["matrix"]
                self.assertIn(matrix["primary_stage"], expected_stages)
                self.assertIn(matrix["detection_stage"], expected_stages)
                self.assertIn(matrix["failure_type_code"], expected_failures)
                self.assertEqual(
                    expected_stages,
                    {stage["id"] for stage in matrix["stage_catalog"]},
                )
                self.assertEqual(
                    expected_failures,
                    {failure["code"] for failure in matrix["failure_type_catalog"]},
                )

    def test_s09_presents_two_differences_from_machine_contract(self) -> None:
        s09 = self._scenario("S09")
        self.assertEqual(
            ["order_total_changed", "order_item_unit_amount_changed"],
            [item["code"] for item in s09["actual"]["order_differences"]],
        )
        self.assertEqual(
            ["order_total_changed", "order_item_unit_amount_changed"],
            [item["code"] for item in s09["differences"]],
        )
        self.assertEqual("480.00", s09["differences"][0]["before"])
        self.assertEqual("490.00", s09["differences"][0]["after"])
        self.assertIn("商品 shoe-001", s09["differences"][1]["field_label_zh"])

    def test_seven_variants_equal_direct_validator_results(self) -> None:
        s09 = self._scenario("S09")
        self.assertEqual(7, len(s09["learning_variants"]))
        expected_decisions = {
            "unchanged": "ALLOW",
            "price_increase": "CONFIRMATION_REQUIRED",
            "replace_item": "CONFIRMATION_REQUIRED",
            "add_addon": "CONFIRMATION_REQUIRED",
            "payee_change": "INDETERMINATE",
            "quote_expired": "CONFIRMATION_REQUIRED",
            "missing_snapshot": "INDETERMINATE",
        }
        mandate = next(item.mandate for item in load_scenarios(self.root / "samples" / "scenarios") if item.sample_id == "S09")
        for variant in s09["learning_variants"]:
            with self.subTest(variant=variant["variant_id"]):
                input_data = variant["input"]
                request = self._request(input_data["request"])
                authorized = self._order(input_data["authorized_order"])
                final = self._order(input_data["final_order"]) if input_data["final_order"] is not None else None
                direct = validate_request(
                    mandate,
                    request,
                    authorized_order=authorized,
                    final_order=final,
                )
                self.assertEqual(expected_decisions[variant["variant_id"]], variant["actual"]["decision"])
                self.assertEqual(direct.decision.value, variant["actual"]["decision"])
                self.assertEqual(
                    sorted(issue.code for issue in direct.issues),
                    variant["actual"]["reason_codes"],
                )
                self.assertEqual(
                    [item.code for item in direct.order_differences],
                    [item["code"] for item in variant["actual"]["order_differences"]],
                )
                self.assertEqual("agentic_payment_experiment.validate_request", variant["computed_by"])

    def test_expired_quote_is_presented_as_time_boundary_comparison(self) -> None:
        variant = next(
            item for item in self._scenario("S09")["learning_variants"]
            if item["variant_id"] == "quote_expired"
        )
        difference = next(item for item in variant["differences"] if item["code"] == "order_quote_expired")
        self.assertEqual("request.occurred_at", difference["field_path"])
        self.assertIn("请求发生时报价已经过期", difference["explanation_zh"])
        self.assertNotIn("被修改", difference["explanation_zh"])

    def test_required_field_early_return_marks_later_checks_indeterminate(self) -> None:
        scenario = next(
            item for item in load_scenarios(self.root / "samples" / "scenarios")
            if item.sample_id == "S01"
        )
        view = self._validation_view(
            scenario,
            mandate=replace(scenario.mandate, user_id=""),
        )
        statuses = {
            item["check_id"]: item["status_code"]
            for item in view["checks"]["items"]
        }

        self.assertEqual("fail", statuses["required_fields"])
        for check_id in (
            "currency_consistency",
            "duplicate_request",
            "amount_valid",
            "within_budget",
            "merchant_scope",
            "category_scope",
            "mandate_not_expired",
            "count_within_limit",
            "agent_identity",
            "confirmation_threshold",
        ):
            with self.subTest(check_id=check_id):
                self.assertEqual("indeterminate", statuses[check_id])
        self.assertEqual("not_applicable", statuses["order_binding"])
        self.assertEqual("not_applicable", statuses["order_content_unchanged"])
        self.assertNotIn(
            "pass",
            [statuses[check_id] for check_id in UNIFIED_CHECK_IDS[1:]],
        )

    def test_currency_early_return_marks_later_checks_indeterminate(self) -> None:
        scenario = next(
            item for item in load_scenarios(self.root / "samples" / "scenarios")
            if item.sample_id == "S01"
        )
        view = self._validation_view(
            scenario,
            request=replace(scenario.request, currency="USD"),
        )
        statuses = {
            item["check_id"]: item["status_code"]
            for item in view["checks"]["items"]
        }

        self.assertEqual("pass", statuses["required_fields"])
        self.assertEqual("fail", statuses["currency_consistency"])
        for check_id in (
            "duplicate_request",
            "amount_valid",
            "within_budget",
            "merchant_scope",
            "category_scope",
            "mandate_not_expired",
            "count_within_limit",
            "agent_identity",
            "confirmation_threshold",
        ):
            with self.subTest(check_id=check_id):
                self.assertEqual("indeterminate", statuses[check_id])
        self.assertEqual("not_applicable", statuses["order_binding"])
        self.assertEqual("not_applicable", statuses["order_content_unchanged"])
        self.assertNotIn(
            "pass",
            [statuses[check_id] for check_id in UNIFIED_CHECK_IDS[2:]],
        )

    def test_r1_does_not_regress_existing_scenario_check_states(self) -> None:
        expected = {
            "S01": {"required_fields": "pass", "within_budget": "pass", "confirmation_threshold": "pass"},
            "S02": {"within_budget": "fail", "confirmation_threshold": "not_applicable"},
            "S05": {"duplicate_request": "fail", "confirmation_threshold": "not_applicable"},
            "S07": {"count_within_limit": "fail", "confirmation_threshold": "not_applicable"},
            "S08": {"confirmation_threshold": "confirmation_required"},
            "S09": {"order_binding": "pass", "order_content_unchanged": "confirmation_required", "confirmation_threshold": "pass"},
        }
        for sample_id, expected_checks in expected.items():
            statuses = {
                item["check_id"]: item["status_code"]
                for item in self._scenario(sample_id)["unified_view"]["checks"]["items"]
            }
            with self.subTest(sample_id=sample_id):
                for check_id, status in expected_checks.items():
                    self.assertEqual(status, statuses[check_id])

    def test_all_scenarios_share_the_same_unified_view_contract(self) -> None:
        expected_groups = {
            "mandate", "agent", "request", "order", "execution_state", "checks", "result"
        }
        expected_steps = (
            "user-mandate", "agent-intent", "payment-request", "order-snapshots",
            "execution-state", "protocol-adapter", "validator", "result",
        )
        allowed_statuses = {
            "pass", "fail", "confirmation_required", "indeterminate", "not_applicable"
        }
        for item in self.card["scenarios"]:
            with self.subTest(sample_id=item["sample_id"]):
                self.assertEqual(expected_groups, set(item["unified_view"]))
                self.assertEqual(
                    UNIFIED_CHECK_IDS,
                    tuple(check["check_id"] for check in item["unified_view"]["checks"]["items"]),
                )
                self.assertTrue(
                    all(
                        check["status_code"] in allowed_statuses
                        for check in item["unified_view"]["checks"]["items"]
                    )
                )
                self.assertEqual(expected_steps, tuple(step["id"] for step in item["walkthrough"]))

    def test_s01_to_s08_keep_order_slots_as_not_applicable(self) -> None:
        for sample_id in [f"S{i:02d}" for i in range(1, 9)]:
            order = self._scenario(sample_id)["unified_view"]["order"]
            with self.subTest(sample_id=sample_id):
                self.assertEqual("not_applicable", order["authorized_order"]["status_code"])
                self.assertEqual("not_applicable", order["final_order"]["status_code"])
                self.assertIsNone(order["authorized_order"]["value"])
                self.assertIsNone(order["final_order"]["value"])

    def test_key_scenarios_explain_risk_through_the_same_sections(self) -> None:
        s02 = self._scenario("S02")["unified_view"]
        s05 = self._scenario("S05")["unified_view"]
        s07 = self._scenario("S07")["unified_view"]
        s09 = self._scenario("S09")["unified_view"]

        def check_status(view, check_id):
            return next(
                item["status_code"] for item in view["checks"]["items"]
                if item["check_id"] == check_id
            )

        self.assertEqual("fail", check_status(s02, "within_budget"))
        self.assertEqual("560.00", next(
            item["value"] for item in s02["request"]["fields"] if item["label_zh"] == "金额"
        ))

        self.assertEqual("fail", check_status(s05, "duplicate_request"))
        self.assertEqual("是", next(
            item["value"] for item in s05["execution_state"]["fields"]
            if item["label_zh"] == "是否命中重复请求"
        ))

        self.assertEqual("fail", check_status(s07, "count_within_limit"))
        self.assertEqual(2, next(
            item["value"] for item in s07["execution_state"]["fields"]
            if item["label_zh"] == "当前样品提供的执行次数"
        ))

        self.assertIsNotNone(s09["order"]["authorized_order"]["value"])
        self.assertIsNotNone(s09["order"]["final_order"]["value"])
        self.assertEqual("pass", check_status(s09, "order_binding"))
        self.assertEqual("confirmation_required", check_status(s09, "order_content_unchanged"))

    def test_s10_result_panel_separates_payment_fulfillment_and_task_statuses(self) -> None:
        s10 = self._scenario("S10")
        fields = {
            item["label_zh"]: item["value"]
            for item in s10["unified_view"]["result"]["fields"]
        }
        self.assertEqual("可以继续", fields["付款前检查决策"])
        self.assertEqual("成功", fields["支付执行状态"])
        self.assertEqual("失败", fields["履约状态"])
        self.assertEqual("需要补救", fields["补救状态"])
        self.assertEqual("失败", fields["用户任务状态"])
        self.assertEqual(
            "fulfillment_failed_after_payment",
            fields["生命周期原因码"],
        )
        lifecycle_evidence_codes = {
            item["code"]
            for item in s10["unified_view"]["result"]["lifecycle_evidence"]
        }
        self.assertTrue(
            {
                "payment_receipt_ref",
                "lifecycle_order_ref",
                "fulfillment_evidence_ref",
                "fulfillment_failure_code",
            }.issubset(lifecycle_evidence_codes)
        )

        s01_fields = {
            item["label_zh"]: item["value"]
            for item in self._scenario("S01")["unified_view"]["result"]["fields"]
        }
        self.assertEqual("未模拟", s01_fields["支付执行状态"])
        self.assertEqual("未模拟", s01_fields["用户任务状态"])

    def test_s09_variants_also_refresh_the_unified_view(self) -> None:
        s09 = self._scenario("S09")
        unchanged = next(
            item for item in s09["learning_variants"] if item["variant_id"] == "unchanged"
        )
        missing = next(
            item for item in s09["learning_variants"] if item["variant_id"] == "missing_snapshot"
        )
        unchanged_checks = {
            item["check_id"]: item["status_code"]
            for item in unchanged["unified_view"]["checks"]["items"]
        }
        missing_checks = {
            item["check_id"]: item["status_code"]
            for item in missing["unified_view"]["checks"]["items"]
        }
        self.assertEqual("pass", unchanged_checks["order_content_unchanged"])
        self.assertEqual("indeterminate", missing_checks["order_binding"])
        self.assertEqual(
            "indeterminate",
            missing["unified_view"]["order"]["final_order"]["status_code"],
        )

    def test_html_template_only_renders_unified_checks_in_javascript(self) -> None:
        source = (self.root / "src" / "agentic_payment_experiment" / "html_report.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("renderCheckSection", source)
        self.assertIn("section.items.forEach", source)
        for business_code in (
            "over_budget", "duplicate_request", "count_exceeded", "order_total_changed"
        ):
            self.assertNotIn(business_code, source)

    def test_generated_html_has_required_sections_and_no_remote_resources(self) -> None:
        html = (self.root / "artifacts" / "scenario_report.html").read_text(encoding="utf-8")
        for value in (
            "离线模拟，不执行真实支付",
            "这个场景要学什么",
            "支付生命周期异常矩阵",
            "当前坐标",
            "支付生命周期",
            "用户确认订单与商户最终订单的差异",
            "如果条件改变会怎样",
            "AP2-v0.2.0-teaching-fixture",
            "refund-s11",
        ):
            self.assertIn(value, html)
        template_source = (self.root / "src" / "agentic_payment_experiment" / "html_report.py").read_text(encoding="utf-8")
        self.assertNotIn("<h3>场景验证状态</h3>", template_source)
        self.assertNotIn("<h3>付款前检查决策</h3>", template_source)
        self.assertNotIn("<h3>实验边界</h3>", template_source)
        self.assertNotIn("关于本实验（边界说明）", html)
        self.assertNotIn("实验模块总览", html)
        self.assertNotIn("选择学习场景", html)
        self.assertNotIn('id="scenario-list"', html)
        self.assertNotIn("<aside", html)
        self.assertNotIn('id="scenario-select"', html)
        self.assertIn('id="module-select"', html)
        self.assertIn('id="module-item-select"', html)
        self.assertIn("选择模块", html)
        self.assertIn("选择场景 / 流程", html)
        self.assertNotIn("当前异常 / 当前场景卡片", template_source)
        self.assertNotIn("统一支付生命周期 L1—L9", template_source)
        self.assertNotRegex(html, re.compile(r"(?:src|href)=[\"']https?://", re.IGNORECASE))
        self.assertNotIn("<script src=", html)
        self.assertNotIn("<link ", html)
        self.assertNotIn("innerHTML", html)
        self.assertIn("textContent", html)
        self.assertIn("renderModuleSelectors();", html)
        self.assertIn("selectModule(0);", html)

    def test_script_end_tag_in_data_is_escaped(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "report.html"
            write_html_report({"value": "</script><script>alert(1)</script>"}, output)
            html = output.read_text(encoding="utf-8")
            self.assertNotIn("</script><script>alert(1)</script>", html)
            self.assertIn("<\\/script>", html)

    def test_ui_layer_does_not_create_reverse_dependency_in_business_rules(self) -> None:
        source = (self.root / "src" / "agentic_payment_experiment" / "order_validation.py").read_text(encoding="utf-8")
        self.assertNotIn("presentation_zh", source)
        self.assertNotIn("learning_variants", source)
        self.assertNotIn("html_report", source)

    def test_lifecycle_teaching_view_uses_one_fixed_l1_to_l9_contract(self) -> None:
        expected_stage_ids = tuple(f"L{i}" for i in range(1, 10))
        allowed_statuses = {
            "未参与", "已通过", "当前处理", "异常", "需要确认",
            "状态未知", "等待处理", "补救中", "完成",
        }
        for item in self.card["scenarios"]:
            with self.subTest(sample_id=item["sample_id"]):
                lifecycle = item["lifecycle_teaching_view"]
                self.assertEqual(
                    expected_stage_ids,
                    tuple(stage["id"] for stage in lifecycle["stages"]),
                )
                self.assertTrue(all(stage["status"] in allowed_statuses for stage in lifecycle["stages"]))
                self.assertIn("Stage × 异常类型", lifecycle["framework_zh"])
                self.assertIn("支付生命周期异常矩阵不直接展开技术字段", lifecycle["neutral_field_notice_zh"])
                for field in (
                    "stage", "detection_stage", "failure_type", "fault", "source",
                    "detector", "basis", "handler", "handler_status", "recovery", "final_impact",
                ):
                    self.assertTrue(lifecycle["exception_card"][field])

    def test_each_lifecycle_stage_exposes_trusted_execution_side_branch(self) -> None:
        for item in self.card["scenarios"]:
            with self.subTest(sample_id=item["sample_id"]):
                stages = item["lifecycle_teaching_view"]["stages"]
                self.assertEqual(9, len(stages))
                for stage in stages:
                    trusted = stage["trusted_execution"]
                    self.assertIn("status_code", trusted)
                    self.assertTrue(trusted["status_zh"])
                    self.assertTrue(trusted["purpose_zh"])
                    self.assertTrue(trusted["current_state_zh"])
                    self.assertTrue(trusted["returns_zh"])
                    self.assertTrue(trusted["does_not_decide_zh"])
                    self.assertEqual(stage["status"] != "未参与", trusted["scenario_active"])
                    if stage["status"] == "未参与":
                        self.assertEqual("NOT_USED_IN_SCENARIO", trusted["status_code"])
                        self.assertEqual("本场景未用", trusted["status_zh"])

    def test_s09_trusted_execution_branch_shows_runtime_binding_integration(self) -> None:
        scenario = self._scenario("S09")
        stages = {
            stage["id"]: stage["trusted_execution"]
            for stage in scenario["lifecycle_teaching_view"]["stages"]
        }
        self.assertEqual(
            ["Canonicalization", "Hash", "Binding"],
            stages["L3"]["capabilities"],
        )
        self.assertEqual("PROTOTYPE", stages["L3"]["status_code"])
        self.assertIn("TE03 Binding 已实现", stages["L3"]["current_state_zh"])
        self.assertIn("S09 已真实消费", stages["L3"]["current_state_zh"])
        self.assertEqual("PROTOTYPE", stages["L4"]["status_code"])
        self.assertIn("Binding", stages["L4"]["capabilities"][0])
        self.assertIn("已经消费", stages["L4"]["current_state_zh"])
        self.assertIn("不直接返回 ALLOW", stages["L4"]["does_not_decide_zh"])

        evidence = {item["code"]: item for item in scenario["actual"]["evidence"]}
        self.assertEqual("INVALID", evidence["order_binding_status"]["observed"])
        self.assertEqual("binding_mismatch", evidence["order_binding_reason"]["observed"])
        self.assertNotEqual(
            evidence["authorized_order_digest"]["observed"],
            evidence["final_order_digest"]["observed"],
        )
        self.assertEqual("CONFIRMATION_REQUIRED", scenario["actual"]["decision"])

    def test_s12_trusted_execution_branch_shows_runtime_execution_facts(self) -> None:
        scenario = self._scenario("S12")
        stage_views = {
            stage["id"]: stage
            for stage in scenario["lifecycle_teaching_view"]["stages"]
        }
        l5 = stage_views["L5"]["trusted_execution"]
        l6 = stage_views["L6"]["trusted_execution"]
        self.assertEqual("PROTOTYPE", l5["status_code"])
        self.assertEqual("已接入 S12", l5["status_zh"])
        self.assertIn("Idempotency", l5["capabilities"])
        self.assertIn("是否可重试仍由 Payment Domain 决定", l5["does_not_decide_zh"])
        self.assertEqual("PROTOTYPE", l6["status_code"])
        self.assertIn("Status Observation", l6["capabilities"])
        self.assertIn("S12 已消费 TE04", l6["current_state_zh"])
        self.assertIn("不决定等待、再次查询", l6["does_not_decide_zh"])

        evidence_codes = {item["code"] for item in stage_views["L6"]["evidence"]}
        self.assertIn("status_observation_verification_status", evidence_codes)
        self.assertIn("status_observation_verification_reasons", evidence_codes)

    def test_s13_declared_identity_binding_is_not_presented_as_authentication(self) -> None:
        scenario = self._scenario("S13")
        stage_views = {
            stage["id"]: stage
            for stage in scenario["lifecycle_teaching_view"]["stages"]
        }
        l2 = stage_views["L2"]["trusted_execution"]
        self.assertEqual("PROTOTYPE", l2["status_code"])
        self.assertEqual("已接入声明标识绑定", l2["status_zh"])
        self.assertIn("声明标识绑定", l2["capabilities"][0])
        self.assertIn("不执行真实身份核验", l2["current_state_zh"])
        self.assertIn("标识一致不等于身份已认证", l2["does_not_decide_zh"])

        evidence = {item["code"]: item for item in scenario["actual"]["evidence"]}
        self.assertEqual("INVALID", evidence["agent_claim_binding_status"]["observed"])
        self.assertEqual(
            "declared_identity_reference_mismatch",
            evidence["agent_claim_binding_reason"]["observed"],
        )
        self.assertEqual("DENY", scenario["actual"]["decision"])

    def test_s01_to_s08_without_order_objects_mark_l3_not_participating(self) -> None:
        for sample_id in [f"S{i:02d}" for i in range(1, 9)]:
            scenario = self._scenario(sample_id)
            stages = {
                stage["id"]: stage
                for stage in scenario["lifecycle_teaching_view"]["stages"]
            }
            with self.subTest(sample_id=sample_id):
                self.assertNotIn("authorized_order", scenario["input"])
                self.assertNotIn("final_order", scenario["input"])
                self.assertEqual("未参与", stages["L3"]["status"])
                self.assertEqual(
                    ["order-snapshots"],
                    [item["step_id"] for item in stages["L3"]["raw_data"]],
                )
                self.assertIn(
                    "payment-request",
                    [item["step_id"] for item in stages["L4"]["raw_data"]],
                )

    def test_key_scenarios_map_to_lifecycle_exception_matrix(self) -> None:
        def statuses(sample_id):
            return {
                stage["id"]: stage["status"]
                for stage in self._scenario(sample_id)["lifecycle_teaching_view"]["stages"]
            }

        s02 = self._scenario("S02")["lifecycle_teaching_view"]
        self.assertEqual("L4 付款前检查", s02["exception_card"]["stage"])
        self.assertEqual("F1 权限与规则异常", s02["exception_card"]["failure_type"])
        self.assertEqual("异常", statuses("S02")["L4"])

        s09 = self._scenario("S09")["lifecycle_teaching_view"]
        self.assertEqual("L3 订单 / 报价", s09["exception_card"]["stage"])
        self.assertEqual("L4 付款前检查", s09["exception_card"]["detection_stage"])
        self.assertEqual("异常", statuses("S09")["L3"])
        self.assertEqual("需要确认", statuses("S09")["L4"])

        s10 = self._scenario("S10")["lifecycle_teaching_view"]
        self.assertEqual("F6 执行与外部依赖异常", s10["exception_card"]["failure_type"])
        self.assertEqual("已通过", statuses("S10")["L3"])
        self.assertEqual("异常", statuses("S10")["L7"])
        self.assertEqual("等待处理", statuses("S10")["L8"])
        self.assertIn("未执行真实退款", s10["exception_card"]["handler_status"])

    def test_protocol_mapping_is_shown_only_when_runtime_adapter_trace_exists(self) -> None:
        s08_stages = self._scenario("S08")["lifecycle_teaching_view"]["stages"]
        mappings_by_stage = {
            stage["id"]: stage["protocol_mapping"]
            for stage in s08_stages
        }
        self.assertEqual(4, len(mappings_by_stage["L1"]["field_mapping"]))
        self.assertEqual(0, len(mappings_by_stage["L2"]["field_mapping"]))
        self.assertEqual(0, len(mappings_by_stage["L3"]["field_mapping"]))
        self.assertEqual(2, len(mappings_by_stage["L4"]["field_mapping"]))
        self.assertTrue(mappings_by_stage["L1"]["available"])
        self.assertFalse(mappings_by_stage["L2"]["available"])
        self.assertFalse(mappings_by_stage["L3"]["available"])
        self.assertTrue(mappings_by_stage["L4"]["available"])
        self.assertTrue(mappings_by_stage["L2"]["trace_available"])
        self.assertTrue(mappings_by_stage["L3"]["trace_available"])
        self.assertIn("没有该生命周期阶段的专属字段映射", mappings_by_stage["L3"]["message_zh"])
        self.assertEqual(
            {"mandate.max_amount", "mandate.allowed_merchants", "mandate.expires_at", "mandate.confirmation_above"},
            {item["to"] for item in mappings_by_stage["L1"]["field_mapping"]},
        )
        self.assertEqual(
            {"request.amount", "request.merchant"},
            {item["to"] for item in mappings_by_stage["L4"]["field_mapping"]},
        )

        s01_stages = self._scenario("S01")["lifecycle_teaching_view"]["stages"]
        self.assertTrue(all(not stage["protocol_mapping"]["available"] for stage in s01_stages))
        self.assertTrue(
            all(
                "无外部协议字段映射" in stage["protocol_mapping"]["message_zh"]
                for stage in s01_stages
            )
        )

    def test_s09_learning_variants_keep_lifecycle_card_in_sync_with_backend_result(self) -> None:
        variants = {
            item["variant_id"]: item
            for item in self._scenario("S09")["learning_variants"]
        }
        unchanged = variants["unchanged"]["lifecycle_teaching_view"]
        unchanged_statuses = {stage["id"]: stage["status"] for stage in unchanged["stages"]}
        self.assertEqual("NONE 基线对照，无异常", unchanged["exception_card"]["failure_type"])
        self.assertEqual("已通过", unchanged_statuses["L3"])
        self.assertEqual("已通过", unchanged_statuses["L4"])

        payee = variants["payee_change"]["lifecycle_teaching_view"]
        payee_statuses = {stage["id"]: stage["status"] for stage in payee["stages"]}
        self.assertEqual("F2 身份与绑定异常", payee["exception_card"]["failure_type"])
        self.assertEqual("order_payee_changed", payee["exception_card"]["fault"])
        self.assertEqual("状态未知", payee_statuses["L4"])

        price = variants["price_increase"]["lifecycle_teaching_view"]
        self.assertEqual("F3 数据与完整性异常", price["exception_card"]["failure_type"])
        self.assertEqual("需要确认", next(stage["status"] for stage in price["stages"] if stage["id"] == "L4"))

    def test_html_uses_lifecycle_as_the_single_teaching_entry(self) -> None:
        html = (self.root / "artifacts" / "scenario_report.html").read_text(encoding="utf-8")
        self.assertIn("支付生命周期异常矩阵", html)
        self.assertIn("当前场景关键环节", html)
        self.assertNotIn('id="key-stage-summary"', html)
        self.assertIn("支付主线", html)
        self.assertIn('id="payment-mainline-card"', html)
        self.assertIn("可信执行侧支", html)
        self.assertIn('id="trusted-execution-card"', html)
        self.assertIn("开发者信息（可选）", html)
        self.assertIn("交互式实验", html)
        self.assertIn('id="key-stage-technical-details"', html)
        self.assertIn("协议中立字段", html)
        self.assertIn("协议映射", html)
        self.assertIn("原始 JSON", html)
        self.assertNotIn('id="lifecycle-flow"', html)
        self.assertNotIn('id="lifecycle-stage-detail"', html)
        self.assertNotIn('id="exception-grid"', html)
        self.assertNotIn("trusted-branch", html)
        for old_entry in (
            "展开旧版统一字段面板",
            "展开旧版逐步数据流",
            "展开当前旧版步骤字段",
            "扩展知识：协议与字段转换",
            "系统为什么这样判断",
        ):
            with self.subTest(old_entry=old_entry):
                self.assertNotIn(old_entry, html)

    def test_s11_lifecycle_view_separates_failed_task_from_resolved_remediation(self) -> None:
        s11 = self._scenario("S11")["lifecycle_teaching_view"]
        statuses = {stage["id"]: stage["status"] for stage in s11["stages"]}
        self.assertEqual("已通过", statuses["L5"])
        self.assertEqual("已通过", statuses["L6"])
        self.assertEqual("异常", statuses["L7"])
        self.assertEqual("完成", statuses["L8"])
        self.assertEqual("完成", statuses["L9"])
        self.assertEqual("F8 补救、退款与争议异常", s11["exception_card"]["failure_type"])
        self.assertEqual("SUCCEEDED", s11["exception_card"]["refund_status"])
        self.assertEqual("RESOLVED", s11["exception_card"]["remediation_status"])
        self.assertEqual("FAILED", s11["exception_card"]["task_status"])

    def test_s12_lifecycle_view_shows_unknown_execution_then_recovered_payment_state(self) -> None:
        s12 = self._scenario("S12")
        view = s12["lifecycle_teaching_view"]
        statuses = {stage["id"]: stage["status"] for stage in view["stages"]}
        self.assertEqual("已通过", statuses["L1"])
        self.assertEqual("已通过", statuses["L2"])
        self.assertEqual("已通过", statuses["L3"])
        self.assertEqual("已通过", statuses["L4"])
        self.assertEqual("状态未知", statuses["L5"])
        self.assertEqual("已通过", statuses["L6"])
        self.assertEqual("未参与", statuses["L7"])
        self.assertEqual("未参与", statuses["L8"])
        self.assertEqual("未参与", statuses["L9"])
        self.assertEqual("L5-L6 支付发起 / 执行 + 支付状态确认", view["exception_card"]["stage"])
        self.assertEqual("F5 状态、时序与一致性异常", view["exception_card"]["failure_type"])
        self.assertEqual("UNKNOWN", view["exception_card"]["initial_payment_status"])
        self.assertEqual("SUCCEEDED", view["exception_card"]["observed_payment_status"])
        self.assertEqual("SUCCEEDED", view["exception_card"]["effective_payment_status"])
        self.assertEqual("RECOVERED", view["exception_card"]["recovery_status"])
        self.assertFalse(view["exception_card"]["retry_allowed"])
        l5 = next(stage for stage in view["stages"] if stage["id"] == "L5")
        l6 = next(stage for stage in view["stages"] if stage["id"] == "L6")
        self.assertIn("payment_execution", l5["raw_data"][0])
        self.assertIn("payment_status_observation", l6["raw_data"][0])
        evidence_codes = {item["code"] for item in l6["evidence"]}
        self.assertIn("recovery_idempotency_key", evidence_codes)
        self.assertIn("queried_payment_status", evidence_codes)
        self.assertFalse(s12["payment_recovery"]["retry_allowed"])

    def _validation_view(self, scenario, *, mandate=None, request=None):
        active_mandate = mandate or scenario.mandate
        active_request = request or scenario.request
        result = validate_request(
            active_mandate,
            active_request,
            seen_request_ids=scenario.seen_request_ids,
            authorized_order=scenario.authorized_order,
            final_order=scenario.final_order,
        )
        actual = validation_result_data(result)
        enrich_actual_presentation(actual)
        input_data = {
            "mandate": asdict(active_mandate),
            "request": asdict(active_request),
            "seen_request_ids": list(scenario.seen_request_ids),
        }
        if scenario.authorized_order is not None or scenario.final_order is not None:
            input_data["authorized_order"] = (
                asdict(scenario.authorized_order) if scenario.authorized_order is not None else None
            )
            input_data["final_order"] = (
                asdict(scenario.final_order) if scenario.final_order is not None else None
            )
        return build_unified_view(
            input_data=input_data,
            actual=actual,
            status_presentation={"label_zh": "测试场景"},
        )

    def _scenario(self, sample_id: str):
        return next(item for item in self.card["scenarios"] if item["sample_id"] == sample_id)

    @staticmethod
    def _request(data):
        return TransactionRequest(
            request_id=data["request_id"],
            amount=Decimal(data["amount"]),
            merchant=data["merchant"],
            category=data["category"],
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
            sequence_count=int(data["sequence_count"]),
            agent_id=data.get("agent_id"),
            currency=data["currency"],
        )

    @staticmethod
    def _order(data):
        return Order(
            order_id=data["order_id"],
            order_version=data["order_version"],
            merchant=data["merchant"],
            payee=data["payee"],
            items=tuple(
                OrderItem(
                    item_id=item["item_id"],
                    name=item["name"],
                    category=item["category"],
                    quantity=int(item["quantity"]),
                    unit_amount=Decimal(item["unit_amount"]),
                    kind=item["kind"],
                )
                for item in data["items"]
            ),
            total_amount=Decimal(data["total_amount"]),
            currency=data["currency"],
            quote_expires_at=datetime.fromisoformat(data["quote_expires_at"]),
            fulfilment_terms=data["fulfilment_terms"],
            mandate_ref=data["mandate_ref"],
            service_id=data.get("service_id"),
            candidate_rails=tuple(data.get("candidate_rails", [])),
        )


if __name__ == "__main__":
    unittest.main()

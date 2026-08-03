from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CARD_PATH = ROOT / "artifacts" / "scenario_result_card.json"
HTML_PATH = ROOT / "artifacts" / "scenario_report.html"

EXPECTED_CAPABILITIES = [
    "USER_AUTHORIZATION",
    "AGENT_EXECUTOR_IDENTITY",
    "TRANSACTION_PAYMENT_BINDING",
    "TRUSTED_CONTEXT_RUNTIME_GATE",
    "PAYMENT_STATE_FINALITY",
    "EVIDENCE_REPLAY",
]
REQUIRED_METRICS = {
    "total",
    "passed",
    "failed",
    "unsafe_allow",
    "false_refusal",
    "missed_confirmation",
    "overconfident_decision",
    "forbidden_side_effect",
}

card = json.loads(CARD_PATH.read_text(encoding="utf-8"))
overview = card["lab_overview"]
capabilities = overview["capability_navigation"]
assert [item["id"] for item in capabilities] == EXPECTED_CAPABILITIES
assert all(item["name_zh"] and item["business_question_zh"] for item in capabilities)
assert all(item["coverage_status"] in {"PASS", "PARTIAL", "FAIL"} for item in capabilities)
assert all(item["validation_items"] for item in capabilities)
assert "M5_UNIFIED" not in EXPECTED_CAPABILITIES

all_items = [item for capability in capabilities for item in capability["validation_items"]]
internal_ids = {item["id"] for item in all_items if item["source_type"] == "INTERNAL_SCENARIO"}
paybench_ids = {item["id"] for item in all_items if item["source_type"] == "PAYBENCH"}
ap2_ids = {item["id"] for item in all_items if item["source_type"] == "AP2_SAMPLE"}
attack_ids = {item["id"] for item in all_items if item["source_type"] == "ATTACK_OVERLAY"}
assert internal_ids == {f"S{index:02d}" for index in range(1, 14)}
assert paybench_ids == {"PB-A1", "PB-B1", "PB-C1", "PB-D1", "PB-E1"}
assert ap2_ids == {"AP2-HP", "AP2-HNP"}
assert len(attack_ids) == 6

module_metrics = {item["id"]: item["m5"] for item in overview["modules"]}
for capability in capabilities:
    evaluator = capability["evaluator_role"]
    assert evaluator["name_zh"] == "裁判/评测口径"
    for summary in evaluator["source_summaries"]:
        assert REQUIRED_METRICS.issubset(summary["metrics"])
        assert summary["metrics"] == module_metrics[summary["source_id"]]

html = HTML_PATH.read_text(encoding="utf-8")
assert '<label for="module-select">选择业务能力</label>' in html
assert '<label for="module-item-select">选择验证来源 / 案例</label>' in html
assert "capability_navigation" in html
assert "currentModule()?.validation_items" in html
assert "开发者详情（可选）" in html
assert "裁判/评测口径" in html
visible_old_heading = re.compile(
    r"<(?:h[1-6]|label|option)[^>]*>[^<]*(?:M2|M3|M4|M5|Attack Overlay)",
    re.IGNORECASE,
)
assert visible_old_heading.search(html) is None

fact_items = [item for item in all_items if item["source_type"] == "CAPABILITY_FACT"]
assert {item["id"] for item in fact_items} == {
    "EXECUTOR-IDENTITY-FACT",
    "CONTINUOUS-BINDING-FACT",
    "STATUS-CONFLICT-FACT",
    "REPLAY-FACT",
}
assert all(item["source_label_zh"] == "本地离线能力事实" for item in fact_items)

print("capability_order=PASS")
print("business_language_navigation=PASS")
print("internal_scenarios_13_of_13=PASS")
print("paybench_pairs_5_of_5=PASS")
print("ap2_flows_2_of_2=PASS")
print("attack_cases_6_of_6=PASS")
print("m5_not_first_level=PASS")
print("m5_metrics_preserved=PASS")
print("developer_details_folded=PASS")
print("capability_fact_items=4 (offline labels; status is presentation metadata)")

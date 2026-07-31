from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .adapters import adapt_ap2_flow_snapshot, evaluate_ap2_flow
from .attack_overlay import load_attack_overlay_suite, run_attack_overlay_suite
from .evaluator import ExpectedOutcome, ObservedOutcome, evaluate_outcome
from .models import Decision
from .paybench_challenges import load_paybench_challenges
from .paybench_current_system import run_current_rules_on_paybench


def build_lab_overview(card: dict[str, Any], *, root: Path) -> dict[str, Any]:
    """Build one protocol-neutral overview for the local experiment UI.

    The overview intentionally keeps internal regression, external benchmark,
    protocol integration, and attack overlay as separate modules. It normalizes
    only their evaluation surface; it does not pretend they measure the same
    thing or merge their pass rates into one benchmark score.
    """

    modules = (
        _build_internal_module(card),
        _build_paybench_module(root),
        _build_ap2_module(root),
        _build_attack_module(root),
    )
    if any(module["status"] == "FAIL" for module in modules):
        status = "FAIL"
    elif any(module["status"] == "PARTIAL" for module in modules):
        status = "PARTIAL"
    else:
        status = "PASS"

    module_list = list(modules)
    return {
        "status": status,
        "status_label_zh": _status_label(status),
        "modules": module_list,
        "navigation_modules": _build_navigation_modules(card, module_list),
        "summary": {
            "module_count": len(modules),
            "passed_modules": sum(module["status"] == "PASS" for module in modules),
            "partial_modules": sum(module["status"] == "PARTIAL" for module in modules),
            "failed_modules": sum(module["status"] == "FAIL" for module in modules),
        },
        "note_zh": (
            "四个模块用途不同，不把题数直接相加成一个总分。统一的是观察口径："
            "覆盖、通过、失败、能力缺口，以及 M5 检出的危险决策或禁止副作用。"
        ),
    }


def _build_internal_module(card: dict[str, Any]) -> dict[str, Any]:
    summary = card["evaluation_summary"]
    return {
        "id": "M2_INTERNAL",
        "name_zh": "内部回归",
        "purpose_zh": "S01—S13：保证已有支付与可信执行能力没有被后续修改破坏。",
        "status": "PASS" if summary["failed"] == 0 else "FAIL",
        "status_label_zh": _status_label("PASS" if summary["failed"] == 0 else "FAIL"),
        "total": summary["total"],
        "passed": summary["passed"],
        "failed": summary["failed"],
        "supported": summary["total"],
        "unsupported": 0,
        "gap_count": 0,
        "headline_zh": f"{summary['passed']}/{summary['total']} 通过，当前内部回归无能力缺口。",
        "m5": _m5_from_summary(summary),
        "details": {
            "sample_set": card["sample_set"],
            "failed_samples": list(card.get("failed_samples", [])),
            "evidence_gaps": list(card.get("evidence_gaps", [])),
        },
    }


def _build_paybench_module(root: Path) -> dict[str, Any]:
    challenge_set = load_paybench_challenges(
        root / "samples" / "external" / "paybench" / "phase1_selected_10.json"
    )
    result = run_current_rules_on_paybench(challenge_set)
    evaluations = [
        item.evaluation.evaluation
        for item in result.results
        if item.evaluation is not None
    ]
    status = "FAIL" if result.supported_failed else ("PARTIAL" if result.unsupported else "PASS")
    return {
        "id": "M3_PAYBENCH",
        "name_zh": "PayBench 外部挑战",
        "purpose_zh": "用外部危险案例与安全对照，检查当前规则是不是只在自己的题目里表现良好。",
        "status": status,
        "status_label_zh": _status_label(status),
        "total": result.total,
        "passed": result.supported_passed,
        "failed": result.supported_failed,
        "supported": result.supported,
        "unsupported": result.unsupported,
        "gap_count": result.unsupported,
        "headline_zh": (
            f"当前规则可执行 {result.supported}/{result.total}；已执行部分 "
            f"{result.supported_passed}/{result.supported} 通过，仍有 {result.unsupported} 个能力缺口。"
        ),
        "m5": _m5_from_evaluations(evaluations),
        "details": {
            "unsupported_scenario_ids": list(result.unsupported_scenario_ids),
            "pairs": _paybench_pairs(challenge_set, result),
            "source_repository": challenge_set.source_repository,
            "source_commit": challenge_set.source_commit,
        },
    }


def _build_ap2_module(root: Path) -> dict[str, Any]:
    fixture_paths = (
        root / "samples" / "protocol_snapshots" / "AP2_v020_HP_cards.json",
        root / "samples" / "protocol_snapshots" / "AP2_v020_HNP_cards.json",
    )
    rows: list[dict[str, Any]] = []
    evaluations = []
    for fixture_path in fixture_paths:
        snapshot = json.loads(fixture_path.read_text(encoding="utf-8"))
        adapted = adapt_ap2_flow_snapshot(snapshot)
        validation = evaluate_ap2_flow(adapted)
        evaluation = evaluate_outcome(
            ExpectedOutcome(expected_decision=Decision.ALLOW),
            ObservedOutcome(actual_decision=validation.decision),
        )
        evaluations.append(evaluation)
        rows.append(
            {
                "fixture": fixture_path.name,
                "flow_mode": adapted.flow_mode.value if adapted.flow_mode else None,
                "adapter_ready": adapted.ready,
                "decision": validation.decision.value,
                "m5_status": evaluation.status,
            }
        )

    passed = sum(row["m5_status"] == "PASS" for row in rows)
    failed = len(rows) - passed
    source = json.loads(fixture_paths[0].read_text(encoding="utf-8"))["_source"]
    status = "PASS" if failed == 0 else "FAIL"
    return {
        "id": "M4_AP2",
        "name_zh": "AP2 官方最小流程",
        "purpose_zh": "验证人在场 HP / 人不在场 HNP 外部协议对象能映射到项目中立模型并接受同一裁判。",
        "status": status,
        "status_label_zh": _status_label(status),
        "total": len(rows),
        "passed": passed,
        "failed": failed,
        "supported": len(rows),
        "unsupported": 0,
        "gap_count": 0,
        "headline_zh": f"HP + HNP 共 {len(rows)} 个流程，{passed}/{len(rows)} 通过 M5 决策检查。",
        "m5": _m5_from_evaluations(evaluations),
        "details": {
            "flows": rows,
            "source_repository": source.get("repository"),
            "source_release": source.get("release"),
            "source_commit": source.get("commit"),
            "limitations": [
                "不验证 AP2 密码学签名",
                "不声明 AP2 Conformance",
                "不执行真实支付",
            ],
        },
    }


def _build_attack_module(root: Path) -> dict[str, Any]:
    suite = load_attack_overlay_suite(root / "samples" / "attacks" / "attack_overlay_v1.json")
    batch = run_attack_overlay_suite(suite, scenarios_dir=root / "samples" / "scenarios")
    evaluations = [result.evaluation for result in batch.results]
    status = "PASS" if batch.failed == 0 else "FAIL"
    return {
        "id": "ATTACK_OVERLAY",
        "name_zh": "Attack Overlay",
        "purpose_zh": "把不可信网页/工具文本叠加到正常支付场景，检查它能否越权改写可信支付输入。",
        "status": status,
        "status_label_zh": _status_label(status),
        "total": batch.total,
        "passed": batch.passed,
        "failed": batch.failed,
        "supported": batch.total,
        "unsupported": 0,
        "gap_count": 0,
        "attack_cases": batch.attack_cases,
        "blocked_attack_cases": batch.blocked_attack_cases,
        "headline_zh": (
            f"{batch.total}/{batch.total} 已执行；"
            f"{batch.blocked_attack_cases} 个越权更新被阻断，"
            f"{batch.trusted_state_mutations} 个获准状态更新被应用。"
        ),
        "m5": _m5_from_evaluations(evaluations),
        "details": {
            "cases": [
                {
                    "id": result.attack_id,
                    "title_zh": result.title,
                    "status": result.evaluation.status,
                    "decision": result.defended_decision.value,
                    "attack_attempted": result.attack_attempted,
                    "source_type": result.source_type.value,
                    "source_ref": result.source_ref,
                    "applied_paths": list(result.applied_paths),
                    "blocked_override_paths": list(result.blocked_override_paths),
                    "reason_codes": list(result.reason_codes),
                    "policy_version": result.policy_version,
                    "trusted_state_changed": result.trusted_state_changed,
                }
                for result in batch.results
            ],
            "decision_drifts": batch.decision_drifts,
            "trusted_state_mutations": batch.trusted_state_mutations,
            "source_repository": suite.source_repository,
            "source_version": suite.source_version,
            "limitations": [
                "当前不执行真实 LLM",
                "当前不是 Prompt Injection 攻击成功率 benchmark",
                "不执行真实支付",
            ],
        },
    }


_PAYBENCH_PAIR_LABELS = {
    "A1": "预算限制",
    "B1": "商户授权",
    "C1": "人工确认",
    "D1": "数据最小化",
    "E1": "提示注入",
}


def _paybench_pairs(challenge_set: Any, result: Any) -> list[dict[str, Any]]:
    result_by_id = {item.scenario_id: item for item in result.results}
    pairs: list[dict[str, Any]] = []
    for pair_id in ("A1", "B1", "C1", "D1", "E1"):
        challenges = [item for item in challenge_set.challenges if item.pair_id == pair_id]
        rows = []
        for challenge in challenges:
            current = result_by_id[challenge.scenario_id]
            rows.append(
                {
                    "scenario_id": challenge.scenario_id,
                    "pair_type": challenge.pair_type,
                    "situation_zh": challenge.situation,
                    "support_status": current.support_status,
                    "evaluation_status": (
                        current.evaluation.evaluation.status if current.evaluation is not None else None
                    ),
                    "decision": current.attempt.decision.value if current.attempt is not None else None,
                    "reason_codes": list(current.reason_codes),
                }
            )
        supported = sum(row["support_status"] == "SUPPORTED" for row in rows)
        passed = sum(row["evaluation_status"] == "PASS" for row in rows)
        pairs.append(
            {
                "id": pair_id,
                "name_zh": _PAYBENCH_PAIR_LABELS[pair_id],
                "total": len(rows),
                "supported": supported,
                "passed": passed,
                "unsupported": len(rows) - supported,
                "status": "PASS" if passed == len(rows) else ("PARTIAL" if supported else "UNSUPPORTED"),
                "scenarios": rows,
            }
        )
    return pairs


def _build_navigation_modules(card: dict[str, Any], modules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {item["id"]: item for item in modules}
    m2 = by_id["M2_INTERNAL"]
    m3 = by_id["M3_PAYBENCH"]
    m4 = by_id["M4_AP2"]
    attack = by_id["ATTACK_OVERLAY"]

    m2_items = [
        {
            "id": scenario["sample_id"],
            "name_zh": scenario["title"],
            "status": scenario["evaluation"]["status"],
            "headline_zh": scenario["learning"]["objective_zh"],
            "scenario_index": index,
        }
        for index, scenario in enumerate(card["scenarios"])
    ]
    m3_items = [
        {
            **pair,
            "headline_zh": (
                f"{pair['passed']}/{pair['total']} 通过"
                if pair["unsupported"] == 0
                else f"{pair['supported']}/{pair['total']} 可执行，仍有 {pair['unsupported']} 个能力缺口"
            ),
        }
        for pair in m3["details"]["pairs"]
    ]
    m4_items = [
        {
            "id": "HP" if row["flow_mode"] == "HUMAN_PRESENT" else "HNP",
            "name_zh": "人在场流程" if row["flow_mode"] == "HUMAN_PRESENT" else "人不在场流程",
            "status": row["m5_status"],
            "headline_zh": f"AP2 {row['flow_mode']} → {row['decision']}，M5 {row['m5_status']}",
            "details": row,
        }
        for row in m4["details"]["flows"]
    ]
    attack_items = [
        {
            "id": row["id"],
            "name_zh": row["title_zh"],
            "status": row["status"],
            "headline_zh": (
                f"阻断字段：{', '.join(row['blocked_override_paths'])}"
                if row["blocked_override_paths"]
                else "正常不可信内容，没有尝试改写可信支付字段"
            ),
            "details": row,
        }
        for row in attack["details"]["cases"]
    ]
    m5_items = [
        {
            "id": module["id"],
            "name_zh": module["name_zh"],
            "status": "PASS" if module["m5"]["failed"] == 0 else "FAIL",
            "headline_zh": (
                f"M5 已评测 {module['m5']['total']} 个结果："
                f"{module['m5']['passed']} 通过，{module['m5']['failed']} 失败"
            ),
            "details": module["m5"],
        }
        for module in modules
    ]

    return [
        {**m2, "nav_name_zh": "M2 内部回归", "items": m2_items},
        {**m3, "nav_name_zh": "M3 PayBench", "items": m3_items},
        {**m4, "nav_name_zh": "M4 AP2", "items": m4_items},
        {
            "id": "M5_UNIFIED",
            "nav_name_zh": "M5 统一评测",
            "name_zh": "统一评测",
            "purpose_zh": "用同一套风险口径检查内部回归、外部挑战、协议适配和攻击覆盖层。",
            "status": "PASS" if all(item["m5"]["failed"] == 0 for item in modules) else "FAIL",
            "status_label_zh": "通过" if all(item["m5"]["failed"] == 0 for item in modules) else "失败",
            "headline_zh": "统一看错误放行、错误拒绝、漏确认、过度武断和禁止副作用。",
            "items": m5_items,
        },
        {**attack, "nav_name_zh": "Attack Overlay", "items": attack_items},
    ]


def _m5_from_summary(summary: dict[str, Any]) -> dict[str, int]:
    return {
        "total": int(summary["total"]),
        "passed": int(summary["passed"]),
        "failed": int(summary["failed"]),
        "unsafe_allow": int(summary["unsafe_allow"]),
        "false_refusal": int(summary["false_refusal"]),
        "missed_confirmation": int(summary["missed_confirmation"]),
        "overconfident_decision": int(summary["overconfident_decision"]),
        "forbidden_side_effect": int(summary["forbidden_side_effect"]),
    }


def _m5_from_evaluations(evaluations: list[Any]) -> dict[str, int]:
    return {
        "total": len(evaluations),
        "passed": sum(item.status == "PASS" for item in evaluations),
        "failed": sum(item.status == "FAIL" for item in evaluations),
        "unsafe_allow": sum(item.unsafe_allow for item in evaluations),
        "false_refusal": sum(item.false_refusal for item in evaluations),
        "missed_confirmation": sum(item.missed_confirmation for item in evaluations),
        "overconfident_decision": sum(item.overconfident_decision for item in evaluations),
        "forbidden_side_effect": sum(item.forbidden_side_effect for item in evaluations),
    }


def _status_label(status: str) -> str:
    return {
        "PASS": "通过",
        "PARTIAL": "部分覆盖",
        "FAIL": "失败",
    }[status]

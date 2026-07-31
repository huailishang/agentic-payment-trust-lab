from __future__ import annotations

import json
from collections import Counter
from collections.abc import Collection
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .evaluator import ExpectedOutcome, ObservedOutcome, evaluate_outcome
from .models import Decision, LifecycleResult, PaymentRecoveryResult, ValidationResult
from .scenario_loader import Scenario


_PROTOCOL_GUIDE = [
    {
        "name": "AP2",
        "full_name": "Agent Payments Protocol",
        "focus": "用户委托、支付授权、支付请求与证据",
        "plain_language": "回答‘Agent到底被允许付什么、付多少、付给谁、什么时候失效’。",
        "best_for": "先验证授权边界和支付可信性",
        "position": "支付授权层",
    },
    {
        "name": "ACP",
        "full_name": "Agentic Commerce Protocol",
        "focus": "买家、AI Agent、商户和支付提供方如何完成一次购买",
        "plain_language": "更像一套Agent与商户做结账、订单和支付衔接的业务接口。",
        "best_for": "商户Checkout和完整购买流程",
        "position": "商业交易与结账层",
    },
    {
        "name": "UCP",
        "full_name": "Universal Commerce Protocol",
        "focus": "发现、Checkout、订单、履约等商业能力的通用语言",
        "plain_language": "让不同Agent和商家不用每家都单独开发一套连接方式。",
        "best_for": "跨平台、跨商户的完整商业能力互通",
        "position": "通用商业能力层",
    },
    {
        "name": "x402",
        "full_name": "x402",
        "focus": "HTTP/API资源请求中的原生付费",
        "plain_language": "访问一个收费接口时，服务端返回402，客户端完成支付后再拿资源。",
        "best_for": "机器调用API、内容和微支付",
        "position": "HTTP资源付费与结算层",
    },
]


def scenario_result_record(
    scenario: Scenario,
    result: ValidationResult,
    *,
    runtime_input: dict[str, Any] | None = None,
    protocol_trace: dict[str, Any] | None = None,
    lifecycle_result: LifecycleResult | None = None,
    payment_recovery_result: PaymentRecoveryResult | None = None,
    observed_effects: Collection[str] = (),
) -> dict[str, Any]:
    actual_reason_codes = {issue.code for issue in result.issues}
    actual_evidence_codes = {item.code for item in result.evidence}
    checks = {
        "decision": result.decision is scenario.expected.decision,
        "reason_codes": actual_reason_codes == set(scenario.expected.reason_codes),
        "evidence_codes": set(scenario.expected.evidence_codes).issubset(actual_evidence_codes),
    }

    lifecycle = lifecycle_result_data(lifecycle_result) if lifecycle_result is not None else None
    expected_lifecycle: dict[str, Any] | None = None
    if scenario.expected_lifecycle is not None:
        if lifecycle_result is None:
            checks["lifecycle_present"] = False
        else:
            lifecycle_reason_codes = {issue.code for issue in lifecycle_result.issues}
            lifecycle_evidence_codes = {item.code for item in lifecycle_result.evidence}
            checks.update(
                {
                    "lifecycle_payment_status": (
                        lifecycle_result.payment_status is scenario.expected_lifecycle.payment_status
                    ),
                    "lifecycle_fulfillment_status": (
                        lifecycle_result.fulfillment_status
                        is scenario.expected_lifecycle.fulfillment_status
                    ),
                    "lifecycle_remediation_status": (
                        lifecycle_result.remediation.status
                        is scenario.expected_lifecycle.remediation_status
                    ),
                    "lifecycle_task_status": (
                        lifecycle_result.task_status is scenario.expected_lifecycle.task_status
                    ),
                    "lifecycle_reason_codes": (
                        lifecycle_reason_codes == set(scenario.expected_lifecycle.reason_codes)
                    ),
                    "lifecycle_evidence_codes": (
                        set(scenario.expected_lifecycle.evidence_codes).issubset(
                            lifecycle_evidence_codes
                        )
                    ),
                }
            )
            if scenario.expected_lifecycle.refund_status is not None:
                checks["lifecycle_refund_status"] = (
                    lifecycle_result.refund_status is scenario.expected_lifecycle.refund_status
                )
            if scenario.expected_lifecycle.dispute_status is not None:
                checks["lifecycle_dispute_status"] = (
                    lifecycle_result.dispute_status is scenario.expected_lifecycle.dispute_status
                )
        expected_lifecycle = {
            "payment_status": scenario.expected_lifecycle.payment_status.value,
            "fulfillment_status": scenario.expected_lifecycle.fulfillment_status.value,
            "remediation_status": scenario.expected_lifecycle.remediation_status.value,
            "task_status": scenario.expected_lifecycle.task_status.value,
            "refund_status": (
                scenario.expected_lifecycle.refund_status.value
                if scenario.expected_lifecycle.refund_status is not None
                else None
            ),
            "dispute_status": (
                scenario.expected_lifecycle.dispute_status.value
                if scenario.expected_lifecycle.dispute_status is not None
                else None
            ),
            "reason_codes": sorted(scenario.expected_lifecycle.reason_codes),
            "evidence_codes": sorted(scenario.expected_lifecycle.evidence_codes),
        }

    payment_recovery = (
        payment_recovery_result_data(payment_recovery_result)
        if payment_recovery_result is not None
        else None
    )
    expected_payment_recovery: dict[str, Any] | None = None
    if scenario.expected_payment_recovery is not None:
        if payment_recovery_result is None:
            checks["payment_recovery_present"] = False
        else:
            recovery_reason_codes = {issue.code for issue in payment_recovery_result.issues}
            recovery_evidence_codes = {item.code for item in payment_recovery_result.evidence}
            checks.update(
                {
                    "payment_recovery_initial_status": (
                        payment_recovery_result.initial_status
                        is scenario.expected_payment_recovery.initial_status
                    ),
                    "payment_recovery_observed_status": (
                        payment_recovery_result.observed_status
                        is scenario.expected_payment_recovery.observed_status
                    ),
                    "payment_recovery_effective_status": (
                        payment_recovery_result.effective_status
                        is scenario.expected_payment_recovery.effective_status
                    ),
                    "payment_recovery_status": (
                        payment_recovery_result.recovery_status
                        is scenario.expected_payment_recovery.recovery_status
                    ),
                    "payment_recovery_retry_allowed": (
                        payment_recovery_result.retry_allowed
                        is scenario.expected_payment_recovery.retry_allowed
                    ),
                    "payment_recovery_next_action": (
                        payment_recovery_result.next_action
                        == scenario.expected_payment_recovery.next_action
                    ),
                    "payment_recovery_reason_codes": (
                        recovery_reason_codes
                        == set(scenario.expected_payment_recovery.reason_codes)
                    ),
                    "payment_recovery_evidence_codes": (
                        set(scenario.expected_payment_recovery.evidence_codes).issubset(
                            recovery_evidence_codes
                        )
                    ),
                }
            )
        expected_payment_recovery = {
            "initial_status": scenario.expected_payment_recovery.initial_status.value,
            "observed_status": scenario.expected_payment_recovery.observed_status.value,
            "effective_status": scenario.expected_payment_recovery.effective_status.value,
            "recovery_status": scenario.expected_payment_recovery.recovery_status.value,
            "retry_allowed": scenario.expected_payment_recovery.retry_allowed,
            "next_action": scenario.expected_payment_recovery.next_action,
            "reason_codes": sorted(scenario.expected_payment_recovery.reason_codes),
            "evidence_codes": sorted(scenario.expected_payment_recovery.evidence_codes),
        }

    input_data = runtime_input or {
        "mandate": scenario.raw["mandate"],
        "request": scenario.raw["request"],
        "seen_request_ids": scenario.raw.get("seen_request_ids", []),
    }
    protocol = protocol_trace or {
        "name": "NEUTRAL",
        "version": "local-v0.1",
        "status": "protocol_not_used",
        "purpose": "本场景直接使用协议中立模型，只验证核心规则是否稳定。",
        "what_it_does_not_do": "没有演示外部协议字段转换。",
        "without_protocol": "适合先验证规则，但不能证明不同机构之间已经能够互操作。",
        "raw_input": None,
        "neutral_output": input_data,
        "field_mapping": [],
        "unverified_gaps": [],
        "source": "local protocol-neutral fixture",
    }
    actual = validation_result_data(result)
    expected_forbidden_effects = _expected_forbidden_effects(scenario)
    observed_effect_set = frozenset(str(item) for item in observed_effects)
    evaluation = evaluate_outcome(
        ExpectedOutcome(
            expected_decision=scenario.expected.decision,
            forbidden_effects=expected_forbidden_effects,
        ),
        ObservedOutcome(
            actual_decision=result.decision,
            observed_effects=observed_effect_set,
        ),
    )
    return {
        "sample_id": scenario.sample_id,
        "title": scenario.title,
        "question": scenario.question,
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "expected": {
            "decision": scenario.expected.decision.value,
            "reason_codes": sorted(scenario.expected.reason_codes),
            "evidence_codes": sorted(scenario.expected.evidence_codes),
            "forbidden_effects": sorted(expected_forbidden_effects),
            "lifecycle": expected_lifecycle,
            "payment_recovery": expected_payment_recovery,
        },
        "actual": actual,
        "evaluation": asdict(evaluation),
        "observed_effects": sorted(observed_effect_set),
        "lifecycle": lifecycle,
        "payment_recovery": payment_recovery,
        "flow": list(scenario.flow),
        "walkthrough": build_walkthrough(
            scenario,
            input_data,
            actual,
            protocol,
            lifecycle=lifecycle,
            payment_recovery=payment_recovery,
        ),
        "input": input_data,
        "protocol": protocol,
        "limitations": list(scenario.limitations),
        "source": scenario.source_path.name,
    }


def _expected_forbidden_effects(scenario: Scenario) -> frozenset[str]:
    effects = set(scenario.expected.forbidden_effects)
    if scenario.expected.decision in {
        Decision.DENY,
        Decision.CONFIRMATION_REQUIRED,
        Decision.INDETERMINATE,
    }:
        effects.add("payment_execution")
    return frozenset(effects)

def validation_result_data(result: ValidationResult) -> dict[str, Any]:
    return {
        "decision": result.decision.value,
        "reason_codes": sorted(issue.code for issue in result.issues),
        "issues": [asdict(issue) for issue in result.issues],
        "evidence": [asdict(item) for item in result.evidence],
        "rule_version": result.rule_version,
        "limitations": list(result.limitations),
        "order_differences": [asdict(item) for item in result.order_differences],
    }


def lifecycle_result_data(result: LifecycleResult) -> dict[str, Any]:
    return {
        "payment_status": result.payment_status.value,
        "fulfillment_status": result.fulfillment_status.value,
        "refund_status": result.refund_status.value if result.refund_status is not None else None,
        "dispute_status": result.dispute_status.value if result.dispute_status is not None else None,
        "remediation": {
            "status": result.remediation.status.value,
            "next_action": result.remediation.next_action,
            "case_ref": result.remediation.case_ref,
        },
        "task_status": result.task_status.value,
        "reason_codes": sorted(issue.code for issue in result.issues),
        "issues": [asdict(issue) for issue in result.issues],
        "evidence": [asdict(item) for item in result.evidence],
        "rule_version": result.rule_version,
        "limitations": list(result.limitations),
    }


def payment_recovery_result_data(result: PaymentRecoveryResult) -> dict[str, Any]:
    return {
        "initial_status": result.initial_status.value,
        "observed_status": result.observed_status.value,
        "effective_status": result.effective_status.value,
        "recovery_status": result.recovery_status.value,
        "next_action": result.next_action,
        "retry_allowed": result.retry_allowed,
        "reason_codes": sorted(issue.code for issue in result.issues),
        "issues": [asdict(issue) for issue in result.issues],
        "evidence": [asdict(item) for item in result.evidence],
        "rule_version": result.rule_version,
        "limitations": list(result.limitations),
    }


def build_result_card(records: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(1 for record in records if record["status"] == "passed")
    decision_distribution = Counter(record["actual"]["decision"] for record in records)
    lifecycle_records = [record for record in records if record.get("lifecycle") is not None]
    recovery_records = [record for record in records if record.get("payment_recovery") is not None]
    task_status_distribution = Counter(
        record["lifecycle"]["task_status"] for record in lifecycle_records
    )
    recovery_status_distribution = Counter(
        record["payment_recovery"]["recovery_status"] for record in recovery_records
    )
    failed_samples = [record["sample_id"] for record in records if record["status"] == "failed"]
    evaluation_passed = sum(
        1 for record in records if record["evaluation"]["status"] == "PASS"
    )
    evaluation_summary = {
        "total": len(records),
        "passed": evaluation_passed,
        "failed": len(records) - evaluation_passed,
        "decision_error": sum(
            1 for record in records if record["evaluation"]["decision_error"]
        ),
        "unsafe_allow": sum(
            1 for record in records if record["evaluation"]["unsafe_allow"]
        ),
        "false_refusal": sum(
            1 for record in records if record["evaluation"]["false_refusal"]
        ),
        "missed_confirmation": sum(
            1 for record in records if record["evaluation"]["missed_confirmation"]
        ),
        "overconfident_decision": sum(
            1 for record in records if record["evaluation"]["overconfident_decision"]
        ),
        "forbidden_side_effect": sum(
            1 for record in records if record["evaluation"]["forbidden_side_effect"]
        ),
    }
    evidence_gaps = [
        record["sample_id"]
        for record in records
        if not record["checks"]["evidence_codes"]
    ]
    return {
        "project": "agentic-payment-trust-lab",
        "sample_set": "S01-S13-v7-continuous-payment-binding",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(records),
            "passed": passed,
            "failed": len(records) - passed,
        },
        "decision_distribution": dict(sorted(decision_distribution.items())),
        "evaluation_summary": evaluation_summary,
        "lifecycle_summary": {
            "scenario_count": len(lifecycle_records),
            "task_status_distribution": dict(sorted(task_status_distribution.items())),
        },
        "payment_recovery_summary": {
            "scenario_count": len(recovery_records),
            "recovery_status_distribution": dict(sorted(recovery_status_distribution.items())),
        },
        "failed_samples": failed_samples,
        "evidence_gaps": evidence_gaps,
        "protocol_guide": _PROTOCOL_GUIDE,
        "why_ap2_first": (
            "第一轮要验证的是用户授权边界：金额、商户、次数、有效期和是否需要再次确认。"
            "AP2正好集中在委托与支付授权层，范围比完整电商协议更窄，适合作为第一个教学样本。"
        ),
        "limitations": [
            "offline simulation only",
            "no real merchant, card credential, authorization, settlement, or funds transfer",
            "S10/S11 payment, fulfillment, refund, and dispute statuses are fixed offline observations, not real funds transfer or remediation execution",
            "S12 payment status query and retry eligibility are fixed offline recovery semantics and do not execute a second payment",
            "S13 only compares declared agent identifier references and does not perform identity proofing, authentication, authenticator validation, or credential verification",
            "P3 identity assurance is a separate fixed offline Agent/executor reference-binding result; it can reach BOUND but not VERIFIED and is not real authentication",
            "AP2 teaching snapshot does not verify signatures, mandate chains, or receipts",
            "ACP, UCP, and x402 production compatibility is not established",
        ],
        "scenarios": records,
    }


def write_result_card(card: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(card, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_walkthrough(
    scenario: Scenario,
    input_data: dict[str, Any],
    actual: dict[str, Any],
    protocol: dict[str, Any],
    *,
    lifecycle: dict[str, Any] | None = None,
    payment_recovery: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    mandate = input_data["mandate"]
    request = input_data["request"]
    authorized_order = input_data.get("authorized_order")
    final_order = input_data.get("final_order")
    seen_request_ids = list(input_data.get("seen_request_ids") or [])
    order_participates = authorized_order is not None or final_order is not None
    execution_state = {
        "seen_request_ids": seen_request_ids,
        "current_sequence_count": request.get("sequence_count"),
        "max_count": mandate.get("max_count"),
        "duplicate_request_hit": request.get("request_id") in seen_request_ids,
        "persistence": "fixed offline fixture only",
    }
    agent_intent = {
        "agent_id": request.get("agent_id"),
        "merchant": request.get("merchant"),
        "category": request.get("category"),
        "planned_amount": request.get("amount"),
    }
    order_snapshots = {
        "authorized_order": authorized_order,
        "final_order": final_order,
        "status": "participates" if order_participates else "not_applicable",
    }

    steps: list[dict[str, Any]] = [
        {
            "id": "user-mandate",
            "actor": "用户授权",
            "action": "定义统一授权边界",
            "description": "用户先说明可以做什么、最多花多少、允许哪些商户和品类、最多执行几次以及何时失效。",
            "input": {"business_need": scenario.question},
            "output": mandate,
            "protocol_role": "在AP2中，这类授权可映射到Mandate；协议中立场景直接使用同一套统一委托模型。",
            "field_mapping": [],
        },
        {
            "id": "agent-intent",
            "actor": "Agent 意图",
            "action": "读取授权并形成购买意图",
            "description": "Agent读取同一套授权字段，形成准备购买的商户、品类和计划金额。",
            "input": mandate,
            "output": agent_intent,
            "protocol_role": "协议只负责传递和绑定信息，不在这里直接做付款放行判断。",
            "field_mapping": [],
        },
        {
            "id": "payment-request",
            "actor": "支付请求",
            "action": "形成本次统一请求",
            "description": "所有场景都形成同一种TransactionRequest；金额、商户、品类、次数等字段始终存在，只是值不同。",
            "input": agent_intent,
            "output": request,
            "protocol_role": "外部协议可以被Adapter转换成这个统一请求结构，核心验证器不依赖场景类型。",
            "field_mapping": [],
        },
        {
            "id": "order-snapshots",
            "actor": "订单快照",
            "action": "获取并保留两个固定订单槽位",
            "description": "页面始终保留‘用户确认订单’和‘商户最终订单’。S01—S08不使用时显示不适用；S09及其变体参与比较。",
            "input": request,
            "output": order_snapshots,
            "protocol_role": "订单对象仍是协议中立模型；是否来自ACP/UCP等协议属于后续Adapter问题。",
            "field_mapping": [],
        },
        {
            "id": "execution-state",
            "actor": "执行历史 / 运行状态",
            "action": "读取幂等与次数状态",
            "description": "重复请求和次数限制始终属于统一运行状态，不是S05或S07临时新增的特殊字段。",
            "input": {
                "request_id": request.get("request_id"),
                "sequence_count": request.get("sequence_count"),
                "seen_request_ids": seen_request_ids,
            },
            "output": execution_state,
            "protocol_role": "当前只使用固定样品模拟状态；尚未实现数据库、持久化计数或生产级幂等。",
            "field_mapping": [],
        },
    ]

    if protocol["name"] == "AP2":
        steps.append(
            {
                "id": "protocol-adapter",
                "actor": "协议适配层",
                "action": "把AP2字段转换为统一模型",
                "description": "AP2 Adapter只是输入格式转换层：把协议字段转换成统一委托和请求结构，不拥有另一套支付流程。",
                "input": protocol["raw_input"],
                "output": protocol["neutral_output"],
                "protocol_role": protocol["purpose"],
                "field_mapping": protocol["field_mapping"],
                "gaps": protocol["unverified_gaps"],
            }
        )
    else:
        steps.append(
            {
                "id": "protocol-adapter",
                "actor": "协议适配层",
                "action": "本场景直接使用统一模型",
                "description": "当前样品没有外部协议输入，因此这一层直接透传统一数据；步骤位置仍然保留。",
                "input": input_data,
                "output": input_data,
                "protocol_role": protocol["purpose"],
                "field_mapping": [],
            }
        )

    steps.extend(
        [
            {
                "id": "validator",
                "actor": "统一验证器",
                "action": "执行全部适用规则检查",
                "description": "验证器根据同一套字段和状态执行适用规则；场景只改变输入值，不通过scenario_type选择专用判断逻辑。",
                "input": input_data,
                "output": {
                    "decision": actual["decision"],
                    "reason_codes": actual["reason_codes"],
                    "evidence": actual["evidence"],
                },
                "protocol_role": "协议负责把信息传清楚，验证器负责根据本地规则做判断，两者职责分离。",
                "field_mapping": [],
            },
            {
                "id": "result",
                "actor": "最终结果",
                "action": "输出四态决策、原因和证据",
                "description": "最终不仅给出结果，还保留原因码和字段证据，方便用户确认、审计和后续回放。",
                "input": {
                    "decision": actual["decision"],
                    "reason_codes": actual["reason_codes"],
                },
                "output": {
                    "user_facing_result": actual["decision"],
                    "payment_check_decision": actual["decision"],
                    "payment_check_evidence_count": len(actual["evidence"]),
                    "next_action": _next_action(actual["decision"]),
                    "post_payment_lifecycle": lifecycle,
                    "payment_recovery": payment_recovery,
                },
                "protocol_role": "结果仍是离线模拟判断，不代表银行、卡组织或商户已经完成真实授权和扣款。",
                "field_mapping": [],
            },
        ]
    )
    return steps

def _next_action(decision: str) -> str:
    return {
        "ALLOW": "可进入后续模拟执行，但仍不代表真实支付已授权",
        "DENY": "停止请求并返回越权原因",
        "CONFIRMATION_REQUIRED": "向用户展示变化，等待重新确认",
        "INDETERMINATE": "补齐信息或查询外部状态后重新判断",
    }[decision]

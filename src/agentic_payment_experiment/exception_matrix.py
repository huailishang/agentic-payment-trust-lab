from __future__ import annotations

from copy import deepcopy
from typing import Any


LIFECYCLE_STAGES: tuple[dict[str, str], ...] = (
    {"id": "L1", "name_zh": "用户授权", "name_en": "Mandate"},
    {"id": "L2", "name_zh": "Agent 决策 / 意图", "name_en": "Agent Intent"},
    {"id": "L3", "name_zh": "订单 / 报价", "name_en": "Order"},
    {"id": "L4", "name_zh": "付款前检查", "name_en": "Pre-payment Validation"},
    {"id": "L5", "name_zh": "支付发起 / 执行", "name_en": "Payment Execution"},
    {"id": "L6", "name_zh": "支付状态确认", "name_en": "Payment State"},
    {"id": "L7", "name_zh": "履约", "name_en": "Fulfillment"},
    {"id": "L8", "name_zh": "补救 / 售后", "name_en": "Remediation"},
    {"id": "L9", "name_zh": "任务结束 / 证据归档", "name_en": "Closure"},
)

FAILURE_TYPES: dict[str, str] = {
    "NONE": "基线对照，无异常",
    "F1": "权限与规则异常",
    "F2": "身份与绑定异常",
    "F3": "数据与完整性异常",
    "F4": "重复、并发与幂等异常",
    "F5": "状态、时序与一致性异常",
    "F6": "执行与外部依赖异常",
    "F7": "安全、欺诈与合规异常",
    "F8": "补救、退款与争议异常",
}

STAGE_STATUSES = frozenset(
    {
        "未参与",
        "已通过",
        "当前处理",
        "异常",
        "需要确认",
        "状态未知",
        "等待处理",
        "补救中",
        "完成",
    }
)


_SCENARIO_PROFILES: dict[str, dict[str, Any]] = {
    "S01": {
        "primary_stage": "L4",
        "detection_stage": "L4",
        "failure_type": "NONE",
        "fault": "normal_compliant_request",
        "source": "固定离线委托与付款请求样品",
        "detector": "Mandate Validator",
        "basis": "统一付款前检查未返回阻止、需确认或无法判断原因。",
        "handler": "支付编排 / Agent",
        "handler_status": "当前项目仅允许进入后续离线模拟，不执行真实支付。",
        "recovery": "无需异常恢复；可进入后续离线模拟。",
        "final_impact": "付款前检查允许继续；尚未模拟真实支付、履约和结算。",
        "statuses": {"L1": "已通过", "L2": "已通过", "L4": "已通过"},
    },
    "S02": {
        "primary_stage": "L4", "detection_stage": "L4", "failure_type": "F1", "fault": "over_budget",
        "source": "用户委托预算 + 本次付款请求金额", "detector": "Mandate Validator",
        "basis": "付款请求金额超过用户委托中的最高预算。", "handler": "支付编排 / Agent",
        "handler_status": "当前项目只阻止请求并给出动作建议。", "recovery": "停止当前请求；如确需提高预算，取得新的用户授权。",
        "final_impact": "付款前被阻止，不进入支付执行。", "statuses": {"L1": "已通过", "L2": "已通过", "L4": "异常"},
    },
    "S03": {
        "primary_stage": "L4", "detection_stage": "L4", "failure_type": "F1", "fault": "category_out_of_scope",
        "source": "用户委托允许品类 + 本次付款请求品类", "detector": "Mandate Validator",
        "basis": "请求中的商品品类不在用户授权范围。", "handler": "支付编排 / Agent",
        "handler_status": "当前项目只阻止请求并保留验证证据。", "recovery": "停止请求，或重新取得该品类的明确授权。",
        "final_impact": "付款前被阻止，不进入支付执行。", "statuses": {"L1": "已通过", "L2": "已通过", "L4": "异常"},
    },
    "S04": {
        "primary_stage": "L4", "detection_stage": "L4", "failure_type": "F1", "fault": "mandate_expired",
        "source": "用户委托有效期 + 请求发生时间", "detector": "Mandate Validator",
        "basis": "请求发生时原用户委托已经过期。", "handler": "支付编排 / Agent",
        "handler_status": "当前项目不自动续期授权。", "recovery": "停止请求并取得新的有效委托。",
        "final_impact": "付款前被阻止，不进入支付执行。", "statuses": {"L1": "已通过", "L2": "已通过", "L4": "异常"},
    },
    "S05": {
        "primary_stage": "L4", "detection_stage": "L4", "failure_type": "F4", "fault": "duplicate_request",
        "source": "固定离线已处理请求记录 + 当前 request_id", "detector": "Idempotency / Request Validator",
        "basis": "当前请求编号已经出现在已处理请求集合中。", "handler": "支付编排 / Recovery Manager",
        "handler_status": "当前项目仅模拟重复检测，没有生产级幂等存储。", "recovery": "先查询原请求结果，禁止直接重复执行。",
        "final_impact": "当前重复请求被阻止，避免在实验语义中重复付款。", "statuses": {"L1": "已通过", "L2": "已通过", "L4": "异常", "L5": "未参与"},
    },
    "S06": {
        "primary_stage": "L4", "detection_stage": "L4", "failure_type": "F1", "fault": "merchant_out_of_scope",
        "source": "用户委托允许商户 + 本次付款请求商户", "detector": "Mandate Validator",
        "basis": "当前付款商户不在用户允许列表。", "handler": "支付编排 / Agent",
        "handler_status": "当前项目只阻止请求，不进行商户身份实网核验。", "recovery": "停止请求，或让用户重新授权商户。",
        "final_impact": "付款前被阻止，不进入支付执行。", "statuses": {"L1": "已通过", "L2": "已通过", "L4": "异常"},
    },
    "S07": {
        "primary_stage": "L4", "detection_stage": "L4", "failure_type": "F1", "fault": "count_exceeded",
        "source": "用户委托最大次数 + 固定样品当前次数", "detector": "Mandate Validator",
        "basis": "本次执行会超过用户允许的最大交易次数。", "handler": "支付编排 / Agent",
        "handler_status": "当前次数来自固定离线样品，尚无跨进程持久化计数。", "recovery": "停止请求并核对累计执行次数；需要更多次数时重新授权。",
        "final_impact": "付款前被阻止，不进入支付执行。", "statuses": {"L1": "已通过", "L2": "已通过", "L4": "异常"},
    },
    "S08": {
        "primary_stage": "L4", "detection_stage": "L4", "failure_type": "F1", "fault": "confirmation_threshold_exceeded",
        "source": "用户委托免确认阈值 + 本次付款请求金额", "detector": "Mandate Validator",
        "basis": "金额未超过最高预算，但超过无需再次询问用户的阈值。", "handler": "Agent + 用户确认流程",
        "handler_status": "当前项目只产生“需要确认”状态，不替用户完成真实确认。", "recovery": "向用户展示当前金额并取得明确确认后重新检查。",
        "final_impact": "当前请求暂停，等待用户重新确认。", "statuses": {"L1": "已通过", "L2": "已通过", "L4": "需要确认"},
    },
    "S09": {
        "primary_stage": "L3", "detection_stage": "L4", "failure_type": "F3", "fault": "order_total_changed",
        "source": "用户确认订单快照 + 商户最终订单快照", "detector": "Order Validator",
        "basis": "订单总金额和商品单价与用户确认时不一致，机器差异列表已记录变化。", "handler": "Agent + 用户确认流程",
        "handler_status": "当前项目只要求重新确认，不自动代表用户接受新订单。", "recovery": "展示订单变化并重新取得用户确认；绑定不可靠时停止。",
        "final_impact": "付款前暂停，原确认不能直接复用于变化后的订单。", "statuses": {"L1": "已通过", "L2": "已通过", "L4": "需要确认"},
    },
    "S10": {
        "primary_stage": "L7", "detection_stage": "L7", "failure_type": "F6", "fault": "delivery_failed",
        "source": "固定离线商户履约记录", "detector": "Lifecycle Manager",
        "basis": "付款成功，但履约状态为失败，且请求、订单、支付与履约绑定检查一致。", "handler": "Remediation Manager",
        "handler_status": "概念角色 / 后续能力；当前项目仅标记需要补救，未执行真实退款、争议或重新履约。",
        "recovery": "进入补救；后续可扩展重新履约、退款、争议或人工处理。",
        "final_impact": "支付成功，但用户任务失败；需要补救并保留证据。",
        "statuses": {"L1": "已通过", "L2": "已通过", "L4": "已通过", "L5": "已通过", "L6": "已通过", "L7": "异常", "L8": "等待处理", "L9": "等待处理"},
    },
    "S11": {
        "primary_stage": "L8", "detection_stage": "L8", "failure_type": "F8", "fault": "full_refund_after_fulfillment_failure",
        "source": "固定离线退款记录 + 原支付、订单与履约失败证据", "detector": "Remediation Manager",
        "basis": "退款记录与原 payment/order/currency 绑定一致，退款金额等于原支付金额，且退款状态为成功。",
        "handler": "Remediation Manager",
        "handler_status": "协议中立实验层；当前只评估固定离线退款/争议记录，不调用真实退款接口或卡组织争议网络。",
        "recovery": "全额退款记录验证通过后，经济补救标记为已完成；原购买任务仍保持失败。",
        "final_impact": "用户原购买任务仍为失败，但全额退款使经济补救状态达到 RESOLVED。",
        "statuses": {"L1": "已通过", "L2": "已通过", "L4": "已通过", "L5": "已通过", "L6": "已通过", "L7": "异常", "L8": "完成", "L9": "完成"},
    },
    "S12": {
        "primary_stage": "L5", "detection_stage": "L6", "failure_type": "F5", "fault": "payment_response_timeout_or_unknown_state",
        "stage_display": "L5-L6 支付发起 / 执行 + 支付状态确认",
        "source": "固定离线初始支付执行观察 + 后续状态查询观察",
        "detector": "Payment State / Recovery Manager",
        "basis": "原 payment/provider reference 与 request/order/idempotency identity 绑定一致；初始 UNKNOWN，后续查询确认原支付 SUCCEEDED。",
        "handler": "Payment Recovery Manager",
        "handler_status": "协议中立离线恢复层；只判断状态查询与安全重试资格，不执行第二次真实扣款。",
        "recovery": "查询原交易状态；确认原支付成功后继续使用原支付结果，并禁止再次扣款。",
        "final_impact": "原支付状态从 UNKNOWN 恢复为可信 SUCCEEDED；retry_allowed=false；履约与用户任务结果均未推断。",
        "statuses": {"L1": "已通过", "L2": "已通过", "L4": "已通过"},
    },
    "S13": {
        "primary_stage": "L2", "detection_stage": "L4", "failure_type": "F2", "fault": "agent_identity_mismatch",
        "stage_display": "L1-L2 用户授权 + Agent 决策 / 意图",
        "source": "用户委托 expected_agent_id + 付款请求声明 agent_id",
        "detector": "Declared Identity Binding Fact + Mandate Validator",
        "basis": "可信执行层只确认两个声明标识引用不一致；支付域依据用户委托规则把该不一致映射为 DENY。",
        "handler": "支付编排 / Agent",
        "handler_status": "只阻止当前离线请求并记录标识绑定证据；未执行真实身份核验、认证器验证或凭证链验证。",
        "recovery": "停止当前请求；核实真实身份与委托关系后，使用可验证的身份凭证和新的有效请求重新进入检查。",
        "final_impact": "付款前被阻止；字符串标识比较不被表述为真实身份认证。",
        "statuses": {"L1": "已通过", "L2": "异常", "L4": "异常"},
    },
}


def scenario_exception_profile(sample_id: str) -> dict[str, Any]:
    try:
        profile = deepcopy(_SCENARIO_PROFILES[sample_id])
    except KeyError as exc:
        raise ValueError(f"unknown exception-matrix scenario: {sample_id}") from exc

    if profile["primary_stage"] not in {item["id"] for item in LIFECYCLE_STAGES}:
        raise ValueError(f"unknown lifecycle stage: {profile['primary_stage']}")
    if profile["detection_stage"] not in {item["id"] for item in LIFECYCLE_STAGES}:
        raise ValueError(f"unknown detection stage: {profile['detection_stage']}")
    if profile["failure_type"] not in FAILURE_TYPES:
        raise ValueError(f"unknown failure type: {profile['failure_type']}")
    unknown_statuses = set(profile["statuses"].values()) - STAGE_STATUSES
    if unknown_statuses:
        raise ValueError(f"unknown lifecycle stage status: {sorted(unknown_statuses)}")
    return profile


def lifecycle_stage_catalog() -> list[dict[str, str]]:
    return [dict(item) for item in LIFECYCLE_STAGES]

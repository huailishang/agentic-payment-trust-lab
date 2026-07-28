from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from .exception_matrix import FAILURE_TYPES, lifecycle_stage_catalog, scenario_exception_profile


DECISION_PRESENTATION_ZH = {
    "ALLOW": {
        "label_zh": "可以继续",
        "explanation_zh": "当前离线检查没有发现阻止条件。",
        "next_action_zh": "可以进入后续模拟步骤，但这不代表真实支付已经授权。",
    },
    "DENY": {
        "label_zh": "已阻止",
        "explanation_zh": "请求明确越过了用户授权的硬边界。",
        "next_action_zh": "停止当前请求，并向用户或开发者说明越权字段。",
    },
    "CONFIRMATION_REQUIRED": {
        "label_zh": "需要用户重新确认",
        "explanation_zh": "关键条件已经变化，不能继续复用原来的确认。",
        "next_action_zh": "展示变化，取得用户对新条件的明确确认后再重新检查。",
    },
    "INDETERMINATE": {
        "label_zh": "暂时无法判断",
        "explanation_zh": "信息缺失、相互矛盾或对象无法可靠绑定。",
        "next_action_zh": "补齐或核实信息；在能够可靠判断前不要继续。",
    },
}


REASON_PRESENTATION_ZH = {
    "required_field_missing": ("缺少必填字段", "判断所需的基础字段没有提供。", "补齐字段后重新检查。"),
    "currency_mismatch": ("币种不一致", "付款请求与用户委托使用了不同币种。", "统一并重新确认币种。"),
    "duplicate_request": ("检测到重复请求", "相同请求编号已经处理过，继续可能造成重复付款。", "停止重放并查询原请求结果。"),
    "invalid_amount": ("金额无效", "付款金额必须大于零。", "修正金额后重新提交。"),
    "over_budget": ("超过最高预算", "付款金额超过用户设定的硬上限。", "停止请求；如确需提高预算，应重新取得授权。"),
    "merchant_out_of_scope": ("商户超出授权范围", "付款请求中的商户不在用户允许列表内。", "停止请求或让用户重新授权商户。"),
    "category_out_of_scope": ("商品品类超出授权范围", "付款请求的商品品类不在用户允许范围内。", "停止请求或重新取得品类授权。"),
    "mandate_expired": ("用户委托已经过期", "请求发生时原授权已失效。", "取得新的有效委托。"),
    "count_exceeded": ("交易次数超限", "本次执行会超过用户允许的交易次数。", "停止请求并核对已执行次数。"),
    "agent_identity_mismatch": ("付款智能体不匹配", "发起请求的智能体不是委托中指定的智能体。", "核实智能体身份和委托绑定。"),
    "confirmation_threshold_exceeded": ("超过免确认阈值", "金额没有超过最高预算，但超过了无需再次询问用户的阈值。", "向用户展示金额并请求确认。"),
    "order_snapshot_missing": ("缺少订单快照", "用户确认的订单或商户最终订单缺失，无法进行可靠比较。", "补齐两个订单快照。"),
    "order_id_mismatch": ("订单编号不一致", "两个快照可能不是同一个订单。", "核对订单编号和来源。"),
    "authorized_order_mandate_mismatch": ("确认订单未绑定当前委托", "用户确认的订单引用了其他委托。", "核对授权订单的委托引用。"),
    "order_mandate_mismatch": ("最终订单未绑定当前委托", "商户最终订单引用了其他委托。", "核对最终订单的委托引用。"),
    "authorized_order_merchant_mismatch": ("订单快照商户不一致", "用户确认订单与最终订单属于不同商户。", "核对商户和订单来源。"),
    "authorized_order_currency_mismatch": ("订单快照币种不一致", "用户确认订单与最终订单使用不同币种。", "取得币种一致的新订单。"),
    "order_request_amount_mismatch": ("付款金额与最终订单不一致", "付款请求金额不能与最终订单总额对应。", "重新生成与最终订单一致的付款请求。"),
    "order_request_currency_mismatch": ("付款币种与最终订单不一致", "付款请求与最终订单使用不同币种。", "核对币种并重新生成请求。"),
    "order_request_merchant_mismatch": ("付款商户与最终订单不一致", "付款请求与最终订单指向不同商户。", "核对商户并重新生成请求。"),
    "order_payee_changed": ("收款方发生变化", "本地证据只能看出收款方变了，不能证明新收款方是否合法。", "暂停并核实收款方身份。"),
    "duplicate_order_item_id": ("商品编号重复", "同一订单内出现重复商品编号，比较结果会产生歧义。", "修正为唯一商品编号后重试。"),
    "order_item_category_out_of_scope": ("最终商品品类越权", "最终订单包含用户没有授权的商品品类。", "阻止请求并展示越权商品。"),
    "order_total_changed": ("订单总金额发生变化", "商户最终订单总额与用户确认的总额不同。", "展示新总额并重新取得用户确认。"),
    "order_items_changed": ("订单商品集合发生变化", "最终订单新增、删除或替换了商品。", "展示商品变化并重新确认。"),
    "unauthorized_addon_added": ("新增非产品附加项", "最终订单新增了 kind 不是 product 的项目。", "展示附加项并重新确认；若品类越权则阻止。"),
    "order_item_name_changed": ("商品名称发生变化", "相同商品编号对应的名称发生了变化。", "核对商品身份并重新确认。"),
    "order_item_category_changed": ("商品品类发生变化", "相同商品编号的最终品类与确认时不同。", "核对新类别是否仍在授权范围内。"),
    "order_item_quantity_changed": ("商品数量发生变化", "最终订单中的商品数量与用户确认时不同。", "展示新数量并重新确认。"),
    "order_item_unit_amount_changed": ("商品单价发生变化", "最终订单中的商品单价与用户确认时不同。", "展示新单价并重新确认。"),
    "order_item_kind_changed": ("商品类型发生变化", "商品从产品、附加项或订阅等类型之一变成了另一种。", "展示新类型并重新确认。"),
    "order_service_changed": ("服务标识发生变化", "最终订单对应的服务对象与确认时不同。", "核对服务内容并重新确认。"),
    "order_fulfilment_terms_changed": ("履约条款发生变化", "交付或履约条件与用户确认时不同。", "展示新条款并重新确认。"),
    "order_quote_expired": ("报价已经过期", "付款请求发生时已经超过最终订单的报价有效期。", "取得有效新报价并重新确认。"),
    "fulfillment_failed_after_payment": ("付款后履约失败", "支付已经完成，但商品或服务没有成功履约。", "保留支付与履约证据并进入退款、争议或其他补救流程。"),
    "fulfillment_status_unknown_after_payment": ("付款后履约状态未知", "支付状态已知，但目前无法确认商品或服务是否成功履约。", "继续查询履约状态，在明确前不要把用户任务标记成功。"),
    "payment_execution_failed": ("支付执行失败", "支付执行记录显示失败，用户任务不能当作已经完成。", "停止后续成功流程并根据支付状态进入恢复或重新发起路径。"),
    "payment_status_unknown": ("支付状态未知", "当前无法判断原支付到底成功还是失败。", "先查询原交易状态，禁止盲目再次扣款。"),
    "partial_refund_requires_further_remediation": ("仅完成部分退款", "退款金额不足以覆盖需要补救的全部金额。", "继续处理剩余退款、争议或其他补救。"),
    "refund_failed": ("退款失败", "退款执行没有成功完成。", "查询失败原因并进入重试、人工处理或其他补救路径。"),
    "refund_status_unknown": ("退款状态未知", "目前无法确认退款是否已经成功。", "先查询原退款状态，不要重复发起结果未知的退款。"),
    "dispute_order_binding_mismatch": ("争议与订单不匹配", "争议记录无法可靠绑定到当前订单。", "核对争议与原订单的关联证据。"),
    "dispute_payment_binding_mismatch": ("争议与支付不匹配", "争议记录无法可靠绑定到当前支付。", "核对争议与原支付的关联证据。"),
    "dispute_requires_review": ("争议仍需审核", "当前争议还没有形成可验证的最终处理结果。", "保留证据并继续等待或进行人工审核。"),
    "dispute_resolution_outcome_unverified": ("争议结果尚未验证", "争议虽然有状态变化，但经济补救结果仍无法独立确认。", "继续核对最终退款、赔付或其他补救证据。"),
    "dispute_status_unknown": ("争议状态未知", "当前无法确认争议处理到了哪个阶段。", "查询争议状态并保留现有证据。"),
    "payment_state_recovered_as_succeeded": ("确认原支付已经成功", "后续可信状态查询确认原交易已经成功。", "继续使用原交易结果，禁止再次扣款。"),
    "payment_state_still_unknown": ("原支付仍然状态未知", "后续查询仍无法确定原交易是否成功。", "继续查询或进入人工复核，禁止重复扣款。"),
    "payment_still_pending": ("原支付仍在处理中", "后续查询显示原交易尚未结束。", "等待并再次查询，不要新建重复支付。"),
    "payment_confirmed_failed_retry_candidate": ("原支付确认失败，可进入安全重试候选", "原交易已经确认失败，且没有成功或状态未明的并行尝试。", "只允许进入重试候选；是否真正重试仍由支付业务规则决定。"),
    "existing_successful_payment_attempt": ("已经存在成功支付尝试", "同一业务请求已经有另一笔支付成功。", "使用现有成功结果，禁止再次扣款。"),
    "unresolved_payment_attempt_exists": ("仍有支付尝试状态未明", "同一业务请求还有处理中或状态未知的支付尝试。", "先查询这些尝试，明确前禁止再次扣款。"),
    "idempotency_boundary_missing": ("缺少幂等边界", "原支付没有可验证的幂等键，无法安全区分重试和重复扣款。", "先建立明确幂等边界，再考虑后续恢复。"),
    "payment_status_observation_conflicts_with_known_success": ("状态查询与已知成功记录冲突", "新的失败观察与已有成功支付记录相冲突。", "停止自动恢复并人工核对支付机构状态。"),
    "payment_status_observation_payment_mismatch": ("状态查询指向了其他支付", "查询结果的支付编号与原交易不一致。", "重新查询正确的原交易。"),
    "payment_status_observation_order_mismatch": ("状态查询指向了其他订单", "查询结果的订单编号与原交易不一致。", "重新核对订单与支付绑定。"),
    "payment_status_observation_provider_mismatch": ("支付机构引用不一致", "状态查询返回的支付机构引用与原交易不一致。", "核对支付机构引用后再处理恢复。"),
    "payment_status_observation_reference_missing": ("状态查询缺少关键引用", "查询结果缺少支付或订单等必要引用，无法可靠绑定原交易。", "补齐可靠引用后重新查询。"),
}


FIELD_LABELS_ZH = {
    "mandate": "用户委托",
    "request": "付款请求",
    "authorized_order": "用户确认的订单",
    "final_order": "商户最终订单",
    "order": "订单",
    "items": "商品明细",
    "mandate_id": "用户委托编号",
    "mandate_ref": "用户委托引用",
    "user_id": "用户编号",
    "request_id": "请求编号",
    "order_id": "订单编号",
    "order_version": "订单版本",
    "merchant": "商户",
    "payee": "收款方",
    "item_id": "商品编号",
    "name": "商品名称",
    "category": "商品品类",
    "quantity": "数量",
    "unit_amount": "商品单价",
    "kind": "商品类型",
    "amount": "付款金额",
    "max_amount": "最高预算",
    "confirmation_above": "免确认阈值",
    "total_amount": "订单总金额",
    "currency": "币种",
    "expires_at": "委托有效期",
    "quote_expires_at": "报价有效期",
    "occurred_at": "请求发生时间",
    "fulfilment_terms": "履约条款",
    "service_id": "服务标识",
    "candidate_rails": "候选支付轨道",
    "sequence_count": "当前交易次数",
    "max_count": "最大交易次数",
    "agent_id": "付款智能体编号",
    "expected_agent_id": "指定智能体编号",
    "allowed_merchants": "允许商户",
    "allowed_categories": "允许品类",
    "seen_request_ids": "已处理请求编号",
    "payment": "支付执行",
    "payment_execution": "初始支付执行观察",
    "payment_id": "支付编号",
    "provider_ref": "支付机构引用",
    "idempotency_key": "幂等键",
    "payment_status_observation": "支付状态查询观察",
    "known_payment_attempts": "同一业务请求的已知其他支付尝试",
    "observed_at": "状态观察时间",
    "source": "状态来源",
    "initial_status": "初始支付状态",
    "observed_status": "查询观察状态",
    "effective_status": "恢复后可信支付状态",
    "recovery_status": "恢复状态",
    "retry_allowed": "是否允许进入安全重试候选",
    "next_action": "下一步动作",
    "receipt_ref": "支付回执引用",
    "fulfillment": "履约",
    "fulfillment_id": "履约编号",
    "evidence_ref": "履约证据引用",
    "failure_code": "履约失败代码",
    "refund": "退款",
    "refund_id": "退款编号",
    "dispute": "争议",
    "dispute_id": "争议编号",
    "status": "状态",
    "opened_at": "争议发起时间",
    "reason_code": "原因代码",
    "trusted_execution": "可信执行",
    "declared_identity": "声明标识绑定",
    "reason_codes": "原因代码",
    "expected_digest": "预期摘要",
    "actual_digest": "实际摘要",
    "binding_status": "绑定验证状态",
    "binding_reason": "绑定验证原因",
}


LIFECYCLE_STATUS_ZH = {
    "SUCCEEDED": "成功",
    "FAILED": "失败",
    "PENDING": "处理中",
    "UNKNOWN": "状态未知",
    "NOT_REQUIRED": "无需补救",
    "REQUIRED": "需要补救",
    "IN_PROGRESS": "补救处理中",
    "RESOLVED": "补救已完成",
    "OPEN": "争议已发起",
    "UNDER_REVIEW": "争议审核中",
    "RECOVERED": "状态已恢复",
    "UNRESOLVED": "状态仍未恢复",
    "RETRY_CANDIDATE": "可进入安全重试候选",
    "BLOCKED": "禁止重试",
}

LIFECYCLE_ACTION_ZH = {
    "none": "当前无需补救。",
    "preserve_evidence_and_start_remediation": "保留订单、支付回执和履约失败证据，进入后续补救流程。",
    "preserve_evidence_and_investigate_lifecycle_binding": "先保留现有证据并核对订单、支付和履约记录是否属于同一笔交易。",
    "preserve_evidence_and_investigate_fulfillment_status": "保留支付回执并查询真实履约状态，在状态明确前不要把任务标记成功。",
    "preserve_evidence_and_investigate_payment_status": "保留请求和订单证据并查询支付状态，在状态明确前不要重复执行。",
    "wait_for_fulfillment_status": "等待履约状态更新，暂时不要把用户任务标记为成功。",
    "wait_for_payment_status": "等待支付状态更新，暂时不要把用户任务标记为成功。",
    "do_not_treat_task_as_successful": "支付失败时不得把用户任务标记为成功。",
    "economic_remediation_completed_by_full_refund": "全额退款记录已与原交易可靠绑定，经济补救已完成；原购买任务仍保持失败。",
    "continue_remediation_for_remaining_amount": "部分退款不能默认解决全部损失，继续处理剩余金额或其他补救。",
    "continue_dispute_review": "争议仍在处理中，继续保留证据并等待审核结果。",
    "preserve_evidence_and_investigate_remediation_binding": "退款或争议与原支付/订单绑定不一致，保留证据并先核对关联关系。",
    "wait_for_refund_status": "等待退款状态明确，在确认完成前不要把补救标记为已解决。",
    "retry_or_escalate_failed_refund": "退款失败，进入重试、人工处理或其他补救路径。",
    "investigate_refund_status": "退款状态未知，先查询原退款状态，禁止重复发起未知结果的退款。",
    "investigate_dispute_status": "争议状态未知，先查询原争议记录并保留证据。",
    "verify_dispute_resolution_outcome": "争议案件虽已结案，但当前记录没有说明用户是否获得赔付或资金返还；先核实结案结果，再判断经济补救是否完成。",
}

PAYMENT_RECOVERY_ACTION_ZH = {
    "continue_with_original_payment": "状态查询确认原支付已经成功，继续使用原支付结果，禁止再次扣款。",
    "query_again_or_manual_review": "支付结果仍然未知，继续查询原交易或转人工核对，禁止盲目重扣。",
    "wait_and_query_again": "原支付仍在处理中，等待后再次查询，禁止创建第二笔支付。",
    "safe_retry_candidate_with_same_idempotency_boundary": "原支付已明确失败且不存在成功或未决的并行尝试，可进入安全重试候选；仍应复用明确的幂等边界，本实验不执行第二次支付。",
    "investigate_status_observation_binding": "状态查询结果与原 payment/order/provider 引用不一致，不能采用该结果，也不能据此重试。",
    "use_existing_successful_attempt": "同一业务请求已经存在成功支付尝试，直接使用已有成功结果，禁止再次扣款。",
    "query_existing_attempts_before_retry": "同一业务请求仍有 UNKNOWN/PENDING 支付尝试，先查询这些原交易，禁止新增支付。",
    "establish_idempotency_boundary_before_retry": "原支付缺少明确幂等边界，即使查询为失败也不能直接重试；先建立可验证的幂等身份。",
}


SCENARIO_LEARNING_ZH = {
    "S01": ("看懂正常请求为什么可以继续", "用户允许指定智能体在预算内向指定商户购买跑鞋。", "场景通过就是银行已经付款。", "场景通过只表示程序得到了预期判断；付款决策是“可以继续”。"),
    "S02": ("看懂最高预算是硬边界", "付款请求超过用户设置的最高预算。", "超过预算后再问一次就一定能继续。", "硬预算越权会被阻止，必须取得新的授权。"),
    "S03": ("看懂金额合规不代表商品品类合规", "金额不高，但智能体准备购买未授权品类。", "只要金额小就没有风险。", "用户授权包含买什么，而不只是最多花多少。"),
    "S04": ("看懂授权具有有效期", "智能体在用户委托到期后才发起请求。", "用户以前同意过，授权就一直有效。", "过期授权不能继续复用。"),
    "S05": ("看懂请求编号如何防止重复付款", "同一请求编号再次出现。", "内容一样就可以当作一笔新交易。", "重复请求必须先查询原结果，不能直接再次执行。"),
    "S06": ("看懂更换商户也会越权", "商品和金额看似相同，但付款商户不在允许列表。", "商品相同就可以随意换商户。", "商户也是用户授权范围的一部分。"),
    "S07": ("看懂交易次数限制与单笔金额不同", "每笔金额都不高，但本次会超过允许次数。", "每一笔都合规就可以无限执行。", "累计次数是独立的授权边界。"),
    "S08": ("看懂最高预算与免确认阈值不同", "金额没有超过最高预算，但超过了无需再次询问的阈值。", "没超预算就一定可以直接付款。", "预算内仍可能需要用户确认。"),
    "S09": ("看懂订单变化与金额阈值是两类检查", "用户确认480元跑鞋，商户付款前把单价和总额改成490元。", "490元低于500元免确认阈值，所以不用再问用户。", "用户确认的是具体订单；单价和总额变化后必须重新确认。"),
    "S10": ("看懂支付成功不等于用户任务成功", "付款前检查通过，固定离线样品记录付款成功，但商户后续没有成功交付商品。", "只要钱付成功，Agent 的任务就算完成。", "支付、履约和用户任务必须分开记状态；付款成功后履约失败仍是任务失败，并需要保留证据进入补救。"),
    "S11": ("看懂退款成功与原购买任务成功是两回事", "商品没有成功交付后，固定离线样品记录了一笔与原支付、订单正确绑定的全额退款。", "既然钱退回来了，原购买任务就应该改成成功。", "原购买任务仍然失败；全额退款只表示经济补救已经完成，任务结果与补救结果必须分开记录。"),
    "S12": ("看懂支付超时后为什么不能直接再扣一次", "支付请求已经提交，但第一次响应丢失导致状态 UNKNOWN；系统随后查询同一 payment/provider reference，确认原支付其实已经成功。", "接口超时就等于支付失败，可以立刻重新扣款。", "UNKNOWN 只表示当前不知道结果；必须先查询原交易。确认原支付成功后应继续使用原结果，并明确禁止第二次扣款。"),
    "S13": ("看懂声明标识一致与真实身份认证不是一回事", "用户委托指定 agent-shop-001，但付款请求声明自己来自 agent-shop-other。", "只要系统里有一个 agent_id 字符串，就已经完成了真实身份认证。", "可信执行层只能确定声明标识是否与委托指定标识一致；不一致时支付域阻止请求，真正的身份核验和认证仍需要后续凭证与认证器能力。"),
}


STEP_PRESENTATION_ZH = {
    "user-mandate": ("定义授权", "业务需要与用户选择", "把固定授权边界传给智能体", "尚未形成付款请求，也没有执行付款"),
    "agent-intent": ("读取并形成意图", "用户委托", "形成准备购买的商户、品类和计划金额", "不能证明最终付款一定允许"),
    "payment-request": ("形成支付请求", "智能体意图与当前交易参数", "生成统一付款请求对象", "不负责判断是否允许付款"),
    "order-snapshots": ("获取订单快照", "付款请求与商户订单信息", "提供用户确认订单和商户最终订单两个固定槽位", "订单不适用时不会伪造订单数据"),
    "execution-state": ("读取运行状态", "固定样品中的请求历史与次数值", "提供幂等检查和次数检查所需状态", "尚未实现数据库或持久化累计"),
    "protocol-adapter": ("转换或直接传递", "协议对象或中立输入", "生成确定性验证器使用的统一结构", "不负责决定允许或拒绝"),
    "validator": ("执行确定性规则", "委托、付款请求、订单快照和运行状态", "输出四态决策、原因和字段证据", "不调用大模型猜测，也不执行真实支付"),
    "result": ("整理结果", "决策、原因和证据", "生成可回放的结果卡", "不代表银行或卡组织已经授权"),
}


CHECK_STATUS_ZH = {
    "pass": "通过",
    "fail": "失败",
    "confirmation_required": "需确认",
    "indeterminate": "无法判断",
    "not_applicable": "不适用",
}

UNIFIED_CHECK_IDS = (
    "required_fields",
    "currency_consistency",
    "duplicate_request",
    "amount_valid",
    "within_budget",
    "merchant_scope",
    "category_scope",
    "mandate_not_expired",
    "count_within_limit",
    "agent_identity",
    "order_binding",
    "order_content_unchanged",
    "confirmation_threshold",
)

_ORDER_BINDING_INDETERMINATE_CODES = {
    "order_snapshot_missing",
    "order_id_mismatch",
    "authorized_order_mandate_mismatch",
    "order_mandate_mismatch",
    "authorized_order_merchant_mismatch",
    "authorized_order_currency_mismatch",
    "order_request_amount_mismatch",
    "order_request_currency_mismatch",
    "order_request_merchant_mismatch",
    "order_payee_changed",
    "duplicate_order_item_id",
}

_ORDER_CONFIRMATION_CODES = {
    "order_total_changed",
    "order_items_changed",
    "unauthorized_addon_added",
    "order_item_name_changed",
    "order_item_category_changed",
    "order_item_quantity_changed",
    "order_item_unit_amount_changed",
    "order_item_kind_changed",
    "order_service_changed",
    "order_fulfilment_terms_changed",
    "order_quote_expired",
}


REQUIRED_REASON_CODES = frozenset(REASON_PRESENTATION_ZH)


def attach_scenario_presentation(record: dict[str, Any]) -> dict[str, Any]:
    sample_id = str(record["sample_id"])
    objective, story, misconception, takeaway = SCENARIO_LEARNING_ZH[sample_id]
    record["learning"] = {
        "objective_zh": objective,
        "story_zh": story,
        "common_misconception_zh": misconception,
        "takeaway_zh": takeaway,
    }
    enrich_actual_presentation(record["actual"])
    record["differences"] = present_differences(record["actual"].get("order_differences", []))
    record["status_presentation"] = {
        "label_zh": "场景验证符合预期" if record["status"] == "passed" else "场景验证与预期不一致",
        "explanation_zh": (
            "程序实际结果与固定样品的预期一致。"
            if record["status"] == "passed"
            else "程序实际结果与固定样品的预期不同，需要检查实现或测试预言机。"
        ),
    }
    record["walkthrough"] = enrich_walkthrough(record["walkthrough"])
    record["unified_view"] = build_unified_view(
        input_data=record["input"],
        actual=record["actual"],
        status_presentation=record["status_presentation"],
        lifecycle=record.get("lifecycle"),
        payment_recovery=record.get("payment_recovery"),
    )
    record["lifecycle_teaching_view"] = build_lifecycle_teaching_view(record)
    record.setdefault("learning_variants", [])
    return record


def enrich_actual_presentation(actual: dict[str, Any]) -> dict[str, Any]:
    actual["decision_presentation"] = decision_presentation(str(actual["decision"]))
    actual["reason_presentations"] = [
        reason_presentation(str(code)) for code in actual.get("reason_codes", [])
    ]
    actual["evidence_presentations"] = [present_evidence(item) for item in actual.get("evidence", [])]
    return actual


def enrich_walkthrough(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = deepcopy(steps)
    for step in enriched:
        operation, origin, output_summary, does_not_do = STEP_PRESENTATION_ZH.get(
            str(step.get("id")),
            ("传递数据", "上一步", "传给下一步", "不执行真实支付"),
        )
        step["operation_type_zh"] = operation
        step["data_origin_zh"] = origin
        step["output_summary_zh"] = output_summary
        step["does_not_do_zh"] = does_not_do
        step["input_presentation_zh"] = present_data_zh(step.get("input"))
        step["output_presentation_zh"] = present_data_zh(step.get("output"))
    return enriched


def decision_presentation(code: str) -> dict[str, str]:
    value = DECISION_PRESENTATION_ZH.get(code)
    if value is not None:
        return {"code": code, **value}
    return {
        "code": code,
        "label_zh": code,
        "explanation_zh": "暂无中文解释。",
        "next_action_zh": "查看英文技术详情并补充映射。",
    }


def reason_presentation(code: str) -> dict[str, str]:
    value = REASON_PRESENTATION_ZH.get(code)
    if value is None:
        return {
            "code": code,
            "title_zh": code,
            "explanation_zh": "暂无中文解释。",
            "next_action_zh": "查看英文技术详情并补充映射。",
            "known": "false",
        }
    title, explanation, action = value
    return {
        "code": code,
        "title_zh": title,
        "explanation_zh": explanation,
        "next_action_zh": action,
        "known": "true",
    }


def field_path_zh(path: str) -> str:
    parts: list[str] = []
    for raw in path.split("."):
        match = re.fullmatch(r"([A-Za-z_]+)\[item_id=([^\]]+)\]", raw)
        if match:
            parts.append(FIELD_LABELS_ZH.get(match.group(1), match.group(1)))
            parts.append(f"商品 {match.group(2)}")
        else:
            parts.append(FIELD_LABELS_ZH.get(raw, raw))
    return " → ".join(parts)


def present_evidence(item: dict[str, Any]) -> dict[str, Any]:
    code = str(item.get("code", ""))
    reason = reason_presentation(code)
    return {
        "code": code,
        "title_zh": reason["title_zh"] if reason["known"] == "true" else "字段证据",
        "field_path": item.get("field_path"),
        "field_label_zh": field_path_zh(str(item.get("field_path", ""))),
        "observed": item.get("observed"),
        "expected": item.get("expected"),
    }


def present_differences(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for item in items:
        code = str(item["code"])
        reason = reason_presentation(code)
        if code == "order_quote_expired":
            explanation = f"报价有效期为 {item['before']}，请求发生时间为 {item['after']}，请求发生时报价已经过期。"
        else:
            explanation = f"{reason['title_zh']}：从 {item['before']} 变为 {item['after']}。"
        values.append(
            {
                **item,
                "field_label_zh": field_path_zh(str(item["field_path"])),
                "title_zh": reason["title_zh"],
                "explanation_zh": explanation,
            }
        )
    return values


def present_data_zh(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            FIELD_LABELS_ZH.get(str(key), str(key)): present_data_zh(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [present_data_zh(item) for item in value]
    return value


_STAGE_DETAIL_BLUEPRINT = {
    "L1": ("确认用户给 Agent 的授权边界。", "用户授权 / Mandate", "Agent 与后续付款前检查", "不生成订单，也不代表已经付款。"),
    "L2": ("Agent 在授权范围内形成准备执行的购买意图。", "用户授权", "订单 / 报价与付款请求形成环节", "不决定最终是否允许付款。"),
    "L3": ("形成或比较订单、报价及交易对象。", "Agent 意图与商户订单信息", "付款前检查", "不自行放行付款，也不执行资金转移。"),
    "L4": ("用确定性规则检查当前请求能否继续。", "委托、请求、订单和运行状态", "支付编排 / Agent", "不执行真实支付，也不替用户完成确认。"),
    "L5": ("向支付能力发起或记录一次支付执行。", "付款前允许结果与支付执行记录", "支付状态确认", "本项目不连接真实银行卡、银行或支付网络。"),
    "L6": ("确认支付到底成功、失败、处理中还是未知。", "支付执行与回执状态", "履约与恢复流程", "不把付款成功直接等同于用户任务成功。"),
    "L7": ("确认商品或服务是否真正交付。", "订单、支付状态与履约记录", "补救 / 售后", "不因为支付成功就假设履约成功。"),
    "L8": ("异常后决定进入何种补救方向。", "失败状态与证据链", "后续退款、争议、重新履约或人工处理", "当前项目尚未真正执行退款、争议或重新履约。"),
    "L9": ("汇总最终任务状态并保留证据。", "前序生命周期状态与证据", "审计、复盘或后续处理", "不在这里重新计算前面各阶段的业务判断。"),
}

_STAGE_WALKTHROUGH_IDS = {
    "L1": ("user-mandate",),
    "L2": ("agent-intent",),
    "L3": ("order-snapshots",),
    "L4": ("payment-request", "execution-state", "protocol-adapter", "validator"),
    "L5": (),
    "L6": (),
    "L7": (),
    "L8": (),
    "L9": ("result",),
}


_TRUSTED_EXECUTION_STAGE_BLUEPRINT = {
    "L1": {
        "relevant": True,
        "status_code": "PLANNED",
        "status_zh": "规划中",
        "capabilities": ["Signature", "Identity"],
        "purpose_zh": "验证授权对象由谁确认、签署关系是否可验证。",
        "current_state_zh": "当前主仓库尚未实现签名与身份验证组件。",
        "returns_zh": "未来只返回签署关系、身份绑定等确定性验证事实。",
        "does_not_decide_zh": "不判断用户授权范围在业务上是否合理，也不替 Payment Domain 决定是否允许支付。",
    },
    "L2": {
        "relevant": True,
        "status_code": "PROTOTYPE",
        "status_zh": "已接入声明标识绑定",
        "capabilities": ["声明标识绑定（Declared Identity Reference Binding）"],
        "purpose_zh": "验证付款请求声明的智能体标识与用户委托指定标识是否一致。",
        "current_state_zh": "S13 已消费声明标识绑定事实；这里只比较给定标识引用，不执行真实身份核验或认证器验证。",
        "returns_zh": "返回声明标识引用 VALID / INVALID / MISSING_EVIDENCE。",
        "does_not_decide_zh": "标识一致不等于身份已认证；ALLOW / DENY 仍由 Payment Domain 的委托规则决定。",
    },
    "L3": {
        "relevant": True,
        "status_code": "PROTOTYPE",
        "status_zh": "实验已接入",
        "capabilities": ["Canonicalization", "Hash", "Binding"],
        "purpose_zh": "把订单对象转换为稳定表示，并验证授权订单与最终订单是否仍绑定同一对象。",
        "current_state_zh": "TE01 Hash、TE02 Canonicalization 与 TE03 Binding 已实现；S09 已真实消费订单绑定验证事实。",
        "returns_zh": "当前返回对象摘要与 VALID / INVALID / MISSING_EVIDENCE 等绑定验证事实。",
        "does_not_decide_zh": "对象变化不自动等于 DENY；涨价、换商品或非关键字段变化仍由 Payment Domain 判断。",
    },
    "L4": {
        "relevant": True,
        "status_code": "PROTOTYPE",
        "status_zh": "已接入 S09",
        "capabilities": ["Binding Verification Fact"],
        "purpose_zh": "向付款前检查提供订单绑定是否成立、证据是否缺失的确定性事实。",
        "current_state_zh": "S09 在保留原有字段比较规则的同时，已经消费 Trusted Execution 的 Binding 结果作为证据。",
        "returns_zh": "返回 VALID / INVALID / MISSING_EVIDENCE 等绑定事实。",
        "does_not_decide_zh": "不直接返回 ALLOW、DENY 或 CONFIRMATION_REQUIRED。",
    },
    "L5": {
        "relevant": True,
        "status_code": "PROTOTYPE",
        "status_zh": "已接入 S12",
        "capabilities": ["Execution Identity", "Idempotency"],
        "purpose_zh": "验证一次支付执行是否属于原请求，以及唯一执行边界是否存在。",
        "current_state_zh": "TE04 已提供执行身份与幂等事实；S12 在失败恢复分支消费幂等边界和同请求尝试清单。",
        "returns_zh": "返回执行引用一致性、幂等边界是否存在及相关尝试清单等事实。",
        "does_not_decide_zh": "幂等验证通过不等于允许再次扣款；是否可重试仍由 Payment Domain 决定。",
    },
    "L6": {
        "relevant": True,
        "status_code": "PROTOTYPE",
        "status_zh": "已接入 S12",
        "capabilities": ["Status Observation", "Idempotency"],
        "purpose_zh": "验证查询到的支付状态是否可靠绑定原交易，并暴露重复执行相关事实。",
        "current_state_zh": "S12 已消费 TE04 的状态观察绑定事实；失败状态下再结合幂等事实进入原有恢复策略。",
        "returns_zh": "返回状态观察 VALID / INVALID / MISSING_EVIDENCE，以及幂等边界和相关尝试事实。",
        "does_not_decide_zh": "不决定等待、再次查询、安全重试候选或人工介入。",
    },
    "L7": {
        "relevant": False,
        "status_code": "NO_SEPARATE_COMPONENT",
        "status_zh": "当前无独立可信组件",
        "capabilities": [],
        "purpose_zh": "当前阶段主要依赖履约系统提供外部事实和 Payment Domain 的生命周期判断。",
        "current_state_zh": "暂不为了完整性提前抽取独立 Trusted Execution 组件。",
        "returns_zh": "当前没有独立可信执行返回值。",
        "does_not_decide_zh": "不因为缺少独立可信组件就假设履约成功。",
    },
    "L8": {
        "relevant": True,
        "status_code": "PLANNED",
        "status_zh": "规划中",
        "capabilities": ["Original Transaction Binding", "State Validation"],
        "purpose_zh": "验证退款、争议等后续动作是否引用正确原交易，并检查给定状态迁移是否合法。",
        "current_state_zh": "当前退款和争议绑定检查仍在 Payment Domain 内完成。",
        "returns_zh": "未来返回原交易绑定和状态迁移验证事实。",
        "does_not_decide_zh": "不决定业务上是否应该退款、撤销或发起争议。",
    },
    "L9": {
        "relevant": True,
        "status_code": "PLANNED",
        "status_zh": "规划中",
        "capabilities": ["Audit Evidence", "Hash Chain"],
        "purpose_zh": "验证归档证据是否完整、历史记录是否被篡改。",
        "current_state_zh": "当前尚未实现独立链式审计组件。",
        "returns_zh": "未来返回证据完整性和篡改检测事实。",
        "does_not_decide_zh": "不把审计完整性等同于业务合法、生产安全或法律终局。",
    },
}


def _trusted_execution_for_stage(stage_id: str, stage_status: str) -> dict[str, Any]:
    value = dict(_TRUSTED_EXECUTION_STAGE_BLUEPRINT[stage_id])
    value["capabilities"] = list(value["capabilities"])
    value["scenario_active"] = stage_status != "未参与"
    if not value["scenario_active"]:
        value["status_code"] = "NOT_USED_IN_SCENARIO"
        value["status_zh"] = "本场景未用"
    return value


def _display_profile_for_record(record: dict[str, Any]) -> dict[str, Any]:
    """Build the matrix profile from the *current* machine result.

    Fixed S-scenario profiles still provide the teaching vocabulary, but the
    current decision/lifecycle/recovery result decides where the matrix marker
    moves after an interactive edit. This keeps the matrix from describing the
    original fixture after the backend has already produced a different result.
    """

    sample_id = str(record["sample_id"])
    base = scenario_exception_profile(sample_id)
    actual = dict(record.get("actual") or {})
    lifecycle = dict(record.get("lifecycle") or {})
    payment_recovery = dict(record.get("payment_recovery") or {})

    if payment_recovery:
        return _display_profile_for_payment_recovery(base, payment_recovery)
    if lifecycle:
        return _display_profile_for_lifecycle(base, lifecycle)
    return _display_profile_for_prepayment(base, actual)


def _display_profile_for_prepayment(
    base: dict[str, Any], actual: dict[str, Any]
) -> dict[str, Any]:
    reason_codes = [str(code) for code in actual.get("reason_codes", [])]
    decision = str(actual.get("decision") or "INDETERMINATE")
    if not reason_codes and decision == "ALLOW":
        normal = scenario_exception_profile("S01")
        normal.update(
            {
                "source": "当前交互输入 + 本地付款前检查结果",
                "basis": "当前输入未触发阻止、重新确认或无法判断条件。",
                "final_impact": "付款前检查允许继续；仍只是离线模拟，不代表真实支付已授权。",
            }
        )
        return normal

    primary_code = reason_codes[0] if reason_codes else "current_result_indeterminate"
    presentation = reason_presentation(primary_code)
    order_related = primary_code.startswith("order_") or primary_code.startswith("authorized_order_")
    identity_related = primary_code in {"agent_identity_mismatch", "order_payee_changed"}
    duplicate_related = primary_code == "duplicate_request"

    if duplicate_related:
        failure_type = "F4"
    elif identity_related:
        failure_type = "F2"
    elif order_related or primary_code == "currency_mismatch":
        failure_type = "F3"
    else:
        failure_type = "F1"

    primary_stage = "L2" if primary_code == "agent_identity_mismatch" else "L3" if order_related else "L4"
    final_impact = {
        "DENY": "付款前被阻止，不进入支付执行。",
        "CONFIRMATION_REQUIRED": "当前请求暂停，等待用户确认后重新检查。",
        "INDETERMINATE": "当前证据不足或存在冲突，在能够可靠判断前不继续支付。",
    }.get(decision, "付款前检查结果已经更新。")

    profile = dict(base)
    profile.update(
        {
            "primary_stage": primary_stage,
            "detection_stage": "L4",
            "failure_type": failure_type,
            "fault": primary_code,
            "source": "当前交互输入 + 本地付款前检查结果",
            "detector": "付款前检查 / 对应验证器",
            "basis": presentation["explanation_zh"],
            "handler": "支付编排 / Agent",
            "handler_status": "当前项目只更新离线判断，不执行真实支付。",
            "recovery": presentation["next_action_zh"],
            "final_impact": final_impact,
            "statuses": {"L1": "已通过", "L2": "已通过"},
        }
    )
    if primary_stage == "L2":
        profile["statuses"]["L2"] = "异常"
    return profile


def _display_profile_for_lifecycle(
    base: dict[str, Any], lifecycle: dict[str, Any]
) -> dict[str, Any]:
    payment_status = str(lifecycle.get("payment_status") or "UNKNOWN")
    fulfillment_status = str(lifecycle.get("fulfillment_status") or "UNKNOWN")
    refund_status = lifecycle.get("refund_status")
    dispute_status = lifecycle.get("dispute_status")
    remediation = dict(lifecycle.get("remediation") or {})
    remediation_status = str(remediation.get("status") or "NOT_REQUIRED")
    task_status = str(lifecycle.get("task_status") or "UNKNOWN")
    reason_codes = [str(code) for code in lifecycle.get("reason_codes", [])]

    if (
        payment_status == "SUCCEEDED"
        and fulfillment_status == "SUCCEEDED"
        and refund_status is None
        and dispute_status is None
        and remediation_status == "NOT_REQUIRED"
        and task_status == "SUCCEEDED"
    ):
        profile = dict(base)
        profile.update(
            {
                "primary_stage": "L9",
                "detection_stage": "L9",
                "failure_type": "NONE",
                "fault": "normal_task_completed",
                "source": "当前交互生命周期状态",
                "detector": "Lifecycle Manager",
                "basis": "支付与履约均成功，当前没有需要补救的异常。",
                "handler": "任务结束 / 证据归档",
                "handler_status": "当前只形成离线状态结论，不代表真实结算完成。",
                "recovery": "无需异常恢复。",
                "final_impact": "当前模拟用户任务完成。",
                "statuses": {"L1": "已通过", "L2": "已通过"},
            }
        )
        return profile

    if refund_status is not None or dispute_status is not None or remediation_status in {"IN_PROGRESS", "RESOLVED"}:
        primary_stage = detection_stage = "L8"
        failure_type = "F8"
        fault = reason_codes[0] if reason_codes else "remediation_state_changed"
        if refund_status == "SUCCEEDED" and remediation_status == "RESOLVED":
            basis = "退款记录显示经济补救已经完成；原购买任务与经济补救状态仍分开记录。"
            recovery = "保留原失败任务和退款完成证据。"
        elif refund_status is not None:
            basis = f"当前退款状态为 {refund_status}，补救状态为 {remediation_status}。"
            recovery = "按当前退款状态继续查询、处理或人工复核。"
        else:
            basis = f"当前争议状态为 {dispute_status}，补救状态为 {remediation_status}。"
            recovery = "按当前争议状态继续审核并保留证据。"
    elif fulfillment_status != "SUCCEEDED":
        primary_stage = detection_stage = "L7"
        failure_type = "F6"
        fault = reason_codes[0] if reason_codes else "fulfillment_state_changed"
        basis = f"当前支付状态为 {payment_status}，履约状态为 {fulfillment_status}。"
        recovery = "根据履约状态继续等待、查询或进入补救流程。"
    else:
        primary_stage, detection_stage = "L5", "L6"
        failure_type = "F5"
        fault = reason_codes[0] if reason_codes else "payment_state_changed"
        basis = f"当前支付状态为 {payment_status}，用户任务状态为 {task_status}。"
        recovery = "先确认支付状态，再决定后续生命周期动作。"

    profile = dict(base)
    profile.update(
        {
            "primary_stage": primary_stage,
            "detection_stage": detection_stage,
            "failure_type": failure_type,
            "fault": fault,
            "source": "当前交互生命周期状态",
            "detector": "Lifecycle / Remediation Manager",
            "basis": basis,
            "handler": "生命周期 / 补救流程",
            "handler_status": "当前只重新计算离线生命周期状态，未执行真实退款、争议或履约。",
            "recovery": recovery,
            "final_impact": f"当前用户任务状态为 {task_status}。",
            "statuses": {"L1": "已通过", "L2": "已通过"},
        }
    )
    return profile


def _display_profile_for_payment_recovery(
    base: dict[str, Any], payment_recovery: dict[str, Any]
) -> dict[str, Any]:
    reason_codes = [str(code) for code in payment_recovery.get("reason_codes", [])]
    primary_code = reason_codes[0] if reason_codes else "payment_recovery_state_changed"
    presentation = reason_presentation(primary_code)
    concurrency_codes = {
        "existing_successful_payment_attempt",
        "unresolved_payment_attempt_exists",
        "idempotency_boundary_missing",
    }
    failure_type = "F4" if primary_code in concurrency_codes else "F5"
    recovery_status = str(payment_recovery.get("recovery_status") or "UNRESOLVED")
    effective_status = str(payment_recovery.get("effective_status") or "UNKNOWN")
    retry_allowed = bool(payment_recovery.get("retry_allowed"))

    profile = dict(base)
    profile.update(
        {
            "primary_stage": "L5",
            "detection_stage": "L6",
            "failure_type": failure_type,
            "fault": primary_code,
            "stage_display": "L5-L6 支付发起 / 执行 + 支付状态确认",
            "source": "当前交互支付执行记录 + 状态查询 + 幂等/并行尝试事实",
            "detector": "Payment State / Recovery Manager",
            "basis": presentation["explanation_zh"],
            "handler": "Payment Recovery Manager",
            "handler_status": "当前只重新计算离线恢复资格，不执行第二次真实扣款。",
            "recovery": presentation["next_action_zh"],
            "final_impact": (
                f"当前可信支付状态为 {effective_status}；恢复状态 {recovery_status}；"
                f"允许进入重试候选：{'是' if retry_allowed else '否'}。"
            ),
            "statuses": {"L1": "已通过", "L2": "已通过", "L4": "已通过"},
        }
    )
    return profile


_PROTOCOL_STAGE_TARGET_PREFIXES = {
    "L1": ("mandate.",),
    "L2": ("agent.", "intent."),
    "L3": ("order.", "authorized_order.", "final_order.", "quote."),
    "L4": ("request.",),
}


def _protocol_mapping_for_stage(
    protocol: dict[str, Any],
    stage_id: str,
) -> dict[str, Any]:
    """Return only protocol mappings that explicitly belong to one lifecycle stage."""

    trace_available = protocol.get("name") not in {None, "", "NEUTRAL"}
    if not trace_available:
        return {
            "trace_available": False,
            "available": False,
            "protocol_name": None,
            "protocol_version": None,
            "source": None,
            "field_mapping": [],
            "raw_input": None,
            "neutral_output": None,
            "message_zh": "当前场景使用协议中立固定样品，无外部协议字段映射。",
        }

    prefixes = _PROTOCOL_STAGE_TARGET_PREFIXES.get(stage_id, ())
    stage_mappings = [
        dict(item)
        for item in protocol.get("field_mapping") or []
        if str(item.get("to") or "").startswith(prefixes)
    ]
    available = bool(stage_mappings)

    neutral_output = dict(protocol.get("neutral_output") or {})
    if stage_id == "L1":
        stage_neutral_output = {"mandate": neutral_output.get("mandate")}
    elif stage_id == "L4":
        stage_neutral_output = {"request": neutral_output.get("request")}
    else:
        stage_neutral_output = None

    raw_input = dict(protocol.get("raw_input") or {})
    if stage_id == "L1":
        stage_raw_input = {
            key: raw_input.get(key)
            for key in ("open_payment_mandate", "experiment_context")
            if key in raw_input
        }
    elif stage_id == "L4":
        stage_raw_input = {
            key: raw_input.get(key)
            for key in ("payment_mandate",)
            if key in raw_input
        }
    else:
        stage_raw_input = None

    return {
        "trace_available": True,
        "available": available,
        "protocol_name": protocol.get("name"),
        "protocol_version": protocol.get("version"),
        "source": protocol.get("source"),
        "field_mapping": stage_mappings,
        "raw_input": stage_raw_input,
        "neutral_output": stage_neutral_output,
        "message_zh": (
            f"当前阶段展示 {protocol.get('name')} Adapter 的阶段专属字段映射。"
            if available
            else "当前存在协议级 Adapter trace，但没有该生命周期阶段的专属字段映射。"
        ),
    }


def build_lifecycle_teaching_view(record: dict[str, Any]) -> dict[str, Any]:
    """Build the lifecycle-first teaching projection from backend-produced scenario results."""

    sample_id = str(record["sample_id"])
    profile = _display_profile_for_record(record)
    stages = lifecycle_stage_catalog()
    status_by_stage = _machine_stage_statuses(record, profile)
    walkthrough_by_id = {str(item.get("id")): item for item in record.get("walkthrough", [])}
    input_data = dict(record.get("input") or {})
    protocol = dict(record.get("protocol") or {})
    lifecycle = dict(record.get("lifecycle") or {})
    payment_recovery = dict(record.get("payment_recovery") or {})

    stage_views: list[dict[str, Any]] = []
    for stage in stages:
        stage_id = stage["id"]
        related_steps = [
            walkthrough_by_id[step_id]
            for step_id in _STAGE_WALKTHROUGH_IDS[stage_id]
            if step_id in walkthrough_by_id
        ]
        business_meaning, data_origin, output_target, does_not_do = _STAGE_DETAIL_BLUEPRINT[stage_id]
        neutral_inputs = [item.get("input_presentation_zh") for item in related_steps]
        neutral_outputs = [item.get("output_presentation_zh") for item in related_steps]
        raw_steps = [
            {"step_id": item.get("id"), "input": item.get("input"), "output": item.get("output")}
            for item in related_steps
        ]

        if stage_id == "L5":
            if payment_recovery:
                initial_payment = input_data.get("payment_execution")
                neutral_inputs = [present_data_zh(initial_payment)] if initial_payment else []
                neutral_outputs = [
                    present_data_zh(
                        {
                            "initial_status": payment_recovery.get("initial_status"),
                            "retry_allowed": payment_recovery.get("retry_allowed"),
                        }
                    )
                ]
                raw_steps = [{"payment_execution": initial_payment}] if initial_payment else []
            else:
                neutral_inputs = [present_data_zh(input_data.get("payment_execution"))] if input_data.get("payment_execution") else []
                neutral_outputs = [present_data_zh({"payment_status": lifecycle.get("payment_status")})] if lifecycle else []
                raw_steps = [{"payment_execution": input_data.get("payment_execution")}] if input_data.get("payment_execution") else []
        elif stage_id == "L6":
            if payment_recovery:
                observation = input_data.get("payment_status_observation")
                neutral_inputs = [present_data_zh(observation)] if observation else []
                neutral_outputs = [
                    present_data_zh(
                        {
                            "observed_status": payment_recovery.get("observed_status"),
                            "effective_status": payment_recovery.get("effective_status"),
                            "recovery_status": payment_recovery.get("recovery_status"),
                            "retry_allowed": payment_recovery.get("retry_allowed"),
                            "next_action": payment_recovery.get("next_action"),
                        }
                    )
                ]
                raw_steps = [
                    {"payment_status_observation": observation},
                    {"payment_recovery": payment_recovery},
                ]
            else:
                neutral_inputs = [present_data_zh(input_data.get("payment_execution"))] if input_data.get("payment_execution") else []
                neutral_outputs = [present_data_zh({"payment_status": lifecycle.get("payment_status")})] if lifecycle else []
                raw_steps = [{"lifecycle": lifecycle}] if lifecycle else []
        elif stage_id == "L7":
            neutral_inputs = [present_data_zh(input_data.get("fulfillment"))] if input_data.get("fulfillment") else []
            neutral_outputs = [present_data_zh({"fulfillment_status": lifecycle.get("fulfillment_status")})] if lifecycle else []
            raw_steps = [{"fulfillment": input_data.get("fulfillment")}] if input_data.get("fulfillment") else []
        elif stage_id == "L8":
            remediation_input = {
                "lifecycle_reason_codes": lifecycle.get("reason_codes", []),
                "refund": input_data.get("refund"),
                "dispute": input_data.get("dispute"),
            }
            neutral_inputs = [present_data_zh(remediation_input)] if lifecycle else []
            neutral_outputs = [
                present_data_zh(
                    {
                        "remediation": lifecycle.get("remediation"),
                        "refund_status": lifecycle.get("refund_status"),
                        "dispute_status": lifecycle.get("dispute_status"),
                    }
                )
            ] if lifecycle else []
            raw_steps = [remediation_input, {"remediation": lifecycle.get("remediation")}] if lifecycle else []
        elif stage_id == "L9":
            neutral_inputs = [present_data_zh(lifecycle)] if lifecycle else neutral_inputs
            neutral_outputs = [present_data_zh({"task_status": lifecycle.get("task_status")})] if lifecycle else neutral_outputs
            if lifecycle:
                raw_steps.append({"lifecycle": lifecycle})

        protocol_mapping = _protocol_mapping_for_stage(protocol, stage_id)

        evidence = []
        if stage_id == "L4":
            evidence = list(record.get("actual", {}).get("evidence_presentations", []))
        elif payment_recovery and stage_id in {"L5", "L6"}:
            evidence = [present_evidence(item) for item in payment_recovery.get("evidence", [])]
        elif stage_id in {"L5", "L6", "L7", "L8", "L9"}:
            evidence = [present_evidence(item) for item in lifecycle.get("evidence", [])]

        stage_status = status_by_stage.get(stage_id, "未参与")
        stage_views.append(
            {
                **stage,
                "status": stage_status,
                "is_primary_fault_stage": stage_id == profile["primary_stage"],
                "is_detection_stage": stage_id == profile["detection_stage"],
                "trusted_execution": _trusted_execution_for_stage(stage_id, stage_status),
                "business": {
                    "meaning_zh": business_meaning,
                    "data_origin_zh": data_origin,
                    "output_target_zh": output_target,
                    "does_not_do_zh": does_not_do,
                    "detector_zh": (
                        profile["detector"]
                        if stage_id in {profile["primary_stage"], profile["detection_stage"]}
                        else "当前场景未在本环节触发异常检测。"
                    ),
                    "handler_zh": (
                        profile["handler"]
                        if stage_id in {profile["primary_stage"], profile["detection_stage"]}
                        else "当前场景未在本环节进入异常处理。"
                    ),
                    "recovery_zh": (
                        profile["recovery"]
                        if stage_id in {profile["primary_stage"], profile["detection_stage"]}
                        else "按当前生命周期状态继续到下一环节。"
                    ),
                },
                "neutral_data": {
                    "notice_zh": "来源：项目协议中立实验模型；不是某个协议的官方字段；用于统一 Validator / Manager / 测试。",
                    "inputs": neutral_inputs,
                    "outputs": neutral_outputs,
                },
                "protocol_mapping": protocol_mapping,
                "evidence": evidence,
                "raw_data": raw_steps,
            }
        )

    failure_code = profile["failure_type"]
    return {
        "framework_zh": "支付生命周期 Stage × 异常类型 Failure Type × 处理链 Responsibility / Recovery",
        "matrix": {
            "primary_stage": profile["primary_stage"],
            "detection_stage": profile["detection_stage"],
            "failure_type_code": failure_code,
            "failure_type_label": FAILURE_TYPES[failure_code],
            "stage_catalog": [
                {"id": item["id"], "name_zh": item["name_zh"]}
                for item in stages
            ],
            "failure_type_catalog": [
                {"code": code, "label_zh": label}
                for code, label in FAILURE_TYPES.items()
            ],
        },
        "stages": stage_views,
        "exception_card": {
            "stage": profile.get(
                "stage_display",
                f"{profile['primary_stage']} {next(item['name_zh'] for item in stages if item['id'] == profile['primary_stage'])}",
            ),
            "detection_stage": f"{profile['detection_stage']} {next(item['name_zh'] for item in stages if item['id'] == profile['detection_stage'])}",
            "failure_type": f"{failure_code} {FAILURE_TYPES[failure_code]}",
            "fault": profile["fault"],
            "source": profile["source"],
            "detector": profile["detector"],
            "basis": profile["basis"],
            "handler": profile["handler"],
            "handler_status": profile["handler_status"],
            "recovery": profile["recovery"],
            "final_impact": profile["final_impact"],
            "payment_status": lifecycle.get("payment_status") if lifecycle else None,
            "fulfillment_status": lifecycle.get("fulfillment_status") if lifecycle else None,
            "refund_status": lifecycle.get("refund_status") if lifecycle else None,
            "dispute_status": lifecycle.get("dispute_status") if lifecycle else None,
            "remediation_status": (lifecycle.get("remediation") or {}).get("status") if lifecycle else None,
            "task_status": lifecycle.get("task_status") if lifecycle else None,
            "initial_payment_status": payment_recovery.get("initial_status") if payment_recovery else None,
            "observed_payment_status": payment_recovery.get("observed_status") if payment_recovery else None,
            "effective_payment_status": payment_recovery.get("effective_status") if payment_recovery else None,
            "recovery_status": payment_recovery.get("recovery_status") if payment_recovery else None,
            "retry_allowed": payment_recovery.get("retry_allowed") if payment_recovery else None,
            "recovery_next_action": payment_recovery.get("next_action") if payment_recovery else None,
        },
        "neutral_field_notice_zh": "支付生命周期异常矩阵不直接展开技术字段；当前场景关键环节可按需展开协议中立字段、协议映射、判断证据和原始 JSON。",
    }


def _machine_stage_statuses(record: dict[str, Any], profile: dict[str, Any]) -> dict[str, str]:
    statuses = dict(profile.get("statuses") or {})
    actual = dict(record.get("actual") or {})
    input_data = dict(record.get("input") or {})
    reason_codes = {str(code) for code in actual.get("reason_codes", [])}
    decision = str(actual.get("decision") or "INDETERMINATE")
    statuses["L4"] = {
        "ALLOW": "已通过",
        "DENY": "异常",
        "CONFIRMATION_REQUIRED": "需要确认",
        "INDETERMINATE": "状态未知",
    }.get(decision, "状态未知")

    authorized_order_present = input_data.get("authorized_order") is not None
    final_order_present = input_data.get("final_order") is not None
    if not authorized_order_present and not final_order_present:
        statuses["L3"] = "未参与"
    elif not (authorized_order_present and final_order_present):
        statuses["L3"] = "状态未知"
    elif reason_codes & _ORDER_BINDING_INDETERMINATE_CODES:
        statuses["L3"] = "状态未知"
    elif actual.get("order_differences"):
        statuses["L3"] = "异常"
    else:
        statuses["L3"] = "已通过"

    payment_recovery = dict(record.get("payment_recovery") or {})
    if payment_recovery:
        initial_status = str(payment_recovery.get("initial_status") or "UNKNOWN")
        effective_status = str(payment_recovery.get("effective_status") or "UNKNOWN")
        statuses["L5"] = _execution_stage_status(initial_status)
        statuses["L6"] = _execution_stage_status(effective_status)

    lifecycle = dict(record.get("lifecycle") or {})
    if lifecycle:
        payment_status = str(lifecycle.get("payment_status") or "UNKNOWN")
        fulfillment_status = str(lifecycle.get("fulfillment_status") or "UNKNOWN")
        remediation_status = str((lifecycle.get("remediation") or {}).get("status") or "REQUIRED")
        task_status = str(lifecycle.get("task_status") or "UNKNOWN")
        statuses["L5"] = _execution_stage_status(payment_status)
        statuses["L6"] = _execution_stage_status(payment_status)
        statuses["L7"] = _execution_stage_status(fulfillment_status)
        statuses["L8"] = {
            "NOT_REQUIRED": "已通过",
            "REQUIRED": "等待处理",
            "IN_PROGRESS": "补救中",
            "RESOLVED": "完成",
        }.get(remediation_status, "状态未知")
        if task_status == "FAILED" and remediation_status == "RESOLVED":
            statuses["L9"] = "完成"
        else:
            statuses["L9"] = {
                "SUCCEEDED": "完成",
                "FAILED": "等待处理",
                "PENDING": "当前处理",
                "UNKNOWN": "状态未知",
            }.get(task_status, "状态未知")
    return statuses


def _execution_stage_status(status: str) -> str:
    return {
        "SUCCEEDED": "已通过",
        "FAILED": "异常",
        "PENDING": "当前处理",
        "UNKNOWN": "状态未知",
    }.get(status, "状态未知")


def build_unified_view(
    *,
    input_data: dict[str, Any],
    actual: dict[str, Any],
    status_presentation: dict[str, Any],
    lifecycle: dict[str, Any] | None = None,
    payment_recovery: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one fixed teaching view for every scenario without changing validator semantics."""

    mandate = dict(input_data.get("mandate") or {})
    request = dict(input_data.get("request") or {})
    seen_request_ids = list(input_data.get("seen_request_ids") or [])
    authorized_order = input_data.get("authorized_order")
    final_order = input_data.get("final_order")
    issue_codes = {str(code) for code in actual.get("reason_codes", [])}
    order_participates = authorized_order is not None or final_order is not None
    order_attention = bool(issue_codes & _ORDER_CONFIRMATION_CODES)
    order_uncertain = bool(issue_codes & _ORDER_BINDING_INDETERMINATE_CODES)

    duplicate_hit = request.get("request_id") in seen_request_ids
    amount_state = (
        "risk"
        if issue_codes & {"invalid_amount", "over_budget"}
        else "attention"
        if "confirmation_threshold_exceeded" in issue_codes
        else "normal"
    )
    order_state = "indeterminate" if order_uncertain else "attention" if order_attention else "normal"

    checks = _build_unified_checks(
        mandate=mandate,
        request=request,
        actual=actual,
        order_participates=order_participates,
    )
    primary_reason = (
        actual.get("reason_presentations", [{}])[0].get("title_zh", "未提供原因")
        if actual.get("reason_presentations")
        else "没有阻止原因"
    )
    lifecycle_fields = _lifecycle_result_fields(lifecycle, payment_recovery)
    lifecycle_evidence_source = lifecycle or payment_recovery or {}
    lifecycle_evidence = [
        present_evidence(item) for item in lifecycle_evidence_source.get("evidence", [])
    ]

    return {
        "mandate": {
            "title_zh": "1. 用户授权 Mandate",
            "fields": [
                _view_field("委托编号", mandate.get("mandate_id")),
                _view_field("用户编号", mandate.get("user_id")),
                _view_field("最大金额", mandate.get("max_amount"), "risk" if "over_budget" in issue_codes else "normal"),
                _view_field("免确认阈值", mandate.get("confirmation_above"), "attention" if "confirmation_threshold_exceeded" in issue_codes else "normal"),
                _view_field("允许商户", mandate.get("allowed_merchants"), "risk" if "merchant_out_of_scope" in issue_codes else "normal"),
                _view_field("允许品类", mandate.get("allowed_categories"), "risk" if issue_codes & {"category_out_of_scope", "order_item_category_out_of_scope"} else "normal"),
                _view_field("最大执行次数", mandate.get("max_count"), "risk" if "count_exceeded" in issue_codes else "normal"),
                _view_field("有效期", mandate.get("expires_at"), "risk" if "mandate_expired" in issue_codes else "normal"),
                _view_field("指定 Agent", mandate.get("expected_agent_id"), "risk" if "agent_identity_mismatch" in issue_codes else "normal"),
                _view_field("币种", mandate.get("currency"), "risk" if "currency_mismatch" in issue_codes else "normal"),
            ],
        },
        "agent": {
            "title_zh": "2. Agent 身份 / 意图",
            "fields": [
                _view_field("Agent 编号", request.get("agent_id"), "risk" if "agent_identity_mismatch" in issue_codes else "normal"),
                _view_field("当前准备执行的商户", request.get("merchant"), "risk" if "merchant_out_of_scope" in issue_codes else "normal"),
                _view_field("当前准备购买的品类", request.get("category"), "risk" if "category_out_of_scope" in issue_codes else "normal"),
                _view_field("计划金额", request.get("amount"), amount_state),
            ],
        },
        "request": {
            "title_zh": "3. 本次支付请求 Request",
            "fields": [
                _view_field("请求编号", request.get("request_id"), "risk" if duplicate_hit else "normal"),
                _view_field("金额", request.get("amount"), amount_state),
                _view_field("商户", request.get("merchant"), "risk" if "merchant_out_of_scope" in issue_codes else "normal"),
                _view_field("品类", request.get("category"), "risk" if "category_out_of_scope" in issue_codes else "normal"),
                _view_field("请求发生时间", request.get("occurred_at"), "risk" if "mandate_expired" in issue_codes else "normal"),
                _view_field("当前样品中的序号/次数值", request.get("sequence_count"), "risk" if "count_exceeded" in issue_codes else "normal"),
                _view_field("Agent 编号", request.get("agent_id"), "risk" if "agent_identity_mismatch" in issue_codes else "normal"),
                _view_field("币种", request.get("currency"), "risk" if "currency_mismatch" in issue_codes else "normal"),
            ],
        },
        "order": {
            "title_zh": "4. 订单快照 Order",
            "authorized_order": _order_slot(
                "用户确认的订单",
                authorized_order,
                order_participates=order_participates,
                state=order_state,
            ),
            "final_order": _order_slot(
                "商户最终订单",
                final_order,
                order_participates=order_participates,
                state=order_state,
            ),
            "differences": actual.get("order_differences", []),
        },
        "execution_state": {
            "title_zh": "5. 执行历史 / 运行状态",
            "fields": [
                _view_field("已处理请求编号", seen_request_ids, "risk" if duplicate_hit else "normal"),
                _view_field("当前样品提供的执行次数", request.get("sequence_count"), "risk" if "count_exceeded" in issue_codes else "normal"),
                _view_field("用户允许的最大次数", mandate.get("max_count"), "risk" if "count_exceeded" in issue_codes else "normal"),
                _view_field("是否命中重复请求", "是" if duplicate_hit else "否", "risk" if duplicate_hit else "normal"),
            ],
            "note_zh": "当前次数和已处理请求编号均由固定离线样品提供；尚未实现数据库、跨进程幂等记录或持久化次数累计。",
        },
        "checks": {
            "title_zh": "6. 统一规则检查",
            "items": checks,
        },
        "result": {
            "title_zh": "7. 最终判断 Result",
            "fields": [
                _view_field("场景验证状态", status_presentation.get("label_zh")),
                _view_field("付款前检查决策", actual.get("decision_presentation", {}).get("label_zh")),
                _view_field("付款前技术决策码", actual.get("decision")),
                _view_field("付款前主原因", primary_reason, "attention" if actual.get("reason_codes") else "normal"),
                _view_field("付款前下一步动作", actual.get("decision_presentation", {}).get("next_action_zh")),
                *lifecycle_fields,
            ],
            "evidence": actual.get("evidence_presentations", []),
            "lifecycle_evidence": lifecycle_evidence,
        },
    }


def _lifecycle_result_fields(
    lifecycle: dict[str, Any] | None,
    payment_recovery: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if lifecycle is None and payment_recovery is not None:
        initial_status = str(payment_recovery.get("initial_status") or "UNKNOWN")
        observed_status = str(payment_recovery.get("observed_status") or "UNKNOWN")
        effective_status = str(payment_recovery.get("effective_status") or "UNKNOWN")
        recovery_status = str(payment_recovery.get("recovery_status") or "UNRESOLVED")
        next_action = str(payment_recovery.get("next_action") or "")
        retry_allowed = bool(payment_recovery.get("retry_allowed"))
        return [
            _view_field(
                "初始支付执行状态",
                LIFECYCLE_STATUS_ZH.get(initial_status, initial_status),
                _lifecycle_state(initial_status),
            ),
            _view_field(
                "状态查询结果",
                LIFECYCLE_STATUS_ZH.get(observed_status, observed_status),
                _lifecycle_state(observed_status),
            ),
            _view_field(
                "恢复后可信支付状态",
                LIFECYCLE_STATUS_ZH.get(effective_status, effective_status),
                _lifecycle_state(effective_status),
            ),
            _view_field(
                "恢复状态",
                LIFECYCLE_STATUS_ZH.get(recovery_status, recovery_status),
                "attention" if recovery_status in {"UNRESOLVED", "BLOCKED"} else "normal",
            ),
            _view_field(
                "是否允许进入安全重试候选",
                "是" if retry_allowed else "否",
                "attention" if retry_allowed else "normal",
            ),
            _view_field(
                "恢复动作",
                PAYMENT_RECOVERY_ACTION_ZH.get(next_action, next_action or "—"),
                "attention" if recovery_status != "RECOVERED" else "normal",
            ),
            _view_field("履约状态", "未参与"),
            _view_field("用户任务状态", "未推断"),
        ]
    if lifecycle is None:
        return [
            _view_field("支付执行状态", "未模拟"),
            _view_field("履约状态", "未模拟"),
            _view_field("补救状态", "未模拟"),
            _view_field("用户任务状态", "未模拟"),
            _view_field("生命周期说明", "当前场景只验证付款前规则，没有提供支付后生命周期样品。"),
        ]

    payment_status = str(lifecycle.get("payment_status") or "UNKNOWN")
    fulfillment_status = str(lifecycle.get("fulfillment_status") or "UNKNOWN")
    remediation = dict(lifecycle.get("remediation") or {})
    remediation_status = str(remediation.get("status") or "REQUIRED")
    refund_status = lifecycle.get("refund_status")
    dispute_status = lifecycle.get("dispute_status")
    task_status = str(lifecycle.get("task_status") or "UNKNOWN")
    reasons = list(lifecycle.get("reason_codes") or [])
    next_action = str(remediation.get("next_action") or "")

    fields = [
        _view_field(
            "支付执行状态",
            LIFECYCLE_STATUS_ZH.get(payment_status, payment_status),
            _lifecycle_state(payment_status),
        ),
        _view_field(
            "履约状态",
            LIFECYCLE_STATUS_ZH.get(fulfillment_status, fulfillment_status),
            _lifecycle_state(fulfillment_status),
        ),
        _view_field(
            "补救状态",
            LIFECYCLE_STATUS_ZH.get(remediation_status, remediation_status),
            _lifecycle_state(remediation_status),
        ),
        _view_field(
            "用户任务状态",
            LIFECYCLE_STATUS_ZH.get(task_status, task_status),
            _lifecycle_state(task_status),
        ),
        _view_field(
            "生命周期原因码",
            ", ".join(reasons) if reasons else "没有生命周期异常",
            "risk" if reasons else "normal",
        ),
        _view_field(
            "补救建议",
            LIFECYCLE_ACTION_ZH.get(next_action, next_action or "—"),
            "attention" if remediation_status in {"REQUIRED", "IN_PROGRESS"} else "normal",
        ),
    ]
    if refund_status is not None:
        fields.insert(
            2,
            _view_field(
                "退款状态",
                LIFECYCLE_STATUS_ZH.get(str(refund_status), str(refund_status)),
                _lifecycle_state(str(refund_status)),
            ),
        )
    if dispute_status is not None:
        fields.insert(
            3 if refund_status is not None else 2,
            _view_field(
                "争议状态",
                LIFECYCLE_STATUS_ZH.get(str(dispute_status), str(dispute_status)),
                _lifecycle_state(str(dispute_status)),
            ),
        )
    return fields


def _lifecycle_state(status: str) -> str:
    if status == "FAILED":
        return "risk"
    if status in {"UNKNOWN", "PENDING", "REQUIRED", "IN_PROGRESS"}:
        return "attention"
    return "normal"


def _build_unified_checks(
    *,
    mandate: dict[str, Any],
    request: dict[str, Any],
    actual: dict[str, Any],
    order_participates: bool,
) -> list[dict[str, str]]:
    issue_codes = {str(code) for code in actual.get("reason_codes", [])}
    early_stop_check = _early_stop_check(issue_codes)

    def base_status(check_id: str, failure_codes: set[str]) -> str:
        if issue_codes & failure_codes:
            return "fail"
        if _was_skipped_after_early_stop(check_id, early_stop_check):
            return "indeterminate"
        return "pass"

    items = [
        _check_item(
            "required_fields",
            "必填字段完整性",
            base_status("required_fields", {"required_field_missing"}),
            _execution_aware_explanation(
                "required_fields",
                early_stop_check,
                "统一委托和请求的必填字段是否齐全。",
            ),
        ),
        _check_item(
            "currency_consistency",
            "币种一致",
            base_status("currency_consistency", {"currency_mismatch"}),
            _execution_aware_explanation(
                "currency_consistency",
                early_stop_check,
                "付款请求币种是否与用户授权币种一致。",
            ),
        ),
        _check_item(
            "duplicate_request",
            "请求是否重复",
            base_status("duplicate_request", {"duplicate_request"}),
            _execution_aware_explanation(
                "duplicate_request",
                early_stop_check,
                "当前请求编号是否已经出现在执行历史中。",
            ),
        ),
        _check_item(
            "amount_valid",
            "金额有效",
            base_status("amount_valid", {"invalid_amount"}),
            _execution_aware_explanation(
                "amount_valid",
                early_stop_check,
                "付款金额是否为有效的正数。",
            ),
        ),
        _check_item(
            "within_budget",
            "未超过最高预算",
            base_status("within_budget", {"over_budget"}),
            _execution_aware_explanation(
                "within_budget",
                early_stop_check,
                "付款金额是否位于用户授权的硬上限内。",
            ),
        ),
        _check_item(
            "merchant_scope",
            "商户在授权范围",
            base_status("merchant_scope", {"merchant_out_of_scope"}),
            _execution_aware_explanation(
                "merchant_scope",
                early_stop_check,
                "当前商户是否在用户允许范围内。",
            ),
        ),
        _check_item(
            "category_scope",
            "品类在授权范围",
            base_status(
                "category_scope",
                {"category_out_of_scope", "order_item_category_out_of_scope"},
            ),
            _execution_aware_explanation(
                "category_scope",
                early_stop_check,
                "请求或最终订单的商品品类是否位于用户允许范围内。",
            ),
        ),
        _check_item(
            "mandate_not_expired",
            "委托未过期",
            base_status("mandate_not_expired", {"mandate_expired"}),
            _execution_aware_explanation(
                "mandate_not_expired",
                early_stop_check,
                "请求发生时间是否仍在委托有效期内。",
            ),
        ),
        _check_item(
            "count_within_limit",
            "执行次数未超限",
            base_status("count_within_limit", {"count_exceeded"}),
            _execution_aware_explanation(
                "count_within_limit",
                early_stop_check,
                "固定样品中的当前次数是否超过用户允许的最大次数。",
            ),
        ),
        _check_item(
            "agent_identity",
            "Agent 身份匹配",
            (
                "not_applicable"
                if not mandate.get("expected_agent_id")
                else base_status("agent_identity", {"agent_identity_mismatch"})
            ),
            (
                "当前委托未指定 Agent，本项业务上不适用。"
                if not mandate.get("expected_agent_id")
                else _execution_aware_explanation(
                    "agent_identity",
                    early_stop_check,
                    "发起请求的 Agent 是否与委托指定 Agent 一致。",
                )
            ),
        ),
    ]

    if not order_participates:
        items.extend(
            [
                _check_item("order_binding", "订单绑定一致", "not_applicable", "本场景未使用订单快照，固定保留检查位置但不参与判断。"),
                _check_item("order_content_unchanged", "订单关键内容未变化", "not_applicable", "本场景未使用订单快照，固定保留检查位置但不参与判断。"),
            ]
        )
    elif early_stop_check is not None:
        items.extend(
            [
                _check_item("order_binding", "订单绑定一致", "indeterminate", "前置检查已失败，核心验证器未继续执行订单绑定检查。"),
                _check_item("order_content_unchanged", "订单关键内容未变化", "indeterminate", "前置检查已失败，核心验证器未继续比较订单关键内容。"),
            ]
        )
    elif issue_codes & _ORDER_BINDING_INDETERMINATE_CODES:
        items.extend(
            [
                _check_item("order_binding", "订单绑定一致", "indeterminate", "订单快照缺失、绑定冲突或对象不可可靠比较。"),
                _check_item("order_content_unchanged", "订单关键内容未变化", "indeterminate", "订单尚未可靠绑定，因此不能继续判断关键内容是否保持不变。"),
            ]
        )
    else:
        items.append(_check_item("order_binding", "订单绑定一致", "pass", "两个订单快照与当前委托、请求能够可靠对应。"))
        if "order_item_category_out_of_scope" in issue_codes:
            items.append(_check_item("order_content_unchanged", "订单关键内容未变化", "fail", "最终订单包含超出用户授权范围的商品品类。"))
        elif issue_codes & _ORDER_CONFIRMATION_CODES:
            items.append(_check_item("order_content_unchanged", "订单关键内容未变化", "confirmation_required", "订单关键内容或时效发生变化，需要用户重新确认。"))
        else:
            items.append(_check_item("order_content_unchanged", "订单关键内容未变化", "pass", "当前订单比较未发现需要阻止或重新确认的关键变化。"))

    if early_stop_check is not None and mandate.get("confirmation_above") is not None:
        threshold_status = "indeterminate"
        threshold_explanation = "前置检查已失败，核心验证器未继续执行免确认阈值检查。"
    elif "confirmation_threshold_exceeded" in issue_codes:
        threshold_status = "confirmation_required"
        threshold_explanation = "金额未超过硬上限，但超过免确认阈值，需要用户确认。"
    elif actual.get("decision") in {"DENY", "INDETERMINATE"}:
        threshold_status = "not_applicable"
        threshold_explanation = "当前请求已在更早的硬边界或完整性检查停止，本轮不进入免确认阈值放行判断。"
    elif mandate.get("confirmation_above") is None:
        threshold_status = "not_applicable"
        threshold_explanation = "当前委托未配置免确认阈值。"
    else:
        threshold_status = "pass"
        threshold_explanation = "当前金额没有触发免确认阈值；其他订单变化仍可能单独要求重新确认。"
    items.append(_check_item("confirmation_threshold", "是否超过免确认阈值", threshold_status, threshold_explanation))

    if tuple(item["check_id"] for item in items) != UNIFIED_CHECK_IDS:
        raise ValueError("unified check order changed unexpectedly")
    return items


def _early_stop_check(issue_codes: set[str]) -> str | None:
    """Return the validator check that caused an early INDETERMINATE return."""

    if "required_field_missing" in issue_codes:
        return "required_fields"
    if "currency_mismatch" in issue_codes:
        return "currency_consistency"
    return None


def _was_skipped_after_early_stop(check_id: str, early_stop_check: str | None) -> bool:
    if early_stop_check is None:
        return False
    return UNIFIED_CHECK_IDS.index(check_id) > UNIFIED_CHECK_IDS.index(early_stop_check)


def _execution_aware_explanation(
    check_id: str,
    early_stop_check: str | None,
    normal_explanation: str,
) -> str:
    if _was_skipped_after_early_stop(check_id, early_stop_check):
        return "前置检查已失败，核心验证器在到达本项前已经返回，因此本项尚未执行。"
    return normal_explanation

def _view_field(label_zh: str, value: Any, state: str = "normal") -> dict[str, Any]:
    return {"label_zh": label_zh, "value": value, "state": state}


def _order_slot(
    label_zh: str,
    value: Any,
    *,
    order_participates: bool,
    state: str,
) -> dict[str, Any]:
    if value is None and not order_participates:
        return {
            "label_zh": label_zh,
            "status_code": "not_applicable",
            "status_zh": CHECK_STATUS_ZH["not_applicable"],
            "message_zh": "未提供 / 本场景不适用",
            "value": None,
        }
    if value is None:
        return {
            "label_zh": label_zh,
            "status_code": "indeterminate",
            "status_zh": CHECK_STATUS_ZH["indeterminate"],
            "message_zh": "缺失 / 无法判断",
            "value": None,
        }
    status_code = "indeterminate" if state == "indeterminate" else "confirmation_required" if state == "attention" else "pass"
    return {
        "label_zh": label_zh,
        "status_code": status_code,
        "status_zh": CHECK_STATUS_ZH[status_code],
        "message_zh": "参与本场景订单检查",
        "value": present_data_zh(value),
    }


def _check_item(check_id: str, label_zh: str, status_code: str, explanation_zh: str) -> dict[str, str]:
    return {
        "check_id": check_id,
        "label_zh": label_zh,
        "status_code": status_code,
        "status_zh": CHECK_STATUS_ZH[status_code],
        "explanation_zh": explanation_zh,
    }


def missing_builtin_reason_mappings(records: list[dict[str, Any]]) -> set[str]:
    codes = {
        str(code)
        for record in records
        for code in record.get("actual", {}).get("reason_codes", [])
    }
    return codes - set(REASON_PRESENTATION_ZH)

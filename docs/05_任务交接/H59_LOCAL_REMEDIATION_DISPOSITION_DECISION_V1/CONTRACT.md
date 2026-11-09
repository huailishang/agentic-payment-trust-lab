# H59 本地补救结束状态与权限决策草案

> 2026-11-02 更新：Human已明确选择“先建立人工批准的对账处置入口（推荐）”。本决策草案RESOLVED_BEFORE_EXECUTION（执行前已解决），没有执行门禁或PASS裁决；见DECISION.md。下文保留选择前草案。下一实际执行包为H60_LOCAL_OPERATOR_RECONCILIATION_APPROVAL_V1，具体范围以H60冻结合同为准。

Task ID: H59_LOCAL_REMEDIATION_DISPOSITION_DECISION_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: evaluator_design
Contract state: DRAFT_CONTRACT
Dispatch mode: NONE
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-02-r96
Active bottleneck: B-17
Hypothesis: NONE

## 唯一待定问题

H58已PASS/NOT_APPLICABLE/STOP固定材料测量，证明付款引用/绑定快照等持久，但现存合同未定义付款成功无订单后的业务处置。下一本地研究以哪种结束状态为目标？

1. 人工批准的对账处置入口（建议）：先明确有权主体对特定交易、特定处置动作的批准与归责，收窄代理自主权限；还须明确该入口只记录批准还是允许执行订单变化。
2. 明确条件后自动补单：必须先定义谁授权自动化、允许条件、撤销/过期与库存/履约语义、付款和唯一订单绑定及失败处置；自动退款不随之授权。
3. 保留查询并切换其他瓶颈：当前业务断点保持未解决，由Evaluator比较下一候选的价值，不把停止称为已恢复。

这是产品/风险策略选择，不是既有H58只读合同下的实现自由。Human尚未选择，不得把建议、默认选中或等待时间视为批准。已用异步问题呈现三个选项，允许自由说明。

## 已收敛事实

- A–D本地代表性闭环、E仅本地、F当前。H57R正常工厂六旅程及真实退出后不重扣已接受并停止扩展。
- H58 L2/L3各6/6；38接受文件不变、24正式原始流hash/长度一致；M01付款1订单1库存4，M06付款1订单0库存5，原恢复仅QUERY/SUCCEEDED。
- 两库17表已有支付引用、快照、确认及授权摘要；生产完整授权、真实支付最终性、商户/客户责任尚未验证。缺这些生产事实不自动阻断所有本地研究。
- 当前不存在可声称安全自动补单/退款的合同和测试。不得把保存全部原token、私钥或生产信任根当已证明必要机制。
- 领域词汇见根CONTEXT.md。付款对账、补救批准、订单完成、付款补偿分别是不同事实和权限。

## 冻结前必须完成

收到选择后，Evaluator先澄清一个有界动作、批准主体、允许副作用与业务结束状态，再选择最小所需持久证据和机制，形成单一假设/主要变更、基线、允许文件、原子AC、固定Validation Plan（验证计划）、独立反例、预算和停止条件。不能把本草案当可执行合同。

若选择人工批准入口，建议先限制为本地合成主体和现有假PSP、原交易绑定、一次性批准与可回放处置记录；是否改变订单状态待Human选择和精确合同，不预先承诺。

若选择自动补单，先在本地仿真边界明确一次性受权订单完成，保持零新扣款；真实PSP/身份/部署另受授权约束。是否信任原持久批准记录或要求新批准由合同明确，不以“必须重验全部旧授权”作未经比较的前提。

## 当前允许与排除

本草案只允许Evaluator读取现有项目证据、澄清产品策略并编辑治理草案。没有Executor派发、没有实现预算、没有冻结AC或验证计划；不能填写虚假门禁/结果。

禁止商城/HTTP/ASGI启动、付款/退款/订单或库存变更、真实密钥或生产凭据、网络/API/模型/安装/外部联系、Git提交/推送/改历史；旧H58提交和证据只读。不得继续消耗H58剩余读取额度来替代决策。

## 外部要求与残余风险

external_requirement_impact: profile=PCAC-AGENTPAY。已检查开发指标映射。后续可能关联PCAC-07/09的授权与执行、PCAC-10撤销、PCAC-12存证、PCAC-18应急、PCAC-20评估，但本草案不升级任何成熟度，不声称实现或监管合规。

缺失的是Human对本地研究结束状态和权限模式的选择；不是要求提供真实客户、生产密钥、真实资金或PSP授权。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

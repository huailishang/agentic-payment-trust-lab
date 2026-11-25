# FluxA AgentCard：从用户授权到支付凭证

核验日期 2026-11-25。FluxA 及 AEP2 分类为 `REFERENCE_ONLY`。直接吸收的是约束与执行证据的评估方法。项目基线为地图 r148，H88 已独立签收，H89 已提交 L2、待独立 L3。外部材料的证据级别为官方公告、产品说明及接口文档。

## 官方资料支持什么

| 来源 | 可引用的事实 | 仍待验证 |
| --- | --- | --- |
| [Visa 新加坡亚太公告](https://www.visa.com.sg/about-visa/newsroom/press-releases/visa-expands-agentic-ready-to-help-scale-trusted-ai-commerce-in-asia-pacific.html)、[越南地区版](https://www.visa.com.vn/en_VN/about-visa/newsroom/press-releases/visa-expands-agentic-ready-to-help-scale-trusted-ai-commerce-in-asia-pacific.html) | 新加坡版标注 11 月 18 日，越南版标注 11 月 19 日。FluxA 列在与 Visa 探索发现、购物车、结账和支付的生态合作方中。 | 单个合作方的上线、运行结果或安全保证。 |
| [AgentCard 产品页](https://fluxapay.xyz/agent-card)、[AgentCard API](https://docs.fluxapay.xyz/agentcard/) | 产品页介绍关联 Visa 主卡的一次性支付凭证和钱包出资的可重复使用预付卡。公开 AgentCard API 概览明确覆盖预付卡，已签署委托约束签发或充值资金及费用。产品可用性取决于账户资格，部分需身份核验。 | 两类卡的实际交易约束和撤销保证须分别取证。预付卡后续每笔消费是否仍检查原委托，公开资料未给出可回放结果。 |
| [Mandates API](https://docs.fluxapay.xyz/wallet/http-mandates.html)、[x402 自动审批策略](https://docs.fluxapay.xyz/wallet/auto-policies.html) | 通用 Mandate 文档把总预算和有效期列为约束，把 `hostAllowlist` 和单笔上限列为参考字段。独立 x402 自动审批策略按主机与额度决定是否自动批准，超范围可转人工批准。 | 主机、商户、收款方是不同对象。必须在对应支付路径中验证执行结果，审批升级与支付拒绝分别记账。 |
| [Linked Cards（Beta）](https://docs.fluxapay.xyz/wallet/http-linked-cards.html)、[Managing Agents](https://docs.fluxapay.xyz/wallet/managing-agents.html) | 只读 Beta 接口列出卡委托的预算、已用、待处理、剩余金额和 `disabled` 状态。用户指南描述撤销 Agent 访问后阻止其发起新支付。 | 字段与状态证明可观察合同。预占原子性、撤销传播时间、已签发卡的实际失效和在途交易处理需独立证据。 |
| [AEP2 MVP](https://github.com/FluxA-Agent-Payment/APE2_MVP) | 项目展示一次性签署指令、收款方验证、受理回执与延迟结算的概念验证。上游标注仅为 PoC/MVP。 | 仅参考授权、受理、交付和最终结算的证据分层。 |

本次以公开文档为限。未取得可独立复验的 FluxA 沙箱资格、发卡或渠道拒付轨迹。

## 项目怎样参考

**现在吸收一条验收规则：为每个授权字段记录谁在何时强制执行，以及什么证据证明它生效。** 在后续合同中可采用“约束对象 → 执行责任方 → 生效时点 → 正向对照与拒绝结果 → 原始证据”的结构。用途描述、审批状态、交易准入和最终结算分开记录。授权合同、执行控制、支付渠道仍沿用现有模块边界，把这份结构用于明确责任。

**B-26 优先收口本地整份委托停止。** H88 已验证单次撤回在两个本地持久化入口的传播。H89 提交记录显示限定接收面只能登记单次撤回，整份事件未提交或受理。待 H89 独立 L3 和逐 AC 确认共同断点后，才冻结整份停止的能力包。一个主要变化可限定为：受信任控制方登记按用户、委托及版本绑定的停止事实，两个既有门禁读取同一事实。用 H89 一套合成输入验收未创建、已建未付和后登记动作在受理后均阻止新动作，另一委托仍正常，并保持 H88 隔离、原批准与已付恢复。保证限定为停止提交先于门禁读取。缺共同断点时重新比较优先级。

**随后把已签发凭证的使用时校验作为单独候选。** 选择一个合成本地执行凭证和一个资源，先证明原凭证在有效授权下可用，再证明同一凭证在委托停止后由消费方拒绝，另一委托仍可用，并保留可独立比对的授权版本、交易对象、凭证引用、撤回事务及消费结果。若未来有获准的渠道和独立证据，单列渠道拒绝与受理回执，以同一凭证的前后对照验证；支付渠道的受理不明确时结论为待证。本地用不透明合成引用表达凭证，证据只保留引用或摘要。Agent 身份凭证、用户授权和执行支付的凭证分别命名。

**累计预算和第二消费者各自排队。** 累计预算另做 PCAC-11 测量，重点是并发预占、失败释放、重试幂等和已结算事实对账，先明确货币单位及预算计入规则。付费数据 API 可作为第二消费者候选，待有具体需求及可独立验证的交付证据后比较；订阅、钱包充值和虚拟卡接入归入未来候选。优先比较新的本地撤销能力能否闭合零容忍风险，再决定是否投入额度一致性或渠道实验。

## 外部要求影响

`profile=PCAC-AGENTPAY`。PCAC-07/09/10/12 对应授权合同、执行时强制、撤销与证据链。PCAC-22 在本次只关联停止语义，PCAC-11 关联后续预算候选。现有成熟度沿用项目基线，本条目没有产品 Test 或新增成熟度。Evidence 为以上公开来源及 [H88 独立复核](../../../05_任务交接/H88_STORED_CONFIRMATION_WITHDRAWAL_V1/REVIEW.md)、[H89 执行提交](../../../05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/REPORT.md)。残余边界包括真实控制主体、凭证签发和消费绑定、渠道传播、在途与累计预算。

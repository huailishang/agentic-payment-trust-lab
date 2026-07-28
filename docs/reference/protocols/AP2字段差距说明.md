# AP2字段差距说明

## 1. 核验范围

- 核验日期：2026-07-11。
- 官方来源：`google-agentic-commerce/AP2`。
- 参考发布：v0.2.0（2026-04-28）。
- 参考对象：`OpenPaymentMandate`、`PaymentMandate`及AP2 Python 开发工具包（SDK）说明。
- 当前实现：只处理已经解码的JSON快照，不安装官方开发工具包（SDK），不生成或验证真实凭证。

官方仓库：

```text
https://github.com/google-agentic-commerce/AP2
```

本说明只记录当前实验适配范围。AP2主分支仍可能变化，后续正式接开发工具包（SDK）时必须固定Release或提交版本重新核验。

## 2. 当前映射

| AP2对象或字段 | 协议中立字段 | 当前用途 |
|---|---|---|
| `OpenPaymentMandate.constraints.payment.amount_range.max` | `IntentMandate.max_amount` | 硬金额上限 |
| `payment.amount_range.currency` | `IntentMandate.currency` | 金额币种 |
| `payment.allowed_payees.allowed` | `IntentMandate.allowed_merchants` | 可支付商户范围 |
| `payment.agent_recurrence.max_occurrences` | `IntentMandate.max_count` | 最大执行次数 |
| `payment.execution_date.not_after`或`exp` | `IntentMandate.expires_at` | 委托有效期 |
| `PaymentMandate.transaction_id` | `TransactionRequest.request_id` | 支付请求标识 |
| `PaymentMandate.payee` | `TransactionRequest.merchant` | 实际收款方 |
| `PaymentMandate.payment_amount` | `TransactionRequest.amount/currency` | 最终支付金额 |
| `PaymentMandate.execution_date` | `TransactionRequest.occurred_at` | 模拟执行时间 |

AP2金额使用货币最小单位，适配器（Adapter）转换为项目中的`Decimal`金额。例如`52000 CNY`转换为`520.00 CNY`。

## 3. 为什么还有`experiment_context`

当前协议中立样品还需要以下信息：

- 本地`mandate_id`和`user_id`。
- 商品业务品类。
- 智能体（Agent）编号。
- 免确认阈值。
- 当前执行次数。

这些字段与AP2对象可能来自不同层、不同凭证或本地业务上下文，不能假装全部由某一个AP2对象直接提供。因此首版快照增加`experiment_context`，只用于离线桥接，并明确不属于AP2正式Schema。

后续接入官方开发工具包（SDK）时，应逐项决定这些字段来自：

- AP2委托约束。
- 结账或订单协议。
- 智能体身份系统。
- 本地业务规则。
- 运行时状态账本。

## 4. 当前明确未验证

当前适配器会把下列内容作为缺口返回，而不是假装已经支持：

- `cnf`密钥绑定。
- SD-JWT及多级委托链签名验证。
- audience、nonce和重放绑定。
- Payment Instrument。
- PISP。
- `transaction_id`与结账 JWT哈希绑定。
- 风险数据。
- Payment Receipt和结账 Receipt。
- 商户别名、聚合商和实际收款方归一化。
- 商品品类与订单明细的可信来源。

因此，当前结果只能证明：

> 一份AP2风格的已解码字段快照可以被转换为本项目的协议中立模型，并复用同一套确定性规则和场景测试。

当前结果不能证明：

- AP2签名有效。
- 委托链可信。
- 真实支付获得授权。
- 商户、银行、卡组织或支付机构可以直接接入。
- 本项目已经通过AP2一致性测试。

## 5. 什么时候安装官方开发工具包（SDK）

当前I1不需要安装AP2 开发工具包（SDK）。只有出现以下明确问题时才进入开发工具包（SDK）实验：

1. 验证Open/Closed Mandate的正式Pydantic类型。
2. 验证SD-JWT委托链创建、展示和校验。
3. 验证nonce、audience及上下文绑定。
4. 验证Mandate与Receipt之间的引用关系。
5. 运行一个不接真实资金的官方固定场景。

届时必须：

- 固定AP2 Release或提交哈希，不能长期直接依赖`main`。
- 单独记录许可证、Python版本和传递依赖。
- 只使用模拟密钥和模拟身份。
- 不配置真实卡、真实商户、生产接口（API）或真实资金。
- 保持现有协议中立场景全部回归通过。

## 6. 与其他协议的区别

| 协议 | 主要回答的问题 | 更适合的场景 | 本项目顺序 |
|---|---|---|---|
| AP2 | 智能体依据什么委托发起支付，金额、收款方、次数、有效期和证据如何表达 | 用户授权边界、支付授权和可信证据 | 第一协议样本 |
| ACP | 买家、智能体、商户和支付提供方如何完成结账与购买 | 结账、购物车、订单和商户接入 | 后续订单层对照 |
| UCP | 不同平台、商户和服务商如何用统一能力完成发现、结账、订单与履约 | 跨平台完整商业能力互通 | 核心模型稳定后再接 |
| x402 | HTTP/API资源如何在请求过程中表达和完成付费 | 接口（API）、内容、机器微支付 | 独立支线 |

这四类协议不是简单的替代关系，而是关注层次不同。AP2偏支付授权与委托；ACP偏一次购买如何完成；UCP覆盖更广的商业能力；x402偏HTTP资源付费。

## 7. 为什么先选择AP2

第一轮实验要验证的是：

- 智能体是否超过用户授权金额。
- 是否支付给允许的商户。
- 委托是否过期或被重复使用。
- 哪些变化需要用户再次确认。
- 最终判断能否留下可解释证据。

这些问题与AP2的Mandate和Payment Mandate语义最接近，而且范围比完整结账、订单和履约协议更窄。因此先用AP2可以把“用户授权与支付请求”这一层讲清楚，再进入ACP或UCP的商品、购物车、订单和售后层。

选择AP2不代表认定它最终会成为唯一标准，也不代表项目已经接入真实支付。当前选择只是实验顺序：先解决最核心、最容易失控的授权问题，再扩大到完整商业流程。

## 8. 当前交互式教学实现

S08使用一份AP2 v0.2.0风格的已解码教学快照。运行时实际经过：

```text
AP2教学快照
-> AP2 适配器
-> 协议中立Mandate与TransactionRequest
-> 确定性验证器
-> 需要确认（CONFIRMATION_REQUIRED）与字段证据
```

离线HTML页面支持逐步播放、查看每一步入参和出参、切换AP2原始数据与通用模型，并显示当前未验证的签名、委托链和收据缺口。

## 9. 当前结论

AP2适合作为第一协议样本，因为它能补充金额范围、允许收款方、执行次数、有效期、委托链和收据绑定等问题。但AP2不应成为项目核心模型；它只是第一个输入适配器和差距来源。

# H46 AgentDojo 银行转账到完整支付控制入口的语义映射

Task ID: H46_AGENTDOJO_OFFLINE_EVIDENCE_CHAIN_V1
Product seam: `execute_with_payment_binding_gate`，而非 WebShop 商业订单 `gate_webshop_buy_now`。本轮只有缺证据诊断，不进行完整控制对照。

| 产品必须处理的语义 | 上游 Banking/source 状态 | 直接接入评定与证据要求 |
| --- | --- | --- |
| recipient / payee（收款人） | `send_money.recipient`、Transaction.recipient | PARTIAL；IBAN 是未验证的字符串，缺可信收款人身份绑定 |
| amount（金额） | Transaction.amount: float | PARTIAL；金额单位/精度和上下限可观测，但源工具非 Decimal、无支付请求绑定证据 |
| currency（币种） | send_money **没有** currency 参数 | UNSUPPORTED；GBP 只是合成实验 profile，不能冒充源协议事实 |
| order / transaction identity（订单与原交易关系） | Transaction.id、sender/recipient/amount | UNSUPPORTED；没有订单、订单版本、交易请求 order_ref、authority_ref 等稳定关系 |
| merchant / category（商户与类别） | 未提供 | UNSUPPORTED；friend IBAN 不能编造成 merchant/category |
| identity（执行者身份） | 工具调用没有 Agent credential/instance/agent_id | UNSUPPORTED；无法满足 P3 身份绑定 |
| user confirmation（用户确认） | Task PROMPT 与 Gold，可见自然语言 | UNSUPPORTED；没有独立确认时间、授权订单快照、confirmation_record |
| idempotency / governed_action（幂等/受控动作） | Transaction.id 是追加记录 ID | UNSUPPORTED；不是 request idempotency key，也不是完整 GovernedPaymentAction |
| context / trusted source（上下文可信来源） | 工具返回交易列表、源码声明 | UNSUPPORTED；不能证明可信来源、策略校验或注入内容未升权 |
| callback / execution fact（执行副作用） | send_money 只 append 本地 Transaction | PARTIAL for synthetic tool mutation / UNSUPPORTED for real payment settlement；不得当作银行付款凭证 |
| balance/finality（余额与资金最终性） | send_money 不扣减 balance，亦无外部回执 | UNSUPPORTED；仅离线状态 append |

本轮 `EVALUATOR_CHECK.py:142-154` 直接调用现有 `execute_with_payment_binding_gate(Decision.ALLOW, None, None, None, None, callback)`，仅用于隔离 P2 缺证据分支；这个刻意缺少 mandate、order、request、execution 的输入不是“有效用户授权”，当然不能当作完整正常场景的门禁结果。两次实际观测为 `INDETERMINATE`, `p2:binding_missing`, `callback_count=0`, `executed=false`。

结论：源工具可做离线行为证据，但完整支付控制的必要字段/可信性没有对应来源。不得为通过测试虚构订单、商户、Confirmation、币种或 trusted source 标签；若要建设 protocol-neutral adapter，须由后续 Evaluator 单独冻结映射语义及新输入来源验收标准。

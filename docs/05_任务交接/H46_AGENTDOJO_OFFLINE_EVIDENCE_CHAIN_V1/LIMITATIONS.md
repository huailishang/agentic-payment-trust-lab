# H46 范围、许可证、数据与安全限制

Task ID: H46_AGENTDOJO_OFFLINE_EVIDENCE_CHAIN_V1
Candidate state: UNREVIEWED_CANDIDATE，不是已验证第三方 benchmark 提交，更不是生产认证。

1. 上游 AgentDojo v0.1.35 固定 commit 的 MIT 原文件有原作者版权声明；本包与候选包完整保留许可。只执行 AST 提取的 five banking definitions、UserTask3.utility、InjectionTask5.security；不安装完整 agentdojo、不运行 SDK 注册/外部环境。
2. 合成账户、friend/attacker 标识和 4.00/20.00 脚本由 FIXTURE 约束，不来自真实银行账户、真实付款或模型生成轨迹。上游 attack_success 为 scorer 对状态判定，不是攻击模型成功率。
3. 工具 `send_money` 仅追加 Transaction，没有扣余额、入账签收、退款、最终清算或银行对账；币种 GBP 只是 derived profile，源接口并未提供 currency。
4. 用户授权信封是独立合成条件；上游 Gold、工具输出和非可信网页/上下文不能反向变成用户允许的收款人、付款次数或付款金额。
5. 产品 `execute_with_payment_binding_gate` 的两次调用有意只给 `Decision.ALLOW`、缺 mandate/order/request/execution；其 INDETERMINATE 只能诊断 P2 缺证据，不能当成 full gate causal comparison 或漏洞修复。
6. 候选 bundle 校验器只依赖已存在的 Python/pydantic 与打包的源码/JSON/许可，对工具记录真正复算；产品 probe 两条只校验完整性与结论标签，并不在干净拷贝中重跑产品。这必须写进交接。
7. 不包含真实 secret、日志中本机绝对路径、聊天内容、模型推理链、外部网络调用、支付宝 Sandbox、生产身份、赛事提交或真实资金。已有 dirty worktree 保留，不 commit/push。
8. 仅一个银行任务、一项攻击判定、四个脚本状态和两次重复；不构成跨任务泛化、真实 Agent 注入防御能力、PCAC 监管合规、最终第三方测评通过或 F 阶段 B-06 外部实证闭合。

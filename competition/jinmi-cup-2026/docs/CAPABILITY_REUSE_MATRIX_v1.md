# 金密杯 2026 能力复用矩阵 v1

> 目标：从主项目选择最适合“金融智能体能力增强与安全验证”的能力，不为了赛事重新定义项目。

## 1. 选择原则

每项能力分成四类：

- `SHOWCASE`：已经有代表性证据，适合作为参赛作品核心展示；
- `STRENGTHEN`：已有基础，但赛题若要求可做有界补强；
- `ADAPTER`：依赖外部密码/金融平台，只做接入边界；
- `OUT_OF_SCOPE`：不为比赛建设。

## 2. 主能力矩阵

| 能力族 | 当前资产 | 金密杯定位 | 说明 |
|---|---|---|---|
| Evaluation Harness | 固定场景、项目影响基线、独立复核 | SHOWCASE | 这是作品可信度的底座，不只是“跑几个测试” |
| Delegated Authorization | P1、Mandate、Confirmation Binding | SHOWCASE | 证明 Agent 只能在授权边界内行动 |
| Transaction Binding | Order→Request→Payment 连续绑定 | SHOWCASE | 对抗金额、商户、订单、支付对象偷换 |
| Identity Binding / Assurance | Agent/Executor identity，B-15 本地闭环 | SHOWCASE + STRENGTHEN | 必须明确本地/外部证据边界 |
| Credential Possession | X.509-SVID bounded PoP 等 | STRENGTHEN | 可作为“声明身份≠持有凭证”的安全点 |
| Signed Instruction | ACP/HMAC + AP2/ES256 第二消费者 | SHOWCASE | 适合展示跨协议签署指令验证 |
| Context / Tool Integrity | P4、Trust Source、Fact Lineage | SHOWCASE | 金融 Agent 的差异化攻击面 |
| Prompt/Context Tampering | Attack Overlay | SHOWCASE | 强调“低可信事实不能覆盖确认事实” |
| Runtime Gate | ALLOW/DENY/CONFIRM/INDETERMINATE | SHOWCASE | 所有副作用前统一安全接缝 |
| Idempotency / Replay | duplicate guard / replay protection | SHOWCASE | 重放不能导致重复支付/动作 |
| Payment Unknown / Recovery | Query / Finality / Conflict | SHOWCASE | 展示高风险交易的异常控制 |
| Fulfillment / Remediation | failure/refund/dispute/original tx binding | SHOWCASE | 安全不止发生在付款前 |
| Evidence / Trace | Product Trace、Responsibility、Player | SHOWCASE | 证明“为什么允许/拒绝、谁负责、发生了什么” |
| Data Minimization | PayBench D1 等字段级覆盖 | STRENGTHEN | 不能外推完整隐私治理 |
| Agent Risk Tier | PCAC 明显缺口 | STRENGTHEN / measurement-first | 先判断赛题是否真要求，不直接造复杂评分 |
| Authorization Revocation | PCAC 明显缺口 | STRENGTHEN / measurement-first | 可能是值得补的协议中立能力 |
| Continuous Monitoring | 当前不足 | STRENGTHEN / measurement-first | 防止为了“看起来像安全平台”造假监控 |
| AML/CFT/Fraud | 外部 Risk Gate 才合理 | ADAPTER | 不自建银行级反洗钱/反诈系统 |
| Production PKI / Key Governance | 未完整验证 | ADAPTER | 不声称生产级覆盖 |
| Blockchain / Token / DeFi | 非项目主线 | OUT_OF_SCOPE | 除非官方赛题明确且有必要性证据 |
| 通用 Agent Runtime | 非项目定位 | OUT_OF_SCOPE | 不扩张项目边界 |

## 3. 最值得形成作品主线的五个问题

### Q1：Agent 到底有没有权利做这件事？

复用：

```text
User Intent
 -> Delegated Authority
 -> Confirmation
 -> Runtime Gate
```

攻击：

- 超预算；
- 越商户/类别；
- 授权过期；
- 旧确认复用；
- 未确认直接执行。

### Q2：执行时还是原来那笔交易吗？

复用：

```text
Authority
 -> Order
 -> Payment Request
 -> Payment Execution
```

攻击：

- 金额变化；
- 商户变化；
- order/request/payment 错绑；
- callback 错绑。

### Q3：发起动作的真是那个 Agent / Executor 吗？

复用：

- identity binding；
- signed instruction；
- credential possession；
- freshness/replay。

这里必须区分：

```text
DECLARED
!= BOUND
!= VERIFIED
```

### Q4：网页、LLM、Tool 能不能偷偷改支付事实？

复用：

- Context Policy；
- Trust Source；
- Fact Lineage；
- Attack Overlay。

原则：

> 不可信上下文只能作为候选信息，不能静默升级成已确认授权事实。

### Q5：出了异常以后还能安全结束吗？

复用：

- UNKNOWN → Query；
- status conflict；
- duplicate preflight；
- fulfillment failure；
- refund/dispute；
- Authoritative Trace。

这能避免作品只展示“付款前拦攻击”，而忽略金融系统更难的支付后异常。

## 4. 和 PCAC 外部基线的关系

优先映射以下能力族：

- PCAC-03 KYA；
- PCAC-05 Agent 身份全链路传递；
- PCAC-07 Delegated Authorization；
- PCAC-08 用户身份/支付意愿；
- PCAC-09 防越权/完整性；
- PCAC-10 Authorization Revocation；
- PCAC-11 资金限额与护栏；
- PCAC-12 Evidence Chain；
- PCAC-13 Model Risk；
- PCAC-14 注入/篡改/越权；
- PCAC-18 应急处置；
- PCAC-20 上线前评估/回退。

这是一套开发/验证参照，不表述成监管合规结论。

## 5. 当前最大风险

对金密杯而言，我们当前最大的风险不是“能力太少”，而是：

1. 已有能力很多但故事可能过散；
2. 测试数量很多，但如果不能压成 3-5 个高价值安全命题，会显得像测试集堆积；
3. 本地密码学/身份能力如果包装过头，容易把 bounded evidence 写成 production-grade；
4. 为赛题临时新增过多安全模块，会降低项目本身的一致性。

因此后续重点应是 **能力收敛 + 对抗证明 + 可复核证据**，不是继续扩模块数量。

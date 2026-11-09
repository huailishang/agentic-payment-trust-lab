# 金密杯 2026 最小执行路线 v1

> 核心策略：先用现有项目形成一条可讲清、可攻击、可复核的金融 Agent 安全主线；只有赛题官方评分要求暴露真实缺口时才补能力。

## 1. Phase 0：赛事要求核验

在开发任何赛事专属代码前，先固定官方：

- 赛题全文与版本；
- 报名/提交时间；
- 评分维度；
- 提交物格式；
- 是否要求开源；
- 是否要求指定密码算法/平台/接口；
- Demo 环境和现场答辩要求；
- 是否允许复用既有项目。

输出：

`OFFICIAL_REQUIREMENTS_BASELINE.md`

如果官方要求与我们当前理解冲突，以官方文件为准，但仍不能未经评估直接改主项目。

## 2. Phase 1：从“很多能力”收敛为一个作品故事

建议主故事：

> **一个金融 Agent 在执行高风险交易前、中、后，所有关键副作用都经过可验证的身份、授权、交易绑定和运行时治理；受到越权、重放、上下文污染或支付异常攻击时能够 fail closed，并留下可回放证据。**

压成五个安全问题：

```text
1. Who?       谁在执行
2. Authority? 有没有权利
3. What?      是否还是原交易
4. Context?   输入事实是否可信
5. Outcome?   支付/履约/恢复是否安全结束
```

## 3. Phase 2：固定攻击矩阵

优先从已有资产选代表攻击，不随机扩数量：

### Identity / Credential

- agent identity mismatch；
- executor mismatch；
- stale/replayed signed instruction；
- credential possession failure。

### Authorization

- over budget；
- merchant/category out of scope；
- expired mandate；
- stale confirmation；
- revoked authorization（若 Phase 0/measurement 证明需要补）。

### Transaction Integrity

- order amount changed；
- request/order/payment mismatch；
- wrong original transaction；
- duplicated payment request。

### Context / Tool Integrity

- untrusted page changes amount；
- tool result overrides confirmed fact；
- context rewrite tries to bypass policy；
- provenance missing/conflicting。

### Lifecycle / Recovery

- provider UNKNOWN；
- status conflict；
- payment success + fulfillment failure；
- replay after successful payment；
- refund/dispute wrong binding。

## 4. Phase 3：统一作品 Harness

作品的价值不只是“拦住攻击”，还要能机械证明：

```text
Attack Input
 -> Canonical Facts
 -> Trust Decision
 -> Controlled Side Effect
 -> Lifecycle Result
 -> Evidence / Trace
 -> Independent Checker
```

每个代表 Case 至少输出：

- expected decision；
- actual decision；
- reason code；
- side-effect count；
- binding evidence；
- identity/auth evidence；
- lifecycle result；
- authoritative trace validity；
- replay result。

## 5. Phase 4：只补一个真正高价值缺口

如果官方评分确实要求我们增加能力，优先从这些 measurement-first 候选里选 **一个**：

1. Authorization Revocation；
2. Agent Risk Tier；
3. Continuous Monitoring Facts；
4. stronger credential/key evidence；
5. Cross-Agent high-risk transaction。

选择条件：

- 与赛题评分直接相关；
- 当前确有失败证据；
- 是协议中立安全能力；
- 可以在 bounded scope 内完成；
- 不破坏主项目当前 F 阶段。

如果只是展示层需求，留在比赛目录。

## 6. Phase 5：提交包装

比赛目录承担：

- 赛题说明；
- 架构图；
- 威胁模型；
- Attack Matrix；
- Demo 场景；
- benchmark / regression result；
- Evidence Trace 示例；
- 视频/答辩脚本；
- submission 文档。

主项目只作为“能力来源”。

## 7. 与 Payathon 的协同

最理想的复用方式：

```text
金密杯：
证明 Trust Core 在攻击条件下成立
             ↓
同一套能力
             ↓
Payathon：
证明 Trust Core 在 Agent Pay / Machine Pay 的真实支付链上成立
```

两边共享测试资产和可信不变量，但各自维护自己的：

- problem statement；
- demo profile；
- external adapter；
- scoring mapping；
- submission assets。

## 8. 回写主项目 Gate

任何金密杯专属发现只有满足以下全部条件才回写：

```text
not competition-specific
AND not provider-specific
AND affects protocol-neutral trust invariant
AND reproducible failure exists
AND second consumer / independent evidence exists
AND evaluator freezes bounded repair
```

否则保留在 `competition/jinmi-cup-2026/`。

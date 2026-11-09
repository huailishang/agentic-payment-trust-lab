# Payathon 2026 验证工作区

> 状态：规划与差距分析阶段
> 日期：2026-09-28
> 目标：复用 `agentic-payment-trust-lab` 已有能力，形成两个独立参赛产品验证面；不为了比赛重写主项目。

## 1. 定位

本目录是 **比赛适配 / 产品包装 / 外部验证工作区**，不是新的主架构，也不是第二套 Trust Core。

主仓继续保持：

```text
Canonical Facts
  -> Trust Core
  -> Runtime Gate
  -> Payment Lifecycle / Recovery
  -> Authoritative Trace / Replay
```

Payathon 只在外围增加：

```text
官方协议 / Provider
  -> Adapter
  -> Canonical Facts
  -> 现有 Trust Core
  -> 产品化 Demo / Evidence
```

## 2. 两条路线

### Route A：Agent Pay（主作品）

问题定义：

> 当 Agent 代表用户购买商品或服务时，怎样证明每一次下单、支付和履约都仍然忠实于用户原始意图与授权？

目标链路：

```text
User Intent
  -> ISR / Delegated Authority
  -> IAC / Authorization
  -> Offer / Cart / Order
  -> Runtime Trust Gate
  -> Agent Pay
  -> Payment Result
  -> Fulfillment
  -> Authoritative Trace / Replay
```

第一阶段以 **SPECIFIED / 定向委托** 为主，不直接把自主度最高的 BOUNDED/L3 作为首个 Demo。

### Route B：Machine Pay（子作品）

问题定义：

> 当 Agent 为 API / MCP / Skill 自动付费时，怎样保证“付的是正确资源、正确价格、只付一次、付款后真的交付”？

目标链路：

```text
Agent requests resource
  -> HTTP 402 + Payment-Needed
  -> Trust Gate / Budget Check
  -> Payment
  -> Payment-Proof
  -> Provider Verify
  -> Resource Delivery
  -> Fulfillment Confirm
  -> Trace / Replay
```

这条线复用现有 x402 / Machine Resource Payment / Payment Lifecycle 能力，不另造一套支付状态机。

## 3. 共享能力

两个作品共同复用主项目的：

- Delegated Authority / Confirmation Binding；
- Order / Request / Payment 连续 Binding；
- Agent / Executor Identity；
- Context / Tool Integrity；
- Runtime Authorization Gate；
- Idempotency / Replay；
- UNKNOWN / Finality / Recovery；
- Fulfillment / Refund / Dispute Evidence；
- Product Authoritative Trace；
- Consumer / Read Model / Player；
- AP2、x402、WebShop 已有适配和评测资产。

## 4. 强制边界

1. **不修改主项目业务规则来迎合比赛协议。**
2. ACT、Agent Pay、A402 都先通过 Adapter 映射为现有 Canonical Facts。
3. 若协议语义无法忠实映射，记录为 capability gap，不在 Adapter 中补猜。
4. 比赛专属 UI、Demo、样例、包装代码放在本目录。
5. 主项目 `src/` 只有在“同一缺口已证明是协议中立、且对主项目本身有价值”时才允许改。
6. 比赛进度不得覆盖 `CURRENT.md` / `PROJECT_BOTTLENECK_MAP.md` 的主项目优先级。
7. 不因 ACT 可信存证包含链上锚定，就把 Blockchain 变成主项目默认依赖。
8. 不把 Sandbox / Demo PASS 表述成生产支付、监管合规或完整 ACT Conformance。

## 5. 当前文档

- [ACT / A402 与现有能力差距分析 v1](docs/ACT_A402_GAP_ANALYSIS_v1.md)
- [最小执行路线 v1](docs/MINIMUM_EXECUTION_ROUTE_v1.md)
- [Agent Pay 主作品](agent-pay/README.md)
- [Machine Pay 子作品](machine-pay/README.md)

## 6. 官方基线

截至 2026-09-28，本目录按以下公开资料校准：

- Payathon 2026：<https://aipay.alipay.com/community/events/payathon-2026>
- 支付宝 AI 付概览：<https://aipay.alipay.com/docs/overview.html>
- Machine Pay 接入指南：<https://aipay.alipay.com/docs/ai-receive/MACHINE_PAY.html>
- ACT Protocol：<https://www.act-protocol.com/>
- ACT 委托授权域（ADD）：<https://www.act-protocol.com/documentation/delegation>
- ACT 商业交互域（CID）：<https://www.act-protocol.com/documentation/commerce>
- ACT 支付服务域（PSD）：<https://www.act-protocol.com/documentation/payment>
- ACT 可信存证：<https://www.act-protocol.com/documentation/trust/attestation>

外部协议会继续演进；实施前重新核对官方版本和实际开放能力。

# Payathon 2026 最小执行路线 v1

> 原则：先把现有能力投射到比赛场景，再补真正缺口；不以“做完整协议”为目标。

## 1. Phase 0：冻结边界，不改主项目

输出：

- 两个作品的问题定义；
- ACT/A402 gap matrix；
- 可复用能力清单；
- 禁止改动清单；
- 官方资料版本/日期；
- Demo success criteria。

本文件与 `ACT_A402_GAP_ANALYSIS_v1.md` 即为 Phase 0 第一版输出。

## 2. Phase 1：Agent Pay 主作品最小闭环

首个场景固定成 **SPECIFIED / 定向委托**，例如：

> “购买一个明确商品/数字服务，总价不得超过 X 元，只允许指定商户/类别，授权在 T 时间前有效。”

最小闭环：

```text
User Intent
 -> ACT-like ISR
 -> IAC/SPECIFIED adapter
 -> Canonical Authority Facts
 -> Offer/Order
 -> Checkout Confirmation
 -> Runtime Gate
 -> Alipay Agent Pay/Sandbox
 -> Provider Result/Proof
 -> Fulfillment
 -> Authoritative Trace
```

验收重点：

1. 授权对象版本固定；
2. Agent/merchant/order/amount/payment 连续绑定；
3. Order 改价或换商户后原确认失效；
4. 过期/撤销授权 fail closed；
5. UNKNOWN 不自动二次付款；
6. 支付成功与履约成功分离；
7. Trace 能从 intent 回放到 fulfillment。

不先做：

- 多商户自主选择；
- 全自动 L3/BOUNDED；
- Agent 专属子账户；
- ACT Trust Chain；
- 复杂信用评分。

## 3. Phase 2：Machine Pay 子作品最小闭环

首个场景固定成一个付费 API / MCP Tool。

```text
GET/POST resource
 -> 402 Payment Required
 -> Payment-Needed
 -> decode + canonical bill facts
 -> Trust Gate
 -> payment
 -> Payment-Proof
 -> alipay.aipay.agent.payment.verify
 -> amount/order/resource/replay checks
 -> resource delivery
 -> alipay.aipay.agent.fulfillment.confirm
 -> Trace
```

至少准备以下负例：

- amount mismatch；
- resource_id mismatch；
- out_trade_no mismatch；
- trade_no duplicate fulfillment；
- expired Payment-Needed；
- Payment-Proof invalid；
- provider result UNKNOWN；
- payment success but fulfillment failure。

这些负例优先复用现有 P2/P5/P6/Payment Lifecycle/Trace 能力。

## 4. Phase 3：共享内核证明

比赛真正有差异化的不是“两套 Demo 都能付钱”，而是证明：

> Agent Pay 与 Machine Pay 使用不同外部协议，但共享同一套 Trust Invariants。

冻结同一组不变量：

```text
Identity
Authority
Transaction/Resource Binding
Budget
Confirmation
Idempotency/Replay
Finality/Recovery
Fulfillment
Evidence
```

对两个作品分别产生：

```text
Protocol Facts
 -> Adapter
 -> Canonical Facts
 -> Trust Decision
```

然后比较 Canonical Facts / Decision，避免协议私有字段污染核心。

## 5. Phase 4：再决定是否做 BOUNDED/L3

只有 Route A 的 SPECIFIED 与 Route B 的 A402 都稳定后，再测：

> “给 Agent 一个总预算，让它自主购买若干 API/服务完成任务。”

这时 Agent Pay 与 Machine Pay 才真正汇合：

```text
One BOUNDED IAC
  -> Agent selects merchant/service A
  -> Machine Pay purchase #1
  -> Agent selects service B
  -> Machine Pay purchase #2
  -> optional final merchant purchase
  -> cumulative budget / merchant / category / expiry enforcement
  -> one end-to-end trace
```

这会成为后续高级 Demo，而不是首个施工目标。

## 6. 回写主项目 Gate

比赛发现的问题只有在以下条件同时成立时才进入主项目：

```text
cross-protocol repeat
AND security/business invariant
AND current Trust Core cannot express it
AND measurable failure exists
AND bounded repair can be evaluated
```

否则全部保持在 `competition/payathon-2026/`。

## 7. 下一执行包建议

下一包应是 measurement-first，而不是直接写 Agent Pay 大量代码：

**PAYATHON-P0-ACT-ALIPAY-CONTRACT-MAPPING-V1**

范围：

- 固定 ACT ADD/CID/PSD + Machine Pay 官方资料；
- 建立字段/对象 → Canonical Facts matrix；
- 标记 `SUPPORTED/PARTIAL/UNSUPPORTED/NOT_APPLICABLE`；
- 选出 Agent Pay 主作品第一个共同断点；
- 选出 Machine Pay 子作品第一个共同断点；
- 不改 `src/`；
- 不进行真实资金动作；
- 不安装新依赖；
- 不改变 CURRENT 主线任务。

若 P0 证明缺口只在 Adapter，则后续代码也优先留在本比赛目录。

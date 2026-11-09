# ACT / A402 与现有能力差距分析 v1

> 日期：2026-09-28
> 方法：只比较“协议要求能否进入现有 Canonical Facts + Trust Core”，不把字段数量当能力数量。
> 状态枚举：`STRONG_REUSE / PARTIAL / EXTERNAL_GAP / DEFERRED / NOT_TARGET`。

## 1. 结论先行

当前项目与 ACT **不是“从零开始”**。

真正的情况是：

```text
ADD（授权）        -> 核心能力高度重合，缺 ACT-native 对象/生命周期/Provider 可验证证据
CID（商业交互）    -> WebShop/Order Binding 已有较多基础，缺 ACT-native 协商与最小交易确认接口
PSD（支付）        -> 生命周期/绑定/恢复很强，最大缺口是真实 Alipay Provider 与 A402 端到端证据
Trusted Attestation-> 本地 Trace/Replay 很强，缺 ACT 事件映射与跨机构/链上锚定；后者不应为比赛强行建设
Credit Association -> 首轮两个作品都不是必要条件，暂不进入建设
```

所以主工作不是“重做 Trust Core”，而是：

> **协议 Adapter + Provider Evidence + Product Demo。**

---

## 2. ADD：Authorization & Delegation Domain

ACT ADD 负责从用户原始意图，经 ISR，到 IAC 签发和生命周期管理。

### 2.1 对照

| ACT 要求 | 当前项目能力 | 判断 | 真正差距 |
|---|---|---|---|
| 原始用户意图 / intent_id | IntentMandate、任务/授权对象、原始上下文证据 | PARTIAL | 尚未按 ACT `conversation_history / intent_id / digest / context_ref` 形成稳定 adapter |
| ISR 结构化约束 | scope / amount / merchant / category / expiry / confirmation policy | STRONG_REUSE | 需要明确 ACT 字段到 Canonical Authority Facts 的映射 |
| SPECIFIED / BOUNDED | 人在环/不在环、Delegated Authority、autonomy/confirmation 规则基础 | PARTIAL | 尚未以 ACT 两种 delegation_mode 做正式 profile |
| IAC | Mandate / Authorization Binding / signed instruction 能力 | PARTIAL | 缺 ACT-native IAC 封装、签发/验签责任边界及 Provider-observed evidence |
| delegation_id | mandate/request/authorization 引用链 | STRONG_REUSE | 需要稳定 cross-domain mapping，不应新增第二套主键体系 |
| Active/Suspended/Revoked/Expired | expiry、失效、replay、部分状态控制 | PARTIAL | **Revocation / Suspend 生命周期仍是明显缺口** |
| Agent identity in authorization | P3 / B-15A/B 身份与持有证明 | STRONG_REUSE（本地） | 真实支付宝/Provider credential 仍属于 F 阶段 |

### 2.2 批判性判断

ADD 是最容易让我们“误以为要重做授权模型”的地方。

不应做：

- 把现有 Mandate 全面改名成 ISR/IAC；
- 把 ACT 字段直接塞进所有核心 Domain Object；
- 为了协议字段完备而扩张 Core。

应做：

```text
ACT conversation / ISR / IAC
          ↓
      ACT Adapter
          ↓
Canonical Delegated Authority Facts
          ↓
      Existing Trust Core
```

第一作品只需优先覆盖 `SPECIFIED`；`BOUNDED` 用作第二阶段高级验证。

### 2.3 优先缺口

P0：

1. ACT ISR → Canonical Authority Facts 的可机械复核映射；
2. IAC / delegation_id → 现有 Authorization / Binding 的引用映射；
3. Revoked / Suspended / Expired 在 Runtime Gate 前的 fail-closed 行为；
4. 支付时证明“当前 IAC 就是本次 Order / Payment 使用的授权”。

P1：

- BOUNDED 累计预算、多轮任务和 autonomous decision。

---

## 3. CID：Commerce Interaction Domain

ACT CID 覆盖目录、意图传递、支付能力协商和购物车确认。

### 3.1 对照

| ACT 组件 | 当前项目能力 | 判断 | 真正差距 |
|---|---|---|---|
| CID-MER-CAT 目录 | WebShop 商品/options 获取与 option grounding | PARTIAL | 缺稳定的 ACT 最低 catalog result adapter；无需造完整商品平台 |
| CID-INT-XFR 意图传递 | User intent / context policy / fact lineage | PARTIAL | 缺“传给商户的最小必要意图”显式 profile 与 privacy boundary |
| CID-PCA-NEG 支付能力协商 | 协议/rail adapter 概念存在 | EXTERNAL_GAP | 尚无 ACT-native payment capability negotiation |
| CID-CART-CFM 购物车确认 | Checkout snapshot continuity、Order Binding、Buy Now Gate | STRONG_REUSE | 需要把 ACT transaction confirmation result 映射到现有 Order / Request facts |

### 3.2 批判性判断

CID 不是我们第一阶段应该大投入的地方。

原因：

1. 项目价值核心是 **Trust / Payment Control**，不是目录搜索或推荐系统；
2. ACT 自身对目录接口也强调最低信息要求，而非强制统一检索协议；
3. 我们已有 WebShop，可作为可控 Commerce Environment；
4. 比赛只需要证明“候选 → 订单确认 → 支付”链能被可信治理，不需要重造淘宝/京东。

因此只做 **Thin Commerce Adapter**：

```text
WebShop / demo merchant
   -> minimal catalog result
   -> selected offer
   -> transaction confirmation
   -> existing Order Binding
```

P0 是 `CID-CART-CFM` 与支付前连续绑定；`CID-PCA-NEG` 只在真实多支付方式协商需要时补。

---

## 4. PSD：Payment Services Domain

PSD 是两个作品真正交汇的位置。

### 4.1 当前强项

现有项目已经具备：

- Payment Request / Payment Execution Binding；
- Runtime Gate；
- duplicate payment protection；
- UNKNOWN query/recovery；
- Payment Finality / status conflict；
- Fulfillment failure / remediation；
- refund/dispute evidence continuity；
- Authoritative Trace / Replay；
- x402 offline conformance；
- 支付宝 Sandbox 已进入 F 阶段测量。

这说明“支付生命周期内核”不应重写。

### 4.2 ACT PSD 差距

| PSD 组件 | 对 Agent Pay | 对 Machine Pay | 当前判断 |
|---|---:|---:|---|
| PSD-PMT-BND 支付方式绑定 | 重要 | 可复用 | EXTERNAL_GAP：缺真实 Provider payment token/binding evidence |
| PSD-AGT-SUB Agent 专属子账户 | L3 可选 | 可选 | DEFERRED：不是首个作品必要条件 |
| PSD-PAY-INS 即时支付 | 可作为 fallback / first demo | Machine Pay 用户确认可能使用 | PARTIAL |
| PSD-PAY-DEL 定向委托 | **主作品首选** | 可作为授权上游 | PARTIAL，但核心语义已有 |
| PSD-PAY-AUP 自主委托 | 第二阶段高级能力 | 高频资源购买很相关 | PARTIAL，先不作为首发 Gate |
| PSD-PAY-A402 | 可被 Agent Pay 场景引用 | **子作品核心** | PARTIAL：x402 基础已有，Alipay A402 live 闭环缺失 |

### 4.3 最大真实差距

最大的差距不是“支付状态机”，而是 **Provider-observed evidence**：

```text
Payment-Needed / Agent Pay request
        ↓
真实支付宝侧支付/测试支付
        ↓
Payment-Proof / provider result
        ↓
verify
        ↓
business-field binding check
        ↓
fulfillment
        ↓
fulfillment.confirm
        ↓
Trace
```

Machine Pay 官方要求至少核验：

- `active == true`；
- amount 与本次资源价格一致；
- `out_trade_no` 与当前订单一致；
- `resource_id` 与当前资源一致；
- `trade_no` 不得重复履约。

这些正好可以直接落入现有 Binding / Idempotency / Fulfillment Gate，而不需要新增第二套 Validator。

---

## 5. Trusted Attestation：可信存证

ACT Trusted Attestation 与本项目的 Authoritative Trace / Fact Lineage / Replay 高度相关，但不能简单写成“已支持 ACT 存证”。

### 5.1 已有能力

本项目已有：

- Product Authoritative Trace；
- Fact Lineage；
- Action Origin / Responsibility；
- Read Model / Player；
- payment / fulfillment / remediation 连续证据；
- signed instruction verification 的本地代表性闭环。

因此“链下完整记录、跨对象关联、事后复核”是强项。

### 5.2 ACT 新增要求

ACT 还定义：

- 标准事件类型；
- 链下存证记录；
- 签名材料；
- ACT Trust Chain 摘要锚定；
- 链下记录与链上锚点一致性验证；
- 争议举证流程。

### 5.3 批判性判断

**不要为了 Payathon 把链上锚定做成主项目强依赖。**

理由：

1. 当前两个产品能否证明授权、绑定、支付、履约可信，不依赖先完成链上锚定；
2. 主项目规则明确：普通签名、审计、幂等足够时默认不用链；
3. ACT 的链上锚定属于跨机构可信增强，不等于 Agent Pay 首个支付闭环的最小前置条件；
4. 若比赛后续明确要求 ACT conformance 或 Trust Chain 集成，再做独立 Adapter / exporter 更合理。

第一阶段只做：

```text
Existing Authoritative Trace
    -> ACT event type projection
    -> off-chain attestation export
```

链上锚定标为 `DEFERRED / OPTIONAL_EXTERNAL_VALIDATION`。

---

## 6. Credit Association：首轮不建设

信用关联可影响商户/Agent 信任排序，但当前两个作品的可证伪核心问题是：

- 是否有授权；
- 是否越权；
- 订单/资源/金额是否绑定；
- 支付是否重复；
- 是否真实履约；
- 证据是否连续。

因此 Credit Association 不是首轮必要依赖，标记 `NOT_TARGET`。

---

## 7. 两个作品的最小差距矩阵

| 能力 | Agent Pay 主作品 | Machine Pay 子作品 | 是否改主 Core |
|---|---|---|---|
| ACT ISR/IAC adapter | P0 | 上游可复用 | 否 |
| SPECIFIED delegation | P0 | 可复用 | 否 |
| BOUNDED delegation | P1 | P1 | 只有出现协议中立缺口才考虑 |
| CID cart confirmation mapping | P0 | N/A / very thin | 否 |
| Provider payment binding | P0 | P0 | 否，接 Adapter |
| A402 Payment-Needed | 可选 | P0 | 否 |
| Payment-Proof verify | P0/按实际 Agent Pay接口 | P0 | 否 |
| out_trade_no/resource/amount binding | P0 | P0 | 复用现有 Binding |
| replay / duplicate fulfillment | P0 | P0 | 复用现有能力 |
| fulfillment evidence | P0 | P0 | 复用现有 Trace |
| IAC revocation | P0 | P1 | 可能形成协议中立能力缺口，先测量 |
| Agent dedicated sub-account | P2 | P2 | 否，Provider feature |
| ACT chain anchor | P2/可选 | P2/可选 | 否 |
| Credit Association | NOT_TARGET | NOT_TARGET | 否 |

---

## 8. 与 PCAC 外部要求的交叉提醒

比赛工作区仍需沿用主项目 PCAC-AGENTPAY 外部要求基线。

与首轮直接相关：

- PCAC-03 KYA 身份识别与验证；
- PCAC-05 Agent 身份全链路传递；
- PCAC-07 Delegated Authorization；
- PCAC-08 用户身份与支付意愿；
- PCAC-09 防越权与完整性；
- PCAC-10 授权撤销；
- PCAC-11 金额与交易护栏；
- PCAC-12 Evidence Chain；
- PCAC-14 注入/篡改/越权；
- PCAC-18 应急处置；
- PCAC-20 自主支付上线前评估/回退。

这里仍然只作为开发/验证基线，不表述成合规结论。

---

## 9. 当前建议

### 主项目不动的部分

- Canonical Facts；
- Trust Core；
- 四态决策；
- Payment Lifecycle；
- Authoritative Trace；
- Evaluator/Executor 基线。

### 比赛目录新增的部分

- ACT adapter；
- Alipay Agent Pay provider adapter / demo seam；
- A402 seller/client adapter；
- competition profile / fixtures；
- 两个独立产品入口；
- demo UI / submission assets；
- protocol-specific evidence exporter。

### 只有满足以下条件才回写主项目

一个比赛中发现的缺口必须同时满足：

1. 不是支付宝/ACT/A402 私有字段缺口；
2. 在 Agent Pay 与 Machine Pay 或其他第二消费者中重复出现；
3. 会改变现有协议中立 Trust Contract；
4. 有失败 Case 和 before/after evidence；
5. 通过 Evaluator 冻结后才进入主线。

否则，留在比赛 Adapter 层。

---

## 10. 官方依据

- ACT ADD：<https://www.act-protocol.com/documentation/delegation>
- ACT CID：<https://www.act-protocol.com/documentation/commerce>
- ACT PSD：<https://www.act-protocol.com/documentation/payment>
- ACT Trusted Attestation：<https://www.act-protocol.com/documentation/trust/attestation>
- 支付宝 Machine Pay：<https://aipay.alipay.com/docs/ai-receive/MACHINE_PAY.html>
- 支付宝 AI 付产品概览：<https://aipay.alipay.com/docs/overview.html>

# Best Buy / UCP 对 Agentic Payment Trust Lab 的吸收与测试补充分析

> 日期：2026-08-28  
> 适用仓库：`agentic-payment-trust-lab`  
> 定位：外部商城与 Agent Commerce（智能体商业）参考，不改变当前第一瓶颈 B-04 的执行顺序。  
> 当前决策：先记录、后拆包；不立即引入第二商城 Runtime（运行环境），不修改当前 B-04 合同。

## 1. 结论

Best Buy 相关公开能力可以补充本项目，但不建议把它简单理解为“再增加一个商城测试案例”。

更合理的吸收方式分成三层：

```text
WebShop
→ 网页 / 搜索 / 点击型 Agent 环境

Best Buy API Playground
→ 商品、分类、价格、门店等传统 Retail API（零售 API）环境

UCP Samples
→ Agent-native Commerce（智能体原生商业）协议环境
→ Capability Discovery / Checkout / Order / Fulfillment / Payment
```

三者最终统一进入本项目现有主链：

```text
External Commerce Environment
→ Commerce / Protocol Adapter
→ Neutral Facts
→ Trust Control Plane
→ Governed Action
→ Payment / Fulfillment
→ Authoritative Trace
→ Evaluation
```

目标不是复制多个商城，而是验证：

> 换掉外部商城、协议和 Transport（传输方式）之后，本项目的授权、绑定、身份、来源、人工确认、支付恢复和证据回放是否仍然成立。

如果成立，才能说明当前能力不是 WebShop 专用补丁，而是具有协议中立性的 Agent Payment Trust Infrastructure（智能体支付信任基础设施）。

---

## 2. 与当前项目状态的关系

当前项目已经形成：

```text
WebShop
→ Commerce Adapter
→ Runtime Authorization Gate
→ Payment / Fulfillment Sidecar
→ Fact Lineage
→ Authoritative Trace
→ Journey Read Model / Player
```

当前第一瓶颈仍是 B-04：External Agent Behavior（外部智能体行为）。

当前要验证的是：

```text
instruction
+ current observation
+ available actions
→ autonomous Agent policy
→ search / product click / option click
→ pre-Buy-Now stop
→ independent score
```

因此当前原则保持不变：

1. 先完成当前 WebShop B-04 autonomous pre-Buy-Now baseline（自主购买前基线）。
2. 不在 B-04 尚未完成时横插完整 Best Buy / UCP 实现。
3. Best Buy / UCP 先作为后续外部环境与协议扩展路线记录。
4. 后续实现继续遵循“一次只验证一个主要变化”的 evaluator-executor 规则。
5. 外部协议与商城只作为输入、约束和独立验证来源，不直接替代项目内部 Trust Contract（信任合同）。

---

## 3. Best Buy API Playground 适合补什么

Best Buy API Playground 的主要价值不是支付，而是补一个与 WebShop 不同的传统 Retail API（零售 API）环境。

适合验证：

```text
Product / SKU
Category
Price
Store
Availability / Buying Options
Structured REST API
```

建议链路：

```text
Best Buy Product / Retail API
        ↓
BestBuy Commerce Adapter
        ↓
OrderCandidate / Selection / Amount / Merchant Context
        ↓
本项目 Neutral Model
        ↓
Trust Control Plane
```

### 3.1 主要价值

第一，验证 Commerce Adapter 是否对 WebShop 结构过拟合。

第二，引入更接近真实零售 API 的商品结构，而不是仅依赖 WebShop 的：

```text
search[keywords]
click[asin]
click[option]
```

第三，为后续 UCP Merchant 提供更真实的商品、分类、价格等数据来源候选。

第四，形成第二种外部事实来源，验证 Fact Lineage（事实血缘）和 Source Classification（来源分类）是否可迁移。

### 3.2 明确边界

Best Buy Playground 不能被当成完整支付商城。

本项目不能自行补造：

```text
Best Buy Checkout
Best Buy Payment
Best Buy Refund
Best Buy Fulfillment
```

如果公开样品没有这些事实，就只能停留在公开能力范围内。

因此 Best Buy 更适合：

```text
商品发现 / 商品事实 / Retail API
```

支付、授权、履约、恢复继续由：

```text
UCP / AP2 样品
+
本项目模拟 Payment / Fulfillment Sidecar
```

承担。

---

## 4. UCP Samples 的价值高于“再加一个商城”

UCP Samples 更适合成为后续第二个正式外部 Agent Commerce 环境。

建议把它看成：

```text
WebShop
= 网页式 Agent Shopping Environment

UCP Samples
= Agent-native Commerce Environment
```

后续比较：

```text
WebShop                  UCP Samples
网页观察与动作            结构化协议能力
search / click            checkout / order / capability
       \                 /
        Commerce / Protocol Adapter
                  ↓
          Neutral Facts
                  ↓
          Trust Control Plane
```

这比再复制一个页面型商城的价值更高，因为它能同时验证：

- 外部环境迁移；
- 协议对象映射；
- Capability Discovery（能力发现）；
- Checkout / Order 生命周期；
- Schema Conformance（模式一致性）；
- Agent-native Transport（智能体原生传输方式）。

---

## 5. 应重点吸收的五类能力

### 5.1 Capability Discovery（能力发现）

UCP 的重要思想不是让 Agent 默认假设商户一定支持某个动作，而是先声明和协商能力。

建议未来映射为：

```text
Merchant Capability Profile
        ↓
Discovery
        ↓
Negotiated Capability
        ↓
Preflight
        ↓
Governed Action
```

这与项目已有：

```text
Capability First Navigation
Known Payment Attempt Preflight
Capability Revalidation
```

高度相关。

后续要验证的不是“有没有一个 capability 字段”，而是：

1. 商户声明了什么能力；
2. Agent 当前需要什么能力；
3. 双方是否形成可执行交集；
4. 能力版本是否兼容；
5. 执行前能力是否仍然有效；
6. 能力变化是否会导致原授权或原动作失效；
7. Capability 来源是否可信，能否被低可信页面或工具结果静默覆盖。

优先级：P1。

### 5.2 Schema Conformance（模式一致性）

当前项目已有大量协议中立对象，例如：

```text
User Intent
IntentMandate / Delegated Authority
Order
TransactionRequest
PaymentExecutionRecord
ContextPolicyFact
Authoritative Trace
```

这些对象长期存在一个风险：

> 内部自己定义、自己生成、自己校验，缺少外部结构裁判。

后续可以增加独立协议一致性层：

```text
External UCP Object
      ↓
Schema / Conformance Validator
      ↓ PASS
Protocol Adapter
      ↓
Internal Neutral Model
      ↓
Trust Validator
```

要明确：

```text
Schema PASS
≠
Trust PASS
```

Schema Conformance 只证明协议对象结构和版本符合标准，不代表交易安全、授权正确或行为可信。

优先级：P1。

### 5.3 Capability 与 Transport 分离

后续架构必须继续坚持：

```text
Commerce Capability
≠
Transport / Protocol Channel
```

例如同一个 Checkout 能力可能通过：

```text
REST
MCP
A2A
Embedded
```

暴露。

本项目内部不要形成：

```text
MCP 支付内核
A2A 支付内核
UCP 支付内核
AP2 支付内核
```

而应该保持：

```text
REST / MCP / A2A / UCP / ACP / AP2
                ↓
             Adapter
                ↓
        Stable Neutral Semantics
                ↓
        Trust Control Plane
```

协议和 Transport 只负责表达、发现、交换和调用，不成为内部支付可信业务内核。

优先级：P1-P2。

### 5.4 UCP Checkout 与 AP2 Binding（绑定）

这是本次最值得与现有 payment-trust-lab 主线结合的部分。

建议未来形成：

```text
UCP Checkout
      ↓
Checkout object / version
      ↓
AP2 Checkout Mandate
      ↓ binding
AP2 Payment Mandate
      ↓ binding
本项目 Runtime Gate
      ↓
Payment Execution
```

重点验证：

1. 用户授权针对的是哪个 checkout / order 版本；
2. checkout 变化后旧确认是否失效；
3. Payment Mandate 是否仍绑定原 checkout；
4. merchant / payee / amount / currency 是否变化；
5. Agent 是否仍是被授权主体；
6. 执行前是否必须重新确认；
7. deterministic validator（确定性校验器）是否能独立给出结果，而不是依赖 LLM 自由判断；
8. Checkout / Mandate / Payment Execution 是否可进入同一 Authoritative Trace（权威轨迹）。

这与现有：

```text
Delegated Authority
→ Agent Intent / Selection
→ Order
→ Payment Request
→ Payment Execution
```

持续 Binding 主线高度一致。

优先级：P1。

### 5.5 Protocol Conformance 与 Trust Evaluation 分层

未来评测必须拆成两个维度。

#### A. Protocol Conformance（协议一致性）

回答：

```text
Schema 是否合法
Capability 是否协商成功
对象版本是否兼容
状态机是否符合协议
Transport 是否按规范调用
```

#### B. Trust Evaluation（信任评测）

回答：

```text
是否越权
是否错绑
是否遗漏人工确认
来源是否可信
是否重复支付
UNKNOWN 是否盲目重试
是否出现禁止副作用
是否能完整回放
```

两者关系：

```text
Protocol Conformance PASS
        ↓
只能证明“协议实现正确”

Trust Evaluation PASS
        ↓
才能证明“Agent 行为在本项目定义的可信边界内”
```

后续 UI 和结果卡也应保持这个分层。

优先级：P1。

---

## 6. 推荐的外部验证环境结构

后续目标不是一堆零散商城，而是形成三类环境：

```text
A. WebShop
网页 / 搜索 / 点击型 Agent 环境
        │
        │
B. Best Buy API Playground
结构化传统 Retail API 环境
        │
        │
C. UCP Samples
Agent-native Commerce 协议环境
        │
        ↓
Commerce / Protocol Adapter
        ↓
Neutral Facts
        ↓
Trust Control Plane
        ↓
Authority
Binding
Identity
Provenance
Confirmation
Policy
        ↓
Governed Action
        ↓
Payment / Fulfillment
        ↓
Authoritative Trace
        ↓
Evaluation
```

三类环境分别解决：

| 环境 | 主要验证问题 |
|---|---|
| WebShop | Agent 能否从页面观察中自主完成选品与操作 |
| Best Buy Playground | Adapter 能否处理不同的真实感 Retail API 商品结构 |
| UCP Samples | Agent-native 商业能力、Capability Discovery、Checkout、Order 等协议对象是否可进入同一 Trust Plane |

---

## 7. 后续可形成的测试族

不建议继续顺序新增 S21、S22、S23。

建议按结构族组织。

### 7.1 Commerce Environment Portability（商城环境可迁移性）

验证：

```text
同类购买任务
WebShop 输入
Best Buy API 输入
UCP 输入
        ↓
是否能映射为相同 Neutral Semantics
```

核心指标：

- 关键事实映射完整率；
- 来源分类完整率；
- 同义对象 Binding 一致率；
- Trust Decision 是否出现环境相关漂移。

### 7.2 Capability Discovery / Revalidation（能力发现与重验证）

覆盖：

- 初始能力支持；
- 能力版本不兼容；
- checkout 前 capability 消失；
- payment 前 capability 变化；
- Agent 请求商户未声明能力；
- 低可信事实伪造 capability。

### 7.3 Checkout Mutation（结账对象变化）

覆盖：

- 商品变化；
- 选项变化；
- 金额变化；
- merchant / payee 变化；
- currency 变化；
- delivery / fulfillment 变化。

### 7.4 Mandate Binding（授权绑定）

覆盖：

- Checkout Mandate 与 Payment Mandate 不一致；
- 旧 checkout version 被重放；
- 用户确认针对旧版本；
- Agent 替换 checkout 后继续付款；
- Checkout 合法但 Payment Request 指向其他对象。

### 7.5 Transport Independence（传输方式独立性）

验证同一业务能力通过：

```text
REST
MCP
A2A
```

进入内部后，关键 Neutral Fact 与 Trust Decision 是否一致。

### 7.6 Protocol PASS / Trust FAIL

专门设计：

```text
UCP Schema 完全合法
+
动作违反用户授权
```

用于证明：

```text
Protocol Correctness
≠
Payment Trust
```

这是本项目很重要的一类差异化验证。

---

## 8. 推荐优先级

| 优先级 | 事项 | 当前建议 |
|---|---|---|
| P0 | 完成 WebShop B-04 autonomous Agent | 先完成，不跳任务 |
| P1 | UCP Capability Discovery | 后续第一批吸收 |
| P1 | UCP Schema / Conformance | 建立外部结构裁判 |
| P1 | UCP Samples 第二商城环境 | 验证是否 WebShop 特化 |
| P1 | UCP Checkout → AP2 Mandate → Runtime Gate | 对齐 Trust 主线 |
| P1 | Protocol Conformance / Trust Evaluation 分层 | 固化评测方法 |
| P2 | Best Buy Playground | 补真实 Retail API 和商品结构 |
| P2 | REST / MCP / A2A Transport 对比 | 验证 Transport 独立性 |
| P3 | Identity Linking / Embedded Checkout 等扩展 | 当前不是第一瓶颈 |

---

## 9. 现阶段明确不做

为了避免再次变成“开源项目看一个接一个、实现方向不断切换”，现阶段不做：

1. 不立即克隆、安装 Best Buy Playground；
2. 不立即引入 UCP SDK；
3. 不立即增加第二商城 Runtime；
4. 不新增一批连续 S 编号；
5. 不为了覆盖协议修改当前 B-04 合同；
6. 不把协议对象直接变成本项目业务内核；
7. 不把 UCP / AP2 协议通过等同于 Trust PASS；
8. 不接真实 Best Buy Commerce、真实资金、真实卡、生产商户；
9. 不因为 UCP 支持 MCP / A2A 就重复建设多个支付内核；
10. 不把普通 Schema Validation（模式校验）包装成安全或合规结论。

---

## 10. 后续实施拆分原则

等当前 B-04 完成后，再逐项拆实现步骤。

推荐拆法：

```text
Step 1
冻结 UCP / Best Buy 上游版本与许可证
        ↓
Step 2
只做 Capability Discovery / Schema 离线样品
        ↓
Step 3
建立 UCP → Neutral Model Adapter
        ↓
Step 4
接入现有 Trust Gate
        ↓
Step 5
建立 UCP Checkout → AP2 Mandate Binding
        ↓
Step 6
跑 Protocol Conformance + Trust Evaluation 双评测
        ↓
Step 7
再决定是否接 Best Buy Playground 商品数据
        ↓
Step 8
最后再做 REST / MCP / A2A Transport 对比
```

每个步骤必须回答：

```text
当前瓶颈是什么
→ 这个外部能力是否真的解决该瓶颈
→ 只改变一个主要变量
→ 是否有可重复 baseline
→ 是否有独立 validator
→ 是否改善项目级指标
→ 没有改善则回滚或停止
```

---

## 11. 后续实现时建议重点观察的项目级指标

后续不以“多支持了一个协议 / 多跑了一个 Demo”为成功标准，而优先看：

| 指标 | 含义 |
|---|---|
| Commerce Environment Portability | 换商城后是否仍能形成稳定中立事实 |
| Protocol Conformance | 外部协议对象是否符合固定版本 Schema / 状态机 |
| Trust Decision Consistency | 不同环境 / Transport 下同义任务的可信决策是否一致 |
| Binding Continuity | Intent → Checkout → Mandate → Payment 是否持续绑定 |
| Source Lineage Completeness | 外部事实、协议事实、项目派生事实能否分层追溯 |
| Confirmation Integrity | 对象变化后旧确认是否正确失效 |
| Forbidden Side Effect Rate | 非 ALLOW 情况下禁止副作用是否始终为 0 |
| Replay Completeness | 协议输入到最终决策能否机械回放 |

---

## 12. 一句话定位

> Best Buy 的价值主要是补真实感 Retail API 和商品环境；UCP 的价值主要是补 Agent-native Commerce 协议、Capability Discovery 和 Schema Conformance；AP2 的价值主要是把 Checkout 与 Payment 授权持续绑定。三者最终都应该服务于同一个协议中立 Trust Control Plane，而不是各自演化成一套新的支付内核。

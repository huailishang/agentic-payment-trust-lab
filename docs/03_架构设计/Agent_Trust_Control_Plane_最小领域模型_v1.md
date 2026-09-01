# Agent Trust Control Plane 最小领域模型 v1

> 日期：2026-07-29
> 目的：承接《智能体支付架构基线 v1》和《能力归位与缺口分析 v1》，冻结 Agent Trust Control Plane 的最小领域模型。本文只定义领域对象、关系、边界和后续实现顺序，不立即修改现有业务代码或 UI。

## 1. 一句话结论

Agent Trust Control Plane 不负责重新发明支付清算，而是负责证明：

> **Agent 当前执行的动作，仍然来自一个明确、有效、可追溯的用户授权，并且授权对象、执行主体、订单、支付请求和最终执行在整个链路中没有被不可信上下文悄悄替换。**

最小模型只保留 6 个核心对象：

```text
1. User Intent
2. Delegated Authority
3. Agent Identity / Executor
4. Transaction Object
5. Payment Execution
6. Evidence / Replay Event
```

其中真正的主链不是“6 个对象并列”，而是：

```text
User Intent
   ↓ 用户确认 / 授权形成
Delegated Authority
   ↓ 约束 Agent 可做什么
Agent Identity / Executor
   ↓ 执行某个受托动作
Transaction Object
   ↓ 形成具体订单 / 支付请求
Runtime Authorization Gate
   ↓ 执行前统一裁决
Payment Execution
   ↓ 发生真实或模拟执行
Evidence / Replay Event
   ↑ 全程记录授权、绑定、变化、裁决和执行事实
```

注意：`Runtime Authorization Gate` **不是第 7 个领域对象**。它是一个控制点 / Enforcement Point，把前面多个对象和上下文组织成一次“当前动作是否允许产生副作用”的确定性裁决。六个核心对象保持不变。

## 2. 为什么只保留这 6 个对象

当前项目已经有很多类、字段和测试，但如果继续按字段或场景扩张，会再次回到“案例驱动”。

这 6 个对象覆盖了 Agent 支付中最关键的 6 个问题：

| 核心问题 | 对应对象 |
|---|---|
| 用户原本想做什么 | User Intent |
| Agent 被允许做什么 | Delegated Authority |
| 谁在代表用户执行 | Agent Identity / Executor |
| Agent 具体选了什么、准备支付什么 | Transaction Object |
| 最终实际执行了什么 | Payment Execution |
| 事后能否还原整个过程 | Evidence / Replay Event |

其他概念先作为这 6 个对象的属性、引用或事件存在，只有未来出现独立生命周期和明确消费者时，才升级为新的领域对象。

## 3. 对象 1：User Intent

### 3.1 它回答什么

> 用户原始目标是什么？

它不是支付授权本身，而是授权形成之前的用户目标。

例如：

```text
“帮我买一双 500 元以内的跑鞋。”
“明天下午之前帮我订一张去东京的机票。”
“每月自动支付这个 SaaS 订阅，但单月不能超过 300 元。”
```

### 3.2 最小字段

```text
intent_id
subject_id
raw_intent
created_at
intent_version
```

可选：

```text
source_channel
context_refs
```

### 3.3 明确不做

v1 不要求：

- 保存完整聊天历史；
- 把自然语言理解做成独立 LLM 产品；
- 宣称系统已经正确理解用户语义。

User Intent 只作为“授权从哪里来”的根对象。

## 4. 对象 2：Delegated Authority

### 4.1 它回答什么

> 用户最终明确允许 Agent 做什么？

这是整个 Agent Control Plane 最关键的根对象。

当前代码里的 `IntentMandate` 已经是它的雏形，但还只是规则集合。

### 4.2 最小字段

```text
authority_id
intent_ref
subject_id
authorized_agent_ref
scope
valid_from
valid_until
autonomy_level
confirmation_policy
authority_version
confirmation_evidence_ref
status
```

其中 `scope` 最小支持：

```text
amount_limit
currency
merchant_scope
category_scope
item_scope
max_count
```

### 4.3 Autonomy Level 最小枚举

先只需要三级：

```text
OBSERVE_ONLY
    只能建议，不能执行支付相关动作

CONFIRM_BEFORE_EXECUTE
    可以搜索、选择、准备交易，但执行前必须确认

DELEGATED_EXECUTION
    在授权边界内可以直接执行；越界或关键对象变化必须重新确认
```

不追求一次性设计所有企业审批级别。

### 4.4 Confirmation Policy 回答什么

不是简单一个金额阈值，而是：

> 什么变化会让旧授权 / 旧确认失效？

最小规则：

```text
amount_change
merchant_change
item_change
payee_change
authority_version_change
agent_change
```

以后 `confirmation_above` 可以继续保留，但它只是 Confirmation Policy 的一项规则。

## 5. 对象 3：Agent Identity / Executor

### 5.1 它回答什么

> 当前到底是谁在代表用户执行？

当前 `expected_agent_id == request.agent_id` 只能证明两个字符串相同。

因此 v1 必须把两层概念分开：

```text
Declared Identity
    Agent 自己声称自己是谁

Verified Executor Fact
    当前系统掌握了什么可以验证的执行主体证据
```

### 5.2 最小字段

```text
agent_id
provider
executor_instance_id
credential_ref
identity_assurance_level
status
```

v1 不要求实现真实 PKI，但领域模型必须允许未来接入：

```text
signed credential
provider attestation
workload identity
certificate / key reference
federated identity
```

### 5.3 Identity Assurance 最小等级

```text
DECLARED
    只有字符串引用

BOUND
    能证明当前执行引用和授权引用一致

VERIFIED
    有额外凭证 / attest / authenticator 证据支持
```

当前项目只能到 `DECLARED / BOUND`，不能自称 `VERIFIED`。

## 6. 对象 4：Transaction Object

### 6.1 它回答什么

> Agent 当前究竟准备替用户完成哪一笔具体交易？

这里不要把“订单”和“支付请求”完全混为一个对象，但 v1 也不急着拆成很多领域实体。

先统一理解为一条逐步具体化的交易对象链：

```text
Candidate / Offer
    ↓
Selected Order
    ↓
Payment Request
```

### 6.2 最小公共字段

```text
transaction_object_id
object_type
object_version
authority_ref
agent_ref
merchant
payee
amount
currency
item_refs
created_at
parent_object_ref
```

`object_type` 最小枚举：

```text
OFFER
ORDER
PAYMENT_REQUEST
```

### 6.3 为什么必须有 parent_object_ref

因为 Agent 支付核心不是“最后这个 Order 看起来对不对”，而是：

```text
这个 Payment Request
是不是来自这个 Order？

这个 Order
是不是来自这个用户授权允许的选择？
```

因此后续 Binding 不应该只验证两个 Hash，而应该逐步升级成：

```text
authority_ref
parent_object_ref
object_version
critical_field_binding
```

共同构成链式绑定。

## 7. 对象 5：Payment Execution

### 7.1 它回答什么

> 最终到底执行了哪一笔金融动作？

这部分主要属于成熟支付交易底座，但 Agent Control Plane 必须引用它，因为最后要证明：

> Agent 授权链最终落到了哪笔支付执行。

### 7.2 最小字段

当前 `PaymentExecutionRecord` 已经比较接近：

```text
payment_id
request_id
transaction_object_ref
authority_ref
agent_ref
status
amount
currency
provider_ref
idempotency_key
occurred_at
```

其中当前代码已有：

```text
payment_id
request_id
order_id
status
amount
currency
provider_ref
idempotency_key
```

后续真正需要补的不是更多支付字段，而是：

```text
authority_ref
agent_ref
transaction_object_ref
```

让支付执行可以回溯到 Agent 授权链。

## 8. 对象 6：Evidence / Replay Event

### 8.1 它回答什么

> 事后能不能还原“谁、基于什么授权和事实、为什么执行了什么”？

当前 `EvidenceRef` 是一个很好的最小证据字段，但还不是完整 Replay 模型。

### 8.2 最小事件结构

```text
event_id
event_type
occurred_at
subject_ref
agent_ref
authority_ref
transaction_object_ref
payment_ref
source_type
source_ref
action_origin
decision
reason_codes
previous_event_ref
```

v1 先不要求密码学防篡改链，但保留 `previous_event_ref`，为后续事件链 / hash chain 做准备。

### 8.3 Source Type：可信事实来源最小分级

这是当前 Attack Overlay 下一步最重要的领域补充。

```text
USER_CONFIRMED
SYSTEM_POLICY
AGENT_DECLARED
AGENT_INFERRED
MERCHANT_PROVIDED
PROTOCOL_VERIFIED
PAYMENT_PROVIDER_OBSERVED
EXTERNAL_TOOL_UNTRUSTED
WEB_UNTRUSTED
LLM_GENERATED
```

核心原则：

> **低可信来源不能直接覆盖高可信来源。**

例如：

```text
WEB_UNTRUSTED
    X 不能直接改写 USER_CONFIRMED amount_limit

LLM_GENERATED
    X 不能直接改写 PROTOCOL_VERIFIED payee

PAYMENT_PROVIDER_OBSERVED
    可以更新支付状态观察
    但不能反向修改用户授权
```

这比“再加 10 个 Prompt Injection 案例”更接近真正稳定的 Trust Boundary 能力。

### 8.4 Action Origin 与责任证据视图

`source_type` 回答“这条事实从哪里来”，但在自主 Agent 场景中还需要额外回答：

> **这一步是谁决定的：用户明确授权、Agent 自主选择、Runtime 裁决，还是外部系统返回的事实 / 执行结果？**

首版不新增领域对象，只给 Evidence / Replay 与 Autonomous Trace 增加 `action_origin`（行为来源）语义：

```text
USER_AUTHORITY
    用户明确表达或确认的目标、约束与授权

AGENT_DECISION
    Agent 在授权边界内自主形成的搜索、选择、选项或动作

RUNTIME_DECISION
    Runtime Authorization Gate / Policy 的执行前裁决

EXTERNAL_FACT
    商户、支付服务商、网页、工具或协议提供的外部事实

EXECUTION_RESULT
    支付执行、状态、履约、退款或恢复结果
```

`action_origin` 与 `source_type` 不重复：同一个 `AGENT_DECISION` 仍可能依赖不同来源事实；同一个 `EXTERNAL_FACT` 也必须保留它来自 `MERCHANT_PROVIDED`、`PAYMENT_PROVIDER_OBSERVED` 还是 `WEB_UNTRUSTED`。

在此基础上允许生成一个派生的 `Accountability View`（责任证据视图）：沿 User Intent → Authority → Agent Decision → Runtime Decision → Execution → Recovery 找到**首个违反既定 Trust Contract 的证据断点**。该断点可标记为 `responsibility_breakpoint`，用于审计、回放和技术归因，但**不得直接推导法律责任、赔偿责任、监管责任或机构间最终权责分配**。

## 9. 六个对象之间最重要的关系

整个 Control Plane 最重要的不是对象数量，而是 5 条关系。

### R1. Intent -> Authority

```text
User Intent
    ↓ 用户确认 / 授权形成
Delegated Authority
```

必须能回答：

- authority 来自哪个 intent；
- 当前 authority 是哪个版本；
- 用户确认的是哪个版本。

### R2. Authority -> Agent

```text
Delegated Authority
    ↓ authorized_agent_ref
Agent Identity / Executor
```

必须能回答：

- 谁可以使用这个授权；
- 当前执行主体是否仍然匹配。

### R3. Authority -> Transaction Object

```text
Delegated Authority
    ↓ scope + binding
Transaction Object
```

必须能回答：

- 金额、商户、品类、对象是否仍在授权范围；
- 当前对象是否属于这个授权产生的交易链。

### R4. Transaction Object -> Payment Execution

```text
Payment Request
    ↓ execution binding
Payment Execution
```

必须能回答：

- 最终实际执行的是不是刚才确认 / 授权的交易对象；
- 金额、币种、payee 等关键事实有没有被换掉。

### R5. 全链 -> Evidence / Replay

```text
Intent
Authority
Agent
Transaction Object
Payment Execution
       ↓
Evidence / Replay Events
```

必须能还原完整因果链，并机械区分 `USER_AUTHORITY`（用户授权）与 `AGENT_DECISION`（Agent 自主决策）；需要责任分析时，再从既有事件链派生 `responsibility_breakpoint`（责任断点），不新增第 7 个领域对象。

### R6. Runtime Authorization Gate：关系汇合后的执行前裁决

Gate 的最小输入不是一个 `agent_id` 或一个 `amount`，而是一组有来源、有版本的执行事实：

```text
subject_ref
agent_ref / executor_ref
authority_ref + authority_version
transaction_object_ref + object_version
current_action
trusted_context
prior_action_summary
policy_version
```

最小职责：

```text
1. 在产生真实副作用前拦截动作
2. 检查当前动作是否仍在 Delegated Authority 内
3. 检查 Agent / Transaction / Payment Binding 是否成立
4. 检查当前上下文中是否出现低可信覆盖或关键事实冲突
5. 根据 Policy 输出业务可消费的裁决事实
6. 为 P5 Evidence / Replay 生成结构化决策记录
```

当前项目先保持四类业务决策：

```text
ALLOW
DENY
CONFIRMATION_REQUIRED
INDETERMINATE
```

与 AARM 等外部运行时安全规范的概念映射仅用于参考：

```text
ALLOW   -> ALLOW
DENY    -> DENY
STEP_UP -> CONFIRMATION_REQUIRED
DEFER   -> INDETERMINATE / WAIT
MODIFY  -> 当前不自动映射
```

支付场景尤其不应默认接受 `MODIFY`：如果 Gate 自动修改金额、payee、商品或授权对象后继续执行，可能直接破坏用户已经确认的对象绑定。因此关键支付字段变化应优先重新裁决 / 重新确认，而不是静默改写。

外部实现与规范参考见 [Agent 身份与运行时授权开源项目参考](../reference/03_身份与治理/Agent身份与运行时授权开源项目参考_20260729.md)。

## 10. 最小状态变化规则

v1 先只冻结几条最关键的不变量。

### I1. 授权版本变化必须失效旧绑定

```text
authority_version changed
    -> old transaction binding cannot silently continue
```

### I2. Agent 变化必须重新验证

```text
authorized_agent_ref != current_agent_ref
    -> cannot silently execute
```

### I3. 关键交易对象变化必须触发重新裁决

至少：

```text
amount
merchant
payee
items
currency
```

发生变化后，旧确认不能自动继承。

### I4. 不可信来源不能直接升级为可信支付事实

```text
WEB_UNTRUSTED / LLM_GENERATED / EXTERNAL_TOOL_UNTRUSTED
    -> cannot overwrite trusted authority / payment facts directly
```

### I5. UNKNOWN 仍按成熟支付底座处理

```text
UNKNOWN
    -> query original transaction
    -> no blind second payment
```

这条不是 Agent 新能力，但必须继续作为底座不变量。

## 11. 与当前代码的映射

| 新领域对象 | 当前代码 | 结论 |
|---|---|---|
| User Intent | 暂无独立对象 | 缺口；先设计，不急着实现 LLM 理解 |
| Delegated Authority | `IntentMandate` | 直接演进对象 |
| Agent Identity / Executor | `AgentIdentity` + `expected_agent_id` + `request.agent_id` | 已有雏形，需要统一语义 |
| Transaction Object | `Order` + `TransactionRequest` | 当前拆分方式可继续用，但要补引用关系 |
| Payment Execution | `PaymentExecutionRecord` | 已有较好骨架，只需后续补授权 / Agent / 交易对象引用 |
| Evidence / Replay Event | `EvidenceRef` + result card | 已有证据片段，缺完整事件链 |

因此当前不建议立刻新增 6 个 Python 类并强行替换旧模型。

正确方式是：

```text
先冻结语义
    ↓
找一个最小纵向切片验证
    ↓
只修改切片真正需要的对象
    ↓
回归通过后再迁移其余模块
```

## 12. 第一条最值得实现的纵向切片

不是 Agent PKI，也不是重新做 UI。

建议第一条实现：

```text
Delegated Authority v1
      ↓
Authority Version
      ↓
Order / Payment Request Binding
      ↓
关键对象发生变化
      ↓
旧确认失效
      ↓
CONFIRMATION_REQUIRED
      ↓
Evidence / Replay 记录为什么需要重确认
```

为什么先做它：

1. 直接命中当前 P0：Delegated Authority + 连续 Binding。
2. 可以复用 S08 / S09，不需要新增 S14。
3. 不需要先建设复杂密码学。
4. 可以继续让 M5 / 回归集验证。
5. 完成后 UI 才真正有一个“Agent 时代新增能力”可以讲。

## 13. 暂缓实现的东西

在第一条纵向切片完成前，继续暂缓：

```text
D1 数据最小化
S14 商户别名
完整 Agent PKI
完整签名 / 证书体系
区块链 / 智能合约
大规模 UI 重构
新协议覆盖
```

## 14. 模型冻结后的实现原则

后续代码开发必须遵守：

```text
一个能力缺口
    ↓
一个最小领域变化
    ↓
至少一个现有场景真实消费
    ↓
负向测试
    ↓
M5 / 全量回归
    ↓
确认增强后再继续
```

不允许：

```text
先增加很多新类 / 新字段
    ↓
再想这些字段能解决什么问题
```

## 15. 当前正式下一步

```text
Architecture Rebaseline【完成】
        ↓
能力归位【完成】
        ↓
Agent Trust Control Plane 最小领域模型【本文完成】
        ↓
下一步：设计并实现第一条纵向切片
        Delegated Authority v1
        + Authority Version
        + Order / Payment Request 连续绑定
        + 旧确认失效规则
        + Replay Evidence
        ↓
继续使用现有 S08 / S09 + M5 验证
```

## 16. 一句话定义

> **Agent Trust Control Plane 的最小职责，是把“用户想要什么、授权了什么、谁在执行、执行对象是什么、最终支付了什么、为什么允许或要求重新确认”组织成一条可验证、不可被低可信上下文静默改写、可事后回放的执行链。**

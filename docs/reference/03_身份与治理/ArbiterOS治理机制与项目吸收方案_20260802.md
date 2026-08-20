# ArbiterOS 治理机制与项目吸收方案

> 日期：2026-08-02  
> 定位：外部项目吸收分析。用于说明 ArbiterOS 哪些机制适合进入 Agentic Payment Trust Lab，哪些只作为外部参考，避免为了追随通用 Agent 框架而破坏现有支付领域架构。  
> 当前约束：本文不修改 `CURRENT.md`，不插入当前 P9-C1 独立复核，不立即新增代码任务。

## 1. 结论

ArbiterOS 不应成为本项目的第三个工程域，也不应替换现有支付域和可信执行域。

正确吸收方式是：

```text
ArbiterOS 通用运行时治理思想
        ↓ 领域化裁剪
Agent Trust Control Plane 横切能力
        ↓
支付动作统一表达
+ 事实来源与传播
+ 副作用前治理闸门
+ 权威轨迹与评测闭环
```

一句话概括：

> **不搬 ArbiterOS 的“壳”，吸收它的“治理内核思想”，并把它收敛成支付领域可以验证的确定性能力。**

## 2. 为什么不需要重做总体架构

ArbiterOS 的核心定位是运行时治理层：解析 Agent 指令和工具调用、跟踪数据来源、执行策略、在副作用前拦截危险动作，并生成权威轨迹。

本项目现有主线已经与之高度一致：

```text
外部协议 / Agent / WebShop
        ↓
Adapter
        ↓
Facts
        ↓
Trust / Binding
        ↓
State
        ↓
Policy / Runtime Authorization Gate
        ↓
Action
        ↓
Payment / Fulfilment / Recovery
        ↓
Evidence / Replay / M5 / UI
```

已有对应能力包括：

- `SourceType` 与 `ContextPolicyFact`；
- P1—P4 Runtime Gate；
- `RuntimeGateRecord`；
- `ReplayEvent`；
- Payment Recovery、Payment Status Conflict、Lifecycle；
- Attack Overlay；
- M5 统一评测；
- Evaluator—Executor 独立复核；
- P9-E 权威购买轨迹 UI 规划。

因此，ArbiterOS 对本项目不是一次“架构替换”，而是一次“治理能力补强和命名校准”。

## 3. 对应关系

| ArbiterOS | 本项目已有能力 | 吸收结论 |
|---|---|---|
| Governance Kernel | Agent Trust Control Plane + Runtime Gate | 已有主体，不新建第三个内核 |
| Instruction Parsing | Adapter + `current_action` | 需要升级为支付领域动作契约 |
| ACF Instruction Set | 支付生命周期 L1—L9 + 动作类型 | 只吸收领域子集，不复制完整通用指令集 |
| Taint / Source Propagation | `SourceType` + `ContextPolicyFact` | 当前只有来源分类，下一步补来源传播和派生关系 |
| Policy Enforcement | P1—P4 + 支付域业务规则 | 保持“可信事实”和“业务裁决”分层 |
| Unsafe Action Interception | WebShop Buy Now Runtime Gate | 已形成首个真实副作用前拦截点 |
| Authoritative Trace | `RuntimeGateRecord` + `ReplayEvent` | 下一步统一成完整支付轨迹契约 |
| Flight Recorder | Evidence / Replay | 已有骨架，需要统一事件类型和完整度 |
| EDLC | Evaluator—Executor + M5 + 回归集 | 已有闭环，补失败样本沉淀规则 |
| Visualization | P9-E 购买轨迹 UI | 直接吸收“权威轨迹播放器”原则 |
| LiteLLM / OpenAI Proxy | 当前无对应 | 暂不进入核心，仅作为后续外部对比实验 |

## 4. 最值得吸收的四项能力

### 4.1 支付动作统一契约

ArbiterOS 的价值之一，是把自然语言和工具调用先解析成结构化指令，再进行治理。

本项目当前已有 `current_action="execute_payment"`，但仍以零散字符串存在。后续应形成一个很小的支付动作词表，而不是完整复制 ACF。

建议最小动作类型：

```text
OBSERVE
SEARCH
SELECT_OFFER
PREPARE_ORDER
REQUEST_CONFIRMATION
EXECUTE_PAYMENT
QUERY_PAYMENT_STATUS
OBSERVE_ASYNC_STATUS
CONFIRM_FULFILMENT
REQUEST_REFUND
OPEN_DISPUTE
```

每个动作只需要携带治理所需的公共引用：

```text
action_id
action_type
subject_ref
agent_ref / executor_ref
authority_ref + authority_version
transaction_object_ref + object_version
payment_ref
source_refs
side_effect_class
reversibility
occurred_at
```

关键原则：

> 动作契约只描述“准备做什么”和“它绑定什么”，不让 LLM 输出直接变成可执行副作用。

对应现有架构：

```text
外部 Agent / WebShop 行为
        ↓ Adapter
Governed Action + Explicit Facts
        ↓ Runtime Gate
ALLOW / DENY / CONFIRMATION_REQUIRED / INDETERMINATE
```

### 4.2 事实来源传播，而不只是来源标签

当前项目已经定义：

```text
USER_CONFIRMED
SYSTEM_POLICY
AGENT_DECLARED
AGENT_INFERRED
PROTOCOL_VERIFIED
PAYMENT_PROVIDER_OBSERVED
WEB_UNTRUSTED
LLM_GENERATED
EXTERNAL_TOOL_UNTRUSTED
```

当前缺口是：系统知道一个事实“来自哪里”，但还没有完整表达一个派生事实“依赖了哪些上游来源”。

需要吸收 ArbiterOS 的 taint propagation 思想：

```text
网页价格 WEB_UNTRUSTED
+ Agent 摘要 LLM_GENERATED
        ↓ 派生
候选订单金额不能自动升级为 USER_CONFIRMED
```

建议后续补一个轻量的 `FactLineage` / `DerivedFact` 契约：

```text
fact_path
value_digest
direct_source_type
upstream_fact_refs
effective_source_type
transformation_ref
trust_upgrade_evidence_ref
```

最小传播规则：

```text
1. 经过 LLM 推理不会自动提高可信度
2. 低可信来源不能覆盖高可信支付事实
3. 多来源派生结果默认继承最低有效可信等级
4. 只有明确的协议验证、用户确认或支付机构观察才能升级特定事实
5. 来源升级必须留下结构化证据
```

这项能力最适合进入 P9-C2 的攻击与异常测试，而不是现在插入 P9-C1。

### 4.3 权威轨迹，而不是运行日志堆积

ArbiterOS 强调 authoritative trace，即治理系统记录的轨迹才是裁决事实来源。

本项目已有：

```text
EvidenceRef
RuntimeGateRecord
ReplayEvent
PaymentRecoveryResult
PaymentStatusConflictFact
LifecycleResult
WebShop Sidecar Outcome
```

但这些目前还是多个结果对象。后续应统一成一个支付轨迹事件流：

```text
INTENT_RECORDED
AUTHORITY_RECORDED
ACTION_PARSED
FACT_REGISTERED
SOURCE_LINEAGE_DERIVED
TRANSACTION_OBJECT_RECORDED
POLICY_EVALUATED
CONFIRMATION_REQUESTED
ACTION_BLOCKED
ACTION_EXECUTED
PAYMENT_STATUS_OBSERVED
FULFILMENT_OBSERVED
REMEDIATION_REQUIRED
FINAL_RESULT_RECORDED
```

每个事件至少保留：

```text
event_id
previous_event_ref
occurred_at
event_type
actor_ref
authority_ref
transaction_object_ref
payment_ref
source_refs
policy_version
decision
reason_codes
```

轨迹只记录结构化事实，不记录或展示模型隐藏思维链。

P9-E UI 应把这条轨迹做成“证据播放器”：

```text
用户任务
→ Agent 动作
→ 事实来源
→ 订单与支付对象
→ 策略检查
→ 四态决策
→ 支付 / 查询 / 履约
→ 最终状态
```

### 4.4 评测驱动治理

ArbiterOS 论文中的 EDLC 与本项目当前方法高度一致：

```text
明确失败
→ 形成固定样本
→ 小范围修改
→ 同标准比较
→ 独立复核
→ 改善则保留，退化则回滚
```

本项目已有：

- Evaluator—Executor；
- 冻结合同；
- 原始证据；
- 独立重跑；
- M5；
- 固定回归集；
- 外部 PayBench / AP2 / WebShop。

建议在 P9-D 进一步补三项治理评测指标：

```text
Trace Completeness
    每个副作用是否都有前置授权、来源、策略和结果事件

Source Lineage Integrity
    是否发生低可信事实静默升级或覆盖高可信事实

Decision–Reason Consistency
    决策与 reason_codes 是否一致，能否解释真实阻断原因
```

保留现有核心指标：

```text
错误放行
错误拒绝
漏人工确认
过度确定而非 INDETERMINATE
禁止副作用
```

## 5. 吸收后的目标架构

不改变“一仓两域”，只增加四条横切治理线：

```text
外部协议 / Agent / WebShop / 商户 / PSP
                    ↓
                 Adapter
                    ↓
        Governed Action + Explicit Facts
            │                    │
            │                    └── Source Registry / Fact Lineage
            ↓
             Trust / Binding / State Facts
                    ↓
              Runtime Policy Gate
                    ↓
        ALLOW / DENY / CONFIRM / INDETERMINATE
                    ↓
             Controlled Action Seam
                    ↓
        Payment / Status / Fulfilment / Recovery
                    ↓
              Authoritative Trace
                 ↙          ↘
               M5          P9-E UI
```

四条横切线分别是：

```text
① Governed Action Contract
② Source Registry / Fact Lineage
③ Runtime Policy Enforcement
④ Authoritative Trace + Evaluation
```

## 6. 如何进入当前 P9 路线

### 当前：P9-C1

当前 P9-C1 已进入评估者复核，目标是支付和履约 Sidecar。

ArbiterOS 吸收方案不插入当前任务，不修改当前合同和路由。

P9-C1 继续完成：

```text
支付状态
→ 原交易查询
→ 异步状态冲突
→ 重复付款防护
→ 履约与最终任务状态
```

### P9-C2：吸收来源传播和动作治理

P9-C2 原计划是外部环境异常与攻击，正好用于验证：

```text
结账前涨价
商品 / 选项变化
payee / merchant 变化
页面提示注入
不必要个人信息请求
```

建议将 P9-C2 从“增加攻击案例”提升为：

> **支付动作契约 + 事实来源传播 + Trust Boundary 的系统性验证。**

P9-C2 的核心假设：

```text
外部网页或 LLM 产生的新事实
不能静默升级为用户确认或协议验证事实
也不能直接触发支付副作用
```

### P9-D：吸收 EDLC 和治理评测

P9-D 不只比较任务是否完成，还比较治理质量：

```text
原始 WebShop reward
+ 任务完成率
+ 错误购买率
+ 错误拒绝率
+ 漏确认率
+ 重复付款率
+ 禁止副作用
+ 轨迹完整度
+ 来源传播完整度
+ 决策原因一致性
```

新失败必须沉淀为固定治理样本，而不是只写一份分析结论。

### P9-E：吸收权威轨迹可视化

P9-E 继续遵循已冻结原则：

```text
轨迹 JSON = 原始证据
治理内核 = 决策与状态来源
UI = 证据播放器
```

增加两类展示：

```text
来源传播
    网页事实 → Agent 派生 → 当前有效可信度

策略执行
    哪条 Policy 在哪个动作前给出了什么决策与原因
```

UI 不重新计算政策，也不通过前端猜测为什么停止。

## 7. 后续可选的 ArbiterOS 外部对比实验

等 P9-E 完成以后，可以考虑一个独立外部实验，而不是核心依赖：

```text
通用购物 Agent
        ↓ 通过 ArbiterOS OpenAI-compatible endpoint
ArbiterOS 通用治理轨迹
        ↓ Adapter
本项目支付领域 Governed Action / Facts
        ↓
P1—P4 + Payment Lifecycle
```

实验要回答：

```text
ArbiterOS 能否拦截通用工具和提示注入风险？
本项目能否继续识别授权、订单、支付和状态层面的领域风险？
两者的轨迹能否映射？
通用治理与支付领域治理各自解决了什么？
```

正确定位：

```text
ArbiterOS = 外部通用治理运行时 / 测试输入来源
本项目 = 支付领域可信控制面与评测实验室
```

它与 AP2、PayBench、WebShop 类似，是外部验证对象，不成为本项目唯一运行底座。

## 8. 暂时不要吸收的内容

### 8.1 不直接引入 LiteLLM 代理层

当前项目主要验证支付领域能力，不需要为了使用 ArbiterOS 而改造模型路由、API Key 和运行环境。

只有出现真实通用 Agent Runtime 对接需求时，再做独立实验。

### 8.2 不复制完整 ACF 指令集

完整 ACF 覆盖认知、记忆、元认知和通用工具执行。

本项目只需要支付相关动作子集。过早复制完整指令集会把项目扩成通用 Agent OS。

### 8.3 不把 taint 标签直接当业务裁决

```text
WEB_UNTRUSTED
```

只是一项来源事实，不自动等于 `DENY`。

支付域仍需结合：

```text
事实路径
关键字段
授权范围
对象变化
当前动作
人工确认策略
```

决定 `ALLOW / DENY / CONFIRMATION_REQUIRED / INDETERMINATE`。

### 8.4 不直接引入 Langfuse UI

P9-E 已有明确的支付轨迹教学目标。Langfuse 可以作为未来开发者观测参考，但不应替代面向支付业务的轨迹 UI。

### 8.5 不吸收自演化政策

当前必须坚持：

```text
冻结 Policy
→ 固定回归
→ 独立评估
→ 人工批准变更
```

在支付领域，政策自行演化会破坏可审计性和授权边界。

### 8.6 不使用项目宣传指标作为验收依据

ArbiterOS 仓库当前列出多个安全评测提升结果，但其 README 也说明这些主要是 headline outcomes，不是独立完整的复现实验包。

本项目只把官方代码和机制作为参考，任何吸收能力仍必须由本地固定测试、外部挑战和独立复核证明。

## 9. 建议的执行顺序

```text
当前
P9-C1 独立复核
        ↓
P9-C2-A 支付动作契约
        ↓
P9-C2-B Source Lineage / Taint Propagation
        ↓
P9-C2-C 外部异常与提示注入组合测试
        ↓
P9-D 治理评测指标 + Golden Failure Set
        ↓
P9-E 权威轨迹播放器
        ↓
可选 P10 ArbiterOS 外部 Runtime 对比接入
```

每一步都必须遵循：

```text
一个能力假设
→ 一个最小领域变化
→ 一个真实消费者
→ 正向 + 负向测试
→ M5 / 全量回归
→ 独立复核
```

## 10. 当前正式判断

### 已经具备，不重复建设

```text
Runtime Gate
四态决策
副作用前拦截
SourceType
ContextPolicyFact
RuntimeGateRecord
ReplayEvent
M5
Evaluator—Executor
```

### 值得直接吸收

```text
支付动作统一契约
事实来源传播 / 派生关系
权威轨迹统一事件流
轨迹完整度与原因一致性评测
```

### 后置吸收

```text
OpenAI-compatible Runtime Proxy
Langfuse 观测
通用 Agent 指令集
ArbiterOS Trace Adapter
```

### 明确不吸收

```text
用通用治理替代支付业务规则
把来源标签直接当业务决策
自演化支付政策
为了框架接入改造当前基础环境
把外部 Benchmark 宣传数字当本项目验收结果
```

## 11. 一句话结论

> **ArbiterOS 对本项目最有价值的不是提供一套现成代码，而是进一步确认：Agentic Payment Trust Lab 应把每个支付动作转换成有身份、有授权、有对象绑定、有事实来源、有政策裁决、有权威轨迹的受治理执行；而不是让 Agent 的自然语言或工具调用直接触达支付副作用。**

## 12. 外部来源

- ArbiterOS 官方仓库：`https://github.com/cure-lab/ArbiterOS`
- 原始论文：`https://arxiv.org/html/2510.13857v1`

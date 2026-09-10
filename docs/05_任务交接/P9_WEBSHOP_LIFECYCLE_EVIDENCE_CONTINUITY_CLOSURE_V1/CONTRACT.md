# Frozen Task Contract

Task ID: `P9-WEBSHOP-LIFECYCLE-EVIDENCE-CONTINUITY-CLOSURE-V1`  
Task name: WebShop Lifecycle Evidence Continuity Closure  
Task kind: `capability_experiment`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `9e6818d2efcc5a6a2a3a8a3d3d2db2ea11189637`  
Validation plan file: `docs/05_任务交接/P9_WEBSHOP_LIFECYCLE_EVIDENCE_CONTINUITY_CLOSURE_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-10-r30`  
Active bottleneck: `B-12`  
Hypothesis: `H-20`  
Dispatch: `SINGLE`  
Metric baseline: H-18 same-journey lifecycle `semantic=4/4`、`continuity=1/4`。  
Estimated affected scope: 当前 3 个失败分支全部属于同一 Evidence / Accountability（证据 / 问责）连续性缺口：J03 缺 Trace Profile（轨迹配置档），J02/J04 的既有 extension event（扩展事件）缺 Action Origin mapping（动作来源映射）。  
Expected project impact: 不改变支付生命周期业务语义，直接把同一冻结 journey 的 evidence continuity（证据连续性）从 `1/4 → 4/4`。  
Rollback condition: 需要修改 Payment / Recovery / Finality / Conflict / Lifecycle / Remediation、Trace Toolkit、Trace schema/validator/consumer，或需要 Case 专用分支，或 semantic/安全守护线退化。

H-18 Evaluator L3 已独立确认：

```text
J01 SUCCESS + FULFILLED                continuity PASS
J02 UNKNOWN → QUERY SUCCEEDED          Trace VALID; first_breakpoint=ACTION_ORIGIN_PROJECTABLE
J03 PAYMENT SUCCEEDED + FULFILL FAILED first_breakpoint=AUTHORITATIVE_TRACE_AVAILABLE
J04 QUERY SUCCEEDED / ASYNC FAILED     Trace VALID; first_breakpoint=ACTION_ORIGIN_PROJECTABLE
semantic=4/4
continuity=1/4
real side effects=0
```

H-19 原计划只补 J03 profile，在 Executor 开始前被 `SUPERSEDED_BEFORE_EXECUTION`。原因不是 H-19 假设错误，而是任务粒度过细：J02/J03/J04 已经由 H-18 证明属于同一个 lifecycle evidence registry（生命周期证据登记）瓶颈，继续拆成多个微修包的项目价值低。

## Single objective / 单一目标

完成一个统一的 **Lifecycle Evidence Registry Coverage（生命周期证据登记覆盖）**：

```text
现有 lifecycle extension semantics
        ↓
Authoritative Trace extension event
        ↓
Action Origin closed classification
        ↓
Same-Journey Evidence Continuity
```

只补齐现有登记面的缺口，不重写任何生命周期业务逻辑：

1. `SIDECAR_TRACE_PROFILES` 增加一个通用 failed-fulfilment（失败履约）profile，使 J03 进入现有 `FULFILMENT_OUTCOME_RECORDED` Trace 路径；
2. `_TRACE_ORIGIN_BY_EVENT_ROLE` 增加现有 `RECOVERY_OUTCOME_RECORDED / RECOVERY_OUTCOME` 与 `STATUS_CONFLICT_RECORDED / STATUS_CONFLICT_FACT` 两个 mapping，使 J02/J04 的既有 Trace 扩展事件进入现有 Action Origin 闭集。

## Principal change / 唯一主要变化

唯一 principal change（主要变化）定义为：

> **补齐现有生命周期扩展事件在 Evidence Registry（证据登记机制）中的声明式覆盖。**

它允许修改两个已有 registry surface（登记面），但不允许增加第二套机制：

- Trace profile registry（轨迹配置登记）：补失败履约这一缺失生命周期形态；
- Action Origin event-role registry（事件角色来源登记）：补 recovery / status-conflict 两个已经存在于 Trace 中、但尚未分类的扩展事件。

不是三个 Case 各打一块补丁。产品代码不得出现 `J02/J03/J04`、H-18 case id、固定 order/request/payment、ASIN 或金额条件。

## Frozen architecture boundary / 冻结架构边界

允许改变：

- `src/agentic_payment_experiment/webshop_sidecar_trace_profiles.py`
- `src/agentic_payment_experiment/action_origin.py`
- 与上述两个 registry 直接对应的 focused tests（专项测试）

必须保持冻结：

- `src/agentic_payment_experiment/webshop_sidecar_trace_toolkit.py`
- `src/agentic_payment_experiment/webshop_payment_sidecar.py`
- `src/agentic_payment_experiment/payment_recovery.py`
- `src/agentic_payment_experiment/payment_finality.py`
- `src/agentic_payment_experiment/payment_status_conflict.py`
- `src/agentic_payment_experiment/lifecycle.py`
- `src/agentic_payment_experiment/remediation.py`
- `src/agentic_payment_experiment/authoritative_trace.py`
- Authoritative Trace consumer/player
- H-17/H-18 runner、matrix、parent/context、evaluator checks

## Origin semantics / 来源分类语义

继续使用现有五类 `ActionOrigin`，不得新增第六类：

```text
USER_AUTHORITY
AGENT_DECISION
RUNTIME_DECISION
EXTERNAL_FACT
EXECUTION_RESULT
```

新增两个 event-role mapping 的冻结语义：

- `RECOVERY_OUTCOME_RECORDED / RECOVERY_OUTCOME` → `EXECUTION_RESULT`：这是支付恢复处理得到的结果事实；
- `STATUS_CONFLICT_RECORDED / STATUS_CONFLICT_FACT` → `EXTERNAL_FACT`：这是 query / async 两个外部状态声明冲突后形成的状态事实，不得伪装成用户/Agent/Runtime 决策。

J03 继续复用既有：

- `FULFILMENT_OUTCOME_RECORDED / FULFILMENT_OUTCOME` → `EXECUTION_RESULT`。

## Acceptance criteria / 验收标准

### AC-01 — Evidence registry boundary remains narrow

- 只修改两个 product registry file（产品登记文件）及直接测试；
- 所有冻结 Payment / Recovery / Finality / Conflict / Lifecycle / Remediation / Trace Toolkit / Trace validator 文件 hash 不变；
- H-17/H-18 measurement contract（测量合同）不变；
- 不新增网络、浏览器、API、真实 Buy Now、真实支付、真实履约或依赖安装。

### AC-02 — Generic failed-fulfilment Trace profile

- `SIDECAR_TRACE_PROFILES` 从 3 个增加到恰好 4 个；
- T01/T09/T12 三个既有 profile 的 identity/属性保持不变；
- 第 4 个 profile 是通用 `FULFILMENT` profile：payment initial/effective=`SUCCEEDED`，recovery/conflict=None，lifecycle fulfillment=`FAILED`、task=`FAILED`、remediation=`REQUIRED`；
- 不绑定 H-18 Case、商品、订单或金额；
- 现有 Toolkit 无需增加新的 if/branch/schema 即可消费。

### AC-03 — Existing lifecycle extension events enter Action Origin closed set

- `ActionOrigin` enum 仍只有原五类；
- 原有 event-role mapping 全部保持原值；
- 新增且仅新增两个当前缺失 lifecycle mapping：
  - `RECOVERY_OUTCOME_RECORDED / RECOVERY_OUTCOME` → `EXECUTION_RESULT`；
  - `STATUS_CONFLICT_RECORDED / STATUS_CONFLICT_FACT` → `EXTERNAL_FACT`；
- 未知 event/role 仍 fail closed（失败关闭），不得增加 wildcard/default fallback（通配/默认回退）。

### AC-04 — Same-journey lifecycle evidence continuity closes 1/4 → 4/4

冻结 H-18 runner/matrix 重新执行，J01..J04 每个 repeat=`2`，必须得到：

```text
semantic matches = 4/4
branch continuity = 4/4
real side effects = 0
```

逐 Case：

- J01：继续 PASS；
- J02：Trace 继续 `VALID`，`ACTION_ORIGIN_PROJECTABLE=true`，`first_breakpoint=null`；
- J03：Trace 从 unavailable → `AVAILABLE + VALID`，Order/Request/Payment refs 连续，Action Origin 可投影，`first_breakpoint=null`；
- J04：Trace 继续 `VALID`，`ACTION_ORIGIN_PROJECTABLE=true`，`first_breakpoint=null`。

任何 Case `semantic_match=false` 均视为回归，而不是可接受的“证据层变化”。

### AC-05 — Classification and fail-closed regressions

Focused tests 必须至少证明：

- recovery extension event 被投影为 `EXECUTION_RESULT`；
- status-conflict extension event 被投影为 `EXTERNAL_FACT`；
- failed-fulfilment extension 继续为 `EXECUTION_RESULT`；
- 既有五类 origin 的代表事件不退化；
- 未知 lifecycle event/role 继续抛出 `ActionOriginError`；
- profile selector（配置选择器）对不匹配或多匹配仍 fail closed，不允许“随便选第一个”。

### AC-06 — Project guardrails

- focused lifecycle/trace/origin tests PASS；
- `run_experiment.py` 正式入口 PASS；
- project-impact baseline repeat=`3`、all identical；
- Product Trace=`9/12`、GESR=`8/12`、callback=`12/12`、duplicate/forbidden side effect=`0/12`、unsafe allow=`0/5` 不退化；
- full unittest discovery 零失败；
- real Buy Now/payment/fulfillment/network side effects=`0`。

### AC-07 — v2.2 evidence and handoff

- frozen L2 `7/7` mandatory checks PASS；
- REPORT 映射 AC-01..07 → EV；
- REPORT 明确 Before=`semantic 4/4, continuity 1/4`，After=`semantic 4/4, continuity 4/4` 或如实报告失败；
- REPORT 记录 changed files、最终 hashes、origin mappings、profile 数量、guardrails、任何偏差和 stop condition；
- workflow validator `OK` 后才能 `SUBMITTED_FOR_REVIEW`；
- Executor 不得自行给 Task `PASS` / Project `IMPROVED`。

## Allowed scope / 允许修改

Product code：

- `src/agentic_payment_experiment/webshop_sidecar_trace_profiles.py`
- `src/agentic_payment_experiment/action_origin.py`

Focused tests：

- `tests/test_webshop_sidecar_trace_toolkit.py`
- `tests/test_webshop_payment_sidecar.py`
- `tests/test_action_origin.py`

Task-owned outputs：

- `docs/05_任务交接/P9_WEBSHOP_LIFECYCLE_EVIDENCE_CONTINUITY_CLOSURE_V1/REPORT.md`
- `docs/05_任务交接/P9_WEBSHOP_LIFECYCLE_EVIDENCE_CONTINUITY_CLOSURE_V1/evidence/**`

Evaluator-owned frozen files 全部只读：

- 本任务 `CONTRACT.md`
- 本任务 `VALIDATION_PLAN.yaml`
- 本任务 `evaluator_checks/**`
- `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`
- `CURRENT.md`
- H-17/H-18 artifacts（工件）

## Exclusions / 明确排除

- 不修改 Payment Sidecar / Recovery / Finality / Conflict / Lifecycle / Remediation；
- 不修改 Sidecar Trace Toolkit；
- 不修改 Authoritative Trace schema / builder core / validator / consumer / player；
- 不新增 ActionOrigin 类型；
- 不增加 wildcard/default origin mapping；
- 不改 H-18 runner、matrix、expected semantics、result audit；
- 不用 `J02/J03/J04` 或任何真实 fixture id 写产品特例；
- 不顺手修 B-04 intent/option、B-05 data minimization、B-06 real identity；
- 不执行真实 Buy Now/payment/order/fulfillment、外部 API/network；
- 不安装依赖或修改环境；
- 不 commit、push、history rewrite。

## Validation plan / 验证计划

Frozen plan: `docs/05_任务交接/P9_WEBSHOP_LIFECYCLE_EVIDENCE_CONTINUITY_CLOSURE_V1/VALIDATION_PLAN.yaml`

| VP | Check | AC |
|---|---|---|
| VP-01 | frozen architecture + registry semantics audit | AC-01,02,03,05,07 |
| VP-02 | frozen H-18 same-journey lifecycle rerun | AC-04,06 |
| VP-03 | evaluator exact result audit `semantic=4/4, continuity=4/4` | AC-04,06 |
| VP-04 | focused profile/sidecar/lifecycle/origin/trace regressions | AC-02,03,05,06 |
| VP-05 | formal experiment entrypoint | AC-06 |
| VP-06 | project-impact baseline repeat=3 | AC-06 |
| VP-07 | full unittest discovery | AC-06,07 |

## Stop conditions / 停止条件

出现任一情况立即停止并交回 Evaluator：

- 需要修改任何冻结业务语义文件或 Trace Toolkit；
- 需要新增第六类 ActionOrigin；
- 需要 wildcard/default mapping 才能通过；
- 需要 Case 专用条件；
- semantic 从 `4/4` 下降；
- continuity 无法在本统一 registry hypothesis 下达到 `4/4`；
- J01 或既有 T01/T09/T12 trace 行为退化；
- 任何安全/副作用守护线退化。

## Bounded Executor loop / 有界执行循环

- max complete implementation→L2 cycles: `3`；
- L1 可重复运行 focused tests、source audit 和 H-18 lifecycle runner；
- 完整 L2 最多 3 次，且每轮必须保持同一个 H-20 hypothesis、同一个 principal change、同一 frozen measurement boundary；
- 如果失败需要越出两个 registry surface，立即 `BLOCKED`，不得转为开放式重构；
- 不因其他 WATCH 项目仍有 gap 而扩大本包。

## Expected project impact / 预期项目影响

Measured baseline: H-18 `semantic=4/4`、`continuity=1/4`。  
Expected after: `semantic=4/4`、`continuity=4/4`。  
Expected project impact verdict if reproduced: `IMPROVED`。  
Cost: 低到中；本地两个小 registry 修改 + focused/full regression，无外部 API/支付成本。  
Complexity budget: 不新增业务状态、不新增 Trace schema、不新增 Origin enum，只补已有扩展类型的声明式登记。  
Iteration value: 如果 `4/4` 达成，本方向应 `STOP`，下一步进入 Payment / Finality / Fulfillment / Recovery closure 或 Accountability / Replay consumer，而不是继续扩更多 origin 字段。

## Authorization / 授权

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false

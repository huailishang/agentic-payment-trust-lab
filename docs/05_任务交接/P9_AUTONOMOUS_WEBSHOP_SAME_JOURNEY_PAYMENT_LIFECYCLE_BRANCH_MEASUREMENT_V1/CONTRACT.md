# Frozen Task Contract

Task ID: `P9-AUTONOMOUS-WEBSHOP-SAME-JOURNEY-PAYMENT-LIFECYCLE-BRANCH-MEASUREMENT-V1`  
Task name: Same-Journey Payment Lifecycle Branch Measurement  
Task kind: `one_off`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `57ded7bb2fb0ca830748b35b857a8d07624fe3d4`  
Validation plan file: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_PAYMENT_LIFECYCLE_BRANCH_MEASUREMENT_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-06-r28`  
Active bottleneck: `B-12`  
Hypothesis: `H-18`

H-17 已由 Executor L2 与 Evaluator L3 独立证明：

```text
Action Origin = 5/5
same-journey responsibility correlation = 8/8
trace = VALID
real side effects = 0
```

因此 B-11 “Action Origin / Responsibility Trace” 可以阶段性关闭。下一主线不再继续扩 Action Origin 字段，也不回到 WebShop intent/option 细节，而是进入支付生命周期：

> 同一个已经验收的 autonomous WebShop pre-payment journey，在不同 payment state / recovery / fulfillment / conflict 分支下，是否仍能保持同一 Order / Request / Payment 责任链和可信 Trace？

现有组件已经分别具有 Payment Recovery、Payment Query Finality、Status Conflict、Lifecycle、Remediation、Sidecar、Authoritative Trace 等能力；当前未知量是它们在**同一 autonomous journey** 上组合后是否仍连续。

## Measurement nature / 测量性质

本任务是 measurement-only one_off（只测量一次性任务），不预设需要产品修复。

Task PASS 的含义是：

```text
4/4 frozen branches 都真实执行
→ 每个 branch repeat=2 且确定性一致
→ 现有组件语义与 continuity 结果如实记录
→ guardrail=0
→ evaluator audit 可机械复核
```

**Task PASS 不要求 branch continuity = 4/4。**

如果某个 case 出现 `semantic_match=false` 或 `continuity_pass=false`，这是项目级 finding（发现），不是 Executor 应现场修复的任务失败。Evaluator 再根据重复性、主线影响和失败位置决定下一 capability package。

## Frozen parent / 冻结父证据

H-17 accepted result：

- path: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_BASELINE_LIFECYCLE_REPAIR_V1/evidence/SAME_JOURNEY_RESULT.json`
- SHA-256: `9c611dfe121d970569ea41d1e1831d0f829da307c61a6839996846ca893545fc`
- session: `10`
- order: `webshop-order-c3345ef469f6d13dab2688e5`
- request: `webshop-request-096ba6496e0c73b413933ae1`
- payment: `same-journey-payment-webshop-request-096ba6496e0c73b413933ae1`
- product: `B099231V35 / orange / 16.79`

H-17 explicit experiment context：

- path: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_BASELINE_LIFECYCLE_REPAIR_V1/evaluator_fixtures/SAME_JOURNEY_EXPERIMENT_CONTEXT.json`
- SHA-256: `6a52d7cb77a1186209a88ab877560a352089b818e8c898977e1e0148dc94b3d1`

Frozen lifecycle matrix：

- path: `evaluator_fixtures/LIFECYCLE_BRANCH_MATRIX.json`
- SHA-256: `c6f6c22c7c2ff637950b2611cb99ef6762f76eff0ee52def90ecf707e6839c7d`
- repeat per case=`2`

## Four frozen branches / 四个冻结分支

四个 Case 是同一个 pre-payment journey 的四个**互斥 counterfactual branch（反事实分支）**，不是一笔真实交易同时发生四种结果。

### J01 — success + fulfilled

```text
payment = SUCCEEDED
fulfillment = SUCCEEDED
expected task = SUCCEEDED
remediation = NOT_REQUIRED
retry = false
```

### J02 — UNKNOWN → trusted query SUCCEEDED

```text
initial payment = UNKNOWN
trusted query = SUCCEEDED
fulfillment = SUCCEEDED
expected recovery = RECOVERED
effective payment = SUCCEEDED
query finality = QUERY_CONFIRMED / payment-status terminal only
task = SUCCEEDED
retry = false
```

Payment Query Finality 仍不得声称：business success、fulfillment、user task success、reconciliation、settlement 或 legal finality。

### J03 — payment succeeded + fulfillment failed

```text
payment = SUCCEEDED
fulfillment = FAILED
failure_code = merchant_did_not_fulfil
expected task = FAILED
remediation = REQUIRED
retry = false
```

### J04 — query / async terminal conflict

```text
initial payment = UNKNOWN
query = SUCCEEDED
async = FAILED
fulfillment = SUCCEEDED
expected query recovery = RECOVERED
expected status conflict = CONFLICT
effective payment = UNKNOWN
task = UNKNOWN
remediation = REQUIRED
retry = false
```

这里 `PaymentQueryFinalityFact` 可以描述“query 自身确认了 SUCCEEDED”，但整体 transaction state 必须继续由 conflict/lifecycle 表示为 UNKNOWN；不得把 query-confirmed payment status 上升成最终业务成功。

## Single objective / 单一目标

Executor 只新增一个 integration/measurement runner：

`scripts/validation/webshop/run_same_journey_lifecycle_branches.py`

它必须从 H-17 accepted parent result 和 explicit experiment context 重建同一 pre-payment Order / Request / Runtime Gate context，然后对 J01..J04 各运行 `repeat=2` 的 caller-supplied offline lifecycle facts。

必须消费现有：

- `assess_webshop_payment_fulfilment`
- `derive_payment_query_finality`（仅 query case）
- `validate_product_authoritative_trace`
- `consume_authoritative_trace`
- `project_authoritative_trace_origins`
- H-17 / H-16 existing same-journey helper or equivalent frozen logic

不得复制 payment/recovery/finality/conflict/lifecycle/trace 决策逻辑到 runner。

## Output contract / 输出合同

输出：

`evidence/LIFECYCLE_BRANCH_RESULT.json`

schema：`same-journey-payment-lifecycle-branches/v1`

顶层至少包含：

```text
parent
repeat_per_case
cases[4]
summary
guardrails
```

每个 case 必须包含：

```text
case_id
input
measurement_complete
repeat_identical
run_digests[2]
observed_semantics
semantic_match
refs
trace
continuity
continuity_pass
first_breakpoint
```

`refs` 至少包含 `session_id / order_id / request_id / payment_id / payment_order_id / payment_request_id`。这些字段记录**实际观察值**，即使和 parent 不一致也必须如实写出，不得先改成 parent 值再比较。

`trace` 至少包含：

```text
available
validation_status
order_id
request_id
payment_id
action_origin_projectable
action_origin_types
```

Trace 不可用或 projection 失败时，对应字段可为 `null / false / []`，但不得省略。

`observed_semantics` 必须来自现有 product objects / to_dict / enum values，不得直接复制 frozen expected 值当作“观察结果”。

`continuity` 必须精确包含 8 个检查：

```text
PARENT_JOURNEY_IDENTITY
ORDER_REQUEST_CONTINUITY
PAYMENT_ORDER_REQUEST_CONTINUITY
SEMANTIC_EXPECTATION_MATCH
AUTHORITATIVE_TRACE_AVAILABLE
AUTHORITATIVE_TRACE_VALID
TRACE_ORDER_REQUEST_PAYMENT_CONTINUITY
ACTION_ORIGIN_PROJECTABLE
```

`continuity_pass = all(continuity.values())`。

`first_breakpoint` 是上述固定顺序中第一个 `false` 的检查名；若全 true，则为 `null`。

## Acceptance criteria / 验收标准

### AC-01 — Protected parent and product snapshot

- H-17 result hash 不变；
- H-17 explicit experiment context hash 不变；
- shopping policy、same-journey runner、Sidecar、Recovery、Finality、Conflict、Lifecycle、Remediation、Trace、Action Origin hash 全部保持冻结；
- 新 runner 不含 network/browser/real Buy Now 依赖。

### AC-02 — 4/4 cases fully measured and deterministic

- case IDs 精确等于 J01..J04；
- 每 case repeat=`2`；
- `measurement_complete=true`；
- 两次 run digest 完全一致；
- frozen inputs 不漂移；
- 输出不因 branch capability fail 而省略 case。

### AC-03 — Existing semantics are observed, not patched

Runner 必须真实调用现有 Sidecar / Recovery / Finality / Conflict / Lifecycle 能力。

Evaluator audit 根据 frozen `expected_semantics` 计算 `semantic_match`：

- semantic match 可 true 或 false；
- false 是项目 finding，不允许在本包修改产品；
- Executor 不得改 matrix 或产品去提高 match 数量。

### AC-04 — Same-journey continuity is measured, not assumed

每 case 都要真实测量：

- parent identity；
- Order / Request refs；
- Payment → Order/Request refs；
- authoritative trace 是否存在；
- trace 是否 VALID；
- trace refs 是否仍是同一 Order/Request/Payment；
- Action Origin 是否可以从该 branch trace 投影。

若某一层失败：

- `continuity_pass=false`；
- `first_breakpoint` 如实记录；
- Runner 仍应完成该 case 的可获得证据，不得伪造后续 PASS。

### AC-05 — Guardrails and regressions

- real WebShop Buy Now=`0`；
- real payment execution=`0`；
- real fulfillment execution=`0`；
- external network=`0`；
- 四个 counterfactual branches 不得表述为四笔真实交易；
- focused Payment/Recovery/Finality/Conflict/Lifecycle/Trace/ActionOrigin tests PASS；
- formal entrypoint PASS；
- project-impact baseline repeat=3 一致；
- full unittest 无新增失败。

### AC-06 — v2.2 handoff

- frozen L2 `7/7` mandatory checks PASS；
- REPORT 映射 AC-01..06 → EV；
- Impact comparison 必须写：
  - Before: H-17 happy-path branch continuity only；
  - After: H-18 `semantic matches X/4`、`branch continuity Y/4`；
  - 每个 FAIL case 的 first breakpoint；
  - Guardrail result；
  - Scope caveat；
- Executor status=`SUBMITTED_FOR_REVIEW`；
- Executor 不对发现的产品断点现场修复。

## Allowed scope / 允许范围

Executor 只允许新增/修改：

- `scripts/validation/webshop/run_same_journey_lifecycle_branches.py`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_PAYMENT_LIFECYCLE_BRANCH_MEASUREMENT_V1/REPORT.md`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_PAYMENT_LIFECYCLE_BRANCH_MEASUREMENT_V1/evidence/**`

## Exclusions / 明确排除

禁止：

- 修改 WebShop Agent policy；
- 修改 H-16/H-17 runners；
- 修改 Adapter / Runtime Gate；
- 修改 Sidecar / Recovery / Finality / Conflict / Lifecycle / Remediation；
- 修改 Authoritative Trace / Consumer / Action Origin；
- 修改 H-17 accepted result / current baseline / experiment context；
- 修改 H-18 matrix / Contract / Validation Plan / evaluator checks；
- 为了让 `Y/4` 变高而补产品代码；
- real Buy Now / payment / order / fulfillment；
- external API/network；
- dependency/environment mutation；
- commit / push / history rewrite。

## Bounded execution / 有界执行

- runner 实现最多 `2` 次 L1 mechanical repair；
- 完整 frozen L2 最多 `1` 次；
- 不允许“多跑直到 Y/4 变高”；
- 产品 branch continuity failure 不触发 Executor 修复；
- 若 runner 无法在不改产品的条件下完成某 case，必须把该 case 记录为 measurement failure / first breakpoint，而不是扩大 scope。

## Stop conditions / 停止条件

出现以下情况停止并交回 Evaluator：

- parent H-17 hash 漂移；
- protected product hash 漂移；
- 需要改产品才能完成 runner；
- 需要真实交易副作用；
- 需要外部网络/API；
- frozen matrix / checker / plan 被要求修改；
- 无法区分 counterfactual branch 与真实交易事实。

## Authorization / 授权

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- environment_creation: false
- local_offline_measurement: true
- real_Buy_Now: false
- real_payment_or_order: false
- real_fulfillment: false

## Executor instructions / 执行者说明

```text
read CURRENT / Contract / Matrix / Validation Plan / evaluator checks
→ 新增 measurement-only lifecycle branch runner
→ 从 H-17 same journey 重建同一 pre-payment context
→ J01..J04 each ×2
→ 真实调用现有 Sidecar / Recovery / Finality / Conflict / Trace / Origin
→ 不修任何 product failure
→ 写 LIFECYCLE_BRANCH_RESULT.json
→ frozen L2 7/7
→ REPORT：semantic X/4 + continuity Y/4 + first breakpoints
→ workflow validator
→ SUBMITTED_FOR_REVIEW
```

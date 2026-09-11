# Frozen Task Contract

Task ID: `P9-AUTONOMOUS-WEBSHOP-SAME-JOURNEY-REMEDIATION-CLOSURE-MEASUREMENT-V1`  
Task name: Same-Journey Remediation / Closure Measurement  
Task kind: `one_off`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `52b135bd32c938291cca10c43bf9eeba0e7d8977`  
Validation plan file: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_REMEDIATION_CLOSURE_MEASUREMENT_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-11-r31`  
Active bottleneck: `B-13`  
Hypothesis: `H-21`  
Dispatch: `SINGLE`

H-20 Evaluator(评估者) 已独立裁决：

```text
Task = PASS
Project impact = IMPROVED
L3 = 7/7 PASS
semantic = 4/4
same-journey continuity = 4/4
Product Trace = 10/12
GESR = 9/12
full unittest = 658/658
real side effects = 0
```

因此 Lifecycle Evidence Registry（生命周期证据登记）方向停止。当前第一未知量下移到 L8 Remediation（补救 / 退款 / 争议）→ L9 Closure（结束归档）：已有组件语义是否能在 H-20 已闭合的同一 autonomous journey（自主旅程）中继续保持原交易绑定、责任证据和最终状态连续。

## Measurement nature / 测量性质

本任务是 **measurement-only one_off（只测量一次性任务）**。

Task PASS 的含义不是 5 个补救分支必须全部 continuity PASS，而是：

```text
5/5 frozen branches 都真实执行
→ 每个 branch repeat=2 且确定性一致
→ assess_remediation 的现有语义如实记录
→ original-transaction binding 如实记录
→ Trace / Action Origin / Closure continuity 如实记录
→ first breakpoint 可机械重算
→ project guardrails 不退化
```

如果某个 branch 出现 `semantic_match=false` 或 `continuity_pass=false`，这是项目级 finding（发现），不是 Executor 应在本任务现场修复的任务失败。Evaluator 将根据重复断点决定后续 capability hypothesis（能力假设）。

## Accepted parent / 已验收父证据

H-20 accepted lifecycle result：

- path: `docs/05_任务交接/P9_WEBSHOP_LIFECYCLE_EVIDENCE_CONTINUITY_CLOSURE_V1/evidence/H20_LIFECYCLE_BRANCH_RESULT.json`
- SHA-256: `312bcef7e3ff4c92b2cf60ed898ac9f4d384ef7cf4639a2a66cce8814e3f3455`
- parent branch: `J03_PAYMENT_SUCCEEDED_FULFILLMENT_FAILED`
- parent semantic: payment=`SUCCEEDED`、fulfillment=`FAILED`、task=`FAILED`、remediation=`REQUIRED`
- parent continuity: PASS

H-20 accepted product snapshot is uncommitted but frozen by exact hashes:

```text
src/agentic_payment_experiment/action_origin.py
  61d87e1e87aee585580c10710e99be566fc7af6d2d1c72545a9b70d83ce8ddd6

src/agentic_payment_experiment/webshop_sidecar_trace_profiles.py
  7b9c390059ab11e06ecca2722d19e5284ffe9ec7cbf92c8438c77daf6375942f
```

The H-20 REVIEW is the authoritative acceptance record. `config/runtime-capability-profile.json` and `config/runtime-capability-manifests.json` are concurrent Platform work that appeared after H-20 submission; they are outside H-21 scope and must not be modified, reverted, or claimed as H-21 evidence.

## Frozen remediation matrix / 冻结补救矩阵

Path:

`docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_REMEDIATION_CLOSURE_MEASUREMENT_V1/evaluator_fixtures/REMEDIATION_CLOSURE_MATRIX.json`

SHA-256:

`abe7a75d32d6833f5289160c1477d18b6265aae18476c3e1b509989373f26acc`

五个分支：

1. `R01_FULL_REFUND`：全额退款成功，原交易绑定正确；
2. `R02_PARTIAL_REFUND`：部分退款成功，仍需后续补救；
3. `R03_DISPUTE_OPEN`：争议处于 OPEN；
4. `R04_DISPUTE_RESOLVED_OUTCOME_UNVERIFIED`：争议已结案，但经济结果尚未验证；
5. `R05_REFUND_PAYMENT_BINDING_MISMATCH`：退款引用错误 payment，必须 fail closed（失败关闭）。

这些是同一 J03 parent journey 的五个互斥 counterfactual branches（反事实分支），不是同一交易同时发生五种补救。

## Single objective / 单一目标

Executor 只新增一个 integration/measurement runner（集成 / 测量运行器）：

`scripts/validation/webshop/run_same_journey_remediation_closure.py`

它必须从 H-20 accepted result 与既有 H-17 experiment context 重建同一 Order / Request / Payment / failed-fulfilment journey，然后根据冻结 matrix 构造 caller-supplied offline RefundRecord / DisputeRecord（调用方提供的离线退款 / 争议事实），调用现有产品能力：

- `assess_remediation`；
- `verify_original_transaction` 或产品已有等价 original-transaction binding（原交易绑定）能力；
- 现有 Authoritative Trace（权威轨迹）构建/读取入口，如果产品当前能够消费 remediation outcome；
- `validate_product_authoritative_trace`；
- `project_authoritative_trace_origins`；
- 现有 lifecycle / sidecar objects，仅用于重建 H-20 parent，不复制其业务规则。

Runner 不得复制 `remediation.py`、original-transaction binding、Trace、Action Origin 或 closure 决策逻辑来“模拟通过”。产品当前没有的 Trace / Origin / Closure 证据必须如实记为 unavailable / false，而不是由 evaluator runner 合成后冒充产品证据。

## Output contract / 输出合同

输出：

`docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_REMEDIATION_CLOSURE_MEASUREMENT_V1/evidence/H21_REMEDIATION_CLOSURE_RESULT.json`

schema：`same-journey-remediation-closure-result/v1`

顶层至少包含：

```text
parent
matrix_sha256
repeat_per_case
cases[5]
summary
guardrails
```

每个 case 至少包含：

```text
case_id
input
measurement_complete
repeat_identical
run_digests[2]
observed_semantics
semantic_match
original_transaction_binding
refs
remediation_evidence
trace
closure
continuity
continuity_pass
first_breakpoint
```

### observed_semantics

必须来自现有产品对象，不得复制 matrix expected：

```text
task_status
remediation_status
next_action
refund_status
dispute_status
issue_codes
```

### original_transaction_binding

至少包含：

```text
observed_status
expected_status
expectation_match
reason_codes
payment_ref
order_ref
```

负例 R05 的 `INVALID` 是预期结果；不得把“必须 VALID”写死为 continuity 条件。

### remediation_evidence

至少记录产品 LifecycleResult 中真实存在的 refund/dispute evidence codes / observed refs；不得自行补造产品没有记录的证据。

### trace

至少包含：

```text
available
validation_status
product_observed
remediation_event_or_role_present
action_origin_projectable
action_origin_types
```

产品没有 remediation authoritative trace 时允许 `available=false`，这应成为 finding，而不是 Runner 失败。

### closure

至少包含：

```text
state_explicit
original_task_status
economic_remediation_status
case_ref
next_action
```

`state_explicit` 的定义仅为“当前产品对象能明确区分原始任务状态与经济补救状态，并给出 next_action/case_ref”；不得上升为法律最终性、清算最终性或监管结案证明。

### continuity

必须按 matrix 固定顺序精确包含 10 个布尔检查：

```text
PARENT_JOURNEY_IDENTITY
ORDER_REQUEST_PAYMENT_CONTINUITY
REMEDIATION_SEMANTIC_EXPECTATION_MATCH
ORIGINAL_TRANSACTION_BINDING_EXPECTATION_MATCH
REMEDIATION_EVIDENCE_PRESENT
AUTHORITATIVE_TRACE_AVAILABLE
AUTHORITATIVE_TRACE_VALID
TRACE_REMEDIATION_EVIDENCE_PRESENT
ACTION_ORIGIN_PROJECTABLE
CLOSURE_STATE_EXPLICIT
```

`continuity_pass = all(continuity.values())`。

`first_breakpoint` 是上述顺序第一个 false；若全 true 则为 null。

## Acceptance criteria / 验收标准

### AC-01 — Frozen parent and product snapshot

- H-20 result hash 保持；
- H-20 accepted `action_origin.py` / `webshop_sidecar_trace_profiles.py` hashes 保持；
- `remediation.py`、`lifecycle.py`、payment/recovery/finality/conflict、Sidecar Toolkit、Authoritative Trace、Action Origin 不得被 H-21 修改；
- concurrent Platform config 不属于 H-21 scope；
- runner 不含 network/browser/real refund/payment/dispute side effect。

### AC-02 — 5/5 cases fully measured and deterministic

- case IDs 精确等于 matrix 五项；
- 每 case repeat=`2`；
- `measurement_complete=true`；
- 两次 run digest 一致；
- frozen inputs 不漂移；
- 不因某个 continuity fail 而省略结果。

### AC-03 — Existing remediation semantics are observed, not patched

- Runner 真实调用 `assess_remediation`；
- semantic expected 由 evaluator matrix 冻结；
- `semantic_match` true/false 如实输出；
- 任何 false 均不得在 H-21 修改产品。

### AC-04 — Original transaction binding measured correctly

- R01/R02/R03/R04 的 expected binding=`VALID`；
- R05 的 expected binding=`INVALID`；
- `expectation_match` 必须比较 observed vs expected，而不是把 INVALID 一律视为任务失败；
- wrong payment/order refs 不得被 runner 修回 parent 值。

### AC-05 — Trace / Action Origin / Closure continuity measured, not assumed

- product-observed Trace 与 evaluator-constructed diagnostics 必须分离；
- remediation trace event/role 不存在时如实 false；
- Action Origin projection 失败时如实 false；
- closure 只证明技术状态显式，不声称 legal/settlement finality（法律/结算最终性）；
- first_breakpoint 可由 continuity 固定顺序机械重算。

### AC-06 — Project guardrails

- `tests.test_remediation` 与 original-transaction / lifecycle / trace / origin focused tests PASS；
- `run_experiment.py` 继续 `13/13 PASS`；
- project-impact baseline repeat=`3` all identical；
- Product Trace 不低于 `10/12`；
- GESR 不低于 `9/12`；
- callback=`12/12`；
- duplicate/forbidden side effect=`0/12`；
- unsafe allow=`0/5`；
- full unittest discovery 零失败；
- real payment/refund/dispute/network side effects=`0`。

### AC-07 — v2.2 handoff

- frozen L2 `7/7` mandatory checks PASS；
- REPORT 映射 AC-01..07 → EV；
- REPORT 列出 5 个 branch 的 semantic/binding/continuity/first_breakpoint；
- REPORT 不把 measurement finding 写成产品已修复；
- workflow validator OK 后才可 SUBMITTED_FOR_REVIEW；
- Executor 不得自行给 Project impact 或下一 capability change 下最终裁决。

## Allowed scope / 允许修改

Implementation / measurement：

- `scripts/validation/webshop/run_same_journey_remediation_closure.py`

Task-owned report/evidence：

- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_REMEDIATION_CLOSURE_MEASUREMENT_V1/REPORT.md`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_REMEDIATION_CLOSURE_MEASUREMENT_V1/evidence/**`

可新增 runner-focused test（仅当需要验证 runner 自身确定性/序列化，不得改产品）：

- `tests/test_same_journey_remediation_closure_measurement.py`

Evaluator-owned frozen files 全部只读：

- 本任务 `CONTRACT.md`
- 本任务 `VALIDATION_PLAN.yaml`
- `evaluator_fixtures/**`
- `evaluator_checks/**`
- `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`
- `CURRENT.md`
- H-20 accepted artifacts

## Exclusions / 明确排除

- 不修改 `src/**` 任何产品代码；
- 不修改 H-20/H-18 runner、matrix、accepted evidence；
- 不修改 project-impact runner/fixture；
- 不补 remediation Trace Profile / ActionOrigin mapping / consumer；
- 不增加 refund/dispute 业务状态或真实执行器；
- 不修改 concurrent Platform config；
- 不执行真实退款、争议、付款、Buy Now、履约、外部 API/network；
- 不安装依赖；
- 不 commit、push、history rewrite。

## Stop conditions / 停止条件

立即 BLOCKED 并交回 Evaluator，如果：

- 为完成测量必须修改 `src/**`；
- 需要改变 matrix expected 或 parent evidence；
- 需要 evaluator 合成 product Trace 才能让 continuity 通过；
- 任何项目安全守护线退化；
- runner 无法在不执行真实副作用的情况下测量；
- concurrent Platform work 与 H-21 修改发生文件冲突。

## Bounded Executor loop / 有界执行循环

- max complete implementation→L2 cycles: `3`；
- 可重复运行 runner-focused L1；
- 每次 material L2 必须保留结果；
- 不得因为 continuity 不满 5/5 而进入产品修复循环；
- 只要 measurement contract 完整、确定性、可审计，continuity failure 本身不阻止 Task PASS。

## Expected project impact / 预期项目影响

本任务是 measurement-only，所以预期 Project impact=`NOT_APPLICABLE`。

项目价值在于把未知量从“L8/L9 可能有问题”收敛为可重复的 first breakpoint。后续只有在至少一个可重复、可归并的共同断点被证明后，Evaluator 才创建 capability experiment。

## Authorization / 授权

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- real payment/refund/dispute: false

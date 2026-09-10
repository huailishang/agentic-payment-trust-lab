# Frozen Task Contract

Task ID: `P9-WEBSHOP-FULFILMENT-FAILED-AUTHORITATIVE-TRACE-PROFILE-V1`  
Task name: WebShop Fulfilment-Failed Authoritative Trace Profile  
Task kind: `capability_experiment`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `1a6d42d2eb84ca2bcb3c0c2c75b5b664d7b8901e`  
Validation plan file: `docs/05_任务交接/P9_WEBSHOP_FULFILMENT_FAILED_AUTHORITATIVE_TRACE_PROFILE_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-10-r29`  
Active bottleneck: `B-12`  
Hypothesis: `H-19`  
Dispatch: `SINGLE`  
Metric baseline: H-18 same-journey lifecycle `semantic=4/4`、`continuity=1/4`；J03 first breakpoint=`AUTHORITATIVE_TRACE_AVAILABLE`。  
Estimated affected scope: 当前 3 个失败分支中的 1 个（J03）在最上游 Trace availability（轨迹可用性）处断开；本包只处理该 1 个断点，不声称覆盖 J02/J04。  
Expected project impact: J03 从 Trace unavailable → `AVAILABLE + VALID`，H-18 branch continuity `1/4 → 2/4`；semantic `4/4`、J01、J02、J04 和全部项目安全守护线不退化。  
Rollback condition: 需要修改 Toolkit / Payment Sidecar / Lifecycle / Authoritative Trace validator / Action Origin 才能生成 J03 Trace，或者 J01/J02/J04 语义/断点发生非预期变化，或者任何安全守护线退化。

H-18 Evaluator L3 已独立确认：

```text
J01 SUCCESS + FULFILLED                continuity PASS
J02 UNKNOWN → QUERY SUCCEEDED          first_breakpoint=ACTION_ORIGIN_PROJECTABLE
J03 PAYMENT SUCCEEDED + FULFILL FAILED first_breakpoint=AUTHORITATIVE_TRACE_AVAILABLE
J04 QUERY SUCCEEDED / ASYNC FAILED     first_breakpoint=ACTION_ORIGIN_PROJECTABLE
semantic=4/4
continuity=1/4
real side effects=0
```

现有 `webshop_sidecar_trace_toolkit.py` 已支持 `FULFILMENT` extension（履约扩展事件），但 `SIDECAR_TRACE_PROFILES` 当前只有正常履约、UNKNOWN 恢复、状态冲突三个 profile。H-19 验证 J03 是否只是一个 declarative coverage gap（声明式覆盖缺口），而不是更深的 Toolkit / Action Origin 缺陷。

## Baseline snapshot / 冻结基线

| File | Baseline SHA-256 | Policy |
|---|---|---|
| `src/agentic_payment_experiment/webshop_sidecar_trace_profiles.py` | `eb03ed375c3cb5c0b2a80ad248b4de00e833c007e8dfb687f742d97cca643941` | allowed to change |
| `tests/test_webshop_sidecar_trace_toolkit.py` | `13850d919625f6836d339ff0f5432f38a5fac147cf60ca848b1bea4cb10bdef1` | allowed to change |
| `tests/test_webshop_payment_sidecar.py` | `cea52a6649d207539c2b3f91b2bdc2a12f807c61b85603aeca31d632a7540a73` | allowed to change |
| `src/agentic_payment_experiment/webshop_sidecar_trace_toolkit.py` | `1ccf37b62f6eedc0eff41216ec983ddaea74aed7a0e0529be686f6b15aefbbf3` | frozen |
| `src/agentic_payment_experiment/webshop_payment_sidecar.py` | `e74939a0b1da9eba5e70f34ab8f745ac61e8ae2254c2ab823ee92c5299a210c8` | frozen |
| `src/agentic_payment_experiment/action_origin.py` | `95ef06d6d396f9c912f321df907ed198908f629abf93c296ce0f9bf3d68439a6` | frozen |
| `src/agentic_payment_experiment/authoritative_trace.py` | `07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a` | frozen |
| `src/agentic_payment_experiment/lifecycle.py` | `8fc6df6f56d5aad47cc9c449340307324150f12760f0a124bd32296a659a4c92` | frozen |
| H-18 runner | `c726ba93fe8840bb698673bd38c7e119c38aebff3110b394c4882da7c2e73898` | frozen |
| H-18 matrix | `c6f6c22c7c2ff637950b2611cb99ef6762f76eff0ee52def90ecf707e6839c7d` | frozen |
| H-17 parent result | `9c611dfe121d970569ea41d1e1831d0f829da307c61a6839996846ca893545fc` | frozen |
| H-17 experiment context | `6a52d7cb77a1186209a88ab877560a352089b818e8c898977e1e0148dc94b3d1` | frozen |

## Single objective / 单一目标

只补充一个**通用声明式 Sidecar Trace Profile（侧车轨迹配置档）**，使现有 Toolkit 可以识别并记录如下生命周期：

```text
initial payment = SUCCEEDED
effective payment = SUCCEEDED
query recovery = NONE
status conflict = NONE
fulfillment = FAILED
task = FAILED
remediation = REQUIRED
retry = false
extension kind = FULFILMENT
```

然后直接复用冻结 H-18 runner 对 J01..J04 重测；不得复制或改写 lifecycle / trace 决策逻辑。

## Principal change / 唯一主要变化

唯一 principal change（主要变化）：

> 在 `webshop_sidecar_trace_profiles.py` 中增加一个不绑定 J03 名称、H-18 case id、具体订单/商品/金额的通用 failed-fulfilment profile，并将其加入 `SIDECAR_TRACE_PROFILES`；测试只验证这一通用配置能被现有 `_select_profile` / Toolkit 正确消费。

允许给该 profile 使用清晰通用名称，例如 `FULFILMENT_FAILED_PROFILE`；不得把它命名或编码成 `J03_*` 专用补丁。

## Acceptance criteria / 验收标准

### AC-01 — Frozen architecture boundary

- `webshop_sidecar_trace_toolkit.py` hash 保持 `1ccf37b6...`；
- `webshop_payment_sidecar.py`、`action_origin.py`、`authoritative_trace.py`、`lifecycle.py` 保持冻结 hash；
- H-17/H-18 runner、matrix、parent/context 与 evaluator checks 不变；
- 不新增 network/browser/API/dependency/runtime side effect。

### AC-02 — One generic declarative profile only

- `SIDECAR_TRACE_PROFILES` 从 3 个 profile 增加到恰好 4 个；
- 既有 T01/T09/T12 profile 仍存在且属性不变；
- 新 profile 必须是 `SidecarExtensionKind.FULFILMENT`；
- payment initial/effective=`SUCCEEDED`；recovery/conflict 均为空；
- lifecycle fulfillment=`FAILED`、task=`FAILED`、remediation=`REQUIRED`；
- 不包含 `J03`、H-18 case id、ASIN、order/request/payment 固定值等 Case 专用条件。

### AC-03 — J03 Authoritative Trace closes the upstream breakpoint

冻结 H-18 测量重新执行后，J03 必须满足：

- `measurement_complete=true`、repeat=`2` 且 digest 一致；
- `semantic_match=true`；
- `trace.available=true`；
- `trace.validation_status=VALID`；
- trace 的 `order_id/request_id/payment_id` 与该 Case 实际 refs 一致；
- `AUTHORITATIVE_TRACE_AVAILABLE=true`；
- `AUTHORITATIVE_TRACE_VALID=true`；
- `TRACE_ORDER_REQUEST_PAYMENT_CONTINUITY=true`；
- `ACTION_ORIGIN_PROJECTABLE=true`；
- `continuity_pass=true`、`first_breakpoint=null`。

如果 J03 Trace 已 VALID 但 `ACTION_ORIGIN_PROJECTABLE=false`，本 AC 仍失败；Executor 不得顺手修改 Action Origin，而应停止并把新断点交回 Evaluator。

### AC-04 — Other branches remain semantically stable

冻结 H-18 四分支必须保持：

- semantic matches=`4/4`；
- J01 continuity=PASS / first_breakpoint=null；
- J02 first_breakpoint=`ACTION_ORIGIN_PROJECTABLE`；
- J04 first_breakpoint=`ACTION_ORIGIN_PROJECTABLE`；
- branch continuity 目标恰为 `2/4`；
- 不通过改变 H-18 matrix / expected semantics / checker 来实现。

### AC-05 — Project guardrails

- real Buy Now/payment/fulfillment/network side effects=`0`；
- focused Sidecar/Trace/Lifecycle/Action Origin tests PASS；
- `run_experiment.py` 正式入口 PASS；
- project-impact baseline repeat=`3`、all identical；
- Product Trace=`9/12`、GESR=`8/12`、callback=`12/12`、duplicate/forbidden side effect=`0/12`、unsafe allow=`0/5` 不退化；
- full unittest discovery 零失败。

### AC-06 — v2.2 evidence and handoff

- frozen L2 `7/7` mandatory checks PASS；
- REPORT 映射 AC-01..06 → EV；
- REPORT 明确 Before=`continuity 1/4`，After=`2/4` 或如实报告失败；
- 记录 changed files、最终 hashes、真实副作用、任何偏差与 stop condition；
- workflow validator `OK` 后才能 `SUBMITTED_FOR_REVIEW`；
- Executor 不得自行给 Task PASS / Project IMPROVED。

## Allowed scope / 允许修改

Product/test 只允许：

- `src/agentic_payment_experiment/webshop_sidecar_trace_profiles.py`
- `tests/test_webshop_sidecar_trace_toolkit.py`
- `tests/test_webshop_payment_sidecar.py`

Task-owned outputs：

- `docs/05_任务交接/P9_WEBSHOP_FULFILMENT_FAILED_AUTHORITATIVE_TRACE_PROFILE_V1/REPORT.md`
- `docs/05_任务交接/P9_WEBSHOP_FULFILMENT_FAILED_AUTHORITATIVE_TRACE_PROFILE_V1/evidence/**`

Evaluator-owned frozen files 全部只读：

- `CONTRACT.md`
- `VALIDATION_PLAN.yaml`
- `evaluator_checks/**`
- `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`
- `CURRENT.md`
- H-17 / H-18 contract/report/review/evidence/fixtures/checkers

## Exclusions / 明确排除

- 不修改 `webshop_sidecar_trace_toolkit.py`；
- 不修改 `webshop_payment_sidecar.py`；
- 不修改 Recovery / Finality / Conflict / Lifecycle / Remediation；
- 不修改 Authoritative Trace validator/consumer/player；
- 不修改 Action Origin；
- 不改 H-18 runner、matrix、expected semantics、result audit；
- 不修 J02/J04 的 Action Origin gap；
- 不新增第二个 profile 或第二种产品机制；
- 不执行真实 Buy Now、支付、履约、网络/API；
- 不安装依赖或修改环境；
- 不 commit、push、history rewrite。

## Validation plan / 验证计划

Frozen plan: `docs/05_任务交接/P9_WEBSHOP_FULFILMENT_FAILED_AUTHORITATIVE_TRACE_PROFILE_V1/VALIDATION_PLAN.yaml`

| VP | Check | AC |
|---|---|---|
| VP-01 | frozen source/profile boundary audit | AC-01,02,06 |
| VP-02 | frozen H-18 same-journey lifecycle rerun | AC-03,04,05 |
| VP-03 | evaluator result audit for exact H-19 signal | AC-03,04,05 |
| VP-04 | focused Sidecar/Trace/Lifecycle/Action Origin regression | AC-02,05 |
| VP-05 | formal experiment entrypoint | AC-05 |
| VP-06 | project-impact baseline repeat=3 | AC-05 |
| VP-07 | full unittest discovery | AC-05,06 |

## Stop conditions / 停止条件

出现任一情况立即停止并交回 Evaluator，不得扩合同：

- profile-only（仅配置档）变化无法让 J03 生成 `VALID` Trace；
- J03 Trace 已 `VALID`，但首断点下移到 `ACTION_ORIGIN_PROJECTABLE`；
- 需要修改 Toolkit / Payment Sidecar / Lifecycle / Authoritative Trace validator / Action Origin；
- 需要第二个 profile、第二个产品机制或 Case 专用条件；
- J01/J02/J04 的既有语义或 first breakpoint 非预期变化；
- 任何真实副作用或项目守护线退化。

## Bounded Executor loop / 有界执行循环

- max complete implementation→L2 cycles: `2`；
- L1 可重复运行 profile/Sidecar focused tests 与 H-18 runner；
- 只允许一个完整 L2 失败后的 contract 内修正；
- 命中上述停止条件时立即返回 `BLOCKED`；
- 不因 J02/J04 仍失败而继续扩范围。

## Expected project impact / 预期项目影响

Measured baseline: H-18 semantic=`4/4`、continuity=`1/4`。  
Expected after: semantic=`4/4`、continuity=`2/4`，J03 从 `AUTHORITATIVE_TRACE_AVAILABLE` 断点变为完整 PASS；J02/J04 仍停在 `ACTION_ORIGIN_PROJECTABLE`。  
Expected project impact verdict if reproduced: `IMPROVED`。  
Cost: 低；本地声明式 profile + 测试 + 离线回归，无外部 API/支付成本。  
Complexity budget: 不新增 Toolkit 分支，不新增新的 trace schema，不新增 Action Origin 类型。  
Rollback/stop: profile-only 假设无法关闭 J03、出现多 profile ambiguity（多配置匹配歧义）、其他分支/安全指标退化，或需要第二主要变化。

## Authorization / 授权

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false

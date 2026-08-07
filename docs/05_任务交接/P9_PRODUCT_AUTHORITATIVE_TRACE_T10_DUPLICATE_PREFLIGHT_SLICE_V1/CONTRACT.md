# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-T10-DUPLICATE-PREFLIGHT-SLICE-V1`  
Task name: T10 重复付款预检产品权威轨迹纵向切片  
Task kind: `capability_experiment`  
Risk: `L2`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-04-r5`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-MEASUREMENT-ADAPTER-V1`  
Parent verdict: `PASS / NOT_APPLICABLE`  
Metric baseline: accepted T10 target 中 product-observed trace 为 `0/12`、GESR 为 `0/12`、T10 为 `NOT_AVAILABLE`，其余 T10 决策与副作用维度已匹配。  
Estimated affected scope: 本轮直接影响固定任务 `T10`，即 `1/12`；不得扩展到其他 11 项。  
Expected project impact: 同一 accepted target 上 product trace 从 `0/12` 提升到 `1/12`、GESR 从 `0/12` 提升到 `1/12`，非 trace 业务投影和安全守护线不变。  
Rollback condition: runner、validator、fixture、registry 或 non-trace hash 变化，T10 决策/回调/状态/原因/副作用变化，或其他任务出现 trace producer 时立即回滚本轮产品改动。

### Active bottleneck

```text
产品公开 outcome 的统一权威轨迹 = 0/12
GESR = 0/12
```

当前产品已经产生授权、订单、请求、动作、支付、预检和 Runtime Gate 事实，但这些事实没有随产品 outcome 形成统一、可验证的产品轨迹。

### Falsifiable hypothesis

如果只在 T10 duplicate-preflight `BLOCKED` 产品路径中，把该次调用已经产生的不可变事实组装为 `PRODUCT_OBSERVED` 轨迹，那么：

```text
T10 product trace: NOT_AVAILABLE → VALID
Target GESR:       0/12 → 1/12
```

同时决策、callback、重复付款阻断、状态、reason codes 和其他 11 项产品结果必须不变。

### Estimated affected scope

- 直接影响：固定任务 `T10`，即 `1/12`；
- 最终潜在范围：B-03 覆盖 `12/12`，但本任务不得扩展到其他任务；
- 估算信心：高，T10 当前只有产品 trace 与 `authoritative_trace` evidence stage 两类缺口；
- 风险：如果同时修改 runner、validator 或业务规则，将无法归因，必须回滚。

## Accepted measuring instrument

以下文件及哈希已经由 Evaluator 接受，本任务只读，不得修改：

| 项目 | 接受值 |
|---|---|
| `scripts/validation/run_project_impact_baseline.py` | `cbeafe9a3badcc5a69e7972420a5c90bb815f84bdd0d5bcde3d05f739c072100` |
| `src/agentic_payment_experiment/authoritative_trace.py` | `07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a` |
| Baseline fixture | `4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5` |
| T10 target fixture | `f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee` |
| Accepted target BEFORE output | `ac3ec88433718bbd097f2738cd2330267107431ce18c9c7b2a45964f9971b488` |
| Accepted target BEFORE normalized | `c802bacfcd9154bdca7e36a5e9a8a2cdcfdc24158c0af96baf755aafa738a770` |
| Non-trace business projection | `6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc` |

Accepted runtime contract hashes:

```text
formula registry
= 2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd

projection registry
= 45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4

profiles
= 6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2

full runtime contract
= 4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e
```

## Single objective

只修改 T10 duplicate-preflight `BLOCKED` 产品返回，使 `WebShopBuyNowGateOutcome` 显式携带：

```text
ProductAuthoritativeTrace
schema_version = product-authoritative-trace/v1
source = PRODUCT_OBSERVED
profile = WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V2
completeness_status = COMPLETE
events = exact 12
source_bindings = exact 11 unique bindings
```

其他所有返回路径的 `authoritative_trace` 必须保持 `None`。

## Exactly one principal change

```text
T10 duplicate-preflight BLOCKED return
→ 读取本次产品调用中已经产生的事实
→ 构造 exact T10 ProductAuthoritativeTrace
→ 随 WebShopBuyNowGateOutcome 返回
```

不得修改任何业务裁决规则，不得重新运行授权、绑定、支付或预检判断来“制造”轨迹结论。

## T10 source facts

轨迹只能消费该分支已经存在的对象：

1. `mandate`；
2. `authorized_snapshot.order`；
3. `adaptation.order`；
4. `bound_request`；
5. `governed_action`；
6. `execution_candidate`；
7. `governed_action_fact`；
8. `known_payment_attempts` 中与 `related_attempt_refs` 对应的历史成功付款；
9. `known_attempt_fact`；
10. `duplicate_result`；
11. `runtime_record`；
12. duplicate `BLOCKED` 分支准备返回的 `WebShopBuyNowGateOutcome` 非 trace 字段。

轨迹构造器不得读取 fixture、runner、docs、CURRENT、task evidence、隐藏 `GateContext` 或 evaluator replay。

## Exact profile

### Events

```text
1  AUTHORITY_RECORDED [AUTHORITY]
2  ORDER_RECORDED [AUTHORIZED_ORDER_SNAPSHOT]
3  ORDER_RECORDED [CURRENT_ORDER_SNAPSHOT]
4  REQUEST_RECORDED [CURRENT_REQUEST]
5  ACTION_RECORDED [GOVERNED_ACTION]
6  PAYMENT_CANDIDATE_RECORDED [CURRENT_PAYMENT_CANDIDATE]
7  ACTION_BINDING_DECISION_RECORDED [ACTION_BINDING_FACT]
8  PAYMENT_OUTCOME_RECORDED [HISTORICAL_SUCCEEDED_PAYMENT]
9  KNOWN_PAYMENT_PREFLIGHT_RECORDED [KNOWN_PAYMENT_PREFLIGHT_FACT]
10 PREPAYMENT_DECISION_RECORDED [PREPAYMENT_VALIDATION]
11 RUNTIME_DECISION_RECORDED [RUNTIME_GATE_OBSERVATION]
12 RESULT_RECORDED [FINAL_OUTCOME]
```

### Binding rules

- exact `12 events / 11 unique bindings`；
- authorized/current Order 两个 event 共享同一个 Order binding；
- 当前付款候选和历史成功付款使用不同 `PaymentExecutionRecord` binding、role 和 `payment_id`；
- 每个 event 只通过 `source_binding_ref` 解析 binding；
- 所有 relation target type、role、ref 和 target binding assertions 必须精确解析；
- RESULT projection 排除 `authoritative_trace`，不得形成循环 hash；
- `trace_ref` 使用稳定、无时间和随机数的关闭格式：

```text
ProductAuthoritativeTrace:
WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V2:
<bound_request.request_id>
```

## Acceptance criteria

### AC-01 — Outcome boundary

`WebShopBuyNowGateOutcome` 增加：

```text
authoritative_trace: ProductAuthoritativeTrace | None = None
```

要求：

1. 保持 dataclass frozen；
2. 新字段放在默认字段区域，不破坏现有调用；
3. 只有 T10 duplicate `BLOCKED` 分支返回非空值；
4. prepayment、action invalid、known-attempt INDETERMINATE、正常 ALLOW、callback failure 等路径均保持 `None`。

### AC-02 — Pure product trace builder

可新增：

```text
src/agentic_payment_experiment/webshop_authoritative_trace.py
```

只允许实现 T10 轨迹投影与构造。它必须：

- 使用 accepted `authoritative_trace.py` 的 contract、canonicalization 和 ref helpers；
- 不复制 validator；
- 不读取文件、环境变量、当前时间、随机数或网络；
- 不调用 `validate_request`、`verify_governed_payment_action`、`derive_known_payment_attempt_preflight` 或支付执行函数；
- 对缺失、多个或关系不一致的历史成功付款 fail closed，不产生伪造 trace；
- 不改变任何输入对象。

### AC-03 — Product call-path insertion

在 `known_attempt_fact.status is BLOCKED` 分支：

1. 先按现有逻辑得到 `duplicate_result` 与 `runtime_record`；
2. 先构造一个 `authoritative_trace=None` 的冻结 outcome 或等价非 trace projection；
3. 从本次调用已有事实构造 T10 trace；
4. 返回携带 trace 的 outcome；
5. 不增加 callback、retry、支付、履约或其他副作用。

不得在 runner 或测试中事后注入 trace。

### AC-04 — Strict validator acceptance

真实调用 `gate_webshop_buy_now(...)` 得到的 T10 trace 必须由冻结 validator 判定：

```text
status = VALID
profile = WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V2
reason_codes = product_authoritative_trace_valid
event_count = 12
binding_count = 11
```

还必须证明：

- 两个 Order event 共享 binding；
- 当前付款候选与历史付款不同；
- historical payment status 为 `SUCCEEDED`；
- known preflight status 为 `BLOCKED`；
- validation decision 和 runtime final decision 均为 `DENY`；
- final outcome decision 为 `DENY`；
- 所有 relation target 解析成功。

### AC-05 — Same-target before / after impact

使用完全相同的 accepted runner 和 target fixture：

```text
BEFORE
T10 trace = NOT_AVAILABLE
product trace = 0/12
GESR = 0/12

AFTER
T10 trace = VALID
product trace = 1/12
GESR = 1/12
```

AFTER target 必须满足：

```text
matched_tasks = 1
gap_task_ids = T01—T09,T11,T12
T10 capability_gaps = []
```

其他 11 项仍为 `NOT_AVAILABLE`，不得顺带增加 producer。

### AC-06 — Non-trace business invariance

以下接受的 canonical projection SHA-256 必须保持：

```text
6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

T10 以下字段必须与 BEFORE 完全一致：

```text
actual_decision = DENY
actual_callback_count = 0
actual_callback_observations = 0
actual_retry_count = 0
known_payment_attempt_preflight_status = BLOCKED
duplicate_payment_blocked = true
retry_allowed = false
trusted_state_changed = false
binding_status = VALID
reason_codes unchanged
forbidden_side_effects = []
```

允许变化仅限：

- `product_observed_trace_status`；
- `product_observed_trace_events`；
- `product_observed_trace_reason_codes`；
- `product_observed_trace_source`；
- `evidence_stages` 新增 `authoritative_trace`；
- 由这些字段直接计算的 task matched、gap 和 GESR 指标。

### AC-07 — Measuring instrument frozen

任务完成时以下哈希必须仍等于 accepted 值：

- runner；
- `authoritative_trace.py`；
- baseline fixture；
- target fixture；
- 四项 runtime registry。

任何变化均直接回滚，不得通过更新合同哈希解决。

### AC-08 — Negative boundaries

测试至少覆盖：

- 所有非 T10 BLOCKED 路径 trace 为 `None`；
- 无 governed action 时不产生 T10 trace；
- known attempt `INDETERMINATE` 不产生 trace；
- unrelated succeeded attempt / CLEAR 不产生 T10 trace；
- 多个 related historical payment 无法唯一闭合时 fail closed；
- 当前 payment 与 historical payment 被错误合并时 validator 不通过；
- Order 两个 event 未共享 binding 时 validator 不通过；
- RESULT projection 包含 trace 时不通过；
- 构造器不得通过 evaluator replay 或 runner 补事实。

### AC-09 — Guardrails and regression

独立运行：

```text
python3 -m unittest \
  tests.test_webshop_authoritative_trace \
  tests.test_webshop_runtime_gate \
  tests.test_project_impact_baseline -v

python3 -m unittest discover -s tests -p 'test_*.py'
```

要求：

- 全量至少 `477` 项并全部通过；
- callback match 仍为 `12/12`；
- duplicate/forbidden side effect 仍为 `0/12`；
- unsafe allow `0/5`；
- missed confirmation `0/2`；
- overconfident decision `0/2`；
- forbidden state write `0/2`；
- retry match `12/12`；
- binding completeness `5/5`；
- lineage completeness `2/2`；
- decision-reason consistency `11/12`。

### AC-10 — Evidence and impact comparison

REPORT 必须提供：

- exact changed files；
- BEFORE accepted hashes；
- AFTER baseline/target repeat=3 原始 JSON 与 normalized hashes；
- T10 before/after 字段级 diff；
- non-trace projection hash；
- runner/module/fixture/registry freeze audit；
- trace 12-event/11-binding 结构化摘要；
- focused/full tests 原始证据；
- product producer 静态审计；
- workflow validator `OK`；
- `Impact comparison`：baseline、after、delta、scope caveat；
- Executor 候选 verdict，但不得自行签发 PASS。

## Expected project impact

成功阈值：

```text
T10 product trace: +1 task
Product trace rate: 0/12 → 1/12
Target GESR:        0/12 → 1/12
Business projection: unchanged
Safety guardrails:   unchanged
```

达到以上条件时，项目影响候选为 `IMPROVED`。

## Rollback condition

任一条件成立即回滚本任务产品改动：

- accepted runner、validator、fixture 或 registry hash 变化；
- non-trace projection hash 变化；
- T10 决策、callback、reason、状态或副作用变化；
- trace 不是 exact 12/11；
- 其他任务出现非空产品 trace；
- validator 需要读取隐藏对象或 evaluator replay 才能通过；
- 全量测试失败或低于 477；
- 需要网络、WebShop runtime、Buy Now、真实支付或外部副作用。

## Required outputs

1. T10 产品 trace producer；
2. T10 pure builder；
3. 正负测试；
4. 本任务 `REPORT.md`；
5. 本任务 `evidence/EV-*`；
6. AFTER baseline/target JSON 与 impact comparison。

## Allowed scope

可新增或修改：

- `src/agentic_payment_experiment/webshop_runtime_gate.py`
- `src/agentic_payment_experiment/webshop_authoritative_trace.py`
- `tests/test_webshop_runtime_gate.py`
- `tests/test_webshop_authoritative_trace.py`
- `tests/test_project_impact_baseline.py`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/REPORT.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/evidence/EV-*`
- `CURRENT.md`（仅 `CONTRACT_FROZEN → EXECUTING`）

只读输入：accepted measurement module、runner、fixtures、设计文档、T10 grounded evidence 和现有产品对象。

工作区继承此前已接受但未提交的 P9 产物。不得清理、重置、覆盖或回退这些文件。

## Exclusions

- 不修改 `src/agentic_payment_experiment/authoritative_trace.py`；
- 不修改 `scripts/validation/run_project_impact_baseline.py`；
- 不修改 `samples/`；
- 不修改授权、确认、绑定、身份、上下文、重复付款、支付或状态业务规则；
- 不为 T01—T09、T11、T12 增加 trace producer；
- 不把 evaluator replay 改名为产品 trace；
- 不读取 docs、task evidence、CURRENT、fixture 或 hidden context 来构造产品 trace；
- 不执行 WebShop runtime、Buy Now、支付、钱包、订单或 callback 外部副作用；
- 不调用网络、LLM 或外部 API；
- 不安装依赖、不创建环境；
- 不提交、不推送、不改写历史；
- 不更新项目瓶颈地图；
- 不扩大为全部 12 项轨迹重构。

## Validation plan

| VP | Exact action | Expected |
|---|---|---|
| VP-01 | 审计 accepted hashes | runner/module/fixture/registry 不变 |
| VP-02 | 调用真实 T10 gate | outcome 直接携带 trace |
| VP-03 | strict validator | exact T10 trace `VALID` |
| VP-04 | 结构审计 | 12 events / 11 bindings / Order shared binding |
| VP-05 | 非 T10 negative paths | trace 均为 `None` |
| VP-06 | target repeat=3 | product trace 1/12，GESR 1/12 |
| VP-07 | baseline repeat=3 | guardrails 不回归，结果可重复 |
| VP-08 | non-trace projection | SHA-256 `6eb5...` 不变 |
| VP-09 | focused + full unittest | 全部通过，full >= 477 |
| VP-10 | workflow validator | `OK` |

## Stop conditions

- 无法只用本次调用已有对象闭合 exact T10 profile；
- 需要修改 accepted validator 或 runner；
- 多个历史付款无法确定 profile 所需唯一 target；
- 构造 trace 会改变 outcome 的非 trace 字段；
- target AFTER 不能归因到 T10 唯一 producer；
- 任何外部副作用或新依赖是必要条件。

## Authorization

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- data_download: false
- dependency_install: false
- create_environment: false
- webshop_runtime_execution: false
- buy_now_execution: false
- payment_or_order_side_effect: false

## Amendments

None.

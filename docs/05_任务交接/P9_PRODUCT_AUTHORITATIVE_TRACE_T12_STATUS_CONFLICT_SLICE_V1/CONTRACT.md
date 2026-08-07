# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-T12-STATUS-CONFLICT-SLICE-V1`  
Task name: T12 支付状态冲突产品权威轨迹切片  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `capability_experiment`  
Risk: `L1`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-06-r8`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-T09-UNKNOWN-PAYMENT-RECOVERY-SLICE-V1`  
Parent verdict: `PASS / IMPROVED`  
Metric baseline: 同一 accepted baseline 中 Product Trace 为 `3/12`、GESR 为 `2/12`、T12 product trace 为 `NOT_AVAILABLE`，T12 其他业务维度已匹配。  
Estimated affected scope: 本轮直接影响固定任务 `T12`，即 `1/12`；不得扩展到其他 11 项。  
Expected project impact: Product Trace 从 `3/12` 提升到 `4/12`、GESR 从 `2/12` 提升到 `3/12`、T12 从不匹配变为完全匹配，非 trace 业务投影与安全守护线不变。  
Rollback condition: runner、validator、gate、T10/T01/T09 builder、fixture、registry、既有完整 trace 或 non-trace hash 变化，T12 业务行为变化，或 T12 之外新增 trace producer 时立即回滚本轮产品改动。

当前已验证：

```text
T10 duplicate-preflight 拒绝链 = VALID
T01 正常支付与履约成功链 = VALID
T09 UNKNOWN 支付查询恢复链 = VALID
Product Trace = 3/12
baseline GESR = 2/12
```

T12 当前业务行为已经正确：

```text
initial payment = UNKNOWN
query status = SUCCEEDED
async status = FAILED
status conflict = CONFLICT
effective payment = UNKNOWN
fulfilment = SUCCEEDED
task = UNKNOWN
remediation = REQUIRED
retry = false
```

T12 当前唯一 capability gap 是产品未返回权威轨迹。真实 `PaymentStatusConflictFact` 已存在，因此可以保持单变量，不需要修改冲突判断或保留原始 observation。

## Single objective

只为真实 T12 产品调用生成一条完整产品权威轨迹：

```text
WEBSHOP_PAYMENT_STATUS_CONFLICT_V2
11 events
10 unique bindings
source = PRODUCT_OBSERVED
product source = webshop_payment_fulfilment_outcome
validator = VALID
```

不得新增或改变 payment recovery、status conflict、lifecycle、binding、Runtime Gate 或任何业务判断。

## Entering baseline

```text
baseline output SHA-256
= a38b2d91bc6e636201c9ab94c4bced1ad6653dadffb32811cb996d7ab0141086

repeat=3 normalized SHA-256
= ee99b8bf73092ef09d0b890d74b66323963bebf10c1a1b4cecf2f5cbc32d8399

Product Trace = 3/12
baseline GESR = 2/12
valid product tasks = T01, T09, T10
non-trace projection SHA-256
= 6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

### T12 before

```text
decision = ALLOW
callback count = 1
retry count = 0
initial payment = UNKNOWN
query recovery = RECOVERED
status conflict = CONFLICT
effective payment = UNKNOWN
fulfilment = SUCCEEDED
task = UNKNOWN
remediation = REQUIRED
retry_allowed = false
duplicate_payment_blocked = false
forbidden_side_effects = []

product trace = NOT_AVAILABLE
matched = false
```

### Existing trace invariants

```text
T01 full trace SHA-256
= 7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906

T09 full trace SHA-256
= a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e

T10 full trace SHA-256
= 2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3
```

### Frozen boundaries

```text
runner
= 70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3

authoritative_trace.py
= 07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a

webshop_runtime_gate.py
= 5abf1a6f08060e111b6fbd9ba96809c2823ef07adee0e23b6d60a6c50c06bdef

webshop_authoritative_trace.py / T10 builder
= 9653277777d06ce8d2c65862765ec57c17874a9d311d2c5c9c117993a0feeac8

baseline fixture
= 4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5

T10 target fixture
= f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee

formula registry
= 2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd

projection registry
= 45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4

profiles
= 6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2

runtime contract
= 4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e
```

## Single principal change

只做一个主要 capability change：

> 使用已接受的中立 Trace Assembler，把 T12 当前真实 gate、payment recovery、status conflict 和 sidecar lifecycle 事实组装为产品权威轨迹。

不得同时增加 T11 或其他场景，不得修改冲突、恢复、生命周期或测量逻辑。

## Exact T12 trace contract

Profile：

```text
WEBSHOP_PAYMENT_STATUS_CONFLICT_V2
```

事件顺序固定为：

```text
1  AUTHORITY_RECORDED [AUTHORITY]
2  ORDER_RECORDED [AUTHORIZED_ORDER_SNAPSHOT]
3  ORDER_RECORDED [CURRENT_ORDER_SNAPSHOT]
4  REQUEST_RECORDED [CURRENT_REQUEST]
5  ACTION_RECORDED [GOVERNED_ACTION]
6  PAYMENT_CANDIDATE_RECORDED [CURRENT_PAYMENT_CANDIDATE]
7  ACTION_BINDING_DECISION_RECORDED [ACTION_BINDING_FACT]
8  RUNTIME_DECISION_RECORDED [RUNTIME_GATE_OBSERVATION]
9  PAYMENT_OUTCOME_RECORDED [PAYMENT_EXECUTION_OUTCOME]
10 STATUS_CONFLICT_RECORDED [STATUS_CONFLICT_FACT]
11 RESULT_RECORDED [FINAL_OUTCOME]
```

Binding 规则：

- authorized/current order 共享同一 Order binding；
- candidate 使用 gate 留存的执行前 `PENDING` payment；
- payment outcome 使用 conflict 收敛后的 `effective_payment=UNKNOWN`；
- candidate 与 payment outcome 使用同一 payment ID/entity ref，但 projection、status 和 binding 不同；
- conflict event 使用真实 `PaymentStatusConflictFact`；
- 共 11 events / 10 unique bindings。

## Acceptance criteria

### AC-01 — Neutral conflict projection

中立 assembler 可新增：

```text
project_payment_status_conflict
```

要求：

- 字段严格匹配冻结 `payment-status-conflict-fact-trace/v2` registry；
- 不包含 T12 场景判断；
- 不调用 conflict、recovery、lifecycle 或其他业务函数；
- 不读取 observation、文件、环境、时间或随机数；
- 不改变已有 projection 输出和 T01/T09/T10 完整 trace。

### AC-02 — Pure T12 builder

新增纯 builder，建议：

```text
src/agentic_payment_experiment/webshop_payment_status_conflict_authoritative_trace.py
```

只能读取：

- `WebShopBuyNowGateOutcome` 已留存事实；
- `WebShopCommerceAdaptation`；
- `IntentMandate`；
- 已经完成业务计算的 `WebShopPaymentFulfilmentOutcome`；
- 中立 Trace Assembler。

不得接收或保留 `PaymentStatusObservation`，不得调用：

- `derive_payment_status_conflict`；
- `assess_payment_recovery`；
- `assess_lifecycle`；
- binding verification；
- Runtime Gate；
- 支付、订单、callback 或任何外部副作用。

任一事实缺失或矛盾时返回 `None`。

### AC-03 — Exact T12 fact gate

仅以下条件全部成立时允许产出 T12 trace：

```text
gate decision = ALLOW
checkout_executed = true
gate callback_count = 1
runtime final_decision = ALLOW
runtime callback_executed = true
runtime callback_count = 1
action binding fact = VALID
retained authorized order / action / candidate 均存在
candidate status = PENDING
authorized order = current order projection
bound request = adapter request projection
base outcome ready = true
initial_payment status = UNKNOWN
query_recovery exists
query_recovery initial_status = UNKNOWN
query_recovery observed_status = SUCCEEDED
query_recovery effective_status = SUCCEEDED
query_recovery recovery_status = RECOVERED
query_recovery retry_allowed = false
status_conflict exists
status_conflict resolution = CONFLICT
status_conflict initial_status = UNKNOWN
status_conflict query_status = SUCCEEDED
status_conflict async_status = FAILED
status_conflict effective_status = UNKNOWN
status_conflict effective_status_terminal = false
status_conflict reason_codes contains payment_status_opposite_terminal_claims
effective_payment status = UNKNOWN
candidate / initial / effective payment ID 相同
lifecycle payment = UNKNOWN
lifecycle fulfillment = SUCCEEDED
lifecycle task = UNKNOWN
lifecycle remediation = REQUIRED
base retry_allowed = false
duplicate_payment_blocked = false
```

任一条件不满足，builder 必须 fail-closed 返回 `None`，业务结果不得变化。

### AC-04 — Product call-path insertion

sidecar 必须保持：

```text
先完成 recovery / conflict / lifecycle 业务计算
→ 构造 authoritative_trace=None 的 base outcome
→ 尝试 T01
→ 尝试 T09
→ 若仍为空，再尝试 T12
→ replace(base_outcome, authoritative_trace=trace_or_None)
```

要求：

- 不改变现有业务计算顺序；
- T01/T09/T12 条件互斥；
- 不使用 runner、fixture 或 evaluator replay 注入 trace；
- 一次产品调用最多返回一条 trace。

### AC-05 — Strict validator acceptance

真实 T12 产品调用必须得到：

```text
source = PRODUCT_OBSERVED
profile = WEBSHOP_PAYMENT_STATUS_CONFLICT_V2
status = VALID
events = 11
unique bindings = 10
product source = webshop_payment_fulfilment_outcome
```

关键状态：

```text
CURRENT_PAYMENT_CANDIDATE = PENDING
PAYMENT_EXECUTION_OUTCOME = UNKNOWN
STATUS_CONFLICT_FACT = CONFLICT
FINAL_OUTCOME = UNKNOWN
```

### AC-06 — Same-baseline project impact

使用同一 accepted fixture、runner 和 `repeat=3`：

```text
BEFORE:
Product Trace = 3/12
GESR = 2/12
valid product tasks = T01, T09, T10
T12 trace = NOT_AVAILABLE
T12 matched = false

AFTER:
Product Trace = 4/12
GESR = 3/12
valid product tasks = T01, T09, T10, T12
T12 trace = VALID
T12 matched = true
T12 capability_gaps = []
```

三次 normalized hash 必须一致。只允许 T12 新增产品轨迹。

### AC-07 — T12 business and safety invariance

必须保持：

```text
decision = ALLOW
callback count = 1
callback observations = 1
retry count = 0
initial payment = UNKNOWN
query recovery = RECOVERED
conflict resolution = CONFLICT
effective payment = UNKNOWN
fulfilment = SUCCEEDED
task = UNKNOWN
remediation = REQUIRED
retry_allowed = false
duplicate_payment_blocked = false
forbidden_side_effects = []
```

全项目 non-trace projection SHA-256 必须保持：

```text
6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

### AC-08 — Existing traces and other paths remain closed

必须保持：

```text
T01 full trace SHA-256
= 7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906

T09 full trace SHA-256
= a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e

T10 full trace SHA-256
= 2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3
```

产品轨迹只能存在于：

```text
T01
T09
T10
T12
```

以下仍不得产生新 trace：

- T02—T08；
- T11；
- query recovery 缺失或非 `RECOVERED`；
- status conflict 缺失或非 `CONFLICT`；
- query/async/effective status 不符合；
- conflict 已收敛为 terminal status；
- payment ID 不一致；
- lifecycle 非 UNKNOWN/REQUIRED 组合；
- candidate 非 `PENDING`；
- retained facts 缺失或矛盾。

### AC-09 — Measuring instrument and business boundary freeze

不得修改：

- `scripts/validation/run_project_impact_baseline.py`；
- `src/agentic_payment_experiment/authoritative_trace.py`；
- `src/agentic_payment_experiment/webshop_runtime_gate.py`；
- `src/agentic_payment_experiment/webshop_authoritative_trace.py`；
- T01/T09 builders；
- baseline/target fixtures；
- projection/formula/profile registry；
- recovery、conflict、lifecycle、payment 或 binding 业务模块；
- 项目地图。

### AC-10 — Tests and evidence

运行：

```text
python3 -m unittest \
  tests.test_webshop_trace_assembler \
  tests.test_webshop_payment_status_conflict_authoritative_trace \
  tests.test_webshop_unknown_payment_authoritative_trace \
  tests.test_webshop_payment_sidecar \
  tests.test_webshop_authoritative_trace \
  tests.test_authoritative_trace \
  tests.test_project_impact_baseline -v

python3 -m unittest discover -s tests -p 'test_*.py'

python3 scripts/validation/run_project_impact_baseline.py \
  --repeat 3 \
  --output <evidence>/EV-AFTER-baseline.json
```

要求：

- focused 全过；
- full 至少 `504` 项且全部通过；
- baseline repeat=3 normalized hash 一致；
- 保存 T12 exact 11-event/10-binding 结构；
- 保存 T01/T09/T10 full trace hash；
- 保存 non-trace hash、producer coverage 和冻结边界审计；
- workflow validator 为 `OK`。

## Validation plan

| VP | Exact action | Expected result |
|---|---|---|
| VP-01 | 真实 T12 gate + sidecar 调用 | product trace 为 `VALID / 11 events / 10 bindings` |
| VP-02 | T12 projection 审计 | candidate PENDING、payment UNKNOWN、conflict CONFLICT、final UNKNOWN |
| VP-03 | T12 negative matrix | 缺失、矛盾、非冲突条件全部返回 `None` |
| VP-04 | baseline repeat=3 | Product Trace `4/12`、GESR `3/12`，三次 normalized hash 一致 |
| VP-05 | non-trace projection | SHA-256 保持 `6eb5...9099dc` |
| VP-06 | T01/T09/T10 full trace | 三条完整 hash 不变 |
| VP-07 | producer coverage | 产品轨迹仅 T01/T09/T10/T12 |
| VP-08 | frozen boundary hash | runner、validator、gate、T10 builder、fixtures、registry 保持 |
| VP-09 | focused/full unittest | focused 全过；full 至少 504 项全过 |
| VP-10 | workflow validator | `OK` |

## Allowed scope

可修改：

- `src/agentic_payment_experiment/webshop_trace_assembler.py`（仅增加中立 conflict projection）；
- `src/agentic_payment_experiment/webshop_payment_status_conflict_authoritative_trace.py`（新增）；
- `src/agentic_payment_experiment/webshop_payment_sidecar.py`（仅增加 T12 builder 调用/选择）；
- `tests/test_webshop_trace_assembler.py`；
- `tests/test_webshop_payment_status_conflict_authoritative_trace.py`（新增）；
- `tests/test_webshop_payment_sidecar.py`；
- `tests/test_project_impact_baseline.py`；
- 本任务 `REPORT.md`；
- 本任务 `evidence/EV-*`；
- `CURRENT.md`（仅 `CONTRACT_FROZEN → EXECUTING`）。

工作区继承此前已接受但未提交的 P9 产物。不得清理、重置、覆盖或回退继承内容。

## Exclusions

- 不修改 runner、validator、gate、T10/T01/T09 builder、fixtures、registry、profiles 或项目地图；
- 不新增 T02—T08、T11 产品轨迹；
- 不改变 payment recovery、status conflict、lifecycle、authorization、binding、Runtime Gate 或 side-effect 业务规则；
- 不保留 query/async observation 原对象、完整 GateContext、callback、credential、页面、prompt 或隐藏上下文；
- 不使用 evaluator replay、fixture、docs 或 evidence 构造产品 trace；
- 不调用网络、LLM、外部 API、WebShop runtime、Buy Now、钱包、支付或订单；
- 不安装依赖、不创建环境；
- 不提交、不推送、不改写历史；
- 不清理、删除、重置或回退继承产物。

## Stop conditions

立即停止并报告，不得扩大范围：

- 需要修改 runner、validator、fixture、registry、profile、gate 或既有 builder；
- 需要修改 recovery、conflict、lifecycle 或其他业务规则；
- 无法仅靠 retained/product facts 构造 T12 trace；
- 需要保留 query/async observation 或完整隐藏上下文；
- T01/T09/T10 full trace hash 变化；
- non-trace hash 或安全守护线变化；
- T12 之外出现新产品 trace；
- 11 events / 10 bindings 无法闭合；
- 需要网络、真实支付、依赖安装或新环境。

## Required report

REPORT 必须包含：

- exact changed files 和 SHA-256；
- 中立 conflict projection；
- T12 builder 的真实事实输入与 fail-closed 条件；
- exact 11-event / 10-binding 结构；
- candidate/initial/effective payment 与 conflict 状态关系；
- baseline repeat=3 before/after；
- Product Trace `3/12 → 4/12`；
- GESR `2/12 → 3/12`；
- T12 business/non-trace invariance；
- T01/T09/T10 full trace hashes；
- producer coverage scan；
- frozen boundary hashes；
- focused/full tests 原始证据；
- workflow validator；
- `task_verdict_candidate`；
- `project_impact_candidate`。

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

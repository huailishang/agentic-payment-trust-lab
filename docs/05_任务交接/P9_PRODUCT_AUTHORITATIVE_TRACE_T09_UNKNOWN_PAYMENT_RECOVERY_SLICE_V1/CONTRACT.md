# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-T09-UNKNOWN-PAYMENT-RECOVERY-SLICE-V1`  
Task name: T09 UNKNOWN 支付查询恢复产品权威轨迹切片  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `capability_experiment`  
Risk: `L1`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-06-r7`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-ASSEMBLER-EXTRACTION-V1`  
Parent verdict: `PASS / NOT_APPLICABLE`  
Metric baseline: 同一 accepted baseline 中 Product Trace 为 `2/12`、GESR 为 `1/12`、T09 product trace 为 `NOT_AVAILABLE`，T09 其他业务维度已匹配。  
Estimated affected scope: 本轮直接影响固定任务 `T09`，即 `1/12`；不得扩展到其他 11 项。  
Expected project impact: Product Trace 从 `2/12` 提升到 `3/12`、GESR 从 `1/12` 提升到 `2/12`、T09 从不匹配变为完全匹配，非 trace 业务投影与安全守护线不变。  
Rollback condition: runner、validator、gate、T10 builder、fixture、registry、T01/T10 full trace 或 non-trace hash 变化，T09 业务行为变化，或 T09 之外新增 trace producer 时立即回滚本轮产品改动。

当前已验证：

```text
T10 重复付款拒绝链 = VALID
T01 正常支付与履约成功链 = VALID
Product Trace = 2/12
baseline GESR = 1/12
```

统一 `webshop_trace_assembler.py` 已完成等价抽取，T01/T10 完整轨迹和所有业务指标保持不变。下一步应验证第三类路径，而不是继续维护架构。

T09 当前业务行为已经与 fixture 完全一致：

```text
初始支付状态 = UNKNOWN
→ 查询原交易得到 SUCCEEDED
→ recovery = RECOVERED
→ effective payment = SUCCEEDED
→ fulfilment = SUCCEEDED
→ task = SUCCEEDED
→ retry = false
```

T09 当前唯一 capability gap 是产品未返回权威轨迹。因此选择 T09 能保持单变量，并验证统一 Assembler 可复用于 payment recovery 路径。

## Single objective

只为真实 T09 产品调用生成一条完整产品权威轨迹：

```text
WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2
11 events
10 unique bindings
source = PRODUCT_OBSERVED
product source = webshop_payment_fulfilment_outcome
validator = VALID
```

不得新增或改变 recovery、payment、lifecycle、binding、Runtime Gate 或任何业务判断。

## Entering baseline

### Same accepted baseline

```text
baseline output SHA-256
= 8d4304dce72bb4f3d572512ee4d09e2e4bd2ee06f34ec4e8e6b0887acf059d9a

repeat=3 normalized SHA-256
= 56a82f9ab99cd5d83ae0b1259c2cef9f6b6cdf2a1b7183c029ba7569ab332619

Product Trace = 2/12
baseline GESR = 1/12
valid product tasks = T01, T10
non-trace projection SHA-256
= 6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

### T09 before

```text
T09 decision = ALLOW
callback count = 1
retry count = 0
initial payment = UNKNOWN
effective payment = SUCCEEDED
recovery = RECOVERED
fulfilment = SUCCEEDED
task = SUCCEEDED
remediation = NOT_REQUIRED
retry_allowed = false
duplicate_payment_blocked = false
forbidden_side_effects = []

product trace = NOT_AVAILABLE
matched = false
capability gaps:
- product_observed_trace_status_mismatch:expected=VALID
- evidence_stages_missing:authoritative_trace
- product_observed_trace_events_missing:...
```

### Accepted existing trace invariants

```text
T01 full trace SHA-256
= 7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906

T10 full trace SHA-256
= 2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3
```

### Frozen implementation and measurement hashes

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

> 使用已经接受的中立 Trace Assembler，把 T09 当前真实 gate、payment recovery 和 sidecar 事实组装为产品权威轨迹。

不得同时增加 T11/T12 或其他场景，不得修改业务规则或测量器。

## Exact T09 trace contract

Profile：

```text
WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2
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
10 RECOVERY_OUTCOME_RECORDED [RECOVERY_OUTCOME]
11 RESULT_RECORDED [FINAL_OUTCOME]
```

Binding 规则：

- `AUTHORIZED_ORDER_SNAPSHOT` 与 `CURRENT_ORDER_SNAPSHOT` 共享同一 Order binding；
- `CURRENT_PAYMENT_CANDIDATE` 使用 gate 留存的执行前 `PENDING` payment；
- `PAYMENT_EXECUTION_OUTCOME` 使用 sidecar 的 `effective_payment=SUCCEEDED`；
- candidate 与 effective payment 使用同一个 payment ID，但 projection、status 和 binding 必须不同；
- `RECOVERY_OUTCOME` 使用真实 `PaymentRecoveryResult`；
- 共 11 events / 10 unique bindings。

## Acceptance criteria

### AC-01 — Neutral recovery and result projection reuse

中立 assembler 可新增 T09 所需的机械 projection，例如：

```text
project_payment_recovery
project_payment_sidecar_outcome
```

要求：

- 不包含 T09 场景判断；
- 不调用 recovery、lifecycle 或其他业务函数；
- projection 字段严格匹配冻结 registry；
- T01 可改为复用同一 sidecar result projection，但其完整轨迹 hash 必须保持；
- 不得把 T09 专属名称加入 assembler 公共 API。

### AC-02 — Pure T09 builder

新增纯 builder，建议：

```text
src/agentic_payment_experiment/webshop_unknown_payment_authoritative_trace.py
```

它只能读取：

- `WebShopBuyNowGateOutcome` 已留存事实；
- `WebShopCommerceAdaptation`；
- `IntentMandate`；
- 已经完成业务计算的 `WebShopPaymentFulfilmentOutcome` base outcome；
- 中立 Trace Assembler。

不得：

- 调用 `assess_payment_recovery`、`assess_lifecycle`、binding verification、Runtime Gate 或任何业务函数；
- 读取 runner、fixture、docs、CURRENT、evidence、文件、环境变量、时间或随机数；
- 使用 evaluator replay 补事实；
- 补造 PaymentRecoveryResult 或状态观察。

任一事实缺失或矛盾时返回 `None`。

### AC-03 — Exact T09 fact gate

仅以下条件全部成立时允许产出 T09 trace：

```text
gate decision = ALLOW
checkout_executed = true
gate callback_count = 1
runtime final_decision = ALLOW
runtime callback_executed = true
runtime callback_count = 1
action binding fact = VALID
retained authorized order / governed action / candidate 均存在
candidate status = PENDING
authorized order = current order projection
bound request = adapter request projection
base outcome ready = true
initial_payment status = UNKNOWN
effective_payment status = SUCCEEDED
initial/effective/candidate payment ID 相同
query_recovery exists
query_recovery initial_status = UNKNOWN
query_recovery observed_status = SUCCEEDED
query_recovery effective_status = SUCCEEDED
query_recovery recovery_status = RECOVERED
query_recovery retry_allowed = false
status_conflict = None
lifecycle payment = SUCCEEDED
lifecycle fulfillment = SUCCEEDED
lifecycle task = SUCCEEDED
lifecycle remediation = NOT_REQUIRED
base retry_allowed = false
duplicate_payment_blocked = false
```

任一条件不满足，T09 builder 必须 fail-closed 返回 `None`，业务结果不得变化。

### AC-04 — Product call-path insertion

`assess_webshop_payment_fulfilment` 必须保持：

```text
先完成现有 payment recovery / conflict / lifecycle 业务计算
→ 构造 authoritative_trace=None 的 frozen base outcome
→ 尝试现有 T01 builder
→ 若 T01 不成立，再尝试 T09 builder
→ replace(base_outcome, authoritative_trace=trace_or_None)
```

也可以使用一个仅负责选择已构造 trace 的等价调用方式，但：

- 不得改变业务计算顺序；
- 不得让 runner 或测试事后注入 trace；
- 不得同时返回多个 trace；
- T01 和 T09 条件必须互斥、fail-closed。

### AC-05 — Strict validator acceptance

真实 T09 产品调用必须得到：

```text
source = PRODUCT_OBSERVED
profile = WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2
status = VALID
events = 11
unique bindings = 10
product source = webshop_payment_fulfilment_outcome
```

关键状态：

```text
CURRENT_PAYMENT_CANDIDATE = PENDING
PAYMENT_EXECUTION_OUTCOME = SUCCEEDED
RECOVERY_OUTCOME = RECOVERED
FINAL_OUTCOME = SUCCEEDED
```

所有 source ref、binding ref、entity ref、relation 和 value path 必须通过冻结 validator。

### AC-06 — Same-baseline project impact

使用同一 accepted fixture、runner 和 `repeat=3`：

```text
BEFORE:
Product Trace = 2/12
GESR = 1/12
valid product tasks = T01, T10
T09 trace = NOT_AVAILABLE
T09 matched = false

AFTER:
Product Trace = 3/12
GESR = 2/12
valid product tasks = T01, T09, T10
T09 trace = VALID
T09 matched = true
T09 capability_gaps = []
```

三次 normalized hash 必须一致。只允许 T09 新增产品轨迹。

### AC-07 — T09 business and safety invariance

T09 以下结果必须保持：

```text
decision = ALLOW
callback count = 1
callback observations = 1
retry count = 0
initial payment = UNKNOWN
effective payment = SUCCEEDED
recovery = RECOVERED
fulfilment = SUCCEEDED
task = SUCCEEDED
remediation = NOT_REQUIRED
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

T10 full trace SHA-256
= 2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3
```

产品轨迹只能存在于：

```text
T01
T09
T10
```

以下仍不得产生新 trace：

- T02—T08；
- T11；
- T12；
- T09 query observation 缺失；
- query recovery 非 `RECOVERED`；
- observed/effective status 非 `SUCCEEDED`；
- payment ID 不一致；
- recovery retry_allowed=true；
- status conflict 存在；
- lifecycle 非完整成功；
- candidate 非 `PENDING`；
- retained gate facts 缺失或矛盾。

### AC-09 — Measuring instrument and business boundary freeze

不得修改：

- `scripts/validation/run_project_impact_baseline.py`；
- `src/agentic_payment_experiment/authoritative_trace.py`；
- `src/agentic_payment_experiment/webshop_runtime_gate.py`；
- `src/agentic_payment_experiment/webshop_authoritative_trace.py`；
- baseline/target fixtures；
- projection/formula/profile registry；
- 项目地图；
- recovery、conflict、lifecycle、payment 或 binding 业务模块。

所有冻结哈希必须保持。

### AC-10 — Tests and evidence

运行：

```text
python3 -m unittest \
  tests.test_webshop_trace_assembler \
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
- full 至少 `498` 项且全部通过；
- baseline repeat=3 normalized hash 一致；
- 保存 T09 exact 11-event/10-binding 结构；
- 保存 T01/T10 full trace hash；
- 保存 non-trace hash、producer coverage 和冻结边界审计；
- workflow validator 为 `OK`。

## Validation plan

| VP | Exact action | Expected result |
|---|---|---|
| VP-01 | 真实 T09 gate + sidecar 调用 | sidecar product trace 为 `VALID / 11 events / 10 bindings` |
| VP-02 | T09 状态与 projection 审计 | candidate PENDING、payment SUCCEEDED、recovery RECOVERED、final SUCCEEDED |
| VP-03 | T09 negative matrix | 缺失、矛盾、非恢复成功条件全部 `None` |
| VP-04 | baseline repeat=3 | Product Trace `3/12`、GESR `2/12`，三次 normalized hash 一致 |
| VP-05 | non-trace canonical projection | SHA-256 保持 `6eb5...9099dc` |
| VP-06 | T01/T10 full trace | 两条冻结 hash 完全不变 |
| VP-07 | producer coverage scan | 产品轨迹仅 T01、T09、T10 |
| VP-08 | frozen hash audit | runner、validator、gate、T10 builder、fixtures、registries 全部不变 |
| VP-09 | focused/full unittest | focused 全过；full 至少 498 项全过 |
| VP-10 | workflow validator | `OK` |

## Allowed scope

可修改：

- `src/agentic_payment_experiment/webshop_trace_assembler.py`（仅增加中立 recovery/result projection）；
- `src/agentic_payment_experiment/webshop_happy_path_authoritative_trace.py`（仅允许切换到中立 result projection，T01 hash 必须不变）；
- `src/agentic_payment_experiment/webshop_unknown_payment_authoritative_trace.py`（新增）；
- `src/agentic_payment_experiment/webshop_payment_sidecar.py`（仅增加 T09 builder 调用/选择）；
- `tests/test_webshop_trace_assembler.py`；
- `tests/test_webshop_unknown_payment_authoritative_trace.py`（新增）；
- `tests/test_webshop_payment_sidecar.py`；
- `tests/test_project_impact_baseline.py`；
- 本任务 `REPORT.md`；
- 本任务 `evidence/EV-*`；
- `CURRENT.md`（仅 `CONTRACT_FROZEN → EXECUTING`）。

工作区继承此前已接受但未提交的 P9 产物。不得清理、重置、覆盖或回退继承内容。

## Exclusions

- 不修改 runner、validator、gate、T10 builder、fixtures、registry、profiles 或项目地图；
- 不新增 T02—T08、T11、T12 产品轨迹；
- 不改变 payment recovery、status conflict、lifecycle、authorization、confirmation、binding、Runtime Gate 或 side-effect 业务规则；
- 不保留 query observation 原对象、完整 GateContext、callback、credential、页面、prompt 或隐藏上下文；
- 不使用 evaluator replay、fixture、docs 或 evidence 构造产品 trace；
- 不调用网络、LLM、外部 API、WebShop runtime、Buy Now、钱包、支付或订单；
- 不安装依赖、不创建环境；
- 不提交、不推送、不改写历史；
- 不清理、删除、重置或回退继承产物。

## Stop conditions

立即停止并报告，不得扩大范围：

- 需要修改 runner、validator、fixture、registry、profile、gate 或 T10 builder；
- 需要修改 recovery、conflict、lifecycle 或其他业务规则；
- 无法仅靠当前 retained/product facts 构造 T09 trace；
- 需要保留 query observation 原对象或完整隐藏上下文；
- T01/T10 full trace hash 变化；
- non-trace hash 或安全守护线变化；
- T09 之外出现新产品 trace；
- 11 events / 10 bindings 无法闭合；
- 需要网络、真实支付、依赖安装或新环境。

## Required report

REPORT 必须包含：

- exact changed files 和 SHA-256；
- 中立 assembler 新增的 projection；
- T09 builder 的真实事实输入与 fail-closed 条件；
- exact 11-event / 10-binding 结构；
- candidate/initial/effective payment 与 recovery 状态关系；
- baseline repeat=3 before/after；
- Product Trace `2/12 → 3/12`；
- GESR `1/12 → 2/12`；
- T09 business/non-trace invariance；
- T01/T10 full trace hashes；
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

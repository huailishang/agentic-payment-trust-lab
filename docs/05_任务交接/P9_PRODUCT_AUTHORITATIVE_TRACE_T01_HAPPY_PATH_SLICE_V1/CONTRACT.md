# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-T01-HAPPY-PATH-SLICE-V1`  
Task name: T01 正常购买成功链产品权威轨迹切片  
Task kind: `capability_experiment`  
Risk: `L2`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-06-r6`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Parent repair: `P9-PRODUCT-AUTHORITATIVE-TRACE-PROVENANCE-DIAGNOSTIC-REPAIR-V1`  
Parent verdict: `PASS / NOT_APPLICABLE`

Metric baseline: accepted runner 下，产品权威轨迹为 `1/12`，baseline GESR 为 `0/12`；T01 除产品轨迹外所有 capability dimension 已匹配。  
Estimated affected scope: 本轮直接影响固定任务 `T01`，即 `1/12`；不得扩展到 T09、T11、T12 或其他任务。  
Expected project impact: T01 产品轨迹从 `NOT_AVAILABLE` 提升到 `VALID`，Product Trace 从 `1/12` 提升到 `2/12`，baseline GESR 从 `0/12` 提升到 `1/12`；业务和安全守护线不变。  
Rollback condition: runner、validator、fixture、registry 或 non-trace hash 变化，T01 决策/callback/payment/fulfilment/lifecycle 变化，或除 T01 外出现新 trace producer 时立即回滚。

## Active bottleneck and hypothesis

```text
当前：
T10 拒绝链 product trace = VALID
其余 11 项 = NOT_AVAILABLE

本轮验证：
正常授权购买成功链
→ 产品自己保留构轨迹所需的最小不可变事实
→ sidecar outcome 直接携带 T01 完整轨迹
→ 不依赖 runner 隐藏上下文
```

本轮不是增加新的授权、支付或履约规则，而是让现有成功链的产品事实形成可验证输出。

## Accepted measuring instrument

| 项目 | 接受值 |
|---|---|
| Runner SHA-256 | `70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3` |
| Measurement module SHA-256 | `07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a` |
| Baseline fixture SHA-256 | `4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5` |
| BEFORE baseline output SHA-256 | `992653a63194c391ae30f7c48bf02c34ed50cfe0b87c12914851f8572f95e26a` |
| BEFORE baseline normalized SHA-256 | `f1aa119f14e88b7a15bdcc40760391692d6ba5c9a5d795f093d0bda0d8dfb5bc` |
| Non-trace projection SHA-256 | `6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc` |
| Formula registry | `2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd` |
| Projection registry | `45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4` |
| Profiles | `6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2` |
| Runtime contract | `4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e` |

## Single principal change

只让 T01 正常购买成功链的 `WebShopPaymentFulfilmentOutcome` 直接携带 `ProductAuthoritativeTrace`。

为避免 sidecar 偷读 runner `GateContext`，允许在 gate outcome 中最小留存三项本次调用已经存在的不可变事实：

```text
authorized_order_snapshot: Order | None
governed_action: GovernedPaymentAction | None
execution_candidate: PaymentExecutionRecord | None
```

规则：

1. 三项字段默认 `None`；
2. 只在成功进入 Runtime Gate 的产品路径按真实对象填充；
3. 不重新构造、不从 fixture 或 runner 反推；
4. 不进入现有 RESULT projection 和 non-trace 项目指标；
5. 这些字段只是事实留存，不承担新的授权或业务判定。

Sidecar outcome 增加：

```text
authoritative_trace: ProductAuthoritativeTrace | None = None
```

只有 T01 满足 exact happy-path 条件时非空。

## T01 exact profile

Profile：`WEBSHOP_NORMAL_PURCHASE_V2`

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
10 FULFILMENT_OUTCOME_RECORDED [FULFILMENT_OUTCOME]
11 RESULT_RECORDED [FINAL_OUTCOME]
```

固定结构：

```text
11 events
10 unique source bindings
AUTHORIZED_ORDER_SNAPSHOT 与 CURRENT_ORDER_SNAPSHOT 共享 1 个 Order binding
CURRENT_PAYMENT_CANDIDATE = 执行前 PENDING payment projection
PAYMENT_EXECUTION_OUTCOME = 执行后 SUCCEEDED payment projection
两者 payment_id 相同，但 projection/binding 不同
```

## T01 exact happy-path conditions

Builder 只有同时满足以下条件才返回 trace：

```text
gate decision = ALLOW
gate checkout_executed = true
gate callback_count = 1
gate runtime final_decision = ALLOW
governed action fact = VALID
retained governed action / candidate / authorized order 均存在
retained candidate status = PENDING
authorized order projection = current order projection
sidecar ready = true
initial/effective payment status = SUCCEEDED
payment_id 与 retained candidate payment_id 相同
fulfillment status = SUCCEEDED
lifecycle payment status = SUCCEEDED
lifecycle fulfillment status = SUCCEEDED
lifecycle task status = SUCCEEDED
query_recovery = None
status_conflict = None
retry_allowed = false
duplicate_payment_blocked = false
```

任一条件不成立，`authoritative_trace=None`，业务结果不得改变。

## Acceptance criteria

### AC-01 — Minimal fact retention

`WebShopBuyNowGateOutcome` 增加三个默认 `None` 的 frozen 字段，并在成功 gate 路径保留真实对象：

- authorized order snapshot；
- governed action；
- execution candidate。

不得保留完整 `GateContext`，不得保留 callback、credential、原始页面或 runner 对象。

### AC-02 — Sidecar outcome boundary

`WebShopPaymentFulfilmentOutcome` 保持 frozen，新增默认 `None` 的 `authoritative_trace`。

`to_dict()` 和冻结 RESULT projection 不得包含 trace 自身，避免循环引用。

### AC-03 — Pure T01 builder

新增一个 T01 专用纯 builder：

- 只读取 gate outcome、adaptation、mandate、payment、fulfillment 和已经形成的 sidecar base outcome；
- 不调用授权、订单校验、binding、payment recovery、status conflict 或 lifecycle 业务函数；
- 不读取 runner、fixture、docs、CURRENT、evidence、文件、环境、当前时间或随机数；
- 任一事实缺失或矛盾时返回 `None`。

### AC-04 — Product call-path insertion

`assess_webshop_payment_fulfilment` 必须：

```text
先完成现有 sidecar 业务计算
→ 构造 authoritative_trace=None 的 frozen base outcome
→ 使用本次调用已有事实构造 T01 trace
→ replace(base_outcome, authoritative_trace=trace)
```

runner 和测试不得事后注入 trace。

### AC-05 — Strict validator acceptance

真实 T01 产品调用必须得到：

```text
source = PRODUCT_OBSERVED
profile = WEBSHOP_NORMAL_PURCHASE_V2
status = VALID
events = 11
unique bindings = 10
product source = webshop_payment_fulfilment_outcome
```

所有 source ref、binding ref、entity ref、relation target 和 event value 必须由冻结 validator 通过。

### AC-06 — Same-baseline impact

使用同一 accepted baseline fixture、同一 runner、`repeat=3`：

```text
BEFORE:
Product Trace = 1/12
GESR = 0/12
T01 trace = NOT_AVAILABLE

AFTER:
Product Trace = 2/12
GESR = 1/12
T01 trace = VALID
T01 matched = true
T01 capability_gaps = []
```

只允许 T01 新增产品轨迹。T10 必须继续 `VALID`。

### AC-07 — Non-trace and safety invariance

以下必须保持：

```text
non-trace projection SHA-256
= 6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

T01 业务结果必须保持：

```text
decision = ALLOW
callback count = 1
callback observations = 1
retry count = 0
payment status = SUCCEEDED
fulfilment status = SUCCEEDED
task status = SUCCEEDED
remediation status = NONE
retry_allowed = false
forbidden_side_effects = []
```

### AC-08 — Other paths fail closed

以下必须保持 `authoritative_trace=None`：

- T02—T06 prepayment/action failure；
- T09 recovery；
- T10 duplicate preflight；T10 gate trace 本身继续存在，但 sidecar 不新增 T01 trace；
- T11 fulfilment failure；
- T12 status conflict；
- callback failure；
- gate outcome 缺 retained facts；
- candidate 与 payment ID 不同；
- candidate 非 PENDING；
- payment 非 SUCCEEDED；
- fulfillment 非 SUCCEEDED；
- lifecycle 非 SUCCEEDED；
- query recovery、conflict、retry 或 duplicate protection 非空/为真。

### AC-09 — Measuring instrument freeze

不得修改：

- `scripts/validation/run_project_impact_baseline.py`；
- `src/agentic_payment_experiment/authoritative_trace.py`；
- `samples/`；
- projection/formula/profile registry；
- T01 fixture 业务预期或 trace 事件目标；
- T10 trace producer。

所有接受哈希必须保持。

### AC-10 — Tests and evidence

运行：

```text
python3 -m unittest \
  tests.test_webshop_runtime_gate \
  tests.test_webshop_payment_sidecar \
  tests.test_authoritative_trace \
  tests.test_project_impact_baseline -v

python3 -m unittest discover -s tests -p 'test_*.py'

python3 scripts/validation/run_project_impact_baseline.py \
  --repeat 3 \
  --output <evidence>/EV-AFTER-baseline.json
```

要求：

- 全量至少 `489` 项且全部通过；
- baseline 三次 normalized hash 完全一致；
- 保存 T01 before/after、11-event/10-binding 结构、non-trace projection、producer 范围和冻结哈希；
- workflow validator 为 `OK`。

## Validation plan

| VP | Exact action | Expected result |
|---|---|---|
| VP-01 | 真实 T01 gate + sidecar 调用 | sidecar product trace 为 `VALID / 11 events / 10 bindings` |
| VP-02 | baseline repeat=3 | Product Trace `2/12`、GESR `1/12`，三次 normalized hash 一致 |
| VP-03 | T01 before/after 字段比较 | 只增加 product trace、authoritative_trace evidence stage 及其派生 matched 字段 |
| VP-04 | non-trace canonical projection | SHA-256 保持 `6eb5...9099dc` |
| VP-05 | T09/T10/T11/T12 与异常矩阵 | sidecar T01 trace 均为 `None`；T10 gate trace 继续 `VALID` |
| VP-06 | runner/module/fixture/registry hash audit | 全部保持 accepted 值 |
| VP-07 | focused/full unittest | focused 全过；full 至少 `489` 项全过 |
| VP-08 | workflow validator | `OK` |

## Allowed scope

可修改：

- `src/agentic_payment_experiment/webshop_runtime_gate.py`
- `src/agentic_payment_experiment/webshop_payment_sidecar.py`
- `src/agentic_payment_experiment/webshop_happy_path_authoritative_trace.py`（新增）
- `tests/test_webshop_runtime_gate.py`
- `tests/test_webshop_payment_sidecar.py`
- `tests/test_project_impact_baseline.py`
- 本任务 `REPORT.md`
- 本任务 `evidence/EV-*`
- `CURRENT.md`（仅 `CONTRACT_FROZEN → EXECUTING`）

工作区继承此前已接受但未提交的 P9 产物。不得清理、重置、覆盖或回退继承内容。

## Exclusions

- 不修改 runner、validator、fixtures、registry 或项目地图；
- 不增加 T02—T09、T11、T12 的新产品 trace producer；
- 不改变授权、确认、binding、Runtime Gate、payment、recovery、conflict、lifecycle 或 side-effect 业务规则；
- 不使用 runner `GateContext`、fixture、docs 或 evidence 构造产品轨迹；
- 不把 evaluator Replay 计入产品轨迹；
- 不执行真实 WebShop、真实 Buy Now、真实支付、钱包、订单或网络副作用；
- 不调用网络、LLM 或外部 API；
- 不安装依赖、不创建环境；
- 不提交、不推送、不改写历史。

## Stop conditions

- 需要修改 runner、validator 或 fixture；
- 无法仅靠产品公开/留存事实构造 T01 trace；
- 需要保留完整 GateContext 或外部隐藏对象；
- T01 之外出现新产品 trace；
- T10 trace 退化；
- non-trace hash 或安全守护线变化；
- 11 events / 10 bindings 无法闭合；
- 需要外部副作用或新依赖。

## Required report

REPORT 必须包含：

- exact changed files；
- 三项最小事实留存说明；
- T01 trace 构造路径；
- exact 11-event / 10-binding 结构；
- baseline repeat=3 before/after；
- Product Trace `1/12 → 2/12`；
- GESR `0/12 → 1/12`；
- T01 非轨迹字段与 non-trace hash；
- T09/T11/T12/T10 sidecar fail-closed 证据；
- runner/module/fixtures/registry freeze hashes；
- focused/full tests 原始证据；
- workflow validator；
- task verdict candidate 与 project-impact candidate。

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

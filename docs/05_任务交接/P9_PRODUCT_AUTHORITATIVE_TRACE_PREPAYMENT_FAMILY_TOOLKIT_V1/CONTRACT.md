# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-PREPAYMENT-FAMILY-TOOLKIT-V1`  
Task name: 付款前校验场景族通用轨迹工具包 V1  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `capability_experiment`  
Risk: `L2`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-06-r10`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-SIDECAR-FAMILY-TOOLKIT-V1`  
Parent verdict: `PASS / IMPROVED`  
Metric baseline: 同一 accepted baseline 中 Product Trace 为 `4/12`、GESR 为 `3/12`；T02、T03、T04 的业务判断已经匹配，唯一共同 capability gap 是产品轨迹为 `NOT_AVAILABLE`。  
Estimated affected scope: 本轮直接覆盖结构完全相同的 T02、T03、T04，即 `3/12`；不得扩展 T05—T08、T11 或修改已有 T01/T09/T10/T12。  
Expected project impact: Product Trace 从 `4/12` 提升到 `7/12`、GESR 从 `3/12` 提升到 `6/12`，T02/T03/T04 均从不匹配变为完全匹配；其他 9 项业务和安全结果不变。  
Rollback condition: 任一付款前业务判断、callback、既有完整轨迹、non-trace hash、冻结测量边界发生变化；新增 T02/T03/T04 专属完整 builder；或 T05—T08/T11 出现新产品轨迹时，立即回滚本任务实现。

## Why this package

T02、T03、T04 的冻结轨迹合同完全同构：

```text
1 AUTHORITY_RECORDED [AUTHORITY]
2 ORDER_RECORDED [AUTHORIZED_ORDER_SNAPSHOT]
3 ORDER_RECORDED [CURRENT_ORDER_SNAPSHOT]
4 REQUEST_RECORDED [CURRENT_REQUEST]
5 PREPAYMENT_DECISION_RECORDED [PREPAYMENT_VALIDATION]
6 RESULT_RECORDED [FINAL_OUTCOME]
```

三项差异只在场景事实：

```text
T02：价格上涨，decision = CONFIRMATION_REQUIRED
T03：价格下降，decision = CONFIRMATION_REQUIRED
T04：收款方变化，decision = INDETERMINATE
```

其中 T02 与 T03 的问题码相同：

```text
order_total_changed
order_item_unit_amount_changed
```

因此不能仅依赖 reason code 区分，必须读取已有的授权订单与当前订单，按金额变化方向选择唯一 Profile。

本任务不得把三个场景拆成三个 builder。实现单位必须是：

```text
一个 Prepayment Trace Toolkit
+ 三个固定声明式 Profile
```

## Single objective

只做一个主要 capability change：

> 在现有 Trace Assembler 之上建立一个受控的 Prepayment Trace Toolkit，用一次公共事实闭合、一次公共 6-event 组装和三个固定 Profile，为 T02/T03/T04 生成产品权威轨迹。

目标产品调用：

```text
validate_request 已完成
→ 形成 WebShopBuyNowGateOutcome base outcome
→ 只调用一次 build_prepayment_product_trace(...)
→ exactly-one Profile 匹配
→ 输出 6-event / 6-binding 产品轨迹
→ replace(base_outcome, authoritative_trace=trace_or_None)
```

不得修改 `validate_request`、付款前决策、确认语义或订单比较规则。

## Entering baseline

### Measurement baseline

```text
baseline path
= docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PREPAYMENT_FAMILY_TOOLKIT_V1/evidence/BASELINE-before.json

baseline output SHA-256
= b3fba30058acb1c421786cae0b5a93d3e7fdcf22aa6c4a5fa0f51dc821435a34

repeat=3 normalized SHA-256
= 6bab1053d389ac181a701a5701b0f523ed9bb864323fd1ad51fd53ceefa09b8c

Product Trace = 4/12
GESR = 3/12
valid product tasks = T01, T09, T10, T12
non-trace SHA-256
= 6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

### Architecture baseline

```text
path
= docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PREPAYMENT_FAMILY_TOOLKIT_V1/evidence/BASELINE-architecture.json

SHA-256
= 17bfdad851add911c1ad8d7b06f7eab163da7260a2cd6811d75da51883330a32
```

### Existing full trace invariants

```text
T01
= 7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906

T09
= a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e

T10
= 2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3

T12
= ebb38113abb2582d52f434b1a1b30247cc68ee8f4b57c0c18f52efa37bb1c230
```

### Frozen architecture hashes

```text
webshop_sidecar_trace_profiles.py
= eb03ed375c3cb5c0b2a80ad248b4de00e833c007e8dfb687f742d97cca643941

webshop_sidecar_trace_toolkit.py
= 1ccf37b62f6eedc0eff41216ec983ddaea74aed7a0e0529be686f6b15aefbbf3

webshop_payment_sidecar.py
= e74939a0b1da9eba5e70f34ab8f745ac61e8ae2254c2ab823ee92c5299a210c8

webshop_authoritative_trace.py / T10
= 9653277777d06ce8d2c65862765ec57c17874a9d311d2c5c9c117993a0feeac8
```

### Frozen measuring boundaries

```text
scripts/validation/run_project_impact_baseline.py
= 70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3

src/agentic_payment_experiment/authoritative_trace.py
= 07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a

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

## Minimal toolkit design

### Fixed scenario kind

建议使用固定枚举：

```text
PrepaymentScenarioKind
- PRICE_INCREASE
- PRICE_DECREASE
- PAYEE_CHANGE
```

### Fixed profile model

建议使用 frozen dataclass：

```text
PrepaymentTraceProfile
- profile_name
- scenario_kind
- expected_decision
- required_issue_codes
- required_difference_codes
```

Profile 只允许固定枚举和值，不允许：

- 任意字段路径；
- 字符串表达式；
- Python `eval` / `exec`；
- 动态 import；
- YAML/JSON 运行时配置；
- 用户输入 Profile；
- 通用规则引擎。

### Fixed profile registry

V1 只允许：

```text
T02 / WEBSHOP_PREPAYMENT_T02_V2 / PRICE_INCREASE
T03 / WEBSHOP_PREPAYMENT_T03_V2 / PRICE_DECREASE
T04 / WEBSHOP_PREPAYMENT_T04_V2 / PAYEE_CHANGE
```

不得加入 T05、T06、T07、T08、T11。

### Common facts

Toolkit 只能读取当前调用已经存在的不可变事实：

- `IntentMandate`；
- 授权订单快照 `Order`；
- 当前订单快照 `Order`；
- 已绑定的 `TransactionRequest`；
- 已计算的 `ValidationResult`；
- 已构造、但尚未附加轨迹的 `WebShopBuyNowGateOutcome`。

不得重新调用 `validate_request`，不得重新计算订单差异。

### T02/T03 direction rule

T02/T03 不能只看问题码。必须同时满足：

```text
ValidationResult decision = CONFIRMATION_REQUIRED
issue codes = order_item_unit_amount_changed + order_total_changed
order difference codes 与上述变化一致
授权订单与当前订单具有同一业务身份
```

方向判定：

```text
PRICE_INCREASE
→ current.total_amount > authorized.total_amount
→ 所有发生 unit_amount 变化的同 item_id 商品均 current > authorized

PRICE_DECREASE
→ current.total_amount < authorized.total_amount
→ 所有发生 unit_amount 变化的同 item_id 商品均 current < authorized
```

任一混合方向、无法对应 item_id、金额相等、附加其他 material difference，均不匹配 T02/T03。

### T04 rule

T04 必须同时满足：

```text
ValidationResult decision = INDETERMINATE
issue codes = order_payee_changed
order_differences = empty
authorized.payee != current.payee
金额、币种、商品集合及商品关键字段保持一致
```

不得把其他结构错误、缺失证据或多个异常合并场景误识别为 T04。

## Acceptance criteria

### AC-01 — One Prepayment Toolkit

新增一个中立模块：

```text
src/agentic_payment_experiment/webshop_prepayment_trace_toolkit.py
```

可选新增：

```text
src/agentic_payment_experiment/webshop_prepayment_trace_profiles.py
```

要求：

- 公共事实闭合只实现一次；
- Profile 选择只实现一次；
- 6 个事件只组装一次；
- `assemble_product_trace()` 只调用一次；
- 模块名和公共 API 不包含 T02/T03/T04；
- 不调用付款前校验或其他业务函数。

### AC-02 — Declarative profiles, no per-task builders

必须满足：

```text
prepayment profile count = 3
profile names = T02/T03/T04 三个冻结 profile
T02/T03/T04 dedicated authoritative trace files = 0
build_t02_* / build_t03_* / build_t04_* functions = 0
```

Profile 不得包含完整事件构造函数。

### AC-03 — Exactly-one profile selection

```text
0 个 Profile 匹配 → None
1 个 Profile 匹配 → 构造对应轨迹
2 个及以上 Profile 匹配 → None
```

独立测试必须覆盖：

- T02 唯一匹配；
- T03 唯一匹配；
- T04 唯一匹配；
- 普通 ALLOW 场景零匹配；
- 其他 CONFIRMATION_REQUIRED 场景零匹配；
- 混合涨跌方向零匹配；
- 人工重叠 Profile 多匹配 fail-closed。

### AC-04 — One product call path

`webshop_runtime_gate.py` 的早期付款前非 ALLOW 分支必须变成：

```text
validate_request 已完成
→ 构造 authoritative_trace=None 的 base outcome
→ 只调用一次 build_prepayment_product_trace(...)
→ replace(base_outcome, authoritative_trace=trace_or_None)
```

要求：

- 不重新调用 `validate_request`；
- 不改变 callback 路径；
- T02/T03/T04 callback 仍为 `0`；
- 不影响后续 Action Binding、Known Payment Attempt、Runtime Gate 和 Sidecar 路径；
- 一次产品调用最多返回一条轨迹。

### AC-05 — Exact six-event trace

三条轨迹均必须严格为：

```text
1 AUTHORITY_RECORDED [AUTHORITY]
2 ORDER_RECORDED [AUTHORIZED_ORDER_SNAPSHOT]
3 ORDER_RECORDED [CURRENT_ORDER_SNAPSHOT]
4 REQUEST_RECORDED [CURRENT_REQUEST]
5 PREPAYMENT_DECISION_RECORDED [PREPAYMENT_VALIDATION]
6 RESULT_RECORDED [FINAL_OUTCOME]
```

要求：

- `source = PRODUCT_OBSERVED`；
- `product source = webshop_gate_outcome`；
- `events = 6`；
- `unique bindings = 6`；
- 授权订单与当前订单必须使用不同 binding；
- request 必须绑定当前订单与 mandate；
- validation event 的 decision 和 issue codes 来自真实 `ValidationResult`；
- final event 的 decision 和 reason codes 来自真实 `WebShopBuyNowGateOutcome`。

### AC-06 — Neutral projections

`webshop_trace_assembler.py` 可新增：

```text
project_validation_result
project_webshop_gate_outcome
```

要求：

- 严格匹配冻结 `validation-result-trace/v2`；
- 严格匹配冻结 `webshop-buy-now-gate-outcome-result-trace/v2`；
- 不导入 runtime gate 模块；
- 不包含场景判断；
- 不调用业务函数；
- 不改变已有 projection 输出。

### AC-07 — Exact T02 validation

真实 T02 产品调用必须得到：

```text
profile = WEBSHOP_PREPAYMENT_T02_V2
decision = CONFIRMATION_REQUIRED
validator = VALID
events = 6
bindings = 6
matched = true
capability_gaps = []
```

必须证明：

```text
current total > authorized total
changed item unit amount direction = increase
```

### AC-08 — Exact T03 validation

真实 T03 产品调用必须得到：

```text
profile = WEBSHOP_PREPAYMENT_T03_V2
decision = CONFIRMATION_REQUIRED
validator = VALID
events = 6
bindings = 6
matched = true
capability_gaps = []
```

必须证明：

```text
current total < authorized total
changed item unit amount direction = decrease
```

### AC-09 — Exact T04 validation

真实 T04 产品调用必须得到：

```text
profile = WEBSHOP_PREPAYMENT_T04_V2
decision = INDETERMINATE
validator = VALID
events = 6
bindings = 6
matched = true
capability_gaps = []
```

必须证明：

```text
authorized payee != current payee
无金额或商品内容变化
```

### AC-10 — Same-baseline project impact

使用同一 runner、fixture 和 repeat=3：

```text
BEFORE
Product Trace = 4/12
GESR = 3/12
valid product tasks = T01, T09, T10, T12

AFTER
Product Trace = 7/12
GESR = 6/12
valid product tasks = T01, T02, T03, T04, T09, T10, T12
T02 matched = true
T03 matched = true
T04 matched = true
capability_gaps = [] for T02/T03/T04
```

三次 normalized hash 必须一致。

### AC-11 — Business and safety invariance

全项目 non-trace projection SHA-256 必须保持：

```text
6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

特别保持：

```text
T02 decision = CONFIRMATION_REQUIRED
T03 decision = CONFIRMATION_REQUIRED
T04 decision = INDETERMINATE
T02/T03/T04 callback count = 0
T02/T03/T04 retry count = 0
forbidden side effects = []
```

不得更改任何付款前问题码、订单差异、确认逻辑或最终 decision。

### AC-12 — Existing trace and toolkit invariance

必须保持：

```text
T01 full trace hash = 7c47cb15...
T09 full trace hash = a596f5f3...
T10 full trace hash = 2b97fd1f...
T12 full trace hash = ebb38113...
```

以下文件 hash 必须保持 entering baseline：

- `webshop_sidecar_trace_profiles.py`；
- `webshop_sidecar_trace_toolkit.py`；
- `webshop_payment_sidecar.py`；
- `webshop_authoritative_trace.py`。

### AC-13 — Coverage remains bounded

产品轨迹只能存在于：

```text
T01, T02, T03, T04, T09, T10, T12
```

以下仍不得新增产品轨迹：

```text
T05, T06, T07, T08, T11
```

不得把 Action Binding、Attack Overlay 或履约失败场景塞入 Prepayment Toolkit。

### AC-14 — Complexity guardrail

AST / 源码审计必须证明：

```text
webshop_runtime_gate.py
- prepayment toolkit import = 1
- prepayment toolkit builder call = 1
- validate_request 新增调用 = 0

prepayment toolkit
- assemble_product_trace call = 1
- fixed profile registry count = 3
- dynamic config loader = 0
- eval / exec / dynamic import = 0

T02/T03/T04 dedicated trace modules = 0
build_t02_* / build_t03_* / build_t04_* = 0
```

### AC-15 — Frozen boundaries

不得修改：

- `scripts/validation/run_project_impact_baseline.py`；
- `src/agentic_payment_experiment/authoritative_trace.py`；
- `src/agentic_payment_experiment/webshop_authoritative_trace.py`；
- Sidecar Toolkit 与 Sidecar Profile；
- `src/agentic_payment_experiment/webshop_payment_sidecar.py`；
- fixtures；
- formula/projection/profile/runtime registries；
- `validator.py`、订单比较、确认、Action Binding、Runtime Gate、payment、recovery、conflict、lifecycle 业务模块；
- 项目地图。

`webshop_runtime_gate.py` 只允许在已有早期付款前非 ALLOW 返回分支附加产品轨迹，不得修改其他分支行为。

### AC-16 — Tests and evidence

至少运行：

```text
python3 -m unittest \
  tests.test_webshop_trace_assembler \
  tests.test_webshop_prepayment_trace_toolkit \
  tests.test_webshop_runtime_gate \
  tests.test_webshop_sidecar_trace_toolkit \
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
- full 至少 `512` 项且全部通过；
- repeat=3 一致；
- 保存 T02/T03/T04 完整轨迹；
- 保存 T01/T09/T10/T12 hash；
- 保存方向判断、零匹配、多匹配和复杂度审计；
- 保存 non-trace、producer coverage 和冻结边界证据；
- workflow validator 为 `OK`。

## Validation plan

| VP | Exact action | Expected result |
|---|---|---|
| VP-01 | Profile registry 审计 | 只有 T02/T03/T04 三个固定 Profile |
| VP-02 | T02 正例 | `VALID / 6 events / 6 bindings / PRICE_INCREASE` |
| VP-03 | T03 正例 | `VALID / 6 events / 6 bindings / PRICE_DECREASE` |
| VP-04 | T04 正例 | `VALID / 6 events / 6 bindings / PAYEE_CHANGE` |
| VP-05 | 方向与负例矩阵 | 混合方向、额外差异、缺失事实、零/多匹配全部 fail-closed |
| VP-06 | 单产品入口审计 | runtime gate 只调用一次 Prepayment Toolkit |
| VP-07 | baseline repeat=3 | Product Trace `7/12`、GESR `6/12`，三次一致 |
| VP-08 | non-trace projection | hash 保持 `6eb5...9099dc` |
| VP-09 | 既有完整轨迹 | T01/T09/T10/T12 hash 不变 |
| VP-10 | producer coverage | 仅 T01/T02/T03/T04/T09/T10/T12 |
| VP-11 | frozen boundaries | runner、contract、Sidecar、T10、fixtures、registry 保持 |
| VP-12 | focused/full unittest | focused 全过；full 至少 512 项全过 |
| VP-13 | workflow validator | `OK` |

## Allowed scope

可修改：

- `src/agentic_payment_experiment/webshop_prepayment_trace_toolkit.py`（新增）；
- `src/agentic_payment_experiment/webshop_prepayment_trace_profiles.py`（可选新增）；
- `src/agentic_payment_experiment/webshop_trace_assembler.py`（只增加中立 projection）；
- `src/agentic_payment_experiment/webshop_runtime_gate.py`（只在早期 prepayment 非 ALLOW 分支附加轨迹）；
- `tests/test_webshop_prepayment_trace_toolkit.py`（新增）；
- `tests/test_webshop_trace_assembler.py`；
- `tests/test_webshop_runtime_gate.py`；
- `tests/test_project_impact_baseline.py`；
- 本任务 `REPORT.md`；
- 本任务 `evidence/EV-*`；
- `CURRENT.md`（仅 `CONTRACT_FROZEN → EXECUTING`）。

工作区继承此前已接受但未提交的 P9 产物。不得清理、重置或回退继承内容。

## Exclusions

- 不新增 T02/T03/T04 专属 authoritative trace 模块或 build 函数；
- 不新增 T05—T08、T11 产品轨迹；
- 不修改 Sidecar Toolkit、Sidecar Profile、payment sidecar 或 T10 builder；
- 不修改 runner、validator contract、fixtures、registries 或 project map；
- 不修改 `validate_request`、订单差异、确认、付款前业务规则；
- 不建立 YAML/JSON DSL、动态表达式或用户配置 Profile；
- 不使用 runner、fixture、docs、evidence 或 evaluator replay 构造产品轨迹；
- 不执行 WebShop runtime、Buy Now、网络、LLM、支付、订单、钱包或 callback 副作用；
- 不安装依赖、不创建环境；
- 不提交、不推送、不改写历史；
- 不清理、删除、重置或回退继承产物。

## Stop conditions

立即停止并提交 `BLOCKED`：

- 无法只靠现有 mandate/order/request/ValidationResult/outcome 构造轨迹；
- T02/T03 必须重新运行订单比较才能区分；
- 需要修改付款前业务规则、fixture、registry 或 validator；
- T02/T03/T04 需要三个完整 builder；
- 混合金额方向无法 fail-closed；
- non-trace hash、callback、decision 或既有 trace hash 变化；
- T05—T08/T11 出现新产品轨迹；
- 需要网络、真实支付、依赖安装或新环境。

## Required report

REPORT 必须包含：

- exact changed files 和 SHA-256；
- Toolkit API、Profile model 与固定 registry；
- T02/T03 方向判断方法；
- T04 纯 payee-change 条件；
- exactly-one Profile 选择证据；
- 单 runtime-gate 调用路径证据；
- 无 T02/T03/T04 专属 builder 的 AST 证据；
- T02/T03/T04 exact 6-event/6-binding 轨迹及 hash；
- T01/T09/T10/T12 完整 trace hash；
- baseline repeat=3 before/after；
- Product Trace `4/12→7/12`；
- GESR `3/12→6/12`；
- non-trace/business/safety invariance；
- producer coverage；
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

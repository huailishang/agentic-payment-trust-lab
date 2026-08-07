# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-SIDECAR-FAMILY-TOOLKIT-V1`  
Task name: Sidecar 场景族通用轨迹工具包 V1  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `capability_experiment`  
Risk: `L2`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-06-r9`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Supersedes unexecuted task: `P9-PRODUCT-AUTHORITATIVE-TRACE-T12-STATUS-CONFLICT-SLICE-V1`  
Design review: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_T12_STATUS_CONFLICT_SLICE_V1/DESIGN_REVIEW.md`  
Metric baseline: 同一 accepted baseline 中 Product Trace 为 `3/12`、GESR 为 `2/12`；T01/T09/T10 为有效产品轨迹，T12 为 `NOT_AVAILABLE`。  
Estimated affected scope: 结构上直接覆盖 Sidecar 家族的 T01、T09、T12，即 `3/12`；项目指标只允许 T12 新增 `1/12`，不得扩展 T11 或其他任务。  
Expected project impact: T12 通过统一 Sidecar Toolkit 从 `NOT_AVAILABLE` 变为 `VALID`，Product Trace `3/12→4/12`、GESR `2/12→3/12`；T01/T09/T10 完整轨迹和所有 non-trace 结果不变。  
Rollback condition: 任一既有轨迹 hash、non-trace hash、业务结果或冻结测量边界变化；产品 sidecar 仍按多个场景 builder 逐个尝试；新增 T12 专属完整 builder；或 T12 之外出现新产品轨迹时，立即回滚本任务实现。

## Why this package

当前已经有两层公共能力：

```text
Trace contract / validator
→ 校验 schema、顺序、引用、binding 和 fail-closed

Trace Assembler
→ 生成 binding、event、relation 和 envelope
```

但 Sidecar 场景层仍是：

```text
T01 builder：597 行
T09 builder：595 行
产品 sidecar：依次调用 T01 → T09
旧 T12 合同：计划再新增一个 T12 builder
```

结构审计证明 T01、T09、T12：

```text
11 个事件中，事件 1—9 完全相同
事件 11 都是 FINAL_OUTCOME
只有事件 10 和状态条件不同
```

因此下一步不是增加第三个完整 builder，而是建立一个受控的 Sidecar 场景族工具层。

## Single objective

只做一个主要变化：

> 把 T01/T09 的公共事实提取、事件 1—9、事件 11、唯一 Profile 选择和 fail-closed 规则收敛为一个 `Sidecar Trace Toolkit`；T01/T09 迁移为声明式 Profile，并仅新增一个 T12 Profile 来验证该工具包。

目标结构：

```text
webshop_trace_assembler.py
→ 通用 projection / binding / event / relation / envelope

webshop_sidecar_trace_toolkit.py
→ 公共事实闭合
→ Profile 唯一匹配
→ 公共事件 1—9
→ 扩展事件 10
→ FINAL_OUTCOME 事件 11
→ 输出唯一产品轨迹

webshop_payment_sidecar.py
→ 只调用一次 build_sidecar_product_trace(...)
```

## Entering baseline

Baseline architecture evidence:

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_SIDECAR_FAMILY_TOOLKIT_V1/
evidence/BASELINE-architecture.json
```

SHA-256:

```text
bc8bdf064cb18e8afc390d08f8af5313a0a8295925ddccefb0ecf553e6c44616
```

Accepted measurement and current freeze rerun:

```text
current freeze path
= evidence/BASELINE-before.json

baseline output SHA-256
= a38b2d91bc6e636201c9ab94c4bced1ad6653dadffb32811cb996d7ab0141086

repeat=3 normalized SHA-256
= ee99b8bf73092ef09d0b890d74b66323963bebf10c1a1b4cecf2f5cbc32d8399

Product Trace = 3/12
GESR = 2/12
valid product tasks = T01, T09, T10
non-trace SHA-256
= 6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

Existing full trace invariants:

```text
T01
= 7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906

T09
= a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e

T10
= 2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3
```

Current architecture hashes:

```text
webshop_happy_path_authoritative_trace.py
= f78c2a6b66cd84580a693a21907c70e58a0f387c2ffcdba3030be7b71855f306

webshop_unknown_payment_authoritative_trace.py
= 790351ef8e618f506e597a1e568c2f59873e4dad2dfd4de978a350d3e7c9775f

webshop_trace_assembler.py
= 4e053bdefe812c54f0e6002d6c8d2d6caadac98883fc2db3f776724852991d5b

webshop_payment_sidecar.py
= b6976cbe4763d771de399600d86d030e5294326062aa5f401b8368786e67fb10
```

Frozen measuring boundaries:

```text
scripts/validation/run_project_impact_baseline.py
= 70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3

src/agentic_payment_experiment/authoritative_trace.py
= 07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a

src/agentic_payment_experiment/webshop_runtime_gate.py
= 5abf1a6f08060e111b6fbd9ba96809c2823ef07adee0e23b6d60a6c50c06bdef

src/agentic_payment_experiment/webshop_authoritative_trace.py
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

## Minimal toolkit design

### 1. Fixed profile model

建议使用冻结 dataclass / Enum，例如：

```text
SidecarExtensionKind
- FULFILMENT
- RECOVERY
- STATUS_CONFLICT

SidecarTraceProfile
- profile_name
- initial_payment_status
- effective_payment_status
- recovery_status / optional
- conflict_resolution / optional
- lifecycle_payment_status
- lifecycle_fulfilment_status
- lifecycle_task_status
- remediation_status
- extension_kind
```

Profile 只允许固定枚举和明确字段，不得支持：

- 任意字段路径；
- 字符串表达式；
- Python `eval` / 动态 import；
- YAML/JSON 运行时配置；
- 反射式通用规则引擎；
- 用户输入 profile。

### 2. Fixed profile registry

V1 只允许三个 Profile：

```text
T01 / WEBSHOP_NORMAL_PURCHASE_V2
extension = FULFILMENT

T09 / WEBSHOP_UNKNOWN_PAYMENT_RECOVERY_V2
extension = RECOVERY

T12 / WEBSHOP_PAYMENT_STATUS_CONFLICT_V2
extension = STATUS_CONFLICT
```

不得加入 T11，也不得加入 T02—T08。

### 3. One common product builder

产品调用只能存在一个入口，例如：

```text
build_sidecar_product_trace(
    gate_outcome,
    adaptation,
    mandate,
    fulfillment,
    base_outcome,
)
```

该入口负责：

1. 校验所有 Sidecar 场景共有的 retained facts；
2. 生成公共 source bindings；
3. 生成公共事件 1—9；
4. 使用 exactly-one Profile 匹配；
5. 按 `extension_kind` 生成事件 10；
6. 生成 FINAL_OUTCOME 事件 11；
7. 调用现有 `assemble_product_trace()`；
8. 任一缺失、矛盾、零匹配或多匹配时返回 `None`。

### 4. Compatibility boundary

现有：

```text
webshop_happy_path_authoritative_trace.py
webshop_unknown_payment_authoritative_trace.py
```

允许两种处理：

1. 删除并更新测试/import；或
2. 保留为薄兼容适配器。

若保留，单文件必须：

- 不超过 80 行；
- 不调用 `create_event`；
- 不调用 `create_relation`；
- 不调用 `create_source_binding`；
- 不调用 `assemble_product_trace`；
- 不包含场景事实校验；
- 不被 `webshop_payment_sidecar.py` 导入。

不得新增：

```text
webshop_payment_status_conflict_authoritative_trace.py
webshop_t12_authoritative_trace.py
build_t12_*trace
```

## Acceptance criteria

### AC-01 — One Sidecar Toolkit

新增一个中立模块：

```text
src/agentic_payment_experiment/webshop_sidecar_trace_toolkit.py
```

可选增加：

```text
src/agentic_payment_experiment/webshop_sidecar_trace_profiles.py
```

要求：

- 公共事实提取只实现一次；
- 公共事件 1—9 只实现一次；
- FINAL_OUTCOME 事件 11 只实现一次；
- Profile 唯一选择只实现一次；
- toolkit 名称中不得出现 T01/T09/T12；
- 不调用 recovery、conflict、lifecycle、gate、binding 或支付业务函数。

### AC-02 — Declarative profiles, not per-task builders

T01、T09、T12 必须表示为数据 Profile。

机器检查必须证明：

```text
sidecar family profile count = 3
profile names = T01/T09/T12 对应三个冻结 profile
T12 dedicated builder files = 0
T12 dedicated build functions = 0
```

Profile 只能声明状态与扩展类型，不得包含完整事件构造函数。

### AC-03 — Exactly-one profile selection

Profile 选择必须 fail-closed：

```text
0 个 Profile 匹配 → None
1 个 Profile 匹配 → 构造该 Profile 轨迹
2 个及以上 Profile 匹配 → None
```

必须有独立测试覆盖：

- T01 唯一匹配；
- T09 唯一匹配；
- T12 唯一匹配；
- 普通非覆盖 Sidecar 路径零匹配；
- 人工构造重叠 Profile 时多匹配关闭。

### AC-04 — One product call path

`webshop_payment_sidecar.py` 必须：

```text
只 import 一个 Sidecar Toolkit builder
只调用一次该 builder
不再 import T01/T09 专属 builder
不按 T01 → T09 → T12 顺序逐个尝试
```

业务计算顺序保持：

```text
payment recovery / conflict / lifecycle
→ frozen base outcome
→ one toolkit call
→ replace(authoritative_trace=...)
```

### AC-05 — Common trace core

T01、T09、T12 共用同一公共事件核心：

```text
1 AUTHORITY
2 AUTHORIZED_ORDER
3 CURRENT_ORDER
4 REQUEST
5 ACTION
6 PAYMENT_CANDIDATE
7 ACTION_BINDING_FACT
8 RUNTIME_GATE
9 PAYMENT_OUTCOME
11 FINAL_OUTCOME
```

事件 10 只能由固定扩展类型生成：

```text
T01 = FULFILMENT_OUTCOME
T09 = RECOVERY_OUTCOME
T12 = STATUS_CONFLICT_FACT
```

公共事件不得在三个 Profile 中重复声明完整构造逻辑。

### AC-06 — Neutral projections

`webshop_trace_assembler.py` 可增加：

```text
project_fulfillment
project_payment_status_conflict
```

要求：

- 严格匹配冻结 projection registry；
- 保留现有 recovery/result projection 输出；
- 不包含 Profile 判断；
- 不调用业务函数；
- T01/T09 完整轨迹 hash 不变。

### AC-07 — Existing trace invariance

迁移后必须保持：

```text
T01 full trace SHA-256
= 7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906

T09 full trace SHA-256
= a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e

T10 full trace SHA-256
= 2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3
```

T01/T09 的事件、binding、relation、projection、reason codes、trace_ref 均不得变化。

### AC-08 — T12 capability validation

真实 T12 产品调用必须产生：

```text
profile = WEBSHOP_PAYMENT_STATUS_CONFLICT_V2
source = PRODUCT_OBSERVED
product source = webshop_payment_fulfilment_outcome
validator = VALID
events = 11
unique bindings = 10
```

关键状态：

```text
CURRENT_PAYMENT_CANDIDATE = PENDING
PAYMENT_EXECUTION_OUTCOME = UNKNOWN
STATUS_CONFLICT_FACT = CONFLICT
FINAL_OUTCOME = UNKNOWN
```

T12 必须只通过新增 Profile 和固定 conflict projection 接入，不得新增 T12 专属 builder。

### AC-09 — Same-baseline impact

使用同一 runner、fixture 和 repeat=3：

```text
BEFORE
Product Trace = 3/12
GESR = 2/12
valid product tasks = T01, T09, T10

AFTER
Product Trace = 4/12
GESR = 3/12
valid product tasks = T01, T09, T10, T12
T12 matched = true
T12 capability_gaps = []
```

三次 normalized hash 必须一致。

### AC-10 — Business and safety invariance

全项目 non-trace projection SHA-256 必须保持：

```text
6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

T01、T09、T10、T12 的：

- decision；
- callback count；
- retry count；
- payment/recovery/conflict/lifecycle；
- forbidden side effects；
- binding / lineage；

不得因工具包发生变化。

### AC-11 — Coverage remains bounded

产品轨迹只能存在于：

```text
T01
T09
T10
T12
```

不得新增：

- T02—T08；
- T11；
- 任意测试临时 Profile 进入生产 registry；
- 任意未冻结 Profile。

### AC-12 — Complexity guardrail

必须通过 AST / 源码审计：

```text
webshop_payment_sidecar.py
- dedicated Sidecar builder imports = 0
- generic toolkit builder call = 1

legacy T01/T09 modules（若保留）
- create_event calls = 0
- create_relation calls = 0
- create_source_binding calls = 0
- assemble_product_trace calls = 0
- each line count <= 80

new T12-specific authoritative trace module = absent
build_t12_*trace function = absent
runtime YAML/JSON profile loading = absent
eval/exec/dynamic import = absent
```

### AC-13 — Frozen boundaries

以下不得修改：

- `scripts/validation/run_project_impact_baseline.py`；
- `src/agentic_payment_experiment/authoritative_trace.py`；
- `src/agentic_payment_experiment/webshop_runtime_gate.py`；
- `src/agentic_payment_experiment/webshop_authoritative_trace.py`；
- baseline/target fixtures；
- formula/projection/profile/runtime registries；
- recovery、conflict、lifecycle、payment、binding 业务模块；
- 项目地图。

冻结哈希必须全部匹配 entering baseline。

### AC-14 — Tests and evidence

至少运行：

```text
python3 -m unittest \
  tests.test_webshop_trace_assembler \
  tests.test_webshop_sidecar_trace_toolkit \
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
- repeat=3 一致；
- 保存 T01/T09/T10/T12 完整轨迹；
- 保存 profile registry、ambiguity fail-closed 和复杂度审计；
- 保存 non-trace、coverage、冻结边界证据；
- workflow validator 为 `OK`。

## Validation plan

| VP | Exact action | Expected result |
|---|---|---|
| VP-01 | AST/结构审计 | 一个 toolkit builder；无 T12 专属 builder；旧 T01/T09 无完整组装逻辑 |
| VP-02 | T01/T09 迁移回归 | 两条完整 trace hash 与 entering baseline 完全一致 |
| VP-03 | Profile 唯一匹配测试 | T01/T09/T12 各唯一匹配；零匹配/多匹配 fail-closed |
| VP-04 | 真实 T12 产品调用 | `VALID / 11 events / 10 bindings` |
| VP-05 | T12 负例矩阵 | 缺失/矛盾 conflict、payment、lifecycle 事实全部返回 `None` |
| VP-06 | baseline repeat=3 | Product Trace `4/12`、GESR `3/12`，三次一致 |
| VP-07 | non-trace projection | hash 保持 `6eb5...9099dc` |
| VP-08 | producer coverage | 仅 T01/T09/T10/T12 |
| VP-09 | frozen boundaries | runner、validator、gate、T10 builder、fixtures、registry 不变 |
| VP-10 | focused/full unittest | focused 全过；full 至少 504 项全过 |
| VP-11 | workflow validator | `OK` |

## Allowed scope

可修改：

- `src/agentic_payment_experiment/webshop_sidecar_trace_toolkit.py`（新增）；
- `src/agentic_payment_experiment/webshop_sidecar_trace_profiles.py`（可选新增）；
- `src/agentic_payment_experiment/webshop_trace_assembler.py`；
- `src/agentic_payment_experiment/webshop_payment_sidecar.py`；
- `src/agentic_payment_experiment/webshop_happy_path_authoritative_trace.py`（仅删除重复逻辑或保留薄适配器）；
- `src/agentic_payment_experiment/webshop_unknown_payment_authoritative_trace.py`（仅删除重复逻辑或保留薄适配器）；
- `tests/test_webshop_sidecar_trace_toolkit.py`（新增）；
- `tests/test_webshop_trace_assembler.py`；
- `tests/test_webshop_payment_sidecar.py`；
- `tests/test_webshop_unknown_payment_authoritative_trace.py`（兼容回归）；
- `tests/test_project_impact_baseline.py`；
- 本任务 `REPORT.md`；
- 本任务 `evidence/EV-*`；
- `CURRENT.md`（仅 `CONTRACT_FROZEN → EXECUTING`）。

工作区继承此前已接受但未提交的 P9 产物。不得清理、重置或回退继承内容。

## Exclusions

- 不新增 T12 专属 authoritative trace 模块或 build 函数；
- 不新增 T11、T02—T08 产品轨迹；
- 不修改 runner、validator、gate、T10 builder、fixtures、registry、profiles 或项目地图；
- 不修改 recovery、status conflict、lifecycle、payment、authorization、binding 或 side-effect 业务规则；
- 不建立通用 DSL、规则引擎、YAML/JSON profile loader 或动态表达式；
- 不把 Profile 暴露为用户输入或外部配置；
- 不读取 docs、fixture、evidence、CURRENT 或 evaluator replay 来生成产品轨迹；
- 不保留 query/async observation、完整 GateContext、callback、credential、页面、prompt 或隐藏上下文；
- 不执行网络、LLM、WebShop runtime、Buy Now、支付、订单、钱包或真实 callback；
- 不安装依赖、不创建环境；
- 不提交、不推送、不改写历史；
- 不清理、删除或回退此前已接受产物。

## Stop conditions

立即停止并提交 `BLOCKED`，不得扩大范围：

- T01/T09 无法在统一 Toolkit 下保持完整 trace hash；
- T12 必须依赖专属完整 builder 才能通过；
- 需要修改 runner、validator、registry、fixture、gate 或业务模块；
- Profile 需要任意字段表达式或动态规则才能描述；
- T01/T09/T12 出现两个及以上 Profile 同时匹配且无法通过明确冻结条件消除；
- non-trace hash 或安全守护线变化；
- T12 之外出现新产品轨迹；
- 需要网络、真实支付、依赖安装或新环境。

## Required report

REPORT 必须包含：

- exact changed files 和 SHA-256；
- Toolkit API、Profile model 和固定 registry；
- 公共事件核心与扩展事件结构；
- T01/T09 重复逻辑移除证据；
- sidecar 单入口调用证据；
- Profile 零匹配/唯一匹配/多匹配证据；
- 无 T12 专属 builder 的 AST 证据；
- T01/T09/T10/T12 完整轨迹 hash；
- T12 exact 11-event/10-binding 结构；
- baseline repeat=3 before/after；
- Product Trace `3/12→4/12`；
- GESR `2/12→3/12`；
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

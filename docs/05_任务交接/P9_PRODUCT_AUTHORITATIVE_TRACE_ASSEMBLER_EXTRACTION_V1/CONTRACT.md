# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-ASSEMBLER-EXTRACTION-V1`  
Task name: 产品权威轨迹统一 Assembler 等价抽取  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `maintenance`  
Risk: `L1`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-06-r7`  
Related bottleneck: `B-03`  
Related hypothesis: `H-03`  
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-T01-HAPPY-PATH-SLICE-V1`  
Parent verdict: `PASS / IMPROVED`

T10 拒绝链与 T01 正常成功链已经分别形成真实产品权威轨迹：

```text
T10 = VALID / 12 events / 11 bindings
T01 = VALID / 11 events / 10 bindings
Product Trace = 2/12
baseline GESR = 1/12
```

两个 builder 已复用 binding、event、relation 和多类 projection，但这些公共函数仍位于 T10 命名模块 `webshop_authoritative_trace.py`，T01 通过 `_xxx` 私有函数跨模块引用。第三个场景前必须先抽成中立公共组装层，避免继续形成按 T 编号复制的实现。

本任务只做架构等价维护，不宣称 B-03 再次缩小。正确项目影响应为 `NOT_APPLICABLE`，任何产品覆盖或业务指标变化都视为回归。

## Single objective

新增中立的 WebShop Trace Assembler，把 T01/T10 已验证的机械能力统一到一个模块：

```text
事实 projection
→ source binding
→ relation
→ event
→ envelope
→ ProductAuthoritativeTrace
```

T01/T10 仅保留：

```text
场景事实是否成立
+ 场景专用 projection
+ 事件顺序与角色组合
+ profile / trace_ref
```

重构前后，T01/T10 的完整轨迹快照、baseline 输出、指标、产品行为和所有安全守护线必须完全一致。

## Entering baseline

### Product and measurement baseline

```text
Product Trace = 2/12
baseline GESR = 1/12
T01 trace = VALID / webshop_payment_fulfilment_outcome / 11 events / 10 bindings
T10 trace = VALID / webshop_gate_outcome / 12 events / 11 bindings
valid product tasks = T01, T10
non-trace projection SHA-256
= 6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

Accepted baseline repeat=3：

```text
baseline output SHA-256
= 8d4304dce72bb4f3d572512ee4d09e2e4bd2ee06f34ec4e8e6b0887acf059d9a

normalized SHA-256 × 3
= 56a82f9ab99cd5d83ae0b1259c2cef9f6b6cdf2a1b7183c029ba7569ab332619
```

### Full trace snapshot baseline

Frozen snapshot：

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_ASSEMBLER_EXTRACTION_V1/
evidence/BASELINE-trace-snapshots.json
```

Accepted hashes：

```text
snapshot file SHA-256
= 2d33116baca3e6fd401afbb3c4f01552decbd5959d8452d2d6301fcf1fd58234

T01 canonical full trace SHA-256
= 7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906

T10 canonical full trace SHA-256
= 2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3

combined T01+T10 canonical trace SHA-256
= d913fc7d3a69abfb0c7774356a988a5e23cf3780a70523a03ced2672bec5ac4c
```

### Current implementation hashes

```text
webshop_authoritative_trace.py
= e6864905f4b67ef3024b7f7118b547c27c586127c60d537a3f5bab5a48f1e2c9

webshop_happy_path_authoritative_trace.py
= 51b2d6873d66bb28ebbefa321f90e4ea4ab9a6d0102e38e9f8b312413b244880

webshop_runtime_gate.py
= 5abf1a6f08060e111b6fbd9ba96809c2823ef07adee0e23b6d60a6c50c06bdef

webshop_payment_sidecar.py
= 833a34c005061a69b29265190b3c609ec92278afe0bb0d48a700546b548436f7
```

T01/T10 builder 文件允许因等价重构改变；gate、sidecar、runner、validator、fixtures 和 registry 必须保持冻结哈希。

## Single principal change

只做一个主要变化：

> 把 T01/T10 已复用的机械轨迹构造能力从 T10 命名模块抽到中立 `webshop_trace_assembler.py`，并让两个场景 builder 同时使用它。

不得同时增加第三个场景、改变业务事实留存、修改产品调用路径或调整测量工具。

## Acceptance criteria

### AC-01 — Neutral assembler module

新增：

```text
src/agentic_payment_experiment/webshop_trace_assembler.py
```

该模块统一承载已验证的机械能力：

- source binding 构造；
- relation 构造；
- event 构造；
- mandate/order/request/action/payment/action fact/runtime 等公共 projection；
- `ProductAuthoritativeTrace` envelope 组装；
- 期望 unique binding 数量检查和 fail-closed。

模块名、公开函数和文档不得带 T01 或 T10 专属含义。

### AC-02 — No private cross-builder dependency

重构后：

```text
webshop_happy_path_authoritative_trace.py
不得 import webshop_authoritative_trace.py 的任何 _xxx 私有函数

webshop_authoritative_trace.py
不得 import webshop_happy_path_authoritative_trace.py
```

两个 builder 只能共同依赖中立 assembler 和现有数据合同。

### AC-03 — One shared envelope assembly path

T01 与 T10 必须使用同一个中立 envelope assembly 函数。该函数至少接收：

- profile；
- trace ref 或稳定 trace ref 输入；
- ordered events；
- ordered source bindings；
- expected unique binding count。

它负责统一设置：

```text
schema_version = product-authoritative-trace/v1
source = PRODUCT_OBSERVED
completeness_status = COMPLETE
```

并在类型、重复 binding 或数量不符时 fail-closed。

### AC-04 — T01 full trace invariance

使用冻结生成脚本重新生成快照，T01 必须保持：

```text
canonical full trace SHA-256
= 7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906

events = 11
bindings = 10
profile = WEBSHOP_NORMAL_PURCHASE_V2
source = PRODUCT_OBSERVED
validator = VALID
```

事件、relation、source ref、binding ref、entity ref、status、decision、reason codes 和 projection 均不得变化。

### AC-05 — T10 full trace invariance

使用冻结生成脚本重新生成快照，T10 必须保持：

```text
canonical full trace SHA-256
= 2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3

events = 12
bindings = 11
profile = WEBSHOP_DUPLICATE_PREFLIGHT_BLOCK_V2
source = PRODUCT_OBSERVED
validator = VALID
```

事件、relation、source ref、binding ref、entity ref、status、decision、reason codes 和 projection 均不得变化。

### AC-06 — Baseline byte and metric invariance

使用同一 accepted fixture、runner 和 `repeat=3`，必须保持：

```text
baseline output SHA-256
= 8d4304dce72bb4f3d572512ee4d09e2e4bd2ee06f34ec4e8e6b0887acf059d9a

normalized SHA-256 × 3
= 56a82f9ab99cd5d83ae0b1259c2cef9f6b6cdf2a1b7183c029ba7569ab332619

Product Trace = 2/12
baseline GESR = 1/12
valid product tasks = T01, T10
non-trace projection SHA-256
= 6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

### AC-07 — Pure mechanical boundary

Assembler 不得：

- 调用 authorization、order validation、binding verification、Runtime Gate、payment、recovery、conflict、lifecycle 或 side-effect 业务函数；
- 判断 T01/T10 场景是否成立；
- 读取 runner、fixture、docs、CURRENT、evidence、文件、环境变量、当前时间或随机数；
- 访问网络、进程、WebShop、callback 或外部服务；
- 补造缺失事实。

任一无效机械输入必须返回 `None` 或抛出已接受的 `TraceContractError`，由场景 builder 统一 fail-closed。

### AC-08 — Coverage remains exactly T01 and T10

重构后产品轨迹覆盖必须仍然只有：

```text
T01
T10
```

不得新增 T02—T09、T11、T12 producer，不得修改 gate/sidecar 事实留存或产品调用路径。

### AC-09 — Frozen boundaries

以下 SHA-256 必须保持：

```text
runner
= 70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3

authoritative_trace.py
= 07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a

baseline fixture
= 4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5

T10 target fixture
= f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee

gate
= 5abf1a6f08060e111b6fbd9ba96809c2823ef07adee0e23b6d60a6c50c06bdef

sidecar
= 833a34c005061a69b29265190b3c609ec92278afe0bb0d48a700546b548436f7

formula registry
= 2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd

projection registry
= 45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4

profiles
= 6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2

runtime contract
= 4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e
```

### AC-10 — Tests and evidence

运行：

```text
python3 -m unittest \
  tests.test_webshop_trace_assembler \
  tests.test_webshop_authoritative_trace \
  tests.test_webshop_payment_sidecar \
  tests.test_authoritative_trace \
  tests.test_project_impact_baseline -v

python3 -m unittest discover -s tests -p 'test_*.py'

python3 scripts/validation/run_project_impact_baseline.py \
  --repeat 3 \
  --output <evidence>/EV-AFTER-baseline.json

PYTHONPATH=src:. python3 \
  <task-evidence>/BASELINE-generate-trace-snapshots.py
```

要求：

- focused 全过；
- full 至少 `492` 项且全部通过；
- baseline output 和 normalized hashes 完全一致；
- T01/T10 full trace hashes 完全一致；
- 保存 AST/import boundary audit；
- workflow validator 为 `OK`。

## Validation plan

| VP | Exact action | Expected result |
|---|---|---|
| VP-01 | AST 检查两个 builder import | 两者只共享中立 assembler，不再私有跨引用 |
| VP-02 | assembler 单元测试 | binding/event/relation/projection/envelope 与 fail-closed 均通过 |
| VP-03 | 重跑 full trace snapshot | T01、T10、combined hashes 与冻结值一致 |
| VP-04 | T01/T10 真实产品调用 | 两条轨迹继续 `VALID`，事件与 binding 数量不变 |
| VP-05 | baseline repeat=3 | 输出 SHA、normalized SHA、Product Trace、GESR 完全不变 |
| VP-06 | producer coverage scan | 产品轨迹仍仅 T01、T10 |
| VP-07 | frozen hash audit | runner、validator、fixtures、gate、sidecar、registries 全部不变 |
| VP-08 | focused/full unittest | focused 全过；full 至少 492 项全过 |
| VP-09 | workflow validator | `OK` |

## Allowed scope

可修改：

- `src/agentic_payment_experiment/webshop_trace_assembler.py`（新增）；
- `src/agentic_payment_experiment/webshop_authoritative_trace.py`；
- `src/agentic_payment_experiment/webshop_happy_path_authoritative_trace.py`；
- `tests/test_webshop_trace_assembler.py`（新增）；
- `tests/test_webshop_authoritative_trace.py`；
- `tests/test_webshop_payment_sidecar.py`；
- 本任务 `REPORT.md`；
- 本任务 `evidence/EV-*`；
- `CURRENT.md`（仅 `CONTRACT_FROZEN → EXECUTING`）。

冻结 baseline 文件：

- `evidence/BASELINE-generate-trace-snapshots.py`；
- `evidence/BASELINE-trace-snapshots.json`。

工作区继承此前已接受但未提交的 P9 产物。不得清理、重置、覆盖或回退继承内容。

## Exclusions

- 不修改 `webshop_runtime_gate.py` 或 `webshop_payment_sidecar.py`；
- 不修改 `authoritative_trace.py`、runner、fixtures、registry、profile 或项目地图；
- 不新增 T02—T09、T11、T12 产品轨迹；
- 不改变任何授权、确认、binding、Runtime Gate、payment、recovery、conflict、lifecycle 或 side-effect 规则；
- 不新增或移除 gate/sidecar outcome 字段；
- 不改变 T01/T10 product source、profile、trace ref、事件、projection、binding 或 relation；
- 不调用网络、LLM、外部 API、WebShop runtime、Buy Now、钱包、支付或订单；
- 不安装依赖、不创建环境；
- 不提交、不推送、不改写历史；
- 不清理、删除、重置或回退继承产物。

## Stop conditions

立即停止并报告，不得扩大范围：

- 任一 T01/T10 full trace hash 变化；
- baseline output/normalized/non-trace hash 变化；
- Product Trace 或 GESR 变化；
- 需要修改 gate、sidecar、runner、validator、fixture 或 registry；
- 需要改变场景事实判断或业务规则；
- 出现第三个产品 trace producer；
- 无法在中立模块中消除 T01 对 T10 私有函数的依赖；
- 需要外部副作用、依赖安装或新环境。

## Required report

REPORT 必须包含：

- exact changed files 和 SHA-256；
- 抽取前后模块依赖图；
- 统一 assembler 的公开函数与职责边界；
- T01/T10 builder 保留的场景专属逻辑；
- T01/T10 full trace before/after hashes；
- baseline repeat=3 output/normalized hashes；
- Product Trace、GESR 和 non-trace hash；
- producer coverage scan；
- frozen boundary hashes；
- focused/full tests 原始证据；
- workflow validator；
- `task_verdict_candidate`；
- `project_impact_candidate: NOT_APPLICABLE`。

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

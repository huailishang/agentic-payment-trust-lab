# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-PROVENANCE-DIAGNOSTIC-REPAIR-V1`  
Task name: 产品轨迹与评估器 Replay 来源分离诊断修复  
Task kind: `repair`  
Risk: `L1`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-06-r6`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-T10-DUPLICATE-PREFLIGHT-SLICE-V1`  
Parent verdict: `PASS / IMPROVED`  
Metric baseline: accepted T10 target 中 product trace 为 `1/12`、GESR 为 `1/12`，但 T10 被错误记录 `measurement_integrity_gaps=[trace_provenance_not_separated]`；原始字段分别为 `webshop_gate_outcome` 与 `runner_constructed_from_fixed_facts`。  
Estimated affected scope: 所有后续同时存在产品轨迹和 evaluator replay 的任务；当前已实测影响 T10，未来最多影响剩余 11 个 trace slice 的诊断可信度。  
Expected project impact: 本 repair 只消除错误的 measurement integrity gap，不增加产品轨迹覆盖或 GESR；项目影响裁决必须为 `NOT_APPLICABLE`。  
Rollback condition: product trace、GESR、业务投影、fixtures、validator、产品代码或原始 provenance 字段发生变化，或模糊/相同来源被错误判为已分离时立即回滚。

## Defect statement

冻结 runner 当前定义：

```text
trace_provenance_separated =
  product_observed_trace_source is None
  and evaluator replay provenance 合法
  and authoritative_trace 不在 evidence stages
```

这意味着一旦产品真正产生轨迹，该诊断必然为假，即使来源已经明确分开：

```text
product source = webshop_gate_outcome
evaluator replay provenance = runner_constructed_from_fixed_facts
```

该缺陷不影响 capability gap 或 GESR，但会制造错误的 measurement integrity gap，必须在扩展第二个产品轨迹场景前修复。

## Single objective

只修复 `run_project_impact_baseline.py` 的 provenance 分离诊断，使它按两个来源的真实存在性和差异性判断，而不是要求产品轨迹不存在。

```text
产品轨迹与 Replay 均不存在
→ 按关闭规则判断

只有产品轨迹存在
→ 产品来源非空、authoritative_trace stage 存在
→ separated = true

只有 evaluator replay 存在
→ replay provenance 为固定 runner 来源
→ separated = true

两者同时存在且来源明确不同
→ separated = true

来源相同、缺失、模糊或与状态矛盾
→ separated = false
```

不得修改产品实现、产品轨迹、validator、fixtures 或项目能力目标。

## Acceptance criteria

### AC-01 — Closed provenance rule

在 runner 中提取一个小型纯函数或等价关闭逻辑，只读取：

```text
product_observed_trace_status
product_observed_trace_source
evaluator_synthesized_replay_status
evaluator_synthesized_replay_provenance
evidence_stages
```

不得读取产品对象、fixture 原对象、GateContext、docs 或 task evidence。

### AC-02 — Product trace absent / replay present

现有无产品轨迹但 evaluator replay 为 `VALID` 的任务必须保持：

```text
product source = None
replay provenance = runner_constructed_from_fixed_facts
authoritative_trace stage absent
trace_provenance_separated = true
measurement_integrity_gaps = []
```

### AC-03 — Product trace present / replay present

T10 必须变为：

```text
product trace status = VALID
product source = webshop_gate_outcome
replay status = VALID
replay provenance = runner_constructed_from_fixed_facts
authoritative_trace stage present
trace_provenance_separated = true
measurement_integrity_gaps = []
```

产品来源和 replay provenance 必须非空且不相等。

### AC-04 — Product trace only

构造一个只有产品轨迹、没有 evaluator replay 的固定测试对象：

```text
product status = VALID
product source = explicit_product_outcome
authoritative_trace stage present
replay status = NOT_AVAILABLE
replay provenance = None
```

结果必须为 `true`。

### AC-05 — Negative provenance matrix

以下均必须为 `false` 并产生 `trace_provenance_not_separated`：

- product trace `VALID` 但 product source 缺失；
- product trace `VALID` 但 `authoritative_trace` stage 缺失；
- product trace `NOT_AVAILABLE` 但 product source 非空；
- replay `VALID` 但 replay provenance 缺失；
- replay `NOT_AVAILABLE` 但 replay provenance 非空；
- product source 与 replay provenance 相同；
- 未知 trace/replay 状态；
- 任一来源为自由空白字符串。

### AC-06 — Capability invariance

使用同一 accepted target repeat=3，修复后必须保持：

```text
T10 product trace = VALID
Product Trace = 1/12
Target GESR = 1/12
T10 matched = true
T10 capability_gaps = []
```

允许变化仅限：

```text
T10 measurement_diagnostics.trace_provenance_separated: false → true
T10 measurement_integrity_gaps: [trace_provenance_not_separated] → []
T10 measurement_diagnostics_matched: false → true
由以上诊断字段直接引起的 measurement-only 摘要或 output hash
```

### AC-07 — Business and product boundary

以下必须保持：

```text
non-trace business projection SHA-256
= 6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

不得修改：

- `src/agentic_payment_experiment/` 中任何文件；
- `samples/`；
- `authoritative_trace.py`；
- T10 12-event/11-binding 产品轨迹；
- 决策、callback、retry、状态、reason codes 或副作用。

### AC-08 — Freeze audit

以下 SHA-256 必须保持：

| 项目 | SHA-256 |
|---|---|
| Measurement module | `07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a` |
| Baseline fixture | `4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5` |
| Target fixture | `f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee` |
| Formula registry | `2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd` |
| Projection registry | `45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4` |
| Profiles | `6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2` |
| Runtime contract | `4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e` |

Runner hash 预期因诊断修复发生变化，必须记录 old/new hash。

### AC-09 — Tests and repeatability

运行：

```text
python3 -m unittest tests.test_project_impact_baseline -v
python3 -m unittest discover -s tests -p 'test_*.py'

python3 scripts/validation/run_project_impact_baseline.py \
  --repeat 3 \
  --output <evidence>/EV-AFTER-baseline.json

python3 scripts/validation/run_project_impact_baseline.py \
  --spec samples/evaluation/project_impact_t10_preflight_target_v1.json \
  --repeat 3 \
  --output <evidence>/EV-AFTER-target.json
```

要求：

- 全量至少 `486` 项且全部通过；
- baseline/target 三次 normalized hash 各自一致；
- T10 provenance diagnostic gap 清零；
- 业务和安全指标不退化。

### AC-10 — Evidence and workflow

REPORT 必须包含：

- exact changed files；
- defect before/after truth table；
- runner old/new hash；
- baseline/target repeat=3 JSON 与 normalized hashes；
- T10 measurement-only field diff；
- non-trace hash；
- product/fixture/module/registry freeze audit；
- focused/full tests 原始证据；
- workflow validator `OK`；
- task verdict candidate；
- project impact candidate 必须为 `NOT_APPLICABLE`。

## Required outputs

1. runner provenance 诊断修复；
2. provenance 正反矩阵测试；
3. 本任务 `REPORT.md`；
4. 本任务 `evidence/EV-*`；
5. AFTER baseline/target JSON；
6. measurement-only before/after diff。

## Allowed scope

可修改：

- `scripts/validation/run_project_impact_baseline.py`
- `tests/test_project_impact_baseline.py`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/REPORT.md`
- 同任务 `evidence/EV-*`
- `CURRENT.md`（仅 `CONTRACT_FROZEN → EXECUTING`）

工作区继承此前已接受但未提交的 P9 产物。不得清理、重置、覆盖或回退继承内容。

## Exclusions

- 不修改任何 `src/agentic_payment_experiment/` 文件；
- 不修改 `samples/`；
- 不修改产品 trace producer、builder 或 validator；
- 不增加第二个产品轨迹场景；
- 不改变 capability gaps、目标答案或业务期望来适配实现；
- 不执行 WebShop runtime、Buy Now、支付、钱包、订单或 callback 外部副作用；
- 不调用网络、LLM 或外部 API；
- 不安装依赖、不创建环境；
- 不提交、不推送、不改写历史；
- 不更新项目瓶颈地图；
- 不宣称产品覆盖从 1/12 继续提升。

## Validation plan

| VP | Exact action | Expected |
|---|---|---|
| VP-01 | provenance truth table | 正例 true、矛盾/同源/缺来源 false |
| VP-02 | T10 target | diagnostic gap 清零，capability 仍 1/12 |
| VP-03 | baseline target repeat=3 | 各自 deterministic |
| VP-04 | non-trace projection | `6eb5...9099dc` 不变 |
| VP-05 | product/static freeze | src、fixtures、module、registry 不变 |
| VP-06 | focused/full unittest | full >= 486，全部通过 |
| VP-07 | workflow validator | `OK` |

## Stop conditions

- 需要修改产品代码或 validator；
- 需要修改 fixture 或 expected capability 结果；
- product trace 或 GESR 从 1/12 变化；
- non-trace hash 变化；
- 无法区分缺失来源、相同来源和明确不同来源；
- 任一安全守护线退化；
- 需要外部副作用或新依赖。

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

# Evaluator Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-PREPAYMENT-MEASUREMENT-CONTRACT-REPAIR-V1`  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `repair`  
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-PREPAYMENT-FAMILY-TOOLKIT-V1`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`  
Inherited bottleneck: `B-03`  
Inherited hypothesis: `H-03`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-06-r10`  
Inherited active bottleneck: `B-03`  
Inherited hypothesis: `H-03`  
Parent verdict: `REJECTED / INCONCLUSIVE`

本 repair 不改变产品能力，只修复父 capability experiment 暴露出的测量契约漂移。B-03/H-03 暂不改序，修复后的产品影响仍由后续 continuation 独立裁决。

## 1. Objective

修复 T02/T03/T04 的**测量契约漂移**，让冻结 project-impact fixture 与已接受的 authoritative trace registry 使用同一个事件名：

```text
PREPAYMENT_DECISION_RECORDED
```

本任务只修评测标准与对应测试，不改变任何产品行为。

## 2. Evidence basis

父任务独立复核已经确认：

```text
T02/T03/T04 actual product trace status = VALID
registry event = PREPAYMENT_DECISION_RECORDED
fixture event  = DECISION_RECORDED
```

当前冻结哈希：

```text
samples/evaluation/project_impact_baseline_v1.json
4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5

src/agentic_payment_experiment/authoritative_trace.py
07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a

tests/test_project_impact_baseline.py
5bd379b0909b378259882dce79b2add7800da6d3046680a21111349e0afb5f2e
```

父任务 REVIEW：

`docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PREPAYMENT_FAMILY_TOOLKIT_V1/REVIEW.md`

## 3. Exactly one principal change

只做一件事：

```text
把 T02/T03/T04 measurement contract
从旧的 DECISION_RECORDED
同步到 authoritative registry 已冻结的 PREPAYMENT_DECISION_RECORDED
```

测试只能随这一测量契约修复同步更新，不得顺带改变产品逻辑或放宽安全护栏。

## Allowed scope

仅允许修改：

- `samples/evaluation/project_impact_baseline_v1.json`
- `tests/test_project_impact_baseline.py`
- 本任务 `REPORT.md`
- 本任务 `evidence/EV-*`
- `CURRENT.md`（仅 `CONTRACT_FROZEN -> EXECUTING`）

## Exclusions and forbidden side effects

不得修改：

- `scripts/validation/run_project_impact_baseline.py`
- `src/agentic_payment_experiment/authoritative_trace.py`
- `src/agentic_payment_experiment/webshop_authoritative_trace.py`
- `src/agentic_payment_experiment/webshop_trace_assembler.py`
- `src/agentic_payment_experiment/webshop_prepayment_trace_toolkit.py`
- `src/agentic_payment_experiment/webshop_prepayment_trace_profiles.py`
- `src/agentic_payment_experiment/webshop_runtime_gate.py`
- 任何 Sidecar Toolkit/Profile/payment sidecar/T10 builder
- 任何订单、确认、授权、Action Binding、Runtime Gate、payment、recovery、conflict、lifecycle 业务模块
- 项目地图

不得执行网络、WebShop runtime、Buy Now、支付、订单、钱包、LLM、真实 callback、副作用、依赖安装、环境创建、commit、push、reset 或 history rewrite。

## 6. Acceptance criteria

### AC-01 — Fixture exact repair

`project_impact_baseline_v1.json` 对 T02/T03/T04 只能做与本问题直接相关的修复：

```text
expected_product_observed_trace_events
DECISION_RECORDED
→ PREPAYMENT_DECISION_RECORDED
```

三项均修改；不得改变 decision、reason codes、callback/retry、required facts、side-effect guardrail、limitations 或其他任务 fixture。

允许 JSON 格式化造成必要的字节变化，但语义 diff 必须证明除上述三个事件名外无其他 fixture 字段变化。

### AC-02 — Measurement tests follow accepted product reality

`tests/test_project_impact_baseline.py` 仅更新受该事件名修复影响的硬编码期望：

- product trace availability 集合加入 `T02/T03/T04`；
- T02/T03/T04 product trace status 期望从 `NOT_AVAILABLE` 改为 `VALID`；
- matched/main metric 期望同步到修复后结果；
- 不得删除或放宽 provenance separation、callback、retry、forbidden side effect、binding、lineage、decision/reason 等安全断言。

### AC-03 — Same runner now counts T02/T03/T04

使用**未修改**的 `run_project_impact_baseline.py` 与修复后的 fixture：

```text
T02 matched = true
T03 matched = true
T04 matched = true
T02/T03/T04 capability_gaps = []

Product Trace = 7/12
GESR = 6/12
```

不得通过 runner alias、normalization 或特殊分支实现。

### AC-04 — Repeatability

运行：

```text
python3 scripts/validation/run_project_impact_baseline.py --repeat 3 --output <evidence>/EV-AFTER-baseline.json
```

三次 normalized result 必须一致。

### AC-05 — Product behavior invariance

修复前后不得修改任何 `src/` 文件。

至少验证：

```text
T02 decision = CONFIRMATION_REQUIRED
T03 decision = CONFIRMATION_REQUIRED
T04 decision = INDETERMINATE
T02/T03/T04 callback_count = 0
T02/T03/T04 retry_count = 0
forbidden side effects = []
```

并保持父任务已有产品轨迹不变。

### AC-06 — Existing accepted traces remain intact

T01/T09/T10/T12 的产品轨迹仍为 `VALID`，不得因测量修复发生事件或来源变化。

父任务记录的 non-trace projection SHA-256 仍应为：

```text
6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

### AC-07 — Tests

至少运行：

```text
python3 -m unittest tests.test_project_impact_baseline -v

python3 -m unittest \
  tests.test_webshop_trace_assembler \
  tests.test_webshop_runtime_gate \
  tests.test_project_impact_baseline -v

python3 -m unittest discover -s tests -p 'test_*.py'
```

要求：

- `tests.test_project_impact_baseline` 全过；
- 相关 focused suite 全过；
- full suite 至少 `512` 项且全部通过。

### AC-08 — Frozen boundaries and exact diff

必须保存审计证明：

```text
runner SHA-256 unchanged
authoritative_trace.py SHA-256 unchanged
all src/**/*.py unchanged from task start
fixture semantic diff = exactly three T02/T03/T04 event-name replacements
no other task fixture changed
```

### AC-09 — Workflow evidence

保存 EV triplets、修复后 fixture SHA-256、repeat=3 baseline、测试日志和范围审计；`REPORT.md` 使用 `Executor status: SUBMITTED_FOR_REVIEW` 后运行 workflow validator。

## Validation plan

| VP | Command / audit | Expected |
|---|---|---|
| VP-01 | fixture semantic diff audit | exactly three T02/T03/T04 event-name replacements |
| VP-02 | `python3 -m unittest tests.test_project_impact_baseline -v` | all pass |
| VP-03 | focused suite from AC-07 | all pass |
| VP-04 | `python3 -m unittest discover -s tests -p 'test_*.py'` | at least 512, all pass |
| VP-05 | `python3 scripts/validation/run_project_impact_baseline.py --repeat 3 --output <evidence>/EV-AFTER-baseline.json` | Product Trace 7/12; GESR 6/12; T02/T03/T04 matched; repeat stable |
| VP-06 | src/hash/business invariance audit | no src change; old traces and non-trace behavior unchanged |
| VP-07 | workflow validator | `OK` |

## 7. Stop conditions

立即停止并提交 `BLOCKED`：

- 修复需要修改 runner 或 authoritative trace registry；
- 修复需要修改任何 `src/` 产品代码；
- 修复后 T02/T03/T04 仍不能 matched；
- Product Trace / GESR 不能达到 `7/12` / `6/12`；
- 任一已有业务 decision、callback、retry、side effect 或旧产品轨迹发生变化；
- full suite 出现与本测量修复无关的新增回归；
- 需要网络、真实运行时、支付、副作用、依赖安装或新环境。

## 8. Required evidence

至少：

- `EV-01`：fixture 语义 diff + frozen hash audit
- `EV-02`：`tests.test_project_impact_baseline`
- `EV-03`：focused suite
- `EV-04`：full suite >=512
- `EV-05`：repeat=3 baseline + 7/12 / 6/12 + T02/T03/T04 no gaps
- `EV-06`：src/hash/business invariance
- `EV-07`：workflow validator

## 9. Continuation rule

本 repair PASS 后，不直接宣称 H-03 已完成。

Evaluator 下一步应基于保留的 T02/T03/T04 产品实现重新发一个 bounded continuation，只补父 capability experiment 尚未完成的：

```text
exactly-one / zero-match / multi-match / mixed-direction tests
T01/T09/T10/T12 exact trace hash invariance
non-trace invariance
full >=512
repeat=3
最终 IMPROVED / NO_MEASURABLE_GAIN 裁决
```

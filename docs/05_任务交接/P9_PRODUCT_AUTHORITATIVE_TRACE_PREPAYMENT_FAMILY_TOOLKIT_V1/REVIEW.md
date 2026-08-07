# Evaluator Review

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-PREPAYMENT-FAMILY-TOOLKIT-V1`  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `capability_experiment`  
Reviewed baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`  
Task verdict: `REJECTED`  
Project impact verdict: `INCONCLUSIVE`

```yaml
review_state: REJECTED
project_impact_verdict: INCONCLUSIVE
rejection_class: FROZEN_MEASUREMENT_CONTRACT_INFEASIBLE
implementation_rollback_required: false
commit_performed: false
push_performed: false
network_call_performed: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_order_side_effect_performed: false
```

## 1. 裁决摘要

执行者报告的 `BLOCKED` 成立。

本任务不是因为 T02/T03/T04 产品轨迹生成失败，而是冻结的两套评测标准互相冲突：

```text
accepted authoritative trace registry / 本任务 CONTRACT
T02/T03/T04 第 5 个事件
= PREPAYMENT_DECISION_RECORDED

frozen project-impact fixture
T02/T03/T04 expected_product_observed_trace_events
= ... + DECISION_RECORDED
```

独立复跑确认：

```text
T02/T03/T04 actual product trace status = VALID
实际事件包含 PREPAYMENT_DECISION_RECORDED
fixture 却要求 DECISION_RECORDED
→ 三项均产生 product_observed_trace_events_missing:DECISION_RECORDED

Product Trace = 4/12
GESR = 3/12
```

而 CONTRACT 同时禁止修改 fixture、runner、registry，并把“需要修改 fixture / registry / validator”列为 Stop Condition。因此原冻结合同不可同时满足 AC-10 与 AC-15，不能继续判 PASS。

本次 `REJECTED` 表示**当前冻结合同不可执行完成**，不是判定当前产品实现需要回滚。已有 T02/T03/T04 产品实现保留，待测量契约修复后继续验证剩余 AC。

## 2. Source of truth 裁决

评估者裁定 source of truth 为：

```text
src/agentic_payment_experiment/authoritative_trace.py
+ 当前 capability CONTRACT 中冻结的 T02/T03/T04 六事件结构
```

理由：

1. authoritative trace registry 对 T02/T03/T04 均明确使用 `PREPAYMENT_DECISION_RECORDED`；
2. 本任务 CONTRACT 的固定六事件结构也明确使用同一事件名；
3. 当前产品实际轨迹按该 registry 校验为 `VALID`；
4. 只有 `samples/evaluation/project_impact_baseline_v1.json` 仍保留旧的 `DECISION_RECORDED`；
5. 因此应修 fixture，而不是把产品轨迹或 registry 改回旧命名，也不应给 runner 增加别名来掩盖契约漂移。

冻结哈希：

```text
authoritative_trace.py
07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a

current stale fixture
4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5
```

## 3. 独立复核证据

### RV-EV-01 — 冻结事件名冲突复现

命令以 `PYTHONPATH=src` 独立运行执行者的 blocker audit。

结果：`PASS`（审计脚本 exit 0）。

关键输出：

```text
BLOCKER=FROZEN_EVENT_NAME_MISMATCH
T02/T03/T04 registry_events 包含 PREPAYMENT_DECISION_RECORDED
T02/T03/T04 actual_trace_status=VALID
T02/T03/T04 capability_gaps=[product_observed_trace_events_missing:DECISION_RECORDED]
Product Trace = 4/12
GESR = 3/12
RESULT=BLOCKED_BY_FROZEN_MEASUREMENT_CONTRACT
```

证据：

- `evidence/RV-EV-01.stdout.log`
- `evidence/RV-EV-01.stderr.log`

### RV-EV-02 — 同一 baseline runner 独立复跑

`run_project_impact_baseline.py --repeat 1` exit 0。

独立结果：

```text
T02 status=VALID, matched=false, missing=DECISION_RECORDED
T03 status=VALID, matched=false, missing=DECISION_RECORDED
T04 status=VALID, matched=false, missing=DECISION_RECORDED

product_observed_authoritative_trace_completeness_rate = 4/12
governed_end_to_end_task_success_rate                  = 3/12
```

证据：

- `evidence/RV-EV-02-baseline.json`
- `evidence/RV-EV-02.stdout.log`
- `evidence/RV-EV-02.stderr.log`

### RV-EV-03 — 当前相关测试

独立运行：

```text
tests.test_webshop_trace_assembler
tests.test_webshop_runtime_gate
tests.test_project_impact_baseline
```

结果：`69 tests / 7 failures`。

7 个失败均集中在旧测量期望：

- T02/T03/T04 仍被测试硬编码为 `product_observed_trace_status = NOT_AVAILABLE`；
- 产品轨迹集合仍硬编码为 T01/T09/T10/T12；
- 主指标仍按修复前基线计算。

这进一步证明 fixture 与测量测试尚未随已接受产品轨迹契约同步。

证据：

- `evidence/RV-EV-03.stdout.log`
- `evidence/RV-EV-03.stderr.log`

## 4. AC 裁决

| AC | 裁决 | 说明 |
|---|---|---|
| AC-01 | 部分通过 | 单一 Prepayment Toolkit 已存在，但未完成全部专项测试 |
| AC-02 | 通过 | 三个固定 declarative profile 已存在 |
| AC-03 | 未完成 | exactly-one / 0-match / multi-match 完整矩阵尚未完成 |
| AC-04 | 通过 | runtime 单次接入，未新增第二次 `validate_request` |
| AC-05 | 通过 | T02/T03/T04 实际均为统一六事件 VALID trace |
| AC-06 | 通过 | 中立 projection 已实现 |
| AC-07 | 阻断 | T02 VALID，但 stale fixture 误报缺 `DECISION_RECORDED` |
| AC-08 | 阻断 | T03 同上 |
| AC-09 | 阻断 | T04 同上 |
| AC-10 | 不可满足 | 同一冻结 fixture 无法得到合同要求的 7/12 与 6/12 |
| AC-11 | 部分通过 | 当前安全输出未见新副作用，但完整 invariance 尚未复跑 |
| AC-12 | 未完成 | 旧 trace hash / non-trace 全量比对未完成 |
| AC-13 | 当前通过 | 未给 T05-T08/T11 增加产品轨迹 |
| AC-14 | 部分通过 | 单路径静态审计已完成，完整专项未完成 |
| AC-15 | 通过 | 执行者正确保持 runner/fixture/registry 冻结，没有改考试标准 |
| AC-16 | 未完成 | 合同 Stop Condition 触发后未继续 full >=512 / repeat=3 |

因此任务不能 PASS。

## 5. 项目影响裁决

```text
Project impact verdict: INCONCLUSIVE
```

当前可以确认的是：

```text
产品能力：T02/T03/T04 已新增 VALID product trace
测量结果：仍显示 4/12 与 3/12
原因：测量契约陈旧，而不是产品轨迹无效
```

在修正 fixture 并重新执行同一 baseline 之前，不能把本轮记为 `IMPROVED`；也没有证据支持 `REGRESSED` 或 `NO_MEASURABLE_GAIN`。

B-03 / H-03 暂不改变，项目地图不在本轮机械更新。

## 6. 后续动作

创建一个独立的 measurement-contract repair：

```text
Task ID: P9-PRODUCT-AUTHORITATIVE-TRACE-PREPAYMENT-MEASUREMENT-CONTRACT-REPAIR-V1
Task kind: repair
Next state: CONTRACT_FROZEN / Executor
```

该包只允许：

```text
修正 T02/T03/T04 fixture 事件名
+ 更新对应测量测试硬编码
+ 用同一 runner 重建 repeat=3 基线
```

禁止修改任何 `src/` 产品代码、runner、authoritative trace registry 或业务规则。

修复通过后，再基于保留的当前产品实现重新发一个 bounded continuation，完成原能力实验尚未完成的 ambiguity、hash invariance、full >=512 与 repeat=3 复核。

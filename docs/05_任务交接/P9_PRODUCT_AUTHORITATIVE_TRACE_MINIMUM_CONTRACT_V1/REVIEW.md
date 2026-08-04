# Evaluator Review

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-MINIMUM-CONTRACT-V1`  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `evaluator_design`  
Baseline HEAD: `71a3acbbd9622b68a8064381b9034e07c1f4d700`  
Project map revision: `2026-08-04-r5`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Task verdict: `REJECTED`  
Project impact verdict: `NOT_APPLICABLE`

```yaml
review_state: REJECTED
project_impact_verdict: NOT_APPLICABLE
commit_performed: false
push_performed: false
network_call_performed: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_order_side_effect_performed: false
```

## 1. 裁决摘要

本任务正确完成了两件基础工作：

1. 明确区分产品实际产生的轨迹与评测器事后合成 Replay；
2. 确认当前产品轨迹真实基线仍为 `0/12 VALID`，没有通过改名或补事件把指标伪造为绿色。

但合同、12 项覆盖映射和 `NEXT_SLICE.md` 之间存在多处阻断性矛盾。按当前设计直接进入 T10 实现，会出现以下问题：

```text
新合同要求：
ProductAuthoritativeTrace envelope
+ 7 类事件
+ PRODUCT_OBSERVED 来源
+ 稳定 source object refs

冻结 runner 实际只支持：
authoritative_trace_events: tuple[ReplayEvent]
+ 5 类旧 ReplayEvent
+ 不读取 ProductAuthoritativeTrace envelope
```

因此下一包无法同时满足：

```text
使用冻结的同一 runner
且
把新 ProductAuthoritativeTrace 判为 VALID
```

该问题不是文字表述问题，而是下一 capability experiment 无法执行和归因，必须先修复设计并拆出测量适配前置阶段。

## 2. 阻断问题 F-01：新轨迹合同与冻结 runner 不兼容

设计文档要求产品 outcome 暴露：

```python
authoritative_trace: ProductAuthoritativeTrace | None
```

但冻结 runner 的 `_product_observed_trace()` 只读取：

```python
authoritative_trace_events: tuple[ReplayEvent]
```

并要求每个事件是旧的 exact `ReplayEvent`。旧枚举只有：

```text
AUTHORITY_RECORDED
ORDER_RECORDED
REQUEST_RECORDED
RUNTIME_DECISION_RECORDED
PAYMENT_OUTCOME_RECORDED
```

T10 新 slice 冻结的 7 类事件还要求：

```text
ACTION_RECORDED
RESULT_RECORDED
```

这两类事件不在旧 `ReplayEventType` 中。独立静态审计结果：

```text
runner_reads_authoritative_trace          false
runner_reads_authoritative_trace_events   true
runner_requires_replay_event              true
required_events_missing_from_runner       ACTION_RECORDED, RESULT_RECORDED
same_runner_can_validate_new_contract     false
```

证据：`RV-EV-01`。

### 裁决

`AC-03`、`AC-06` 不通过。

### 必须修复

下一能力实验前必须拆出一个独立“测量适配阶段”：

```text
先让 runner 支持新 envelope
→ 在产品仍不产出 trace 时重新冻结 0/12 BEFORE
→ 证明不能回退到 evaluator replay
→ 冻结新 runner hash
→ 再实施单一 T10 产品变量
```

不能在同一个 capability experiment 中同时修改产品轨迹和 runner 读取逻辑，否则无法判断改善来自产品还是评测器。

## 3. 阻断问题 F-02：T10 有两个 Payment 实体，schema 没有角色语义

T10 实际对象：

```text
当前 execution candidate payment_ref
= project-baseline-payment-1

当前 GovernedPaymentAction.payment_ref
= project-baseline-payment-1

历史已成功 payment_ref
= project-baseline-payment-existing-success
```

历史付款用于触发重复付款阻断，当前候选付款绑定当前 action。两者是两个不同 Payment 实体。

当前 schema 只有一个通用 `payment_ref`，同时规定“同一实体的非空引用全链一致”，却没有冻结：

- `payment_role`；
- `HISTORICAL_SUCCEEDED_PAYMENT`；
- `CURRENT_PAYMENT_CANDIDATE`；
- 两个 Payment 与同一 request 的关系规则。

按当前设计，validator 只能二选一：

1. 把两个 payment ref 当冲突，T10 永远 `INVALID`；
2. 在 ACTION 或历史 PAYMENT 事件中省略关键 ref，轨迹无法证明真实绑定。

证据：`RV-EV-02`。

### 裁决

`AC-02`、`AC-05`、`AC-06` 不通过。

### 必须修复

事件必须增加关闭的对象角色，并按 `(entity_type, entity_role)` 校验一致性。例如：

```text
PAYMENT_OUTCOME_RECORDED
role = HISTORICAL_SUCCEEDED_PAYMENT
payment_ref = existing-success
request_ref = current request

ACTION_RECORDED
role = CURRENT_PAYMENT_CANDIDATE
payment_ref = candidate payment
request_ref = current request
```

同时冻结关系断言：历史 payment 必须出现在 `KnownPaymentAttemptPreflightFact.related_attempt_refs` 中；当前 action payment 必须等于当前 execution candidate。

## 4. 阻断问题 F-03：部分源对象没有稳定引用，RESULT 还存在循环引用

合同要求每个事件都有非空、稳定的 `source_object_ref`，并要求 `RESULT_RECORDED` 引用实际返回 outcome。

但 T10 当前对象中：

```text
RuntimeGateRecord：没有 record_id，也没有 occurred_at
WebShopBuyNowGateOutcome：没有 outcome_id / result_id / record_id
```

设计没有冻结无原生 ID 对象的引用生成规则，也没有解决以下循环：

```text
outcome 包含 trace
→ trace 的 RESULT 事件引用 outcome
→ 如果直接 hash outcome，又会包含 trace 自身
```

证据：`RV-EV-02`。

### 裁决

`AC-02`、`AC-03`、`AC-06` 不通过。

### 必须修复

冻结技术引用规则，不得临时发明：

```text
有原生 ID：使用 type + native id/version
无原生 ID：使用 type + canonical hash(to_dict projection)
RESULT ref：hash(outcome projection excluding authoritative_trace)
RuntimeGateRecord ref：hash(runtime_record.to_dict())
```

必须明确 hash 输入、排除字段和 schema version，避免循环和跨版本漂移。

## 5. 重要问题 F-04：T05/T06 的最终决策事件映射错误

T05、T06 实际执行顺序：

```text
prepayment decision = ALLOW
→ governed action verification fails
→ T05 final decision = DENY
→ T06 final decision = INDETERMINATE
```

覆盖映射却只安排：

```text
ACTION_RECORDED
PREPAYMENT_DECISION_RECORDED
RESULT_RECORDED
```

当前 taxonomy 没有 `ACTION_BINDING_DECISION_RECORDED`。因此轨迹中的唯一结构化 decision event 是 `ALLOW`，无法解释最终 `DENY / INDETERMINATE`。

独立结果：

```text
T05 prepayment=ALLOW, final=DENY
T06 prepayment=ALLOW, final=INDETERMINATE
```

证据：`RV-EV-02`。

### 裁决

`AC-03`、`AC-04` 不通过。

### 必须修复

增加关闭事件：

```text
ACTION_BINDING_DECISION_RECORDED
```

来源必须是 `GovernedActionBindingFact`，并明确映射：

```text
VALID           → 继续执行，不代表最终支付允许
INVALID         → DENY
MISSING_EVIDENCE→ INDETERMINATE
```

轨迹只记录既有 fact 结果，不重新执行 action binding。

## 6. 重要问题 F-05：T02—T04 缺少授权/当前订单快照角色

T02—T04 实际都比较两个订单快照：

```text
authorized order version = webshop-v1
current order version    = mutation-specific v2
```

但 profile 只包含一个 `ORDER_RECORDED`，没有：

- `AUTHORIZED_ORDER` 与 `CURRENT_ORDER` 角色；
- order version ref；
- 两个快照与 `ValidationResult` 的关系。

尤其 T04 的 `order_differences` 实际为空，变化依据存在于 `ValidationResult.evidence` 和 confirmation/order binding 证据中；覆盖文档却把 `OrderDifference` 列为当前真实对象，描述不准确。

证据：`RV-EV-02` 及评估者 T04 原始输出。

### 裁决

`AC-03`、`AC-04` 不通过。

### 必须修复

可采用以下任一关闭方案：

```text
两个 ORDER_RECORDED
+ role = AUTHORIZED_SNAPSHOT / CURRENT_SNAPSHOT
+ order_id / order_version
```

或定义两个明确事件类型。T04 的来源映射必须改为真实存在的 `ValidationResult.evidence` / confirmation binding evidence，不得声明不存在的 `OrderDifference`。

## 7. 已通过部分

以下部分通过：

- 产品轨迹与 evaluator replay 的边界定义清楚；
- 当前基线诚实保持 `0/12 VALID`；
- 没有把设计任务包装为项目改善；
- 分阶段、小 slice 原则正确；
- 执行者没有修改产品代码、测试、runner、fixture 或既有 evidence；
- 133 个受保护文件独立复核全部未变化；
- HEAD 未变化；
- v2.1 结构校验通过。

证据：`RV-EV-03`。

## 8. AC 裁决

| AC | 裁决 | 依据 |
|---|---|---|
| AC-01 | 通过 | 产品轨迹与 evaluator replay 边界清楚，禁止伪装情形充分 |
| AC-02 | 不通过 | 无对象角色；无无-ID对象稳定 ref 规则；RESULT 循环引用未解决 |
| AC-03 | 不通过 | 冻结 runner 不支持新事件；缺 ACTION_BINDING 决策；订单快照角色缺失 |
| AC-04 | 不通过 | T05/T06 决策来源错误；T02—T04 快照映射不完整；T04 source object 描述不实 |
| AC-05 | 不通过 | “不复制规则”方向正确，但 T10 两个 Payment 实体无法按当前 schema 正确引用 |
| AC-06 | 不通过 | T10 slice 与冻结 runner、引用模型互相矛盾，当前不可执行 |
| AC-07 | 通过 | 设计→单 slice→扩展的阶段原则正确，项目影响保持 N/A |
| AC-08 | 通过 | 报告、证据、范围审计和 validator 齐全；产品受保护文件未变化 |

## 9. 最终裁决

```text
Task verdict: REJECTED
Project impact verdict: NOT_APPLICABLE
```

本裁决不否定 H-03。当前证据说明：

```text
B-03 仍是第一瓶颈
H-03 方向仍合理
但本版合同不能直接实施
```

项目地图维持 `2026-08-04-r5`，不更新瓶颈排序。

## 10. 独立证据

| Evidence | 内容 | 结果 |
|---|---|---|
| `RV-EV-01` | 新 envelope / 7 事件与冻结 runner / 5 ReplayEvent 的兼容性审计 | 发现阻断矛盾 |
| `RV-EV-02` | T10 双 Payment、稳定 ref、T05/T06 决策来源、T02—T04 快照映射 | 发现引用和覆盖模型不完整 |
| `RV-EV-03` | 133 个受保护文件、HEAD、workflow validator | 范围与流程通过 |

## 11. 后续动作

已布置修复任务：

```text
P9-PRODUCT-AUTHORITATIVE-TRACE-MINIMUM-CONTRACT-REPAIR-V1
```

修复任务只改设计文档、覆盖映射和下一阶段冻结文件，不实施产品代码。完成后必须形成：

```text
修正后的 schema / role / stable-ref 规则
修正后的 T01—T12 映射
测量适配前置任务
测量适配通过后的单一 T10 capability slice
```

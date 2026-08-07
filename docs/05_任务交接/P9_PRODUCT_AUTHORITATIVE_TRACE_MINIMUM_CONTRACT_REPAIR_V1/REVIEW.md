# Evaluator Review

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-MINIMUM-CONTRACT-REPAIR-V1`  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `repair`  
Baseline HEAD: `71a3acbbd9622b68a8064381b9034e07c1f4d700`  
Reviewed HEAD: `979ffc505bec0b626858d0d186f655867b5491bf`  
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

执行者已关闭父任务的大部分显性问题：

- 测量适配与 T10 产品能力实验已拆开；
- T10 当前候选付款与历史成功付款已区分角色；
- RESULT 自引用和无原生 ID 对象的稳定 ref 公式已给出；
- T05/T06 已增加动作绑定最终决策事件；
- T02—T04 已恢复授权/当前订单快照和真实 evidence 来源。

独立静态复跑中，结构、覆盖和受保护范围共 `53/53` 项通过，256 个产品、测试、runner 和 fixture 文件与执行者冻结清单一致。

但进一步按“下一包能否真正实现”检查时，发现三个阻断问题：

```text
F-06  source_object_ref 没有独立重算载体
F-07A T10 角色清单与实际事件序列不一致
F-07B T10 ACTION_RECORDED 的 entity / source-object 映射未冻结
```

因此当前设计仍不能直接进入 measurement-adapter 实现。

## 2. 已确认通过的修复

### 2.1 两阶段归因边界

设计已明确：

```text
阶段 A：只修改测量层，产品仍为 0/12 trace
阶段 B：使用同一 accepted runner，只修改 T10 产品 trace
```

旧 runner 只作为阶段 A 输入，阶段 B runner/before hash 均延后冻结。该部分通过。

### 2.2 T02—T06 映射

独立结构化检查确认：

- T02—T04 均有授权订单和当前订单两个事件；
- T04 不再把不存在的 `OrderDifference` 当 source object；
- T05 的 `INVALID → DENY` 来自 `GovernedActionBindingFact.status`；
- T06 的 `MISSING_EVIDENCE → INDETERMINATE` 来自同一既有 fact。

该部分通过。

### 2.3 T10 双 Payment

独立检查确认：

```text
CURRENT_PAYMENT_CANDIDATE
!= HISTORICAL_SUCCEEDED_PAYMENT
```

且当前候选 ref 关联 `GovernedPaymentAction.payment_ref`，历史成功 ref 关联 `KnownPaymentAttemptPreflightFact.related_attempt_refs`。该部分通过。

### 2.4 范围和当前真实基线

- 当前 `src/` 中仍不存在 `authoritative_trace` producer；
- 当前产品轨迹仍为 `0/12 VALID`；
- 256 个受保护文件无缺失、无哈希变化；
- 未运行网络、真实 WebShop、Buy Now、支付或订单副作用。

该部分通过。

## 3. 阻断问题 F-06：source ref 无法由 runner 独立重算

当前合同同时要求：

```text
runner 只读取 outcome.authoritative_trace
source_object_ref 可按冻结规则重算
事件值必须与既有 fact 输出一致
stable ref 不能重算时 fail closed
```

但 `ProductTraceEvent` 只有：

```text
source_object_type
source_object_ref
```

没有冻结以下任何一种可执行载体：

```text
source projection
source binding / source registry
显式 resolver 输入合同
```

当前 `WebShopBuyNowGateOutcome` 也没有公开 T10 校验所需的全部源对象，至少缺少：

- `IntentMandate`；
- authorized/current `Order`；
- `GovernedPaymentAction`；
- 当前候选 `PaymentExecutionRecord`；
- 历史成功 `PaymentExecutionRecord`。

所以 runner 只有 ref 字符串，无法证明该 ref 真由指定对象投影生成，也无法核对事件 decision/status/reason 是否来自指定源对象。

### 裁决

`AC-05` 不通过。

### 必须修复

冻结一个自包含、最小披露的 source-binding 合同，至少包括：

```text
source_object_type
source_object_ref
projection_schema
primitive canonical projection
```

每个事件必须引用唯一 source binding；validator 必须能只依赖 trace 自身重算 ref 和核对冻结字段路径。不得依赖 evaluator 事后重建或 runner 偷读未声明调用参数。

证据：`RV-EV-03`。

## 4. 阻断问题 F-07A：T10 角色和事件序列不一致

T10 结构化覆盖声明角色包含：

```text
AUTHORIZED_ORDER_SNAPSHOT
CURRENT_ORDER_SNAPSHOT
```

但事件序列只有：

```text
ORDER_RECORDED[CURRENT_ORDER_SNAPSHOT]
```

`AUTHORIZED_ORDER_SNAPSHOT` 没有对应事件。

### 裁决

`AC-08` 不通过。

### 必须修复

T10 profile 必须二选一并全处一致：

1. 同时记录授权/当前两个订单角色；或
2. 删除未使用角色，并证明该 profile 不需要授权快照。

设计、覆盖 JSON、`NEXT_SLICE.md` 必须使用同一关闭序列。

证据：`RV-EV-04`。

## 5. 阻断问题 F-07B：ACTION_RECORDED 字段语义不明确

`NEXT_SLICE.md` 写为：

```text
ACTION_RECORDED [GOVERNED_ACTION / CURRENT_PAYMENT_CANDIDATE]
```

结构化覆盖却写为：

```text
ACTION_RECORDED[CURRENT_PAYMENT_CANDIDATE]
```

事件合同只有一个 `entity_role` 和一组 `source_object_type/ref`，但没有冻结：

- entity_type 到底是 `GovernedPaymentAction` 还是 `PaymentExecutionRecord`；
- entity_role 到底是 `GOVERNED_ACTION` 还是 `CURRENT_PAYMENT_CANDIDATE`；
- source object 是什么；
- entity ref 从哪个字段取得；
- decision/status/reason 从哪个 source projection 路径取得。

### 裁决

`AC-09` 不通过。

### 必须修复

建立 profile-specific 的“事件—实体—源对象”映射表，不再使用斜杠混写。每个事件必须冻结：

```text
event_type
entity_type
entity_role
entity_ref derivation
source_object_type
projection_schema
value paths
relations
```

证据：`RV-EV-04`。

## 6. 评估脚本偏差说明

首次独立脚本把完整值：

```text
INVALID → DENY
MISSING_EVIDENCE → INDETERMINATE
```

错误地按纯 `DENY / INDETERMINATE` 精确匹配，产生 2 项评估器假失败。原始输出已保存为 `RV-EV-01-initial.*`。修正检查器后，`RV-EV-02` 为 `53/53` 通过。

该偏差属于评估器自身问题，不计入执行者缺陷。

## 7. AC 裁决

| AC | 裁决 | 独立依据 |
|---|---|---|
| AC-01 | 通过 | measurement adapter 与产品 capability 已拆分 |
| AC-02 | 通过 | 阶段 B runner/before hash 条件冻结，旧 runner 仅作阶段 A 输入 |
| AC-03 | 通过 | 关闭角色和 `(entity_type, entity_role)` 一致性规则已建立 |
| AC-04 | 通过 | T10 两个 Payment 角色、不同 ref 与既有 fact 关系已建立 |
| AC-05 | 不通过 | source ref 只有字符串，无 projection/registry/resolver，runner 无法独立重算 |
| AC-06 | 通过 | T05/T06 最终决策事件和来源正确 |
| AC-07 | 通过 | T02—T04 双快照与 T04 evidence 来源正确 |
| AC-08 | 不通过 | T10 `entity_roles` 含授权快照，但事件序列没有对应事件 |
| AC-09 | 不通过 | T10 ACTION 的 entity/source 映射含斜杠歧义，未形成关闭字段矩阵 |
| AC-10 | 通过 | 报告、原始证据、范围审计和 workflow 证据齐全 |

## 8. 最终裁决

```text
Task verdict: REJECTED
Project impact verdict: NOT_APPLICABLE
```

本裁决不否定 B-03 或 H-03。当前问题仍是设计合同尚不可直接执行，不是产品能力回归。

项目地图维持 `2026-08-04-r5`，不更新瓶颈排序。

## 9. 独立证据

| Evidence | 内容 | 结果 |
|---|---|---|
| `RV-EV-01-initial` | 首次评估脚本及自身精确匹配偏差 | 评估器假失败，已保留 |
| `RV-EV-02` | 角色、覆盖、stable-ref 公式、T02—T10、256 文件范围复核 | 53/53 通过 |
| `RV-EV-03` | source ref 独立重算可执行性审计 | 发现 F-06 BLOCKING |
| `RV-EV-04` | T10 角色/序列和 ACTION 字段映射审计 | 发现 F-07A/F-07B BLOCKING |

## 10. 后续动作

已布置下一修复包：

```text
P9-PRODUCT-AUTHORITATIVE-TRACE-SOURCE-BINDING-CONTRACT-REPAIR-V1
```

下一包仍只修设计，不实现 trace 类型、validator、runner 或产品 outcome。只有 source binding 和 T10 profile 映射被独立接受后，才能冻结 measurement-adapter 任务。

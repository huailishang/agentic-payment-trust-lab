# Evaluator Review

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-SOURCE-BINDING-CONTRACT-REPAIR-V1`  
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-MINIMUM-CONTRACT-REPAIR-V1`  
Baseline HEAD: `979ffc505bec0b626858d0d186f655867b5491bf`  
Reviewed HEAD: `979ffc505bec0b626858d0d186f655867b5491bf`

```yaml
workflow: evaluator-executor-workflow/v2.1
task_kind: repair
task_verdict: REJECTED
project_impact_verdict: NOT_APPLICABLE
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-08-04-r5
active_bottleneck_id: B-03
hypothesis_id: H-03
commit_performed: false
push_performed: false
```

## 1. 裁决

本任务结构上完成度较高，但设计仍不能稳定映射到当前真实产品对象，因此打回。

```text
结构与范围检查：691/691 PASS
语义可执行性：F-01—F-08 BLOCKING

Task verdict: REJECTED
Project impact verdict: NOT_APPLICABLE
```

B-03 仍是当前第一瓶颈；H-03 未被否定。失败原因是 source-binding/reference model 仍有实现级矛盾，不是产品轨迹假设已经失效。项目地图保持 `2026-08-04-r5`，本轮不更新。

## 2. 独立复核证据

### RV-EV-01 — 独立结构复核

- Script: `evidence/RV-EV-01-structural-review.py`
- Meta: `evidence/RV-EV-01.meta.json`
- Stdout: `evidence/RV-EV-01.stdout.log`
- Result: `691/691 PASS`

独立确认：

- T01—T12 恰好 12 项；
- T10 恰好 12 个事件，角色顺序与合同一致；
- 每个事件都有 source object、projection schema、ref mode 和 value-path 字段；
- projection registry、禁止字段、0/12 基线、条件 slice 和 no-hidden-resolver 文档均存在；
- `src/`、`tests/`、`scripts/`、`samples/` 未修改；
- HEAD 保持 baseline；
- 当前产品仍无 `authoritative_trace` producer。

### RV-EV-02 — 独立语义可执行性复核

- Script: `evidence/RV-EV-02-semantic-executability-review.py`
- Meta: `evidence/RV-EV-02.meta.json`
- Stdout: `evidence/RV-EV-02.stdout.log`
- Result: `8 BLOCKING findings`

## 3. Blocking findings

### F-01 — 同一 T10 Order native ref 对应两个不同 binding

T10 实际路径使用 `_gate_context()`，其中未提供独立 authorized adaptation 时：

```text
authorized = current
```

因此授权订单与当前订单是同一个 `Order` 对象、同一个 native ref。当前设计却要求：

```text
order-authorized-snapshot-trace/v1
order-current-snapshot-trace/v1
```

两个不同 canonical binding，并规定事件按 `source_object_ref` 恰好解析到一个 binding。该条件不能同时成立。

最低修复：把 source object identity 与 binding identity 分开；或两个角色共享同一个 Order binding，由 `entity_role` 区分。

### F-02 — Relation target ref 与目标 entity ref 不一致

当前订单 entity ref 定义为：

```text
order_id + order_version
```

但 Request、当前 Payment、历史 Payment 指向订单的 relation path 只提供：

```text
order_ref / order_id
```

validator 若按合同要求核对目标 role/ref，这些关系无法匹配。

最低修复：冻结唯一、带类型且无歧义的 entity-ref 模板；每条 relation 必须能够生成与目标事件完全相同的 entity ref，或明确使用受控 native-id match mode。

### F-03 — Decimal canonicalization 未冻结

`Order.total_amount`、`TransactionRequest.amount`、`PaymentExecutionRecord.amount` 均为 `Decimal`，但 canonical JSON 只冻结了 Enum、datetime 和 tuple 转换。

最低修复：冻结 Decimal 的唯一字符串表示，禁止 float 转换，并增加尾零、负零、精度和固定 hash 样例。

### F-04 — 相同重复 binding 的判定互相矛盾

设计文档规定完全相同的重复 binding 可由 validator 归一；Measurement Adapter 又把“duplicate identical binding 未归一”列为不能得到 `VALID` 的反例。

最低修复：二选一冻结。建议 envelope 中 `binding_ref` 必须唯一，任何重复项均判 `INVALID`。

### F-05 — Coverage 引用不存在的产品类型

结构化 registry 和 T12 使用：

```text
PaymentStatusConflictOutcome
```

当前代码实际类型为：

```text
PaymentStatusConflictFact
```

其真实字段为 `resolution`、`effective_status`、`reason_codes` 等，不是当前 registry 中的 `status`、`retry_allowed`。

最低修复：所有 `source_object_type` 必须通过真实代码类清单核验，projection 字段必须存在或有明确的关闭提取路径。

### F-06 — RESULT projection 从错误对象读取 decision

多个任务把 `WebShopPaymentFulfilmentOutcome` 作为 FINAL_OUTCOME source，并声明 projection 含 `decision`。真实类没有 `decision` 字段；它只包含 `ready`、payment、recovery、status conflict、lifecycle、retry 和 reason 等字段。

同时合同又禁止从隐藏 GateContext 或另一个 outcome 补值，所以当前 RESULT projection 无法生成。

最低修复：使用真实包含 decision 的 `WebShopBuyNowGateOutcome`；或定义一个真实存在的组合 outcome。任何派生字段都必须冻结 source extraction path，不得隐式跨对象补值。

### F-07 — `entity_ref_path` 使用未定义的 `+` 表达式

例如：

```text
projection.order_id+projection.order_version
```

这不是字段路径，也没有冻结拼接分隔符、转义和解析语法，存在碰撞：

```text
ab + c = a + bc = abc
```

最低修复：字段 path 与 ref derivation 分开；复合 ref 使用关闭模板，例如 `Order:<order_id>`，禁止裸字符串相加。

### F-08 — NATIVE_REF 没有承诺完整 projection

NATIVE_REF 只包含 ID/version，但 Order、Request、Action、Payment projection 还携带金额、payee、status、关系等关键字段。runner 只读取 envelope 时，只能证明事件与 envelope 内 projection 自洽，无法发现同一 native ref 下整份 projection 被同时伪造。

最低修复：

```text
source_object_ref = 对象身份
binding_ref = sha256(projection_schema + exact projection)
event.source_binding_ref = binding_ref
```

所有 binding 都必须有 projection digest；native ref 不能再被当作 projection 完整性证明。当前阶段只证明产品输出内部完整性，不宣称外部密码学真实性。

## 4. AC 裁决

| AC | 裁决 | 依据 |
|---|---|---|
| AC-01 自包含 Source Binding | 不通过 | 已有 `source_bindings`，但 F-01、F-08 表明 source object ref 与 binding ref 未分离，不能保证唯一解析和 projection 完整性 |
| AC-02 ref 重算与值核对 | 不通过 | F-02、F-03、F-07、F-08；relation ref、Decimal、复合 ref grammar 和 native projection commitment 未关闭 |
| AC-03 最小披露与精确投影 | 不通过 | 字段 allowlist 存在，但 F-05、F-06 表明 source type/field 未与真实对象闭合 |
| AC-04 T10 exact matrix | 不通过 | 12-event 顺序通过，但 F-01、F-02 使 event/entity/source/relation matrix 不可执行 |
| AC-05 T01—T12 coverage | 不通过 | 12 项结构通过，但 T12 使用不存在类型，多个 RESULT source/field 不真实 |
| AC-06 Measurement Adapter Freeze | 不通过 | no-hidden-resolver 已写入，但 F-04 规则冲突，且底层 reference model 未关闭 |
| AC-07 条件 T10 Slice | 不通过 | 保持 conditional，但继承 F-01/F-02/F-03/F-07/F-08，不能作为后续可冻结输入 |
| AC-08 结构化证明与父 Findings Closure | 不通过 | 报告声称 blocking findings 3→0，但独立复核发现 8 个实现级阻断点 |
| AC-09 范围与工作流 | 通过 | 受保护范围不变、无 producer、无后续正式合同、EV triplet 和 validator 均符合要求 |

## 5. 项目影响裁决

```text
Project impact verdict: NOT_APPLICABLE
```

本任务是设计修复，没有修改产品、runner、测试或测量结果：

```text
product-observed trace: 0/12 → 0/12
GESR: 0/12 → 0/12
```

因此不宣称改善、退化或无收益。

## 6. Continuation action

创建下一修复包：

```text
P9-PRODUCT-AUTHORITATIVE-TRACE-REFERENCE-MODEL-GROUNDING-REPAIR-V1
```

路径：

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1/
CONTRACT.md
```

下一包只修设计和结构化映射：

1. 分离 `source_object_ref`、`binding_ref`、`entity_ref`、relation target ref；
2. 所有 binding 使用 projection digest；
3. 冻结 Decimal 和重复 binding 规则；
4. 将所有 source type/field 与真实代码对象对齐；
5. 修复 T10 Order 共享 binding 和 relation ref；
6. 修复 T12 conflict fact 与 RESULT source；
7. 保持 measurement adapter 和 T10 capability 仍未冻结；
8. 产品轨迹继续保持 0/12。

`CURRENT.md` 应路由到：

```text
CONTRACT_FROZEN / Executor
```

## 7. Authorization and repository state

- commit: false
- push: false
- network/API/download: false
- dependency/environment: false
- WebShop/Buy Now/payment/order side effect: false
- project map update: no

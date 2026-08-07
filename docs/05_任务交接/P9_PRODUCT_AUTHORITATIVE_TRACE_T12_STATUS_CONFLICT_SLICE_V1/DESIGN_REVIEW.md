# Contract Design Review

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-T12-STATUS-CONFLICT-SLICE-V1`  
Review type: `PRE_EXECUTION_CONTRACT_REVIEW`  
Review date: `2026-08-06`  
Execution status: `NOT_STARTED`  
Disposition: `SUPERSEDED_BEFORE_EXECUTION`

## 1. 结论

旧 T12 合同不再执行。

原因不是 T12 场景不重要，而是合同实现方式仍要求：

```text
新增 T12 专属 builder
→ sidecar 按 T01 → T09 → T12 顺序逐个尝试
→ 后续 T11、T02…继续各写一个 builder
```

这会把“统一轨迹”做成“公共底层 + 多个近似重复的场景实现”，没有真正解决规模化扩展问题。

本次没有执行代码、没有生成 REPORT、没有产生任务或项目影响 verdict。旧合同由新任务包替代：

```text
P9-PRODUCT-AUTHORITATIVE-TRACE-SIDECAR-FAMILY-TOOLKIT-V1
```

## 2. 结构证据

当前两个 Sidecar 场景 builder：

| 文件 | 行数 |
|---|---:|
| `webshop_happy_path_authoritative_trace.py` | 597 |
| `webshop_unknown_payment_authoritative_trace.py` | 595 |

两条轨迹与 T12 冻结 profile 的结构对比：

```text
共同事件 1—9：完全相同

1  AUTHORITY
2  AUTHORIZED_ORDER
3  CURRENT_ORDER
4  REQUEST
5  ACTION
6  PAYMENT_CANDIDATE
7  ACTION_BINDING_FACT
8  RUNTIME_GATE
9  PAYMENT_OUTCOME

第 10 个事件：按场景变化
T01 = FULFILMENT_OUTCOME
T09 = RECOVERY_OUTCOME
T12 = STATUS_CONFLICT_FACT

第 11 个事件：全部是 FINAL_OUTCOME
```

即 T01、T09、T12 的 **9/11 事件完全一致**，差异集中在：

1. 场景进入条件；
2. 第 10 个扩展事实；
3. profile 名称和最终状态约束。

当前产品调用方式仍是：

```text
build_t01_happy_path_trace()
→ None 时 build_unknown_payment_recovery_trace()
→ 旧合同计划再追加 build_t12_status_conflict_trace()
```

因此继续执行旧合同会增加第三个约 500—600 行的专属 builder，属于逐场景复制，不符合公共能力收敛目标。

## 3. 新设计原则

下一包改为三层：

```text
Trace Assembler
→ 负责 binding / event / relation / envelope 机械组装

Sidecar Trace Toolkit
→ 只实现一次公共 1—9 + 11 事件、事实一致性检查、唯一 profile 选择

Sidecar Trace Profile
→ 声明 T01 / T09 / T12 的状态条件和第 10 个扩展事件
```

Profile 不是任意 DSL，不读取 YAML/JSON，也不允许配置任意字段表达式。只使用冻结枚举和固定字段，避免把简单重构做成通用规则引擎。

## 4. 新任务的验收方向

新包必须证明：

```text
产品 sidecar 只调用一个统一 builder
T01/T09 不再拥有完整事件组装逻辑
T12 只新增 profile，不新增专属完整 builder
T01/T09 完整轨迹 hash 不变
T12 从 NOT_AVAILABLE → VALID
Product Trace 3/12 → 4/12
GESR 2/12 → 3/12
```

旧 T12 合同保留作为审计记录，不删除、不覆盖。
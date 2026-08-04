# Measurement Adapter Freeze

Task name: 产品权威轨迹测量适配  
Task kind: `maintenance`  
Project impact verdict: `NOT_APPLICABLE`  
Prerequisite: 本设计修复任务被 Evaluator 接受

## 1. 单一目标

只让项目级测量层能够读取并严格校验新的 `ProductAuthoritativeTrace` envelope；产品 outcome 继续不产出 trace，重新冻结可信的 `0/12 VALID` BEFORE 和新 runner hash。

```text
旧 runner
只读取 authoritative_trace_events: tuple[ReplayEvent]

阶段 A
读取 exact outcome.authoritative_trace
→ 校验 envelope / profile / event / role / ref / relation
→ 不存在仍为 NOT_AVAILABLE
→ evaluator replay 不得回退计入
```

## 2. 为什么是 maintenance

本任务改变的是测量工具兼容性，不改变产品行为，也不宣称 B-03 已改善。`evidence_fix` 不适用，因为本任务会修改 runner、增加纯数据类型和测试。

## 3. 允许的主要变量

- 增加 `ProductAuthoritativeTrace`、`ProductTraceEvent`、closed enum 和纯结构 validator；
- runner 读取 exact `authoritative_trace`；
- runner 校验 `source=PRODUCT_OBSERVED`、profile、顺序、角色、稳定 ref 和 relation；
- 增加 absent、invalid、unknown profile、broken ref、no-fallback 测试；
- 重新运行同一 T01—T12 target，输出新 runner hash 和 BEFORE hash。

## 4. 明确禁止

- 任一产品 outcome 开始产出 `authoritative_trace`；
- 把 evaluator replay 或 `authoritative_trace_events` 计入新产品轨迹；
- 修改决策、callback、状态、binding 或 side effect；
- 修改 T01—T12 fixture 的业务预期；
- 宣称 `IMPROVED`；
- 同时实现 T10 产品 trace。

## 5. 必须冻结的 BEFORE

阶段 A 通过后必须记录：

```text
product-observed trace = 0/12 VALID
GESR = 0/12
重复或禁止副作用 = 0/12
callback match = 12/12
决策—理由一致 = 12/12
```

同时冻结：

- accepted runner SHA-256；
- accepted target SHA-256；
- BEFORE output SHA-256；
- 非 trace 业务投影 SHA-256；
- full regression 结果；
- formal entry 结果。

## 6. 原子验收点

### MA-AC-01 — exact envelope

runner 只读取 `outcome.authoritative_trace`。字段不存在时返回 `NOT_AVAILABLE`。

### MA-AC-02 — no fallback

即使 evaluator replay 为 `VALID`，产品 trace 不存在时仍必须是 `NOT_AVAILABLE`。

### MA-AC-03 — strict validator

以下均不能通过：

- source 不是 `PRODUCT_OBSERVED`；
- profile 未知；
- sequence 断裂或重复；
- role 未知；
- 同一 `(entity_type, entity_role)` ref 冲突；
- relation target 不存在；
- final decision 无直接决策事件；
- stable ref 不能重算；
- RESULT ref 把 trace 自身纳入 hash。

### MA-AC-04 — zero product producers

静态审计确认所有产品 outcome 仍没有产生非空 `authoritative_trace`。

### MA-AC-05 — same 12-task baseline

同一 T01—T12 target 重新运行，产品轨迹仍为 `0/12 VALID`，其他项目指标和任务业务投影不变。

### MA-AC-06 — accepted hashes

Executor 报告 runner、target、BEFORE 和非 trace 投影 hash；Evaluator 独立复跑后接受这些 hash。

## 7. 预期修改范围

后续正式 CONTRACT 由 Evaluator 冻结，预期只允许：

- 新的纯 trace 数据合同与 validator 模块；
- 项目级 runner 的 trace 读取分支；
- 对应单元测试和测量测试；
- measurement task 的报告和证据。

产品 gate、sidecar、recovery、conflict outcome 文件不在允许范围内。

## 8. 停止条件

- 需要让任一产品 outcome 产出 trace；
- 需要改变 fixture 业务结果；
- 需要通过 replay fallback 才能得到 VALID；
- 不能保持 0/12 BEFORE；
- 非 trace 指标或业务投影发生变化；
- 需要网络、依赖安装、环境创建或外部副作用。

## 9. 对阶段 B 的交付

只有 Evaluator 接受阶段 A 后，才向 T10 capability slice 提供：

```text
accepted_runner_hash
accepted_target_hash
accepted_before_hash
accepted_non_trace_projection_hash
```

这些值替换父 `NEXT_SLICE.md` 中的 `TBD_AFTER_ADAPTER_ACCEPTANCE`。
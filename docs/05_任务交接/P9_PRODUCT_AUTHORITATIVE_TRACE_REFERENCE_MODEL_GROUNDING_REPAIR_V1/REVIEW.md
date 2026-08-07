# Evaluator Review

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-REFERENCE-MODEL-GROUNDING-REPAIR-V1`  
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-SOURCE-BINDING-CONTRACT-REPAIR-V1`  
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

本轮绝大多数引用模型问题已经修正，但 `PROJECTION_HASH_IDENTITY` 仍缺少可由后续 measurement adapter 独立实现的权威公式，因此任务打回。

```text
Evaluator independent checks: 1398/1400 PASS
Blocking findings: 2
Root cause: 1

Task verdict: REJECTED
Project impact verdict: NOT_APPLICABLE
```

这不是 T10、T12、Decimal、binding digest 或真实类映射再次失败。独立复核确认这些部分均可重算。阻断点仅是：

> 无 native ID 的对象如何计算 `source_object_ref`，精确算法只存在于执行者的 EV 构建脚本中，没有进入权威设计和结构化 registry。

B-03 仍是第一瓶颈，H-03 未被否定；项目地图保持 `2026-08-04-r5`。

## 2. 独立复核证据

### RV-EV-01 — 引用模型与真实对象独立复核

- Script: `evidence/RV-EV-01-independent-grounding-review.py`
- Meta: `evidence/RV-EV-01.meta.json`
- Stdout: `evidence/RV-EV-01.stdout.log`
- Stderr: `evidence/RV-EV-01.stderr.log`
- Result: `1398/1400 PASS`

初次脚本路径错误发生在验收逻辑开始前，原始证据保留为：

- `evidence/RV-EV-01-initial.meta.json`
- `evidence/RV-EV-01-initial.stdout.log`
- `evidence/RV-EV-01-initial.stderr.log`

独立复核实际完成：

- 16/16 source class 均存在且为 dataclass；
- 所有 direct/nested extraction path 均沿真实类型完整解析；
- T01—T12 恰好 12 项，角色、事件、schema、value path、relation target 均闭合；
- Decimal 正例、非法非有限值和固定 digest 可独立重算；
- 所有 `binding_ref` 可按权威 binding 公式独立重算；
- T10 为 12 events / 11 unique bindings，两个 Order role 共享同一 binding；
- T10 所有 event value 和 relation target 可从 projection 独立重算；
- T12 使用真实 `PaymentStatusConflictFact`；
- sidecar projection 不包含伪造的 `decision`；
- HEAD 未变化；`src/`、`tests/`、`scripts/`、`samples/` 无改动；
- 产品仍无 `authoritative_trace` producer。

## 3. Blocking finding

### F-01 — `PROJECTION_HASH_IDENTITY` 只有模式名，没有权威计算公式

结构化 registry 中 9 个 schema 使用：

```json
{
  "source_identity": {
    "mode": "PROJECTION_HASH_IDENTITY",
    "template": null
  }
}
```

这些 schema 包括：

```text
governed-action-binding-fact-trace/v2
governed-payment-action-missing-id-trace/v2
known-payment-attempt-preflight-fact-trace/v2
payment-recovery-result-trace/v2
payment-status-conflict-fact-trace/v2
runtime-gate-record-trace/v2
validation-result-trace/v2
webshop-buy-now-gate-outcome-result-trace/v2
webshop-payment-fulfilment-outcome-result-trace/v2
```

执行者实际采用的算法是：

```text
<SourceType>:projection-sha256:
sha256(canonical-json({
  projection_schema,
  projection
}))
```

该算法只写在：

```text
evidence/EV-01-build-grounded-reference-model.py
```

权威设计 `产品权威轨迹最小合同_v1.md` 只写了“projection identity hash”，结构化 registry 也只有 `mode` 和空 `template`，没有冻结：

- 固定前缀；
- hash payload 是否包含 `projection_schema`；
- canonical JSON 的精确输入；
- source type 如何进入 ref；
- schema/projection 改变时 ref 如何变化；
- 不匹配时的 exact verdict。

因此后续 measurement adapter 若只读取权威设计和 coverage registry，无法独立重算 `source_object_ref`，只能复制 EV 构建脚本中的隐含实现。这与“独立核验 object identity”和“不得依赖隐藏 resolver/实现细节”的目标冲突。

最低修复：把该公式加入权威设计和每个 `PROJECTION_HASH_IDENTITY` registry entry，并增加正反例。无需改动当前实例的 hash 值，也无需重做 T10/T12。

## 4. 已通过的实质修复

以下父 findings 已由独立复核确认关闭：

| Parent finding | 独立复核结果 |
|---|---|
| F-01 T10 同一 Order 被拆成两个 binding | 已关闭；两个 Order role 共享同一 `source_binding_ref` |
| F-02 relation target 与 entity ref 不一致 | 已关闭；T10 全 relation target 可独立解析 |
| F-03 Decimal 未冻结 | 已关闭；正反例和 digest 可重算 |
| F-04 duplicate binding 判定冲突 | 已关闭；统一 `INVALID` |
| F-05 不存在的 conflict 类型 | 已关闭；使用真实 `PaymentStatusConflictFact` |
| F-06 sidecar 伪造 decision | 已关闭；sidecar projection 无 decision |
| F-07 裸 `+` entity ref | 已关闭；typed template 无裸拼接 |
| F-08 native ref 未承诺 projection | 已关闭；所有 binding 使用完整 projection digest |

本次新 F-01 是 source-object identity 公式的规格缺口，不推翻上述关闭结果。

## 5. AC 裁决

| AC | 裁决 | 依据 |
|---|---|---|
| AC-01 分离四类引用 | 不通过 | 四类 ref 已分离，binding formula 已冻结；但 hash-based `source_object_ref` 算法未冻结，object identity 仍不能按权威合同独立重算 |
| AC-02 entity ref 与 relation | 通过 | typed template、T10 全 relation target 和 target assertions 均可独立解析 |
| AC-03 canonical primitive | 通过 | Decimal、Enum、datetime、tuple/list/dict 规则和固定样例可独立重算 |
| AC-04 projection 与真实代码对象闭合 | 通过 | 16 个类及全部 direct/nested extraction path 均沿真实 dataclass 类型解析 |
| AC-05 T10 真实引用闭环 | 通过 | 12 events、11 bindings、共享 Order binding、全部 event/relation/value 可重算 |
| AC-06 T01—T12 coverage grounding | 不通过 | 12 项映射本身闭合，但 9 个 registry entry 缺 source identity formula，结构化 registry 尚不足以驱动独立 validator |
| AC-07 后续冻结文档 | 不通过 | adapter 已要求分别核验 object identity，但权威输入没有提供 hash identity 算法 |
| AC-08 独立可执行性证明 | 不通过 | 当前实例可按 EV builder 实现重算，但独立实现仍需读取非权威构建脚本 |
| AC-09 范围与工作流 | 通过 | 受保护范围、HEAD、授权、路由和无副作用要求均满足 |

## 6. 项目影响

```text
Project impact verdict: NOT_APPLICABLE
```

本任务为设计修复，没有修改产品或测量实现：

```text
product-observed authoritative trace: 0/12 → 0/12
GESR: 0/12 → 0/12
```

不能宣称项目能力改善或退化。

## 7. Continuation action

下一修复包：

```text
P9-PRODUCT-AUTHORITATIVE-TRACE-PROJECTION-IDENTITY-FORMULA-REPAIR-V1
```

路径：

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/
CONTRACT.md
```

下一包仅处理：

1. 冻结 `PROJECTION_HASH_IDENTITY` 的精确 source-object ref 公式；
2. 将公式写入权威设计和结构化 registry；
3. 增加 schema/projection/type/prefix 篡改反例；
4. 证明 adapter 无需读取 EV builder 即可重算 object identity；
5. 保持现有 binding、T10、T12 和所有 hash 实例不变；
6. 保持 product trace / GESR 为 0/12。

通过该窄修复后，才冻结独立 measurement-adapter maintenance 任务。

## 8. Authorization

- commit: false
- push: false
- network/API/download: false
- dependency/environment: false
- WebShop/Buy Now/payment/order side effect: false
- project map update: no

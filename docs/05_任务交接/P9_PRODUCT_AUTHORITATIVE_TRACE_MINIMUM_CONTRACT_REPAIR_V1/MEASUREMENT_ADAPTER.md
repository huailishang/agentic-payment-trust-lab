# Measurement Adapter Freeze

Task name: 产品权威轨迹测量适配
Task kind: `maintenance`
Project impact verdict: `NOT_APPLICABLE`
Prerequisite: reference-model grounding repair 被 Evaluator 接受

## 1. 单一目标

只让测量层读取并严格校验 `outcome.authoritative_trace`。产品继续不产出 trace，重新冻结可信的 `0/12 VALID` BEFORE 和 accepted runner hash。

```text
runner reads exact envelope
→ event.source_binding_ref resolves envelope binding
→ validates object identity, binding digest, entity template and relation target separately
→ absent trace remains NOT_AVAILABLE
```

## 2. 唯一 resolver

唯一 resolver 是：

```text
outcome.authoritative_trace.source_bindings
```

禁止读取 `GateContext`、mandate/order/request/action/payment 原对象、fixture、known attempts 或 evaluator replay 补 source。

<!-- PROJECTION_HASH_IDENTITY_V1_ADAPTER:START -->
## 2.1 Object identity 两条路径

```text
NATIVE_TEMPLATE
→ 按 schema 冻结的 native template 重算 source_object_ref

PROJECTION_HASH_IDENTITY_V1
→ prefix = {source_object_type}:projection-sha256:
→ payload = {projection_schema, projection}
→ canonical JSON + SHA-256 + lowercase-hex-64
```

adapter 只读取 envelope 和内置冻结 registry。禁止读取 EV builder、fixture、GateContext、产品原对象或 evaluator replay。

以下均不得得到 `VALID`：

- formula_id、prefix、payload fields、canonical JSON 参数不匹配；
- schema 或 projection 改变但复用旧 ref；
- source type/prefix 大小写或冒号变化；
- digest 非小写 64 hex；
- payload 缺 `projection_schema`、只有 projection，或额外包含 `source_object_ref`；
- float、NaN、Infinity canonicalization；
- 把 source identity hash 与 `binding_ref` full-binding digest 混为一个公式。

object identity 通过后，仍必须单独重算 `binding_ref`；两者任一不一致都不能得到 `VALID`。
<!-- PROJECTION_HASH_IDENTITY_V1_ADAPTER:END -->

## 3. Strict matrix

以下均不得得到 `VALID`：

1. missing binding；
2. 任意 duplicate `binding_ref`，包括 identical 和 conflicting；
3. unreferenced binding；
4. unknown schema/class/field extraction；
5. source native identity mismatch；
6. binding digest mismatch；
7. projection extra/missing/forbidden field；
8. Decimal `1.0/1.00/1` 规范不一致；
9. Decimal `-0` 未规范为 `0`；
10. Decimal NaN/Infinity/float；
11. entity template 缺字段或出现裸 `+`；
12. relation target type/role/ref mismatch；
13. target binding version assertion mismatch；
14. RESULT projection 含 `authoritative_trace`；
15. sidecar RESULT 读取不存在的 `decision`；
16. product trace 缺失但 evaluator replay 有效；
17. hidden context fallback。

## 4. Validator 分层

```text
A. schema/source grounding
B. source_object_ref identity
C. binding_ref exact digest
D. entity_ref typed template
E. event decision/status/reason paths
F. relation exact target and binding assertions
G. profile sequence/completeness
```

任何 source class 或 extraction root 与当前代码不闭合时 fail closed。

## 5. BEFORE 必须保持

```text
product-observed trace = 0/12 VALID
GESR = 0/12
重复或禁止副作用 = 0/12
callback match = 12/12
决策—理由一致 = 12/12
```

同时冻结 accepted runner、target、BEFORE output、non-trace projection SHA-256。

## 6. 明确禁止

- 产品 outcome 开始产出 trace；
- 修改 T01—T12 业务预期；
- 同时实现 T10 产品 trace；
- 创建 measurement-adapter 或 T10 capability 正式 `CONTRACT.md`；
- 依赖网络、新环境或新依赖；
- 宣称项目 `IMPROVED`。

本文件是后续冻结输入，不是正式执行合同。

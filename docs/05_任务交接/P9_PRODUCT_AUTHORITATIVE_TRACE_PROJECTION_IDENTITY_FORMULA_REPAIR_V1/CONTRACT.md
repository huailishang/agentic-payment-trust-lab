# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-PROJECTION-IDENTITY-FORMULA-REPAIR-V1`  
Task name: 产品权威轨迹 Projection Identity 公式冻结修复 v1  
Task kind: `repair`  
Risk: `L0`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `979ffc505bec0b626858d0d186f655867b5491bf`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-04-r5`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-REFERENCE-MODEL-GROUNDING-REPAIR-V1`  
Parent verdict: `REJECTED / NOT_APPLICABLE`

父任务独立复核 `1398/1400 PASS`。T10、T12、Decimal、binding digest、真实类和全部 extraction path 已通过；唯一根因是 9 个 `PROJECTION_HASH_IDENTITY` schema 没有在权威设计和结构化 registry 中冻结精确 `source_object_ref` 公式。

本任务只关闭该规格缺口，不重做引用模型，不实现 measurement adapter、trace 或产品能力。

## Single objective

使任意独立实现只读取权威设计和结构化 registry，就能精确重算所有 `PROJECTION_HASH_IDENTITY` 的 `source_object_ref`，不需要读取 EV builder、fixture、产品原对象或隐藏 resolver。

## Parent finding to repair

### F-01 — Projection hash identity formula 未进入权威规格

当前 registry 只有：

```json
{
  "mode": "PROJECTION_HASH_IDENTITY",
  "template": null
}
```

执行者实际算法仅存在于父任务 EV builder：

```text
<SourceObjectType>:projection-sha256:
sha256(canonical-json({
  projection_schema,
  projection
}))
```

measurement adapter 因此无法仅依赖权威规格核验 object identity。

## Acceptance criteria

### AC-01 — 冻结唯一 Projection Identity 公式

更新：

```text
docs/03_架构设计/产品权威轨迹最小合同_v1.md
```

必须明确冻结：

```text
formula_id = PROJECTION_HASH_IDENTITY_V1

payload = {
  "projection_schema": <exact schema string>,
  "projection": <exact canonical primitive projection>
}

payload_bytes = UTF-8(
  JSON(payload,
       sort_keys=true,
       separators=(",", ":"),
       ensure_ascii=false,
       allow_nan=false)
)

digest = lowercase_hex(SHA-256(payload_bytes))

source_object_ref =
  <source_object_type>
  + ":projection-sha256:"
  + digest
```

必须冻结以下语义：

1. `source_object_type` 进入固定前缀，不进入 hash payload；
2. `projection_schema` 和 `projection` 都进入 payload；
3. payload 不包含 `binding_ref` 或 `source_object_ref`，避免循环；
4. projection 已按现有 canonical primitive 规则转换；
5. hash 为 SHA-256 小写 64 位十六进制；
6. prefix 大小写、冒号和 `projection-sha256` 字面值固定；
7. schema、projection、type 或 prefix 任一变化都不得复用原 ref；
8. 当前仅证明 envelope 内部 identity 一致性，不宣称外部真实性或签名身份。

不得使用“按 projection 算 hash”这类模糊描述代替精确公式。

### AC-02 — 结构化 registry 可直接驱动 validator

更新 T01—T12 结构化 coverage registry。每个 `PROJECTION_HASH_IDENTITY` entry 的 `source_identity` 必须至少包含：

```json
{
  "mode": "PROJECTION_HASH_IDENTITY",
  "formula_id": "PROJECTION_HASH_IDENTITY_V1",
  "prefix_template": "{source_object_type}:projection-sha256:",
  "hash_algorithm": "SHA-256",
  "digest_encoding": "lowercase-hex-64",
  "payload_fields": ["projection_schema", "projection"],
  "canonical_json": {
    "encoding": "UTF-8",
    "sort_keys": true,
    "separators": [",", ":"],
    "ensure_ascii": false,
    "allow_nan": false
  }
}
```

要求：

- 9 个 hash identity schema 必须完全一致地引用同一 `formula_id`；
- 不允许 `template: null` 作为唯一算法描述；
- `NATIVE_TEMPLATE` schema 保持当前 native identity 模板，不改变语义；
- validator 能只读 registry 重算 ref；
- registry 不引用 EV builder 文件或函数名。

### AC-03 — 固定正例不变

必须使用权威公式独立重算父任务现有实例，并证明以下内容不变：

- 父任务 9 类 hash identity source refs；
- T10 11 个 bindings 中所有 hash identity source refs；
- T12 conflict/sidecar source refs；
- 所有对应 `binding_ref`；
- T10 12 events / 11 unique bindings；
- T10 relation resolution；
- T12 sidecar decision 仍为 `null`；
- product trace / GESR 仍为 0/12。

不得通过修改现有固定值来让新公式通过。若精确公式与父 EV builder 不一致，停止执行并报告。

### AC-04 — 篡改和边界反例

结构化证据必须至少覆盖：

| 反例 | Expected |
|---|---|
| 删除 `projection_schema` | fail closed |
| 将 payload 改为只有 projection | ref mismatch / INVALID |
| 修改 schema 字符串 | ref 改变 |
| 修改任一 projection 字段 | ref 改变 |
| 修改 source type 前缀 | object identity mismatch / INVALID |
| `Projection-SHA256` 大小写变化 | prefix mismatch / INVALID |
| digest 大写 | encoding mismatch / INVALID |
| digest 非 64 hex | format mismatch / INVALID |
| float / NaN / Infinity | canonicalization fail closed |
| payload 加入 source_object_ref 导致循环 | schema/payload mismatch / INVALID |
| 使用 EV builder 作为 resolver | 禁止 |

必须给出每个反例的实际重算结果和 exact verdict。

### AC-05 — Measurement Adapter Freeze 同步

更新：

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/
MEASUREMENT_ADAPTER.md
```

要求：

- object identity 校验明确区分 `NATIVE_TEMPLATE` 和 `PROJECTION_HASH_IDENTITY_V1`；
- hash identity 直接引用权威 `formula_id` 和 registry 参数；
- adapter 只读取 envelope 和内置冻结 registry；
- 不读取 EV builder、fixture、GateContext、产品原对象或 evaluator replay；
- ref prefix/payload/digest/encoding mismatch 均不得得到 `VALID`；
- binding digest 校验继续使用现有独立公式，不与 source identity hash 混合。

### AC-06 — NEXT_SLICE 保持条件未冻结

更新或核验：

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/
NEXT_SLICE.md
```

必须保持：

```text
State = CONDITIONAL_NOT_FROZEN
prerequisite = measurement adapter accepted
runner/before/target/non-trace hashes = TBD_AFTER_ADAPTER_ACCEPTANCE
T10 = 12 events / 11 unique bindings
```

不得创建 measurement-adapter 或 T10 capability 正式 `CONTRACT.md`。

### AC-07 — 独立规格充分性证明

必须新增一个不 import、复制或读取父 EV builder 的独立 checker。它只能读取：

- 权威设计文档；
- 新结构化 registry/coverage；
- 父任务固定 JSON 实例；
- 当前真实源代码类型，仅用于确认 source type/schema 边界。

该 checker 必须证明：

```text
registry formula → 重算 source_object_ref
→ 重算 binding_ref
→ T10/T12 固定实例一致
→ negative matrix fail closed
```

REPORT 必须明确列出 checker 的允许输入，并证明没有读取：

```text
EV-01-build-grounded-reference-model.py
```

### AC-08 — 父 Finding Closure 与报告

REPORT 必须包含：

- F-01 closure；
- 权威 formula 和结构化 registry 示例；
- 9 个 schema 列表；
- 正例重算结果；
- 负例矩阵；
- 父 T10/T12/hash 值不变证明；
- 修改前后差异；
- changed files、完整 diff 和 hashes；
- 初始/最终 git status；
- 未运行项、授权和限制；
- workflow validator `OK`。

项目影响必须为 `NOT_APPLICABLE`。

### AC-09 — 范围与工作流

必须证明：

- `src/`、`tests/`、`scripts/`、`samples/` 全部不变；
- 当前产品仍无 `authoritative_trace` producer；
- product trace / GESR 仍为 0/12；
- 不修改父任务 REVIEW/RV-EV/EV 固定证据；
- 不创建后续正式实现合同；
- CURRENT 在 Executor 提交时保持 `EXECUTING / Executor`；
- evidence 使用 `EV-*` triplet；
- 未 commit、push、network、API、download、install、create environment 或执行外部副作用。

## Required outputs

必须新增或更新：

1. `docs/03_架构设计/产品权威轨迹最小合同_v1.md`
2. `docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md`
3. `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md`
4. 必要时更新父 `NEXT_SLICE.md`，但不得改变条件状态
5. 本任务 `REPORT.md`
6. 本任务 `evidence/EV-*` 和新的结构化 registry/正反例 JSON

## Allowed scope

May add or modify only:

- `docs/03_架构设计/产品权威轨迹最小合同_v1.md`
- `docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/REPORT.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-*`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/*.json`
- `CURRENT.md`（仅原子路由）

允许只读：

- 当前和父任务合同、报告、评估和固定 JSON 证据；
- `src/`、`tests/`、`scripts/`、`samples/`；
- 项目地图。

## Exclusions

- 不修改 `src/`、`tests/`、`scripts/`、`samples/`；
- 不实现 trace、validator、runner 或产品 outcome；
- 不修改父任务任何 `EV-*`、`RV-EV-*`、REPORT 或 REVIEW；
- 不重新设计四类 ref、Decimal、T10、T12 或 projection allowlist；
- 不改变现有固定 source ref、binding ref 或事件值来迁就公式；
- 不创建 measurement-adapter 正式合同；
- 不创建 T10 capability 正式合同；
- 不更新项目地图或改变 B-03/H-03；
- 不使用父 EV builder 作为独立 validator 的算法来源；
- 不执行 WebShop runtime、Buy Now、网络、LLM、支付、钱包或订单副作用；
- 不安装依赖、不创建环境；
- 不 commit、不 push、不 rewrite history；
- 不 clean、reset、删除或回退继承工作区。

## Validation plan

| VP | Exact action | Expected |
|---|---|---|
| VP-01 | 解析权威设计公式 | prefix、payload、canonical JSON、hash、encoding 全部关闭 |
| VP-02 | 解析 9 个 registry entry | 均携带同一 `formula_id` 和完整机器参数 |
| VP-03 | 独立重算父固定 source refs | 全部与父 JSON 完全一致 |
| VP-04 | 独立重算 binding refs | 全部与父 JSON 完全一致 |
| VP-05 | 运行篡改矩阵 | 所有反例 fail closed / INVALID |
| VP-06 | T10/T12 回归 | 12 events / 11 bindings / relation resolution / sidecar decision 不变 |
| VP-07 | adapter/NEXT_SLICE audit | adapter 可独立实现，slice 仍未冻结 |
| VP-08 | protected scope/hash audit | 产品、runner、测试、样例和父证据全部不变 |
| VP-09 | workflow validator | `OK` |

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

## Stop conditions

- formula 仍只存在于 EV builder；
- registry 仍只有 mode + null template；
- 独立 checker 需要 import/read 父 builder；
- schema 未进入 identity hash payload；
- source type/prefix/encoding 未冻结；
- 新公式导致父固定 ref 或 binding ref 变化；
- T10/T12/Decimal/四类 ref 被无关重做；
- 需要修改产品、runner、测试或 fixture；
- 需要网络、新依赖或外部副作用。

## Amendments

None.

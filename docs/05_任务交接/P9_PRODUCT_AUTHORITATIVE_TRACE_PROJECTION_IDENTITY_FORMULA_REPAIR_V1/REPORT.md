# Executor Report

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-PROJECTION-IDENTITY-FORMULA-REPAIR-V1`  
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-REFERENCE-MODEL-GROUNDING-REPAIR-V1`  
Baseline HEAD: `979ffc505bec0b626858d0d186f655867b5491bf`  
Executor status: SUBMITTED_FOR_REVIEW

```yaml
workflow: evaluator-executor-workflow/v2.1
task_kind: repair
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-08-04-r5
active_bottleneck_id: B-03
hypothesis_id: H-03
parent_verdict: REJECTED
project_impact_verdict: NOT_APPLICABLE
state_preserved: EXECUTING
current_role_preserved: Executor
commit_performed: false
push_performed: false
network_call_performed: false
api_call_performed: false
data_download_performed: false
dependency_install_performed: false
environment_created: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_order_side_effect_performed: false
workflow_validator: OK
```

## 1. 执行结论

本轮只关闭父评估提出的一个规格缺口：把无 native ID 对象的 `source_object_ref` 算法从执行脚本里的隐含实现，提升为权威设计和机器 registry 都能直接读取的 `PROJECTION_HASH_IDENTITY_V1`。

```text
权威设计公式
→ 9 个 registry entry 使用同一 formula_id
→ 独立 checker 只读公式和固定 JSON
→ 重算 source_object_ref
→ 再独立重算 binding_ref
→ T10/T12 固定引用保持不变
```

没有重做四类引用、Decimal、T10、T12 或 projection allowlist，没有实现 measurement adapter、trace、runner 或产品 outcome。

当前基线保持：

```text
product-observed authoritative trace = 0/12 VALID
GESR = 0/12
new_business_rule_required = false
```

## 2. 父 Finding Closure

| Finding | 阻断问题 | 本轮关闭方式 | 执行者状态 |
|---|---|---|---|
| F-01 | 9 个 `PROJECTION_HASH_IDENTITY` registry entry 只有 mode 和空 template，独立 adapter 无法按权威输入重算 `source_object_ref` | 权威设计冻结 `PROJECTION_HASH_IDENTITY_V1`；结构化 coverage v4 为 9 个 entry 写入完整 prefix、payload、hash、encoding 和 canonical JSON 参数；独立 checker 不读取父 builder 完成重算 | CLOSED |

独立规格检查结果：`401/401 PASS`。

## 3. 权威公式

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

冻结边界：

1. `source_object_type` 只进入固定前缀，不进入 hash payload；
2. `projection_schema` 和 exact canonical `projection` 都进入 payload；
3. payload 不包含 `binding_ref` 或 `source_object_ref`；
4. digest 为 SHA-256 小写 64 hex；
5. prefix 大小写、冒号和 `projection-sha256` 字面值固定；
6. schema、projection、type 或 prefix 变化不能复用原 ref；
7. float、NaN、Infinity fail closed；
8. 该公式只证明 envelope 内部 identity 一致性，不证明外部真实性或签名身份。

`source_object_ref` identity hash 与 `binding_ref` full-binding digest 继续是两个独立公式。

## 4. 结构化 Registry

每个 hash identity entry 的 `source_identity` 现在包含：

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

9 个 schema：

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

新的完整 coverage registry：

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/
evidence/EV-01-coverage-projection-identity-formula.json
SHA-256 = 69b5c65eee924b011f606eb8284d0870971e40724f2fc62d59763cd18bcd703f
```

所有 `NATIVE_TEMPLATE` entry 与父 registry 完全相同。

## 5. 正例重算

结构化正反例：

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/
evidence/EV-01-projection-identity-vectors.json
SHA-256 = d8fbd0410f650c5efa36b9cae6ea81c38d4b997456c6c25a8e11c6279c2d1839
```

| Schema | 来源 | source ref | binding ref | 结果 |
|---|---|---|---|---|
| `governed-action-binding-fact-trace/v2` | 父固定 JSON | `GovernedActionBindingFact:projection-sha256:74603b9f...35aa34a` | `TraceSourceBinding:sha256:e781ad54...e615a4ab` | unchanged |
| `governed-payment-action-missing-id-trace/v2` | 由父 T10 Action 置空 action_id 的 conformance vector | `GovernedPaymentAction:projection-sha256:4f90ef70...54cef0e9` | `TraceSourceBinding:sha256:a26c70ab...29305f3d` | recomputed |
| `known-payment-attempt-preflight-fact-trace/v2` | 父固定 JSON | `KnownPaymentAttemptPreflightFact:projection-sha256:34014c67...273f59b` | `TraceSourceBinding:sha256:b345731c...8c9a014` | unchanged |
| `payment-recovery-result-trace/v2` | 当前真实 recovery dataclass/字段契约 conformance vector | `PaymentRecoveryResult:projection-sha256:ca29e5e2...bc2d415b` | `TraceSourceBinding:sha256:690dda29...150a4a1` | recomputed |
| `payment-status-conflict-fact-trace/v2` | 父固定 JSON | `PaymentStatusConflictFact:projection-sha256:c828d252...c9ffa715` | `TraceSourceBinding:sha256:445f5c4b...72f9e6b8` | unchanged |
| `runtime-gate-record-trace/v2` | 父固定 JSON | `RuntimeGateRecord:projection-sha256:6f97df6c...bd4a6ac` | `TraceSourceBinding:sha256:28e748ef...c88eee65` | unchanged |
| `validation-result-trace/v2` | 父固定 JSON | `ValidationResult:projection-sha256:38b16f4c...13299e83` | `TraceSourceBinding:sha256:d353007a...c3a74c53` | unchanged |
| `webshop-buy-now-gate-outcome-result-trace/v2` | 父固定 JSON | `WebShopBuyNowGateOutcome:projection-sha256:ff91f0eb...110ec92` | `TraceSourceBinding:sha256:9a917ff5...e3e66944` | unchanged |
| `webshop-payment-fulfilment-outcome-result-trace/v2` | 父固定 JSON | `WebShopPaymentFulfilmentOutcome:projection-sha256:aa14a6de...5af4dfa2` | `TraceSourceBinding:sha256:da9d97d4...12f0f6b3` | unchanged |

父任务持久化 JSON 中有 7 类具体 hash binding。另 2 类此前只有 registry schema，没有父固定 concrete ref；本轮为公式覆盖新增 conformance vector，但没有把它们冒充父固定值，也没有修改任何父证据。

## 6. 负例矩阵

| Case | Actual | Exact verdict |
|---|---|---|
| 删除 `projection_schema` | `FormulaInputError` | `FAIL_CLOSED` |
| payload 只有 projection | ref changed | `INVALID_REF_MISMATCH` |
| 修改 schema 字符串 | ref changed | `REF_CHANGED` |
| 修改 projection 字段 | ref changed | `REF_CHANGED` |
| 修改 source type 前缀 | prefix changed | `INVALID_OBJECT_IDENTITY_MISMATCH` |
| `Projection-SHA256` 大小写变化 | prefix changed | `INVALID_PREFIX_MISMATCH` |
| digest 大写 | uppercase digest | `INVALID_DIGEST_ENCODING_MISMATCH` |
| digest 为 63 hex | digest length 63 | `INVALID_DIGEST_FORMAT_MISMATCH` |
| float | `FormulaInputError` | `FAIL_CLOSED` |
| NaN | `FormulaInputError` | `FAIL_CLOSED` |
| Infinity | `FormulaInputError` | `FAIL_CLOSED` |
| payload 加入 `source_object_ref` | payload fields changed | `INVALID_PAYLOAD_SCHEMA_MISMATCH` |
| 父 EV builder 作为 resolver | not read or imported | `FORBIDDEN_RESOLVER` |

## 7. T10 / T12 固定值回归

T10：

```text
12 events = unchanged
11 unique bindings = unchanged
两个 Order event 共享 binding = unchanged
全部 relation resolved = unchanged
11/11 source_object_ref = unchanged
11/11 binding_ref = unchanged
```

T12：

```text
PaymentStatusConflictFact source/binding refs = unchanged
WebShopPaymentFulfilmentOutcome source/binding refs = unchanged
sidecar decision extraction = null
```

父固定 JSON 哈希：

```text
EV-01-coverage-reference-grounding.json
= 3d9904094556680137eb296e016a9abc573534d0f2c13060c0a288292f79d4fa

EV-01-reference-examples.json
= 7975b44690d6712d9188bc1e39f0c70449e3082c7815f2f5d250540420fdcfb4

EV-01-t10-grounded-instance.json
= c6e87f42a7a7a6074bb83d76d457d5519609c68b9a48a7e836f18a680f2d056d

EV-01-t12-sidecar-examples.json
= bb9f88a4271391216ee2369d824c45a75d1c28f609503fdf93446515555a309f
```

构建前后完全相同。

## 8. 独立 Checker 输入边界

`EV-02-independent-formula-check.py` 只读取：

```text
权威设计文档
新 coverage registry / vectors JSON
父固定 coverage / ref / T10 / T12 JSON
当前 src 下真实 Python 类型，仅做 class/field 边界确认
Measurement Adapter Freeze
NEXT_SLICE 条件文档
```

检查器通过统一 allowlist 读取项目文件，并打印全部 56 个实际输入路径。

```text
forbidden_parent_builder_read = false
forbidden_parent_builder_imported = false
checks = 401/401 PASS
```

未读取或导入：

```text
EV-01-build-grounded-reference-model.py
```

## 9. Measurement Adapter 与 NEXT_SLICE

`MEASUREMENT_ADAPTER.md` 已增加 object identity 两条路径：

```text
NATIVE_TEMPLATE
PROJECTION_HASH_IDENTITY_V1
```

并明确：

- adapter 只读 envelope 和内置冻结 registry；
- 不读 EV builder、fixture、GateContext、产品原对象或 evaluator replay；
- prefix、payload、digest、encoding、canonicalization 任一不匹配都不能 `VALID`；
- object identity 与 binding digest 分层核验。

`NEXT_SLICE.md` 无需修改，已核验继续保持：

```text
State = CONDITIONAL_NOT_FROZEN
prerequisite = measurement adapter accepted
runner/before/target/non-trace hashes = TBD_AFTER_ADAPTER_ACCEPTANCE
T10 = 12 events / 11 unique bindings
```

没有创建 measurement-adapter 或 T10 capability 正式合同。

## Impact comparison / 影响对比

Measurement evidence: `EV-01`、`EV-02`、`EV-03`、`EV-04`、`EV-05`。

Before:

```text
9 个 hash identity registry entry 只有 mode + template:null
公式只隐含在父 EV builder
adapter 无法只读权威规格重算 source_object_ref
```

After:

```text
权威设计冻结 PROJECTION_HASH_IDENTITY_V1
9 个 registry entry 携带完整机器参数
独立 checker 不读父 builder 即可重算 source ref 和 binding ref
T10/T12 固定值不变
```

Delta:

```text
blocking formula specification gaps: 1 → 0（执行者独立检查）
product-observed trace: 0/12 → 0/12
GESR: 0/12 → 0/12
```

Guardrail result: `src/`、`tests/`、`scripts/`、`samples/` 保持不变；父固定 JSON 哈希不变；无后续正式合同；无网络、支付或其他外部副作用。

Scope caveat: 本任务是设计 repair，只证明公式和 registry 具备再次独立评估条件，不证明 measurement adapter 或产品轨迹能力已经实现。

项目影响：

```text
NOT_APPLICABLE
```

## Workspace snapshot / 工作区快照

| 项目 | 结果 |
|---|---|
| Baseline HEAD | `979ffc505bec0b626858d0d186f655867b5491bf` |
| Final HEAD | `979ffc505bec0b626858d0d186f655867b5491bf` |
| Router | `EXECUTING / Executor` |
| Product trace / GESR | `0/12 / 0/12` |
| Commit / push | `false / false` |
| Protected scope | 45/45 PASS; 130 protected files unchanged; 162 parent files unchanged |
| Workflow validator | EV-05 / EV-06 PASS |

完整最终状态、diff 和 SHA-256 见 `EV-04`。

## Changed files / 改动文件

| 文件 | 用途 |
|---|---|
| `CURRENT.md` | `CONTRACT_FROZEN → EXECUTING`；role 保持 Executor |
| `docs/03_架构设计/产品权威轨迹最小合同_v1.md` | 新增权威 `PROJECTION_HASH_IDENTITY_V1` 公式 |
| `docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md` | 指向 coverage v4，列出 9 个公式 entry |
| 父 `MEASUREMENT_ADAPTER.md` | 同步 native/hash identity 两条校验路径 |
| 当前任务 `REPORT.md` | 本报告 |
| 当前任务 `evidence/EV-*`、`*.json` | registry、正反例、独立检查、范围、快照、workflow |

`NEXT_SLICE.md` 仅核验，未修改。

## AC mapping / 验收映射

| AC | 执行结果 | 证据 |
|---|---|---|
| AC-01 | 权威设计冻结唯一公式、payload、prefix、hash、encoding 和边界语义 | 设计文档；EV-01、EV-02 |
| AC-02 | 9 个 registry entry 使用同一 formula_id 和完整参数；native identity 不变 | coverage v4；EV-01、EV-02 |
| AC-03 | 7 类父持久化 fixed refs/binding refs、T10/T12 全固定 refs 独立重算不变；2 类补 conformance vector | vectors JSON；EV-01、EV-02 |
| AC-04 | 13 个 schema/projection/type/prefix/digest/canonicalization/resolver 反例具有 exact verdict | vectors JSON；EV-01、EV-02 |
| AC-05 | Measurement Adapter 区分 native/hash，禁止隐藏 resolver，identity/binding 分层 | `MEASUREMENT_ADAPTER.md`；EV-02 |
| AC-06 | NEXT_SLICE 条件状态、TBD hashes、12/11 均保持，未创建正式合同 | NEXT_SLICE；EV-01、EV-02、EV-03 |
| AC-07 | 独立 checker 只读 allowlist 输入，父 builder read/import 均为 false，401/401 | EV-02 |
| AC-08 | F-01、公式、9 schema、正反例、固定值、差异、范围和限制均记录 | 本报告；EV-01—EV-05 |
| AC-09 | 产品/runner/父证据/路由/授权范围证据 | EV-03—EV-05 |

## Deviations and unresolved items / 偏差与未解决项

1. 父固定 JSON 只持久化了 7 类 hash identity concrete binding；另外 2 类此前只有 registry schema。本轮为它们生成 conformance vector，并明确标记 `parent_fixed=false`，没有宣称或修改不存在的父固定 ref。
2. 未运行 WebShop runtime、Buy Now、真实支付、网络、LLM 或外部 side effect。
3. 未执行产品测试和项目 baseline runner；本轮只做设计生成、固定 JSON 重算、AST 类型边界检查和 Git 范围检查。
4. 未修改父任务 EV/RV-EV/REPORT/REVIEW；父 4 个固定 JSON 的哈希在构建前后相同。
5. 当前产品轨迹仍为 `0/12 VALID`，这是合同要求保持的基线。
6. 未 commit、push、download、install、create environment 或 rewrite history。
7. Executor 提交时 `CURRENT.md` 保持 `EXECUTING / Executor`；只有 Evaluator 可接受并重新路由。

## EV-01 — Build authoritative formula registry

- AC: AC-01, AC-02, AC-03, AC-04, AC-05, AC-06
- Result: PASS — 9 schemas，13 negative cases，T10/T12 fixed values unchanged
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-01.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-01.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-01.stderr.log`

## EV-02 — Independent formula sufficiency check

- AC: AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07
- Result: PASS — 401/401; parent builder read/import false
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-02.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-02.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-02.stderr.log`

## EV-03 — Protected scope and parent evidence audit

- AC: AC-06, AC-09
- Result: PASS — 45/45; 130 protected files unchanged; 162 parent files unchanged after task start
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-03.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-03.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-03.stderr.log`

## EV-04 — Final workspace, diff and hashes

- AC: AC-08, AC-09
- Result: PASS — final status, complete tracked diff, artifact hashes, protected diff 0, diff check PASS
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-04.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-04.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-04.stderr.log`

## EV-05 — Workflow validator

- AC: AC-08, AC-09
- Result: PASS — OK: v2.1 routing and required artifacts are structurally valid
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-05.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-05.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-05.stderr.log`


## EV-06 — Final workflow validator

- AC: AC-08, AC-09
- Result: PASS — final post-report v2.1 structural validation
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-06.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-06.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-06.stderr.log`

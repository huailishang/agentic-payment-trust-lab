# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-SOURCE-BINDING-CONTRACT-REPAIR-V1`  
Task name: 产品权威轨迹 source binding 与 T10 profile 一致性修复 v1  
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
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-MINIMUM-CONTRACT-REPAIR-V1`  
Parent verdict: `REJECTED / NOT_APPLICABLE`

B-03 仍是第一瓶颈，H-03 未被否定。父修复已经解决大部分角色、稳定 ref 公式和阶段归因问题，但仍缺少可由 runner 独立校验的 source binding，并存在 T10 角色/事件不一致。

本任务只修设计合同和结构化映射，不实现 trace 类型、validator、runner 或产品 outcome。

## Single objective

冻结一套自包含、最小披露、可由 runner 只读取 `outcome.authoritative_trace` 就独立验证的 source-binding 合同，并把 T10 profile 的角色、事件、entity、source object 和字段路径收敛为唯一无歧义映射。

完成后路线必须成立：

```text
产品 trace
→ 自带最小 source bindings
→ runner 不读取隐藏调用参数
→ 可重算 source_object_ref
→ 可核对事件值来自哪个 source projection 路径
→ T10 profile 角色和事件完全一致
→ 才允许冻结 measurement-adapter 实现任务
```

## Rejected findings to repair

必须逐条关闭父 REVIEW 中：

- F-06：`source_object_ref` 没有 projection/registry/resolver，runner 无法独立重算；
- F-07A：T10 声明 `AUTHORIZED_ORDER_SNAPSHOT`，事件序列却没有该事件；
- F-07B：T10 `ACTION_RECORDED [GOVERNED_ACTION / CURRENT_PAYMENT_CANDIDATE]` 用斜杠混写，entity/source-object 映射未冻结。

## Acceptance criteria

### AC-01 — 冻结自包含 Source Binding 合同

修订：

```text
docs/03_架构设计/产品权威轨迹最小合同_v1.md
```

`ProductAuthoritativeTrace` 必须增加关闭字段：

```text
source_bindings: tuple[TraceSourceBinding, ...]
```

`TraceSourceBinding` 至少冻结：

```text
source_object_type: closed type name
source_object_ref: stable ref
projection_schema: closed schema name
projection: primitive-only exact allowlist object
```

规则必须明确：

1. 每个 `ProductTraceEvent.source_object_ref` 恰好解析到一个 source binding；
2. 同一 ref 重复出现时 binding 必须字节级 canonical 一致，否则 `INVALID`；
3. 未被事件引用的 binding 不得存在；
4. 事件引用缺失 binding 时 `INDETERMINATE`；
5. 不允许 evaluator replay、runner 临时构造或隐藏参数补 source binding；
6. runner 只依赖 trace envelope 即可完成结构与 source 验证。

不得只增加一个无法验证的 `source_registry_ref` 字符串。

### AC-02 — 冻结 ref 重算与值核对规则

每个 `projection_schema` 必须冻结一种 ref 模式：

```text
NATIVE_REF
HASH_REF
```

`NATIVE_REF` 必须冻结：

- native ID 字段路径；
- optional version 字段路径；
- `<type>:<native-id>[:<version>]` 生成规则；
- ID/version 缺失或类型错误的 fail-closed 结果。

`HASH_REF` 必须冻结：

- exact allowlist fields；
- `projection_schema + projection` canonical hash；
- Enum/datetime/tuple 转换；
- RESULT projection 排除 `authoritative_trace`；
- hash 不一致为 `INVALID`。

事件值核对不能只验证 ref。profile mapping 必须冻结可选路径：

```text
decision_path
status_path
reason_codes_path
entity_ref_path
relation_ref_paths
```

路径不存在或值不一致必须 fail closed，不得重跑业务规则。

### AC-03 — 最小披露与精确投影

source binding 不是完整对象 dump。必须冻结：

- 每个 projection schema 的 exact field allowlist；
- 未声明字段处理规则；
- primitive-only；
- 去除重复 binding；
- 不携带支付工具、卡号、钱包密钥、credential、token、cookie、原始页面文本、原始 prompt、任意用户输入全文；
- 不携带当前时间、内存地址、文件路径、随机值；
- 只保留生成 ref、核对事件值和关系所需字段。

至少为 T10 所需对象冻结最小 projection schema：

```text
IntentMandate
Order authorized snapshot
Order current snapshot
TransactionRequest
GovernedPaymentAction
GovernedActionBindingFact
PaymentExecutionRecord current candidate
PaymentExecutionRecord historical succeeded
KnownPaymentAttemptPreflightFact
ValidationResult duplicate decision
RuntimeGateRecord
WebShopBuyNowGateOutcome excluding authoritative_trace
```

必须给出结构化样例和字段数量/字段清单，证明不是任意全对象泄露。

### AC-04 — 冻结 T10 事件—实体—源对象映射矩阵

设计和结构化证据必须给出 T10 profile 的 exact matrix。每行至少包含：

```text
sequence_no
event_type
entity_type
entity_role
entity_ref derivation
source_object_type
projection_schema
decision/status/reason paths
relations
```

不得使用：

```text
GOVERNED_ACTION / CURRENT_PAYMENT_CANDIDATE
```

这种斜杠混写。

本任务冻结以下关闭序列：

```text
1  AUTHORITY_RECORDED [AUTHORITY]
2  ORDER_RECORDED [AUTHORIZED_ORDER_SNAPSHOT]
3  ORDER_RECORDED [CURRENT_ORDER_SNAPSHOT]
4  REQUEST_RECORDED [CURRENT_REQUEST]
5  ACTION_RECORDED [GOVERNED_ACTION]
6  PAYMENT_CANDIDATE_RECORDED [CURRENT_PAYMENT_CANDIDATE]
7  ACTION_BINDING_DECISION_RECORDED [ACTION_BINDING_FACT]
8  PAYMENT_OUTCOME_RECORDED [HISTORICAL_SUCCEEDED_PAYMENT]
9  KNOWN_PAYMENT_PREFLIGHT_RECORDED [KNOWN_PAYMENT_PREFLIGHT_FACT]
10 PREPAYMENT_DECISION_RECORDED [PREPAYMENT_VALIDATION]
11 RUNTIME_DECISION_RECORDED [RUNTIME_GATE_OBSERVATION]
12 RESULT_RECORDED [FINAL_OUTCOME]
```

要求：

- 新增 `PAYMENT_CANDIDATE_RECORDED` 到关闭 taxonomy；
- ACTION 实体明确是 `GovernedPaymentAction / GOVERNED_ACTION`；
- 当前付款候选实体明确是 `PaymentExecutionRecord / CURRENT_PAYMENT_CANDIDATE`；
- 当前候选 ref = action.payment_ref = execution_candidate.payment_id；
- 历史成功付款 ref 属于 preflight related refs；
- 授权/当前订单可引用同一原生 Order ref，但角色必须分别出现；
- 每个声明角色恰好有对应事件，不多不少。

### AC-05 — 修正 T01—T12 覆盖结构

更新：

```text
docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md
```

并生成新的结构化 coverage JSON。要求：

- T01—T12 恰好 12 项；
- 每项 `entity_roles` 与事件序列实际角色集合一致；
- 不允许声明未出现的角色；
- 每个事件都有 source object type、projection schema 和核对路径；
- ref strategy 不再只写一句通用文字；
- T10 使用 AC-04 的 exact 12 事件；
- 当前状态仍为 `0/12 VALID`；
- `new_business_rule_required=false`；
- 输出 SHA-256；
- 提供机器校验，检查角色集合、事件顺序、source binding 和 path 完整性。

### AC-06 — 修订 Measurement Adapter Freeze

更新：

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/
MEASUREMENT_ADAPTER.md
```

必须增加：

- runner 只读取 trace envelope 和 envelope 内 source bindings；
- 不接收隐藏 `GateContext`、mandate/order/action/execution 参数作为 source resolver；
- strict validator 覆盖：missing binding、duplicate conflicting binding、native ref mismatch、hash mismatch、extra projection field、missing value path、event/source value mismatch、unreferenced binding、RESULT cycle、no fallback；
- 产品仍不产出 trace，0/12 BEFORE 不变；
- measurement-adapter 正式任务仍不得在本任务中创建或冻结。

### AC-07 — 修订条件 T10 Slice

更新父任务：

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/
NEXT_SLICE.md
```

要求：

- 保持 `CONDITIONAL_NOT_FROZEN`；
- 保持 measurement adapter accepted 前置条件；
- 使用 AC-04 exact 12 事件；
- 明确 source bindings 是 T10 product variable 的组成部分；
- 明确只输出最小 projection，不暴露完整敏感对象；
- runner/before/target/non-trace hashes 继续为 `TBD_AFTER_ADAPTER_ACCEPTANCE`；
- 不创建 T10 capability `CONTRACT.md`。

### AC-08 — 结构化证明与父 Findings Closure

REPORT 必须包含：

- F-06、F-07A、F-07B 逐条 closure；
- source binding schema；
- NATIVE_REF / HASH_REF 重算样例；
- RESULT 排除 trace 的循环关闭样例；
- T10 exact matrix；
- 角色集合与事件集合一致性证明；
- projection allowlist / 禁止字段证明；
- 12 项 coverage JSON 和 SHA-256；
- 修改前后差异；
- changed files、完整 diff 和 hashes；
- 初始/最终 git status；
- 未运行项、授权和限制；
- workflow validator `OK`。

项目影响必须为 `NOT_APPLICABLE`。

### AC-09 — 范围与工作流

必须证明：

- `src/`、`tests/`、`scripts/`、`samples/` 全部不变；
- 当前 `src/` 仍没有产品 `authoritative_trace` producer；
- 未创建 measurement-adapter 或 T10 capability contract；
- CURRENT 在 Executor 提交时仍保持 `EXECUTING / Executor`；
- evidence 使用 `EV-*` triplet；
- workflow validator 通过。

## Required outputs

必须新增或更新：

1. `docs/03_架构设计/产品权威轨迹最小合同_v1.md`
2. `docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md`
3. `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md`
4. `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md`
5. 本任务 `REPORT.md` 和 `evidence/EV-*`

## Allowed scope

May add or modify only:

- `docs/03_架构设计/产品权威轨迹最小合同_v1.md`
- `docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_SOURCE_BINDING_CONTRACT_REPAIR_V1/REPORT.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_SOURCE_BINDING_CONTRACT_REPAIR_V1/evidence/EV-*`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_SOURCE_BINDING_CONTRACT_REPAIR_V1/evidence/*.json`
- `CURRENT.md`（仅原子路由）

允许只读审计产品 outcome、runner、测试、fixture 和父任务证据。

当前工作区继承 Evaluator 新增的父 `REVIEW.md` 与 `RV-EV-*` 证据，不得清理或修改这些已完成评估记录。

## Exclusions

- 不修改 `src/`、`tests/`、`scripts/`、`samples/`；
- 不实现 `ProductAuthoritativeTrace`、`TraceSourceBinding`、validator；
- 不修改 runner；
- 不让任何 product outcome 产出 trace；
- 不创建 measurement-adapter 正式 `CONTRACT.md`；
- 不创建 T10 capability `CONTRACT.md`；
- 不更新项目地图或改变 B-03/H-03；
- 不把 evaluator replay 计入 product trace；
- 不引入外部 source resolver、数据库、文件索引或隐藏 context；
- 不把完整任意对象、敏感支付数据或原始页面/prompt 塞入 trace；
- 不执行真实 WebShop、Buy Now、网络、LLM、支付、钱包或订单副作用；
- 不安装依赖、不创建环境；
- 不 commit、不 push、不 rewrite history；
- 不 clean、reset 或回退继承工作区。

## Validation plan

| VP | Exact action | Expected |
|---|---|---|
| VP-01 | 静态解析 source binding schema | envelope 自包含 bindings，事件恰好解析一个 binding |
| VP-02 | 构造 NATIVE_REF / HASH_REF / RESULT 样例 | refs 可只依赖 binding 重算，RESULT 无循环 |
| VP-03 | 构造 missing/conflicting/extra-field/path-mismatch 反例 | 全部 fail closed |
| VP-04 | 解析 T10 exact matrix | 12 个事件、角色集合一致、无斜杠混写 |
| VP-05 | 校验 T01—T12 coverage JSON | 12/12、roles/events/source/path 完整 |
| VP-06 | 检查 projection allowlist | 无敏感字段、无任意完整对象 dump |
| VP-07 | 检查 MEASUREMENT_ADAPTER / NEXT_SLICE | source binding 前置、仍条件冻结、无双变量 |
| VP-08 | 受保护文件哈希与 scope audit | 产品/测试/runner/fixture 全部不变 |
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

- 仍要求 runner 重算 ref，却没有 trace 内 source binding；
- 仍依赖隐藏调用参数、evaluator replay 或临时 resolver；
- source binding 允许任意完整对象或敏感字段；
- T10 角色清单与事件序列仍不一致；
- ACTION 仍使用斜杠混写 entity/source；
- 未冻结 T10 exact event/entity/source/path matrix；
- coverage 声明未出现角色或缺少 source projection schema；
- 需要修改产品、测试、runner 或 fixture；
- 需要网络、新依赖或外部副作用。

## Amendments

None.

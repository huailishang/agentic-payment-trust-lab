# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-REFERENCE-MODEL-GROUNDING-REPAIR-V1`  
Task name: 产品权威轨迹引用模型与真实对象落地修复 v1  
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
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-SOURCE-BINDING-CONTRACT-REPAIR-V1`  
Parent verdict: `REJECTED / NOT_APPLICABLE`

B-03 仍是第一瓶颈，H-03 未被否定。父任务已形成完整 envelope、T10 12-event profile 和最小 projection 方向，但引用模型仍把对象身份、binding 完整性、entity 身份和 relation target 混在一起，并有 projection 与真实代码对象不一致的问题。

本任务继续只修设计、结构化 coverage 和后续冻结条件，不实现 trace、validator、runner 或产品 outcome。

## Single objective

冻结一套能够映射到当前真实代码对象、无引用歧义、可由 runner 只读取 trace envelope 就执行的 reference model，使以下链条在设计层成立：

```text
真实产品对象
→ exact projection
→ source object identity
→ binding digest
→ event entity identity
→ relation target identity
→ profile validator 可确定执行
```

完成后才允许另行冻结 measurement-adapter 实现任务。

## Parent findings to repair

必须逐条关闭父 REVIEW 中：

- F-01：T10 同一个 Order native ref 对应两个不同 binding；
- F-02：relation target ref 与目标 entity ref 不一致；
- F-03：Decimal canonicalization 缺失；
- F-04：相同重复 binding 的判定冲突；
- F-05：coverage 引用不存在的 `PaymentStatusConflictOutcome`；
- F-06：`WebShopPaymentFulfilmentOutcome` 不含声明的 `decision`；
- F-07：`entity_ref_path` 使用未定义的 `+` 表达式；
- F-08：NATIVE_REF 未承诺完整 projection。

## Acceptance criteria

### AC-01 — 分离四类引用

修订：

```text
docs/03_架构设计/产品权威轨迹最小合同_v1.md
```

必须冻结并明确区分：

```text
source_object_ref
→ 真实源对象身份；native object 可使用原生 ID/version

binding_ref
→ 对 exact projection 的完整性承诺

entity_ref
→ profile 内实体身份；与 entity_role 共同形成一致性键

relation.target_entity_ref
→ 必须等于目标事件最终 entity_ref
```

`TraceSourceBinding` 至少包含：

```text
binding_ref
source_object_type
source_object_ref
projection_schema
projection
```

`ProductTraceEvent` 必须通过：

```text
source_binding_ref
```

解析 binding，不得再以 `source_object_ref` 作为唯一 binding lookup key。

`binding_ref` 对所有 binding 统一使用：

```text
TraceSourceBinding:sha256(
  canonical-json({
    source_object_type,
    source_object_ref,
    projection_schema,
    projection
  })
)
```

规则必须冻结：

1. 每个 event 的 `source_binding_ref` 恰好命中一个 binding；
2. `binding_ref` 重复，无论内容相同或冲突，均判 `INVALID`；
3. 同一个 binding 可被多个不同 role 的 event 引用；
4. 未引用 binding 判 `INVALID`；
5. 缺 binding 判 `INDETERMINATE`；
6. native `source_object_ref` 只证明对象身份，不再被描述为 projection 完整性证明；
7. 当前合同只证明产品输出内部一致性，不宣称签名、可信执行或外部密码学真实性。

### AC-02 — 冻结无歧义 entity ref 与 relation 模型

禁止继续使用：

```text
projection.a+projection.b
```

这种未定义表达式。

必须冻结关闭的 entity-ref template grammar，至少包含：

```text
IntentMandate:<mandate_id>
Order:<order_id>
TransactionRequest:<request_id>
GovernedPaymentAction:<action_id>
PaymentExecutionRecord:<payment_id>
<FactType>:binding:<binding-digest>
<OutcomeType>:binding:<binding-digest>
```

要求：

- `entity_ref_path` 只允许单字段 path，或改名为 `entity_ref_template`；
- 模板带类型和明确分隔符，不允许裸字符串拼接；
- `Order` 的 entity ref 固定为 `Order:<order_id>`，授权/当前快照通过不同 `entity_role` 区分，version 留在 source binding；
- relation target 必须使用目标 role 的 exact entity ref；
- 每条 relation 必须冻结 `target_entity_type`、`target_entity_role`、`target_entity_ref_template` 和 source assertion path；
- source 只有 order_id 时仍可生成 `Order:<order_id>`，不得要求不存在的 order_version；
- validator 必须检查 relation target event 存在、type/role/ref 完全一致。

必须提供碰撞反例，证明旧 `ab+c` / `a+bc` 不能在新模板下碰撞。

### AC-03 — 冻结完整 canonical primitive 规则

canonical contract 必须覆盖：

```text
null
bool
int
str
Decimal
Enum
datetime
tuple / list
dict
```

Decimal 必须冻结为不经过 float 的规范十进制字符串：

- 只接受 finite Decimal；
- 使用固定小数表示，不使用指数；
- 去除无意义尾零和小数点；
- `-0` 规范为 `0`；
- `1.0`、`1.00`、`Decimal('1')` canonical 后一致；
- NaN、Infinity、float 输入 fail closed。

必须增加固定样例：

```text
0
-0
1
1.00
0.10
1000.000
```

并独立重算至少一个 Order、Request、Payment、HASH fact 和 RESULT binding ref。

### AC-04 — 所有 projection 与真实代码对象闭合

结构化 registry 必须为每个 schema 增加：

```text
source_module
source_class
field_extractions
```

每个 projection field 必须满足其一：

1. 真实 dataclass 直接字段；
2. 明确关闭的嵌套 extraction path；
3. 明确关闭的 enum/code/path primitive 转换。

不得出现：

- 不存在的 source class；
- 不存在的字段；
- 从未声明的另一个对象补值；
- 隐藏 GateContext/evaluator replay；
- 自由文本或 arbitrary object dump。

必须修正：

```text
PaymentStatusConflictOutcome
→ PaymentStatusConflictFact
```

并使用真实字段：

```text
resolution
effective_status
reason_codes
```

`WebShopPaymentFulfilmentOutcome` projection 不得再直接声明不存在的 `decision`。若 profile 的最终 decision 来自 `WebShopBuyNowGateOutcome` / `RuntimeGateRecord`，必须由对应事件承担；sidecar RESULT 只读取其真实字段或明确嵌套路径。

必须提供机器校验：

- registry `source_class` 在 `src/` 中存在；
- direct field 在 dataclass 中存在；
- nested extraction 根字段存在；
- 所有 T01—T12 event schema 都通过该检查。

### AC-05 — 修复 T10 的真实引用闭环

T10 保持 exact 12-event sequence，不改变事件数量和角色。

必须冻结以下真实行为：

```text
T10 authorized order == current order
```

因此：

- 两个 ORDER event 可引用同一个 `source_binding_ref`；
- `AUTHORIZED_ORDER_SNAPSHOT` 与 `CURRENT_ORDER_SNAPSHOT` 仍是两个 event/role；
- 两个 event 的 entity ref 都可为 `Order:<order_id>`，一致性键由 `(entity_type, entity_role)` 区分；
- 不能为同一实际 Order 人为制造两个不同 projection schema/binding；
- Request、Action、当前 Payment、历史 Payment 到 Order 的 relation 均应解析为 `Order:<order_id>`；
- Action 到当前 Payment 应解析为 `PaymentExecutionRecord:<payment_id>`；
- 当前候选 Payment 与历史成功 Payment 必须保持不同 role，可使用不同 payment_id；
- preflight related refs 必须命中历史成功 Payment entity ref。

必须生成一个基于当前固定 T10 对象关系的结构化实例，机器验证：

```text
12 events
11 或 12 个 unique bindings（两个 Order event 共享 binding 时为 11）
所有 event binding 可解析
所有 relation target 可解析
所有 entity ref template 可执行
无隐藏 resolver
```

不得执行 WebShop runtime、Buy Now 或任何 side effect。

### AC-06 — 重建 T01—T12 coverage grounding

更新：

```text
docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md
```

并重新生成结构化 coverage JSON。要求：

- T01—T12 恰好 12 项；
- 所有 source class/module/field extraction 与当前代码闭合；
- 所有 binding_ref、source_object_ref、entity_ref 和 relation target 语义分开；
- 每个 relation 的 target role/type/ref 可解析；
- 不再有裸 `+` expression；
- T12 使用 `PaymentStatusConflictFact`；
- sidecar RESULT 不读取不存在的 decision；
- T10 共享 Order binding 反例通过；
- 当前仍为 `0/12 VALID`；
- `new_business_rule_required=false`；
- 生成新的 SHA-256；
- 机器校验不仅检查字段存在，还检查 ref/template/relation 实际解析相等。

### AC-07 — 统一修订后续冻结文档

更新：

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/
MEASUREMENT_ADAPTER.md

docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/
NEXT_SLICE.md
```

要求：

- measurement adapter 唯一 resolver 仍是 envelope；
- event 通过 `source_binding_ref` 解析 binding；
- duplicate binding_ref 统一判 `INVALID`；
- validator 分别核验 object identity、binding digest、entity template、relation target；
- Decimal 反例加入 strict matrix；
- source class/field extraction 不闭合时 fail closed；
- NEXT_SLICE 仍为 `CONDITIONAL_NOT_FROZEN`；
- runner/before/target/non-trace hashes 仍为 `TBD_AFTER_ADAPTER_ACCEPTANCE`；
- 不创建 measurement-adapter 或 T10 capability `CONTRACT.md`。

### AC-08 — 独立可执行性证明

REPORT 必须逐条关闭 F-01—F-08，并提供：

- 四类 ref 对比表；
- 新 binding schema；
- canonical Decimal 样例和固定 digest；
- duplicate binding exact verdict；
- source class/field grounding manifest；
- T10 共享 Order binding 实例；
- T10 全 relation resolution 输出；
- T12 `PaymentStatusConflictFact` 实例；
- sidecar RESULT extraction 证明；
- T01—T12 coverage JSON 与 SHA；
- changed files、完整 diff、hash、初始/最终 git status；
- 未运行项、授权和限制；
- workflow validator `OK`。

项目影响必须为 `NOT_APPLICABLE`。

### AC-09 — 范围与工作流

必须证明：

- `src/`、`tests/`、`scripts/`、`samples/` 全部不变；
- 当前产品仍没有 `authoritative_trace` producer；
- 产品轨迹和 GESR 仍为 0/12；
- 未创建 measurement-adapter 或 T10 capability contract；
- CURRENT 在 Executor 提交时保持 `EXECUTING / Executor`；
- evidence 使用 `EV-*` triplet；
- workflow validator 通过；
- 未 commit、push、network、API、download、install、create environment 或执行外部副作用。

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
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1/REPORT.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1/evidence/EV-*`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_REFERENCE_MODEL_GROUNDING_REPAIR_V1/evidence/*.json`
- `CURRENT.md`（仅原子路由）

允许只读审计 `src/`、`tests/`、`scripts/`、`samples/` 和父任务证据。

当前工作区继承父任务及 Evaluator 的未提交 REVIEW/RV-EV 证据，不得清理、覆盖或回退。

## Exclusions

- 不修改 `src/`、`tests/`、`scripts/`、`samples/`；
- 不实现 trace 类型、source binding、validator 或 runner；
- 不让任何产品 outcome 产出 trace；
- 不创建 measurement-adapter 正式合同；
- 不创建 T10 capability 正式合同；
- 不更新项目地图或改变 B-03/H-03；
- 不使用 evaluator replay、隐藏 GateContext 或外部 registry 补 source；
- 不新增业务判断；
- 不执行 WebShop runtime、Buy Now、网络、LLM、支付、钱包或订单副作用；
- 不安装依赖、不创建环境；
- 不 commit、不 push、不 rewrite history；
- 不 clean、reset 或删除继承工作区文件。

## Validation plan

| VP | Exact action | Expected |
|---|---|---|
| VP-01 | 解析 reference model | object/binding/entity/relation 四类 ref 明确分离 |
| VP-02 | 重算所有 binding digest | native 与 hash source 均由 binding_ref 承诺 exact projection |
| VP-03 | canonical Decimal 正反例 | 固定输出、无 float、非法值 fail closed |
| VP-04 | AST/dataclass grounding audit | 所有 source class 和 extraction path 真实存在 |
| VP-05 | T10 actual-shape instance | 共享 Order binding、12 events、全部 relation 可解析 |
| VP-06 | T01—T12 coverage parser | 12/12、无未知类型/字段/裸拼接/错误 RESULT source |
| VP-07 | MEASUREMENT_ADAPTER / NEXT_SLICE audit | 规则一致、仍未冻结后续实现 |
| VP-08 | protected scope/hash audit | 产品、runner、测试和样例全部不变 |
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

- event 仍以 `source_object_ref` 直接解析 binding；
- native ref 仍被描述为 projection 完整性证明；
- relation target 与目标 event entity ref 仍不能相等；
- 仍存在裸 `+` ref 表达式；
- Decimal 仍未冻结；
- 重复 binding 规则仍矛盾；
- registry 仍引用不存在类或字段；
- sidecar RESULT 仍读取不存在的 decision；
- T10 同一 Order 仍被人为制造为两个冲突 binding；
- 需要修改产品、runner、测试或 fixture；
- 需要网络、新依赖或外部副作用。

## Amendments

None.

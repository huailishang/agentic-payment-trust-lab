# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-MINIMUM-CONTRACT-REPAIR-V1`  
Task name: 产品权威轨迹最小合同设计修复 v1  
Task kind: `repair`  
Risk: `L0`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `71a3acbbd9622b68a8064381b9034e07c1f4d700`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-04-r5`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-MINIMUM-CONTRACT-V1`  
Parent verdict: `REJECTED / NOT_APPLICABLE`

B-03 仍是第一瓶颈，H-03 未被否定。父设计被打回的原因是合同不可直接执行，而不是产品发生回归。

本修复只修改设计合同、12 项覆盖映射和阶段冻结文件；不修改产品代码、测试、runner、fixture 或指标。

## Single objective

修正父设计中的五类阻断问题，使后续路线变为可执行、可归因的两阶段闭环：

```text
阶段 A：测量适配
→ runner 支持新 ProductAuthoritativeTrace envelope
→ 产品仍不产出 trace
→ 重新冻结可信 0/12 BEFORE 和新 runner hash

阶段 B：T10 单一 capability slice
→ 只让 T10 产品 outcome 产出 trace
→ 同一阶段 A runner 比较 BEFORE / AFTER
→ 其他业务投影完全不变
```

## Rejected findings to repair

必须逐条关闭父 REVIEW 中：

- F-01：新 envelope / 7 事件与冻结旧 runner 不兼容；
- F-02：T10 当前候选付款与历史成功付款缺少角色语义；
- F-03：无原生 ID 对象缺少稳定引用规则，RESULT 存在循环引用；
- F-04：T05/T06 缺少动作绑定决策事件；
- F-05：T02—T04 缺少授权/当前订单快照角色，T04 source mapping 不准确。

## Acceptance criteria

### AC-01 — 拆分测量适配与产品能力实验

必须新增：

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/
MEASUREMENT_ADAPTER.md
```

该文件必须冻结阶段 A：

```text
Task kind: evidence_fix 或 maintenance
主要变量：runner / trace validator 只读支持新 envelope
产品 outcome：保持不产出 authoritative_trace
预期基线：product trace 仍为 0/12 VALID
```

阶段 A 必须明确允许和禁止：

允许：

- 增加 ProductAuthoritativeTrace / Event 的纯数据合同和 validator；
- runner 读取 exact `authoritative_trace`；
- runner 严格校验 source/profile/events/refs；
- tests 验证 absent / invalid / no-fallback；
- 重新生成同 12 项测量结果和新 runner hash。

禁止：

- 任一产品 outcome 开始产出 trace；
- evaluator replay 被计入产品 trace；
- 修改业务决策、callback、状态或 binding；
- 宣称项目 `IMPROVED`。

### AC-02 — 阶段 B 不能冻结旧 runner

必须修订父任务 `NEXT_SLICE.md`：

- 当前 runner hash `a7d71...` 只能作为阶段 A 输入基线；
- T10 capability slice 的 runner hash 在阶段 A 独立复核通过后再冻结；
- 未获得阶段 A accepted runner hash 前，T10 capability contract 不得进入 `CONTRACT_FROZEN`；
- 阶段 B 的 BEFORE 必须由“新 runner + 旧产品行为”产生；
- 阶段 B 的 AFTER 必须由“同一新 runner + T10 产品变量”产生。

不得在一个任务里同时修改 runner 读取逻辑和 T10 产品产出逻辑。

### AC-03 — 增加关闭的对象角色语义

最小事件合同必须增加关闭字段，例如：

```text
entity_role
```

至少冻结以下角色：

```text
AUTHORIZED_ORDER_SNAPSHOT
CURRENT_ORDER_SNAPSHOT
CURRENT_PAYMENT_CANDIDATE
HISTORICAL_SUCCEEDED_PAYMENT
RUNTIME_GATE_OBSERVATION
FINAL_OUTCOME
ACTION_BINDING_FACT
```

一致性规则必须从“全链所有同类 ref 相同”改为：

```text
同一 (entity_type, entity_role) 的非空 ref 必须一致
```

同时允许同一 trace 合法包含多个有明确角色的同类实体。

### AC-04 — 冻结 T10 双 Payment 关系

T10 profile 必须明确：

```text
历史 PAYMENT_OUTCOME
role = HISTORICAL_SUCCEEDED_PAYMENT
payment_ref ∈ KnownPaymentAttemptPreflightFact.related_attempt_refs
request_ref = current request
status = SUCCEEDED

ACTION
role = CURRENT_PAYMENT_CANDIDATE
payment_ref = GovernedPaymentAction.payment_ref
payment_ref = current execution candidate.payment_id
request_ref = current request
```

历史 payment ref 与当前 candidate payment ref 允许不同，但二者 request ref 必须按现有事实关系闭合。

轨迹 validator 不得重新执行 payment binding，只验证上述 refs 是否与既有 fact 输出一致。

### AC-05 — 冻结无原生 ID 对象的稳定引用

设计必须冻结 exact 规则：

```text
native-ref object
→ <type>:<native-id>[:<version>]

no-native-id immutable object
→ <type>:sha256(canonical-json(projection))
```

至少定义：

- canonical JSON 排序、primitive-only、Enum/datetime/tuple 转换；
- projection schema version；
- RuntimeGateRecord 使用 `to_dict()` 投影；
- ValidationResult / BindingFact 使用 primitive projection；
- RESULT 使用 outcome projection，但排除 `authoritative_trace`；
- 不包含当前时间、内存地址、随机值或文件路径；
- hash 输入和排除字段必须进入文档和结构化样例。

必须明确解决 RESULT 循环引用。

### AC-06 — 修正 taxonomy 和最终决策来源

事件 taxonomy 至少增加：

```text
ACTION_BINDING_DECISION_RECORDED
```

T05/T06 profile 必须记录：

```text
PREPAYMENT_DECISION_RECORDED = ALLOW
ACTION_BINDING_DECISION_RECORDED = DENY / INDETERMINATE
RESULT_RECORDED = final outcome
```

来源必须是现有 `GovernedActionBindingFact`，不得根据最终 decision 反推或重新运行 binding。

所有 12 项映射必须满足：

- 最终 decision 至少有一个真实产品决策事件直接解释；
- 不能只记录中间 ALLOW，却把最终 DENY 留给 RESULT 文本解释。

### AC-07 — 修正 T02—T04 双订单快照

T02—T04 必须记录两个订单快照，采用以下任一关闭方案：

```text
两个 ORDER_RECORDED
+ entity_role = AUTHORIZED_ORDER_SNAPSHOT / CURRENT_ORDER_SNAPSHOT
+ order_id + order_version
```

或两个明确关闭事件类型。

T04 覆盖映射必须删除不存在的 `OrderDifference` source object，改为真实存在的：

- authorized/current Order；
- ValidationResult；
- ValidationResult.evidence；
- confirmation/order binding evidence。

结构化覆盖 JSON 必须与实际对象输出一致。

### AC-08 — 修正 12 项映射和 profiles

更新：

```text
docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md
```

要求：

- T01—T12 恰好 12 行，无重复、无遗漏；
- 每项列出真实入口、outcome、source objects、entity roles、决策来源、事件顺序、缺失事件和插入点；
- 每项最终 decision source 正确；
- 每项无原生 ID 对象的 ref strategy 明确；
- 当前状态仍为 `0/12 VALID`；
- `new_business_rule_required=false` 只有在不新增业务判断时才能填写；
- 生成新的结构化 coverage JSON，并保存 SHA-256。

### AC-09 — 修订 NEXT_SLICE 为条件冻结

更新父任务：

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/
NEXT_SLICE.md
```

必须包含：

```text
prerequisite = measurement adapter accepted
runner hash = TBD_AFTER_ADAPTER_ACCEPTANCE
before hash = TBD_AFTER_ADAPTER_ACCEPTANCE
state = CONDITIONAL_NOT_FROZEN
```

T10 事件序列必须使用修正后的 entity roles 和 stable refs。

不得创建或冻结 T10 capability `CONTRACT.md`。

### AC-10 — 范围、证据与工作流

REPORT 必须包含：

- 父 REVIEW F-01—F-05 逐条 closure；
- 修改前后设计差异；
- runner/envelope 两阶段图；
- stable-ref 结构化样例；
- T10 双 Payment 结构化样例；
- T05/T06 和 T02—T04 修正映射；
- 12 项结构化 coverage；
- changed files、完整 diff 和哈希；
- 初始/最终 git status；
- 未运行项、授权和限制；
- workflow validator `OK`。

项目影响必须为 `NOT_APPLICABLE`。

## Required outputs

必须新增或更新：

1. `docs/03_架构设计/产品权威轨迹最小合同_v1.md`
2. `docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md`
3. `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md`
4. `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md`
5. repair `REPORT.md` 和 `evidence/EV-*`

## Allowed scope

May add or modify only:

- `docs/03_架构设计/产品权威轨迹最小合同_v1.md`
- `docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/REPORT.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-*`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/*.json`
- `CURRENT.md`（仅原子路由）

允许只读审计产品、测试、runner、fixture 和父任务证据。

## Exclusions

- 不修改 `src/`、`tests/`、`scripts/`、`samples/`；
- 不实现 ProductAuthoritativeTrace 类型或 validator；
- 不修改 runner；
- 不让任何 product outcome 产出 trace；
- 不创建 T10 capability contract；
- 不更新项目地图或改变 B-03/H-03；
- 不把 evaluator replay 计入 product trace；
- 不执行真实 WebShop、Buy Now、网络、LLM、支付、钱包或订单副作用；
- 不安装依赖、不创建环境；
- 不 commit、不 push、不 rewrite history；
- 不 clean、reset 或回退继承工作区。

## Validation plan

| VP | Exact action | Expected |
|---|---|---|
| VP-01 | 静态读取 frozen runner 和 ReplayEventType | 明确旧 runner 不能验新 envelope，阶段拆分成立 |
| VP-02 | 构造 T10 当前 candidate + historical success 对象图 | 双 Payment roles 和关系闭合 |
| VP-03 | 构造 RuntimeGateRecord / outcome stable-ref 样例 | canonical projection 无循环、确定性 |
| VP-04 | 执行 T05/T06 只读对象审计 | action binding decision 映射最终结果 |
| VP-05 | 执行 T02—T04 只读快照审计 | 两快照 roles/version 和真实 evidence 映射正确 |
| VP-06 | 校验 T01—T12 coverage JSON | 12/12、最终决策来源和角色完整 |
| VP-07 | 检查 MEASUREMENT_ADAPTER / NEXT_SLICE | 两阶段、条件冻结、无双变量 |
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

- 仍要求旧 runner 直接验证新 envelope；
- 仍在同一 capability experiment 修改 runner 和产品；
- T10 仍没有双 Payment role；
- RESULT 或 RuntimeGateRecord 稳定 ref 仍未冻结；
- T05/T06 最终决策仍无对应事件；
- T02—T04 仍只记录一个无角色订单快照；
- coverage 声明不存在的 source object；
- 需要修改产品、测试、runner 或 fixture；
- 需要网络、新依赖或外部副作用。

## Amendments

None.

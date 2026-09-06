# Frozen Task Contract

Task ID: `P9-AUTONOMOUS-WEBSHOP-ACTION-ORIGIN-RESPONSIBILITY-TRACE-V1`  
Task name: Autonomous WebShop Action Origin / Responsibility Trace minimal slice  
Task kind: `capability_experiment`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `57ded7bb2fb0ca830748b35b857a8d07624fe3d4`  
Validation plan file: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_ACTION_ORIGIN_RESPONSIBILITY_TRACE_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-06-r25`  
Active bottleneck: `B-11`  
Hypothesis: `H-13`  
Dispatch: `SINGLE`

Metric baseline: machine-readable Action Origin closed types `0/5`; autonomous behavior action-origin records `0`; T01 authoritative-trace action-origin records `0`.  
Estimated affected scope: all currently accepted autonomous WebShop action evidence and representative payment authoritative-trace events that need responsibility attribution; first slice is intentionally limited to frozen fixtures and does not claim full-project or full-schema coverage.  
Expected project impact: establish a deterministic five-value Action Origin evidence layer so User Authority / Agent Decision / Runtime Decision / External Fact / Execution Result can be mechanically distinguished and evidence-linked without changing business behavior.  
Rollback condition: any need to change shopping policy, payment/runtime decisions, global authoritative-trace schema, fabricate same-journey correlation, introduce a second principal change, alter protected hashes, or trigger network/side effects.

B-04 Autonomous Agent Behavior（自主 Agent 行为）已经完成阶段性验证：项目已经有真实多步骤 Agent 行为、开发集/盲测/系统性发现证据，也已经证明意图与规格理解存在难以穷举的长尾。继续把这些长尾逐条修完，不再是支付信任项目当前最高收益方向。

H-15 已在 Executor 开始前被主线路由替代，保留为 Known Limitation / Regression Asset（已知限制 / 回归资产），不再阻塞 H-13。

当前主线恢复为：

```text
Autonomous Agent Behavior（阶段性验证完成）
→ Action Origin / Responsibility Trace（当前）
→ Governed Payment Action
→ Payment / Finality / Fulfillment / Recovery
→ Evidence / Replay / Accountability
```

## Baseline / 当前基线

Evaluator 在产品修改前冻结：

- `evaluator_baseline/BASELINE_ACTION_ORIGIN.json`；
- baseline SHA-256 在冻结时由 Evaluator 留存；
- machine-readable Action Origin closed types（机器可读行为来源闭集）=`0/5`；
- autonomous behavior evidence 中 `action_origin` records=`0`；
- T01 authoritative trace read-model payload 中 `action_origin` records=`0`。

冻结输入证据：

1. Autonomous behavior fixture（自主行为证据）  
   `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_PREBUY_BEHAVIOR_CAPTURE_V1/evidence/EV-AUTONOMOUS-BEHAVIOR.json`  
   SHA-256 `cb11bdc27e514118c8e9ae69384be16d188ec08bba7c1d4514d6b3c50e316dd0`

2. T01 authoritative trace fixture（T01 权威支付轨迹）  
   `docs/05_任务交接/P9_AUTHORITATIVE_TRACE_READ_MODEL_PLAYER_V1/evidence/EV-03-T01.payload.json`  
   SHA-256 `7663a7c0f6387197d3d7bf6054a74025ff4a1f975b62482a99dff2fa4a7c6cca`

这些输入已经存在且可重复，本任务不重新优化它们的业务结果。

## Hypothesis / 假设

> 如果在不改变 Agent 购物策略、支付裁决和核心 Authoritative Trace schema（权威轨迹结构）的前提下，增加一个只读 Action Origin projection（行为来源投影），把已有自主 Agent 动作和权威支付事件机械映射为 `USER_AUTHORITY / AGENT_DECISION / RUNTIME_DECISION / EXTERNAL_FACT / EXECUTION_RESULT` 五类，并给每条记录保留可回指的 evidence ref（证据引用），则项目可以从“Agent 会行动”推进到“能回答是谁决定、依据来自哪里、执行结果是什么”的责任证据链。

这里的 responsibility（责任）仅指技术证据归因，不推导法律责任、赔偿责任、监管责任或机构最终权责。

## Single objective / 单一目标

只实现一个 principal change（唯一主要变化）：

> 新增一个 **read-only Action Origin / Responsibility Trace projection（只读行为来源 / 责任轨迹投影）**，消费已经冻结的 autonomous behavior evidence 与 authoritative trace read-model evidence，输出机器可读、确定性、可回指、fail-closed 的行为来源记录。

第一包不修改全局 `ProductTraceEvent` schema，不把 `action_origin` 强塞进所有既有 12 类产品轨迹；先验证最小纵向切片成立。后续只有出现真实消费者价值，才评估是否下沉到全局 Trace contract。

## Frozen Action Origin contract / 冻结行为来源闭集

只允许以下五类：

```text
USER_AUTHORITY
    用户明确授权 / Mandate / Authority 形成的行为或约束来源

AGENT_DECISION
    Agent 在授权边界内自主形成的搜索、选择或受治理动作

RUNTIME_DECISION
    Runtime Gate / Policy / binding checker 在执行前形成的机器裁决

EXTERNAL_FACT
    商户 / 页面 / 外部系统提供、而不是用户或 Agent 自主决定的事实

EXECUTION_RESULT
    支付、履约、退款、恢复等执行后产生的结果
```

不得新增 `UNKNOWN` 然后静默兜底。无法按冻结规则映射的输入必须 `fail closed（失败关闭）`，由显式异常/拒绝表示，不得猜来源。

## Frozen evaluator probe / 冻结评估探针

Evaluator checker：

`evaluator_checks/action_origin_probe.py`

目标必须 `5/5 PASS`：

1. `ActionOrigin` 正好是冻结五值闭集；
2. 已验收 autonomous behavior fixture 的每个 `chosen_action` 都投影为 `AGENT_DECISION`，顺序与动作值保持一致，并有 `evidence_ref`；
3. T01 authoritative trace 中至少机械确认以下 anchor：
   - `AUTHORITY_RECORDED → USER_AUTHORITY`
   - `ORDER_RECORDED:CURRENT_ORDER_SNAPSHOT → EXTERNAL_FACT`
   - `ACTION_RECORDED → AGENT_DECISION`
   - `RUNTIME_DECISION_RECORDED → RUNTIME_DECISION`
   - `PAYMENT_OUTCOME_RECORDED → EXECUTION_RESULT`
4. T01 投影总体覆盖五类来源，并且每条记录都有可回指 `evidence_ref`；
5. 未知 event / role 不能被猜测分类，必须抛出冻结 `ActionOriginError`。

## Public API boundary / 公共接口边界

Executor 在 `src/agentic_payment_experiment/action_origin.py` 中实现以下最小公共 API；命名冻结，内部实现可自行组织：

```text
ActionOrigin
ActionOriginError
ActionOriginRecord
classify_trace_event_origin(event)
project_autonomous_behavior_origins(behavior)
project_authoritative_trace_origins(trace)
action_origin_records_to_primitive(records)
```

要求：

- projector（投影器）只接受调用方传入的 mapping / evidence object；
- 产品模块自己不得读文件、访问网络、运行 WebShop、调用 payment callback；
- 输出必须 deterministic（确定性）；
- 每个 record 至少包含：`action_origin`、`action_or_event`、`evidence_ref`、可识别的 source namespace / source type；
- 允许附带 sequence、entity ref、decision/status/reason 等已有字段，但不得重新计算业务决策。

## Acceptance criteria / 验收标准

### AC-01 — Closed five-value Action Origin contract

- `ActionOrigin` 精确等于冻结五类；
- 无第六种默认/UNKNOWN 值；
- unknown trace event/role fail closed。

### AC-02 — Autonomous Agent decisions become attributable evidence

- 冻结 autonomous fixture 的 run0 三个真实 `chosen_action` 全部进入 `AGENT_DECISION` records；
- 顺序和值与原 evidence 完全一致；
- 只读投影，不重新运行 Agent，不修改其结果；
- 每条 action 有明确 evidence ref，可回指 `runs[0].steps[n]` 或等价稳定路径。

### AC-03 — User Authority / External Fact / Runtime Decision / Execution Result anchors

T01 frozen trace fixture 必须至少得到：

- `AUTHORITY_RECORDED → USER_AUTHORITY`；
- `CURRENT_ORDER_SNAPSHOT → EXTERNAL_FACT`；
- `ACTION_RECORDED → AGENT_DECISION`；
- `RUNTIME_DECISION_RECORDED → RUNTIME_DECISION`；
- `PAYMENT_OUTCOME_RECORDED → EXECUTION_RESULT`。

同一 event 的 origin 必须由明确 closed mapping 决定，不得根据测试期望动态改写。

### AC-04 — Evidence refs / source namespaces

- 每个 ActionOriginRecord 都必须保留稳定 `evidence_ref`；
- autonomous evidence 与 authoritative trace evidence 必须保持不同 source namespace，不能伪装成同一来源；
- 不制造两份 fixture 属于同一个真实 transaction/journey 的虚假 correlation（关联）。

### AC-05 — Deterministic primitive read model

- `action_origin_records_to_primitive(records)` 只输出 JSON-compatible primitive；
- 同一输入重复投影完全一致；
- 不读 hidden truth，不依赖当前时间/随机数/内存地址/本地绝对路径。

### AC-06 — Read-only / anti-scope-creep

`action_origin_source_audit.py` 必须 PASS：

- WebShop shopping policy 及 dedicated tests hash 不变；
- core `authoritative_trace.py` / `authoritative_trace_consumer.py` hash 不变；
- 两份冻结 evidence fixture hash 不变；
- 新模块不得 import WebShop runtime / network / subprocess；
- 不触发 Buy Now、payment callback 或执行链；
- 不写法律/监管/赔偿责任裁决字段。

### AC-07 — Existing trust/payment chain unchanged

- Authoritative Trace / Consumer regression PASS；
- WebShop Agent behavior regression PASS；
- Journey Read Model / Player regression PASS；
- formal `run_experiment.py` PASS；
- project-impact baseline repeat=3 一致；
- Product Trace、GESR、callback、duplicate/forbidden side-effect 指标不退化；
- full unittest 无新增失败。

### AC-08 — v2.2 evidence handoff

- frozen Validation Plan `8/8` mandatory checks PASS；
- REPORT.md 映射 AC-01..08 → EV；
- 记录 baseline `0/5` → target `5/5`、新文件 hash、protected asset hash、deviations；
- Executor 只提交 `SUBMITTED_FOR_REVIEW`，不得自行签发 Task PASS / Project IMPROVED。

## Allowed scope / 允许范围

Executor 仅可修改/新增：

- `src/agentic_payment_experiment/action_origin.py`
- `tests/test_action_origin.py`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_ACTION_ORIGIN_RESPONSIBILITY_TRACE_V1/REPORT.md`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_ACTION_ORIGIN_RESPONSIBILITY_TRACE_V1/evidence/**`

如公共 `__init__.py` 导出确有必要，先不做；第一包直接从 module import，避免无价值扩散。

## Exclusions / 明确排除

本包禁止：

- 修改 `webshop_agent_behavior.py` 或继续修 H-15 intent/option 长尾；
- 修改 H-14/H-15 probe、Systematic Discovery matrix / failure ledger；
- 修改 `authoritative_trace.py` / `authoritative_trace_consumer.py` 全局 schema；
- 修改 WebShop Adapter、Runtime Gate、Governed Payment Action、Payment/Fulfillment/Recovery 的业务裁决；
- 把两份冻结 fixture 伪装成同一真实 transaction；
- 新增 `responsibility_breakpoint` 自动法律归责；
- 执行 Buy Now、真实购买、支付、订单、履约或恢复副作用；
- 外部 API / network；
- 依赖安装 / 新环境；
- commit / push / history rewrite。

## Bounded execution / 有界执行

- max implementation→L2 cycles: `3`；
- 一个 principal change：read-only Action Origin projection；
- 不因为某个 event 不好分类就修改原业务对象；应在 closed mapping 证据不足时 fail closed；
- 不扩大到全局 Trace schema 或 UI。

推荐 L1：

```text
python3 -m unittest tests.test_action_origin -v
python3 .../action_origin_probe.py --require-all
python3 .../action_origin_source_audit.py
```

## Stop conditions / 停止条件

出现以下任一情况立即停止并回 Evaluator：

- 必须修改 Agent shopping policy 才能完成 Action Origin；
- 必须修改 payment/runtime decision 才能获得来源分类；
- 必须修改全局 Authoritative Trace schema 才能完成第一包；
- 无法在 frozen fixtures 上明确区分五类来源；
- 需要把两份独立 fixture 声称成同一 transaction；
- 需要第二个 principal change；
- 任一 protected hash 改变；
- 任一真实副作用或网络调用；
- 3 个完整 implementation→L2 cycles 用尽仍不满足 AC。

## Authorization / 授权

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- environment_creation: false
- local_fixture_read: true
- WebShop_runtime_execution: false
- Buy_Now_execution: false
- payment_or_order_side_effect: false

## Executor instructions / 执行者说明

直接执行冻结 H-13，不重新设计主线：

```text
read CURRENT / Contract / Validation Plan / evaluator checks
→ implement read-only action_origin.py + dedicated tests
→ L1
→ frozen L2
→ REPORT.md with AC-01..08 / EV mapping
→ workflow validator
→ SUBMITTED_FOR_REVIEW
```

不要回头修 H-15。发现新的 intent / option 长尾只记入已知限制，不属于本包。

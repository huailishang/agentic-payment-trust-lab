# Execution Contract

Task ID: `P9_T05_T06_ACTION_BINDING_REJECTION_TRACE_V1`  
Task kind: `capability_experiment`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `04047308519a0ea69b7d7c0173f74e2b1fe30fc7`  
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-17-r43`  
Active bottleneck: `B-03`  
Hypothesis: `H-31`  
Validation plan file: `docs/05_任务交接/P9_T05_T06_ACTION_BINDING_REJECTION_TRACE_V1/VALIDATION_PLAN.yaml`  
Metric baseline: Product Authoritative Trace=`10/12`; GESR=`9/12`; T05/T06 only fail authoritative-trace dimensions  
Estimated affected scope: T05/T06 WebShop action-binding rejection branch and its product trace only  
Expected project impact: Product Trace `10/12→12/12`; GESR `9/12→11/12`; T05/T06 decision/binding/reason/callback unchanged  
Rollback condition: any T05/T06 decision/binding/reason/callback drift, any non-target task drift, protected hash drift, side effect regression, or inability to produce a VALID trace without changing business rules

Baseline git HEAD: `04047308519a0ea69b7d7c0173f74e2b1fe30fc7`  
Accepted parent snapshot: current working tree after H-30 `PASS / IMPROVED`; H-30 remains uncommitted because commit/push authorization is false.

## 1. Global position / 全局位置

```text
A. 评测与治理底座                  [完成]
→ B. 授权、绑定、来源、执行前治理   [完成]
→ C. 支付生命周期、恢复、补救证据链 [完成]
→ D. 责任归因与可消费审计链         [完成]
→ E. 主体真实性 / 凭证 / 签署指令   [本地代表性闭环完成]
→ F. 外部真实协议 / SDK / 网络接入   [DEFERRED]

横切 B-05 Data Minimization         [H-30 本地阶段关闭]
当前本地主线 B-03 Authoritative Trace [H-31]
```

H-30 已经独立 L3 再次 `8/8 PASS`，PayBench=`10/10`。不继续扩大 Data Minimization，也不把完整 Privacy Governance 拉入本任务。

## Strategic basis / 战略依据

当前项目已完成 A-D 与阶段 E 的本地代表性闭环，H-30 又关闭了 B-05 字段名级 Data Minimization 缺口。剩余候选中，B-04 继续 WATCH、B-06 受外部环境与授权约束继续 DEFERRED；B-03 的 T05/T06 是当前唯一明确、重复、可本地闭合且不需要修改业务决策的 measured gap，因此优先进入 H-31。

## 3. Measured bottleneck / 实测瓶颈

Evaluator 重新运行 12 项项目基线，当前共同断点是：

```text
T05 Agent 错绑
  decision=DENY
  binding=INVALID
  callback=0
  reasons=(
    action:agent_ref_identity_mismatch,
    action:agent_ref_mandate_mismatch,
    action:agent_ref_request_mismatch,
  )
  authoritative_trace=NOT_AVAILABLE

T06 动作契约缺证据
  decision=INDETERMINATE
  binding=MISSING_EVIDENCE
  callback=0
  reasons=(action:action_id_missing,)
  authoritative_trace=NOT_AVAILABLE
```

二者共同缺：

```text
authoritative_trace evidence stage
AUTHORITY_RECORDED
ORDER_RECORDED
REQUEST_RECORDED
ACTION_BINDING_DECISION_RECORDED
```

这不是决策错误。现有 `verify_governed_payment_action()` 已经正确 fail closed（失败即关闭），WebShop Runtime Gate 也没有执行 callback。缺的是：拒绝之后，产品没有把已经存在的 mandate / order / request / governed action / binding fact / outcome 机械装配成 Product Authoritative Trace（产品权威轨迹）。

## 3. Hypothesis / 假设

> 若新增一个协议中立、只消费既有不可变事实的 action-binding rejection trace family（动作绑定拒绝轨迹族），复用现有 `webshop_trace_assembler.py` 与已经冻结在 `authoritative_trace.py` 中的 T05/T06 profile contract，并只在 Runtime Gate 的 `GovernedActionBindingFact != VALID` 早退分支挂载 trace，则可以在不改变治理决策和副作用语义的情况下，把 Product Trace `10/12→12/12`，并预计把 GESR `9/12→11/12`。

唯一 principal change（主要变化）：

```text
existing mandate/order/request/action/payment-candidate/binding-fact/outcome
        ↓
action-binding rejection trace toolkit
        ↓
existing ProductAuthoritativeTrace contract
        ↓
attach to the existing early-rejection outcome
```

不得通过 task ID、T05/T06 名称或 baseline expected answer 生成 trace。选择 trace profile 必须由实际事实形状与 `VerificationStatus` / reason evidence 决定。

## 4. Frozen semantics / 冻结语义

### T05 必须保持

```text
decision=DENY
binding_status=INVALID
callback_count=0
checkout_executed=false
reason_codes exact=
  action:agent_ref_identity_mismatch
  action:agent_ref_mandate_mismatch
  action:agent_ref_request_mismatch
```

### T06 必须保持

```text
decision=INDETERMINATE
binding_status=MISSING_EVIDENCE
callback_count=0
checkout_executed=false
reason_codes exact=action:action_id_missing
```

### 新增证据要求

T05/T06 的 `authoritative_trace` 均必须经现有 `validate_product_authoritative_trace()` 验证为 `VALID`，并至少包含：

```text
AUTHORITY_RECORDED
ORDER_RECORDED
REQUEST_RECORDED
ACTION_BINDING_DECISION_RECORDED
RESULT_RECORDED
```

且 trace 必须绑定真实产品路径已经产生的源对象，不允许 evaluator reconstruction（评估器重建）或隐藏 resolver（解析器）。

## 5. Allowed scope / 允许范围

### Allowed product scope

- `src/agentic_payment_experiment/webshop_action_binding_trace_toolkit.py`（新增，建议）
- `src/agentic_payment_experiment/webshop_runtime_gate.py`（只允许在 action-binding rejection 早退分支挂载 trace，并新增必要 import）

### Allowed tests

- `tests/test_webshop_action_binding_trace_toolkit.py`（新增，建议）
- `tests/test_webshop_runtime_gate.py`（只增加/加强 T05/T06 等价拒绝分支的 trace 断言）

### Task-owned artifacts

- `docs/05_任务交接/P9_T05_T06_ACTION_BINDING_REJECTION_TRACE_V1/REPORT.md`
- `docs/05_任务交接/P9_T05_T06_ACTION_BINDING_REJECTION_TRACE_V1/evidence/*`

## 6. Exclusions / 明确排除

- 不修改 Governed Action verifier、Payment policy、P1-P4、M5、PayBench、H-30；
- 不修改 frozen project-impact fixture 或 trace validator/profile contract；
- 不用 `task_id` / `scenario_id` 决定产品行为；
- 不修 T10；
- 不新增依赖、网络、API、数据库、真实支付、真实凭证；
- 不 commit、push 或 history rewrite。

## 7. Protected / frozen files

以下文件不得修改：

```text
src/agentic_payment_experiment/authoritative_trace.py
SHA-256 f1d06b9d0654f0a34954104b62b8555fe91e2b80fc34a0d4049d093928feb492

src/agentic_payment_experiment/webshop_trace_assembler.py
SHA-256 c98c3a1477ebf64a5696707c0d637da60d8563ef174b06a100c9d9b7bebc1656

src/agentic_payment_experiment/trusted_execution/governed_action.py
SHA-256 115df903ff7ba4090438c7a5b89132882e43bc97830672899837165d05058c7e

src/agentic_payment_experiment/payment_execution.py
SHA-256 d161be5afe73192491e20203651dc3b222fa37454235c1bacc37042c6254fb49

src/agentic_payment_experiment/validator.py
SHA-256 9c001311c36a00d33959fffbf50784ff42928100d622a4d645b79ec8e395cbcb

scripts/validation/run_project_impact_baseline.py
SHA-256 70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3

samples/evaluation/project_impact_baseline_v1.json
SHA-256 e7a1d338ece0c65c6417ce58384e8dc9eb2dc29b2e37ad461cf92b9deb9b89c0

src/agentic_payment_experiment/data_disclosure.py
SHA-256 42fb3ffff4bbb034f9d1fe3840f58931b9281fa4f691b5303eb7ff0775da3d26

src/agentic_payment_experiment/paybench_current_system.py
SHA-256 319cdf82d849393b8adcaeabf73d79f4f7fb772fab2784439fc2c4877fbaccc1
```

禁止修改 T05/T06 frozen baseline fixture、trace validator contract、Governed Action verification、Payment policy、P1-P4、M5、PayBench 或 H-30 语义来让本任务通过。

## 7. Acceptance Criteria / 验收条件

### AC-01 — Generic rejection trace family

存在一个只消费既有产品事实的通用 action-binding rejection trace builder。允许引用冻结 trace contract 中已有的 T05/T06 profile 名称作为输出 schema 标识，但不得读取/接收 `task_id`、`scenario_id`、`governed_action_agent_mismatch`、`governed_action_missing_id` 等评测身份来决定业务分支；profile 选择必须由实际 `GovernedActionBindingFact` 与源对象形状机械决定。

### AC-02 — T05 semantics preserved + trace added

T05 保持冻结的 `DENY / INVALID / callback=0 / exact reasons`，同时产品权威轨迹从 `NOT_AVAILABLE→VALID`。

### AC-03 — T06 semantics preserved + trace added

T06 保持冻结的 `INDETERMINATE / MISSING_EVIDENCE / callback=0 / exact reason`，同时产品权威轨迹从 `NOT_AVAILABLE→VALID`。

### AC-04 — Trace contract integrity

T05/T06 trace 均由现有 validator 判定 `VALID`，至少包含冻结必需事件；所有 event/source binding/relation 仍服从现有 trace contract，不修改 validator/profile contract。

### AC-05 — Project impact

同一 12 项 fixture：

```text
Product Trace 10/12 → 12/12
GESR          9/12  → 11/12
remaining gap task IDs = [T10]
```

T10 当前安全语义和既有 gap 不在本任务处理范围。

### AC-06 — Non-target and side-effect guardrails

- T01-T04/T07-T12 除 T05/T06 新 trace 外，业务结果不漂移；
- callback match=`12/12`；
- unsafe allow=`0/5`；
- duplicate/forbidden side-effect=`0/12`；
- project baseline repeat=`3/3 identical`。

### AC-07 — Regression guardrails

- S01-S13=`13/13 PASS`；
- PayBench current rules=`10/10 PASS`；
- full unittest zero failures；
- protected hashes unchanged。

### AC-08 — v2.2 evidence handoff

L2 Validation Plan 全绿，REPORT 映射 AC-01..08，并明确本能力只补离线产品证据连续性，不构成生产审计、监管合规或真实网络证据。

## 8. Evaluator-owned negative properties / 评估者反例性质

至少证明：

1. builder 不依赖 task/scenario ID；
2. `INVALID` 和 `MISSING_EVIDENCE` 两种 action-binding rejection 都能产生合法 trace；
3. trace 构建失败时不得改变原决策或触发 callback；
4. 不得把 missing action ID 伪造成一个正常 native action identity；应继续使用冻结的 missing-id projection contract；
5. 不得用 evaluator-synthesized replay 充当产品权威轨迹。

## 9. External requirement impact

```text
profile: PCAC-AGENTPAY
PCAC-12 可信存证 / Evidence Chain: CORE
applicability: DIRECT
before: Product Trace 10/12，T05/T06 安全拒绝但产品证据链缺口
expected_after: Product Trace 12/12，拒绝原因可由产品事实链机械回指
PCAC-15 Data Minimization: NO_CHANGE（H-30 已本地阶段关闭）
residual_risk: 离线 deterministic trace，不代表生产存证、不可抵赖或监管合规
```

## 10. Stop conditions / 停止条件

立即停止并返回 Evaluator：

- 需要修改任何 protected file；
- 需要改变 T05/T06 decision / binding / reason / callback 才能生成 trace；
- 需要 task ID/scenario ID 特判；
- T10 被顺带修改；
- PayBench/H-30、S01-S13 或其他项目守护线退化；
- 需要网络、数据库、新依赖、真实支付或真实凭证；
- 超过 `2` 个完整 implementation→L2 cycle。

## 11. Amendment A1 / 历史回归期望窄修订

Evaluator 独立复现第一次 L2 的 6 个失败后确认：产品实现、T05/T06 决策语义、Product Trace 目标和项目守护线没有新增失败；阻断来自两份旧回归测试仍冻结 H-31 之前的历史期望。

在本任务剩余最后 `1` 次 implementation→L2 cycle 内，新增允许修改：

- `tests/test_project_impact_baseline.py`
- `tests/test_webshop_authoritative_trace.py`

唯一允许变化是机械同步已经由 VP-02 / VP-04 独立证明的结果：

```text
matched tasks: 9 → 11
gap tasks: 3 [T05,T06,T10] → 1 [T10]
GESR: 9/12 → 11/12
evidence-stage completeness: 9/12 → 11/12
Product Trace: 10/12 → 12/12
T05/T06 product trace: NOT_AVAILABLE → VALID
T05/T06 product trace source: webshop_gate_outcome
CLI gap_tasks: 3 → 1
```

`tests/test_project_impact_baseline.py` 必须继续证明 evaluator-synthesized replay 与 product-observed trace 来源分离；不得删除 provenance 断言或把 evaluator replay 当作产品轨迹。

`tests/test_webshop_authoritative_trace.py` 只允许把 `action_invalid` 子案例从“无 trace”同步为 `WEBSHOP_ACTION_BINDING_T05_V2 / VALID`；`prepayment_deny`、`known_attempt_indeterminate`、`known_attempt_clear` 等其余非目标分支仍必须保持原来的无 trace 断言。允许为准确表达新合同而重命名该测试方法，但不得放宽其他分支。

A1 禁止修改任何产品实现、fixture、baseline runner、trace validator/profile contract、T10、PayBench/H-30 或业务判断。若第二次 L2 仍有产品/守护线失败，停止并返回 Evaluator，不再追加第三个实现循环。

## 12. Authorization / 授权

- local CPU: true
- dependency install: false
- network/API: false
- real payment: false
- real credential/PII: false
- commit: false
- push: false
- history rewrite: false

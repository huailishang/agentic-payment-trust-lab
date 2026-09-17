# Execution Contract

Task ID: `P9_T10_BASELINE_SEMANTIC_RECONCILIATION_V1`  
Task kind: `repair`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `04047308519a0ea69b7d7c0173f74e2b1fe30fc7`  
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-17-r44`  
Active bottleneck: `B-01`  
Hypothesis: `H-32`  
Validation plan file: `docs/05_任务交接/P9_T10_BASELINE_SEMANTIC_RECONCILIATION_V1/VALIDATION_PLAN.yaml`  
Metric baseline: H-31 后 Product Trace=`12/12`; GESR=`11/12`; evidence completeness=`11/12`; sole gap=`T10`  
Estimated affected scope: only T10 expected semantics in the main 12-task measurement fixture plus directly dependent regression expectations  
Expected project impact: `NOT_APPLICABLE` — this repairs measurement semantics; any GESR `11/12→12/12` change is a corrected measurement, not a product capability gain  
Rollback condition: any product/runner/accepted-target drift, any non-T10 fixture drift, any T10 non-authorized-field drift, or any safety/regression failure

Accepted parent snapshot: current working tree after H-30 and H-31 Evaluator `PASS`; commit/push remain unauthorized.

## 1. Global position / 全局位置

```text
A. 评测与治理底座                  [需要一次 T10 语义漂移修复]
→ B. 授权、绑定、来源、执行前治理   [完成]
→ C. 支付生命周期、恢复、补救证据链 [完成]
→ D. 责任归因与可消费审计链         [完成]
→ E. 主体真实性 / 凭证 / 签署指令   [本地代表性闭环完成]
→ F. 外部真实协议 / SDK / 网络接入   [DEFERRED]

B-03 Product Authoritative Trace     [H-31 后固定 12 项覆盖 12/12]
B-01 Measurement Integrity           [CURRENT: T10 expectation drift]
```

H-31 已独立 L3 `8/8 PASS`，Product Trace=`12/12`。剩余 T10 gap 不是继续改产品 trace 的依据。

## Strategic basis / 战略依据

T10 的业务目标一直是“同一请求已有成功付款时不产生第二次付款副作用”。B-07 已独立验收：历史同 request `SUCCEEDED` payment 应在 callback 前触发 preflight block，Runtime Gate 返回 `DENY`、callback=`0`，并消除重复付款副作用。

但当前主 fixture `samples/evaluation/project_impact_baseline_v1.json` 仍保留更早的：

```text
expected_decision=ALLOW
payment_status=UNKNOWN
fulfilment_status=PENDING
task_status=UNKNOWN
remediation_status=REQUIRED
reason=duplicate:payment_blocked
required evidence includes lifecycle
```

已验收 target `samples/evaluation/project_impact_t10_preflight_target_v1.json` 则冻结：

```text
expected_decision=DENY
callback=0
preflight BLOCKED
no new payment/lifecycle state mutation
reason includes p1:duplicate_request + preflight:known_payment_attempt_duplicate_succeeded
required fact/evidence includes known_payment_attempt_preflight
```

Evaluator 已在不修改仓库产品代码的临时 fixture 上机械对齐这 5 个 expected 字段，得到：

```text
GESR=12/12
evidence completeness=12/12
Product Trace=12/12
gap=0
repeat=3/3 identical
```

因此 H-32 是测量合同修复，不是产品能力实验。

## 3. Measured bottleneck / 实测瓶颈

H-31 独立 L3 后，T10 当前 actual：

```text
decision=DENY
callback=0
binding=VALID
known_payment_attempt_preflight=BLOCKED
product_observed_trace=VALID
forbidden_side_effects=[]
duplicate_payment_blocked=true
payment/task/lifecycle terminal state not produced because callback is blocked before payment
```

主 fixture 当前却仍期待 `ALLOW + UNKNOWN/PENDING lifecycle`，所以 T10 的四个 gap 是：

```text
decision mismatch
final_environment_state mismatch
reason_codes mismatch
lifecycle evidence missing
```

这些差异与 B-07 已验收的安全行为相冲突。

## 3. Hypothesis / 假设

> 若只把主 12-task fixture 的 T10 期望语义机械对齐到已独立验收的 `project_impact_t10_preflight_target_v1.json`，并同步直接依赖这些测量值的回归断言，而不修改任何产品代码、runner 或 accepted target，则剩余 T10 gap 应消失，GESR / evidence completeness / Product Trace 均为 `12/12`，同时全部安全守护线保持不变。

唯一 principal change：

```text
accepted B-07 T10 semantics
        ↓
reconcile five stale expected fields in main project baseline fixture
        ↓
mechanically sync measurement regression expectations
        ↓
rerun same runner / same product snapshot
```

这不是把 expected 改成“当前代码输出”来过测试；依据必须是先于本任务存在、并已独立验收的 B-07 target 和 REVIEW。

## 4. Frozen semantic source / 冻结语义来源

权威对照：

` samples/evaluation/project_impact_t10_preflight_target_v1.json `  
SHA-256 `f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee`

只允许主 fixture T10 的以下 5 个字段与该 target 完全一致：

```text
expected_decision
expected_final_environment_state
expected_reason_codes
expected_required_evidence_stages
expected_required_facts
```

T10 其他字段全部冻结，包括 scenario、initial state、user goal、mandate、order snapshot、action sequence、observations、callback/retry expectations、binding、lineage、trace status/events、side-effect guardrail、limitations。

## 5. Allowed scope / 允许范围

### Allowed measurement scope

- `samples/evaluation/project_impact_baseline_v1.json`
  - 仅 T10 上述 5 个 `expected_*` 字段；
  - 必须逐字段复制已验收 target 语义，不得自行重新定义。

### Allowed regression scope

- `tests/test_project_impact_baseline.py`
  - 只同步由该 T10 fixture reconciliation 直接导致的：`matched 11→12`、`gap 1→0`、GESR `11/12→12/12`、evidence completeness `11/12→12/12`、CLI gap count、execution status 及 T10 expected semantics；
  - Product Trace 继续 `12/12`；
  - provenance 分离、安全守护线、runner boundary、tamper tests 不得删除或弱化。

### Task-owned artifacts

- `docs/05_任务交接/P9_T10_BASELINE_SEMANTIC_RECONCILIATION_V1/REPORT.md`
- `docs/05_任务交接/P9_T10_BASELINE_SEMANTIC_RECONCILIATION_V1/evidence/*`

## 6. Exclusions / 明确排除

- 不修改任何 `src/` 产品代码；
- 不修改 `scripts/validation/run_project_impact_baseline.py`；
- 不修改 `project_impact_t10_preflight_target_v1.json`；
- 不修改 trace validator/profile、PayBench、S01-S13、H-30/H-31 产品实现；
- 不修改 T01-T09/T11/T12 fixture；
- 不把本任务的 GESR 上涨写成产品能力改善；
- 不新增依赖、网络/API、数据库、真实支付或真实凭证；
- 不 commit、push 或 history rewrite。

## 7. Protected / frozen files

```text
src/agentic_payment_experiment/webshop_runtime_gate.py
SHA-256 d041e6e41fdc536f7969144eeca5aff164bd504da1cf29f352b428f5f92fa2d7

src/agentic_payment_experiment/webshop_action_binding_trace_toolkit.py
SHA-256 c3e6bfa1c549c75a79b51aadfcd7ef1b3d9d8021ac2d9f76ab44f6a03ed4ba9d

src/agentic_payment_experiment/authoritative_trace.py
SHA-256 f1d06b9d0654f0a34954104b62b8555fe91e2b80fc34a0d4049d093928feb492

scripts/validation/run_project_impact_baseline.py
SHA-256 70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3

samples/evaluation/project_impact_t10_preflight_target_v1.json
SHA-256 f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee
```

主 fixture 的冻结分块：

```text
top-level excluding tasks canonical SHA-256 = 608b2def9f1711d4f6bb600f11329e7b3d829b51a49563e0f4bd670fa19b48bf
non-T10 tasks canonical SHA-256            = b970d15ef26cbecf4ae03f78b1061653edfaadb237e1c538504f5d2a9bbe29a8
T10 excluding five allowed fields SHA-256 = 48515848eeea263718092cf4d8140836b27067dde03c3132b913b6c2aa3e4877
```

## 7. Acceptance Criteria / 验收条件

### AC-01 — Semantic authority preserved

已验收 T10 target 与 runner/product protected hashes 完全不变；主 fixture 只有 5 个授权字段变化，且逐字段等于 target。

### AC-02 — No product change

本任务不得有任何 `src/` 修改；T10 actual 仍为 `DENY / callback=0 / BLOCKED / trace VALID`，不是靠产品改动匹配 fixture。

### AC-03 — Measurement reconciliation

同一主 12-task fixture repeat=3：

```text
matched=12/12
gap=[]
GESR=12/12
evidence completeness=12/12
Product Trace=12/12
execution_status=MEASURED_ALL_MATCHED
```

### AC-04 — Safety guardrails unchanged

```text
callback match=12/12
duplicate/forbidden side effect=0/12
unsafe allow=0
T10 callback=0
T10 forbidden side effects=[]
```

### AC-05 — Regression integrity

`tests.test_project_impact_baseline` 全绿，且 provenance/tamper/runner-boundary/side-effect guardrails 仍存在；不得通过删测试、skip 或放宽断言实现。

### AC-06 — External regressions

PayBench current rules=`10/10 PASS`；S01-S13=`13/13 PASS`；full unittest zero failures。

### AC-07 — Correct project-impact attribution

REPORT 必须明确：本任务为 measurement repair；即使 GESR `11/12→12/12`，Project impact verdict 也只能是 `NOT_APPLICABLE`，不得宣称新增产品能力。

## 8. Evaluator-owned checks / 评估者检查

Evaluator checks 将机械验证：

1. accepted target、runner 和 H-31 产品代码哈希不变；
2. non-T10 与 T10 非授权字段 canonical hash 不变；
3. 5 个授权字段精确等于 accepted target；
4. fresh repeat=3 得到 `12/12 / gap=0`；
5. T10 actual 保持安全的 preflight DENY 语义；
6. 不要求 lifecycle evidence，因为 callback 已在支付前阻断。

## 9. External requirement impact

```text
profile: PCAC-AGENTPAY
PCAC-12 Evidence Chain: NO_NEW_CAPABILITY
measurement effect: corrected baseline attribution only
before reported GESR: 11/12
expected corrected GESR: 12/12
Product Trace: remains 12/12
residual risk: external/live production evidence remains DEFERRED
```

## 10. Stop conditions / 停止条件

立即停止并返回 Evaluator：

- 需要修改产品代码或 runner；
- accepted T10 target 需要改动；
- 非 T10 fixture 发生任何变化；
- T10 除 5 个授权 expected 字段外发生变化；
- 需要把 current safe `DENY` 产品行为改回 `ALLOW`；
- guardrail、PayBench、S01-S13 或 full unittest 退化；
- 需要网络、新依赖、真实支付/凭证；
- 超过 `1` 个 implementation→L2 cycle。

## 11. Authorization / 授权

- local CPU: true
- dependency install: false
- network/API: false
- real payment: false
- real credential/PII: false
- commit: false
- push: false
- history rewrite: false

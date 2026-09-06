# Frozen Task Contract

Task ID: `P9-AUTONOMOUS-WEBSHOP-SAME-JOURNEY-RESPONSIBILITY-CORRELATION-V1`  
Task name: Autonomous WebShop Same-Journey Responsibility Correlation  
Task kind: `one_off`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `57ded7bb2fb0ca830748b35b857a8d07624fe3d4`  
Validation plan file: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_RESPONSIBILITY_CORRELATION_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-06-r26`  
Active bottleneck: `B-11`  
Hypothesis: `H-16`

H-13 已经由 Executor L2 与 Evaluator L3 独立证明：`Action Origin 0/5 → 5/5`，Task=`PASS`、Project impact=`IMPROVED`。但 H-13 使用的 autonomous behavior fixture 与 T01 payment authoritative trace 是两个独立证据命名空间，不能证明它们来自同一条真实 WebShop journey。

因此 B-11 当前剩余的第一问题不是继续扩 `ActionOrigin` 枚举，也不是把字段马上下沉到全局 `ProductTraceEvent` schema，而是：

> **同一条 autonomous WebShop journey，能不能从 Agent actions 连续关联到同一 session 的 Commerce Order/Request、Runtime Decision、offline execution result 与 authoritative trace？**

本包先测现有组件是否已经具备这种连续性。若可以，不新增产品层；若不可以，真实断点才升级成下一 capability hypothesis。

当前主线：

```text
H-13 Action Origin semantics【PASS / IMPROVED】
        ↓
H-16 Same-Journey Responsibility Correlation【CURRENT】
        ↓
确认真实断点
        ↓
再决定：consumer/global Trace integration 或新的最小能力修复
        ↓
Governed Payment Action → Payment / Finality / Fulfillment / Recovery
```

## Measurement basis / 测量基础

Evaluator 在执行前冻结：

- accepted autonomous behavior evidence：
  `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_PREBUY_BEHAVIOR_CAPTURE_V1/evidence/EV-AUTONOMOUS-BEHAVIOR.json`
- fixture SHA-256：`cb11bdc27e514118c8e9ae69384be16d188ec08bba7c1d4514d6b3c50e316dd0`
- accepted normalized trace SHA-256：`8c0a03b2f2e5dd9dce051ce176c546e2e171b5e7eacfdb36b258ba04dddd5897`
- goal index=`10`
- seed=`20260823`
- checkout HEAD=`64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd`
- accepted ASIN=`B099231V35`
- accepted option=`orange`
- accepted price=`16.79`
- same-journey required correlations baseline=`0/8`

Evaluator-frozen explicit experiment context：

`evaluator_fixtures/SAME_JOURNEY_EXPERIMENT_CONTEXT.json`

它与 WebShop instruction 严格分离：

- instruction **不是** authorization mandate；
- experiment context **不是** WebShop verified fact；
- offline callback **不是** real Buy Now；
- offline payment / fulfillment record **不是** real execution。

## Single objective / 单一目标

只完成一个 bounded one-off evidence task（有界一次性证据任务）：

> 重放已经验收的 goal 10 autonomous journey；只有 replay normalized trace 与 accepted trace 完全一致时，才从**同一次 runtime/session** 导出 pre-Buy-Now candidate，并调用现有 Commerce Adapter、Runtime Gate、Payment/Fulfillment Sidecar、Authoritative Trace 与 H-13 Action Origin，产出一个机器可核验的 `webshop-same-journey-responsibility/v1` 结果。

本包不预设产品代码需要修改。若现有组件不能串起来，Executor 应记录真实断点并返回，而不是扩 scope 修产品。

## Frozen execution design / 冻结执行设计

Executor 新增：

`scripts/validation/webshop/run_same_journey_responsibility.py`

允许复用 `run_autonomous_prebuy_behavior.py` 的已有 runtime/policy helper，也可等价实现；但不得修改旧 runner。

Runner 必须按以下顺序执行：

```text
1. local WebShop goal 10 / seed 20260823 replay × 2
2. 到 pre-Buy-Now stop；绝不执行 click[buy now]
3. 使用与 accepted evidence 相同的 normalized trace 算法
4. 两次 replay 相同，并且 trace hash == accepted trace hash
5. 从同一次 replay runtime/session 导出 candidate：
   session / instruction / actions / ASIN / title / selected options / quantity / exact price
6. source/provenance 只可复用 frozen WebShop source scaffold；
   experiment_context 使用 Evaluator-frozen SAME_JOURNEY_EXPERIMENT_CONTEXT.json
7. 调现有 adapt_webshop_purchase_candidate(candidate)
8. 用 frozen explicit authority/identity 构建 mandate / identity / context-policy / governed-action inputs
9. 调现有 gate_webshop_buy_now(...)；仅允许 injected local callback seam
10. 构造 caller-supplied offline PaymentExecutionRecord / FulfillmentRecord
11. 调现有 assess_webshop_payment_fulfilment(...)
12. 验证 sidecar authoritative trace == VALID
13. 调现有 Authoritative Trace Consumer + H-13 Action Origin projection
14. 写 SAME_JOURNEY_RESULT.json
```

禁止用 accepted expected ASIN/option/price 去改变 Agent policy 决策。它们只能用于 replay identity / evidence audit。

## Required correlation contract / 必须连续的 8 条关联

结果必须精确包含以下 8 个 correlation IDs：

```text
C01_REPLAY_IDENTITY
    accepted autonomous normalized trace == replay normalized trace

C02_SESSION_TO_CANDIDATE
    replay runtime session == exported candidate session

C03_ACTIONS_TO_CANDIDATE
    replay instruction/actions == candidate instruction/actions

C04_PRODUCT_TO_ORDER
    replay selected product/options == candidate == Commerce Order item/options

C05_ORDER_TO_REQUEST
    Commerce Order.order_id == TransactionRequest.order_ref

C06_REQUEST_TO_RUNTIME
    same TransactionRequest.request_id/order_ref == Runtime Gate bound request

C07_ORDER_REQUEST_TO_EXECUTION
    same order/request == offline PaymentExecutionRecord / FulfillmentRecord refs

C08_TRACE_ORIGIN_CONTINUITY
    same order/request/payment refs enter VALID authoritative trace and expose the five H-13 Action Origin classes
```

每条 correlation 必须记录：

- `correlation_id`
- `source_path`
- `source_value`
- `target_path`
- `target_value`
- `equal`

不得只写一个布尔结论而不留下两端证据值。

## Acceptance criteria / 验收标准

### AC-01 — Accepted autonomous replay identity

- goal 10 / seed 20260823 / repeat=2；
- repeat identical；
- replay normalized trace SHA=`8c0a03b2f2e5dd9dce051ce176c546e2e171b5e7eacfdb36b258ba04dddd5897`；
- replay 仍选择 `B099231V35 / orange / 16.79`；
- real WebShop `buy_now_executed=false`；
- purchase count=`0`。

若 replay 与 accepted evidence 不一致，立即停止；不得调整 policy 或 expected truth 来制造一致。

### AC-02 — Candidate comes from the same runtime/session

Candidate 必须从同一次 replay 的 runtime/session 直接导出：

- session id 完全一致；
- instruction 完全一致；
- actions 完全一致；
- ASIN / selected options / price 完全一致；
- title 读取 `runtime.server.product_item_dict[selected_asin]` 或等价当前 runtime source；
- 不得从历史 Commerce fixture 复制商品/session/actions。

允许复用 `samples/external/webshop/pre_buy_now_candidate_v1.json` 的 **source/provenance scaffold only**；该历史 fixture 的 session / product / instruction / actions / experiment context 均不得作为当前 journey 事实。

### AC-03 — Commerce Order/Request continuity

现有 `adapt_webshop_purchase_candidate(candidate)` 必须 `ready=true`，并满足：

- `user_intent_text == replay instruction`；
- Order item ASIN == replay ASIN；
- selected options 保持；
- Order total == exact replay price × quantity；
- `Order.order_id == TransactionRequest.order_ref`；
- authority ref/version 来自 frozen explicit experiment context，而不是 instruction 推导。

### AC-04 — Runtime decision continuity

使用现有 Runtime Gate：

- explicit `IntentMandate` 来自 evaluator fixture；
- AgentIdentity / executor / context-policy facts 明确构造；
- governed action refs 必须使用 AC-03 的同一 Order/Request；
- final decision=`ALLOW`；
- injected callback seam count=`1`；
- callback ref=`offline-same-journey-checkout-seam`；
- 必须明确 `real_webshop_buy_now_executed=false`。

如果 Runtime Gate 因现有合同真实阻断，则记录为 H-16 evidence gap，不允许修改 Runtime Gate 来强行通过。

### AC-05 — Offline execution + authoritative trace continuity

使用 caller-supplied offline facts：

- payment status=`SUCCEEDED`；
- fulfillment status=`SUCCEEDED`；
- payment.request_id == same Commerce request；
- payment.order_id == same Commerce order；
- fulfillment.order_id == same Commerce order；
- `assess_webshop_payment_fulfilment` ready=true；
- authoritative trace validation=`VALID`；
- trace 中 Order/Request/Payment refs 与本 journey 一致；
- H-13 projection 覆盖 `USER_AUTHORITY / AGENT_DECISION / RUNTIME_DECISION / EXTERNAL_FACT / EXECUTION_RESULT`。

这仍是 offline synthetic execution evidence，不得表述为真实付款/真实履约。

### AC-06 — 8/8 correlations + fail-closed guardrails

Frozen `same_journey_result_audit.py` 必须 PASS：

- `C01..C08 = 8/8`；
- 每条两端 value 相同且 evidence paths 非空；
- evaluator negative control 修改任一 correlation target 后必须被拒绝；
- external network calls=`0`；
- real WebShop Buy Now=`0`；
- real payment execution=`0`；
- real fulfillment execution=`0`；
- instruction 不得升级成 authorization；
- experiment context 不得升级成 WebShop fact。

### AC-07 — Existing project guardrails unchanged

- H-13 Action Origin tests PASS；
- WebShop Adapter PASS；
- Runtime Gate PASS；
- Payment Sidecar PASS；
- `run_experiment.py` PASS；
- project impact baseline repeat=3 一致；
- Product Trace / GESR / callback / duplicate / forbidden-side-effect 指标不退化；
- full unittest 无新增失败。

### AC-08 — v2.2 evidence handoff

- frozen Validation Plan `7/7` mandatory checks PASS，或如实记录失败断点；
- REPORT.md 映射 AC-01..08 → EV；
- Impact comparison 必须记录：
  - Before: same-journey required correlation `0/8`；
  - After: 实测值；
  - Delta；
  - Guardrail result；
  - Scope caveat；
- Executor status 只能为 `SUBMITTED_FOR_REVIEW` 或 `BLOCKED`；不得自行签发 PASS。

## Allowed scope / 允许范围

Executor 只允许新增/修改：

- `scripts/validation/webshop/run_same_journey_responsibility.py`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_RESPONSIBILITY_CORRELATION_V1/REPORT.md`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_RESPONSIBILITY_CORRELATION_V1/evidence/**`

Evaluator-owned Contract / Validation Plan / evaluator fixtures / evaluator checks 不得修改。

## Exclusions / 明确排除

禁止：

- 修改 `webshop_agent_behavior.py` 或任何 H-15 intent/option tuning；
- 修改 `action_origin.py`；
- 修改 WebShop Adapter；
- 修改 Runtime Gate；
- 修改 Payment/Fulfillment Sidecar；
- 修改 Authoritative Trace schema / consumer；
- 修改 accepted autonomous evidence；
- 修改 evaluator fixture/checker/plan；
- 执行 real `click[buy now]`；
- 执行真实 payment/order/fulfillment；
- 外部 API/network；
- 安装依赖、创建/修改环境；
- 把 instruction 当 authorization；
- 把 offline callback 当真实购买；
- 把 synthetic payment/fulfillment 当真实执行；
- commit / push / history rewrite。

## Bounded execution / 有界执行

这不是开放式实现任务。

- 最多 `2` 次完整 H-16 runner→L2 cycle；
- 允许修 runner 自身的机械 bug；
- 不允许为了通过而改任何 protected product module；
- 第一次发现真实组件合同断点时，可以在第二 cycle 仅验证是否是 runner 使用错误；
- 若第二次仍是产品合同断点，停止并 `BLOCKED`，由 Evaluator 决定是否升级新 capability package。

## Stop conditions / 停止条件

出现以下任一情况停止：

- accepted replay trace 无法复现；
- 需要修改 Agent policy；
- candidate 无法从同一 runtime/session 导出；
- 现有 Adapter / Runtime Gate / Sidecar 合同无法在不改产品的前提下连续绑定；
- 需要伪造 session/order/request/payment correlation；
- 需要把 instruction 升级为 mandate；
- 需要真实 Buy Now/payment/fulfillment；
- 需要网络/API/依赖/环境修改；
- 任一 protected hash 改变；
- 2 个完整 cycle 用尽。

## Authorization / 授权

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- environment_creation: false
- local_WebShop_replay: true
- real_Buy_Now: false
- real_payment_or_order: false
- real_fulfillment: false

## Executor instructions / 执行者说明

```text
read CURRENT / Contract / Validation Plan / evaluator fixture / evaluator checks
→ 新增一个 integration-only runner
→ goal10 same replay ×2
→ same runtime candidate
→ existing Adapter
→ existing Runtime Gate with injected local seam
→ existing offline Payment Sidecar
→ VALID trace + H-13 Action Origin
→ SAME_JOURNEY_RESULT.json
→ frozen L2 7/7
→ REPORT.md
→ workflow validator
→ SUBMITTED_FOR_REVIEW / BLOCKED
```

不要重新设计任务，也不要回头修 WebShop 意图识别。

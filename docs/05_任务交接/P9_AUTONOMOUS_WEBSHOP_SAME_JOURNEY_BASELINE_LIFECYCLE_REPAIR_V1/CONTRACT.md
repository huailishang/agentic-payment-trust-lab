# Frozen Task Contract

Task ID: `P9-AUTONOMOUS-WEBSHOP-SAME-JOURNEY-BASELINE-LIFECYCLE-REPAIR-V1`  
Task name: Same-Journey Baseline Lifecycle Repair + Correlation Retry  
Task kind: `one_off`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `57ded7bb2fb0ca830748b35b857a8d07624fe3d4`  
Validation plan file: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_BASELINE_LIFECYCLE_REPAIR_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-06-r27`  
Active bottleneck: `B-11`  
Hypothesis: `H-17`

H-16 已由 Executor L2 与 Evaluator L3 独立复现为 `REJECTED / INCONCLUSIVE / SWITCH`：两个 Gate 都在 C01 失败，原因不是下游支付信任组件，而是 historical H-11 accepted trace 属于旧 policy SHA `af2a8530...`，当前 protected policy 已演进到 `6133eaac...`。最终商品/规格/价格仍一致，但完整 action / observation trace 已变化。

因此当前 principal change（主要变化）不是产品代码，而是 **measurement contract（测量合同）**：把“历史行为回归”和“当前 policy 的可重复 identity”分开，禁止跨 policy 版本要求 byte-identical full trace。

## Measurement basis / 测量基础

### Historical behavior regression（历史行为回归）

- H-11 accepted evidence SHA: `cb11bdc27e514118c8e9ae69384be16d188ec08bba7c1d4514d6b3c50e316dd0`
- historical policy SHA: `af2a8530c661709c35a806f4074c38691ba9718f63d2f4d3aa8a2f5d2aa61189`
- historical trace SHA: `8c0a03b2f2e5dd9dce051ce176c546e2e171b5e7eacfdb36b258ba04dddd5897`
- role: only final behavior + safety regression；不再作为 current policy byte-level identity。

### Current-policy reproducibility identity（当前策略可重复身份）

Evaluator 已在冻结前使用当前 protected policy 独立 replay 3 次：

- current policy SHA: `6133eaac32d2c806028d6ecdd9ab4887f45eb4a2a63e0bc8a5cc63331d4ddd5f`
- autonomous driver SHA: `8c3b1b893449502dd2096cc86ac5b6ada693468667acde10f1c01c2064109a40`
- checkout HEAD: `64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd`
- baseline file SHA: `cdbece32497a4935ecd8048d8e83c5c26105d393657dfa6a645950e815ca234d`
- current trace SHA: `b99e99e8be4ffa43c744375deec287130e0cee0275a07a4d1de34ed11a6187a5`
- repeat=`3`, repeat_identical=`true`
- goal=`10`, seed=`20260823`
- result=`B099231V35 / orange / 16.79`
- Buy Now / purchase / payment-order-network side effect=`0`

Frozen metadata: `evaluator_baseline/BASELINE_LIFECYCLE.json`。

## Single objective / 单一目标

在**不修改任何 protected product module** 的前提下，使用 current-policy baseline 重跑 existing H-16 same-journey runner，完成：

```text
Historical H-11 evidence
→ 只做最终行为 / 安全回归

Current policy baseline
→ C01 current replay identity
→ C02 session → candidate
→ C03 instruction/actions → candidate
→ C04 product/options → Order
→ C05 Order → Request
→ C06 Request → Runtime Gate
→ C07 Order/Request → offline Payment/Fulfillment
→ C08 same refs → VALID Trace + five Action Origin classes
```

本任务不新增产品能力。如果 current-policy C01 通过后在 C02..C08 暴露真实断点，Executor 只记录第一个真实断点，不在本包修改产品。

## Acceptance criteria / 验收标准

### AC-01 — Baseline lifecycle separation

Frozen `baseline_lifecycle_audit.py` 必须 PASS：

- historical policy SHA != current policy SHA；
- historical trace SHA != current trace SHA 是允许且预期的；
- historical final ASIN/options/price 与 current baseline 一致；
- current baseline 3 次 trace 完全一致；
- current baseline zero real side effect；
- same-journey correlation 明确使用 current baseline。

### AC-02 — Protected snapshot remains frozen

- current policy SHA=`6133eaac...`；
- autonomous driver SHA=`8c3b1b89...`；
- existing H-16 same-journey runner 不修改；
- H-13 Action Origin / Adapter / Runtime Gate / Sidecar / Authoritative Trace 不修改；
- evaluator baseline / fixture / checks / plan 不修改。

### AC-03 — Current replay identity

existing same-journey runner 使用 `CURRENT_POLICY_AUTONOMOUS_BEHAVIOR.json`：

- goal 10 / seed 20260823 / repeat=2；
- replay repeat identical；
- replay trace SHA=`b99e99e8...`；
- matches current-policy accepted baseline；
- final result 仍为 `B099231V35 / orange / 16.79`；
- real Buy Now / purchase count=`0`。

历史 H-11 trace `8c0a...` 不参与 AC-03 equality。

### AC-04 — Same runtime/session candidate continuity

Candidate 必须来自 AC-03 同一次 runtime/session：session / instruction / actions / ASIN / options / price 全部一致，不得使用历史 Commerce fixture 的商品/session/actions。

### AC-05 — Commerce + Runtime continuity

- existing Adapter ready=true；
- replay product/options → same Order；
- Order.order_id == TransactionRequest.order_ref；
- same request/order 进入 existing Runtime Gate；
- explicit evaluator authority/context 独立于 natural-language instruction；
- offline callback seam count=1；
- real WebShop Buy Now=false。

### AC-06 — Execution + Trace continuity

- same request/order → caller-supplied offline PaymentExecutionRecord / FulfillmentRecord；
- sidecar ready=true；
- authoritative trace validation=`VALID`；
- C01..C08 exactly `8/8`；
- five Action Origin classes 全部覆盖；
- tampered correlation negative control fail closed；
- real payment / fulfillment / external network=`0`。

### AC-07 — Existing project guardrails unchanged

- focused H-13/Adapter/Runtime/Sidecar regressions PASS；
- formal experiment entrypoint PASS；
- project-impact repeat=3 一致；
- Product Trace/GESR/callback/duplicate/forbidden side-effect 不退化；
- full unittest 无新增失败。

### AC-08 — v2.2 handoff

- frozen L2 `8/8` mandatory checks PASS，或如实记录第一个真实断点；
- REPORT 映射 AC-01..08 → EV；
- Impact comparison 写明：
  - Before: H-16 `0/8` because stale cross-policy C01；
  - After: H-17 observed current-policy C01..C08；
  - Delta；
  - Guardrail result；
  - Scope caveat；
- Executor status 只能是 `SUBMITTED_FOR_REVIEW` 或 `BLOCKED`。

## Allowed scope / 允许范围

Executor 只允许新增/修改：

- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_BASELINE_LIFECYCLE_REPAIR_V1/REPORT.md`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_BASELINE_LIFECYCLE_REPAIR_V1/evidence/**`

本包**不允许修改任何 product / runner / evaluator-owned artifact**。

## Exclusions / 明确排除

禁止：

- 修改 `webshop_agent_behavior.py`；
- 修改 `run_autonomous_prebuy_behavior.py`；
- 修改 `run_same_journey_responsibility.py`；
- 修改 Action Origin / Adapter / Runtime Gate / Payment Sidecar / Authoritative Trace / Consumer；
- 修改 historical H-11 evidence；
- 修改 current-policy evaluator baseline；
- 修改 evaluator fixture/checkers/plan；
- 用 historical trace SHA 重新要求 current policy byte identity；
- 把 natural-language instruction 当 authorization；
- real Buy Now / payment / order / fulfillment；
- external API/network；
- dependency/environment mutation；
- commit / push / history rewrite。

## Bounded execution / 有界执行

- 最多 `1` 个完整 runner→L2 cycle；
- 因为本包不允许产品/runner 修改，不允许“多跑直到通过”；
- 如果 VP-01/02 失败，立即 BLOCKED；
- 如果 current C01 通过但 C02..C08 失败，保留第一个真实断点并 BLOCKED；
- 不得在本包修断点。

## Stop conditions / 停止条件

出现以下任一项停止：

- current policy / driver / baseline / checkout hash 漂移；
- current baseline replay 不能复现；
- historical final behavior regression 不再成立；
- existing runner 需要修改；
- 任一 protected product module 需要修改；
- 需要伪造 correlation；
- 需要真实交易副作用或外部网络；
- frozen L2 出现 mandatory failure。

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
read CURRENT / Contract / Validation Plan
→ 不改任何代码
→ VP-01 baseline lifecycle
→ VP-02 protected source audit
→ existing same-journey runner with current-policy baseline
→ result audit C01..C08
→ regressions
→ L2 8/8
→ REPORT
→ workflow validator
→ SUBMITTED_FOR_REVIEW / BLOCKED
```

# Frozen Task Contract

Task ID: `P9-AUTONOMOUS-WEBSHOP-PREBUY-BEHAVIOR-CAPTURE-V1`  
Task name: Autonomous WebShop pre-Buy-Now behavior capture  
Task kind: `capability_experiment`  
Risk: `L1`  
Contract state: `CONTRACT_FROZEN` with `Amendment A1`  
Branch: `main`  
Baseline HEAD: `a9d02f9dbe3dd1ca580a8c4ac278151081a281be`  
Pre-existing changes: Evaluator-owned Journey Player reviews/evidence、accepted-input repair implementation/report/review、project-map r17 与 CURRENT routing；全部保留，不得重写、删除或重新归因。

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-24-r18`  
Active bottleneck: `B-04`  
Hypothesis: `H-11`  
Measurement status: unmeasured autonomous behavior  
Metric baseline: autonomous pre-Buy-Now Journey captured/scored `0/1`；autonomous target product + required option match `0/1`；Journey UI-ready `1/1`；Product Trace `9/12`；GESR `8/12`；callback match `12/12`；duplicate/forbidden side effect `0/12`。  
Estimated affected scope: 一个受限 policy、一个真实本地 WebShop driver、一个结果 validator 及专项测试。  
Expected project impact: autonomous pre-Buy-Now Journey captured/scored `0/1 -> 1/1` 且 target/required-option match `0/1 -> 1/1`，既有守护指标不变。  
Rollback condition: hidden truth 泄漏、单任务硬编码、执行 Buy Now、产生购买/支付/订单副作用、三次结果不一致或既有指标退化。

## Single objective

在已冻结的本地 WebShop small/1k runtime 中，用 deterministic local policy(确定性本地策略)只根据用户 instruction、当前 text observation、available actions 与自身有界历史，自主完成 search、商品选择和 orange 选项选择，停在 Buy Now 前，并输出可独立复核的 `AUTONOMOUS_AGENT` 行为轨迹与事后评分。

## Frozen environment and truth boundary

- Checkout: `local_sources/third_party/webshop`，不得修改其 tracked files。
- Runtime: `<LOCAL_SOFTWARE>\Anaconda\workspace\.conda\envs\webshop38\python.exe`，复用现有环境，不安装依赖、不改环境。
- Environment: `WebAgentTextEnv-v0`，`observation_mode=text`，`num_products=1000`，human goals。
- Deterministic selector: fresh environment per run，seed `20260823`，`reset(session=10)`，对应 fixed-shuffle runtime goal index `10`。
- Evaluator truth: expected ASIN `B099231V35`；required option value `orange`；冻结 target price `$16.79`。这些值只允许出现在 CONTRACT、VALIDATION_PLAN、测试、Evaluator procedure 或运行结束后的 scorer 输入中。
- Selector preflight: checkout HEAD `64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd`；Evaluator 独立 probe 观察到 index `2`=`B07S7HDC88` black loafers，index `10`=`B099231V35` orange cargo pants；两次 reset 的 purchase count 均为 `0`。
- Policy input fields must be exactly: `instruction_text`、`observation`、`available_actions`、`step_index`、`previous_actions`。
- Policy must never receive or read: goal object/index、expected ASIN/option/price、server、product dict、user session、reward target、evaluator labels or result score。
- Runtime driver 可在 policy 停止后进入独立 `score_after_stop` 阶段读取 scorer CLI truth；不得把 truth 传入 policy 或用于 action selection。

## Acceptance criteria

### AC-01 — Autonomous policy boundary

- Type: mandatory anti-cheating boundary。
- Given: a policy decision request during the real runtime。
- When: an action is selected。
- Must observe: decision derives only from the five frozen policy input fields；production policy source contains no target ASIN、old fixed-smoke product/search literal、server/goal/evaluator access or complete hard-coded action sequence。
- Must not observe: hidden truth、runtime internals or post-run scorer values influencing an action。
- Evidence required: dedicated tests plus frozen Evaluator source-boundary audit。
- Mandatory: yes。

### AC-02 — Real autonomous pre-Buy-Now behavior

- Type: mandatory capability behavior。
- Given: fresh real local `WebAgentTextEnv-v0` small/1k run at seed `20260823`, session/fixed-shuffle goal index `10`。
- When: the policy acts from reset until its bounded stop condition。
- Must observe: at least one dynamic `search[...]`、a product `click[asin]`、required option selection including `orange`、selected ASIN `B099231V35`、selected price `$16.79` and Buy Now available before stopping。
- Must not observe: replaying the old fixed script、selecting its console table、or claiming success without environment steps。
- Evidence required: real runtime JSON and independent post-run audit。
- Mandatory: yes。

### AC-03 — Structured autonomous trace and determinism

- Type: mandatory evidence contract。
- Given: three fresh runs with the same frozen seed and goal selector。
- When: normalized traces are compared after excluding explicitly named session/runtime timing fields。
- Must observe: schema `webshop-autonomous-prebuy-behavior/v1`；trace type `AUTONOMOUS_AGENT`；policy type `DETERMINISTIC_LOCAL_POLICY`；`no_llm=true`；every step records sequence、observation SHA-256、available actions、chosen action、short reason summary、reward/done and source；three normalized hashes and scores are identical。
- Must not observe: hidden chain-of-thought、timestamp/local-path dependence or a fixed-script trace mislabeled as autonomous。
- Evidence required: dedicated tests、runtime JSON、product validator and frozen Evaluator audit。
- Mandatory: yes。

### AC-04 — Pre-purchase side-effect boundary

- Type: mandatory safety boundary。
- Given: target product and required option are selected and Buy Now becomes available。
- When: the policy reaches its stop condition。
- Must observe: `buy_now_available=true`、`buy_now_executed=false`、purchase count `0` for every repeat；no payment/order/network callback is invoked。
- Must not observe: `click[buy now]` in any chosen action or a completed purchase/order/payment side effect。
- Evidence required: runtime JSON and independent post-run audit。
- Mandatory: yes。

### AC-05 — Existing project guardrails

- Type: mandatory regression guard。
- Given: the new autonomous behavior slice。
- When: related Journey tests、formal entrypoint and project-impact repeat=3 run。
- Must observe: Journey Player/Read Model regressions pass；formal entrypoint `13/13`；project-impact identical；Product Trace `9/12`；GESR `8/12`；callback match `12/12`；duplicate/forbidden side effect `0/12`。
- Must not observe: changes to Journey Player/Read Model、payment producers/gates、fixtures or accepted evidence from earlier tasks。
- Evidence required: VP-04..06 and changed-file snapshot。
- Mandatory: yes。

### AC-06 — v2.2 handoff gate

- Type: mandatory workflow gate。
- Given: frozen contract and `VALIDATION_PLAN.yaml`。
- When: Executor finishes implementation and prepares `REPORT.md`。
- Must observe: all six mandatory VP checks pass in L2；REPORT maps AC-01..06 and cites evidence triplets/result JSON；workflow validator returns OK before `SUBMITTED_FOR_REVIEW`。
- Must not observe: Executor self-issuing final PASS/IMPROVED or changing CURRENT to Evaluator ownership。
- Evidence required: L2 gate、REPORT、EV triplets and workflow validator output。
- Mandatory: yes。

## Allowed scope

- May add: `src/agentic_payment_experiment/webshop_agent_behavior.py`。
- May add: `scripts/validation/webshop/run_autonomous_prebuy_behavior.py`。
- May add: `scripts/validation/webshop/validate_autonomous_prebuy_behavior.py`。
- May add: `tests/test_webshop_agent_behavior.py`。
- May add: this task's `REPORT.md`、saved diff、`evidence/EV-*`、runtime result、`L2-GATE.json/.md`。
- Runtime driver must remain Python 3.8 compatible and must not import the Python 3.12-only main package. Policy logic may be loaded through a narrow compatible module boundary or implemented in a Python 3.8-compatible product module.
- Before importing WebShop/Pyserini, the runtime driver must derive the existing environment-local JVM from `sys.prefix/Library/lib/jvm`, set process-local `JAVA_HOME` and prepend its `bin` to process-local `PATH`; this is runtime routing only and must not mutate the Conda environment.
- Policy API must expose `choose_webshop_action(state: AgentPolicyInput) -> AgentPolicyDecision` and keep the five input fields frozen above.
- Reason summaries must be short observable justifications, not private chain-of-thought.

## Exclusions and forbidden side effects

- Must not modify: `local_sources/third_party/webshop/**`、existing Journey/Trace/payment product files、fixtures、prior task reports/reviews/evidence、project map、CURRENT、this CONTRACT/VALIDATION_PLAN or `evaluator_checks/**`。
- Must not use: LLM/API/network/browser automation、hidden goal/server/product internals for action selection、target ASIN/complete action hardcoding、dependency install or environment creation。
- Must not execute: `click[buy now]`、checkout completion、payment、order、wallet、fulfilment、production/testnet or external callback。
- Must not commit、push、reset、clean or rewrite history。

## Validation plan

Validation plan file: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_PREBUY_BEHAVIOR_CAPTURE_V1/VALIDATION_PLAN.yaml`

| VP | Observable check | Expected result | AC |
|---|---|---|---|
| VP-01 | dedicated policy tests；Evaluator substitutes frozen source-boundary audit | policy boundary and unit behavior PASS | AC-01,03,06 |
| VP-02 | real WebShop runtime repeat=3 | target/option selected；Buy Now available but not executed；identical | AC-02,03,04 |
| VP-03 | product result validator；Evaluator substitutes frozen independent result audit | schema/truth/trace/side-effect assertions PASS | AC-02,03,04 |
| VP-04 | Journey Player + Journey Read Model regressions | all pass | AC-05 |
| VP-05 | formal entrypoint | 13/13 PASS | AC-05 |
| VP-06 | project-impact repeat=3 | identical and frozen metrics unchanged | AC-05 |

## Authorization

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- environment_creation: false
- WebShop_runtime_execution: true
- Buy_Now_execution: false
- payment_or_order_side_effect: false

## Stop conditions

- Existing checkout/runtime hashes or required goal index no longer match the accepted local baseline。
- Baseline dedicated/related validation fails for an unrelated reason that prevents trustworthy comparison。
- Policy requires hidden truth, task-specific target literals or an excluded file。
- Runtime cannot stop before Buy Now or cannot prove zero purchase side effects。
- Work requires a false authorization flag to become true。
- The objective expands to multiple goals, LLM policy, payment execution or Journey UI integration。
- Frozen Validation Plan no longer represents the intended acceptance semantics。

## Amendments

### Amendment A1 — Correct fixed-shuffle runtime selector

- Date: `2026-08-24`。
- Owner: Evaluator。
- Reason: the original contract confused a source-data position with WebShop's fixed-shuffle runtime index。Independent runtime reset confirmed index `2` is `B07S7HDC88` black loafers, while index `10` is the frozen `B099231V35` orange cargo-pants task。
- Changes: map revision `r17 -> r18`；all task runtime selector semantics `session/goal index 2 -> 10`；Evaluator result audit expectation `2 -> 10`；process-local JVM bootstrap requirement made explicit。
- Unchanged: task ID、objective、target ASIN/option/price、policy truth boundary、allowed product scope、six ACs、side-effect prohibitions、authorization and before/after metrics。
- Lifecycle: no implementation、REPORT or L2 evidence existed when A1 was frozen, so the same task returns directly to `CONTRACT_FROZEN / Executor` without a repair round。

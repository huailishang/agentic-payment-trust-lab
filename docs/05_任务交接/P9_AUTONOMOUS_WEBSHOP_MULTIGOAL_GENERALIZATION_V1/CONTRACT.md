# Frozen Task Contract

Task ID: `P9-AUTONOMOUS-WEBSHOP-MULTIGOAL-GENERALIZATION-V1`  
Task name: Autonomous WebShop multi-goal generalization  
Task kind: `capability_experiment`  
Risk: `L1`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `57ded7bb2fb0ca830748b35b857a8d07624fe3d4`

## Inherited uncommitted baseline

The previous H-11 task was accepted without an implementation commit. This task therefore inherits the accepted product snapshot rather than pretending HEAD alone contains it.

Frozen inherited product hashes:

| File | Baseline SHA-256 |
|---|---|
| `src/agentic_payment_experiment/webshop_agent_behavior.py` | `af2a8530c661709c35a806f4074c38691ba9718f63d2f4d3aa8a2f5d2aa61189` |
| `scripts/validation/webshop/run_autonomous_prebuy_behavior.py` | `8c3b1b893449502dd2096cc86ac5b6ada693468667acde10f1c01c2064109a40` |
| `scripts/validation/webshop/validate_autonomous_prebuy_behavior.py` | `182342b50b038759030ed0faa92ebbfd7f37ab71bb9c442a58b1a168c16127d7` |
| `tests/test_webshop_agent_behavior.py` | `f1b7956528f486d20967a3a4618e7ab159f5fe0a1d7076b9a8b9f4f87a7a2dbf` |

The H-11 `REPORT.md`, `REVIEW.md`, L2/L3 evidence, Evaluator-owned project-map/current-control changes and reference-doc changes are inherited governance/evidence state. Executor must preserve them and must not reattribute them to H-12.

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-02-r19`  
Active bottleneck: `B-04`  
Hypothesis: `H-12`  
Measurement status: measured multi-goal generalization gap  
Metric baseline: frozen five-goal target + required-option match `3/5` with goals 0/9/10 PASS and goals 2/7 FAIL; each baseline goal was independently rerun with `repeat_per_goal=2`.  
Estimated affected scope: one existing deterministic policy module plus its dedicated unit tests. Existing runtime driver, result validator, WebShop upstream, Journey/Trace/payment chain and evaluator checks are frozen.  
Expected project impact: same five-goal metric `3/5 -> 5/5`, all required options present, same policy boundary and zero Buy Now/payment/order side effects; old Product Trace/GESR/callback guardrails unchanged.  
Rollback condition: target-specific literals/goal-index branching/hidden truth enter the policy; five-goal result remains below 5/5; existing driver/validator/payment chain must be changed; or any guardrail regresses.

## Single objective

Generalize the existing `choose_webshop_action(state)` policy so that **one instruction-grounded visible-choice matching / ranking rule family** correctly handles the five frozen WebShop goals `0 / 2 / 7 / 9 / 10`.

The task is not “fix goal 2 and goal 7 separately”. The same policy must use only:

```text
instruction_text
+ observation
+ available_actions
+ step_index
+ previous_actions
```

to improve both:

```text
search-result product ranking
+
required-option matching
```

and stop before Buy Now.

## Frozen environment and evaluator truth boundary

- Checkout: `local_sources/third_party/webshop`; tracked upstream files are immutable.
- Runtime: existing `python3` / Python 3.8.13.
- Environment: `WebAgentTextEnv-v0`, text observation, `num_products=1000`, human goals.
- Seed: `20260823`.
- Five frozen goal indices: `0 / 2 / 7 / 9 / 10`.
- The following target truth is **Evaluator / scorer truth only** and may exist only in this Contract, frozen evaluator checks, tests that explicitly exercise checker boundaries, or post-run score evidence. It must not enter production policy logic.

| Goal | Expected ASIN | Required option values | Expected runtime price |
|---:|---|---|---:|
| 0 | `B09MW563KN` | `blue` | 22.90 |
| 2 | `B07S7HDC88` | `black1901`, `10.5` | 35.421970457880775 |
| 7 | `B09HX5CD2D` | `heather charcoal`, `small` | 39.95 |
| 9 | `B09KP78G37` | `red`, `x-large` | 55.69454800459104 |
| 10 | `B099231V35` | `orange` | 16.79 |

- Policy input fields remain exactly: `instruction_text`, `observation`, `available_actions`, `step_index`, `previous_actions`.
- Policy must never receive/read goal object/index, expected ASIN/options/price, server, product dict, evaluator labels, reward target, local WebShop data files or scorer result.
- The existing runtime driver may read scorer truth only after policy stop, exactly as accepted under H-11.

## Acceptance criteria

### AC-01 — Generalization source boundary / anti-overfit

- Mandatory.
- Production policy keeps exactly the five frozen input fields.
- No target ASIN from the five-goal set appears in production policy.
- No `goal_index` / `goal_idx` branch, server/user-session/product-data access, evaluator truth or local WebShop data import is allowed.
- Current hard cases must not be patched with target-specific literals such as `black1901`, `heather charcoal`, target product names or complete fixed action sequences.
- Frozen `policy_generalization_source_audit.py` must PASS.

### AC-02 — Five-goal target product generalization

- Mandatory capability criterion.
- Frozen `multigoal_runtime_audit.py` runs goals 0/2/7/9/10 with `repeat_per_goal=2`.
- All five cases must select the expected target ASIN.
- Same-baseline comparison must move from `3/5 -> 5/5`.
- Each real run must contain a runtime-generated `search[...]` and target product `click[asin]`.

### AC-03 — Required option completion and deterministic trace

- Mandatory.
- Every case must end with all frozen required option values present in the runtime-selected options.
- Each goal's two normalized traces must be identical.
- Existing `AUTONOMOUS_AGENT`, `DETERMINISTIC_LOCAL_POLICY`, `no_llm=true` and five-field declaration remain unchanged.
- Goal 10 accepted H-11 behavior must not regress.

### AC-04 — Pre-purchase safety boundary

- Mandatory.
- Every run reaches a state where Buy Now is available but does not execute `click[buy now]`.
- `buy_now_executed=false`, purchase count=0 and payment/order/network side-effect count=0 for every goal/repeat.
- No retry, callback, payment, order, wallet or fulfilment side effect is introduced.

### AC-05 — One principal change / frozen surrounding chain

- Mandatory scope criterion.
- Product behavior changes are limited to the existing policy module and its dedicated unit tests.
- Existing `run_autonomous_prebuy_behavior.py`, `validate_autonomous_prebuy_behavior.py`, WebShop upstream, Journey/Trace/payment product files, fixtures and evaluator checks remain byte-identical to the frozen baseline unless the task stops for Evaluator decision.
- The implementation must be explainable as one generalized visible-choice matching/ranking rule family, not per-goal patches.

### AC-06 — Existing project guardrails

- Mandatory regression criterion.
- Journey Player / Read Model focused regression passes.
- Formal `run_experiment.py` remains `13/13 PASS`.
- Full unittest discovery has zero new failures.
- Project-impact repeat=3 remains deterministic with Product Trace `9/12`, GESR `8/12`, callback match `12/12`, duplicate/forbidden side effect `0/12`.

### AC-07 — v2.2 handoff gate

- Mandatory workflow criterion.
- Executor runs the frozen `VALIDATION_PLAN.yaml` as L2 and all mandatory VP checks PASS.
- `REPORT.md` maps AC-01..07 to EV evidence and records before/after `3/5 -> 5/5`.
- Workflow validator returns OK before submission.
- Executor submits but does not self-issue `PASS` or `IMPROVED`; `CURRENT.md` remains Executor-owned until Evaluator accepts the unchanged snapshot.

## Allowed scope

Executor may modify only:

- `src/agentic_payment_experiment/webshop_agent_behavior.py`
- `tests/test_webshop_agent_behavior.py`
- this task's `REPORT.md`
- this task's generated `evidence/EV-*`, `L2-GATE.json/.md` and saved task diff/snapshot

Executor may read all repository files needed to understand existing behavior, but the implementation itself must stay within the two product/test files above.

## Frozen evaluator-owned files

Executor must not modify:

- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_MULTIGOAL_GENERALIZATION_V1/CONTRACT.md`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_MULTIGOAL_GENERALIZATION_V1/VALIDATION_PLAN.yaml`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_MULTIGOAL_GENERALIZATION_V1/evaluator_checks/**`
- `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`
- `CURRENT.md`
- prior task reports/reviews/evidence

## Exclusions and forbidden side effects

- No modification of `local_sources/third_party/webshop/**`.
- No modification of existing WebShop runtime driver/result validator.
- No modification of payment, Runtime Gate, Journey, Trace, protocol or x402 implementation.
- No LLM/API/network/browser automation.
- No hidden goal/server/product internals for action selection.
- No dependency install or environment creation.
- No Buy Now execution, checkout completion, payment, order, wallet, fulfilment, testnet, production or external callback.
- No commit, push, reset, clean or history rewrite.

## Validation plan

Validation plan file:

`docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_MULTIGOAL_GENERALIZATION_V1/VALIDATION_PLAN.yaml`

| VP | Observable check | Expected result | AC |
|---|---|---|---|
| VP-01 | dedicated policy unit tests | PASS | AC-01,03,05 |
| VP-02 | frozen five-goal real WebShop audit, repeat=2 per goal | `5/5 PASS`; zero Buy Now/side effects | AC-02,03,04 |
| VP-03 | frozen Evaluator source-boundary audit | PASS | AC-01,05 |
| VP-04 | Journey Player + Journey Read Model regression | PASS | AC-06 |
| VP-05 | formal entrypoint | `13/13 PASS` | AC-06 |
| VP-06 | project-impact repeat=3 | frozen metrics unchanged | AC-06 |
| VP-07 | full unittest discovery | zero failures | AC-06 |

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

Stop and return to Evaluator instead of broadening the implementation if:

- the frozen five-goal truth or WebShop runtime no longer matches the accepted local baseline;
- achieving 5/5 requires a target ASIN, goal-index branch, target product name/special option hardcode or hidden truth;
- achieving 5/5 appears to require changing the existing driver/validator, WebShop upstream or payment/Trace/Journey chain;
- the requested principal change naturally splits into unrelated per-goal patches;
- any run crosses Buy Now or creates purchase/payment/order/network side effects;
- a false authorization flag must become true;
- frozen Validation Plan semantics need to change.

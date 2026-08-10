# Frozen Task Contract

Task ID: `P9-WEBSHOP-JOURNEY-PLAYER-V1`  
Task name: WebShop Journey Player V1  
Task kind: `capability_experiment`  
Risk: `L1`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `c18a24066973b3fb33742a0c5c59a0bd8a35e1ae`  
Pre-existing changes: accepted but uncommitted Consumer / Trace Player / Journey Read Model / reviews / evidence and project-map governance artifacts; preserve them and do not re-attribute them.

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-10-r15`  
Active bottleneck: `B-10`  
Hypothesis: `H-10`  
Measurement status: `measured`  
Metric baseline: `Journey UI-ready representative path=0/1; Journey source-classified=1/1; Trace Player UI-ready=4/4; Product Trace=9/12; GESR=8/12`  
Estimated affected scope: `1 existing fixed-script WebShop/T01 Journey; UI composition contract reusable for later Journey inputs`  
Expected project impact: `Journey UI-ready 0/1 -> 1/1 while Journey source-classified stays 1/1, Trace Player stays 4/4, Product Trace stays 9/12, GESR stays 8/12`  
Rollback condition: `UI flattens or relabels evidence sources; hides instruction/product mismatch; reruns Adapter/payment/WebShop logic; requires task/profile hard-coding; accepted Journey/Consumer/Player/fixture hashes change; or any frozen metric regresses`

## Frozen accepted input

The accepted Journey Read Model implementation is frozen:

```text
src/agentic_payment_experiment/webshop_journey_read_model.py
sha256 = 70d6c19fe7d48d27fc377f943ba53b0db276391f3f48402b66f0a57490d1ba7d

tests/test_webshop_journey_read_model.py
sha256 = 9767c6bb0877d081812bd43d43b2d939f6353bf0d59b56988a02b37a9ccd5263
```

Other accepted boundaries remain frozen:

```text
src/agentic_payment_experiment/authoritative_trace_player.py
sha256 = 9cd38620ee966632191b376f13d95446711ff55d08b18aa844f9a7fb6ef74541

src/agentic_payment_experiment/authoritative_trace_consumer.py
sha256 = 6ad65118a4ab50e648e4f6098f6c2c5009ce5731232ae0a4e11d2f60c0c431b5

samples/external/webshop/pre_buy_now_candidate_v1.json
sha256 = 6e9d67c3b787cc2d9202bd22b30dec88bf9f920dfa3741bdeb364108a2a3c8e5
```

The representative Journey intentionally contains a visible semantic mismatch:

```text
user instruction: orange cargo pants under 30 USD
selected product: Vhomes console table, 877.80 USD
```

The Player must display both faithfully and must not infer or claim that they match.

## Single objective

Build one deterministic, self-contained, read-only HTML Journey Player that consumes only an accepted `WebShopJourneyReadModel` and lets a user inspect the complete fixed-script purchase journey with source-aware evidence sections.

```text
accepted WebShopJourneyReadModel
→ deterministic primitive/payload
→ generic Journey Player HTML
→ instruction + WebShop actions/product + experiment context + Commerce objects + payment authoritative evidence
```

This task does not run WebShop, does not execute Buy Now/payment, and does not implement autonomous Agent behavior.

## Required production shape

Add exactly one production module:

```text
src/agentic_payment_experiment/webshop_journey_player.py
```

Recommended public boundary:

```text
WebShopJourneyReadModel
→ webshop_journey_read_model_to_primitive(...)
→ exact embedded payload
→ self-contained HTML
```

Production code may import Python stdlib plus the accepted generic Journey Read Model module only. It must not import Adapter, Consumer, Trace Player, trace producers, payment logic, Policy, Lineage, runner, evaluator, WebShop runtime, browser/network clients or external dependencies.

## Required UI behavior

Chinese-first fixed labels are preferred. The Player must visibly separate:

```text
1. 用户需求与商城动作 / webshop_runtime
2. 实验补充上下文 / experiment_context
3. Commerce 派生对象 / commerce_adaptation
4. 支付权威证据 / payment_authoritative_trace
5. 跨源关联 / correlations
6. 限制与事实边界 / limitations
```

The page must visibly state:

```text
固定脚本轨迹，不代表自主 Agent
实验补充字段不是 WebShop 核验事实
支付权威轨迹是独立证据源
```

The page must preserve, not hide, the cargo-pants instruction and console-table selected product.

The embedded product-data payload must equal `webshop_journey_read_model_to_primitive(read_model)` exactly. UI-only state may exist outside the payload.

Controls may include previous/next/reset/play-pause or source-section navigation, but all controls must be local-only and must not mutate the payload or call backend/network/business execution.

## Acceptance criteria

### AC-01 — Journey-only input boundary
- Must accept only accepted `WebShopJourneyReadModel` / its generic primitive.
- Must not read fixture/Adapter/trace producer directly.
- Mandatory: yes.

### AC-02 — Exact embedded payload
- Embedded JSON must equal `webshop_journey_read_model_to_primitive(read_model)` exactly.
- No renamed/deleted/enriched product facts.
- Mandatory: yes.

### AC-03 — Four source namespaces visibly separated
- UI must render the four evidence namespaces under distinct fixed labels.
- Must not flatten them into one truth object.
- Mandatory: yes.

### AC-04 — Source semantics preserved
- `experiment_context.origin = explicit_experiment_context_not_webshop_verified` remains visible or mechanically inspectable.
- Page must not label experiment context as WebShop/payment/user verified.
- Mandatory: yes.

### AC-05 — Instruction/product mismatch preserved
- The representative page must show the cargo-pants instruction and the Vhomes console-table product/877.80 amount without claiming match/success against user intent.
- No hidden semantic repair.
- Mandatory: yes.

### AC-06 — Commerce and payment evidence drill-down
- Order/request identifiers and payment authoritative events/source bindings must be inspectable from the Journey payload.
- Correlations must be displayable with source path, target path, values and equality.
- Mandatory: yes.

### AC-07 — Fixed-script boundary explicit
- Page must expose `fixed_script_webshop_smoke_not_autonomous_agent` and a user-facing fixed-script notice.
- It must not display `autonomous Agent completed purchase` or equivalent.
- Mandatory: yes.

### AC-08 — Deterministic rendering
- Same Journey Read Model rendered 3 times must have identical HTML and payload SHA.
- No timestamp/random/local-path/object-repr additions.
- Mandatory: yes.

### AC-09 — Fail closed / safe text rendering
- Wrong input or malformed Journey structure must not produce a normal player.
- Hostile display strings must round-trip exactly while remaining non-executable; use safe text insertion and safe JSON/script boundary.
- Mandatory: yes.

### AC-10 — Generic no-execution production path
- No T01/profile/fixed ID branches.
- No Adapter/Consumer/Trace Player/payment/Policy/Lineage/runner/evaluator/WebShop/network/browser calls.
- Mandatory: yes.

### AC-11 — Existing capability invariance
- Journey source-classified remains 1/1.
- Trace Player 21/21, Journey Read Model 27/27, Consumer 19/19, project-impact 21/21, formal 13/13, repeat=3 stable.
- Product Trace=9/12, GESR=8/12, duplicate/forbidden side effect=0/12, callback match=12/12.
- Frozen accepted hashes unchanged.
- Mandatory: yes.

### AC-12 — Test/workflow gate
- New Journey Player dedicated tests >=18 all pass.
- Full unittest >=623 all pass.
- Workflow validator OK.
- Mandatory: yes.

## Allowed scope

May add:

```text
src/agentic_payment_experiment/webshop_journey_player.py
tests/test_webshop_journey_player.py
```

May modify only this task `REPORT.md` / evidence and `CURRENT.md` from `CONTRACT_FROZEN -> EXECUTING` after work starts.

## Exclusions and forbidden side effects

Must not modify:

```text
webshop_journey_read_model.py
webshop_journey_read_model tests
authoritative_trace_consumer.py
authoritative_trace_player.py
WebShop fixture / Adapter
trace producers/toolkits/profiles
existing UI files
runner / registry / project-impact measurement
prior accepted task artifacts
```

Must not implement autonomous Agent behavior, WebShop runtime replay, Buy Now, browser automation, payment/order/wallet/fulfilment/callback execution, network/API calls, dependency installation, environment creation, commit, push, reset, clean or history rewrite.

## Validation plan

| VP | Exact command / action | Expected | AC |
|---|---|---|---|
| VP-01 | freeze accepted Journey/Player/Consumer/fixture hashes and task-start src manifest | exact match | AC-11 |
| VP-02 | `python3 -m unittest tests.test_webshop_journey_player -v` | >=18 PASS | AC-01..10,12 |
| VP-03 | representative Journey HTML/payload audit | Journey UI-ready 1/1; exact payload/source labels/mismatch/fixed-script evidence | AC-02..09 |
| VP-04 | static/security audit | generic, no execution/network/unsafe HTML | AC-09,10 |
| VP-05 | `python3 -m unittest tests.test_webshop_journey_read_model -v` | 27/27 | AC-11 |
| VP-06 | `python3 -m unittest tests.test_authoritative_trace_player -v` | 21/21 | AC-11 |
| VP-07 | `python3 -m unittest tests.test_authoritative_trace_consumer -v` | 19/19 | AC-11 |
| VP-08 | `python3 -m unittest tests.test_project_impact_baseline -v` | 21/21 | AC-11 |
| VP-09 | project-impact repeat=3 | identical; Product Trace 9/12; GESR 8/12 | AC-11 |
| VP-10 | `python3 run_experiment.py` | 13/13 PASS | AC-11 |
| VP-11 | full unittest discovery | >=623 PASS | AC-12 |
| VP-12 | workflow validator | OK | AC-12 |

## Authorization

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- create_environment: false
- webshop_runtime_execution: false
- buy_now_execution: false
- payment_or_order_side_effect: false

## Stop conditions

- UI requires changing accepted Journey Read Model or existing Player/Consumer.
- UI cannot preserve source classification exactly.
- User instruction/product mismatch would need to be hidden or semantically repaired.
- Journey rendering requires family/task/profile hard-coding.
- External execution/authority is required.
- Any frozen project metric or accepted hash regresses.

## Amendments

None.

# Frozen Task Contract

Task ID: `P9-WEBSHOP-JOURNEY-FACT-SOURCE-READ-MODEL-V1`  
Task name: WebShop Journey Fact Source Read Model V1  
Task kind: `capability_experiment`  
Risk: `L1`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `c18a24066973b3fb33742a0c5c59a0bd8a35e1ae`  
Pre-existing changes: accepted but uncommitted Consumer / Trace Player / reviews / evidence and project-map governance artifacts from the immediately preceding P9 tasks; Executor must preserve them and may not re-attribute them to this task.

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-10-r14`  
Active bottleneck: `B-09`  
Hypothesis: `H-09`  
Measurement status: `measured`  
Metric baseline: `Journey source-classified representative path=0/1; Trace Player UI-ready=4/4; Consumer-ready=4/4; Product Trace=9/12; GESR=8/12; duplicate/forbidden side effect=0/12; callback match=12/12`  
Estimated affected scope: `1 existing fixed-script WebShop smoke / T01 normal-purchase journey; reusable contract for later WebShop journeys`  
Expected project impact: `Journey source-classified representative path 0/1 -> 1/1 while Trace Player UI-ready remains 4/4, Product Trace remains 9/12, GESR remains 8/12, and accepted source/trace/UI boundaries remain unchanged`  
Rollback condition: `source namespaces are merged or mislabeled; experiment context is promoted to WebShop-verified fact; payment fields are reconstructed from WebShop prose; correlation mismatch does not fail closed; accepted Consumer/Player/trace/fixture changes; or any frozen project metric regresses`

## Single objective

Build one deterministic, UI-neutral `WebShopJourneyReadModel` for the existing fixed-script T01 normal-purchase path that keeps four evidence namespaces distinct:

```text
webshop_runtime
experiment_context
commerce_adaptation
payment_authoritative_trace
```

The Read Model must preserve each namespace mechanically, expose only verified cross-source correlations, and fail closed when those correlations do not match. This task does **not** build the next UI and does **not** claim autonomous Agent behavior.

## Frozen source boundary

The first representative path is frozen to the existing repository evidence chain:

```text
samples/external/webshop/pre_buy_now_candidate_v1.json
sha256 = 6e9d67c3b787cc2d9202bd22b30dec88bf9f920dfa3741bdeb364108a2a3c8e5

src/agentic_payment_experiment/adapters/webshop.py
sha256 = 035e6bb20d44b0a52be3f6adab2830c402e01f53839e917698343761c5481ec4

src/agentic_payment_experiment/authoritative_trace_consumer.py
sha256 = 6ad65118a4ab50e648e4f6098f6c2c5009ce5731232ae0a4e11d2f60c0c431b5

src/agentic_payment_experiment/authoritative_trace_player.py
sha256 = 9cd38620ee966632191b376f13d95446711ff55d08b18aa844f9a7fb6ef74541
```

The fixture already distinguishes `experiment_context.origin = explicit_experiment_context_not_webshop_verified`. That label is authoritative for this task and must survive unchanged.

The accepted T01 path is derived from the same frozen fixture through the existing Commerce Adapter and accepted Sidecar/Trace chain. The accepted payment Read Model contains, among other evidence, the deterministic order/request refs:

```text
order_id   = webshop-order-9eccab2b0154fca4af27f322
request_id = webshop-request-6c6a78eddffdb552c2af66ef
trace_ref  = ProductAuthoritativeTrace:WEBSHOP_NORMAL_PURCHASE_V2:webshop-request-6c6a78eddffdb552c2af66ef
```

These values are evidence examples for validation; production code must not hard-code T01, the profile name, or these literal IDs.

## Required production shape

Add exactly one production module:

```text
src/agentic_payment_experiment/webshop_journey_read_model.py
```

Recommended public boundary:

```text
frozen decoded WebShop fixture
+ accepted WebShopCommerceAdaptation
+ accepted AuthoritativeTraceReadModel
→ validate source/correlation boundary
→ WebShopJourneyReadModel
→ deterministic primitive / JSON / SHA helpers
```

Production code may use Python stdlib plus existing generic types/helpers from `adapters.webshop` and `authoritative_trace_consumer`. It must not import T01/T02/T07/T10 builders, profile registries, payment execution, Policy, Lineage, runner, evaluator, Trace Player, WebShop runtime, browser/network code or external dependencies.

## Read Model contract

The exact dataclass/function names are implementation-owned, but the public primitive must contain only these top-level evidence namespaces plus generic metadata/correlation status:

```text
schema_version
journey_ref
source_classification_status
correlations[]
webshop_runtime
experiment_context
commerce_adaptation
payment_authoritative_trace
limitations[]
```

### `webshop_runtime`

Must mechanically preserve the frozen fixture's WebShop/runtime-facing facts required for the journey:

```text
session_id
task_identifier
instruction_text
actions_executed
buy_now_available
buy_now_executed
product
source
```

No new search result, observation, reward, done, purchase count or Agent reasoning field may be invented if absent from this frozen fixture.

### `experiment_context`

Must be an exact projection of the fixture's `experiment_context`, including:

```text
origin = explicit_experiment_context_not_webshop_verified
```

It must never be labeled `webshop_verified`, `payment_verified`, `user_confirmed`, or equivalent.

### `commerce_adaptation`

Must mechanically project the accepted `WebShopCommerceAdaptation` without re-running a different adapter path. It must preserve at least:

```text
user_intent_text
order
payment_request
source_commit
fixture_version
source_smoke_sha256
source_asset_hashes
selected_options
experiment_context_origin
missing_fields
unmapped_fields
limitations
ready
```

### `payment_authoritative_trace`

Must be exactly equal to:

```text
trace_read_model_to_primitive(read_model)
```

No enrichment, deletion, renaming, decision recomputation or UI wording belongs in this namespace.

### Correlations

Only mechanically verifiable correlations may be emitted. At minimum prove:

```text
fixture instruction_text == adaptation.user_intent_text
fixture product ASIN/name/amount/quantity -> adaptation order item projection
fixture experiment_context origin == adaptation.experiment_context_origin
adaptation order_id == payment trace Order projection order_id
adaptation payment_request.request_id == payment trace TransactionRequest projection request_id
adaptation payment_request.order_ref == adaptation order.order_id
payment trace trace_ref is bound to the same request_id
```

A correlation record must expose the two paths/refs compared and the equality result. A required mismatch must reject the normal Journey Read Model rather than silently mark it usable.

## Acceptance criteria

### AC-01 — Four namespaces remain separate

- Given: the frozen representative fixture, accepted adaptation and accepted T01 Read Model.
- When: the Journey Read Model is built.
- Must observe: four distinct namespaces `webshop_runtime`, `experiment_context`, `commerce_adaptation`, `payment_authoritative_trace`.
- Must not observe: one flattened truth map or reclassified source labels.
- Evidence required: exact primitive comparison.
- Mandatory: yes.

### AC-02 — WebShop runtime projection is exact

- Given: the frozen fixture.
- When: projected.
- Must observe: session/task/instruction/actions/Buy Now flags/product/source values exactly equal their fixture values.
- Must not observe: invented reward/done/observation/search-result/Agent-reasoning facts.
- Evidence required: field-by-field audit.
- Mandatory: yes.

### AC-03 — Experiment context cannot be promoted

- Given: `experiment_context.origin` in the frozen fixture.
- When: projected.
- Must observe: exact origin `explicit_experiment_context_not_webshop_verified` and exact context values.
- Must not observe: any verified/WebShop/payment/user-confirmed promotion.
- Evidence required: positive and negative tests.
- Mandatory: yes.

### AC-04 — Commerce Adaptation projection is exact

- Given: accepted `WebShopCommerceAdaptation` from the frozen fixture.
- When: projected.
- Must observe: order/request/source/limitations/ready values mechanically preserved.
- Must not observe: a new adaptation or alternative business mapping.
- Evidence required: dataclass/primitive equality audit.
- Mandatory: yes.

### AC-05 — Payment Read Model is exact

- Given: accepted T01 `AuthoritativeTraceReadModel`.
- When: projected.
- Must observe: `payment_authoritative_trace == trace_read_model_to_primitive(read_model)` exactly.
- Must not observe: recomputed payment decision, renamed evidence, lost relations or source bindings.
- Evidence required: exact equality and SHA.
- Mandatory: yes.

### AC-06 — Required cross-source correlations are explicit

- Given: matching fixture/adaptation/payment Read Model.
- When: built.
- Must observe: required session/item/order/request/trace correlations explicitly recorded with source/target paths and equality.
- Must not observe: correlation inferred from profile/task name.
- Evidence required: correlation matrix.
- Mandatory: yes.

### AC-07 — Correlation mismatch fails closed

- Given: independently mutated copies with wrong instruction, ASIN/amount, experiment origin, order ID, request ID or trace request binding.
- When: built.
- Must observe: deterministic rejection/no normal Journey Read Model.
- Must not observe: fallback to mock/manual repair.
- Evidence required: negative matrix with >=10 cases.
- Mandatory: yes.

### AC-08 — Deterministic canonical output

- Given: same valid inputs.
- When: built and serialized 3 times.
- Must observe: identical canonical primitive/JSON/SHA all three times.
- Must not observe: timestamp/random/object repr/local path additions.
- Evidence required: repeat=3 SHA.
- Mandatory: yes.

### AC-09 — Generic production path

- Given: production source.
- When: statically audited.
- Must observe: no `T01`, `WEBSHOP_NORMAL_PURCHASE_V2`, fixed literal order/request IDs, family/profile branches, UI/network/business execution imports/calls.
- Must not observe: WebShop runtime, Buy Now, payment execution, Policy, Lineage, runner/evaluator calls.
- Evidence required: AST/source audit.
- Mandatory: yes.

### AC-10 — Existing capability invariance

- Given: accepted project snapshot.
- When: implementation completes.
- Must observe: Trace Player 21/21, Consumer 19/19, project-impact 21/21, formal entrypoint 13/13, repeat=3 stable, Product Trace=9/12, GESR=8/12, duplicate/forbidden side effect=0/12, callback match=12/12.
- Must not observe: any accepted Consumer/Player/fixture/trace hash change.
- Evidence required: frozen hash audit and regressions.
- Mandatory: yes.

### AC-11 — Test and workflow gate

- Given: completed implementation.
- When: validation runs.
- Must observe: new Journey Read Model dedicated tests >=16 all pass; full unittest >=594 all pass; workflow validator OK.
- Must not observe: skipped mandatory checks.
- Evidence required: raw EV triplets.
- Mandatory: yes.

## Allowed scope

May add:

```text
src/agentic_payment_experiment/webshop_journey_read_model.py
tests/test_webshop_journey_read_model.py
```

May modify only:

```text
this task REPORT.md / evidence/
CURRENT.md only CONTRACT_FROZEN -> EXECUTING after implementation starts
```

## Exclusions and forbidden side effects

Must not implement:

- Journey UI / Player composition;
- autonomous Agent behavior;
- WebShop runtime replay;
- Buy Now execution;
- browser automation;
- LLM reasoning or hidden chain-of-thought display;
- payment/order/wallet/fulfilment/callback execution;
- T05/T06/T11 product-trace work.

Must not modify:

```text
samples/external/webshop/pre_buy_now_candidate_v1.json
src/agentic_payment_experiment/adapters/webshop.py
src/agentic_payment_experiment/authoritative_trace.py
src/agentic_payment_experiment/authoritative_trace_consumer.py
src/agentic_payment_experiment/authoritative_trace_player.py
any trace producer/toolkit/profile
runner / fixture / registry / project-impact measurement code
existing UI files
prior accepted task artifacts
```

Must not call or write externally: network/API, dependency installation, environment creation, WebShop runtime, browser, wallet, testnet, payment/order side effect, commit, push, reset, clean or history rewrite.

## Validation plan

| VP | Exact command or steps | Expected result | AC |
|---|---|---|---|
| VP-01 | freeze task-start src + fixture/adapter/Consumer/Player hashes | accepted snapshot matches contract | AC-10 |
| VP-02 | `python3 -m unittest tests.test_webshop_journey_read_model -v` | >=16 tests, all PASS | AC-01..09, AC-11 |
| VP-03 | dedicated representative audit script using frozen fixture + accepted adaptation + accepted T01 Read Model | Journey source-classified path=1/1; exact namespace/correlation equality | AC-01..08 |
| VP-04 | static AST/source audit | generic path; no profile/task/business/network/UI execution | AC-09 |
| VP-05 | `python3 -m unittest tests.test_authoritative_trace_player -v` | 21/21 PASS | AC-10 |
| VP-06 | `python3 -m unittest tests.test_authoritative_trace_consumer -v` | 19/19 PASS | AC-10 |
| VP-07 | `python3 -m unittest tests.test_project_impact_baseline -v` | 21/21 PASS | AC-10 |
| VP-08 | `python3 scripts/validation/run_project_impact_baseline.py --repeat 3 --output <task evidence>/EV-AFTER-baseline.json` | repeat=3 identical; Product Trace=9/12; GESR=8/12 | AC-10 |
| VP-09 | `python3 run_experiment.py` | 13/13 PASS | AC-10 |
| VP-10 | `python3 -m unittest discover -s tests -p 'test_*.py'` | >=594, all PASS | AC-11 |
| VP-11 | v2.1 workflow validator | OK | AC-11 |

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

- The frozen fixture/adaptation/T01 Read Model cannot be mechanically correlated without family/task/profile hard-coding.
- Required Journey facts are absent and would need to be invented.
- Existing Adapter, Consumer, Player, Trace producer or fixture would need modification.
- Any required source namespace cannot retain its original provenance semantics.
- Product Trace/GESR/Trace Player regress.
- External execution or authority whose flag is false becomes necessary.

## Amendments

None.

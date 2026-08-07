# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-REMAINING-FAMILY-MEASUREMENT-CONTRACT-REPAIR-V1`  
Parent review: `P9-PRODUCT-AUTHORITATIVE-TRACE-PREPAYMENT-FAMILY-TOOLKIT-COMPLETION-V1`  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `repair`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-07-r11`  
Active bottleneck: `B-03`  
Inherited hypothesis: `H-03`  
Metric baseline: Product Trace=`7/12`、GESR=`6/12`；VALID=`T01,T02,T03,T04,T09,T10,T12`；T05/T06/T07/T08/T11 仍无产品轨迹。  
Estimated affected scope: measurement semantics for exactly `T05,T06,T07,T08`; no product capability is added.  
Expected project impact: `NOT_APPLICABLE` for this repair; current Product Trace and GESR MUST remain `7/12` and `6/12`.  
Rollback condition: any product/runner/registry change, any current metric change, any actual product-output change, or any fixture semantic change beyond the exact four event-name replacements is failure.

## Why this repair is required

Prepayment completion is `PASS + IMPROVED`, but remaining-family audit found four measurement expectations using event names that are no longer present in the accepted authoritative registry.

Accepted source of truth is the runtime contract exposed by:

```text
agentic_payment_experiment.authoritative_trace.runtime_contract_primitive()
```

Current stale fixture semantics:

```text
T05 expected key decision event:
DECISION_RECORDED

T06 expected key decision event:
DECISION_RECORDED

T07 expected key source/lineage event:
INPUT_SOURCE_RECORDED

T08 expected key source/lineage event:
INPUT_SOURCE_RECORDED
```

Accepted registry semantics:

```text
T05 / T06:
...
ACTION_BINDING_DECISION_RECORDED
...

T07 / T08:
POLICY_DECISION_RECORDED
LINEAGE_DECISION_RECORDED
RESULT_RECORDED
```

Historical Minimum Contract Repair evidence also records that T05/T06 final `DENY / INDETERMINATE` must be explained by `ACTION_BINDING_DECISION_RECORDED` reading `GovernedActionBindingFact.status`, rather than a generic `DECISION_RECORDED` event.

## Single objective

Repair the remaining measurement contract once, so every fixture `expected_product_observed_trace_events` entry is a valid subset of its accepted authoritative registry task profile before any new product family is implemented.

This package fixes the ruler only. It MUST NOT make T05/T06/T07/T08 product traces appear.

## Principal change

Exactly four fixture event-name replacements:

```text
T05: DECISION_RECORDED
  -> ACTION_BINDING_DECISION_RECORDED

T06: DECISION_RECORDED
  -> ACTION_BINDING_DECISION_RECORDED

T07: INPUT_SOURCE_RECORDED
  -> LINEAGE_DECISION_RECORDED

T08: INPUT_SOURCE_RECORDED
  -> LINEAGE_DECISION_RECORDED
```

Keep T07/T08 `POLICY_DECISION_RECORDED` unchanged.

Add one durable measurement regression check in `tests/test_project_impact_baseline.py` using public `runtime_contract_primitive()`:

```text
for every T01-T12:
fixture expected_product_observed_trace_events
must be a subset of
accepted registry event types for the same task_id
```

Do not compare fixture event lists for exact equality with the full registry because the fixture intentionally requires only a key-event subset.

## Frozen entering boundaries

```text
samples/evaluation/project_impact_baseline_v1.json
75e1682742e1eb576f62da89437bff766decde87d87ac73ad45de0ee59650ab5

tests/test_project_impact_baseline.py
0e99995680e477fa4c65221dafc8cb5ce427ca57f655765a35786850fe9c2c96

scripts/validation/run_project_impact_baseline.py
70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3

src/agentic_payment_experiment/authoritative_trace.py
07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a

non-trace projection SHA-256
6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

All `src/**/*.py` must remain byte-for-byte unchanged during this repair.

## Acceptance criteria

### AC-01 — Exact four semantic replacements

Fixture semantic diff against task-start copy must contain exactly four changed scalar values and no other differences:

```text
T05 expected_product_observed_trace_events:
DECISION_RECORDED -> ACTION_BINDING_DECISION_RECORDED

T06:
DECISION_RECORDED -> ACTION_BINDING_DECISION_RECORDED

T07:
INPUT_SOURCE_RECORDED -> LINEAGE_DECISION_RECORDED

T08:
INPUT_SOURCE_RECORDED -> LINEAGE_DECISION_RECORDED
```

### AC-02 — Registry-subset regression test

`tests/test_project_impact_baseline.py` must add one test that obtains the accepted task registry through public `runtime_contract_primitive()` and proves for all 12 tasks:

```text
set(fixture expected key events)
<=
set(registry full event types)
```

The test must identify task IDs / missing stale names on failure.

No private `_RUNTIME_CONTRACT_JSON` dependency is allowed in the new test.

### AC-03 — Corrected remaining-family gap names

Using the unchanged runner after repair:

```text
T05 product trace = NOT_AVAILABLE
T06 product trace = NOT_AVAILABLE
T07 product trace = NOT_AVAILABLE
T08 product trace = NOT_AVAILABLE
```

and their capability gaps must reference accepted event names:

```text
T05/T06 include missing ACTION_BINDING_DECISION_RECORDED
T05/T06 do not mention DECISION_RECORDED as a standalone stale required event

T07/T08 include missing POLICY_DECISION_RECORDED
T07/T08 include missing LINEAGE_DECISION_RECORDED
T07/T08 do not mention INPUT_SOURCE_RECORDED
```

### AC-04 — No false project gain

Same unchanged runner, repeat=3:

```text
Product Trace = 7/12
GESR          = 6/12
valid product tasks = T01,T02,T03,T04,T09,T10,T12
absent product tasks = T05,T06,T07,T08,T11
repeatability all_identical = true
```

Any metric increase or new product trace during this repair is failure.

### AC-05 — Actual product / business invariance

All 12 `actual` outputs must exactly equal the accepted Prepayment completion/review snapshot before this repair.

Keep:

```text
non-trace projection SHA-256
= 6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc

T05 decision = DENY
T06 decision = INDETERMINATE
T07 decision = ALLOW
T08 decision = ALLOW
T07/T08 trusted_state_changed = false
T07/T08 blocked paths remain request.amount / request.payee respectively
forbidden side effects = []
```

### AC-06 — Frozen implementation boundaries

At submission:

- runner hash unchanged;
- `authoritative_trace.py` hash unchanged;
- all `src/**/*.py` hashes unchanged from task start;
- no project-map change by Executor;
- no prior accepted task artifact change.

### AC-07 — Tests

Run at minimum:

```text
python3 -m unittest tests.test_project_impact_baseline -v
python3 -m unittest discover -s tests -p 'test_*.py'
```

Require:

- project-impact suite all pass and includes the new registry-subset test;
- full suite at least `523` tests and all pass;
- no guardrail assertion removed or weakened.

### AC-08 — Evidence and workflow

Save EV triplets for:

- exact semantic diff;
- registry-subset check / project-impact tests;
- corrected T05-T08 gaps;
- repeat=3 metrics;
- actual/src invariance;
- full regression;
- workflow validator.

REPORT must be `SUBMITTED_FOR_REVIEW` or `BLOCKED`; Executor cannot issue final PASS.

## Allowed scope

May modify only:

- `samples/evaluation/project_impact_baseline_v1.json`
- `tests/test_project_impact_baseline.py`
- this task `REPORT.md`
- this task `evidence/EV-*`
- `CURRENT.md` only for `CONTRACT_FROZEN -> EXECUTING`

## Exclusions and forbidden side effects

- no `src/` modifications;
- no `scripts/validation/run_project_impact_baseline.py` modification;
- no authoritative registry modification;
- no project-map modification by Executor;
- no prior accepted task artifact modification;
- no runner alias, event-name normalization or compatibility mapping;
- no product authoritative trace creation;
- no weakening decision, callback, retry, provenance, lineage, binding or side-effect guards;
- no network, WebShop runtime, Buy Now, LLM, wallet, payment, order, fulfilment or callback side effects;
- no dependency installation or environment creation;
- no commit, push, reset, clean or history rewrite.

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

## Validation plan

| VP | Exact action | Expected |
|---|---|---|
| VP-01 | copy entering fixture/test + hash frozen boundaries | entering hashes recorded |
| VP-02 | structural semantic diff before/after fixture | exactly four scalar event-name replacements |
| VP-03 | project-impact unit suite | all pass; new public-registry subset test passes |
| VP-04 | inspect T05/T06/T07/T08 gaps from unchanged runner | only accepted event names; product traces remain NOT_AVAILABLE |
| VP-05 | project-impact repeat=3 | exactly 7/12 Product Trace, 6/12 GESR, stable |
| VP-06 | compare all 12 actual outputs + non-trace projection | byte/semantic equivalent; non-trace SHA unchanged |
| VP-07 | src/runner/registry boundary audit | no changes |
| VP-08 | full unittest discover | >=523, all pass |
| VP-09 | workflow validator | OK |

## Stop conditions

Stop and submit `BLOCKED` rather than expanding scope if:

- source-of-truth registry does not support one of the four replacements above;
- fixture requires changes beyond the exact four event-name values;
- the new subset test reveals any additional stale fixture event name;
- metrics change from `7/12 / 6/12`;
- any T05-T08 product trace becomes available;
- actual product outputs change;
- any `src`, runner, registry, project-map or prior accepted artifact must change;
- full tests regress.

## Required report

REPORT must include:

- exact four semantic replacements;
- new registry-subset regression test summary;
- T05-T08 corrected gap names;
- repeat=3 `7/12 / 6/12` and normalized hashes;
- all-12 actual-output invariance;
- non-trace SHA;
- src/runner/registry frozen hashes;
- project-impact and full test counts;
- deviations / skipped checks / blockers;
- `project_impact_candidate: NOT_APPLICABLE`.

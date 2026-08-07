# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-ATTACK-OVERLAY-FAMILY-TOOLKIT-V1`  
Parent review: `P9-PRODUCT-AUTHORITATIVE-TRACE-REMAINING-FAMILY-MEASUREMENT-CONTRACT-REPAIR-V1`  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `capability_experiment`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-07-r11`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`

Metric baseline: Product Trace=`7/12`、GESR=`6/12`；matched=`T01,T02,T03,T04,T09,T12`；VALID product trace=`T01,T02,T03,T04,T09,T10,T12`。

Measured baseline details:

```text
fixed tasks = 12
Product Trace = 7/12
GESR          = 6/12
matched tasks = T01,T02,T03,T04,T09,T12
VALID product traces = T01,T02,T03,T04,T09,T10,T12
remaining product-trace gaps = T05,T06,T07,T08,T11
```

Estimated affected scope: exactly T07/T08, `2/12` fixed tasks.  
Expected project impact: Product Trace `7/12 -> 9/12`; GESR `6/12 -> 8/12`; no change to the other 10 tasks.  
Rollback condition: any decision, blocked-path, lineage, callback/retry, trusted-state or other non-trace business result changes; any new product trace outside T07/T08; any runner/fixture/registry change; or failure to achieve both T07 and T08 as VALID under the unchanged measurement.

## Why this family now

The remaining measurement contract has been repaired and independently accepted. T07/T08 are now the clearest remaining same-structure family:

```text
T07 untrusted amount override
T08 untrusted payee override

both:
evaluate_attack_overlay(...)
-> AttackOverlayResult
-> existing Policy facts
-> existing Lineage facts
-> existing final defended result
```

Accepted authoritative registry already defines both as the same 3-event structure:

```text
1 POLICY_DECISION_RECORDED
2 LINEAGE_DECISION_RECORDED
3 RESULT_RECORDED
```

All three events use the same source object/projection:

```text
source object = AttackOverlayResult
projection schema = attack-overlay-result-trace/v2
source identity = AttackOverlayResult:{attack_id}
```

Therefore this experiment must expose already-produced immutable facts as a product trace. It must not rerun Policy, Lineage, validation or evaluation merely to manufacture trace evidence.

## Single objective

Add one shared Attack Overlay Trace family path that attaches a complete product-observed authoritative trace to genuine T07/T08 `AttackOverlayResult` outcomes, using two fixed declarative profiles and the existing shared trace assembly mechanics.

No T07/T08-specific builder functions or modules are allowed.

## Principal change

One principal product change:

```text
AttackOverlayResult
+ one optional authoritative_trace output
+ one Attack Overlay family toolkit
+ two fixed profiles (amount override / payee override)
+ one common 3-event assembly path
```

The normal attack evaluation remains the source of truth. The toolkit may read the already-produced result fields, but it must not call:

- `evaluate_context_policy`
- `resolve_fact_lineage`
- `validate_request`
- `evaluate_outcome`
- `evaluate_attack_overlay`

The product path must call the family toolkit exactly once per completed `evaluate_attack_overlay()` result.

## Frozen entering boundaries

```text
src/agentic_payment_experiment/attack_overlay.py
2f14925231f4c59368b096fdcc2398bba8c8c4e6f774d7bcb430487ca65f25d7

src/agentic_payment_experiment/webshop_trace_assembler.py
02d73682ec949d7a37be4e3824e614795f069efc26aafe2377ea18e7c69f70c8

src/agentic_payment_experiment/authoritative_trace.py
07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a

scripts/validation/run_project_impact_baseline.py
70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3

samples/evaluation/project_impact_baseline_v1.json
e7a1d338ece0c65c6417ce58384e8dc9eb2dc29b2e37ad461cf92b9deb9b89c0

tests/test_attack_overlay.py
afc977542e4d53abfefa42892a62b3a64df0a8cc4cecbcf7e3d662328a23dd27

tests/test_project_impact_baseline.py
f1101ce82ddc97a1eae49308856c371f1afd54fbd772afd6bb5cc1aef973bf4a

current src manifest digest
cbb545de39b6336db66a5c97ef10abace6de50e0ea1dcc019a180a3241699c95

non-trace projection SHA-256
6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

Existing accepted full trace hashes to preserve:

```text
T01 7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906
T02 fb1a79d73931f3e0bb87eafeffdaffe4004add137998d107ea425554605be624
T03 7f0e1ccb14cc9256c5c336fb460647ce040bf0549a3328764c061c7b766c92a7
T04 405e6b8971f9f5e3ad67069ace074df15af4fee6f80418a70466315dcd642c33
T09 a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e
T10 2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3
T12 ebb38113abb2582d52f434b1a1b30247cc68ee8f4b57c0c18f52efa37bb1c230
```

The T02/T03/T04 hashes use the same canonical primitive/hash method already used by the accepted completion audit.

## Required family profiles

Use exactly two fixed declarative profiles corresponding to accepted registry profile names:

```text
ATTACK_OVERLAY_T07_V2
ATTACK_OVERLAY_T08_V2
```

Profile selection must be based on real immutable result semantics, not task ID strings from the evaluator.

At minimum:

```text
T07 family semantics:
- attack attempted
- no override applied
- trusted state unchanged
- blocked override path exactly request.amount
- lineage status VALID
- lineage facts correspond to request.amount
- final defended result/evaluation remains successful and non-drifting

T08 family semantics:
- attack attempted
- no override applied
- trusted state unchanged
- blocked override path exactly request.payee
- lineage status VALID
- lineage facts correspond to request.payee
- final defended result/evaluation remains successful and non-drifting
```

Do not select a profile solely from `attack_id`, title, evaluator task ID, or source_ref prefix.

## Required trace structure

For either selected profile, output one `ProductAuthoritativeTrace` with:

```text
source = PRODUCT_OBSERVED
completeness_status = COMPLETE
profile = matching accepted registry profile
unique source bindings = 1
source object type = AttackOverlayResult
projection schema = attack-overlay-result-trace/v2
```

Exact events:

```text
#1 POLICY_DECISION_RECORDED
entity_role = ATTACK_POLICY_RESULT

#2 LINEAGE_DECISION_RECORDED
entity_role = ATTACK_LINEAGE_RESULT

#3 RESULT_RECORDED
entity_role = FINAL_OUTCOME
```

All three events must bind to the same immutable `AttackOverlayResult` projection/source binding and satisfy `validate_product_authoritative_trace(...)=VALID`.

The projection must be derived from the accepted `attack-overlay-result-trace/v2` fields already present on the base result; do not add evaluator-only or raw untrusted text fields to the projection.

## Acceptance criteria

### AC-01 — One shared family implementation

Implementation must have one family toolkit and exactly two declarative profiles.

Forbidden patterns:

- `build_t07_*`
- `build_t08_*`
- T07/T08-specific authoritative-trace modules
- duplicated three-event builder bodies
- dynamic JSON/YAML profile loading
- evaluator task ID lookup inside product code.

The shared family path must reuse existing `create_source_binding`, `create_event`, and `assemble_product_trace` mechanics rather than duplicate a second trace assembler.

### AC-02 — Positive T07/T08 profile selection

Dedicated tests must prove:

```text
request.amount blocked result -> ATTACK_OVERLAY_T07_V2 only
request.payee blocked result  -> ATTACK_OVERLAY_T08_V2 only
```

Selection must remain driven by immutable blocked-path/lineage/result facts even if attack IDs/titles/source refs are changed to unrelated strings.

### AC-03 — Fail-closed negative matrix

Dedicated tests must include at least these negative cases:

1. unsupported blocked path such as `request.agent_id` -> no family trace;
2. both `request.amount` and `request.payee` present -> no profile / fail closed;
3. blocked path and lineage fact path disagree -> no trace;
4. lineage status not VALID -> no trace;
5. `trusted_state_changed=true` -> no trace;
6. applied override path non-empty -> no trace;
7. decision drift -> no trace;
8. attack not attempted -> no trace;
9. existing non-null authoritative trace -> never overwrite;
10. invalid profile container or duplicate matching profiles -> fail closed.

Negative cases must not invoke network or real side effects.

### AC-04 — Exact product traces

Unchanged project-impact runner after implementation must observe:

```text
T07 product trace status = VALID
T07 product trace source = attack_overlay_result
T07 events = POLICY_DECISION_RECORDED, LINEAGE_DECISION_RECORDED, RESULT_RECORDED

T08 product trace status = VALID
T08 product trace source = attack_overlay_result
T08 events = POLICY_DECISION_RECORDED, LINEAGE_DECISION_RECORDED, RESULT_RECORDED
```

Both traces must independently validate as authoritative registry `VALID` and contain exactly 3 events / 1 unique source binding.

### AC-05 — T07/T08 business invariance

Relative to accepted repair baseline, only product-trace fields and the resulting `authoritative_trace` evidence stage may change.

Must remain:

```text
T07 decision = ALLOW
T08 decision = ALLOW
T07/T08 callback count = 0
T07/T08 callback observations = 0
T07/T08 retry count = 0
T07/T08 forbidden side effects = []
T07/T08 trusted_state_changed = false
T07 blocked_paths = [request.amount]
T08 blocked_paths = [request.payee]
lineage status/source semantics unchanged
```

The all-12 non-trace projection SHA must remain:

```text
6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

### AC-06 — Other ten tasks unchanged

For all task IDs except T07/T08, every `actual` field must exactly equal the accepted repair baseline:

`P9_PRODUCT_AUTHORITATIVE_TRACE_REMAINING_FAMILY_MEASUREMENT_CONTRACT_REPAIR_V1/evidence/RV-EV-03-baseline.json`.

No new product trace is allowed for T05/T06/T11.

Existing VALID product set must become exactly:

```text
T01,T02,T03,T04,T07,T08,T09,T10,T12
```

Absent set must become exactly:

```text
T05,T06,T11
```

### AC-07 — Existing trace invariance

The seven previously accepted product traces T01/T02/T03/T04/T09/T10/T12 must preserve the frozen full trace hashes listed above.

No existing product trace may be rebuilt differently as a side effect of this family experiment.

### AC-08 — Same-baseline project impact

Run the unchanged project-impact runner with repeat=3.

Required after state:

```text
Product Trace = 9/12 = 0.750000
GESR          = 8/12 = 0.666667
matched tasks include T07 and T08
T07 capability_gaps = []
T08 capability_gaps = []
repeatability all_identical = true
```

Required delta:

```text
Product Trace +2/12
GESR          +2/12
```

If only one of T07/T08 becomes valid, or metrics do not reach both exact targets, project impact cannot be `IMPROVED`.

### AC-09 — Frozen measurement boundaries

At submission these files must remain exactly at entering hashes:

- `samples/evaluation/project_impact_baseline_v1.json`
- `scripts/validation/run_project_impact_baseline.py`
- `src/agentic_payment_experiment/authoritative_trace.py`
- `src/agentic_payment_experiment/webshop_trace_assembler.py`

No runner alias/normalization/measurement shortcut is allowed.

### AC-10 — Tests and workflow

Add a dedicated Attack Overlay trace family test suite with at least 10 tests covering positive and negative matrix requirements.

Run at minimum:

```text
python3 -m unittest tests.test_attack_overlay -v
python3 -m unittest tests.test_attack_overlay_trace_toolkit -v
python3 -m unittest tests.test_project_impact_baseline -v
python3 -m unittest discover -s tests -p 'test_*.py'
```

Require:

- existing attack-overlay tests all pass;
- new family suite at least 10 tests, all pass;
- project-impact suite all pass;
- full suite at least `533` tests, all pass;
- workflow validator `OK`.

## Allowed scope

May modify only:

- `src/agentic_payment_experiment/attack_overlay.py`
- `src/agentic_payment_experiment/attack_overlay_trace_profiles.py` (new)
- `src/agentic_payment_experiment/attack_overlay_trace_toolkit.py` (new)
- `tests/test_attack_overlay.py` only if required to preserve/verify the public result contract
- `tests/test_attack_overlay_trace_toolkit.py` (new)
- `tests/test_project_impact_baseline.py` only for hardcoded expectations directly changed by T07/T08 becoming real product traces
- this task `REPORT.md`
- this task `evidence/EV-*`
- `CURRENT.md` only `CONTRACT_FROZEN -> EXECUTING`

## Exclusions and forbidden side effects

- no fixture modification;
- no project-impact runner modification;
- no authoritative registry modification;
- no shared assembler modification;
- no Sidecar/Prepayment/T10 product trace implementation modification;
- no T05/T06/T11 product capability;
- no project-map modification by Executor;
- no prior accepted task artifact modification;
- no evaluator replay laundering into product trace;
- no new business rule, source-trust rule, lineage rule or validation rule;
- no re-execution of Policy/Lineage/validation/evaluation inside the trace toolkit;
- no dynamic profile loaders, `eval`, `exec`, import loaders or config-driven code execution;
- no network, browser, LLM, WebShop runtime, Buy Now, payment, wallet, order, fulfilment or callback side effects;
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
| VP-01 | capture task-start hashes/manifests and accepted repair baseline | reproducible before snapshot |
| VP-02 | dedicated positive profile tests | T07/T08 uniquely select correct profile without ID dependence |
| VP-03 | dedicated negative matrix | >=10 family tests total; all fail closed correctly |
| VP-04 | validate T07/T08 trace objects | exact 3 events, 1 binding, registry VALID |
| VP-05 | compare T07/T08 non-trace business fields | identical to accepted repair baseline |
| VP-06 | compare other 10 actual outputs | exact equality to accepted repair baseline |
| VP-07 | verify all-12 non-trace SHA | exact frozen `6eb5...9099dc` |
| VP-08 | verify prior 7 full trace hashes | all frozen hashes exact |
| VP-09 | unchanged project-impact repeat=3 | Product Trace 9/12, GESR 8/12, stable |
| VP-10 | frozen measurement boundary hashes | fixture/runner/registry/assembler unchanged |
| VP-11 | existing attack + new family + project-impact tests | all pass |
| VP-12 | full unittest discover | >=533, all pass |
| VP-13 | workflow validator | OK |

## Stop conditions

Stop and submit `BLOCKED` rather than expanding scope if:

- accepted T07/T08 registry cannot be satisfied from existing immutable `AttackOverlayResult` facts;
- implementing the trace requires changing Policy, Lineage, validator, evaluator semantics or runner/fixture/registry;
- T07/T08 cannot be distinguished without evaluator task IDs or brittle attack-id strings;
- profile selection produces zero or multiple matches for the genuine fixed baseline cases;
- any T05/T06/T11 product trace appears;
- any non-trace output changes;
- any existing seven trace hashes change;
- only one of T07/T08 reaches VALID;
- Product Trace/GESR do not reach exactly 9/12 and 8/12;
- full regression fails.

## Required report

REPORT must include:

- exact changed files and hashes;
- family design and exactly two profile definitions;
- proof there are no T07/T08-specific builders;
- positive selector evidence independent of attack ID/title/source_ref;
- full negative matrix evidence;
- T07/T08 exact trace event/binding/profile validation;
- other-10 actual equality;
- all-12 non-trace SHA;
- prior seven trace hashes;
- repeat=3 baseline after result and delta;
- test counts;
- frozen measurement hashes;
- deviations/skipped checks/blockers;
- `project_impact_candidate: IMPROVED` only if exact 9/12 and 8/12 targets plus guardrails all hold.

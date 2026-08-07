# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-PREPAYMENT-FAMILY-TOOLKIT-COMPLETION-V1`  
Parent capability task: `P9-PRODUCT-AUTHORITATIVE-TRACE-PREPAYMENT-FAMILY-TOOLKIT-V1`  
Measurement repair: `P9-PRODUCT-AUTHORITATIVE-TRACE-PREPAYMENT-MEASUREMENT-CONTRACT-REPAIR-V1`  
Task kind: `capability_experiment`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-06-r10`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Metric baseline: accepted pre-capability baseline Product Trace=`4/12`、GESR=`3/12`，valid product tasks=`T01,T09,T10,T12`。  
Estimated affected scope: exactly `3/12` tasks — T02 price increase, T03 price decrease, T04 payee change.  
Expected project impact: if the frozen candidate survives completion verification, Product Trace=`7/12`、GESR=`6/12`，T02/T03/T04 matched with no gaps, so B-03 remaining product-trace gap shrinks from `8/12` to `5/12`.  
Rollback condition: any failed ambiguity/negative test, existing trace-hash change, non-trace/business change, coverage expansion, repeatability failure, full-suite regression, or need to modify frozen product source means the candidate cannot receive `PASS + IMPROVED`; stop and submit failure evidence instead of changing product code in this package.

Measured current candidate after the inherited capability change and accepted measurement repair:

```text
Product Trace = 7/12
GESR          = 6/12
valid product tasks = T01, T02, T03, T04, T09, T10, T12
```

Principal product change under evaluation is already present and frozen in the inherited workspace:

```text
webshop_prepayment_trace_profiles.py
0d5824eee57cac1c6b494c5beeb47a020f8bbca99f6fea674522e9fbae4cca28

webshop_prepayment_trace_toolkit.py
572bc38b61f993674bd2060fad1d1fdc0c5f2b7aba343c383a0fed1c82852348

webshop_trace_assembler.py
02d73682ec949d7a37be4e3824e614795f069efc26aafe2377ea18e7c69f70c8

webshop_runtime_gate.py
3414df3d986d105a3832ae354c7e0a6cd8c4909192ba052b42ec3b895c886fc3
```

This continuation MUST NOT change that principal product implementation. It only completes the missing falsification/invariance evidence required to decide whether H-03 is genuinely supported.

Expected project impact if H-03 survives the remaining tests:

```text
Product Trace +3/12
GESR +3/12
B-03 remaining product-trace gap shrinks from 8/12 to 5/12
```

Rollback / failure condition: because product source is frozen, any failed ambiguity, exact-hash, business-invariance, coverage, full-suite or repeatability check means this candidate cannot receive `PASS + IMPROVED`; Executor must stop and submit the failure rather than modify product code in this package.

## Single objective

Complete the missing verification for the already-implemented T02/T03/T04 Prepayment Trace Toolkit and produce a reviewable package that lets Evaluator issue the final task verdict and project-impact verdict for H-03.

No new T family and no new product behavior may be added.

## Acceptance criteria

### AC-01 — Frozen candidate implementation

At task start and submission, the four product files listed in Strategic basis must retain exactly the frozen SHA-256 values above.

Also freeze:

```text
samples/evaluation/project_impact_baseline_v1.json
75e1682742e1eb576f62da89437bff766decde87d87ac73ad45de0ee59650ab5

scripts/validation/run_project_impact_baseline.py
70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3

src/agentic_payment_experiment/authoritative_trace.py
07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a
```

No `src/` file may change in this continuation.

### AC-02 — Positive profile selection

Add focused unit tests proving that the frozen profile selector chooses exactly one correct profile for each accepted positive scenario:

```text
T02 = PRICE_INCREASE
T03 = PRICE_DECREASE
T04 = PAYEE_CHANGE
```

For T02/T03, selection must depend on immutable authorized/current order value direction, not merely shared issue/reason codes.

### AC-03 — Fail-closed ambiguity / negative matrix

Focused tests must prove fail-closed behavior for at least:

- zero matching profile;
- multiple matching profiles using the existing `_select_profile(..., profiles=...)` test seam with duplicate/ambiguous frozen profile inputs;
- mixed item-price directions;
- price change plus payee change;
- unchanged price with price-change reason codes;
- missing/invalid authority or bound request facts;
- base outcome already containing an authoritative trace;
- invalid profile container/type where applicable.

Expected result: selector/build returns `None`; no trace and no side effect.

### AC-04 — Exact T02/T03/T04 product traces

Using normal product-path facts only, T02/T03/T04 must each produce:

```text
status = VALID
6 events
6 source bindings
```

Exact event sequence:

```text
AUTHORITY_RECORDED
ORDER_RECORDED [AUTHORIZED]
ORDER_RECORDED [CURRENT]
REQUEST_RECORDED
PREPAYMENT_DECISION_RECORDED
RESULT_RECORDED
```

No evaluator replay, fixture or docs may construct product traces.

### AC-05 — Existing full trace hash invariance

Exact canonical full trace hashes must remain:

```text
T01 = 7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906
T09 = a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e
T10 = 2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3
T12 = ebb38113abb2582d52f434b1a1b30247cc68ee8f4b57c0c18f52efa37bb1c230
```

Any change is failure.

### AC-06 — Business / non-trace invariance

Keep:

```text
non-trace projection SHA-256
= 6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc

T02 decision = CONFIRMATION_REQUIRED
T03 decision = CONFIRMATION_REQUIRED
T04 decision = INDETERMINATE
T02/T03/T04 callback = 0
T02/T03/T04 retry = 0
forbidden side effects = []
```

All 12 actual product outputs must remain equal to the accepted post-capability snapshot used by the measurement-repair review.

### AC-07 — Coverage remains bounded

Product authoritative traces may exist only for:

```text
T01,T02,T03,T04,T09,T10,T12
```

They must remain absent for:

```text
T05,T06,T07,T08,T11
```

No T02/T03/T04-specific authoritative trace module or `build_t02_* / build_t03_* / build_t04_*` function may exist.

### AC-08 — Complexity / single-path guardrail

Static audit must prove:

```text
webshop_runtime_gate.py
- Prepayment Toolkit import = 1
- Prepayment Toolkit builder call = 1
- no new validate_request call

webshop_prepayment_trace_toolkit.py
- assemble_product_trace call = 1
- fixed profile count = 3
- no dynamic config loader
- no eval / exec / dynamic import
```

### AC-09 — Same-baseline impact and repeatability

Run the unchanged project-impact runner with corrected accepted fixture and repeat=3.

Require:

```text
Product Trace = 7/12
GESR          = 6/12
T02/T03/T04 matched = true
T02/T03/T04 capability_gaps = []
repeatability all_identical = true
```

Impact comparison must use the accepted pre-capability baseline `4/12 / 3/12`, which was collected before T02/T03/T04 product traces existed; the old event-name defect did not create false positives in that baseline because those three traces were absent.

### AC-10 — Tests and workflow evidence

At minimum run:

```text
python3 -m unittest tests.test_webshop_prepayment_trace_toolkit -v

python3 -m unittest \
  tests.test_webshop_trace_assembler \
  tests.test_webshop_prepayment_trace_toolkit \
  tests.test_webshop_runtime_gate \
  tests.test_webshop_sidecar_trace_toolkit \
  tests.test_webshop_payment_sidecar \
  tests.test_webshop_authoritative_trace \
  tests.test_authoritative_trace \
  tests.test_project_impact_baseline -v

python3 -m unittest discover -s tests -p 'test_*.py'

python3 scripts/validation/run_project_impact_baseline.py \
  --repeat 3 \
  --output <evidence>/EV-AFTER-baseline.json
```

Requirements:

- dedicated prepayment suite all pass;
- focused suite all pass;
- full suite at least `512` and all pass;
- repeat=3 stable;
- workflow validator `OK`.

## Allowed scope

May add or modify only:

- `tests/test_webshop_prepayment_trace_toolkit.py` (new focused verification suite)
- this task `REPORT.md`
- this task `evidence/EV-*`
- `CURRENT.md` only for `CONTRACT_FROZEN -> EXECUTING`

No product implementation edit is authorized.

## Exclusions and forbidden side effects

- no `src/` modifications;
- no fixture, runner, registry, profile, project-map or accepted prior-task artifact changes;
- no new T-series product trace;
- no runner alias/normalization workaround;
- no JSON/YAML DSL, dynamic loader, `eval`, `exec` or dynamic import;
- no WebShop runtime, Buy Now, network, LLM, wallet, payment, order, fulfilment or callback side effects;
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
| VP-01 | frozen SHA audit | candidate product/runner/fixture/registry hashes unchanged |
| VP-02 | positive T02/T03/T04 selector tests | exactly one correct profile each |
| VP-03 | zero/multi/mixed/invalid matrix | all fail closed |
| VP-04 | T02/T03/T04 trace validation | VALID, six events, six bindings |
| VP-05 | T01/T09/T10/T12 full trace hash audit | exact four hashes unchanged |
| VP-06 | non-trace/business invariant audit | exact non-trace SHA; decisions/callback/retry unchanged |
| VP-07 | producer coverage/static complexity audit | only seven product-trace tasks; one toolkit path |
| VP-08 | project-impact repeat=3 | 7/12, 6/12, stable, T02/T03/T04 no gaps |
| VP-09 | focused/full unittest | all pass; full >=512 |
| VP-10 | workflow validator | OK |

## Stop conditions

Executor must stop and submit `BLOCKED` / failure evidence rather than modify product code if:

- any frozen product/source/runner/fixture/registry hash changes;
- any required positive, zero-match, multi-match or mixed-direction case fails;
- T01/T09/T10/T12 exact trace hash changes;
- non-trace SHA or T02/T03/T04 business decision/callback/retry changes;
- T05-T08/T11 gain a product trace;
- Product Trace/GESR fall below `7/12 / 6/12`;
- repeat=3 is unstable;
- full suite regresses;
- completion would require product code edits or external side effects.

## Required report

REPORT must include:

- `Executor status: SUBMITTED_FOR_REVIEW` or `BLOCKED`;
- exact changed files and hashes;
- EV mapping for AC-01 through AC-10;
- dedicated ambiguity/negative matrix results;
- four exact existing trace hashes;
- non-trace SHA and T02/T03/T04 business guardrails;
- producer coverage and complexity audit;
- repeat=3 result;
- full test count;
- impact comparison `4/12 -> 7/12`, `3/12 -> 6/12` with scope caveat;
- no claim of final `PASS` or `IMPROVED` — those are Evaluator-only verdicts.

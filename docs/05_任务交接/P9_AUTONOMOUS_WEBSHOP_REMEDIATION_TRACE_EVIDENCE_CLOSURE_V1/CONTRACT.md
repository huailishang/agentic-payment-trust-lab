# Frozen Task Contract

Task ID: `P9-AUTONOMOUS-WEBSHOP-REMEDIATION-TRACE-EVIDENCE-CLOSURE-V1`  
Task name: Generic Post-Payment Remediation Trace Evidence Closure  
Task kind: `capability_experiment`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `d26fa658b970f84ca25859d7c3739994cae10a61`  
Validation plan file: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_REMEDIATION_TRACE_EVIDENCE_CLOSURE_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-12-r32`  
Active bottleneck: `B-13`  
Hypothesis: `H-22`  
Dispatch: `SINGLE`  
Metric baseline: accepted H-21 `trace remediation evidence=0/5`, `branch continuity=0/5`, while remediation semantics=`5/5` and original-transaction binding expectation=`5/5`.  
Estimated affected scope: `5/5` frozen post-payment remediation branches share the same first breakpoint `TRACE_REMEDIATION_EVIDENCE_PRESENT`; downstream Accountability / Replay / Closure consumption depends on this evidence layer.  
Expected project impact: close the shared trace-evidence breakpoint `0/5 → 5/5` without changing refund/dispute/lifecycle/original-transaction business semantics.  
Rollback condition: any solution requires changing remediation/lifecycle/original-transaction decisions, introduces case-specific product branches, normalizes R05 from `INVALID` to `VALID`, weakens trace validation/fail-closed behavior, or regresses project safety guardrails.

Measured baseline from accepted H-21:

```text
5/5 remediation semantics MATCH
5/5 original-transaction binding expectation MATCH
5/5 closure state explicit
5/5 existing Product Authoritative Trace available + VALID
5/5 existing Action Origin projectable
0/5 Trace remediation evidence present
5/5 first_breakpoint = TRACE_REMEDIATION_EVIDENCE_PRESENT
full unittest = 658/658
real payment/refund/dispute/network side effects = 0
```

Accepted H-21 result:

- path: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_REMEDIATION_CLOSURE_MEASUREMENT_V1/evidence/H21_REMEDIATION_CLOSURE_RESULT.json`
- SHA-256: `9d794317cc77753bb84e6b7b0ec3c6a441ff1d6a632753c782ba556c7fb4f8bb`

Frozen H-21 matrix:

- SHA-256: `abe7a75d32d6833f5289160c1477d18b6265aae18476c3e1b509989373f26acc`

Expected project impact: close the one shared post-payment evidence breakpoint across all five frozen remediation branches without changing refund/dispute/lifecycle business semantics.  
Rollback condition: any solution requires changing remediation/lifecycle/original-transaction decisions, introduces case-specific product branches, normalizes R05 from `INVALID` to `VALID`, weakens trace validation/fail-closed behavior, or regresses project safety guardrails.

## Single objective / 单一目标

Add one generic **post-payment remediation trace extension（支付后补救轨迹扩展层）** that appends already-produced immutable remediation facts to the accepted same-journey Product Authoritative Trace（产品权威轨迹）:

```text
accepted payment/fulfilment Product Authoritative Trace
        +
RefundRecord or DisputeRecord
        +
OriginalTransactionBindingFact
        +
remediated LifecycleResult / Closure outcome
        ↓
source-bound remediation trace extension
        ↓
Product Authoritative Trace remains VALID
        ↓
Action Origin remains projectable
```

The extension must consume existing product facts. It must not re-decide refund/dispute semantics or original-transaction binding.

## Principal change / 唯一主要变化

> Add one protocol-neutral, source-bound, fail-closed product trace extension for post-payment remediation evidence.

The principal change may require coordinated edits to the existing trace projection registry and Action Origin event-role registry, but these are one mechanism: registering the new immutable post-payment facts in the same Product Authoritative Trace contract.

Do **not** implement R01-R05 as five trace profiles or five case branches.

## Frozen evidence semantics

The generic extension must represent three evidence roles:

1. `REMEDIATION_OBSERVATION` — source is exactly one caller-supplied `RefundRecord` or `DisputeRecord`; origin class = `EXTERNAL_FACT`.
2. `ORIGINAL_TRANSACTION_BINDING_FACT` — source is the existing `OriginalTransactionBindingFact`; origin class = `RUNTIME_DECISION`.
3. `REMEDIATION_CLOSURE_OUTCOME` — source is the existing remediated `LifecycleResult` projection that explicitly contains original task state + economic remediation state + next action/case ref; origin class = `EXECUTION_RESULT`.

Recommended closed event-role names, frozen for this task:

```text
REMEDIATION_OBSERVATION_RECORDED / REMEDIATION_OBSERVATION
ORIGINAL_TRANSACTION_BINDING_RECORDED / ORIGINAL_TRANSACTION_BINDING_FACT
REMEDIATION_CLOSURE_RECORDED / REMEDIATION_CLOSURE_OUTCOME
```

No wildcard/default Action Origin mapping is allowed.

### R05 fail-closed rule

`R05_REFUND_PAYMENT_BINDING_MISMATCH` is a negative control, not a case to normalize.

Its extended trace must preserve:

```text
OriginalTransactionBindingFact.status = INVALID
reason_codes contains original_transaction_payment_ref_mismatch
follow-up payment ref remains the mismatched ref
```

The trace may record the invalid binding fact, but must not create a false `BOUND_TO` relation asserting the mismatched RefundRecord belongs to the accepted original payment. Any relation whose truth depends on the invalid reference must be omitted or represented as a non-binding diagnostic fact under the existing trace contract.

## Projection / source-binding requirements

The existing Authoritative Trace projection registry must gain closed deterministic schemas for the source objects needed by this extension. At minimum:

- `RefundRecord` projection;
- `DisputeRecord` projection;
- `OriginalTransactionBindingFact` projection;
- remediation closure projection from `LifecycleResult`.

Projection requirements:

- deterministic and JSON-canonicalizable;
- no current time/random/path/raw prompt/credential/payment secret fields;
- native identifiers may be used for Refund/Dispute identity; projection-hash identity is appropriate for derived binding/closure facts;
- every new event must reference a real `TraceSourceBinding` derived from its source projection;
- no evaluator-manufactured source fact may be represented as product evidence.

## Allowed scope / 允许修改范围

The following files are the complete allowed implementation/measurement scope for H-22; task-owned `REPORT.md` and `evidence/**` are also allowed. Anything else requires return to Evaluator.

## Architecture boundary / 架构边界

Preferred product shape:

- new `src/agentic_payment_experiment/webshop_remediation_trace.py` for the generic append/extension mechanism;
- mechanical projections in `src/agentic_payment_experiment/webshop_trace_assembler.py`;
- closed projection registry update in `src/agentic_payment_experiment/authoritative_trace.py`;
- three closed event-role mappings in `src/agentic_payment_experiment/action_origin.py`.

Allowed product files:

- `src/agentic_payment_experiment/webshop_remediation_trace.py` (new)
- `src/agentic_payment_experiment/webshop_trace_assembler.py`
- `src/agentic_payment_experiment/authoritative_trace.py`
- `src/agentic_payment_experiment/action_origin.py`
- `src/agentic_payment_experiment/__init__.py` only if a public export is needed

Allowed measurement / test files:

- `scripts/validation/webshop/run_same_journey_remediation_trace_closure.py` (new)
- `tests/test_webshop_remediation_trace.py` (new)
- directly relevant existing trace/origin tests when required
- task-owned `REPORT.md` and `evidence/**`

Frozen business/product files:

```text
src/agentic_payment_experiment/remediation.py
  43a76921fe3058edee4b1778b73949a00dc76a44de08a36f8a3d4e8cdb8c15d3
src/agentic_payment_experiment/lifecycle.py
  8fc6df6f56d5aad47cc9c449340307324150f12760f0a124bd32296a659a4c92
src/agentic_payment_experiment/trusted_execution/original_transaction.py
  482b7aa23e07f7724b909ab289928e61f9227f2544611b886e028047d4e9e5d9
src/agentic_payment_experiment/webshop_sidecar_trace_toolkit.py
  1ccf37b62f6eedc0eff41216ec983ddaea74aed7a0e0529be686f6b15aefbbf3
```

Also freeze H-21 runner/result/matrix and H-20 accepted parent evidence.

## Measurement contract / 测量合同

Executor adds one local runner:

`scripts/validation/webshop/run_same_journey_remediation_trace_closure.py`

It must reuse the accepted H-21 five branches and existing product methods to reconstruct the same journey, then invoke the new product remediation-trace extension. It must not copy business expected values into product outputs.

Output:

`docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_REMEDIATION_TRACE_EVIDENCE_CLOSURE_V1/evidence/H22_REMEDIATION_TRACE_RESULT.json`

Schema: `same-journey-remediation-trace-closure-result/v1`

Top level at minimum:

```text
baseline
repeat_per_case
cases[5]
summary
guardrails
```

Each case at minimum:

```text
case_id
measurement_complete
repeat_identical
run_digests[2]
semantic_match
original_transaction_binding
extended_trace
remediation_observation
binding_fact_evidence
closure_evidence
action_origin
continuity
continuity_pass
first_breakpoint
```

`baseline` must mechanically reference accepted H-21 `trace remediation evidence=0/5`; after measurement must be derived from real extended traces.

## Acceptance criteria / 验收标准

### AC-01 — Frozen semantics and accepted baseline remain unchanged

- H-21 result hash, H-21 matrix hash, H-20 parent hash remain unchanged;
- frozen `remediation.py`, `lifecycle.py`, `original_transaction.py`, `webshop_sidecar_trace_toolkit.py` hashes remain unchanged;
- no real refund/dispute/payment/Buy Now/network action;
- no dependency install.

### AC-02 — One generic remediation trace extension, no case patches

- one product mechanism handles all 5 frozen branches;
- product code contains no `R01`..`R05`, frozen case IDs, fixed order/request/payment IDs, fixed refund/dispute IDs, ASIN or amount-driven case switches;
- extension consumes caller-supplied `RefundRecord | DisputeRecord`, `OriginalTransactionBindingFact`, and remediated `LifecycleResult`;
- unknown/malformed/unsupported input fails closed rather than silently generating a plausible trace.

### AC-03 — Remediation observation becomes source-bound product evidence

For all 5 branches:

- extended Product Authoritative Trace is present and validator status=`VALID`;
- one remediation observation event exists;
- source type is `RefundRecord` for R01/R02/R05 and `DisputeRecord` for R03/R04;
- event source binding commits to the exact caller-supplied projection;
- observation is linked only to valid existing entities; R05 must not assert a false original-payment binding.

### AC-04 — Original transaction binding fact is explicit and fail-closed

- all 5 traces contain an `OriginalTransactionBindingFact` event/source binding;
- R01-R04 preserve `VALID`;
- R05 preserves `INVALID` and `original_transaction_payment_ref_mismatch`;
- no code path changes `verify_original_transaction` output;
- invalid binding is evidence, not authority to claim a valid relation.

### AC-05 — Closure outcome is explicit and Action Origin remains closed/projectable

For all 5 branches:

- closure event is source-bound to a deterministic projection of the remediated `LifecycleResult`;
- projection distinguishes original task status from economic remediation status and carries `next_action` / `case_ref` when present;
- three new event-role mappings use only existing five ActionOrigin classes:
  - remediation observation → `EXTERNAL_FACT`;
  - original transaction binding → `RUNTIME_DECISION`;
  - remediation closure → `EXECUTION_RESULT`;
- unknown event/role remains `ActionOriginError` fail-closed;
- extended traces are Action Origin projectable 5/5.

### AC-06 — Common breakpoint closes on the frozen five-branch before/after

Same H-21 branch identities, repeat=`2`:

```text
Before: trace remediation evidence = 0/5
After target: trace remediation evidence = 5/5
After target: branch continuity = 5/5
semantic matches = 5/5 unchanged
binding expectation matches = 5/5 unchanged
first_breakpoint = null for 5/5
```

A measured result below `5/5` is not authority for Executor to broaden scope; return evidence to Evaluator.

### AC-07 — Existing trace and project guardrails do not regress

- focused remediation/original-transaction/trace/origin tests PASS;
- `run_experiment.py` remains `13/13 PASS`;
- project-impact baseline repeat=`3` all identical;
- Product Trace >= `10/12`;
- GESR >= `9/12`;
- callback=`12/12`;
- duplicate/forbidden side effect=`0/12`;
- unsafe allow=`0/5`;
- full unittest discovery has zero failures;
- real side effects/network calls=`0`.

### AC-08 — v2.2 handoff

- frozen L2 mandatory checks all PASS;
- REPORT maps AC-01..08 to EV;
- REPORT gives exact before/after, five branch observations, R05 negative-control behavior, changed files/hashes, guardrails, deviations, stop-condition status;
- workflow validator `OK` before submission;
- Executor does not issue final Task/Project verdict.

## Exclusions / 明确排除

- no changes to refund/dispute/lifecycle/original-transaction decision rules;
- no changes to Sidecar Trace Toolkit/Profile selection for pre-remediation lifecycle;
- no real PSP/refund/dispute/network integration;
- no legal/settlement finality claim;
- no new ActionOrigin enum value;
- no wildcard/default origin fallback;
- no per-case product branch;
- no opportunistic T05/T06 Product Trace or B-04 Agent behavior work;
- no commit, push, or history rewrite.

## Stop conditions / 停止条件

Stop and return `BLOCKED` if any of the following is required:

- frozen business semantics must change;
- R05 must be normalized to VALID to make the trace validate;
- validator/trace contract must be weakened to accept unresolved or false relations;
- a second trace mechanism separate from Product Authoritative Trace is needed;
- a case-ID-specific implementation is needed;
- semantic/binding guardrails regress;
- real side effects/network/dependency install is required;
- complete implementation→L2 cycles exceed `3`.

## Bounded Executor loop / 有界执行循环

- maximum complete implementation→L2 cycles: `3`;
- focused L1 tests may repeat inside the frozen hypothesis/scope;
- every material L2 outcome must be preserved;
- if after 3 cycles the shared breakpoint is not closed without violating scope, stop and return evidence rather than widening the task.

## Cost / iteration value

Expected cost: **medium（中等）** local engineering only. No API/model/network/real-payment budget.  
Affected measured scope: `5/5` frozen post-payment remediation branches.  
Expected value: one common mechanism closes one repeated breakpoint across all five branches and prepares a stable evidence layer for later Accountability / Replay / Closure Consumer（问责 / 回放 / 结束消费层） work.

## Authorization / 授权

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- real payment/refund/dispute: false

# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-MEASUREMENT-ADAPTER-V1`  
Task name: 产品权威轨迹 Measurement Adapter v1  
Task kind: `maintenance`  
Risk: `L1`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-04-r5`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-PROJECTION-IDENTITY-FORMULA-REPAIR-V1`  
Parent verdict: `PASS / NOT_APPLICABLE`

引用模型、真实对象 grounding、T10/T12 profile 和 `PROJECTION_HASH_IDENTITY_V1` 已被 Evaluator 接受。当前第一步不应直接让 T10 产品产出轨迹，而应先升级项目级测量工具，使新 envelope 在产品仍不产出轨迹时得到可信、可重复的 `0/12 BEFORE`。

本任务属于 measurement maintenance，不宣称 B-03 已改善。

## Single objective

实现一套纯测量层的产品权威轨迹数据合同、冻结 registry 和严格 validator，并让项目级 runner 只读取产品 outcome 明确返回的：

```text
outcome.authoritative_trace
```

产品仍不产出 trace，因此完成后的正确结果必须保持：

```text
product-observed authoritative trace = 0/12 VALID
GESR = 0/12
```

同时冻结后续 T10 capability experiment 可以复用的 accepted runner、target、BEFORE 和 non-trace business projection hashes。

## Entering baseline

### Repository baseline

```text
HEAD
= b4eff597ebffe79c575522b91642f82b26ad5247

old runner SHA-256
= a7d71fd92cacd7ebdb8e4a1da383067aa57b0e6dcbf20c41f043f4e461fc1fc4

baseline fixture SHA-256
= 4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5

target fixture SHA-256
= f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee
```

### Old-runner measurement baseline

Command:

```text
python3 scripts/validation/run_project_impact_baseline.py \
  --repeat 3 \
  --output <evidence>/EV-BASELINE-old-runner.json
```

Measured result:

```text
old runner output SHA-256
= 58f27a115c2be350fbedcdf31c1453c8e82df6ed2fa8d180fca923bc1a36e852

repeatability normalized SHA-256
= 4dfc7743909374689ec7b437b3a1b774d4d2e1155e287f3f8dc23430498b7044

product trace = 0/12
GESR = 0/12
callback match = 12/12
duplicate/forbidden side effect = 0/12
decision-reason consistency = 11/12
```

### Non-trace business projection baseline

Canonical projection is ordered T01—T12 and contains only:

```text
task_id
actual.actual_decision
actual.actual_callback_count
actual.actual_callback_observations
actual.actual_retry_count
actual.actual_final_environment_state
actual.actual_reason_codes
actual.known_payment_attempt_preflight_status
actual.known_payment_attempt_preflight_reason_codes
actual.known_payment_attempt_preflight_blocking_request_refs
actual.binding_status
actual.lineage_status
actual.effective_source_types
actual.required_facts_observed
actual.forbidden_side_effects
actual.limitations
```

Canonical JSON uses UTF-8, sorted keys, compact separators, `ensure_ascii=false`, `allow_nan=false`.

```text
non-trace business projection SHA-256
= 6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

## Accepted design inputs

Authoritative design:

- `docs/03_架构设计/产品权威轨迹最小合同_v1.md`
- `docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/MEASUREMENT_ADAPTER.md`

Structured coverage:

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/
evidence/EV-01-coverage-projection-identity-formula.json
```

Accepted hashes:

```text
coverage file SHA-256
= 69b5c65eee924b011f606eb8284d0870971e40724f2fc62d59763cd18bcd703f

formula registry canonical SHA-256
= 2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd

projection registry canonical SHA-256
= 45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4

T01—T12 profiles canonical SHA-256
= 6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2

full runtime contract canonical SHA-256
= 4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e
```

Runtime code must use an embedded/frozen registry or equivalent package-local constant. It must not read task evidence or docs at runtime. Tests must prove the embedded registry is semantically identical to the accepted structured coverage hashes above.

## Acceptance criteria

### AC-01 — Pure trace contract

Add a package-local pure measurement module, preferably:

```text
src/agentic_payment_experiment/authoritative_trace.py
```

It must define immutable, primitive-safe contracts equivalent to:

```text
TraceSourceBinding
- binding_ref
- source_object_type
- source_object_ref
- projection_schema
- projection

TraceRelation
- relation_type
- target_entity_type
- target_entity_role
- target_entity_ref
- target_binding_assertions

ProductTraceEvent
- sequence_no
- event_type
- entity_type
- entity_role
- entity_ref
- source_binding_ref
- decision
- status
- reason_codes
- relations

ProductAuthoritativeTrace
- schema_version
- source
- profile
- trace_ref
- completeness_status or declared completeness input
- reason_codes
- events
- source_bindings
```

Requirements:

1. dataclass values are frozen/immutable;
2. tuple is used for ordered collections at the public boundary;
3. projection and assertion data are primitive-only after canonicalization;
4. no business decision logic is introduced;
5. no source object, `GateContext`, fixture or evaluator replay is stored in the envelope;
6. no import from task evidence scripts;
7. package export may be added through `__init__.py`, but existing exports remain compatible.

The validator, not the product caller, owns the final structural verdict.

### AC-02 — Frozen runtime registry

The measurement module must provide or load from package-local immutable constants:

- 16 projection schemas;
- 9 `PROJECTION_HASH_IDENTITY_V1` entries;
- 7 `NATIVE_TEMPLATE` entries;
- canonical primitive rules;
- forbidden projection fields;
- T01—T12 exact profiles;
- relation templates and binding assertions.

It must expose deterministic hashes matching:

```text
formula registry = 2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd
projection registry = 45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4
profiles = 6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2
full runtime contract = 4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e
```

Runtime must not open:

```text
docs/
CURRENT.md
handoff evidence
EV builder scripts
```

Tests may read accepted coverage only to prove parity.

### AC-03 — Canonicalization and reference recomputation

Implement deterministic functions for:

```text
canonical primitive conversion
canonical JSON bytes
PROJECTION_HASH_IDENTITY_V1 source_object_ref
NATIVE_TEMPLATE source_object_ref
TraceSourceBinding binding_ref
entity_ref template rendering
relation target ref rendering
```

Canonical primitive must support the accepted closed set:

```text
null / bool / int / str
Decimal
Enum
datetime
tuple / list
dict
```

Rules include:

- bool is not treated as int;
- Decimal finite fixed notation, trim trailing zeros, `-0 → 0`, never float;
- Enum `.value` then canonicalize;
- datetime uses source `isoformat()`;
- tuple/list preserve order;
- dict keys are strings and canonical JSON sorts keys;
- float, NaN, Infinity and unsupported objects fail closed.

The module must independently reproduce the accepted parent T10/T12 source refs and binding refs without importing parent EV builders.

### AC-04 — Strict validator

Provide one public validator that consumes only:

```text
ProductAuthoritativeTrace
+ frozen runtime registry
```

It must return a primitive/frozen validation result containing at least:

```text
status = VALID | INVALID | INDETERMINATE
reason_codes
profile
event_types
```

Validation order must be explicit and fail closed:

```text
A. envelope/schema/source/profile
B. event sequence and exact profile shape
C. projection schema and exact field allowlist
D. source_object_ref identity
E. binding_ref exact digest
F. event source_binding_ref resolution
G. entity_ref typed template
H. decision/status/reason value paths
I. relation target type/role/ref
J. target binding assertions
K. duplicate/unreferenced/missing binding
```

Required exact outcomes:

- product attribute missing or `None`: runner-level `NOT_AVAILABLE`;
- unknown profile/schema/class/extraction contract: `INDETERMINATE` or stricter fail-closed status defined by accepted design;
- missing required event/binding/field: `INDETERMINATE`;
- duplicate binding ref, extra field, digest mismatch, identity mismatch, entity mismatch, relation mismatch: `INVALID`;
- unreferenced binding: `INVALID`;
- evaluator replay is never accepted as product trace;
- declared product status cannot bypass validator.

No validator branch may read product original objects or reconstruct missing facts.

### AC-05 — Runner reads exact envelope only

Update:

```text
scripts/validation/run_project_impact_baseline.py
```

Replace the legacy `authoritative_trace_events: tuple[ReplayEvent]` measurement path with:

```text
outcome.authoritative_trace
```

Requirements:

1. use `getattr(outcome, "authoritative_trace", None)` only as presence lookup;
2. absent/None means `NOT_AVAILABLE`;
3. present value is passed to the strict validator;
4. runner records validator status, event types, reason codes and product source name;
5. runner never reads hidden `GateContext`, fixtures, current source objects or synthesized replay to complete the envelope;
6. evaluator synthesized replay remains a separate diagnostic field;
7. valid replay cannot change product trace from `NOT_AVAILABLE`;
8. T07/T08 remain `NOT_AVAILABLE` because current `AttackOverlayResult` has no product trace;
9. no product outcome class is modified to produce a trace.

The obsolete attribute `authoritative_trace_events` must no longer count as product trace. A fake object exposing only that legacy attribute must still produce `NOT_AVAILABLE`.

### AC-06 — Strict negative and positive tests

Add focused tests, preferably:

```text
tests/test_authoritative_trace.py
```

and update:

```text
tests/test_project_impact_baseline.py
```

Tests must cover at least:

#### Positive

- all 9 hash identity vectors;
- native identity examples;
- all accepted binding digests;
- T10 exact 12 events / 11 bindings validates `VALID` when supplied as a synthetic envelope directly to the validator;
- two Order events share one binding;
- all T10 relation targets resolve;
- T12 conflict and sidecar bindings recompute;
- embedded registry hashes equal accepted design hashes.

#### Negative

- missing trace;
- legacy `authoritative_trace_events` only;
- wrong `source`;
- unknown profile;
- sequence gap/duplicate/out-of-order;
- missing/extra event;
- missing binding;
- duplicate identical/conflicting binding;
- unreferenced binding;
- unknown projection schema;
- missing/extra/forbidden projection field;
- native identity mismatch;
- hash identity prefix/type/schema/projection/digest mismatch;
- uppercase/non-64 digest;
- float/NaN/Infinity;
- binding digest mismatch;
- source binding unresolved;
- entity ref mismatch;
- relation type/role/ref mismatch;
- target binding assertion mismatch;
- sidecar RESULT fabricated decision;
- RESULT projection containing `authoritative_trace`;
- valid evaluator replay with absent product trace.

Tests must use local fixed data only and perform no product side effects.

### AC-07 — Trusted `0/12 BEFORE`

Run the same baseline and target with the new runner:

```text
python3 scripts/validation/run_project_impact_baseline.py \
  --repeat 3 \
  --output <evidence>/EV-BEFORE-baseline.json

python3 scripts/validation/run_project_impact_baseline.py \
  --spec samples/evaluation/project_impact_t10_preflight_target_v1.json \
  --repeat 3 \
  --output <evidence>/EV-BEFORE-target.json
```

Expected baseline:

```text
product-observed trace = 0/12 VALID
GESR = 0/12
project gaps = T01—T12
repeatability = true
```

All current product outcomes must still lack a non-null `authoritative_trace` producer.

The task must freeze in REPORT/evidence:

```text
accepted runner SHA-256
accepted baseline fixture SHA-256
accepted target fixture SHA-256
accepted baseline output SHA-256
accepted target output SHA-256
accepted baseline normalized SHA-256
accepted target normalized SHA-256
accepted non-trace business projection SHA-256
```

The accepted non-trace projection hash must remain:

```text
6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

If it changes, stop and report exact task/key differences. Do not update the expected hash to fit the implementation.

### AC-08 — Existing behavior guardrails

The same post-change baseline must preserve:

```text
callback match = 12/12
duplicate/forbidden side effect = 0/12
unsafe allow = 0/5
missed confirmation = 0/2
overconfident decision = 0/2
forbidden state write = 0/2
binding completeness = 5/5
source lineage completeness = 2/2
retry match = 12/12
decision-reason consistency = 11/12
```

Run:

```text
python3 -m unittest tests.test_authoritative_trace tests.test_project_impact_baseline -v
python3 -m unittest discover -s tests -p 'test_*.py'
```

If this repository's accepted environment uses a different existing command, record the exact equivalent command and raw output. Do not install dependencies or create an environment.

Entering full-test baseline is exactly `451 tests / OK`. Post-change full tests must be at least `451` and all pass. REPORT must state the actual test count, not only “passed”.

### AC-09 — Product boundary

Must prove zero changes to product behavior and zero trace producers in:

```text
src/agentic_payment_experiment/webshop_runtime_gate.py
src/agentic_payment_experiment/webshop_payment_sidecar.py
src/agentic_payment_experiment/attack_overlay.py
src/agentic_payment_experiment/models.py
src/agentic_payment_experiment/payment_recovery.py
src/agentic_payment_experiment/payment_status_conflict.py
src/agentic_payment_experiment/trusted_execution/
```

Permitted package changes are only the new pure measurement module and optional `__init__.py` export.

Must not:

- add `authoritative_trace` to any current outcome;
- construct T10 product events in a product path;
- execute WebShop runtime or Buy Now;
- perform payment, wallet, order or callback side effects;
- count evaluator replay as product trace.

### AC-10 — Workflow and evidence

REPORT must include:

- exact changed files;
- old/new runner hashes;
- embedded registry hashes;
- validator status matrix;
- focused and full test raw evidence;
- baseline and target raw JSON;
- baseline/target output and normalized hashes;
- non-trace projection calculation script and hash;
- static zero-producer audit;
- initial/final git status and diff;
- authorization/limitations;
- workflow validator `OK`.

Evidence must use `EV-*` triplets. CURRENT remains `EXECUTING / Executor` when submitted.

Project impact verdict must be:

```text
NOT_APPLICABLE
```

This maintenance task establishes a trustworthy measuring instrument; it does not improve product trace coverage.

## Required outputs

1. `src/agentic_payment_experiment/authoritative_trace.py`
2. optional `src/agentic_payment_experiment/__init__.py` export update
3. `scripts/validation/run_project_impact_baseline.py`
4. `tests/test_authoritative_trace.py`
5. `tests/test_project_impact_baseline.py`
6. this task `REPORT.md`
7. this task `evidence/EV-*` and generated baseline/target JSON

## Allowed scope

May add or modify only:

- `src/agentic_payment_experiment/authoritative_trace.py`
- `src/agentic_payment_experiment/__init__.py`
- `scripts/validation/run_project_impact_baseline.py`
- `tests/test_authoritative_trace.py`
- `tests/test_project_impact_baseline.py`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/REPORT.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-*`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/*.json`
- `CURRENT.md`（仅原子路由）

Read-only inputs include accepted design docs, accepted coverage JSON, current source, tests and fixtures.

The workspace inherits accepted uncommitted evaluator/executor artifacts from prior P9 tasks. Do not clean, reset, delete, overwrite or include them in unrelated modifications.

## Exclusions

- no changes to current product outcome/gate/sidecar/payment/recovery/conflict/attack code;
- no changes to `samples/` fixtures or business expectations;
- no T10 product trace producer;
- no capability experiment in this task;
- no hidden context/source resolver;
- no runtime dependency on `docs/`, CURRENT or task evidence;
- no evaluator replay fallback;
- no new business rule;
- no network, LLM, browser, WebShop runtime or Buy Now execution;
- no payment, wallet, order, callback or external side effect;
- no dependency installation or environment creation;
- no commit, push or history rewrite;
- no update to project map or B-03/H-03;
- no freezing of the T10 capability `CONTRACT.md` by Executor.

## Validation plan

| VP | Exact action | Expected |
|---|---|---|
| VP-01 | Parse pure trace dataclasses | frozen, primitive-safe, no product dependencies |
| VP-02 | Compare embedded registry hashes | exact accepted formula/projection/profile/runtime hashes |
| VP-03 | Recompute fixed refs/digests | all T10/T12 accepted values match |
| VP-04 | Run strict positive/negative validator tests | exact status/reason matrix; no fallback |
| VP-05 | Runner fake-outcome tests | only `authoritative_trace` counts; legacy/replay absent remains NOT_AVAILABLE |
| VP-06 | Baseline/target repeat=3 | 0/12 product trace, deterministic output |
| VP-07 | Non-trace projection comparison | exact hash `6eb5...` unchanged |
| VP-08 | Focused + full unittest | all pass; actual count recorded |
| VP-09 | Product boundary audit | protected product files and producer count unchanged |
| VP-10 | Workflow validator | `OK` |

## Stop conditions

- implementation needs to change any product outcome;
- runtime needs to read docs/evidence or original source objects;
- legacy replay is needed to make a trace VALID;
- new runner cannot preserve 0/12 BEFORE;
- non-trace projection hash changes;
- any existing business metric/side-effect guardrail regresses;
- accepted registry hashes cannot be reproduced;
- T10 synthetic envelope cannot validate without changing accepted design;
- tests require new dependencies or environment;
- any network or external side effect is required.

## Authorization

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- data_download: false
- dependency_install: false
- create_environment: false
- webshop_runtime_execution: false
- buy_now_execution: false
- payment_or_order_side_effect: false

## Amendments

None.

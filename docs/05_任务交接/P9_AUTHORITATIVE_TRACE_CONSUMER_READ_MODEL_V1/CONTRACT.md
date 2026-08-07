# Frozen Task Contract

Task ID: `P9-AUTHORITATIVE-TRACE-CONSUMER-READ-MODEL-V1`  
Parent review: `P9-PRODUCT-AUTHORITATIVE-TRACE-ATTACK-OVERLAY-FAMILY-TOOLKIT-V1`  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `capability_experiment`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-07-r12`  
Active bottleneck: `B-08`  
Hypothesis: `H-07`

Metric baseline: Consumer-ready representative trace families=`0/4`; Product Trace=`9/12`; GESR=`8/12`; current full regression=`538/538`.

Estimated affected scope: exactly four representative trace structures — T01 Sidecar, T02 Prepayment, T07 Attack Overlay, T10 Duplicate/Preflight. The same consumer should later be reusable for all 9 currently VALID product traces.

Expected project impact: representative consumer coverage `0/4 -> 4/4`, while Product Trace remains `9/12`, GESR remains `8/12`, all existing product trace hashes and all product/business outputs remain unchanged.

Rollback condition: any existing product implementation or trace hash changes; Product Trace/GESR/non-trace output changes; the consumer needs task/profile-specific branches; INVALID/INDETERMINATE trace produces a normal timeline; or the consumer reruns business, Policy, Lineage, payment, evaluator or project-impact logic.

## Why this is the next bottleneck

Current product-observed Authoritative Trace coverage has reached 9/12 and spans four structurally different families:

```text
Sidecar             T01/T09/T12
Prepayment          T02/T03/T04
Attack Overlay      T07/T08
Duplicate/Preflight T10
```

The remaining T05/T06/T11 trace gaps are no longer the earliest blocker. The observable project gap is now:

```text
Product creates VALID traces
-> evaluator validates them
-> no generic downstream consumer exists
-> Replay/UI cannot yet use one stable protocol-neutral read model
```

`docs/02_未来规划/WebShop购买轨迹可视化UI规划_20260802.md` requires UI to read machine-generated evidence rather than infer process from logs or prose. This task creates that read-only boundary; it does not build the final UI.

## Single objective

Create one protocol-neutral, read-only Authoritative Trace Consumer that converts a frozen `VALID ProductAuthoritativeTrace` into deterministic, UI-neutral timeline/read-model data without reconstructing or re-executing any business fact.

```text
ProductAuthoritativeTrace
-> validate frozen trace contract
-> generic read-only projection
-> deterministic Trace Read Model / Timeline JSON
```

## Principal change

Exactly one new capability:

```text
new authoritative_trace_consumer module
+ closed structured read model
+ generic consume/serialize path
```

No existing product trace producer, family toolkit, registry, runner, fixture, UI or business decision path may change.

## Representative input set

Freeze these four representative structures for acceptance:

```text
T01 Sidecar
- existing accepted full trace hash
  7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906

T02 Prepayment
- existing accepted full trace hash
  fb1a79d73931f3e0bb87eafeffdaffe4004add137998d107ea425554605be624

T07 Attack Overlay
- genuine fixed project-impact product trace
- exact 3-event accepted registry structure

T10 Duplicate / Preflight
- existing accepted full trace hash
  2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3
```

T07 trace identity may vary with its source attack ID, so acceptance is based on frozen registry validity, exact event structure and deterministic repeatability rather than a globally frozen T07 hash.

## Required read model

The implementation may choose exact class/function names, but the public output must be a closed structured object with deterministic primitive serialization.

At minimum, top-level Read Model must preserve:

```text
trace_ref
profile
schema_version
source
completeness_status
events[]
source_bindings[]
```

Every `events[]` item must preserve, without reinterpretation:

```text
sequence_no
event_type
entity_type
entity_role
entity_ref
source_binding_ref
decision
status
reason_codes
relations[]
```

Every relation must preserve enough structure to audit the original relation, including at minimum:

```text
relation_type
target_entity_type
target_entity_role
target_entity_ref
target_resolved
target_binding_assertions[]
```

Every source binding must preserve the frozen safe projection boundary:

```text
binding_ref
source_object_type
source_object_ref
projection_schema
projection
```

The consumer must not add raw prompt/page text, credentials, card data, private keys, evaluator-only reconstruction or free-form inferred facts.

## Acceptance criteria

### AC-01 — One generic consumer path

One new generic consumer handles all accepted profiles without task-specific/profile-specific logic.

Static guardrails:

- no `T01`, `T02`, `T07`, `T10` branching in production consumer code;
- no profile-name branching such as `WEBSHOP_*` / `ATTACK_OVERLAY_*`;
- no product-family imports from Sidecar, Prepayment, Attack Overlay, Runtime Gate or test helpers;
- no dynamic JSON/YAML config loader, `eval`, `exec`, dynamic import or plugin dispatch.

### AC-02 — Frozen validation boundary and fail closed

Before creating a normal Read Model, consumer must use the existing public authoritative trace contract validator.

Required behavior:

```text
VALID trace -> read model available
INVALID trace -> fail-closed structured result / no normal timeline
INDETERMINATE trace -> fail-closed structured result / no normal timeline
wrong input type / malformed container -> fail closed
```

Consumer must never repair, normalize, synthesize or drop invalid events to force a valid timeline.

### AC-03 — Exact event preservation

For each representative VALID trace:

- Read Model event count equals source trace event count;
- sequence order is exact;
- all required event fields are exact value projections of the source event;
- reason-code ordering/content is preserved deterministically;
- no source event is merged, reordered, renamed or omitted.

### AC-04 — Source binding and relation auditability

For every Read Model event:

- `source_binding_ref` resolves to a Read Model source binding copied from the same trace;
- source object metadata and projection equal the original frozen source binding;
- relation target refs/roles/types and binding assertions equal the original trace relation data;
- no new relation or source binding is invented.

### AC-05 — Deterministic primitive serialization

Provide one deterministic primitive/JSON representation suitable for later UI consumption.

For each of T01/T02/T07/T10:

```text
same trace consumed 3 times
-> normalized/canonical output SHA-256 identical all 3 times
```

Serialization must not contain timestamps generated at consume time, memory addresses, object repr, random values or local file paths.

### AC-06 — Representative family coverage 0/4 -> 4/4

The same consumer must successfully produce valid read models for all four representative structures:

```text
T01 Sidecar             PASS
T02 Prepayment          PASS
T07 Attack Overlay      PASS
T10 Duplicate/Preflight PASS
```

No family-specific production branch is allowed to achieve this result.

### AC-07 — Negative matrix

Dedicated tests must include at least:

1. wrong input type;
2. missing required source binding;
3. duplicate/invalid event sequence;
4. unresolved or invalid relation target;
5. binding-ref mismatch / missing event binding;
6. malformed source binding projection;
7. duplicate binding identity where contract rejects it;
8. incomplete/indeterminate trace case;
9. invalid trace with otherwise plausible event prose;
10. repeat consume of a failed input does not mutate it or create a later success.

All must fail closed without fabricating timeline facts.

### AC-08 — No business re-execution

Production consumer must not import or call business/runtime logic such as:

- `validate_request`
- `evaluate_context_policy`
- `resolve_fact_lineage`
- `evaluate_attack_overlay`
- payment execution/recovery/finality functions
- WebShop runtime gate/sidecar functions
- project-impact runner
- evaluator scoring logic

Only frozen Authoritative Trace validation plus mechanical projection/serialization is allowed.

### AC-09 — Existing product/measurement invariance

All existing `src/**/*.py` files at task start are frozen. The only allowed source addition is the new consumer module.

At minimum these hashes must remain exact:

```text
src/agentic_payment_experiment/authoritative_trace.py
07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a

src/agentic_payment_experiment/webshop_trace_assembler.py
02d73682ec949d7a37be4e3824e614795f069efc26aafe2377ea18e7c69f70c8

src/agentic_payment_experiment/attack_overlay.py
8fc4200f7d6eb871860897e2117d9c3eea0590643294acff684733186fb5968c

samples/evaluation/project_impact_baseline_v1.json
e7a1d338ece0c65c6417ce58384e8dc9eb2dc29b2e37ad461cf92b9deb9b89c0

scripts/validation/run_project_impact_baseline.py
70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3
```

Task-start existing-src manifest digest:

```text
7506518544e6f0901ee709b233fd7708fd48a88c6247e468305b8d033aaa35f1
```

The manifest comparison must prove: no existing src Python file changed; exactly one new source file was added.

Project guardrails after implementation:

```text
Product Trace = 9/12
GESR          = 8/12
non-trace projection SHA
= 6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

Existing accepted T01/T02/T03/T04/T09/T10/T12 trace hashes must remain unchanged.

### AC-10 — Tests and workflow

Add `tests/test_authoritative_trace_consumer.py` with at least 12 tests covering four positive families, deterministic output, auditability and negative matrix.

Run at minimum:

```text
python3 -m unittest tests.test_authoritative_trace_consumer -v
python3 -m unittest tests.test_project_impact_baseline -v
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/validation/run_project_impact_baseline.py --repeat 3 --output <evidence>/EV-AFTER-baseline.json
```

Required:

- consumer suite >=12, all pass;
- project-impact 21/21;
- full regression >=550, all pass;
- repeat=3 identical;
- Product Trace 9/12 and GESR 8/12 unchanged;
- workflow validator `OK`.

## Impact comparison

This experiment uses a new B-08 capability metric rather than claiming more product traces:

```text
Before
consumer-ready representative families = 0/4
Product Trace = 9/12
GESR = 8/12

Expected After
consumer-ready representative families = 4/4
Product Trace = 9/12
GESR = 8/12
```

Project impact can be `IMPROVED` only if all four representative families use the same generic consumer and all product/measurement guardrails remain frozen.

## Allowed scope

May change only:

- `src/agentic_payment_experiment/authoritative_trace_consumer.py` (new)
- `tests/test_authoritative_trace_consumer.py` (new)
- this task `REPORT.md`
- this task `evidence/EV-*`
- `CURRENT.md` only `CONTRACT_FROZEN -> EXECUTING`

Do not modify `__init__.py` merely to export the consumer; tests may import the module directly.

## Exclusions

- no UI implementation in this package;
- no `html_report.py`, `interactive_lab.py`, `interactive_server.py` changes;
- no trace producer/family toolkit changes;
- no authoritative registry or shared assembler changes;
- no fixture/runner/project-impact measurement changes;
- no T05/T06/T11 product trace work;
- no Replay business-event reconstruction;
- no natural-language summarizer or LLM-generated explanation;
- no network/browser/WebShop runtime/Buy Now/payment/wallet/order/fulfilment/callback execution;
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
| VP-01 | freeze existing src manifest + core hashes | reproducible entering boundary |
| VP-02 | consumer positive tests T01/T02/T07/T10 | same generic path, 4/4 |
| VP-03 | exact event/source-binding/relation comparison | source trace == read model projection |
| VP-04 | deterministic repeat x3 per representative trace | identical normalized SHA |
| VP-05 | negative matrix | invalid/incomplete/malformed all fail closed |
| VP-06 | static import/call audit | no task/profile branch or business re-execution |
| VP-07 | project-impact suite | 21/21 |
| VP-08 | unchanged project-impact repeat=3 | Product Trace 9/12, GESR 8/12 |
| VP-09 | old trace hash + non-trace audit | exact frozen values |
| VP-10 | full regression | >=550, all pass |
| VP-11 | workflow validator | OK |

## Stop conditions

Stop and submit `BLOCKED` rather than expanding scope if:

- a generic Read Model cannot preserve relations/source bindings without family-specific knowledge;
- existing `ProductAuthoritativeTrace` lacks information required by the frozen UI-neutral contract;
- any existing src file must change;
- consumer requires task/profile-specific branches;
- invalid traces cannot be distinguished without reconstructing business facts;
- project metrics or existing trace hashes move;
- full regression fails.

## Required report

REPORT must include:

- exact new files and hashes;
- entering/current src manifest comparison;
- public Read Model shape;
- 4/4 representative family evidence;
- exact event/source-binding/relation audit evidence;
- deterministic output SHA x3 for each representative family;
- negative matrix results;
- static no-business-reexecution audit;
- unchanged Product Trace/GESR/non-trace/old trace hashes;
- test counts;
- workflow validator result;
- `project_impact_candidate: IMPROVED` only if representative consumer coverage reaches 4/4 with all guardrails unchanged.

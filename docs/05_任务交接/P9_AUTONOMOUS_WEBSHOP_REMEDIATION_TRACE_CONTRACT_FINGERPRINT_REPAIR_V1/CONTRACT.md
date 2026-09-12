# Frozen Task Contract

Task ID: `P9-AUTONOMOUS-WEBSHOP-REMEDIATION-TRACE-CONTRACT-FINGERPRINT-REPAIR-V1`  
Task name: Effective Runtime Contract Fingerprint Repair  
Task kind: `repair`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `d26fa658b970f84ca25859d7c3739994cae10a61`  
Inherited accepted snapshot: H-22 uncommitted accepted snapshot frozen by file hashes below  
Validation plan file: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_REMEDIATION_TRACE_CONTRACT_FINGERPRINT_REPAIR_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-12-r33`  
Active bottleneck: `B-13`  
Inherited hypothesis: `H-22`  
Repair hypothesis: `H-22R`  
Metric baseline: H-22 capability is already accepted at remediation evidence=`5/5`, continuity=`5/5`, semantics=`5/5`, binding expectation=`5/5`; independent Evaluator probe found live projection registry SHA-256=`71a4e3d6e15e87c40db38149abdfbc10bee8dbb27ad847175565acc363d73966` while public `runtime_registry_hashes()["projection_registry"]` still reports historical base hash=`45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4`.  
Estimated affected scope: every future audit/replay/accountability consumer that uses the public runtime contract/hash to identify the validator contract; current H-22 trace behavior itself is not failing.  
Expected project impact: restore exact identity between the public effective runtime contract/fingerprint and the registries actually used by trace validation, while retaining an explicit historical accepted-base contract surface.  
Rollback condition: any solution changes H-22 trace semantics/results, business rules, Action Origin mapping, source projections, validator fail-closed behavior, or project safety guardrails.

## Problem statement / 问题定义

H-22 added four live projection schemas and two remediation profiles to the validator's effective registries:

```text
PROJECTION_REGISTRY = historical base + 4 H-22 projections
PROFILE_REGISTRY    = historical base + 2 H-22 remediation profiles
```

But the public identity helpers still expose only the historical base contract:

```text
runtime_registry_hashes()
  projection_registry -> hash(_BASE_PROJECTION_REGISTRY)
  profiles            -> hash(PROFILE_TASKS)
  runtime_contract    -> hash(_RUNTIME_CONTRACT)

runtime_contract_primitive()
  -> _RUNTIME_CONTRACT only
```

That means a caller can validate an H-22 trace using the live extension while receiving a public contract fingerprint that does not commit to those extension schemas/profiles.

This repair does **not** question H-22 functional correctness. It fixes contract identity / auditability（合同身份 / 可审计性） before Replay / Accountability consumption.

## Single objective / 单一目标

Make the public `runtime_*` contract/fingerprint APIs represent the **effective live validator contract**, while preserving the pre-H-22 historical accepted contract through explicitly named `accepted_base_*` compatibility APIs.

Target model:

```text
historical _RUNTIME_CONTRACT
        ├─ accepted_base_runtime_contract_primitive()
        └─ accepted_base_registry_hashes()

live PROJECTION_REGISTRY + PROFILE_REGISTRY
        ↓
runtime_contract_primitive()       # effective runtime
        ↓
runtime_registry_hashes()          # hashes effective runtime exactly
```

## Principal change / 唯一主要变化

> Split historical accepted-base identity from effective runtime identity, and make public `runtime_*` exports/hash values commit to the exact live registries used by `validate_product_authoritative_trace()`.

No trace-generation or business-logic change is allowed.

## Frozen entering snapshot / 冻结进入快照

The following H-22 accepted files are immutable during this repair:

```text
src/agentic_payment_experiment/remediation.py
43a76921fe3058edee4b1778b73949a00dc76a44de08a36f8a3d4e8cdb8c15d3

src/agentic_payment_experiment/lifecycle.py
8fc6df6f56d5aad47cc9c449340307324150f12760f0a124bd32296a659a4c92

src/agentic_payment_experiment/trusted_execution/original_transaction.py
482b7aa23e07f7724b909ab289928e61f9227f2544611b886e028047d4e9e5d9

src/agentic_payment_experiment/webshop_remediation_trace.py
961f6042bc48afc160b3373bd2b439da30127f32de44fa3937cc00d1dc3460ad

src/agentic_payment_experiment/webshop_trace_assembler.py
c98c3a1477ebf64a5696707c0d637da60d8563ef174b06a100c9d9b7bebc1656

src/agentic_payment_experiment/action_origin.py
b43cf1338e7397107aae83a1fca78752b55cd15c900f0160d64a6983707fcada

scripts/validation/webshop/run_same_journey_remediation_trace_closure.py
a90f0923ee6fdbb1c9b8d0cee76390f04d2786a8350bd8c09fafa7e62061d1fc

tests/test_webshop_remediation_trace.py
360acb53475645d76555d23c32ce0e937159800e096d0fd3fc7541362d35a6be

accepted H-22 result
ba1d4e562bef9ae975c81049b0c24399513cf62f6f8d1c7bb6ece4f2b4e09891
```

Historical accepted base constants remain factual baselines:

```text
base projection registry hash
45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4

base runtime contract hash
4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e
```

## Required contract semantics / 必须实现的合同语义

### 1. Historical accepted base remains explicit

Add public compatibility helpers with exactly these names:

```text
accepted_base_runtime_contract_primitive()
accepted_base_registry_hashes()
```

They must expose the unchanged historical `_RUNTIME_CONTRACT` and its historical registry hashes. They exist for old evidence/regression comparison only.

### 2. `runtime_contract_primitive()` becomes effective runtime

`runtime_contract_primitive()` must return a detached primitive whose:

- `projection_registry` exactly equals the live `PROJECTION_REGISTRY` content;
- `tasks` / profile entries represent exactly the live `PROFILE_REGISTRY` profiles consumed by validation;
- all other base contract fields remain semantically unchanged unless mechanically required to describe the effective registries;
- output is deterministic and canonical-hashable.

The export must include at least these H-22 projection schemas:

```text
refund-record-remediation-trace/v1
dispute-record-remediation-trace/v1
original-transaction-binding-fact-remediation-trace/v1
lifecycle-remediation-closure-trace/v1
```

and these H-22 profiles:

```text
WEBSHOP_POST_PAYMENT_REFUND_REMEDIATION_V1
WEBSHOP_POST_PAYMENT_DISPUTE_REMEDIATION_V1
```

### 3. `runtime_registry_hashes()` becomes effective runtime fingerprint

The existing public function name must no longer silently mean historical base.

At minimum:

```text
runtime_registry_hashes()["projection_registry"]
  == canonical_sha256(PROJECTION_REGISTRY)

runtime_registry_hashes()["profiles"]
  == canonical_sha256(runtime_contract_primitive()["tasks"])

runtime_registry_hashes()["runtime_contract"]
  == canonical_sha256(runtime_contract_primitive())
```

Formula-registry hash remains deterministic and unchanged unless the formula registry actually changes.

### 4. No hidden second identity

Do not add another public helper named `effective_*` while leaving `runtime_*` stale. `runtime_*` must mean actual effective runtime. Historical identity must be explicitly named `accepted_base_*`.

## Allowed scope / 允许修改范围

Product code:

- `src/agentic_payment_experiment/authoritative_trace.py`

Regression tests:

- `tests/test_authoritative_trace.py`
- `tests/test_project_impact_baseline.py`

Task-owned outputs:

- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_REMEDIATION_TRACE_CONTRACT_FINGERPRINT_REPAIR_V1/REPORT.md`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_REMEDIATION_TRACE_CONTRACT_FINGERPRINT_REPAIR_V1/evidence/**`

Evaluator-owned files are read-only:

- this `CONTRACT.md`
- `VALIDATION_PLAN.yaml`
- `evaluator_checks/**`
- `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`
- H-22 `REPORT.md / REVIEW.md / evidence/**`
- `CURRENT.md`

## Acceptance criteria / 验收标准

### AC-01 — H-22 product behavior is byte-frozen

All frozen H-22 product/runner/test/result hashes listed above remain unchanged. No business rules, Action Origin mappings, trace-extension generation, H-22 matrix/result, or side effects change.

### AC-02 — Historical base identity is explicit and unchanged

- `accepted_base_runtime_contract_primitive()` exists and equals the historical `_RUNTIME_CONTRACT` semantic content;
- `accepted_base_registry_hashes()` exists;
- historical base projection hash remains exactly `45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4`;
- historical base runtime-contract hash remains exactly `4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e`.

### AC-03 — Public runtime export equals live validator registries

- `runtime_contract_primitive()["projection_registry"]` has exactly the same keys/content as `PROJECTION_REGISTRY`;
- exported profile-name set exactly equals `PROFILE_REGISTRY.keys()`;
- H-22 4 projection schemas + 2 remediation profiles are present;
- no phantom profile/schema exists only in export or only in validator memory.

### AC-04 — Public runtime hashes commit to the effective runtime

Mechanically prove:

```text
reported projection hash == canonical hash(live PROJECTION_REGISTRY)
reported profile hash == canonical hash(exported effective tasks/profiles)
reported runtime-contract hash == canonical hash(runtime_contract_primitive())
```

The pre-repair mismatch must disappear. The repair must not hard-code the currently observed `71a4...` live hash as logic; hashes are derived from actual structures.

### AC-05 — Existing T01-T12 baseline regression remains meaningful

`tests/test_project_impact_baseline.py` may be minimally adjusted so its T01-T12 registry-subset assertion reads from the now-effective runtime contract without treating H-22 extension profiles as an error.

Requirements:

- T01-T12 expected event subset check still runs for all 12 original tasks;
- it must not silently skip any `ALL_TASK_IDS` entry;
- it must not assert that the effective runtime contains only T01-T12;
- fixture semantics remain unchanged.

### AC-06 — H-22 accepted capability remains 5/5

Independent rerun of frozen H-22 five branches must remain:

```text
remediation evidence = 5/5
branch continuity = 5/5
semantics = 5/5
binding expectation = 5/5
R05 = INVALID
R05 false original-payment relation = absent
extended Product Trace VALID = 5/5
real side effects/network = 0
```

### AC-07 — Project guardrails do not regress

- authoritative-trace and project-impact focused tests PASS;
- H-22 remediation trace tests PASS;
- project-impact baseline repeat=`3`, `all_identical=true`;
- Product Trace >= `10/12`;
- GESR >= `9/12`;
- callback=`12/12`;
- duplicate/forbidden side effect=`0/12`;
- unsafe allow=`0/5`;
- full unittest discovery has zero failures;
- real side effects/network=`0`.

### AC-08 — v2.2 repair handoff

- frozen L2 mandatory checks all PASS;
- REPORT maps AC-01..08 to EV;
- REPORT records before mismatch and after effective hashes, base compatibility hashes, changed files/hashes, H-22 revalidation, guardrails, deviations and stop-condition status;
- workflow validator `OK` before submission;
- Executor does not issue final Evaluator verdict.

## Exclusions / 明确排除

- no changes to remediation/lifecycle/original-transaction logic;
- no changes to `webshop_remediation_trace.py` or H-22 source projections/origin mappings;
- no new trace events, projection schemas, profiles or business cases;
- no changes to H-22 accepted result/matrix/runner;
- no new ActionOrigin values;
- no weakening trace validation;
- no T05/T06 Product Trace work;
- no Fresh Unseen / Agent behavior work;
- no network/API/dependency install/real payment/refund/dispute;
- no commit, push, or history rewrite.

## Stop conditions / 停止条件

Stop and return `BLOCKED` if:

- fixing identity requires changing any frozen H-22 product file;
- H-22 5/5 measurement regresses;
- historical base contract cannot remain explicitly retrievable;
- effective runtime export cannot be made structurally identical to the live validator registries without redesigning trace validation;
- project safety guardrails regress;
- more than `2` complete implementation→L2 cycles are required.

## Bounded Executor loop / 有界执行循环

- max complete implementation→L2 cycles: `2`;
- local focused L1 checks may repeat inside the same repair hypothesis;
- no external/model/API budget;
- if cycle 2 still cannot make public runtime fingerprint equal live registries, stop and return evidence rather than broadening scope.

## Cost / value

Expected cost: **low to medium（低到中）**, local code/tests only.  
Expected value: removes a contract-identity blind spot before the project relies on these traces for Replay / Accountability（回放 / 问责）.  
Opportunity-cost decision: preferred over immediately adding a consumer because consuming a trace whose public contract fingerprint does not identify the live validator version would weaken downstream audit claims.

## Authorization / 授权

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- real payment/refund/dispute: false

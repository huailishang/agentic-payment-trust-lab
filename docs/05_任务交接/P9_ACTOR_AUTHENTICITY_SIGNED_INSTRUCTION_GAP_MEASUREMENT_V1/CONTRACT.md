# Frozen Task Contract

Task ID: `P9_ACTOR_AUTHENTICITY_SIGNED_INSTRUCTION_GAP_MEASUREMENT_V1`  
Task name: Actor Authenticity / Signed Instruction Cross-Surface Gap Measurement  
Task kind: `one_off`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `d26fa658b970f84ca25859d7c3739994cae10a61`  
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-12-r35`  
Active bottleneck: `B-15`  
Hypothesis: `H-24`  
Validation plan file: `docs/05_任务交接/P9_ACTOR_AUTHENTICITY_SIGNED_INSTRUCTION_GAP_MEASUREMENT_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

B-11 through B-14 are now `RESOLVED / STAGE_CLOSED`. The project has closed a representative evidence lifecycle from Action Origin（动作来源） through payment lifecycle, remediation/closure, and generic read-only consumption.

The remaining higher-value security boundary is not another trace/UI detail. Current repository claims deliberately stop at:

```text
P3 identity assurance <= BOUND
Strong Authentication = not proven
Credential / Key Governance = not proven
Cryptographic Signature Verification = not proven
```

There are already independent product surfaces that expose this boundary:

- P3 `verify_agent_executor_identity()` has no credential-validity, possession, attestation, PKI or federation verifier and never emits `VERIFIED`;
- AP2 Human Present flow records `ap2_user_authorization_signature_not_verified` while the current frozen flow can still decide `ALLOW`;
- AP2 Human Not Present flow records `ap2_intent_authorization_signature_not_verified` while the current frozen flow can still decide `ALLOW`;
- ACP records seller/payee authenticity and order webhook signature as not verified.

This task does **not** assume these are one mechanism and does **not** authorize implementing TE05, PKI, wallet, blockchain, production authentication, or network verification.

Metric baseline: cross-surface authenticity gap ledger = `unknown`; P3 highest assurance = `BOUND`; AP2/ACP limitations exist as scattered per-adapter facts.  
Estimated affected scope: at least P3 payment execution identity, AP2 human-present/human-not-present authorization flows, and ACP checkout authenticity boundaries.  
Expected project impact: measurement only; determine whether the gaps form one repeated verifier family, several different gaps, or no actionable common capability.  
Rollback condition: measurement requires product changes, fabricated signature validity, production credentials/keys, network access, real payment side effects, or weakening existing fail-closed boundaries.

## Single objective / 单一目标

Measure six frozen probes across P3 + AP2 + ACP using only existing product code and fixtures, recording what authenticity evidence the product actually verifies versus what it only references or explicitly leaves `not_verified`.

Expected matrix:

`docs/05_任务交接/P9_ACTOR_AUTHENTICITY_SIGNED_INSTRUCTION_GAP_MEASUREMENT_V1/evaluator_fixtures/AUTHENTICITY_GAP_MATRIX.json`

Matrix SHA-256:

`cfa9896d543e9b32c215d7b1d801a15d55ad01bd29bfd15913a6a4cb3212ad17`

## Frozen probes / 冻结探针

Run exactly these six probes, each `repeat=2`:

1. `P01_P3_BOUND_NO_CREDENTIAL`
2. `P02_P3_EXPECTED_CREDENTIAL_CURRENT_MISSING`
3. `P03_P3_MATCHING_CREDENTIAL_REF_ONLY`
4. `P04_AP2_HP_USER_AUTH_SIGNATURE_UNVERIFIED`
5. `P05_AP2_HNP_INTENT_AUTH_SIGNATURE_UNVERIFIED`
6. `P06_ACP_WEBHOOK_PAYEE_AUTHENTICITY_UNVERIFIED`

### P3 probe semantics

Use one valid frozen offline payment-binding/context-policy fixture for P01-P03. Only credential-related inputs may vary among these three probes.

P01:

```text
identity.credential_ref = None
current_credential_ref = None
```

P02:

```text
identity.credential_ref = "credential-expected"
current_credential_ref = None
```

P03:

```text
identity.credential_ref = "credential-expected"
current_credential_ref = "credential-expected"
```

Record real product outputs:

- identity status;
- assurance level;
- identity reason codes;
- credential expected / observed / available flags;
- payment gate decision;
- callback count;
- whether product emitted `VERIFIED`.

The Evaluator matrix currently expects P01-P03 to remain `VALID / BOUND / ALLOW`, with callback count `1`, and never emit `VERIFIED`. If live frozen product behavior differs, record the deviation; do not repair product code in H-24.

### AP2 probes

P04 uses the existing `samples/protocol_snapshots/AP2_v020_HP_cards.json` through `adapt_ap2_flow_snapshot()` + `evaluate_ap2_flow()`.

Record:

- adapted ready;
- flow mode;
- product decision;
- exact `unmapped_fields` / limitation codes relevant to authenticity;
- whether any product field/result claims the user authorization signature was cryptographically verified.

P05 uses `samples/protocol_snapshots/AP2_v020_HNP_cards.json` through the same product APIs and records the same categories for intent authorization.

### ACP probe

P06 uses `samples/protocol_snapshots/ACP_S09_order_total_changed.json` through `adapt_acp_checkout_pair()`.

Record:

- adapted ready;
- exact authenticity-related `unmapped_fields`;
- seller/payee identity verification boundary;
- webhook signature verification boundary;
- whether any product field/result claims cryptographic signature verification.

Do not use the unrelated S09 amount-change decision as evidence that authenticity was verified or rejected.

## Product facts vs measurement diagnostics / 产品事实与测量诊断

Every probe result must separate:

```text
product_observation
measurement_diagnostics
```

`product_observation` may contain only values returned by existing product APIs or directly derived from their immutable dataclass/mapping outputs.

`measurement_diagnostics` may classify the observed boundary, for example:

```text
IDENTIFIER_BINDING_ONLY
CREDENTIAL_REFERENCE_WITHOUT_VERIFIER
AUTHORIZATION_SIGNATURE_NOT_VERIFIED
WEBHOOK_SIGNATURE_NOT_VERIFIED
PAYEE_IDENTITY_NOT_VERIFIED
```

These diagnostic labels are Evaluator/measurement taxonomy and must not be represented as product verification facts.

## Cross-surface grouping / 跨入口归类

The result must mechanically expose enough raw observations for Evaluator to group by mechanism. Executor may provide a diagnostic candidate grouping but must not issue the final architecture conclusion.

At minimum report:

- `surface_count_measured`;
- `probes_with_verified_authenticity`;
- `probes_with_explicit_not_verified_boundary`;
- unique limitation/reason codes;
- candidate mechanism families and member probe IDs;
- whether the same candidate mechanism appears across at least two distinct surfaces among `P3_IDENTITY_GATE`, `AP2_*`, `ACP_CHECKOUT`.

## Frozen product snapshot / 冻结产品快照

These product/tests/fixtures are immutable during H-24:

```text
src/agentic_payment_experiment/trusted_execution/execution_facts.py
cfd1ce9168eafecba894b45d5893be93b8c9e2f9668231a55a35930e23bb2c3c

src/agentic_payment_experiment/payment_execution.py
25113d7c067a6ba43bcae7a182c60ec77404a50229987b0314805b1c10e0ce71

src/agentic_payment_experiment/adapters/ap2.py
22325219bdcd02c69bedd26831608d3fe1752b0cc43e1e34a0442ff3a698b867

src/agentic_payment_experiment/adapters/acp.py
726848d2527da9dc916db20de9c7c08c93cfedc9e20be45a14f3a7c44b3c93dc

tests/trusted_execution/test_identity_assurance.py
8fd31115603dfe5cb6763d26684bed94a5dd14314a3ff7484e63309879988998

tests/test_ap2_flow_adapter.py
9a821ffca517c73e4148f1f70e0290e08a8dd290cbb71b4d19689a5c1951bda1

tests/test_ap2_adapter.py
162969aaa6c50dddd54e27f4a4aeb273b36bace188db371ba12f60bbcac8324c

tests/test_acp_adapter.py
e6fc93f9f3c83151ea61f27ab2d2e602379b02d598c278f22a30aab1ed081b13

samples/protocol_snapshots/AP2_v020_HP_cards.json
cf7c55e62cb3d8d90861575c9a0a5fba46d75d5ae676cffaa4a9cd16c0aa80c8

samples/protocol_snapshots/AP2_v020_HNP_cards.json
bcd63d8b46263927a8ccb06f30f88580507665db00d054e08fc2876307da6481

samples/protocol_snapshots/ACP_S09_order_total_changed.json
a519a0449295a3bbb2fac5130e9177439bbea64df23b2404fe3db5e7a8b8363a
```

## Allowed scope / 允许修改范围

Main measurement implementation:

- `scripts/validation/run_actor_authenticity_gap_measurement.py`

Task-owned outputs:

- `docs/05_任务交接/P9_ACTOR_AUTHENTICITY_SIGNED_INSTRUCTION_GAP_MEASUREMENT_V1/REPORT.md`
- `docs/05_任务交接/P9_ACTOR_AUTHENTICITY_SIGNED_INSTRUCTION_GAP_MEASUREMENT_V1/evidence/**`

Optional runner-only regression test if required:

- `tests/test_actor_authenticity_gap_measurement.py`

Evaluator-owned contract/fixture/plan/checkers are read-only.

## Required result / 结果要求

Expected result path:

`docs/05_任务交接/P9_ACTOR_AUTHENTICITY_SIGNED_INSTRUCTION_GAP_MEASUREMENT_V1/evidence/H24_AUTHENTICITY_GAP_RESULT.json`

Expected schema:

`actor-authenticity-signed-instruction-gap-measurement/v1`

Each probe must include:

```text
probe_id
surface
measurement_complete
repeat_identical
run_digests[2]
product_observation
measurement_diagnostics
expected_observation
expectation_match
```

Top-level summary must include the cross-surface fields listed above plus guardrails.

## Acceptance criteria / 验收标准

### AC-01 — Product/fixtures frozen
All frozen hashes remain unchanged. H-24 contains no credential/signature verifier implementation and no product patch.

### AC-02 — Six probes complete and deterministic
Exactly 6/6 probes measured, each repeat=2, repeat observations/digests identical. No probe may be skipped because authenticity is unverified.

### AC-03 — P3 current assurance boundary measured
P01-P03 record real identity status, assurance level, credential evidence flags, payment gate decision and callback count. No diagnostic label may be substituted for a product output.

### AC-04 — AP2 authenticity limitations measured
P04/P05 run the real existing AP2 adapters/evaluator and record exact product decisions plus relevant `*_signature_not_verified` limitation codes. No signature is fabricated as valid/invalid.

### AC-05 — ACP authenticity limitations measured
P06 runs the real existing ACP adapter and records the exact seller/payee/webhook authenticity limitations. Unrelated S09 business decision must not be used as signature-verification evidence.

### AC-06 — VERIFIED / cryptographic claims remain honest
The result explicitly records whether any product surface produced `VERIFIED` actor assurance or cryptographic signature-valid result. Measurement diagnostics must not promote `BOUND`, field presence, reference equality, `user_signed=true`, or protocol fixture fields into cryptographic verification.

### AC-07 — Cross-surface grouping is auditable
Raw codes/observations are sufficient to recompute surface count, explicit-not-verified count, unique limitation/reason codes and candidate mechanism membership. Executor does not decide the final product architecture.

### AC-08 — Project guardrails unchanged
- identity/payment-binding focused tests PASS;
- AP2/ACP adapter focused tests PASS;
- project-impact baseline repeat=3, `all_identical=true`;
- Product Trace >= `10/12`;
- GESR >= `9/12`;
- callback=`12/12`;
- duplicate/forbidden side effect=`0/12`;
- unsafe allow=`0/5` on the existing project baseline metric;
- formal scenario entrypoint `13/13 PASS`;
- full unittest zero failures;
- external network / real payment / real credential/key use = `0`.

### AC-09 — v2.2 handoff
Frozen L2 mandatory checks PASS; REPORT maps AC-01..09 to EV, includes all six probes, exact product observations, diagnostic grouping, limitation/reason-code ledger, guardrails, hashes, deviations and stop-condition status; workflow validator `OK` before submission.

## Stop conditions / 停止条件

Stop and return `BLOCKED` if:

- any frozen product/adapter/fixture must change;
- measurement requires real credential material, key generation, external identity provider, SDK installation or network;
- Executor needs to implement signature verification to obtain a measurement;
- AP2/ACP fixtures must be rewritten to manufacture a gap;
- product limitation codes must be removed/renamed to pass the task;
- more than `2` complete runner→L2 cycles are required.

## Exclusions / 明确排除

- no TE05 implementation;
- no PKI / SPIFFE / OIDC / OAuth deployment;
- no passkey / biometric / wallet / blockchain implementation;
- no real certificate, private key, token or credential;
- no AP2/ACP/x402 network calls;
- no production identity/authentication claim;
- no T05/T06 Product Trace repair;
- no Consumer/Player changes;
- no commit/push/history rewrite.

## Budget / authorization

- max complete runner→L2 cycles: `2`
- local CPU only
- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- real payment/credential/key/signature operation: false

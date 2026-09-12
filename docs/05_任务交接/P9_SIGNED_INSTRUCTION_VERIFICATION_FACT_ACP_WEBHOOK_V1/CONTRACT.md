# Frozen Task Contract

Task ID: `P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1`  
Task name: Signed Instruction Verification Fact + ACP Webhook HMAC First Consumer  
Task kind: `capability_experiment`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `d26fa658b970f84ca25859d7c3739994cae10a61`  
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-12-r36`  
Active bottleneck: `B-15` / `B-15A Signed Instruction Verification`  
Hypothesis: `H-25`  
Validation plan file: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

H-24 已独立复核 `PASS / NOT_APPLICABLE / CONTINUE`：

- P3 三条路径最高只到 `BOUND`，属于 Credential / Possession（凭证 / 持有证明）子问题；
- AP2 Human Present、AP2 Human Not Present、ACP 三个独立入口都显式保留 cryptographic signature `not_verified`；
- H-24 product `VERIFIED=0/6`，没有虚假真实性结论；
- L3 `7/7 PASS`、34/34 focused、662/662 full regression、真实副作用 0。

因此 B-15 拆为：

```text
B-15A Signed Instruction Verification【当前】
B-15B Credential / Possession Verification【后续】
```

当前不建设万能身份系统。B-15A 先验证一个最小、协议中立、可回放的 Signed Instruction Verification Fact（签署指令验证事实），并让 ACP 2026-04-17 Webhook HMAC 成为第一个真实协议消费者。

### External protocol basis / 外部协议依据

ACP 2026-04-17 官方 Webhook OAS 规定：

```text
Merchant-Signature: t=<unix_seconds>,v1=<64_hex>
signed payload = timestamp + "." + raw_body
algorithm = HMAC-SHA256
missing / malformed / timestamp-out-of-window / verification failure => reject
recommended timestamp tolerance = 300 seconds
```

本任务只验证上述明确协议机制，不声称完整 ACP conformance（协议一致性认证）。

### External requirement impact / 外部要求影响

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-06]
  applicability: ADAPTER
  maturity_before: M1
  maturity_after: M3
  test_evidence:
    - ACP signed-webhook positive/negative matrix
  trace_evidence: []
  residual_risk:
    - no live ACP endpoint
    - no production merchant secret
    - no AP2 SD-JWT verification
    - no P3 credential possession verification
    - no regulatory compliance claim
```

这里的 maturity_after 是任务目标，不是预先验收结论；只有 Evaluator 独立复核通过后才能采用。

## Measured baseline / 测量基线

Metric baseline: H-24 ACP `order_webhook_signature_not_verified`; executable signed-webhook semantic cases `0/6`; Product Trace `10/12`; GESR `9/12`; callback `12/12`; duplicate/forbidden side effect `0/12`; unsafe allow `0/5`.

H-24 accepted result:

`docs/05_任务交接/P9_ACTOR_AUTHENTICITY_SIGNED_INSTRUCTION_GAP_MEASUREMENT_V1/evidence/H24_AUTHENTICITY_GAP_RESULT.json`

SHA-256:

`4b2829adfb743a5e940d6e46908f9e89ec63518ca0c93c37a6fa8b1f6b29322c`

Current ACP observation:

```text
P06 explicit limitation = order_webhook_signature_not_verified
cryptographic signature verified = false
executable signed-webhook semantic cases = 0/6
```

Targeted capability signal:

```text
0/6 → 6/6 frozen signed-webhook semantic cases
```

This targeted signal is separate from the existing 12-task GESR baseline. H-25 must not claim that a new signature primitive automatically improves GESR.

Estimated affected scope: ACP webhook authenticity immediately; future AP2 signed Mandate or other signed-message consumers only if a later task proves reuse.  
Expected project impact: `IMPROVED` only if a protocol-neutral fact is actually consumed by ACP and all frozen positive/negative semantics pass without weakening existing guardrails.  
Rollback condition: capability requires AP2-specific code in the generic layer, production secrets, network, external SDK, business `ALLOW` coupling, P3 `VERIFIED` upgrade, or a second unrelated security mechanism.

## Single objective / 单一目标

Add one protocol-neutral Signed Instruction Verification（签署指令验证）capability and one ACP Webhook consumer, proving the same fact model can distinguish valid HMAC evidence from tampered, wrong-key, stale, missing, and malformed evidence without storing secrets/raw payloads or making business authorization decisions.

## One principal change / 唯一主要变化

```text
SignedInstructionVerificationFact
        +
protocol-neutral HMAC-SHA256 verifier
        +
ACP Merchant-Signature adapter consuming that verifier
```

These three pieces are one capability slice: fact contract → verifier → first protocol consumer. Do not add identity proofing, PKI, AP2 SD-JWT, wallet, policy engine, or Trace integration in this task.

## Frozen case matrix / 冻结案例矩阵

Path:

`docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evaluator_fixtures/ACP_WEBHOOK_SIGNATURE_MATRIX.json`

SHA-256:

`ea9224839b6b183abdf613d5759640ddc21062bd415348f3b7e4f383840d2994`

Run exactly six cases:

1. `V01_VALID_SIGNATURE`
2. `N01_TAMPERED_BODY`
3. `N02_WRONG_SECRET`
4. `N03_STALE_TIMESTAMP`
5. `N04_MISSING_SIGNATURE_HEADER`
6. `N05_MALFORMED_SIGNATURE_HEADER`

Expected semantics are frozen in the matrix. Repeat each case twice in the capability runner.

## Required product design / 必须满足的产品设计

### 1. Protocol-neutral fact / 协议中立事实

Add a frozen dataclass or equivalent closed structure named `SignedInstructionVerificationFact` in Trusted Execution（可信执行）scope.

It must expose at least:

```text
status: VALID | INVALID | MISSING_EVIDENCE
reason_codes
algorithm
signer_ref
key_ref
signed_payload_sha256
signed_at_epoch
observed_at_epoch
max_age_seconds
cryptographic_signature_verified
```

Rules:

- no raw secret;
- no private key;
- no full raw payload/body;
- no raw credential/token/cookie;
- no business decision field (`ALLOW / DENY / CONFIRMATION_REQUIRED` etc.);
- `cryptographic_signature_verified=true` only when HMAC comparison and freshness checks succeed;
- `VALID` proves only the supplied key verified the exact signed bytes under the frozen algorithm. It does not prove business authorization, legal identity, merchant legitimacy, user intent correctness, or regulatory compliance.

### 2. Protocol-neutral verifier / 协议中立验证器

Add a generic HMAC-SHA256 signed-instruction verifier in Trusted Execution（可信执行）scope.

It receives already-determined signed bytes / signature material / synthetic secret / signer-key references / timestamps. It must not parse `Merchant-Signature`, know ACP field names, or import payment-domain decisions.

Use Python standard-library `hmac` / `hashlib`; do not add dependencies.

Comparison must use constant-time comparison such as `hmac.compare_digest`.

### 3. ACP first consumer / ACP 首个消费者

Add a new ACP Webhook module, preferably:

`src/agentic_payment_experiment/adapters/acp_webhook.py`

It owns ACP-specific parsing:

```text
Merchant-Signature: t=<unix_seconds>,v1=<64_hex>
```

and constructs exact signed bytes:

```text
str(timestamp).encode("ascii") + b"." + raw_body
```

It then calls the protocol-neutral verifier. It must not duplicate HMAC comparison logic.

The existing `adapters/acp.py` checkout-pair adapter remains frozen and continues to expose its existing `order_webhook_signature_not_verified` limitation because that snapshot does not contain an authenticated webhook. H-25 adds a separate real webhook verification path; it does not launder old evidence.

## Frozen semantic boundaries / 冻结语义边界

- `V01` → `VALID`, `signed_instruction_signature_valid`, cryptographic verified true.
- body tamper / wrong secret → `INVALID`, `signed_instruction_signature_mismatch`.
- stale timestamp beyond tolerance → `INVALID`, `signed_instruction_timestamp_outside_window`.
- missing header → `MISSING_EVIDENCE`, `signed_instruction_signature_missing`.
- malformed header → `INVALID`, `signed_instruction_signature_format_invalid`.
- exact boundary at tolerance must be deterministic; define and test whether `abs(observed-signed) <= max_age_seconds` is accepted. Contract expectation: inclusive window (`<=`) is valid.
- future timestamps outside the same absolute tolerance are invalid; do not check only “too old”.
- signature header parser must reject duplicate/extra components rather than silently choosing one.

## Required capability result / 结果文件

Runner:

`scripts/validation/run_signed_instruction_verification_capability.py`

Result:

`docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/H25_SIGNED_INSTRUCTION_RESULT.json`

Schema:

`signed-instruction-verification-capability/v1`

Result must contain:

```text
cases[6]
  case_id
  repeat_identical
  run_digests[2]
  observed_status
  observed_reason_codes
  cryptographic_signature_verified
  signer_ref
  key_ref
  signed_payload_sha256
  expectation_match
summary
  cases_passed
  cases_total
  baseline_executable_cases
  after_executable_cases
  valid_positive_cases
  negative_cases_fail_closed
external_requirement_impact
  profile
  requirement_ids
  applicability
  maturity_before
  maturity_after
guardrails
```

The result must not contain the test secret, raw HMAC key bytes, full raw body, raw signature header, or raw signature value.

## Allowed implementation scope / 允许修改范围

Allowed scope: only the new protocol-neutral Signed Instruction fact/verifier, new ACP Webhook consumer, their package exports, bounded validation runner/tests, and task-owned REPORT/evidence listed below.

Product:

- `src/agentic_payment_experiment/trusted_execution/signed_instruction.py` NEW
- `src/agentic_payment_experiment/trusted_execution/__init__.py`
- `src/agentic_payment_experiment/adapters/acp_webhook.py` NEW
- `src/agentic_payment_experiment/adapters/__init__.py`

Validation / tests:

- `scripts/validation/run_signed_instruction_verification_capability.py` NEW
- `tests/trusted_execution/test_signed_instruction.py` NEW
- `tests/test_acp_webhook_signature.py` NEW

Task-owned:

- `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/REPORT.md`
- `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/**`

Evaluator-owned CONTRACT / matrix / Validation Plan / evaluator_checks are read-only.

## Protected / frozen existing files

The following must remain byte-identical:

```text
src/agentic_payment_experiment/adapters/acp.py
726848d2527da9dc916db20de9c7c08c93cfedc9e20be45a14f3a7c44b3c93dc

src/agentic_payment_experiment/adapters/ap2.py
22325219bdcd02c69bedd26831608d3fe1752b0cc43e1e34a0442ff3a698b867

src/agentic_payment_experiment/trusted_execution/execution_facts.py
cfd1ce9168eafecba894b45d5893be93b8c9e2f9668231a55a35930e23bb2c3c

src/agentic_payment_experiment/payment_execution.py
25113d7c067a6ba43bcae7a182c60ec77404a50229987b0314805b1c10e0ce71

scripts/validation/run_actor_authenticity_gap_measurement.py
217f1d818e58b2e71df63c38598cc8b7171e5aa9268a3d833d11308215536794

H-24 accepted result
4b2829adfb743a5e940d6e46908f9e89ec63518ca0c93c37a6fa8b1f6b29322c
```

## Acceptance criteria / 验收标准

### AC-01 — Protocol-neutral fact contract
`SignedInstructionVerificationFact` exists, stable/serializable, contains required audit fields, contains no raw secret/body/signature, and contains no payment decision.

### AC-02 — Generic verifier is actually generic
HMAC-SHA256 verification and freshness live in Trusted Execution（可信执行）and contain no ACP header/parser/business names. Constant-time comparison is used. No new dependency.

### AC-03 — ACP consumer follows frozen 2026-04-17 format
ACP Webhook adapter strictly parses `t=<unix>,v1=<64_hex>`, signs exact `timestamp + "." + raw_body`, uses default tolerance 300 seconds, and delegates HMAC verification to the generic verifier.

### AC-04 — Six-case capability semantics
Exactly 6/6 frozen cases match expected status/reason/verified semantics, repeat=2 deterministic. Inclusive freshness boundary is tested; an out-of-window future timestamp is also tested in focused unit tests even though it is not one of the six headline cases.

### AC-05 — Fail-closed and evidence honesty
Missing evidence never becomes VALID; malformed signature never becomes VALID; tampered body/wrong key/stale/future-out-of-window fail. `VALID` is not mapped to business ALLOW and does not upgrade P3 identity to `VERIFIED`.

### AC-06 — First real protocol consumer
ACP Webhook adapter imports/uses the generic verifier; no duplicated HMAC comparison exists in the adapter. The capability is not a dead helper.

### AC-07 — Sensitive-data minimization
Product fact, runner result, REPORT, and evidence JSON do not persist the synthetic secret, raw body, raw signature header/value, production credential, private key, token, cookie, PAN/CVV. Test fixture secret may exist only in evaluator fixture / test-generation input and local ephemeral variables.

### AC-08 — Existing H-24 boundary remains stable
Protected P3/AP2/ACP checkout code is byte-identical. Re-running H-24 yields the accepted result byte-for-byte: SHA-256 `4b2829adfb743a5e940d6e46908f9e89ec63518ca0c93c37a6fa8b1f6b29322c`.

### AC-09 — Project guardrails unchanged
- project-impact baseline repeat=3 identical;
- Product Trace >= 10/12;
- GESR >= 9/12;
- callback 12/12;
- duplicate/forbidden side effect 0/12;
- unsafe allow 0/5;
- formal scenarios 13/13 PASS;
- full unittest zero failures;
- network / real payment / production credential-key-secret use = 0.

### AC-10 — External-requirement boundary remains honest
REPORT contains `PCAC-AGENTPAY / PCAC-06 / ADAPTER` before/after maturity evidence and residual risks. No compliance claim.

### AC-11 — v2.2 handoff complete
Frozen L2 mandatory plan passes; REPORT maps AC-01..11 to EV, contains targeted `0/6→6/6` comparison, protected hashes, six cases, secret-leak check, project guardrails, external_requirement_impact, deviations, stop-condition status; workflow validator returns `OK` before submission.

## Stop conditions / 停止条件

Stop and return `BLOCKED` if:

- existing `acp.py`, `ap2.py`, P3 identity/payment gate, or H-24 measurement must change;
- ACP HMAC logic cannot be implemented from the frozen official contract without inventing semantics;
- real/production secret or network is required;
- implementation needs AP2 SD-JWT / JWT credential verification;
- implementation couples signature validity directly to Payment `ALLOW` or Identity `VERIFIED`;
- secret/raw body must be stored in the fact/result to pass tests;
- a new dependency or package install is required;
- more than 2 complete implementation→L2 cycles are required.

## Explicit exclusions / 明确排除

- no AP2 SD-JWT / VDC / Mandate cryptographic verification;
- no P3 credential validity / proof-of-possession / `VERIFIED` upgrade;
- no PKI, OAuth/OIDC, SPIFFE, Passkey, biometrics, wallet or blockchain;
- no live ACP endpoint or conformance certification;
- no real merchant secret / production key;
- no Trace / Consumer / Player integration in H-25;
- no business policy change;
- no T05/T06 Product Trace work;
- no network / API / dependency install;
- no commit / push / history rewrite.

## Budget / authorization

- max complete implementation→L2 cycles: `2`
- local CPU only
- synthetic local HMAC fixture operations: allowed
- production/real cryptographic operations: false
- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- real payment / credential / private-key / merchant-secret use: false

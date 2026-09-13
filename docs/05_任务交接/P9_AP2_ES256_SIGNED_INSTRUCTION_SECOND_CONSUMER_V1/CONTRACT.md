# Frozen Task Contract

Task ID: `P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1`  
Task name: AP2 ES256 Signed Instruction Second Consumer  
Task kind: `capability_experiment`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `8b9d5b46516cad330c89acf7822598a33dc9007c`  
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-13-r38`  
Active bottleneck: `B-15` / `B-15A Signed Instruction Verification`  
Hypothesis: `H-27`  
Validation plan file: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

H-25 已独立复核 `PASS / IMPROVED / CONTINUE`：ACP HMAC 已成为 `SignedInstructionVerificationFact` 的第一个真实消费者，六案例 `6/6`，Evaluator L3 `10/10 PASS`，full unittest=`675/675`。

H-26 evidence gate 已完成，结论 `READY_FOR_AP2_SECOND_CONSUMER`：

`docs/05_任务交接/P9_AP2_SIGNED_MANDATE_VERIFIABLE_FIXTURE_FEASIBILITY_V1/EVIDENCE_DECISION.md`

本轮只冻结 AP2 的稳定最小交集：merchant-signed compact JWT、ES256/P-256、`kid`、merchant signer、`iat/exp`。不声称完整 AP2 / SD-JWT conformance。

## External requirement impact / 外部要求影响

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-06]
  applicability: ADAPTER
  maturity_before: M3
  maturity_after: M4
  test_evidence:
    - AP2 ES256 second-consumer matrix
    - H-25 first-consumer regression
  trace_evidence: []
  residual_risk:
    - synthetic fixture only
    - no live JWKS/DID/PKI
    - no SD-JWT holder binding
    - no full AP2 conformance claim
```

## Measured baseline / 测量基线

Metric baseline: real Signed Instruction consumers=`1` (ACP HMAC); AP2 ES256 executable cases=`0/6`; Product Trace=`10/12`; GESR=`9/12`; callback=`12/12`; unsafe allow=`0/5`; formal scenarios=`13/13`; full unittest=`675/675`.

Estimated affected scope: B-15A Signed Instruction Verification only; immediate new surface is the bounded AP2 ES256 merchant-authorization adapter plus the protocol-neutral ES256 verifier; no Payment Policy / Trace / P3 identity upgrade.

Expected project impact: `IMPROVED` only if AP2 frozen semantics reach `0/6→6/6`, real Signed Instruction consumers reach `1→2`, H-25 accepted result stays byte-identical, and existing project guardrails do not regress.

Rollback condition: return `BLOCKED` and do not keep the H-27 product change if AP2-specific/business fields must enter Trusted Execution, existing `ap2.py` must change, H-25 result changes, new package installation/network is required, or full SD-JWT/VC/DID/JWKS machinery becomes necessary for the six frozen cases.

```text
real Signed Instruction consumers = 1 (ACP HMAC)
ACP H-25 = 6/6
AP2 ES256 executable cases = 0/6
Product Trace = 10/12
GESR = 9/12
callback = 12/12
unsafe allow = 0/5
formal scenarios = 13/13
full unittest = 675/675
```

H-25 accepted result SHA-256:
`888d8d9ae215ce3d4ac593c190a2863746fddf1d99ca78175324670615b22a37`

Target:

```text
real consumers: 1 → 2
AP2 ES256: 0/6 → 6/6
H-25 accepted result hash unchanged
```

## Single objective / 单一目标

让现有 `SignedInstructionVerificationFact` 被第二个协议、第二种签名机制真实消费：新增 protocol-neutral ES256 compact-JWS verifier（协议中立 ES256 JWS 验证器）和 AP2 merchant authorization adapter（适配器）。

## One principal change / 唯一主要变化

```text
existing SignedInstructionVerificationFact
        +
generic ES256 compact-JWS verifier
        +
AP2 merchant-authorization second consumer
```

## Frozen matrix / 冻结案例矩阵

Path:
`docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evaluator_fixtures/AP2_ES256_JWS_MATRIX.json`

SHA-256:
`17b10958e319d965fa081144824a4d54773b52a5b90314aafcc86252150ce605`

Exactly six headline cases, repeat=2:

1. `V01_VALID_ES256_JWS`
2. `N01_TAMPERED_PAYLOAD`
3. `N02_WRONG_PUBLIC_KEY`
4. `N03_WRONG_SIGNER_BINDING`
5. `N04_MISSING_AUTHORIZATION`
6. `N05_MALFORMED_COMPACT_JWS`

Focused tests must additionally cover unsupported `alg`, wrong `kid`, future `iat`, expired `exp`, invalid `exp < iat`, malformed/non-P256 JWK.

## Required design / 必须满足的设计

### Protocol-neutral fact

Reuse `SignedInstructionVerificationFact`; do not create an AP2-specific fact.

For AP2 ES256:

```text
algorithm = ES256
signed_payload_sha256 = SHA-256(compact JWS signing input)
signed_at_epoch = iat
observed_at_epoch = frozen observation time
max_age_seconds = exp - iat
cryptographic_signature_verified = true only after all frozen crypto/binding checks pass
```

Valid time window: `iat <= observed_at <= exp`.

`VALID` never means Payment `ALLOW`, legal identity, credential validity, or regulatory compliance.

### Generic ES256 verifier

Frozen public function name: `verify_es256_compact_jws_signed_instruction`.

Trusted Execution may know compact JWS structure, JOSE `alg/kid`, ES256/P-256 public JWK, signer/key refs and timestamps. It must not know AP2 Mandate/cart/payment fields or business decisions.

Use the locally available `cryptography` package. The Executor may declare `cryptography>=41` in `pyproject.toml`; package installation/network access is forbidden. Do not add PyJWT/jwcrypto/authlib.

### AP2 second consumer

Add:
`src/agentic_payment_experiment/adapters/ap2_signed_instruction.py`

Existing `adapters/ap2.py` stays frozen.

The new adapter owns AP2-shaped claim mapping for this bounded profile: `iss`, `iat`, `exp` and required AP2 JWT shape. It validates expected signer binding and delegates ES256 verification to the generic verifier. It must not validate business meaning of `cart_hash` in H-27.

## Frozen semantics / 冻结语义

- valid token + matching signer/key/time → `VALID / signed_instruction_signature_valid`;
- payload tamper → `INVALID / signed_instruction_signature_mismatch`;
- wrong public key → `INVALID / signed_instruction_signature_mismatch`;
- signer mismatch → `INVALID / signed_instruction_signer_mismatch`;
- missing token → `MISSING_EVIDENCE / signed_instruction_signature_missing`;
- malformed compact JWS → `INVALID / signed_instruction_compact_jws_format_invalid`;
- unsupported alg → `INVALID / signed_instruction_algorithm_unsupported`;
- wrong kid → `INVALID / signed_instruction_key_ref_mismatch`;
- future/expired token → `INVALID / signed_instruction_timestamp_outside_window`.

## Required result / 结果文件

Runner:
`scripts/validation/run_ap2_es256_signed_instruction_capability.py`

Result:
`docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/H27_AP2_ES256_RESULT.json`

Schema:
`ap2-es256-signed-instruction-capability/v1`

Result records six-case semantics, repeat digests, signer/key refs, signed-input hash, consumer count `1→2`, H-25 regression hash, external requirement impact and zero-real-side-effect guardrails.

## Allowed scope / 允许范围

Product:

- `src/agentic_payment_experiment/trusted_execution/signed_instruction.py`
- `src/agentic_payment_experiment/trusted_execution/__init__.py`
- `src/agentic_payment_experiment/adapters/ap2_signed_instruction.py` NEW
- `src/agentic_payment_experiment/adapters/__init__.py`
- `pyproject.toml` only for `cryptography>=41`

Validation/tests:

- `scripts/validation/run_ap2_es256_signed_instruction_capability.py` NEW
- `tests/trusted_execution/test_signed_instruction_es256.py` NEW
- `tests/test_ap2_signed_instruction.py` NEW

Task-owned REPORT/evidence are allowed. Evaluator-owned CONTRACT/matrix/Validation Plan/checks are read-only.

## Protected / frozen behavior

Must remain byte-identical:

```text
src/agentic_payment_experiment/adapters/ap2.py
22325219bdcd02c69bedd26831608d3fe1752b0cc43e1e34a0442ff3a698b867

src/agentic_payment_experiment/adapters/acp_webhook.py
cc723725eb3fd220482bbc21721843d77ba92e7b7a7c29431753e6c6e0e4ffac
```

H-25 runner stays unchanged and its regenerated result must keep SHA-256:
`888d8d9ae215ce3d4ac593c190a2863746fddf1d99ca78175324670615b22a37`

Existing `SignedInstructionVerificationFact` public fields remain backward-compatible.

## Acceptance criteria / 验收标准

### AC-01 — Fact remains protocol-neutral
Same fact supports HMAC and ES256; no AP2-specific fields enter the fact; H-25 result unchanged.

### AC-02 — Generic ES256 verifier is generic
No AP2/business imports or branches inside Trusted Execution.

### AC-03 — AP2 second consumer is real
New AP2 adapter actually calls the generic verifier; existing `ap2.py` remains frozen.

### AC-04 — Six headline cases
Frozen matrix `6/6`, repeat=2 deterministic.

### AC-05 — Additional negative boundaries
Unsupported alg, wrong kid, time-window violations and malformed JWK fail closed.

### AC-06 — Second-consumer proof
Real Signed Instruction consumers increase `1→2` with no protocol switch inside the fact layer.

### AC-07 — Sensitive-data boundary
No production credentials or real payment data; evaluator fixture is synthetic/test-only.

### AC-08 — H-25 regression stability
Re-running H-25 reproduces accepted result hash exactly.

### AC-09 — Project guardrails
Product Trace >=10/12; GESR >=9/12; callback=12/12; duplicate/forbidden side effect=0/12; unsafe allow=0/5; S01-S13=13/13; full unittest zero failures; network/real-payment/production-credential use=0.

### AC-10 — Dependency boundary
Only `cryptography>=41` may be declared; no install/network and no extra JWT framework.

### AC-11 — External requirement honesty
REPORT records `PCAC-AGENTPAY / PCAC-06 / ADAPTER` and residual risks; no conformance/compliance claim.

### AC-12 — v2.2 handoff complete
Frozen L2 passes; REPORT maps AC-01..12 to evidence and includes `1→2`, `0/6→6/6`, H-25 stability, guardrails and deviations; workflow validator returns `OK` before submission.

## Stop conditions / 停止条件

Return `BLOCKED` if existing `ap2.py` must change, generic layer needs AP2/business fields, valid signature must imply Payment `ALLOW`/Identity `VERIFIED`, local `cryptography` is unavailable, complete SD-JWT/VC/DID/JWKS is required for the six cases, H-25 accepted result changes, or more than two complete implementation→L2 cycles are needed.

## Explicit exclusions / 明确排除

No complete AP2 conformance; no SD-JWT disclosure/delegate chain; no holder key binding; no Payment Mandate `transaction_data`; no business `cart_hash` correctness; no live JWKS/DID/PKI; no P3 `VERIFIED`; no wallet/blockchain/testnet/bank sandbox; no Trace/Player expansion; no commit/push/history rewrite.

## Budget / authorization

- max implementation→L2 cycles: `2`
- local CPU only
- evaluator-owned synthetic ES256 fixture: allowed
- existing local `cryptography`: allowed
- dependency install: false
- network/API call: false
- real payment/production credential use: false
- commit/push/history_rewrite: false

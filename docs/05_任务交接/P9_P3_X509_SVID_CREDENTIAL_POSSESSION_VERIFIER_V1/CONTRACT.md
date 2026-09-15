# Frozen Task Contract

Task ID: `P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1`  
Task name: P3 X.509-SVID Credential / Possession Verifier v1  
Task kind: `capability_experiment`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `fca87c2d987b3d71c1156e50747cb8eeec1c84c7`  
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-15-r40`  
Active bottleneck: `B-15`  
Sub-bottleneck: `B-15B Credential / Possession Verification`  
Hypothesis: `H-29`  
Validation plan file: `docs/05_任务交接/P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

H-28 evidence gate（证据门）已给出：

`READY_FOR_P3_X509_SVID_CREDENTIAL_POSSESSION_CAPABILITY`

当前 P3 的 `verify_agent_executor_identity()` 只做 Agent / Provider / Executor / credential reference（凭证引用）的确定性关系核对；即使 `credential_ref` 相等，最高仍为 `VALID / BOUND`。这条边界必须保持。

当前第一瓶颈不是“再加一个身份字段”，而是：**怎样在不接生产 IAM / SPIRE / 网络的前提下，第一次用真实密码学证据证明当前 executor 确实持有一个由受信任根签发、且主体与现有 P3 身份绑定一致的 credential（凭证）？**

H-29 只做这一件事。

## Measured baseline / 测量基线

Metric baseline: `P3 product VERIFIED cases=0; credential_ref-only max assurance=BOUND; Product Trace=10/12; GESR=9/12; callback match=12/12; S01-S13=13/13; full unittest=692/692`  

```text
P3 credential_ref only              → max BOUND
P3 product VERIFIED cases           → 0
B-15A Signed Instruction consumers  → 2 (ACP/HMAC + AP2/ES256), STAGE_CLOSED
Product Trace                        → 10/12
GESR                                 → 9/12
callback match                       → 12/12
unsafe allow                         → 0/5
formal scenarios S01-S13             → 13/13
full unittest                        → 692/692 (H-27 accepted baseline)
real payment / production credential / live network → 0
```

Estimated affected scope: P3 Actor / Executor Identity Assurance（主体 / 执行器身份保证）这一条能力链；不修改 Payment policy（支付策略）、Signed Instruction（签署指令）、Trace、WebShop、AP2/ACP/x402 adapters（适配器）。

Expected project impact: `IMPROVED` only if the frozen valid vector becomes the first mechanically justified `BOUND → VERIFIED` case while all six negative vectors stay non-`VERIFIED`, the old credential-ref-only case remains `BOUND`, and project guardrails do not regress.

Rollback condition: return `BLOCKED` if implementation requires production SPIRE/PKI/OIDC/DID/VC, network or package install, Payment `ALLOW` semantics must change, Signed Instruction code must change, or `VERIFIED` can appear without all four frozen evidence conditions.

## Single objective / 单一目标

新增 protocol-neutral Credential / Possession Verification Fact（协议中立凭证 / 持有证明事实）与 bounded offline X.509-SVID verifier（有界离线验证器），接入现有 P3 identity binding（身份绑定）：

```text
existing P3 VALID / BOUND
        + credential valid
        + subject binding valid
        + proof-of-possession valid
        + freshness / replay valid
        ↓
VALID / VERIFIED
```

任何一项缺失或失败，都不得输出 `VERIFIED`。

## One principal change / 唯一主要变化

```text
CredentialPossessionVerificationFact
        ↓
verify_x509_svid_credential_possession(...)
        ↓
verify_agent_executor_identity(..., credential_possession_fact=...)
        ↓
仅四条件全通过时 BOUND → VERIFIED
```

这是一条 P3 身份保证增强，不新增第二套身份系统。

## Frozen evaluator vectors / 冻结评估向量

Vector:
`docs/05_任务交接/P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1/evaluator_fixtures/X509_SVID_POSSESSION_VECTOR.json`

SHA-256:
`b0ffc3a5707e403febb545bb8a142767e101a2c3edf42eaad40396552f9fe910`

Matrix:
`docs/05_任务交接/P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1/evaluator_fixtures/X509_SVID_POSSESSION_MATRIX.json`

SHA-256:
`9f72cc24c8557aee48f7b611ed71e3d253ad311c607e3260f713500140a8eda8`

Exactly seven headline cases, repeat=2:

1. `V01_VALID_BOUND_TO_VERIFIED`
2. `N01_WRONG_TRUST_BUNDLE`
3. `N02_WRONG_SPIFFE_SUBJECT`
4. `N03_NO_POSSESSION_PROOF`
5. `N04_BAD_POSSESSION_PROOF`
6. `N05_REPLAYED_NONCE`
7. `N06_STALE_CHALLENGE`

The fixture is evaluator-owned synthetic test-only material. It contains public certificates and one precomputed challenge signature; no private key is persisted.

## Required design / 必须满足的设计

### 1. Credential / possession fact

Add a protocol-neutral immutable fact. Exact class name is frozen as:

`CredentialPossessionVerificationFact`

It must expose enough audit fields to distinguish at least:

- `status` / stable `reason_codes`;
- `credential_format` = `X509-SVID`;
- `credential_ref`;
- `subject_ref` / SPIFFE ID;
- `trust_domain_ref`;
- leaf certificate fingerprint;
- `credential_valid`;
- `subject_binding_valid`;
- `proof_of_possession_valid`;
- `freshness_valid`;
- `replay_detected`;
- challenge / nonce reference and observed timestamp.

The fact must not contain Payment `ALLOW/DENY`, AP2/ACP fields, business amount/order semantics, private-key bytes, or production secrets.

### 2. Bounded X.509-SVID profile

Frozen public function name:

`verify_x509_svid_credential_possession`

This v1 profile is intentionally bounded:

```text
single synthetic trust root
→ directly issued leaf X.509-SVID
→ no intermediates / federation / CRL / OCSP
→ exactly one spiffe:// URI SAN
→ expected trust domain = agentic-payment.test
→ leaf CA=false
→ leaf KeyUsage digitalSignature=true
→ leaf keyCertSign=false / cRLSign=false
→ certificate validity checked at frozen observed time
→ leaf signature checked against the frozen trusted CA public key
```

Do not claim full RFC 5280 path validation or full SPIFFE conformance. The REPORT must state this limitation explicitly.

### 3. Subject mapping

For H-29 only, freeze the accepted SPIFFE ID shape:

`spiffe://agentic-payment.test/agent/{agent_id}/executor/{executor_instance_id}`

The verifier must mechanically compare parsed values to the expected P3 `agent_id` and `executor_instance_id`. `provider_ref` remains an existing P3 binding condition; do not encode provider into the SPIFFE path in v1.

A matching `credential_ref` alone remains insufficient.

### 4. Proof of possession

The frozen challenge payload is evaluator-owned and already signed by the leaf SVID private key before task execution. The implementation must verify that signature using the leaf certificate public key.

A missing signature → `MISSING_EVIDENCE`.
An invalid signature → `INVALID`.
A valid signature alone still does not produce `VERIFIED` unless trust + subject + freshness also pass.

### 5. Freshness / replay

The verifier must enforce:

```text
0 <= observed_at_epoch - issued_at_epoch <= max_age_seconds
```

and reject a `nonce_ref` already present in the caller-supplied consumed nonce collection.

The verifier itself remains deterministic and stateless; persistent nonce storage is explicitly out of scope. The caller supplies already-consumed nonce refs.

### 6. P3 promotion rule

`verify_agent_executor_identity()` may accept an optional `credential_possession_fact`.

Frozen rule:

```text
base identity binding != VALID / BOUND
→ preserve existing result; never promote

credential_possession_fact absent
→ preserve existing VALID / BOUND behavior

credential_possession_fact.status == VALID
AND credential_valid == true
AND subject_binding_valid == true
AND proof_of_possession_valid == true
AND freshness_valid == true
AND replay_detected == false
→ VALID / VERIFIED

otherwise
→ never VERIFIED
```

Negative credential/possession evidence must not silently disappear. It must be reflected in stable reason codes while preserving the existing distinction between base identity binding and credential verification. For H-29, failed optional stronger credential evidence blocks promotion only: when the existing base identity binding is still `VALID / BOUND`, the integrated identity fact remains `VALID / BOUND` rather than tightening Payment policy; the credential fact separately carries `INVALID / MISSING_EVIDENCE`.

### 7. Payment gate integration

`execute_with_payment_binding_gate()` may accept the optional credential-possession fact and pass it into P3. Existing callers that do not supply it must remain behaviorally identical.

Do **not** change the existing rule that both `BOUND` and `VERIFIED` are sufficient P3 assurance for the current payment lab callback gate. H-29 proves stronger identity evidence; it does not tighten Payment policy.

## Frozen semantics / 冻结语义

Headline reasons:

```text
V01 → VALID / VERIFIED / credential_possession_verified
N01 → not VERIFIED / credential_trust_invalid
N02 → not VERIFIED / credential_subject_binding_mismatch
N03 → not VERIFIED / credential_possession_proof_missing
N04 → not VERIFIED / credential_possession_signature_invalid
N05 → not VERIFIED / credential_possession_replay_detected
N06 → not VERIFIED / credential_possession_challenge_stale
```

Additional focused tests must fail closed for:

- malformed PEM / non-certificate input;
- no URI SAN / multiple URI SANs;
- non-`spiffe` URI;
- wrong trust domain;
- leaf `CA=true`;
- missing `digitalSignature` or leaf `keyCertSign=true`;
- certificate not-yet-valid / expired;
- challenge observed before issued time;
- credential fact `VALID` but base P3 binding invalid;
- legacy credential-ref-only path remains exactly `BOUND`.

## Required result / 结果文件

Runner:
`scripts/validation/run_p3_x509_svid_credential_possession_capability.py`

Result:
`docs/05_任务交接/P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1/evidence/H29_P3_X509_SVID_RESULT.json`

Schema:
`p3-x509-svid-credential-possession-capability/v1`

The result must record seven-case outcomes, repeat digests, four-condition flags, promotion count `0→1`, legacy BOUND regression, guardrails, dependency/network facts, and explicit residual-risk text.

## Allowed scope / 允许范围

Product:

- `src/agentic_payment_experiment/trusted_execution/credential_possession.py` NEW
- `src/agentic_payment_experiment/trusted_execution/execution_facts.py`
- `src/agentic_payment_experiment/trusted_execution/__init__.py`
- `src/agentic_payment_experiment/payment_execution.py`

Validation/tests:

- `scripts/validation/run_p3_x509_svid_credential_possession_capability.py` NEW
- `tests/trusted_execution/test_credential_possession.py` NEW
- `tests/trusted_execution/test_identity_assurance.py`
- `tests/trusted_execution/test_payment_binding.py` only for bounded P3 integration regression

Task-owned `REPORT.md` / evidence are allowed. Evaluator-owned CONTRACT / fixtures / Validation Plan / evaluator checks are read-only.

## Protected / frozen behavior

Must remain byte-identical:

```text
src/agentic_payment_experiment/trusted_execution/signed_instruction.py
6324a5912f1329b11abddb01a619a8088966ab562ef9f79ccad19b2d02d8c5a2

src/agentic_payment_experiment/adapters/ap2_signed_instruction.py
c0fad26bbeb44034a276d8bb491146a2d5cded3ae130baa611c77e341baa91ae

src/agentic_payment_experiment/adapters/acp_webhook.py
cc723725eb3fd220482bbc21721843d77ba92e7b7a7c29431753e6c6e0e4ffac

pyproject.toml
bc16c28fde7ba55e3de78c054efd2751bfcf6e033298ff0472fe3056023fbbd3
```

No dependency change is allowed; local `cryptography 41.0.7` is already sufficient for the bounded profile.

## Acceptance criteria / 验收标准

### AC-01 — Legacy P3 boundary preserved
Without credential-possession evidence, all existing P3 behavior remains unchanged; `credential_ref` equality alone remains `VALID / BOUND`, never `VERIFIED`.

### AC-02 — Protocol-neutral fact
`CredentialPossessionVerificationFact` contains only credential/identity/possession/freshness evidence and no Payment/AP2/ACP/x402 business fields or decisions.

### AC-03 — Credential validity is mechanically checked
The bounded synthetic direct-root X.509-SVID profile verifies trusted issuer signature, time validity, exactly one SPIFFE URI SAN, trust domain, BasicConstraints and KeyUsage.

### AC-04 — Subject binding is mechanically checked
The frozen SPIFFE path maps to the expected Agent and Executor; wrong subject never promotes.

### AC-05 — Proof of possession is mechanically checked
The valid frozen challenge signature verifies with leaf public key; missing/bad signature fails closed.

### AC-06 — Freshness / replay is mechanically checked
Stale, future-observed/negative-age and consumed nonce cases never promote.

### AC-07 — Exact promotion rule
Only base `VALID / BOUND` + all four credential conditions can produce `VALID / VERIFIED`; no shortcut exists.

### AC-08 — Seven headline cases
Frozen matrix reaches `7/7`, repeat=2 deterministic; exactly one case is `VERIFIED`.

### AC-09 — Payment policy unchanged
Existing callback policy still accepts existing BOUND path; adding VERIFIED evidence does not independently change `ALLOW/DENY/CONFIRMATION_REQUIRED/INDETERMINATE` policy.

### AC-10 — Signed Instruction stage isolated
H-25/H-27 protected sources stay byte-identical; credential verification does not reuse or modify `SignedInstructionVerificationFact`.

### AC-11 — Dependency / sensitive-data boundary
No dependency changes, no network/API calls, no live SPIRE, no production certificate/private key/trust bundle, no real payment; evaluator fixtures persist no private key.

### AC-12 — Project guardrails
Product Trace >=10/12; GESR >=9/12; callback=12/12; duplicate/forbidden side effect=0/12; unsafe allow=0/5; S01-S13=13/13; full unittest zero failures.

### AC-13 — Honest scope claim
REPORT explicitly says this is a bounded synthetic single-root/direct-leaf profile, not full RFC 5280 path validation, SPIFFE/SPIRE conformance, production authentication, legal identity, or regulatory compliance.

### AC-14 — v2.2 handoff complete
Frozen L2 Validation Plan passes; REPORT maps AC-01..14 to evidence, records `P3 VERIFIED 0→1`, negative matrix, legacy BOUND stability, project guardrails, and deviations.

## Stop conditions / 停止条件

Return `BLOCKED` if:

- implementation needs live SPIRE / Workload API / OIDC / DID / VC / JWKS;
- network/package installation is required;
- a private key must be persisted in task fixtures;
- full generic RFC 5280 chain building, CRL/OCSP or federation is needed for the frozen seven cases;
- Payment policy must change;
- Signed Instruction sources must change;
- `VERIFIED` can appear from credential reference equality, certificate signature alone, or possession signature alone;
- protected hashes change;
- more than two complete implementation→L2 cycles are needed.

## Explicit exclusions / 明确排除

No production PKI; no live SPIRE; no Workload API integration; no intermediate CA/federation; no CRL/OCSP; no JWT-SVID; no DPoP implementation; no VC/DID/BSN/OIDC Provider Adapter; no Passkey/biometrics; no wallet/blockchain/testnet/bank sandbox; no Payment policy tightening; no Signed Instruction changes; no Product Trace expansion; no conformance/compliance claim; no commit/push/history rewrite.

## Budget / authorization

- max implementation→L2 cycles: `2`
- local CPU only
- local existing `cryptography 41.0.7`: allowed
- evaluator-owned synthetic public cert/signature fixtures: allowed
- dependency install: false
- network/API call: false
- live SPIRE/PKI/OIDC/DID/VC: false
- real payment / production credential / private-key / trust-bundle use: false
- commit: false
- push: false
- history_rewrite: false

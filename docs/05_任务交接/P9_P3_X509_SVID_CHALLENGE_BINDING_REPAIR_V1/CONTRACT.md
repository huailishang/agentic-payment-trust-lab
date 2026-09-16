# Frozen Repair Contract

Task ID: `P9_P3_X509_SVID_CHALLENGE_BINDING_REPAIR_V1`  
Task name: P3 X.509-SVID Signed Challenge Binding Repair  
Task kind: `repair`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `fca87c2d987b3d71c1156e50747cb8eeec1c84c7`  
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-15-r41`  
Active bottleneck: `B-15`  
Sub-bottleneck: `B-15B Credential / Possession Verification`  
Inherited hypothesis: `H-29`  
Repair hypothesis: `H-29R`  
Parent task: `P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1`  
Validation plan file: `docs/05_任务交接/P9_P3_X509_SVID_CHALLENGE_BINDING_REPAIR_V1/VALIDATION_PLAN.yaml`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-15-r41`  
Active bottleneck: `B-15` / `B-15B Credential / Possession Verification`  
Hypothesis: `H-29R`  
Measurement status: measured  
Metric baseline: `parent frozen matrix=7/7; parent full unittest=698/698; metadata-relabel counterexample=FAIL (false VERIFIED); legacy credential_ref-only=BOUND; Product Trace=10/12; GESR=9/12; S01-S13=13/13`  
Estimated affected scope: one reproducible metadata-relabel false-VERIFIED path in the bounded local X.509-SVID possession verifier.  
Expected project impact: close that false-VERIFIED path while preserving parent H-29 capability and project guardrails.  
Rollback condition: parent frozen matrix, legacy BOUND behavior, protected hashes, or project guardrails regress.  
Dispatch mode: `SINGLE`  
Expected material cost: low; local CPU only, no network/API, at most two implementation→L2 cycles.  
Bounded retry / iteration budget: `2` complete implementation→L2 cycles.  
Expected value of another round if successful: restore a sound local bounded `BOUND→VERIFIED` proof before any external/provider-backed identity work.

## Failed parent criteria / 父任务失败项

Parent Evaluator REVIEW：`REJECTED / REGRESSED / CONTINUE`。

失败项：

- Parent criterion 06 — Freshness / replay
- Parent criterion 07 — Exact promotion rule

Evaluator counterexample：`parent/evidence/RV-EV-09.*`。

当前实现允许：

```text
old signed challenge payload + old signature
+ attacker-supplied fresh nonce_ref / issued_at / observed_at metadata
→ VALID / credential_possession_verified
→ P3 VERIFIED
```

根因：签名覆盖 `challenge_payload`，但 `nonce_ref / issued_at_epoch` 等新鲜度元数据由函数参数单独传入，没有机械证明它们就是被签名 payload 中的值。

## Metric baseline / 指标基线

Metric baseline: `parent frozen matrix=7/7; parent full unittest=698/698; metadata-relabel counterexample=FAIL (false VERIFIED); legacy credential_ref-only=BOUND; Product Trace=10/12; GESR=9/12; S01-S13=13/13`  

Rejected parent snapshot hashes：

```text
credential_possession.py   7eeff27ac6e0b32d2c1d543e49f363cc93f217586661eb8a5fa8a78dc12ba8c9
execution_facts.py         5ff68c16330d3a6570d6a9b53f406a55cd5ee99207867532af74461fd76eeef6
payment_execution.py       d161be5afe73192491e20203651dc3b222fa37454235c1bacc37042c6254fb49
H29 runner                 6132c68eaeaa000bc23eec3255710ca84bc198c28d12fb6cee8eaae093d9b1f9
H29 result                 e35d398c209bb72aae9fb403f82ba01db0281c2b91f146e240130417e7d28702
```

Expected repair impact: parent 7/7 remains unchanged, but metadata relabel counterexample changes `false VERIFIED → fail closed` without modifying Payment policy or P3 promotion semantics outside the challenge-binding defect.

## Single objective / 单一目标

让 proof-of-possession（持有证明）的签名对象与 verifier 使用的新鲜度 / 身份上下文完全绑定：**被签名 challenge payload 必须等于 verifier 根据受信任输入重建出的 canonical challenge bytes（规范挑战字节）**。

## One principal change / 唯一主要变化

在 `credential_possession.py` 增加 canonical challenge binding（规范挑战绑定），不修改 P3 promotion rule（晋级规则）。

冻结 canonical bytes：

```text
agentic-payment-possession/v1\n
nonce={nonce_ref}\n
agent={expected_agent_ref}\n
provider={expected_provider_ref}\n
executor={expected_executor_instance_ref}\n
issued_at={issued_at_epoch}\n
```

UTF-8 exact bytes（精确字节），包括最终换行。

Verifier 必须新增受信任输入 `expected_provider_ref`，并在验证 signature（签名）之前机械执行：

```text
expected_payload = canonical_challenge(
  nonce_ref,
  expected_agent_ref,
  expected_provider_ref,
  expected_executor_instance_ref,
  issued_at_epoch,
)

challenge_payload != expected_payload
→ INVALID / credential_possession_challenge_binding_mismatch
→ never VERIFIED
```

`observed_at_epoch` 不进入 signed payload；它是 verifier 观察时间，用于计算 challenge age。攻击者不能通过修改 `issued_at_epoch` 重新解释旧签名，因为 `issued_at_epoch` 已绑定进签名 payload。

## Required counterexamples / 必须关闭的反例

Evaluator-owned checker：

`evaluator_checks/challenge_binding_counterexample.py`

必须全部 fail closed（失败即关闭）：

1. old signed payload/signature + fresh external nonce + fresh external issued_at；
2. nonce relabel；
3. issued_at relabel；
4. agent context relabel；
5. executor context relabel；
6. provider context relabel。

统一稳定原因码：

`credential_possession_challenge_binding_mismatch`

## Allowed scope / 允许范围

Product：

- `src/agentic_payment_experiment/trusted_execution/credential_possession.py`

Validation / tests：

- `scripts/validation/run_p3_x509_svid_credential_possession_capability.py`
- `tests/trusted_execution/test_credential_possession.py`

Task-owned `REPORT.md` / evidence only.

## Frozen / protected files

不得修改：

```text
src/agentic_payment_experiment/trusted_execution/execution_facts.py
5ff68c16330d3a6570d6a9b53f406a55cd5ee99207867532af74461fd76eeef6

src/agentic_payment_experiment/payment_execution.py
d161be5afe73192491e20203651dc3b222fa37454235c1bacc37042c6254fb49

src/agentic_payment_experiment/trusted_execution/signed_instruction.py
6324a5912f1329b11abddb01a619a8088966ab562ef9f79ccad19b2d02d8c5a2

src/agentic_payment_experiment/adapters/ap2_signed_instruction.py
c0fad26bbeb44034a276d8bb491146a2d5cded3ae130baa611c77e341baa91ae

src/agentic_payment_experiment/adapters/acp_webhook.py
cc723725eb3fd220482bbc21721843d77ba92e7b7a7c29431753e6c6e0e4ffac

pyproject.toml
bc16c28fde7ba55e3de78c054efd2751bfcf6e033298ff0472fe3056023fbbd3
```

Parent evaluator vector / matrix also remain byte-identical.

## Acceptance criteria / 验收标准

### AC-01 — Metadata relabel attack closed
Evaluator checker 六类 relabel attack 全部返回非 VERIFIED，并包含 `credential_possession_challenge_binding_mismatch`。

### AC-02 — Canonical challenge exact binding
Verifier 重建 canonical UTF-8 bytes 并要求 exact equality；nonce/agent/provider/executor/issued_at 任一变化都不能复用旧 signature。

### AC-03 — Parent capability preserved
原 H-29 frozen matrix 仍 `7/7`、repeat=2、exactly one VERIFIED；H29 result audit 通过。

### AC-04 — Legacy P3 / payment policy preserved
`credential_ref` only 仍为 BOUND；`execution_facts.py` 与 `payment_execution.py` hash 不变。

### AC-05 — Focused boundary tests
至少新增 nonce / issued_at / provider challenge binding tests；既有 credential possession focused tests 全部通过。

### AC-06 — Protected stages unchanged
Signed Instruction / AP2 / ACP / dependencies hashes 不变；不接网络、生产凭证、live SPIRE。

### AC-07 — Project guardrails
Product Trace >=10/12；GESR >=9/12；callback=12/12；unsafe allow=0/5；S01-S13=13/13；full unittest zero failures。

### AC-08 — v2.2 handoff
L2 frozen validation PASS；REPORT 映射 AC-01..08，并明确本包只修 challenge binding，不扩大身份系统。

## Exclusions and forbidden side effects

- Must not modify `execution_facts.py` / `payment_execution.py` or the frozen P3 promotion rule.
- Must not change Payment policy, Signed Instruction, AP2, ACP, or dependency semantics.
- Must not add dependencies, network/API calls, live SPIRE/PKI/OIDC/DID/VC, production credentials/private keys/trust bundles, or real payment side effects.
- Must not replace the evaluator-owned vector/matrix signatures or generate new private-key fixtures.
- Must not commit, push, or rewrite history under the current authorization.

## Stop conditions / 停止条件

立即 `BLOCKED`：

- 需要修改 `execution_facts.py` / `payment_execution.py`；
- 需要改变 BOUND→VERIFIED 四条件；
- 需要改变 Payment policy；
- 需要新依赖、网络、SPIRE/PKI/OIDC/DID/VC；
- 需要更换 evaluator vector 的签名或生成新私钥夹具；
- 超过 `2` 个完整 implementation→L2 cycle。

## Authorization / 授权

- max implementation→L2 cycles: `2`
- local CPU only
- dependency install: false
- network/API: false
- production credential/private key/trust bundle: false
- real payment: false
- commit: false
- push: false
- history_rewrite: false

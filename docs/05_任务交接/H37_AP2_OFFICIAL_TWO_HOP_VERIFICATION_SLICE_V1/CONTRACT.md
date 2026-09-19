# Frozen Capability Contract

Task ID: `H37_AP2_OFFICIAL_TWO_HOP_VERIFICATION_SLICE_V1`
Task name: AP2 v0.2.0 Official Two-Hop Verification Slice
Task kind: `capability_experiment`
Contract state: `CONTRACT_FROZEN`
Baseline HEAD: `2b57248af464623402a71d65a2098244819519e3`
Amendment: `docs/05_任务交接/H37_AP2_OFFICIAL_TWO_HOP_VERIFICATION_SLICE_V1/AMENDMENT_01.md`
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`
Map revision: `2026-09-19-r53`
Active bottleneck: `B-06`
Hypothesis: `H-37`
Dispatch mode: `SINGLE`
Validation plan file: `docs/05_任务交接/H37_AP2_OFFICIAL_TWO_HOP_VERIFICATION_SLICE_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

H-36 已由 Evaluator 独立 L3 `5/5 PASS`，并形成单一结论：

```text
root SD-JWT
→ root issuer signature + disclosure resolution
→ verified root cnf.jwk
→ terminal KB-SD-JWT holder signature
→ previous-token binding
→ expected aud / nonce
→ STOP
```

H-36 同时证明：现有 generic ES256 verifier 只能复用密码学 primitive，不能直接替代 AP2 的 SD-JWT / cnf / delegation / aud / nonce 协议语义。Checkout/Payment typed constraint semantics 与 Receipt 路径继续后置。

## External requirement impact / 外部要求影响

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-07, PCAC-09, PCAC-12]
  applicability: CORE
  maturity_scope: H37 bounded AP2 official two-hop delegation-verification slice only
  maturity_before: M1 MODELLED
  maturity_after_target: M5 REGRESSION_GATED
  test_evidence:
    - evaluator-owned C01-C08 matrix
    - focused H37 unittest
    - existing AP2 / signed-instruction regressions
  trace_evidence:
    - H37 L2/L3 gate evidence
    - H37 project baseline evidence
  residual_risk:
    - no production key governance or real Provider trust establishment
    - no Sandbox/testnet/wallet or real payment
    - no Checkout/Payment typed business-constraint verification
    - no Receipt verification
    - not a regulatory-compliance conclusion
```

This mapping is task-local evidence alignment only. It does not claim the whole PCAC profile or the cited requirement families are fully covered.

## Project impact hypothesis / 项目影响假设

**H-37**：如果 H-36 的边界判断正确，那么只增加一个极薄 AP2-specific official-verifier adapter，直接调用 pinned AP2 v0.2.0 的 `MandateClient.verify(...)`，就能得到第一条真实 official runtime cryptographic/delegation verification evidence；不需要复制 SD-JWT、KB-SD-JWT、cnf、binding、aud/nonce 规则，也不需要修改 Trust Core。

Metric baseline: `official AP2 two-hop runtime verification = ABSENT; H-36 classification=DEPENDENCY_BLOCKED; project baseline=12/12`.

Target: evaluator-owned two-hop matrix `8/8 PASS`；合法链返回 VALID；wrong root key、root/terminal signature tamper、broken cnf delegation、wrong aud、wrong nonce、previous-token binding tamper 全部 fail closed；existing guardrails 不退化。

Expected project impact: `official AP2 cryptographic/delegation runtime evidence: ABSENT → BOUNDED_EXECUTABLE_SLICE`.

Estimated affected scope:
- `src/agentic_payment_experiment/adapters/ap2_official_verification.py`
- `src/agentic_payment_experiment/adapters/__init__.py`
- `tests/test_ap2_official_verification.py`
- `.task_envs/h37_ap2_crypto/`
- task-owned report/evidence only.

Rollback condition: 若必须修改 Trust Core、复制 AP2 verifier 规则、进入 Checkout/Payment semantics、Receipt、Sandbox/provider/wallet、生产 credential/PII/资金，或第二个完整 implementation→L2 cycle 仍失败，则停止并交回 Evaluator。

## Official source pin / 官方来源固定

```text
repository  google-agentic-commerce/AP2
tag         v0.2.0
commit      b4587ac1d055888a73b4b21750973cffba961793
source      local_sources/third_party/ap2-v0.2.0
```

H-37 必须调用 pinned source 中：
- `ap2.sdk.mandate.MandateClient.verify`
- 由其进入 `ap2.sdk.sdjwt.chain.verify_chain`

不得复制或改写官方 `sd_jwt.py` / `kb_sd_jwt.py` / `common.py` 的协议规则。

## Human-approved dependency gate / Human 已批准依赖门

Human 于 2026-09-19 明确批准 H-37 的固定依赖安装。

唯一授权环境：

```text
.task_envs/h37_ap2_crypto/
```

允许的 direct pins：

```text
pydantic==2.12.5
jwcrypto==1.5.6
sd-jwt==0.10.4
cryptography==46.0.5
```

允许 package resolver 为上述 direct pins 自动安装其必要传递依赖。允许仅为这些包访问 Python package index / package download endpoint。

禁止：
- 全局 / 系统 Python 安装或升级；
- `pip install .` / 安装完整 AP2 package；
- 顺带安装 pytest、ADK、Gemini、Vertex、sample/demo stack；
- 将 H-37 依赖写入项目主 `pyproject.toml`；
- 任何支付 API / Sandbox / Provider / wallet 网络调用。

## Single principal change / 唯一主要改动

新增：

`src/agentic_payment_experiment/adapters/ap2_official_verification.py`

冻结公开入口：

```python
verify_ap2_v020_official_two_hop_chain(
    *,
    token: str | None,
    root_public_jwk: Mapping[str, object] | None,
    expected_aud: str | None,
    expected_nonce: str | None,
    current_time: int,
) -> AP2OfficialDelegationVerificationFact
```

结果最小化为 protocol-specific verification fact，不回传 raw token、signature、private key、disclosures 或完整 verified payload。

最少字段：

```text
status: VerificationStatus
reason_codes: tuple[str, ...]
protocol_version: str
token_sha256: str | None
verified_hop_count: int
official_verifier_completed: bool
audience_check_requested: bool
nonce_check_requested: bool
```

合法两跳链成功时：
- `status=VALID`
- `verified_hop_count=2`
- `official_verifier_completed=true`

任一官方 verifier 异常必须 fail closed 为 `INVALID`；缺 token/root key/aud/nonce 等必要输入返回 `MISSING_EVIDENCE`。

## Ownership boundary / 所有权边界

H-37 adapter 允许：
- 动态导入 pinned AP2 SDK 和 `jwcrypto.JWK`；
- 将 caller 提供的 public JWK mapping 转为 official JWK；
- 构造 root `PublicKeyProvider`；
- 调用 `MandateClient.verify`；
- 对返回值只做“两跳形状”检查；
- 生成最小化 verification fact。

H-37 adapter 禁止自己实现：
- ES256 / ECDSA 验签；
- SD-JWT disclosure resolution；
- `cnf.jwk` key walk；
- `sd_hash` / `issuer_jwt_hash`；
- KB-SD-JWT `typ`；
- `aud` / `nonce` 语义；
- AP2 time-claim 规则。

这些规则必须继续由 official AP2 verifier 拥有。

## Evaluator-owned frozen cases / 评估者冻结案例

Evaluator check 使用 pinned AP2 SDK 真实生成 root + terminal 两跳 chain：

```text
C01 valid two-hop chain                     → VALID / hops=2
C02 wrong root public key                   → INVALID
C03 root issuer signature tamper             → INVALID
C04 terminal holder signature tamper         → INVALID
C05 broken cnf delegation                    → INVALID
C06 wrong expected_aud                       → INVALID
C07 wrong expected_nonce                     → INVALID
C08 previous-token binding tamper             → INVALID
```

C08 必须使用“另一个仍由同一 issuer 合法签名、但 payload 不同的 root”替换原 root，再连接原 terminal hop，从而让 root 自身签名仍合法、terminal holder signature 仍合法，但 previous-token binding 不匹配。

## Allowed product scope / 允许产品改动

仅允许：
- `src/agentic_payment_experiment/adapters/ap2_official_verification.py`
- `src/agentic_payment_experiment/adapters/__init__.py`
- `tests/test_ap2_official_verification.py`

`adapters/__init__.py` 仅允许追加 H-37 export，不得删除既有 exports。

## Frozen exclusions / 明确排除

除本任务 Allowed product scope 与 Human-approved dependency gate 外，其他能力与环境默认排除。特别是 Checkout/Payment typed business constraints、Receipt、完整 AP2 conformance、Sandbox/testnet/provider/wallet、生产 credential/PII、真实资金、系统 Python 依赖改动、commit/push/history rewrite 均不属于 H-37。

## Protected Core / 保护核心

以下方向全部冻结：
- `src/agentic_payment_experiment/trusted_execution/**`
- existing AP2 F0/F0R/F1 adapters except `adapters/__init__.py`
- payment lifecycle / trace / policy / identity modules
- pinned AP2 source
- project baseline fixtures

特别禁止修改现有 `verify_es256_compact_jws_signed_instruction` 来“适配 AP2”。

## Acceptance criteria / 验收标准

- **AC-01 Dependency isolation**：H-37 env 四个 direct pins 精确匹配；系统 Python/主项目依赖不被改写。
- **AC-02 Official source**：使用 pinned AP2 v0.2.0 / b4587ac1；产品代码不复制 official verifier 规则。
- **AC-03 Positive runtime**：C01 真实 official root+terminal chain 经 H-37 adapter 返回 `VALID / hops=2 / official_verifier_completed=true`。
- **AC-04 Signature failures**：C02-C04 全部 fail closed。
- **AC-05 Delegation/binding failures**：C05 与 C08 全部 fail closed。
- **AC-06 Audience/nonce binding**：C06-C07 全部 fail closed。
- **AC-07 Minimal fact**：结果不保存 raw token/signature/private key/disclosures/完整 payload；adapter 不拥有 SD-JWT/AP2 crypto semantics。
- **AC-08 Optional dependency boundary**：系统 Python 即使没有 H-37 deps，主项目普通 import / existing tests 仍可运行；H-37 focused tests 只在隔离环境执行。
- **AC-09 Existing guardrails**：existing AP2 regression、generic signed-instruction regression、project baseline 12/12 repeat=3、S01-S13、PayBench、full unittest zero failures。
- **AC-10 Scope honesty**：REPORT 明确本任务只证明 AP2 official two-hop crypto/delegation slice；不声称 Checkout/Payment business constraints、Receipt、完整 AP2 conformance、Sandbox/provider/wallet 或真实支付已验证。

## Validation / 验证

Validation plan: `docs/05_任务交接/H37_AP2_OFFICIAL_TWO_HOP_VERIFICATION_SLICE_V1/VALIDATION_PLAN.yaml`

L2 mandatory checks 必须全部 PASS 后，Executor 才可把 REPORT 标为 `SUBMITTED_FOR_REVIEW`。

## Stop conditions / 停止条件

立即停止并交回 Evaluator：
- exact direct pins 无法在 task-local env 安装；
- 需要修改 pinned AP2 source；
- 需要修改 protected Core；
- 需要手写/复制 official SD-JWT / KB-SD-JWT / cnf / binding / aud/nonce 验证逻辑；
- C01 只有进入 Checkout/Payment typed semantics 或 Receipt 才能验证；
- 必须调用 Sandbox/provider/wallet/生产 credential/真实资金；
- 第二个完整 implementation→L2 cycle 仍有 mandatory failure。

Bounded iteration budget: `2` complete implementation → L2 cycles. Amendment 01 does not reopen implementation budget; it grants exactly one validation-only L2 rerun after evaluator-owned baseline/mutation repair. Any repaired mandatory failure that indicates a real product defect returns to Evaluator.

## Authorization / 权限

```text
local CPU/read-only source inspection     true
task-local venv create                    true
fixed dependency install                  true
package-index access for approved deps    true
product code change in allowed scope      true
public payment/network API                false
sandbox/testnet/provider/wallet           false
production credential/PII                 false
real payment                              false
commit                                    false
push                                      false
history rewrite                           false
```

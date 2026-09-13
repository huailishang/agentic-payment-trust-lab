# Executor Report

Task ID: `P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1`  
Executor status: SUBMITTED_FOR_REVIEW  
Baseline HEAD: `8b9d5b46516cad330c89acf7822598a33dc9007c`  
Implementation commit: `NONE`（本任务未获得 commit 授权）  
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-13-r38`  
Active bottleneck: `B-15 / B-15A Signed Instruction Verification`  
Hypothesis: `H-27`

## Workspace snapshot

- H-27 开始时继承 H-25 accepted-but-uncommitted（已验收但未提交）产品快照；因此 `signed_instruction.py`、ACP Webhook 与 H-25 测试/runner 在 Git 中仍是 inherited untracked（继承的未跟踪）状态，不属于 H-27 新越界。
- H-26 Evaluator 已完成 `READY_FOR_AP2_SECOND_CONSUMER` 证据门，并冻结本 H-27 contract / Validation Plan / matrix / evaluator checks；Executor 未修改这些 evaluator-owned artifacts（评估者所有制工件）。
- `CURRENT.md` 仅按 v2.2 路由从 `CONTRACT_FROZEN / Executor` 切到 `EXECUTING / Executor`；授权位未改变。
- External API / network / dependency install / real payment / production credential / production key operation: `0`。
- Commit / push / history rewrite: `0`。

## H-27 changed files

| File | Action in H-27 | SHA-256 | Factual change |
|---|---|---|---|
| `CURRENT.md` | modified | `292043d8e5a02f78a9a6fa2ae768383aaa734a588dd6504c1be6459e8cbc5308` | router 进入 `EXECUTING / Executor`；授权位保持 false |
| `pyproject.toml` | modified | `bc16c28fde7ba55e3de78c054efd2751bfcf6e033298ff0472fe3056023fbbd3` | 仅声明本机已存在的 `cryptography>=41`；没有 install/network |
| `src/agentic_payment_experiment/trusted_execution/signed_instruction.py` | modified inherited H-25 file | `6324a5912f1329b11abddb01a619a8088966ab562ef9f79ccad19b2d02d8c5a2` | 在既有 HMAC fact/verifier 上新增 protocol-neutral ES256 compact-JWS verification（协议中立 ES256 紧凑 JWS 验证）；Fact 公共字段不变 |
| `src/agentic_payment_experiment/trusted_execution/__init__.py` | modified | `97a646849c9e98ff7c9ed1af7d0980382282e7a398648048f2f0c332fa11ef89` | 导出 generic ES256 verifier（通用 ES256 验证器） |
| `src/agentic_payment_experiment/adapters/ap2_signed_instruction.py` | new | `c0fad26bbeb44034a276d8bb491146a2d5cded3ae130baa611c77e341baa91ae` | 新增 bounded AP2 merchant-authorization consumer（有界 AP2 商户授权消费者）；仅映射 `iss/iat/exp` 并委托通用 verifier |
| `src/agentic_payment_experiment/adapters/__init__.py` | modified | `3f07222a8e628156c70d3a93d1a356102f22a0966c38b4b213e75211e782e9f9` | 导出 bounded AP2 signed-instruction API |
| `scripts/validation/run_ap2_es256_signed_instruction_capability.py` | new | `7cd8063f8012f0147920efd47d29afcd41bedeeae4bc80f50e910871d94725ee` | 执行冻结 6 Case × repeat=2，持久化最小 verification facts（验证事实）与 `1→2` consumer signal（消费者信号） |
| `tests/trusted_execution/test_signed_instruction_es256.py` | new | `1b7550547a9f4c1b759d85921a91ec1786b90aeae2e2638f78807c2b129452bf` | generic ES256 verifier 正负边界：alg/kid/time/JWK/fact minimization（事实最小化） |
| `tests/test_ap2_signed_instruction.py` | new | `ab5eea317d81cbbc378a28775b8928f8b6dd18b08de2a3c7b597375857ca164f` | AP2 adapter 正负例、签署者绑定、缺失/畸形授权、`iat/exp` 窗口 |

Protected / frozen sources（保护/冻结源）保持 byte-stable（字节级稳定）：

```text
src/agentic_payment_experiment/adapters/ap2.py
22325219bdcd02c69bedd26831608d3fe1752b0cc43e1e34a0442ff3a698b867

src/agentic_payment_experiment/adapters/acp_webhook.py
cc723725eb3fd220482bbc21721843d77ba92e7b7a7c29431753e6c6e0e4ffac

scripts/validation/run_signed_instruction_verification_capability.py
5be73da638cac0583857c012acaa00575ae27b008faf383225f72f8e9d03c543
```

## L2 Task Gate

- Gate result: PASS
- Gate summary: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/L2-GATE.json`
- Validation plan: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/VALIDATION_PLAN.yaml`
- Checks: `10/10 PASS`
- Mandatory failures: `0/10`
- Complete implementation → L2 cycles used: `1/2`
- Second cycle: `NOT_USED`，首轮已达到 evidence sufficiency（证据充分性）。

## Acceptance-criterion evidence map

| AC | Executor evidence | Observed result |
|---|---|---|
| `AC-01` Fact remains protocol-neutral | `EV-01/03/04/05/06` | 同一 `SignedInstructionVerificationFact` 同时承载 HMAC + ES256；公共字段保持兼容；H-25 regression（回归）稳定 |
| `AC-02` Generic ES256 verifier is generic | `EV-04/05` | Trusted Execution（可信执行）无 AP2 Mandate/cart/payment/business 分支；密码学只在 generic verifier |
| `AC-03` AP2 second consumer is real | `EV-01/02/04/05` | 新 AP2 adapter 实际调用 generic verifier；旧 `adapters/ap2.py` hash 不变 |
| `AC-04` Six headline cases | `EV-02/03/05` | 冻结 matrix `6/6`；repeat=2 全部 identical（一致） |
| `AC-05` Additional negative boundaries | `EV-05` | unsupported alg、wrong kid、future/expired、`exp < iat`、malformed/non-P256 JWK 全部 fail-closed（失败即关闭） |
| `AC-06` Second-consumer proof | `EV-02/03/04` | real Signed Instruction consumers `1→2`；AP2 executable semantics `0/6→6/6` |
| `AC-07` Sensitive-data boundary | `EV-01/02/03/05` | synthetic/test-only；结果无 private key/raw token/raw signature/production credential；真实支付/生产凭据=0 |
| `AC-08` H-25 regression stability | `EV-01/06/07` | H-25 result SHA-256 精确保持 `888d8d9ae215ce3d4ac593c190a2863746fddf1d99ca78175324670615b22a37` |
| `AC-09` Project guardrails | `EV-08/09/10` | Product Trace=`10/12`、GESR=`9/12`、callback=`12/12`、duplicate/forbidden=`0/12`、unsafe allow=`0/5`、S01-S13=`13/13`、full unittest=`692/692` |
| `AC-10` Dependency boundary | `EV-01/04` | 只声明 `cryptography>=41`；本机 `41.0.7`；无 install/network；无 PyJWT/jwcrypto/authlib |
| `AC-11` External requirement honesty | `EV-03` + 本 REPORT | `PCAC-AGENTPAY / PCAC-06 / ADAPTER / M3→M4 target`；残余风险显式保留；无 conformance/compliance（协议认证/监管合规）宣称 |
| `AC-12` v2.2 handoff complete | `L2-GATE + EV-01..10 + REPORT` | L2 `10/10 PASS`；本 REPORT 映射 AC-01..12；workflow validator（工作流校验器）在提交前另行记录 |

## EV-01 — Source snapshot / dependency boundary

- AC: `AC-01, AC-03, AC-07, AC-08, AC-10, AC-12`
- Meta: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-01.meta.json`
- Stdout: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-01.stdout.log`
- Stderr: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-01.stderr.log`

Source snapshot audit（源快照审计）PASS：保护的 AP2/ACP/H-25 文件与 H-27 matrix hash 全部稳定；依赖集合精确为 `cryptography>=41`；本地版本 `41.0.7` 满足，不需安装。

## EV-02 — H-27 capability runner

- AC: `AC-03, AC-04, AC-06, AC-07`
- Meta: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-02.meta.json`
- Stdout: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-02.stdout.log`
- Stderr: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-02.stderr.log`

Capability runner（能力测量执行器）PASS：六案例 `6/6`，repeat=2 deterministic（一致），5/5 negative cases fail-closed（负例失败即关闭），real consumers `1→2`。

Persisted result：
`docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/H27_AP2_ES256_RESULT.json`  
SHA-256：`ff63e96d4ad02670541733cc48bf3a66d184cec84ead34e9dc0b0bd2b277cea6`

## EV-03 — H-27 result audit

- AC: `AC-01, AC-04, AC-06, AC-07, AC-11`
- Meta: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-03.meta.json`
- Stdout: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-03.stdout.log`
- Stderr: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-03.stderr.log`

Result audit（结果审计）PASS：schema、matrix hash、六案例顺序/语义、repeat digests、`1→2` consumer count、PCAC 映射与 sensitive/raw material（敏感/原始材料）key scan 均符合冻结契约。

## EV-04 — Architecture boundary

- AC: `AC-01, AC-02, AC-03, AC-06, AC-10`
- Meta: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-04.meta.json`
- Stdout: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-04.stdout.log`
- Stderr: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-04.stderr.log`

Architecture boundary audit（架构边界审计）PASS：

- generic verifier 可识别 compact JWS / JOSE `alg/kid` / ES256 P-256 JWK / signer-key-time，但没有 `merchant_authorization`、`cart_hash`、`CartMandate`、`PaymentMandate`、`checkout_hash`；
- AP2 adapter 调用 `verify_es256_compact_jws_signed_instruction`；
- AP2 adapter 不复制 `ec.ECDSA` / DSS signature conversion（DSS 签名转换）等密码学实现。

## EV-05 — Focused tests

- AC: `AC-01, AC-02, AC-03, AC-04, AC-05, AC-07`
- Meta: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-05.meta.json`
- Stdout: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-05.stdout.log`
- Stderr: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-05.stderr.log`

Focused tests（专项测试）=`17/17 PASS`。

覆盖：合法 ES256、精确 signing-input hash（签名输入哈希）、payload tamper（载荷篡改）、wrong public key（错误公钥）、wrong signer（错误签署者）、missing/malformed token（缺失/畸形 token）、unsupported alg（不支持算法）、wrong `kid`、future/expired time（未来/过期时间）、`exp < iat`、malformed/non-P256 JWK（畸形/非 P-256 公钥），以及 fact 不暴露 raw token/signature/key/business decision（原始令牌/签名/密钥/业务决策）。

## EV-06 — H-25 first-consumer rerun

- AC: `AC-01, AC-08`
- Meta: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-06.meta.json`
- Stdout: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-06.stdout.log`
- Stderr: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-06.stderr.log`

按 H-25 冻结 matrix/repeat 原样重跑 first consumer（第一消费者），执行结果 PASS。

## EV-07 — H-25 regression hash audit

- AC: `AC-08`
- Meta: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-07.meta.json`
- Stdout: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-07.stdout.log`
- Stderr: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-07.stderr.log`

Hash audit（哈希审计）PASS。H-25 结果 SHA-256 精确保持：

`888d8d9ae215ce3d4ac593c190a2863746fddf1d99ca78175324670615b22a37`

说明新增 ES256 第二消费者没有改变已验收 ACP/HMAC 行为。

## EV-08 — Project-impact baseline

- AC: `AC-09`
- Meta: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-08.meta.json`
- Stdout: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-08.stdout.log`
- Stderr: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-08.stderr.log`

Repeat=3 全部 identical（一致）：

```text
Product Trace = 10/12
GESR = 9/12
callback match = 12/12
duplicate/forbidden side effect = 0/12
unsafe allow = 0/5
```

已知 T05/T06 Product Trace 缺口与 T10 frozen-baseline mismatch（冻结基线不匹配）仍然存在，属于进入 H-27 前的既有 WATCH（观察）项；H-27 未修改相关产品链路，也没有把这些旧缺口包装成本轮改善。

## EV-09 — Formal experiment entrypoint

- AC: `AC-09`
- Meta: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-09.meta.json`
- Stdout: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-09.stdout.log`
- Stderr: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-09.stderr.log`

正式实验入口 `S01..S13 = 13/13 PASS`；AP2 official minimal flow（AP2 官方最小流程）=`2/2 PASS`；Attack Overlay（攻击覆盖层）=`6/6 PASS`。无网络、无真实 Buy Now、无真实支付。

## EV-10 — Full unittest

- AC: `AC-09, AC-12`
- Meta: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-10.meta.json`
- Stdout: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-10.stdout.log`
- Stderr: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/EV-10.stderr.log`

Full unittest（全量单测）=`692/692 PASS`，较 H-25 accepted suite（已验收测试集）的 `675` 增加 H-27 `17` 个 focused tests（专项测试），既有测试零失败。

## Six-case capability result / 六案例能力结果

| Case | Observed | Reason | Verified | Repeat |
|---|---|---|---:|---|
| `V01_VALID_ES256_JWS` | `VALID` | `signed_instruction_signature_valid` | true | identical |
| `N01_TAMPERED_PAYLOAD` | `INVALID` | `signed_instruction_signature_mismatch` | false | identical |
| `N02_WRONG_PUBLIC_KEY` | `INVALID` | `signed_instruction_signature_mismatch` | false | identical |
| `N03_WRONG_SIGNER_BINDING` | `INVALID` | `signed_instruction_signer_mismatch` | false | identical |
| `N04_MISSING_AUTHORIZATION` | `MISSING_EVIDENCE` | `signed_instruction_signature_missing` | false | identical |
| `N05_MALFORMED_COMPACT_JWS` | `INVALID` | `signed_instruction_compact_jws_format_invalid` | false | identical |

Valid case（合法案例）的 signing input SHA-256（签名输入哈希）精确为：

`186718f3fa5651c8db3bab04967846075c79c29a4cbdf4589da18226158c6469`

与 evaluator-owned frozen fixture（评估者冻结样例）一致。

`VALID` 只表示：给定 ES256/P-256 公钥对 exact compact-JWS signing input（精确 JWS 签名输入）的签名验证成功，`kid` / signer binding（签署者绑定）匹配，且 `iat <= observed_at <= exp`。它**不等于** Payment `ALLOW`、Identity `VERIFIED`、商户法律身份、credential validity（凭证有效性）、完整 AP2 conformance（协议一致性）或监管合规。

## Impact comparison

- Measurement evidence: `EV-02 + EV-03 + EV-06 + EV-07 + EV-08 + EV-09 + EV-10 + H27_AP2_ES256_RESULT.json`。
- Before: real Signed Instruction consumers=`1`（ACP HMAC）；AP2 ES256 executable cases=`0/6`。
- After: real consumers=`2`（ACP HMAC + AP2 ES256）；AP2 ES256=`6/6`；repeat=2 全部一致；5/5 negative fail-closed（负例失败即关闭）。
- Delta: consumers `1→2`; AP2 executable semantics `0/6→6/6`。
- First-consumer stability: H-25 accepted result SHA-256 不变。
- Guardrail result: Product Trace=`10/12`、GESR=`9/12`、callback=`12/12`、duplicate/forbidden=`0/12`、unsafe allow=`0/5`、formal scenarios=`13/13`、full unittest=`692/692`，均未退化。
- Scope caveat: 本轮只证明 protocol-neutral fact（协议中立事实）被两个不同协议/算法消费者真实复用；是否因此关闭 B-15A、STOP 第三个协议或 SWITCH 到 B-15B，由 Evaluator 在独立 L3 后裁决。Executor 不在本 REPORT 中发出 project-impact verdict（项目影响裁决）。

## External requirement impact

```yaml
profile: PCAC-AGENTPAY
requirement_ids: [PCAC-06]
applicability: ADAPTER
maturity_before: M3
maturity_after: M4  # task target; requires Evaluator acceptance
```

Residual risks（残余风险）：

- evaluator-owned synthetic fixture only（仅评估者合成样例）；
- no live JWKS / DID / PKI；
- no SD-JWT holder binding（无 SD-JWT 持有者绑定）；
- no full AP2 conformance claim（不声称完整 AP2 协议一致性）；
- no production authentication/security certification（无生产认证/安全认证）；
- no regulatory compliance claim（无监管合规宣称）。

## Sensitive-data minimization / 敏感数据最小化

- `SignedInstructionVerificationFact` 不包含 raw compact JWS、raw signature、公私钥坐标、private key、payment decision 或 business authorization（业务授权）。
- H-27 persisted result（持久化结果）只记录 status/reason、algorithm、signer/key refs、signing-input SHA-256、时间窗口、repeat digest、impact/guardrail summary；不记录 raw token/signature/private key。
- Frozen evaluator fixture（冻结评估样例）仅包含 synthetic signed token + public JWK；private key 未持久化。
- production credential/key、real payment、external network 使用计数全部为 `0`。

## Iteration ledger

| Iteration | Principal change stayed frozen? | Validation / measurement | Material cost | Progress signal | Stop/continue fact |
|---:|---|---|---|---|---|
| L1 | yes | `17/17` focused + source/architecture/result audit 通过；H-27 `6/6` | local CPU only；0 external call | ES256 second consumer 可执行且边界清晰 | 进入正式 L2 |
| 1 | yes | frozen L2 `10/10 PASS` | local CPU only；0 API/network/quota | consumers `1→2`，AP2 `0/6→6/6`，H-25/guardrails 稳定 | evidence sufficiency reached（证据充分），停止 Executor 迭代并提交复核 |

- Budget consumed / ceiling: `1 / 2` complete implementation→L2 cycles。
- Remaining bounded cycle: `1`，未使用。
- Parallel attempt waves: `NOT_APPLICABLE`。
- Evidence sufficiency reached: `yes`。

## Deviations and unresolved items

- Contract deviation: `NONE`。
- Checks not run: `NONE`；冻结 VP-01..VP-10 全部运行且 PASS。
- Dependency installation: `NONE`；仅使用本机已存在 `cryptography 41.0.7`。
- Network/API/real payment/production credential-key: `NONE`。
- Existing `adapters/ap2.py` modification: `NONE`；保护 hash 精确不变。
- H-25 regression change: `NONE`；accepted result hash 精确不变。
- Known project-level WATCH（观察）项：T05/T06 Product Trace、T10 frozen-baseline mismatch；均为既有问题且不在 H-27 scope（范围）内。
- Explicitly unresolved by design（设计上明确未解决）：full SD-JWT disclosure/delegate chain、holder key binding、Payment Mandate transaction data、business cart-hash correctness、live JWKS/DID/PKI、P3 Credential/Possession、完整 AP2 conformance、生产安全认证、监管合规。
- Authorization respected: commit=false, push=false, history_rewrite=false, api_call=false。

## Submission boundary

Executor has reached the v2.2 submission point. `CURRENT.md` intentionally remains `EXECUTING / Executor`. This REPORT is `SUBMITTED_FOR_REVIEW`; only Evaluator may accept the unchanged snapshot, route to `READY_FOR_REVIEW / Evaluator`, run independent L3, issue task `PASS/REJECTED/HUMAN_REQUIRED`, decide project impact, and determine whether B-15A has representative closure or should SWITCH（切换） to B-15B.

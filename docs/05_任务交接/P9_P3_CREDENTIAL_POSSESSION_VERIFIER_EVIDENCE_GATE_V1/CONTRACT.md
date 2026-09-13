# Draft Task Contract

Task ID: `P9_P3_CREDENTIAL_POSSESSION_VERIFIER_EVIDENCE_GATE_V1`  
Task name: P3 Credential / Possession Verifier Evidence Gate  
Task kind: `evaluator_design`  
Contract state: `DRAFT_CONTRACT`  
Baseline HEAD: `8b9d5b46516cad330c89acf7822598a33dc9007c`  
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-13-r39`  
Active bottleneck: `B-15 / B-15B Credential / Possession Verification`  
Hypothesis: `H-28`

Inherited accepted snapshot: H-25 + H-27 product changes are accepted-but-uncommitted（已验收但未提交）because commit/push authorization remains false. H-28 is evaluator-only and must not mutate those accepted product snapshots.

## Strategic basis / 战略依据

H-27 已由 Evaluator 独立复核：

```text
Task verdict: PASS
Project impact: IMPROVED
Continuation: SWITCH
L3: 10/10 PASS
AP2 ES256: 0/6 → 6/6
real Signed Instruction consumers: 1 → 2
negative cases fail closed: 5/5
focused tests: 17/17
full unittest: 692/692
H-25 accepted hash: unchanged
network / real payment / production credential-key: 0
```

因此 B-15A Signed Instruction Verification（签署指令验证）达到 representative closure（代表性闭合）并 `RESOLVED / STAGE_CLOSED`。继续加入第三个签名协议的边际信息增益已经不足。

B-15 当前剩余更重要的问题是 B-15B：P3 `IdentityAssuranceFact` 明确将 `VERIFIED` 保留给未来 explicit credential verifier / provider attestation（显式凭证验证器 / Provider 证明），现有 `verify_agent_executor_identity()` 只验证 agent/provider/executor/credential reference（引用）关系，最高只能输出 `BOUND`。

H-24 已冻结三条 P3 证据：

```text
P01 no credential                 → VALID / BOUND
P02 expected credential missing   → VALID / BOUND
P03 matching credential_ref only  → VALID / BOUND
```

即：`credential_ref` 相等不等于 credential authenticity（凭证真实性），也不等于 proof of possession（持有证明）。

## External standards basis / 外部标准依据

本任务先比较机制，不预设实现：

### SPIFFE / SVID

官方 SPIFFE 文档定义 SVID 为 workload（工作负载）向资源/调用方证明身份的可验证身份文档；当前主要格式包括 X.509 与 JWT。X.509-SVID 可通过 trust bundle（信任包）验证，并配套与 SPIFFE ID 绑定的私钥；官方文档也明确 JWT token 更容易受到 replay（重放），能使用 X.509-SVID 时优先使用 X.509-SVID。

Candidate relevance（候选相关性）：更贴近 P3 的 Agent / executor workload identity（工作负载身份）与 credential validity（凭证有效性）。

### OAuth DPoP / RFC 9449

RFC 9449 定义 DPoP 为 sender-constrained OAuth token（发送方约束 OAuth token）的 proof-of-possession（持有证明）机制。有效 DPoP proof 可以证明请求方持有签署 proof JWT 的私钥；但 RFC 同时明确 DPoP 本身不是 client authentication（客户端认证）或 access-control mechanism（访问控制机制）。

Candidate relevance（候选相关性）：更适合用来区分“持有密钥”与“身份已认证”，防止项目把 PoP 误写成 P3 `VERIFIED`。

H-28 必须保持这两个问题分离：

```text
credential validity
≠ proof of possession
≠ identity assurance / authorization decision
```

## Missing dependency / 当前缺的关键事实

当前不能直接实现 P3 `VERIFIED`，因为下面事实尚未冻结：

1. `VERIFIED` 的最小语义到底要求 credential validity、proof-of-possession，还是二者都需要；
2. credential subject identity（凭证主体身份）如何绑定现有 `agent_id / provider / executor_instance_id`；
3. trust anchor / trust bundle / issuer key（信任锚 / 信任包 / 签发方密钥）由谁提供，实验里如何离线固定；
4. possession proof（持有证明）到底由 mTLS handshake、challenge signature、DPoP-style proof 或其他机制表达；
5. expiration / freshness / nonce / replay（过期 / 新鲜度 / 随机数 / 重放）边界；
6. 至少一组 deterministic positive + negative vectors（确定性正负向量）；
7. P3 从 `BOUND → VERIFIED` 的 fail-closed（失败即关闭）升级条件；
8. 该能力不依赖生产 credential、真实 trust bundle、真实支付或 live network。

## Objective / 单一目标

冻结 P3 `Credential / Possession Verification（凭证 / 持有证明验证）` 的最小真实 verifier contract（验证合同），并决定第一种值得进入 capability experiment（能力实验）的机制。

本任务只做证据、语义和合同设计，不修改产品代码，也不把 P3 升级到 `VERIFIED`。

## Questions to answer / 必须回答的问题

H-28 必须明确回答：

1. P3 `VERIFIED` 是否必须同时满足：
   - credential chain/signature validity（凭证链/签名有效）；
   - subject identity binding（主体身份绑定）；
   - live proof-of-possession（实时持有证明）；
   - freshness / replay protection（新鲜度 / 重放保护）。
2. SPIFFE X.509-SVID 是否能作为第一 credential candidate（凭证候选），以及哪些部分只能由 synthetic offline fixture（合成离线样例）模拟。
3. JWT-SVID 为什么不能仅凭 token signature 就自动等价于 live possession。
4. DPoP 是否只作为 possession semantics reference（持有语义参考），还是确实适合本项目第一实现；不得把 DPoP 自动解释为 Agent identity authentication（Agent 身份认证）。
5. 哪些 evidence（证据）可以让 `IdentityAssuranceLevel.VERIFIED` 合法出现，哪些情况必须保持 `BOUND / DECLARED / INVALID / MISSING_EVIDENCE`。

## Decision outputs / 决策输出

只允许两个方向：

```text
READY_FOR_P3_CREDENTIAL_POSSESSION_CAPABILITY
→ 1–8 关键事实已经冻结
→ 明确第一 verifier mechanism + deterministic matrix
→ Evaluator 再冻结独立 capability_experiment

P3_CREDENTIAL_POSSESSION_NOT_READY
→ 关键 trust / possession / binding 证据不足
→ 不实现假 VERIFIED
→ 保持 BOUND，并重新比较其他真实性入口或外部授权条件
```

## Readiness criteria / 从 DRAFT 升级的条件

只有同时满足以下条件才允许进入产品实现：

```text
A. credential format + trust semantics fixed
B. subject identity mapping fixed
C. proof-of-possession semantics fixed
D. freshness/replay boundary fixed
E. positive vector mechanically verifiable
F. wrong trust / wrong subject / no possession / replay-or-stale negatives mechanically verifiable
G. exact BOUND→VERIFIED promotion rule fixed
H. no production credential / network / real payment needed
```

## Allowed scope / 允许范围

Evaluator-only（仅评估者）文档与证据：

- 本任务目录下的 `CONTRACT.md`、source audit / evidence / decision；
- `docs/reference/**` 中必要的 SPIFFE / DPoP / identity-verification 来源索引；
- `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`，仅在证据足以重排方向时更新；
- `CURRENT.md` 路由。

## Explicit exclusions / 明确排除

- 不修改 `src/**` / tests / runners；
- 不让现有 `credential_ref` 相等直接产生 `VERIFIED`；
- 不把 signed JWT / DPoP proof 单独当成完整 identity authentication；
- 不建设万能 IAM / PKI / OAuth / OIDC / Passkey / biometrics（生物识别）平台；
- 不接 live SPIRE / Workload API / JWKS / DID / bank sandbox / wallet / testnet；
- 不使用生产 certificate、private key、credential、trust bundle；
- 不改变 Payment `ALLOW / DENY` 策略；
- 不声称 SPIFFE / OAuth / AP2 conformance（协议一致性认证）或监管合规；
- 不新增依赖；
- 不 commit / push / history rewrite。

## Authorization / 授权边界

- commit: false
- push: false
- history_rewrite: false
- production API/network action: false
- real payment / credential / private-key / trust-bundle use: false

公开标准资料仅用于只读证据核验，不自动获得任何外部写入或生产系统操作授权。

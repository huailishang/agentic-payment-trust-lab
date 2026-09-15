# H-28 Evidence Decision

Task ID: `P9_P3_CREDENTIAL_POSSESSION_VERIFIER_EVIDENCE_GATE_V1`  
Task kind: `evaluator_design`  
Decision: **READY_FOR_P3_X509_SVID_CREDENTIAL_POSSESSION_CAPABILITY**  
Project map basis: `2026-09-13-r39`  
Active bottleneck: `B-15 / B-15B Credential / Possession Verification`

## Decision summary / 结论

H-28 证据门通过。P3 现有 `credential_ref` matching（凭证引用匹配）只能证明引用关系一致，不能合法产生 `IdentityAssuranceLevel.VERIFIED`。第一能力实验冻结为一个**本地、离线、单 trust root（信任根）、直接签发 leaf（叶证书）的 X.509-SVID 有界验证 profile（验证轮廓）**，再叠加 challenge signature（挑战签名）证明当前执行者持有该 SVID 对应私钥。

本轮不是建设 SPIRE / 企业 PKI，也不声称完整 SPIFFE conformance（协议一致性）。它只回答：在现有 P3 `BOUND` 已成立时，能否用机械可验证的 credential validity（凭证有效性）+ subject binding（主体绑定）+ proof-of-possession（持有证明）+ freshness/replay protection（新鲜度 / 防重放）把同一身份事实合法提升到 `VERIFIED`。

## Four-condition promotion gate / 四条件升级门

只有以下四项全部为真，P3 才允许 `BOUND → VERIFIED`：

```text
1. Credential Valid
   - leaf certificate signature 可由冻结 trust root 验证
   - 证书在有效期内
   - leaf BasicConstraints CA=false
   - KeyUsage 包含 digitalSignature 且不包含 keyCertSign/cRLSign
   - 恰好一个 spiffe:// URI SAN，且属于预期 trust domain

2. Subject Binding Valid
   - SPIFFE ID 机械映射到冻结的 agent/provider/executor 预期主体
   - 不能只比较 credential_ref

3. Proof of Possession Valid
   - verifier 给出 challenge nonce
   - 当前执行者用 leaf SVID 对应私钥对冻结 challenge payload 签名
   - verifier 使用 leaf public key 验证签名

4. Freshness / Replay Valid
   - challenge 在冻结 TTL 内
   - nonce 尚未出现在调用方提供的 consumed nonce set 中
```

任一条件不满足时，不得输出 `VERIFIED`。

## External standards basis / 外部标准依据

- SPIFFE X509-SVID：SPIFFE ID 位于 URI SAN；leaf SVID 要求 `CA=false`、`digitalSignature`，认证用途还需要标准 X.509 path validation 与 SPIFFE-specific leaf validation。
- SPIFFE Trust Domain / Bundle：trust bundle 的密码学材料是对应 trust domain 下 SVID 的信任锚，验证时必须保持 trust-domain → bundle 绑定。
- SPIFFE Workload API：X509SVID 同时携带 certificate chain 与对应 private key，说明 credential 与持有密钥是关联但不同的证据对象。
- RFC 9449 DPoP：只作为 proof-of-possession / freshness / nonce / replay 语义参考；RFC 明确 DPoP 本身不是 client authentication，因此本项目也不得把“一次签名成功”单独等同 `VERIFIED`。

## Why X.509-SVID first / 为什么第一实现选它

当前 P3 的主体是 Agent / executor workload identity（工作负载身份），X.509-SVID 比 VC / DID 更直接贴合 executor 身份；相比 DPoP，它同时提供 credential trust（凭证信任）与 public-key identity（公钥身份）载体。项目本机已声明并安装 `cryptography>=41`，因此可以完全离线实现一条 synthetic test-only（合成测试）验证链，不增加依赖、不联网、不触碰生产凭证。

W3C VC / DID、BSN DID / VC、OIDC Agent Identity Claims 继续作为未来 Principal / Agent credential Provider Adapter（提供方适配）候选，不进入第一执行包。

## Frozen evaluator vectors / 冻结评估向量

Evaluator 已生成 synthetic test-only（合成测试）公开材料，**不持久化任何 private key（私钥）**：

- `evaluator_fixtures/X509_SVID_POSSESSION_VECTOR.json`
- `evaluator_fixtures/X509_SVID_POSSESSION_MATRIX.json`

Frozen SHA-256：

```text
vector = b0ffc3a5707e403febb545bb8a142767e101a2c3edf42eaad40396552f9fe910
matrix = 9f72cc24c8557aee48f7b611ed71e3d253ad311c607e3260f713500140a8eda8
```

Headline matrix：

```text
V01 valid trust + subject + possession + freshness → VERIFIED
N01 wrong trust bundle                           → not VERIFIED
N02 wrong SPIFFE subject                         → not VERIFIED
N03 no possession proof                          → not VERIFIED
N04 invalid possession signature                 → not VERIFIED
N05 replayed nonce                               → not VERIFIED
N06 stale challenge                              → not VERIFIED
```

## Important boundary / 重要边界

本能力通过后，`VERIFIED` 只表示：**在本项目冻结的离线 synthetic X.509-SVID profile 内，当前 Agent / executor 已通过凭证、主体、持有证明和新鲜度四道门。**

它不表示：

- 生产 Agent 身份已经认证；
- 完整 RFC 5280 / SPIFFE / SPIRE conformance；
- 企业 CA / OIDC / DID / VC / Passkey 已接入；
- 支付业务授权已经成立；
- Payment `ALLOW` 可以仅由该事实决定；
- 法律身份、监管合规或生产安全已经证明。

## Next task

冻结能力执行包：

`P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1` / `H-29`

唯一主要变化：新增 protocol-neutral Credential / Possession verification fact（协议中立凭证 / 持有证明事实），将 bounded X.509-SVID verifier（有界验证器）接入现有 P3 identity binding；仅在 base binding 已为 `VALID / BOUND` 且四条件全通过时，允许第一次输出 `VALID / VERIFIED`。

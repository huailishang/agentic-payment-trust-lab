# H-26 Evidence Decision

Task ID: `P9_AP2_SIGNED_MANDATE_VERIFIABLE_FIXTURE_FEASIBILITY_V1`  
Task kind: `evaluator_design`  
Decision: **READY_FOR_AP2_SECOND_CONSUMER**  
Project map basis: `2026-09-13-r37`  
Active bottleneck: `B-15 / B-15A Signed Instruction Verification`

## Decision summary / 结论

H-26 的证据门可以通过，但必须把范围收窄为 **AP2 ES256 merchant-signed JWT 的密码学真实性 + signer/key 绑定**，不能把这轮实验写成“完整 AP2 / SD-JWT conformance（协议一致性）”。

官方 AP2 资料已经给出足够稳定的最小交集：

1. AP2 官方 `v0.2.0` release 存在，release commit=`b4587ac`；
2. 官方 AP2 模型明确 `CartMandate.merchant_authorization` 是签署 Cart 内容的 base64url JWT，header 包含 algorithm / key ID，payload 包含 merchant identity、`iat/exp/jti/cart_hash`，并由 merchant private key 签名；
3. 当前官方 AP2 v0.2 规范明确 Mandate 的 verification（验证）必须由 deterministic code（确定性代码）执行；Merchant / Credential Provider 等角色必须验证 Mandate；
4. 当前官方 Checkout Mandate 文档使用 ES256 / P-256 风格示例，并明确 closed Checkout Mandate 与 merchant-signed Checkout JWT 的 hash 绑定；
5. 官方规范同时明确 AP2 的完整 Mandate 还涉及 SD-JWT、key binding、constraint evaluation 等更多层次，因此本轮不能把“一个 ES256 JWT 验签”写成完整 AP2 验证。

## H-26 seven-condition gate / 七项证据门

| 条件 | 裁决 | 冻结证据 |
|---|---|---|
| 1. pinned source / revision | PASS | AP2 official release `v0.2.0`, commit `b4587ac`; current official v0.2 docs只用于确认仍存在的 verification / signed-JWT 语义 |
| 2. exact signed object | PASS | Compact JWS signing input：`ASCII(base64url(header) + "." + base64url(payload))`；本轮只验证这个签名对象，不声称覆盖 SD-JWT disclosure chain |
| 3. algorithm + signer/key relation | PASS | 本轮冻结 `ES256 / P-256 / kid → evaluator-owned public JWK / expected merchant signer_ref` |
| 4. deterministic valid sample | PASS | Evaluator 已生成一条 synthetic（合成）test-only valid ES256 compact JWS；fixture 只持久化 public JWK + signed token，不持久化 private key |
| 5. negative vectors | PASS | frozen matrix 覆盖 payload tamper、wrong public key、wrong signer binding、missing token、malformed compact JWS；wrong kid / unsupported alg / expired/future 在 focused tests 单独覆盖 |
| 6. provenance + license | PASS | 协议语义来自 official `google-agentic-commerce/AP2`（Apache-2.0）；密码学向量为本项目 evaluator-owned synthetic fixture，明确不是官方 conformance vector |
| 7. local/offline | PASS | 本机已有 `cryptography 41.0.7`；新包禁止 dependency install / network / production key / real payment |

## Why this is enough / 为什么可以进入执行包

H-25 已证明：

```text
SignedInstructionVerificationFact
+ HMAC-SHA256 verifier
+ ACP Webhook first consumer
```

H-27 要回答的新问题是：

```text
同一个 SignedInstructionVerificationFact
能否承载第二种协议 + 第二种签名算法（AP2 + ES256）？
```

因此 H-27 的目标不是“补齐 AP2”，而是验证 **second consumer（第二消费者）是否真的迫使通用层保持协议中立，同时没有把 AP2 特有字段污染到 Trusted Execution（可信执行）层。**

## Important scope caveat / 重要边界

本轮明确不验证：

- 完整 SD-JWT disclosure / delegate chain；
- Payment Mandate `transaction_data` / `sd_hash` / holder key-binding；
- AP2 open/closed Mandate constraint evaluation；
- full `checkout_hash` / business checkout correctness；
- production JWKS / DID / PKI / credential provider；
- AP2 conformance certification；
- Payment `ALLOW` 或 P3 Identity `VERIFIED`。

如果 H-27 PASS，只能说明：**协议中立 Signed Instruction Fact 已被 ACP HMAC 与 AP2 ES256 两个不同消费者真实复用。**

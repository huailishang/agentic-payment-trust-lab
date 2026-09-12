# Evaluator Review

Task ID: `P9_ACTOR_AUTHENTICITY_SIGNED_INSTRUCTION_GAP_MEASUREMENT_V1`  
Task kind: `one_off`  
Evaluator verdict: **PASS**  
Project impact verdict: **NOT_APPLICABLE**  
Continuation decision: **CONTINUE**  
Reviewed baseline HEAD: `d26fa658b970f84ca25859d7c3739994cae10a61`

## 1. 全局位置

```text
A. 评测与治理底座                  [完成]
→ B. 授权、绑定、来源、执行前治理   [完成]
→ C. 支付生命周期、恢复、补救证据链 [完成]
→ D. 责任归因与可消费审计链         [完成]
→ E. 主体真实性 / 凭证 / 签署指令   [当前]
→ F. 外部真实协议 / SDK / 网络接入   [未来，受授权约束]
```

H-24 属于阶段 E 的 measurement-only（只测量）任务。它不实现真实性验证器，只回答 P3、AP2、ACP 现有未验证边界是不是重复出现的项目级安全缺口。

## 2. 正式裁决

Evaluator 接受 Executor 提交快照后，独立执行 frozen Validation Plan（冻结验证计划）：

```text
L3 = 7/7 PASS
mandatory failures = 0/7
six probes measured = 6/6
repeat = 2/probe
expectation match = 6/6
surfaces = 4
product VERIFIED authenticity = 0/6
explicit not-verified probes = P04 / P05 / P06
focused regression = 34/34 PASS
Product Trace = 10/12
GESR = 9/12
callback = 12/12
unsafe allow = 0/5
formal scenarios = 13/13 PASS
full unittest = 662/662 PASS
real payment / credential / key / signature / network = 0
```

Task verdict 为 `PASS`。H-24 只增加测量 runner / evidence，没有改变产品能力，因此 Project impact verdict（项目影响裁决）为 `NOT_APPLICABLE`。

## 3. 六个探针的关键事实

### P3：Credential / Possession（凭证 / 持有证明）

P01—P03 都真实返回：

```text
identity status = VALID
assurance = BOUND
payment gate = ALLOW
callback = 1
VERIFIED = false
```

其中：

- P01 没有 credential；
- P02 预期 identity 中有 `credential_ref`，但当前执行没有观测到 credential，仍为 `BOUND / ALLOW`；
- P03 两边 `credential_ref` 相等，仍只到 `BOUND`，不会升级到 `VERIFIED`。

结论：当前 P3 证明的是引用/执行主体 Binding（绑定），不是 credential validity / possession / authenticator（凭证有效性 / 持有证明 / 认证器）验证。

### AP2：Authorization Signature（授权签名）

两个独立流都保持产品 `ALLOW`，同时明确暴露：

- Human Present：`ap2_user_authorization_signature_not_verified`；
- Human Not Present：`ap2_intent_authorization_signature_not_verified`；
- 两者同时保留 merchant authorization signature 未验证边界。

当前 AP2 fixtures 只有 opaque placeholder（不透明占位）或布尔字段，不构成真实 SD-JWT / credential cryptographic evidence（密码学凭证证据）。H-24 正确保留 `VERIFIED=false`。

### ACP：Webhook / Payee Authenticity（Webhook / 收款方真实性）

P06 明确暴露：

- `seller_identity_from_endpoint_context_not_verified`；
- `payee_identity_not_verified`；
- `order_webhook_signature_not_verified`。

没有任何产品字段把这些限制洗成“已验证”。

## 4. H-24 支持什么，不支持什么

H-24 支持：

1. B-15 是真实的项目级安全边界，不再只是路线图上的概念待办；
2. Cryptographic Signature Verification（密码学签名验证）缺口至少横跨 AP2 Human Present、AP2 Human Not Present、ACP 三个独立入口；
3. P3 的 Credential / Possession（凭证 / 持有证明）缺口也真实存在；
4. 当前所有已验证事实都没有产生虚假 `VERIFIED`。

H-24 **不支持**：

- 把 P3 credential assurance（凭证保证）和 AP2/ACP message signature（消息签名）直接实现成一个大而全模块；
- 声称 AP2 / ACP 已完成协议一致性认证；
- 声称真实 Agent 身份已经认证；
- 直接建设 PKI、OIDC、Passkey、钱包、区块链或生产密钥系统。

## 5. 对 B-15 的重新分层

H-24 之后，B-15 应分成两条机制族：

```text
B-15A Signed Instruction Verification（签署指令验证）【当前第一子瓶颈】
  AP2 HP + AP2 HNP + ACP
  → 多入口重复出现
  → 先建立可审计的协议中立验证事实

B-15B Credential / Possession Verification（凭证 / 持有证明验证）【后续】
  P3 Identity Gate
  → 当前只有一条主要消费链证据
  → 保持真实缺口，但暂不抢主线
```

选择 B-15A 的原因不是“签名看起来高级”，而是它已经出现至少三个独立入口，重复性和影响范围都高于单点 P3 credential 问题。

## 6. 外部要求与协议依据

本仓 `PCAC-AGENTPAY` 映射中，KYA 身份识别、Agent 身份链路、用户意愿核验、授权完整性与 Evidence Chain（证据链）都被列为 CORE（核心）或 CORE / ADAPTER（核心 / 适配）方向。后续能力包必须继续保留适用性、成熟度、测试证据与残余风险，不得写成监管合规结论。

现有 TE05 路线也明确要求：只有出现明确 signer（签署者）、signed object/version（被签对象/版本）和 key relation（密钥关系）时才进入；签名有效只能证明某个密钥对确定消息完成可验证签署，不能自动证明业务授权合理。

Evaluator 进一步核对 ACP 2026-04-17 官方 Webhook OAS：`Merchant-Signature` 采用 `t=<unix_seconds>,v1=<64_hex>`，HMAC-SHA256 对 `timestamp + "." + raw_body` 签名；缺失、格式错误、时间窗外或验证失败应拒绝，推荐 tolerance（容忍窗口）300 秒。

这给出了一个可以在本地、无网络、无生产密钥条件下真实验证的第一个消费者。

## 7. Continuation decision / 后续决策

Decision: **CONTINUE**。

下一包不是完整 TE05，而是一个 bounded capability experiment（有界能力实验）：

`P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1`

目标：

```text
protocol-neutral SignedInstructionVerificationFact
        ↓
protocol-neutral HMAC-SHA256 verification primitive
        ↓
ACP 2026-04-17 Merchant-Signature adapter / consumer
        ↓
valid / tampered body / wrong secret / stale timestamp / malformed-missing evidence
        ↓
事实层输出 VALID / INVALID / MISSING_EVIDENCE
```

边界：

- 使用 synthetic test-only secret（合成测试密钥），不保存生产密钥；
- ACP parser（解析器）负责协议格式，通用 Trusted Execution（可信执行）层不硬编码 ACP header；
- 不实现 AP2 SD-JWT；
- 不把 P3 提升为 `VERIFIED`；
- 不把 signature `VALID` 等同于业务 `ALLOW`；
- 不声称 ACP conformance（协议一致性认证）或生产认证安全。

如果该能力包通过并产生一个真实 ACP consumer（消费者）+ 多个负例，B-15A 继续看是否值得接 AP2；如果只形成 ACP 单点价值、无法复用，则停止扩展通用签名能力并重新评估 B-15。

## 8. Final evidence

- H-24 result SHA-256: `4b2829adfb743a5e940d6e46908f9e89ec63518ca0c93c37a6fa8b1f6b29322c`
- H-24 runner SHA-256: `217f1d818e58b2e71df63c38598cc8b7171e5aa9268a3d833d11308215536794`
- L3 gate: `7/7 PASS`
- full unittest: `662/662 PASS`
- no commit / push / API / network / real credential-key-signature-payment operation

# Draft Task Contract

Task ID: `P9_AP2_SIGNED_MANDATE_VERIFIABLE_FIXTURE_FEASIBILITY_V1`  
Task name: AP2 Signed Mandate Verifiable Fixture Feasibility  
Task kind: `evaluator_design`  
Contract state: `DRAFT_CONTRACT`  
Baseline HEAD: `8b9d5b46516cad330c89acf7822598a33dc9007c`  
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-13-r37`  
Active bottleneck: `B-15 / B-15A Signed Instruction Verification`  
Hypothesis: `H-26`

Inherited accepted snapshot: H-25 implementation remains uncommitted because commit authorization is false; H-26 is evaluator-only and must not mutate that accepted product snapshot.

## Why this task exists / 为什么现在做

H-25 已由 Evaluator 独立复核为 `PASS / IMPROVED / CONTINUE`：ACP Webhook 已成为 `SignedInstructionVerificationFact` 的第一个真实消费者，冻结签名语义从 `0/6→6/6`，L3 `10/10 PASS`，既有支付守护线没有退化。

下一步最重要的问题不是继续堆签名算法，而是验证这个 protocol-neutral fact（协议中立事实）能否被**第二个真实协议消费者**复用。AP2 是当前最有价值的候选，但本仓现有 AP2 v0.2.0 normalized fixtures（归一化样例）仍主要是：

- `merchant_authorization = "fixture-merchant-jwt"`；
- `user_authorization = "fixture-user-authorization"` 或 `null`；
- `intent_mandate_user_signed = true` 之类布尔事实。

这些可以保留为协议适配样例，但不足以证明真实 cryptographic verification（密码学验证）。因此在写任何 AP2 verifier（验证器）之前，先做证据可行性门。

## Missing dependency / 当前缺的关键事实

本任务仍处于 `DRAFT_CONTRACT`，因为下面这些事实尚未全部冻结：

1. 可引用的 pinned AP2 source/revision（固定协议/源码版本）；
2. exact signed object（精确被签对象）及 canonicalization / binding rule（规范化 / 绑定规则）；
3. algorithm + signer/key relation（算法 + 签署者/密钥关系）；
4. 至少一个可机械复现的 valid signed vector（合法签名向量）；
5. 至少覆盖 tamper（篡改）、wrong key / issuer（错误密钥 / 签发方）、binding mismatch（绑定错位）的负向向量；
6. fixture/vector 的 provenance + license（来源与许可）；
7. 这些验证可以在本地离线完成，不依赖生产凭据、真实资金或线上放行。

在 1–7 没有满足前，不冻结 capability experiment（能力实验），也不进入 AP2 产品代码。

## Objective / 单一目标

判断 AP2 Signed Mandate（签署 Mandate）是否已经具备足够真实、固定、可机械复核的 cryptographic fixture（密码学样例），可以成为 `SignedInstructionVerificationFact` 的第二个协议消费者。

本任务只做证据与合同设计，不实现 verifier。

## Decision outputs / 决策输出

只允许两个方向：

```text
READY_FOR_AP2_SECOND_CONSUMER
→ 1–7 全部满足
→ Evaluator 再冻结一个独立 capability_experiment

AP2_SECOND_CONSUMER_NOT_READY
→ 任一关键证据不足
→ 不写占位验签代码
→ 重新比较 B-15B Credential / Possession 或其他具备真实 verifier contract 的消费者
```

## Allowed scope / 允许范围

Evaluator-only（仅评估者）文档与证据：

- 本任务目录下的 `CONTRACT.md`、后续 source audit / evidence；
- `docs/reference/01_支付协议/**` 中必要的 AP2 来源索引或快照说明；
- `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`，仅在证据足以重排方向时更新；
- `CURRENT.md` 路由。

## Explicit exclusions / 明确排除

- 不修改 `src/**` 产品实现；
- 不新增 AP2 JWT / SD-JWT / VC verifier；
- 不把 placeholder JWT、布尔 `signed=true` 或 opaque token 当作已验签证据；
- 不升级 P3 `BOUND → VERIFIED`；
- 不使用生产私钥、商户 secret、真实 credential、真实资金；
- 不接 live endpoint / testnet / wallet / bank sandbox；
- 不新增依赖；
- 不声称 AP2 conformance（协议一致性认证）、生产认证安全或监管合规。

## Readiness criteria / 从 DRAFT 升级的条件

当且仅当 Evaluator 能把 1–7 的每一项都绑定到固定来源和可复核证据后，才允许：

1. 将本任务从 `DRAFT_CONTRACT` 完成并作出 READY / NOT_READY 决策；
2. 如果 READY，另建 AP2 second-consumer capability package；
3. 如果 NOT_READY，停止 AP2 coding（停止 AP2 编码）并重新排序 B-15B / 其他候选。

## Authorization / 授权边界

- commit: false
- push: false
- history_rewrite: false
- production API/network action: false
- real payment / credential / private-key / merchant-secret use: false

本任务若需要公开资料检索，只用于只读证据核验，不自动获得任何外部写入或生产系统操作授权。

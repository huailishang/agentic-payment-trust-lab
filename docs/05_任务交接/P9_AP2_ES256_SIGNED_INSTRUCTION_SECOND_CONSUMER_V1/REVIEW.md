# Evaluator Review

Task ID: `P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1`  
Task kind: `capability_experiment`  
Evaluator verdict: **PASS**  
Project impact verdict: **IMPROVED**  
Continuation decision: **SWITCH**  
Reviewed baseline HEAD: `8b9d5b46516cad330c89acf7822598a33dc9007c`  
Project map revision reviewed: `2026-09-13-r38`

## Project context brief / 项目全局位置

```text
A. 评测与治理底座                  [完成]
→ B. 授权、绑定、来源、执行前治理   [完成]
→ C. 支付生命周期、恢复、补救证据链 [完成]
→ D. 责任归因与可消费审计链         [完成]
→ E. 主体真实性 / 凭证 / 签署指令   [当前]
→ F. 外部真实协议 / SDK / 网络接入   [未来，受授权约束]
```

阶段 E 当前分成：

- B-15A Signed Instruction Verification（签署指令验证）；
- B-15B Credential / Possession Verification（凭证 / 持有证明验证）。

H-25 已建立 ACP HMAC 第一消费者；H-27 的唯一目标是验证同一个 protocol-neutral `SignedInstructionVerificationFact` 是否真的能被第二个协议 / 第二种密码学机制复用，而不是继续补第三个协议。

## Pre-review checks / 评估前检查

1. Executor `REPORT.md` 状态为 `SUBMITTED_FOR_REVIEW`；
2. Frozen L2 Validation Plan（冻结验证计划）`10/10 PASS`；
3. workflow validator（工作流校验器）在接受提交后返回 `OK`；
4. Evaluator 将路由切到 `READY_FOR_REVIEW / Evaluator`；
5. Evaluator 使用同一冻结 `VALIDATION_PLAN.yaml` 独立重跑 L3，生成新的 `RV-EV-01..10`，不复用 Executor 的 EV 结论；
6. 代码边界人工复核：Trusted Execution（可信执行）只处理 compact JWS / ES256 / `alg` / `kid` / JWK / signer / time；AP2 Adapter 只负责 `iss/iat/exp` 映射并委托通用 verifier；没有 Payment `ALLOW`、Identity `VERIFIED` 或 AP2 cart/payment 字段进入通用层。

## L3 Independent Gate / L3 独立复核门禁

- Gate result: **PASS**
- Gate summary: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evidence/L3-GATE.json`
- Validation plan: `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/VALIDATION_PLAN.yaml`
- Checks: `10/10 PASS`
- Mandatory failures: `0/10`

Independent highlights:

```text
RV-EV-02: H-27 AP2 ES256 capability 6/6; repeat=2 deterministic; consumers 1→2; 5/5 negatives fail closed
RV-EV-03: result schema / matrix / data-boundary audit PASS
RV-EV-04: generic ES256 remains protocol-neutral; AP2 owns protocol mapping only
RV-EV-05: focused tests PASS
RV-EV-07: H-25 ACP first-consumer result byte-stable
RV-EV-08: Product Trace 10/12; GESR 9/12; callback 12/12; unsafe allow 0/5
RV-EV-09: S01-S13 13/13 PASS; AP2 minimal flow 2/2 PASS; Attack Overlay 6/6 PASS
RV-EV-10: full unittest 692/692 PASS
```

H-27 result SHA-256:

`ff63e96d4ad02670541733cc48bf3a66d184cec84ead34e9dc0b0bd2b277cea6`

H-25 accepted result SHA-256 remains:

`888d8d9ae215ce3d4ac593c190a2863746fddf1d99ca78175324670615b22a37`

## Acceptance matrix / AC 逐条裁决

| AC | Verdict | Independent basis |
|---|---|---|
| AC-01 Fact remains protocol-neutral | 通过 | `RV-EV-01/03/04/05/06`：同一 Fact 承载 HMAC + ES256；公共字段保持兼容；H-25 不变 |
| AC-02 Generic ES256 verifier is generic | 通过 | `RV-EV-04/05`：通用层无 AP2 Mandate / cart / payment / business 分支 |
| AC-03 AP2 second consumer is real | 通过 | `RV-EV-01/02/04/05`：新 AP2 adapter 实际调用通用 verifier；旧 `adapters/ap2.py` byte-stable |
| AC-04 Six headline cases | 通过 | `RV-EV-02/03/05`：6/6，repeat=2 全部 deterministic |
| AC-05 Additional negative boundaries | 通过 | `RV-EV-05`：unsupported alg、wrong kid、future/expired、`exp < iat`、malformed/non-P256 JWK 全部 fail-closed |
| AC-06 Second-consumer proof | 通过 | `RV-EV-02/03/04`：real consumers `1→2`；AP2 executable semantics `0/6→6/6` |
| AC-07 Sensitive-data boundary | 通过 | `RV-EV-01/02/03/05`：无 private key/raw token/raw signature/生产凭据持久化；真实支付/生产密钥=0 |
| AC-08 H-25 regression stability | 通过 | `RV-EV-06/07`：H-25 accepted result SHA-256 精确不变 |
| AC-09 Project guardrails | 通过 | `RV-EV-08/09/10`：Product Trace 10/12、GESR 9/12、callback 12/12、duplicate/forbidden 0/12、unsafe allow 0/5、S01-S13 13/13、692/692 |
| AC-10 Dependency boundary | 通过 | `RV-EV-01/04`：只声明 `cryptography>=41`；本机已有 41.0.7；无 install/network |
| AC-11 External requirement honesty | 通过 | `RV-EV-03` + REPORT：`PCAC-AGENTPAY / PCAC-06 / ADAPTER`，残余风险保留，无 conformance/compliance 宣称 |
| AC-12 v2.2 handoff complete | 通过 | L2 10/10 + L3 10/10 + REPORT 完整 + workflow validator OK |

## Capability result / 能力结果

H-27 冻结能力信号达到：

```text
AP2 ES256 executable semantics: 0/6 → 6/6
real Signed Instruction consumers: 1 → 2
```

六案例：

```text
V01 valid ES256 JWS       → VALID
N01 tampered payload      → INVALID / signature_mismatch
N02 wrong public key      → INVALID / signature_mismatch
N03 wrong signer binding  → INVALID / signer_mismatch
N04 missing authorization → MISSING_EVIDENCE
N05 malformed compact JWS → INVALID / compact_jws_format_invalid
```

这证明的不是“完整 AP2 已实现”，而是：**同一个 `SignedInstructionVerificationFact` 已经被 ACP/HMAC 与 AP2/ES256 两个不同协议、不同算法消费者真实复用。**

`VALID` 仍只表示 exact signed input（精确被签输入）在给定 key/signer/time 约束下通过密码学验证，不等于 Payment `ALLOW`、Identity `VERIFIED`、credential validity（凭证有效性）或监管合规。

## Project impact verdict / 项目影响裁决

Impact verdict: **IMPROVED**

理由：

- B-15A 的核心架构问题从“只有一个消费者，可能只是 ACP 包装”前移到“两个独立消费者跨协议 / 跨算法复用同一 Fact”；
- consumers `1→2`、AP2 `0/6→6/6`，且 5/5 negatives fail-closed；
- H-25 accepted result byte-stable，证明第二消费者没有破坏第一消费者；
- 通用层没有出现 `if protocol == AP2 / ACP` 一类协议污染；
- 12-task GESR 仍为 `9/12`，因此本任务没有虚假宣称整体支付链指标提升。

## Representative closure decision / 代表性闭合裁决

B-15A：**RESOLVED / STAGE_CLOSED**。

原因不是“已经支持所有协议”，而是当前代表性证据已经足够回答原始架构问题：

```text
ACP + HMAC-SHA256
        ↓
SignedInstructionVerificationFact
        ↑
AP2 + ES256/P-256
```

两个消费者在协议格式、密钥模型和算法上都不同，仍复用同一 Fact / 通用验证边界；继续补第三个协议的边际信息增益已经明显下降。

因此不继续为了“协议数量”接 x402 / UCP / 第三个 verifier。只有以后出现新的机制反例，才重新打开 B-15A。

## Residual boundaries / 残余边界

B-15A 关闭不代表阶段 E 完成。仍有：

1. P3 `IdentityAssuranceLevel` 最高仍为 `BOUND`；`VERIFIED` 明确保留给未来 credential verifier / provider attestation；
2. P3 当前 credential 只做 reference match（引用匹配），不验证 credential authenticity（凭证真实性）或 proof-of-possession（持有证明）；
3. H-27 使用 evaluator-owned synthetic ES256 fixture，不是 live AP2 conformance / production key infrastructure；
4. full SD-JWT holder binding、live JWKS/DID/PKI、生产 credential/key governance 仍未验证；
5. B-03 T05/T06、B-04、B-05 保持 WATCH；B-06 live SDK/network 继续 DEFERRED。

## Continuation / 下一步

Continuation decision: **SWITCH**。

下一主线从 B-15A 切到 **B-15B Credential / Possession Verification（凭证 / 持有证明验证）**。

不直接实现“万能身份系统”。下一步先冻结真实机制边界：

```text
credential validity（凭证有效性）
≠
proof of possession（持有证明）
≠
identity / authorization decision（身份 / 授权决策）
```

H-24 已经证明 P3 的 `credential_ref` 只到引用匹配；公开标准对比也表明：SPIFFE SVID 更贴近 workload/executor identity（工作负载/执行器身份），而 OAuth DPoP 更偏 access-token sender constraint（访问令牌发送方约束），且 DPoP 本身不是 client authentication（客户端认证）。所以下一步应先做有界 evaluator-design（评估设计）证据门，再决定 B-15B 的第一种真实 verifier contract（验证合同），不能直接把现有 ES256 helper 套成 `VERIFIED`。

## Final verdict / 最终裁决

- Task verdict: **PASS**
- Project impact: **IMPROVED**
- B-15A: **RESOLVED / STAGE_CLOSED**
- Continuation: **SWITCH**
- Next active direction: **B-15B Credential / Possession Verification**

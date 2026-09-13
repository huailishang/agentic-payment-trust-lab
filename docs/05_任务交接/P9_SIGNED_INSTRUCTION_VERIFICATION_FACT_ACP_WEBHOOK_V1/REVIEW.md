# Evaluator Review

Task ID: `P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1`  
Task kind: `capability_experiment`  
Evaluator verdict: **PASS**  
Project impact verdict: **IMPROVED**  
Continuation decision: **CONTINUE**  
Reviewed baseline HEAD: `d26fa658b970f84ca25859d7c3739994cae10a61`  
Project map revision reviewed: `2026-09-12-r36`

## 1. Project context brief / 项目全局位置

```text
A. 评测与治理底座                  [完成]
→ B. 授权、绑定、来源、执行前治理   [完成]
→ C. 支付生命周期、恢复、补救证据链 [完成]
→ D. 责任归因与可消费审计链         [完成]
→ E. 主体真实性 / 凭证 / 签署指令   [当前]
→ F. 外部真实协议 / SDK / 网络接入   [未来，受授权约束]
```

H-24 已把阶段 E 拆成两个不同机制族：

- B-15A Signed Instruction Verification（签署指令验证）：AP2 HP / AP2 HNP / ACP 三个独立入口重复出现；
- B-15B Credential / Possession Verification（凭证 / 持有证明验证）：当前主要集中在 P3，最高仍为 `BOUND`。

H-25 只打 B-15A：建立协议中立验证事实 + HMAC-SHA256 verifier（验证器）+ ACP Webhook 第一个真实消费者。它不是完整身份认证、不是 AP2 验证、也不是生产密钥系统。

## 2. Acceptance and independent rerun / 接受提交与独立复核

Executor 报告状态为 `SUBMITTED_FOR_REVIEW`，L2 frozen Validation Plan（冻结验证计划）为 `10/10 PASS`。Evaluator 在接受提交快照后：

1. 运行 workflow validator（工作流校验器）：`OK`；
2. 将路由切到 `READY_FOR_REVIEW / Evaluator`；
3. 使用同一冻结 `VALIDATION_PLAN.yaml` 独立运行 L3；
4. L3 生成新的 `RV-EV-*` 证据，不复用 Executor 的 EV 结论。

独立结果：

```text
L3 gate = 10/10 PASS
mandatory failures = 0/10
H25 six cases = 6/6
repeat = 2/case, all identical
negative cases fail closed = 5/5
focused tests = 13/13 PASS
H24 accepted result SHA-256 unchanged
Project Trace = 10/12
GESR = 9/12
callback match = 12/12
duplicate/forbidden side effect = 0/12
unsafe allow = 0/5
formal scenarios = 13/13 PASS
full unittest = 675/675 PASS
external network / real payment / production credential-key-secret = 0
```

L3 evidence root:

`docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/`

L3 gate:

`L3-GATE.json` / `L3-GATE.md`

## 3. AC verdicts / 验收项裁决

| AC | Verdict | Independent basis |
|---|---|---|
| AC-01 Protocol-neutral fact contract | 通过 | `RV-EV-01/03/05`：字段合同、最小化、状态语义通过；无 raw secret/body/signature、无支付 decision 字段 |
| AC-02 Generic verifier is generic | 通过 | `RV-EV-01/04/05`：Trusted Execution 层无 ACP 解析/业务决策耦合，使用 stdlib `hmac/hashlib` 与 `hmac.compare_digest` |
| AC-03 ACP consumer contract | 通过 | `RV-EV-01/02/04/05`：严格 `t=<unix>,v1=<64_hex>`，精确 `timestamp + "." + raw_body`，默认 300s，委托通用 verifier |
| AC-04 Six-case semantics | 通过 | `RV-EV-02/03/05`：冻结 6/6、repeat=2；inclusive 300s 有效，future 301s INVALID |
| AC-05 Fail-closed and honest semantics | 通过 | `RV-EV-02/04/05`：tamper / wrong key / stale / future / missing / malformed 均不成为 VALID；无 `ALLOW` / `VERIFIED` 升级 |
| AC-06 First real protocol consumer | 通过 | `RV-EV-04`：ACP adapter 实际调用通用 verifier，没有复制 `hmac.new` / `compare_digest` |
| AC-07 Sensitive-data minimization | 通过 | `RV-EV-02/03/05`：结果不持久化 synthetic secret、raw body、raw signature/header、credential/token/cookie |
| AC-08 H-24 boundary stability | 通过 | `RV-EV-01/06/07`：受保护文件保持冻结；H-24 accepted result SHA-256=`4b2829adfb743a5e940d6e46908f9e89ec63518ca0c93c37a6fa8b1f6b29322c` |
| AC-09 Project guardrails | 通过 | `RV-EV-08/09/10`：基线 repeat=3 一致、13/13 正式入口、675/675 全量，无新增副作用 |
| AC-10 External requirement boundary | 通过 | `RV-EV-03` + REPORT：`PCAC-AGENTPAY / PCAC-06 / ADAPTER`，残余风险明确，无监管合规结论 |
| AC-11 v2.2 handoff complete | 通过 | L2 10/10、L3 10/10、REPORT 完整、workflow validator `OK` |

## 4. Capability result / 能力结果

H-25 冻结能力信号真实达到：

```text
ACP signed-webhook executable semantics
0/6 → 6/6
```

六案例：

```text
V01 valid signature       → VALID
N01 tampered body         → INVALID / signature_mismatch
N02 wrong secret          → INVALID / signature_mismatch
N03 stale timestamp       → INVALID / timestamp_outside_window
N04 missing header        → MISSING_EVIDENCE
N05 malformed header      → INVALID / signature_format_invalid
```

H25 result SHA-256：

`888d8d9ae215ce3d4ac593c190a2863746fddf1d99ca78175324670615b22a37`

这不是“测试数增加”而已：ACP Webhook 已成为一个真实 consumer（消费者），会把协议格式解析后交给协议中立 Signed Instruction fact/verifier 层；负例能机械区分篡改、错误密钥、时间过期和证据缺失。

## 5. Project impact verdict / 项目影响裁决

Project impact: **IMPROVED**。

理由：

- B-15A 从 `signature not_verified` 的 limitation（已知限制）前移到第一个可执行、可负测、可回放的真实性能力锚点；
- targeted capability（目标能力）`0/6→6/6`；
- ACP adapter 是真实消费者，不是 dead helper（无人消费的工具函数）；
- H-24 的旧边界仍 byte-stable（字节级稳定），没有把旧 ACP checkout snapshot“洗成已验签”；
- GESR 仍为 `9/12`，所以本任务没有虚假宣称整体端到端成功率提升；
- 所有零容忍 guardrail（守护线）未退化。

## 6. Residual boundaries / 仍然没有解决的真实性问题

H-25 通过不代表阶段 E 已完成。至少还有四个边界：

1. `signer_ref` / `key_ref` 当前是调用方传入的引用，本任务没有证明它们已经绑定到可信 Key Registry（密钥注册表）或真实主体；
2. HMAC 是 shared-secret（共享密钥）验证，只证明“持有该共享 secret 的一方对这些字节产生了匹配 MAC”，不自动证明法律身份或独占签署者；
3. freshness window（时间新鲜度窗口）不是完整 nonce / replay registry（随机数 / 重放注册表）；
4. AP2 的 JWT / SD-JWT / Verifiable Credential（可验证凭证）与 P3 Credential / Possession（凭证 / 持有证明）仍未验证。

这些是明确 residual risk（残余风险），不是 H-25 AC 失败，因为合同已明确排除。

## 7. Iteration-value decision / 是否继续沿这个方向

Decision: **CONTINUE**，但**不直接开始 AP2 实现**。

H-25 已证明 `SignedInstructionVerificationFact` 有第一个真实 consumer（消费者）价值；下一步最有信息增益的问题是：能否找到第二个**真实可验证**的签署指令消费者，证明 fact contract（事实合同）可以跨算法 / 跨协议复用。

当前仓库内 AP2 v0.2.0 normalized fixtures（归一化样例）仍只是：

- `merchant_authorization = "fixture-merchant-jwt"`；
- `user_authorization = "fixture-user-authorization"` 或 `null`；
- HNP `intent_mandate_user_signed = true` 是布尔事实。

这些不能作为真实密码学验签样例，禁止据此直接写“AP2 verifier”。

外部 AP2 当前模型已经明确把 CartMandate `merchant_authorization` 定义为签名 JWT，把 PaymentMandate `user_authorization` 描述为可包含 SD-JWT-VC / key-binding JWT 的 verifiable presentation（可验证呈现）。这说明 AP2 仍是合理的第二消费者候选；但当前项目还缺**固定 revision + 可机械验证的 signed object + key relation + 正负 golden vectors（黄金向量）**。在这些证据冻结之前，不进入产品代码。

因此下一步优先做一个 bounded evaluator-design（有界评估设计）任务：**AP2 Signed Mandate Verifiable Fixture Feasibility（AP2 签署 Mandate 可验证样例可行性）**。它只决定“是否具备真实第二消费者的证据条件”，不改产品逻辑。

如果能冻结官方/可信来源的可验证样例：继续 B-15A 第二消费者；如果不能：STOP AP2 coding（停止 AP2 编码），再在 B-15B Credential / Possession 或其他具备真实 verifier contract（验证合同）的入口中重排。

## 8. Bottleneck movement summary / 瓶颈前移总结

```text
评估前：
B-15A 只有重复出现的 signature-not-verified 缺口

H-25：
建立 SignedInstructionVerificationFact
+ generic HMAC-SHA256 verifier
+ ACP Webhook first consumer

评估后：
B-15A 已获得第一个真实能力锚点
但“协议中立是否真的可复用”尚未由第二消费者证明
```

因此：

- H-25：**PASS**
- Project impact：**IMPROVED**
- B-15A：**SHRANK / NOT CLOSED**
- Continuation：**CONTINUE**
- Next task：`P9_AP2_SIGNED_MANDATE_VERIFIABLE_FIXTURE_FEASIBILITY_V1`
- Next path：`docs/05_任务交接/P9_AP2_SIGNED_MANDATE_VERIFIABLE_FIXTURE_FEASIBILITY_V1/CONTRACT.md`
- Next state：`DRAFT_CONTRACT / Evaluator`
- 下一步：先冻结 AP2 第二消费者的真实密码学证据条件，不直接写 AP2 验证代码。

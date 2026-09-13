# Evaluator ↔ Executor Current State

<!-- evaluator-executor-workflow:v2.2 -->

```yaml
workflow: evaluator-executor-workflow/v2.2
task_id: P9_P3_CREDENTIAL_POSSESSION_VERIFIER_EVIDENCE_GATE_V1
task_kind: evaluator_design
state: DRAFT_CONTRACT
current_role: Evaluator
baseline_commit: 8b9d5b46516cad330c89acf7822598a33dc9007c
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-09-13-r39
active_bottleneck_id: B-15
hypothesis_id: H-28
contract_path: docs/05_任务交接/P9_P3_CREDENTIAL_POSSESSION_VERIFIER_EVIDENCE_GATE_V1/CONTRACT.md
executor_report_path: NONE
evaluator_review_path: NONE
next_artifact_path: docs/05_任务交接/P9_P3_CREDENTIAL_POSSESSION_VERIFIER_EVIDENCE_GATE_V1/CONTRACT.md
authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
```

## Global position / 全局位置

```text
A. 评测与治理底座                  [完成]
→ B. 授权、绑定、来源、执行前治理   [完成]
→ C. 支付生命周期、恢复、补救证据链 [完成]
→ D. 责任归因与可消费审计链         [完成]
→ E. 主体真实性 / 凭证 / 签署指令   [当前]
→ F. 外部真实协议 / SDK / 网络接入   [未来，受授权约束]
```

当前阶段 E：

- B-15A Signed Instruction Verification（签署指令验证）【已代表性闭合 / STAGE_CLOSED】；
- B-15B Credential / Possession Verification（凭证 / 持有证明验证）【当前第一子瓶颈】。

## Previous accepted result / 上一能力结果

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
H-25 accepted result SHA-256: unchanged
real payment / production credential-key / network: 0
```

因此 B-15A 不再继续增加第三协议；ACP/HMAC + AP2/ES256 已足以证明 `SignedInstructionVerificationFact` 的跨协议 / 跨算法复用。

## Current action / 当前动作

H-28 是 `evaluator_design（评估设计）`，不是 Executor 编码包。

当前只回答：**P3 从 `BOUND` 合法升级到 `VERIFIED`，到底必须具备哪些真实 credential / possession（凭证 / 持有证明）证据，以及第一种值得实现的 verifier mechanism（验证机制）是什么。**

Read first:

- `docs/05_任务交接/P9_P3_CREDENTIAL_POSSESSION_VERIFIER_EVIDENCE_GATE_V1/CONTRACT.md`
- `docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/REVIEW.md`
- `docs/05_任务交接/P9_ACTOR_AUTHENTICITY_SIGNED_INSTRUCTION_GAP_MEASUREMENT_V1/CONTRACT.md`
- `src/agentic_payment_experiment/trusted_execution/execution_facts.py`

必须冻结：

```text
1. credential format + trust semantics
2. subject identity → agent/provider/executor mapping
3. proof-of-possession semantics
4. freshness / nonce / replay boundary
5. deterministic positive vector
6. wrong trust / wrong subject / no possession / replay-or-stale negatives
7. exact BOUND → VERIFIED promotion rule
8. no production credential / real payment / live network dependency
```

必须保持：

```text
credential validity
≠ proof of possession
≠ identity / authorization decision
```

Do not:

- 修改 `src/**`、tests 或 runner；
- 把 `credential_ref` 相等、signed token 或单次签名成功直接写成 `VERIFIED`；
- 建设万能 IAM / PKI / OAuth / OIDC / Passkey / biometrics 平台；
- 接 live SPIRE / Workload API / JWKS / DID / bank sandbox / wallet / testnet；
- 使用生产 credential、certificate、private key、trust bundle 或真实资金；
- commit、push、history rewrite。

## Routing rule

H-28 当前保持 `DRAFT_CONTRACT / Evaluator`。证据充分时，Evaluator 应直接冻结新的 P3 Credential / Possession capability package（能力执行包）；证据不足时保持 P3 `BOUND`，不得制造假的 `VERIFIED`。

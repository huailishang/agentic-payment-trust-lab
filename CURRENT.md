# Evaluator ↔ Executor Current State

<!-- evaluator-executor-workflow:v2.2 -->

```yaml
workflow: evaluator-executor-workflow/v2.2
task_id: P9_P3_X509_SVID_CHALLENGE_BINDING_REPAIR_V1
task_kind: repair
state: EXECUTING
current_role: Executor
baseline_commit: fca87c2d987b3d71c1156e50747cb8eeec1c84c7
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-09-15-r41
active_bottleneck_id: B-15
hypothesis_id: H-29R
contract_path: docs/05_任务交接/P9_P3_X509_SVID_CHALLENGE_BINDING_REPAIR_V1/CONTRACT.md
executor_report_path: docs/05_任务交接/P9_P3_X509_SVID_CHALLENGE_BINDING_REPAIR_V1/REPORT.md
evaluator_review_path: docs/05_任务交接/P9_P3_X509_SVID_CHALLENGE_BINDING_REPAIR_V1/REVIEW.md
next_artifact_path: docs/05_任务交接/P9_P3_X509_SVID_CHALLENGE_BINDING_REPAIR_V1/REPORT.md
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

阶段 E：

- B-15A Signed Instruction Verification（签署指令验证）：`STAGE_CLOSED`；
- B-15B Credential / Possession Verification（凭证 / 持有证明验证）：当前第一子瓶颈；
- H-29：`REJECTED / REGRESSED`；
- H-29R：当前有界修复包。

## Previous evaluator verdict / 上一评估结论

H-29 的 Executor L2 与 Evaluator 对冻结 VP-01..08 的独立复跑均通过：

```text
frozen matrix = 7/7
focused tests = 29/29
formal scenarios = 13/13
full unittest = 698/698
protected Signed Instruction / AP2 / ACP / dependency hashes = unchanged
```

但 Evaluator 独立反例 `RV-EV-09` 证明：

```text
old signed challenge payload
+ old valid signature
+ relabelled fresh nonce_ref / issued_at / observed_at
→ current verifier incorrectly returns VALID / credential_possession_verified
```

根因：签名覆盖 `challenge_payload`，但 freshness/replay（新鲜度 / 防重放）使用的 nonce / issued_at 由外部参数单独传入，未证明这些值就是被签名 payload 中的值。

因此：

```text
Task verdict: REJECTED
Project impact: REGRESSED
Continuation: CONTINUE with bounded repair
```

Review：
`docs/05_任务交接/P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1/REVIEW.md`

## Current repair / 当前修复

Executor 读取：

1. `docs/05_任务交接/P9_P3_X509_SVID_CHALLENGE_BINDING_REPAIR_V1/CONTRACT.md`
2. `docs/05_任务交接/P9_P3_X509_SVID_CHALLENGE_BINDING_REPAIR_V1/VALIDATION_PLAN.yaml`
3. `docs/05_任务交接/P9_P3_X509_SVID_CHALLENGE_BINDING_REPAIR_V1/evaluator_checks/challenge_binding_counterexample.py`
4. Parent H-29 `REVIEW.md`

只允许一个 principal change（主要变化）：

```text
在 credential_possession verifier 内
重建 canonical challenge bytes：
nonce + agent + provider + executor + issued_at
        ↓
要求 challenge_payload exact match
        ↓
再验 signature
```

必须实现：

```text
old signed payload/signature + fresh metadata label
→ INVALID / credential_possession_challenge_binding_mismatch
→ never VERIFIED
```

必须保持：

```text
parent H-29 frozen matrix = 7/7
credential_ref-only = BOUND
execution_facts.py = frozen
payment_execution.py = frozen
Payment policy = unchanged
Signed Instruction / AP2 / ACP = frozen
```

Do not:

- 修改 `execution_facts.py` / `payment_execution.py`；
- 改 BOUND→VERIFIED 四条件；
- 改 Payment policy；
- 接 live SPIRE / PKI / OIDC / DID / VC；
- 新增依赖 / 网络调用；
- 使用生产 credential / private key / trust bundle；
- commit、push、history rewrite。

## Executor completion rule

最多 `2` 个完整 implementation → L2 cycle（实现→L2 验证循环）。

提交前必须：

```text
challenge-binding counterexample PASS
parent H-29 7/7 remains PASS
focused regressions PASS
project guardrails no regression
S01-S13 = 13/13
full unittest zero failures
L2 Validation Plan PASS
REPORT maps AC-R01..08
```

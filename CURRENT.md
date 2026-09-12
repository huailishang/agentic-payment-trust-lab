# Evaluator ↔ Executor Current State

<!-- evaluator-executor-workflow:v2.2 -->

```yaml
workflow: evaluator-executor-workflow/v2.2
task_id: P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1
task_kind: capability_experiment
state: CONTRACT_FROZEN
current_role: Executor
baseline_commit: d26fa658b970f84ca25859d7c3739994cae10a61
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-09-12-r36
active_bottleneck_id: B-15
hypothesis_id: H-25
contract_path: docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/CONTRACT.md
executor_report_path: NONE
evaluator_review_path: NONE
next_artifact_path: docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/REPORT.md
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

当前阶段 E 已由 H-24 拆成两类：

- B-15A Signed Instruction Verification（签署指令验证）【当前第一子瓶颈】；
- B-15B Credential / Possession Verification（凭证 / 持有证明验证）【后续】。

## Current action

```text
Executor owns frozen H-25 Signed Instruction Verification Fact + ACP Webhook HMAC First Consumer.

Read first:
- docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/CONTRACT.md
- docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/VALIDATION_PLAN.yaml
- docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evaluator_fixtures/ACP_WEBHOOK_SIGNATURE_MATRIX.json
- docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evaluator_checks/source_snapshot_audit.py
- docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evaluator_checks/architecture_boundary_audit.py
- docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evaluator_checks/h25_result_audit.py
- docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evaluator_checks/h24_revalidation_audit.py
- docs/05_任务交接/P9_ACTOR_AUTHENTICITY_SIGNED_INSTRUCTION_GAP_MEASUREMENT_V1/REVIEW.md

Strategic facts:
- H-24 final verdict = PASS / NOT_APPLICABLE / CONTINUE; Evaluator L3 = 7/7 PASS.
- H-24 proves the B-15 boundary is real but splits it into B-15A Signed Instruction and B-15B Credential/Possession; do not build a universal identity/security module.
- AP2 HP + AP2 HNP + ACP are three independent signature-not-verified surfaces. B-15A is primary because the mechanism repeats across more independent consumers.
- ACP 2026-04-17 official webhook contract is explicit: Merchant-Signature `t=<unix>,v1=<64_hex>`, HMAC-SHA256 over `timestamp + "." + raw_body`, with a 300-second recommended freshness window.
- H-25 is the first capability experiment in stage E, not another measurement-only task.

One principal change:
- add one protocol-neutral SignedInstructionVerificationFact + generic HMAC-SHA256 verifier + one ACP Webhook consumer that parses the official Merchant-Signature format and delegates cryptographic verification to the generic layer.

Do:
- add `src/agentic_payment_experiment/trusted_execution/signed_instruction.py`;
- export only the new generic fact/verifier through trusted_execution `__init__.py`;
- add `src/agentic_payment_experiment/adapters/acp_webhook.py` and export its bounded API;
- keep existing `adapters/acp.py`, AP2 adapter and P3 identity/payment gate byte-frozen;
- use Python stdlib hmac/hashlib only; no dependency install;
- use `hmac.compare_digest`;
- parse exactly `t=<unix_seconds>,v1=<64_hex>` and sign exact `timestamp + "." + raw_body` bytes;
- execute exactly six frozen cases, repeat=2, and produce H25_SIGNED_INSTRUCTION_RESULT.json without raw secret/body/signature material;
- test inclusive freshness boundary and future out-of-window in focused unit tests;
- keep signature VALID separate from Payment ALLOW and Identity VERIFIED;
- rerun H-24 and require exact accepted SHA-256 unchanged;
- run frozen L2 10/10 and write REPORT.md with AC-01..11, targeted `0/6→6/6`, PCAC-06 ADAPTER impact, residual risks, guardrails and scope evidence;
- submit only after workflow validator is OK.

Stop and return BLOCKED if:
- any frozen P3/AP2/ACP checkout/H-24 file must change;
- implementation needs AP2 SD-JWT, P3 VERIFIED, PKI/wallet/OIDC, live network or production secret;
- generic verifier must know ACP header/business fields;
- ACP adapter duplicates HMAC comparison instead of consuming generic verifier;
- signature VALID must be coupled to business ALLOW;
- secret/raw body must be persisted to pass validation;
- new dependency/install is required;
- more than two complete implementation→L2 cycles are required.

Do not:
- modify T05/T06 Product Trace, Consumer/Player, remediation, Fresh Unseen or unrelated modules;
- claim ACP conformance, production authentication/security, legal authorization or regulatory compliance;
- commit, push, call external APIs, use network, install dependencies, or use real payment/credential/key/merchant secret material.
```

## Routing rule

H-25 is a `capability_experiment` linked to project-map revision `2026-09-12-r36`, active bottleneck `B-15` / B-15A, hypothesis `H-25`.

Task PASS requires correct implementation and L2/L3 evidence. Project impact is judged separately: `IMPROVED` requires a real ACP consumer and frozen `0/6→6/6` targeted capability gain with existing project guardrails unchanged. Even if improved, Evaluator must still decide whether AP2 is worth a second consumer round or whether marginal value now favors STOP/SWITCH.

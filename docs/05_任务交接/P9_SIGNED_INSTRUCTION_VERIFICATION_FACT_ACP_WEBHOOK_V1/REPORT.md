# Executor Report

Task ID: `P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1`  
Executor status: SUBMITTED_FOR_REVIEW  
Baseline HEAD: `d26fa658b970f84ca25859d7c3739994cae10a61`  
Implementation commit: `NONE`（本任务未获得 commit 授权）  
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-12-r36`  
Active bottleneck: `B-15 / B-15A Signed Instruction Verification`  
Hypothesis: `H-25`

## Workspace snapshot

- Initial `git status --short`: clean；分支 `main...origin/main`。
- Final `git status --short`: `CURRENT.md`、两个 package export 文件为 modified；5 个冻结允许范围内的新实现/测试文件与本 `REPORT.md` 为 untracked；L2 raw evidence 位于既有 ignored evidence 区域。
- Saved diff: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/WORKSPACE.patch`（实现 + router 快照；不包含本自述 REPORT）
- Diff SHA-256: `d40456a8bcc801f788320fe0d487db33f3fa859b4843319714083f9ba4c69e60`
- External API / network / dependency install / real payment / production credential-key-secret operation: `0`

## Changed files

| File | Action | SHA-256 | Factual change |
|---|---|---|---|
| `CURRENT.md` | modified | `4097272656d953865700744464e9c23d4d2bc52027aada13f0c9c7199f4ac8ba` | router 从 `CONTRACT_FROZEN` 进入 `EXECUTING`；授权位未改变 |
| `src/agentic_payment_experiment/trusted_execution/signed_instruction.py` | new | `1261316320d6f62eddcc042d44ca604f2334c72a1fc8812f180b5faf443db8f9` | 新增协议中立 `SignedInstructionVerificationFact` 与 HMAC-SHA256 verifier；使用 `hmac.compare_digest`；时间窗采用绝对差且 `<=` 边界有效 |
| `src/agentic_payment_experiment/trusted_execution/__init__.py` | modified | `62a4a475cfba79eb4456ce1d5b5fd6d75567b388fc3a86a13bdcc3e171deaab1` | 只导出新 fact / verifier |
| `src/agentic_payment_experiment/adapters/acp_webhook.py` | new | `cc723725eb3fd220482bbc21721843d77ba92e7b7a7c29431753e6c6e0e4ffac` | 严格解析 ACP `t=<unix>,v1=<64_hex>`，拼接精确 `timestamp + "." + raw_body`，委托通用 verifier |
| `src/agentic_payment_experiment/adapters/__init__.py` | modified | `b8f0258376b336b12a9235c50d3e2fd92de10b94bd3bcb7a6028d742347821f1` | 导出 bounded ACP Webhook API |
| `scripts/validation/run_signed_instruction_verification_capability.py` | new | `5be73da638cac0583857c012acaa00575ae27b008faf383225f72f8e9d03c543` | 执行冻结 6 Case × repeat=2，并只持久化最小验证事实/哈希 |
| `tests/trusted_execution/test_signed_instruction.py` | new | `ee36a6293d02038cbfda0815474a0462bb7d08fb2481de3c3738d68cde04a570` | 通用 verifier 正负例、inclusive boundary、future out-of-window、字段最小化 |
| `tests/test_acp_webhook_signature.py` | new | `345ba33a6c1717ed5fa3e002a7f15ba37dadb4d5f1a1aef2df5877d850c74420` | ACP 精确格式、body tamper、缺失/畸形 header、重复/额外/乱序字段、时间窗 |

Evaluator-owned `CONTRACT.md`、`VALIDATION_PLAN.yaml`、matrix 与 evaluator checks 均未修改；保护的 `acp.py`、`ap2.py`、P3/payment gate、H-24 runner 保持 frozen source audit（冻结源审计）通过。

## L2 Task Gate

- Gate result: PASS
- Gate summary: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/L2-GATE.json`
- Validation plan: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/VALIDATION_PLAN.yaml`
- Mandatory failures: `0/10`
- Complete implementation → L2 cycles used: `1/2`

## EV-01

- AC: `AC-01, AC-02, AC-03, AC-08, AC-11`
- Meta: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-01.meta.json`
- Stdout: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-01.stdout.log`
- Stderr: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-01.stderr.log`

Source snapshot audit（源快照审计）确认保护文件/依赖清单未变，新 H-25 文件存在。

## EV-02

- AC: `AC-03, AC-04, AC-05, AC-06, AC-07`
- Meta: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-02.meta.json`
- Stdout: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-02.stdout.log`
- Stderr: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-02.stderr.log`

Capability runner（能力测量执行器）得到冻结 6/6，repeat=2 全部 deterministic（一致），5 个负例全部 fail-closed（失败即关闭）。

## EV-03

- AC: `AC-01, AC-04, AC-05, AC-07, AC-10`
- Meta: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-03.meta.json`
- Stdout: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-03.stdout.log`
- Stderr: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-03.stderr.log`

Result audit（结果审计）确认 schema、六案例语义、摘要、PCAC 映射与最小化持久化全部符合冻结契约；结果 SHA-256=`888d8d9ae215ce3d4ac593c190a2863746fddf1d99ca78175324670615b22a37`。

## EV-04

- AC: `AC-02, AC-03, AC-05, AC-06`
- Meta: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-04.meta.json`
- Stdout: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-04.stdout.log`
- Stderr: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-04.stderr.log`

Architecture boundary audit（架构边界审计）确认通用 verifier 不含 ACP / 支付决策耦合；ACP adapter 实际调用通用 verifier，且没有复制 `hmac.new` / `compare_digest`。

## EV-05

- AC: `AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07`
- Meta: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-05.meta.json`
- Stdout: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-05.stdout.log`
- Stderr: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-05.stderr.log`

Focused tests（专项测试）新增 `13/13` 通过；覆盖 tolerance inclusive boundary（容忍窗包含边界）与 future out-of-window（未来时间戳越界）。

## EV-06

- AC: `AC-08`
- Meta: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-06.meta.json`
- Stdout: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-06.stdout.log`
- Stderr: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-06.stderr.log`

按冻结参数重新运行 H-24 measurement（测量），没有把 H-25 的新能力反向写进旧 ACP checkout snapshot。

## EV-07

- AC: `AC-08`
- Meta: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-07.meta.json`
- Stdout: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-07.stdout.log`
- Stderr: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-07.stderr.log`

H-24 accepted result 保持 byte-stable（字节级稳定），SHA-256 仍为 `4b2829adfb743a5e940d6e46908f9e89ec63518ca0c93c37a6fa8b1f6b29322c`，`VERIFIED` 真实性仍为 `0/6`。

## EV-08

- AC: `AC-09`
- Meta: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-08.meta.json`
- Stdout: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-08.stdout.log`
- Stderr: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-08.stderr.log`

Project-impact baseline（项目影响基线）repeat=3 全部一致：Product Trace=`10/12`，GESR=`9/12`，callback match=`12/12`，duplicate/forbidden side effect=`0/12`，unsafe allow=`0/5`。

## EV-09

- AC: `AC-09`
- Meta: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-09.meta.json`
- Stdout: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-09.stdout.log`
- Stderr: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-09.stderr.log`

正式实验入口 `S01..S13 = 13/13 PASS`；本轮无网络、无真实 Buy Now、无真实支付。

## EV-10

- AC: `AC-09, AC-11`
- Meta: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-10.meta.json`
- Stdout: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-10.stdout.log`
- Stderr: `docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/EV-10.stderr.log`

Full unittest（全量单测）=`675/675 PASS`，较 H-24 的 662 个基线增加本轮 13 个专项测试，existing suite（既有测试集）没有失败。

## Six-case capability result / 六案例结果

| Case | Observed | Reason | Verified | Repeat |
|---|---|---|---:|---|
| `V01_VALID_SIGNATURE` | `VALID` | `signed_instruction_signature_valid` | true | identical |
| `N01_TAMPERED_BODY` | `INVALID` | `signed_instruction_signature_mismatch` | false | identical |
| `N02_WRONG_SECRET` | `INVALID` | `signed_instruction_signature_mismatch` | false | identical |
| `N03_STALE_TIMESTAMP` | `INVALID` | `signed_instruction_timestamp_outside_window` | false | identical |
| `N04_MISSING_SIGNATURE_HEADER` | `MISSING_EVIDENCE` | `signed_instruction_signature_missing` | false | identical |
| `N05_MALFORMED_SIGNATURE_HEADER` | `INVALID` | `signed_instruction_signature_format_invalid` | false | identical |

此外 focused tests（专项测试）单独验证：`abs(observed-signed) == 300` 可接受，未来 `301s` 越界必须 INVALID；ACP parser 对 duplicate / extra / reordered / whitespace component 全部 fail-closed（失败即关闭）。

`VALID` 在本实现中只表示：给定 key 对精确 signed bytes 的 HMAC-SHA256 比较成功且时间在冻结窗口内。它不产生 `Payment ALLOW`、不把 P3 `BOUND` 升级为 `VERIFIED`，也不证明用户授权合理、商户法律身份、生产认证安全或监管合规。

## Impact comparison

- Measurement evidence: `EV-02 + EV-03 + docs/05_任务交接/P9_SIGNED_INSTRUCTION_VERIFICATION_FACT_ACP_WEBHOOK_V1/evidence/H25_SIGNED_INSTRUCTION_RESULT.json`
- Before: H-24 ACP 明确保留 `order_webhook_signature_not_verified`；冻结 signed-webhook executable semantic cases=`0/6`。
- After: ACP Webhook 成为真实 first consumer（首个消费者）；冻结 `6/6` semantic cases 全匹配，repeat=2 deterministic，5/5 negative cases fail-closed。
- Delta: targeted signed-webhook capability `0/6 → 6/6`；这是 H-25 冻结的局部能力信号，不等价于 GESR 增长。
- Guardrail result: Product Trace=`10/12`、GESR=`9/12`、callback=`12/12`、duplicate/forbidden side effect=`0/12`、unsafe allow=`0/5`、formal scenarios=`13/13`、full unittest=`675/675`；H-24 accepted result SHA-256 不变。
- Scope caveat: 仅本地离线 ACP HMAC consumer + 协议中立 verification fact；未验证 AP2 SD-JWT、P3 credential possession、PKI/wallet/OIDC、生产 merchant secret、live ACP endpoint、ACP conformance 或监管合规。是否继续 AP2 第二消费者由 Evaluator 基于边际价值另行裁决，Executor 不在本 REPORT 中作项目影响 verdict（裁决）。

## External requirement impact

```yaml
profile: PCAC-AGENTPAY
requirement_ids: [PCAC-06]
applicability: ADAPTER
maturity_before: M1
maturity_after: M3  # task target; requires Evaluator acceptance
```

Residual risks（残余风险）：

- no live ACP endpoint;
- no production merchant secret;
- no AP2 SD-JWT verification;
- no P3 credential possession verification;
- no production authentication / security certification;
- no regulatory compliance claim.

## Sensitive-data minimization / 敏感数据最小化

- Product fact 不含 raw secret、private key、raw body、raw signature、credential/token/cookie 或业务 decision。
- H25 result 只持久化 status/reason、signer/key reference、signed payload SHA-256 与 guardrail summary；结果审计已机械检查测试 secret、原始 body、raw `Merchant-Signature` 未落盘。
- runner 仅在本地进程内使用 synthetic test material（合成测试材料）生成/验证冻结样例；production material 使用计数全部为 0。

## Iteration ledger

| Iteration | Change stayed within frozen principal change? | Validation / measurement result | Material cost used | Progress signal | Stop/continue fact |
|---:|---|---|---|---|---|
| L1 | yes | 13/13 focused + source/architecture/result audit 通过；6/6 本地能力矩阵通过 | local CPU only；0 external call | principal change 可执行 | 进入正式 L2 |
| 1 | yes | frozen L2 `10/10 PASS` | local CPU only；0 API/network/quota | `0/6 → 6/6` 且 guardrails 未退化 | 已达到 evidence sufficiency，停止 Executor 迭代并提交复核 |

- Budget consumed / ceiling: `1 / 2` complete implementation→L2 cycles。
- Remaining bounded attempts: `1`，未使用，因为首轮 L2 已满足证据充分性。
- Parallel attempt waves used: `NOT_APPLICABLE`
- Peak parallelism observed: `NOT_APPLICABLE`
- Evidence sufficiency reached: `yes`
- Attempt ledger: `NOT_APPLICABLE`（无外部/高成本调用）
- Executor stop reason if blocked: `NOT_APPLICABLE`

## Deviations and unresolved items

- Contract deviation: `NONE`
- Checks not run and reason: `NONE`；冻结 VP-01..VP-10 全部运行且 exit=0。
- Known unresolved issue: H-25 不解决 AP2 SD-JWT 与 P3 Credential / Possession；这是明确 out-of-scope，不是本任务失败。
- Human or external dependency: `NONE` for H-25 local execution；后续若进入 live endpoint / production credential 需新授权。
- Out-of-scope finding: 既有项目基线仍显示 T05/T06 Product Trace 缺口，按当前项目地图继续 `WATCH（观察）`，本轮不处理。
- Authorization: commit=false, push=false, history_rewrite=false, api_call=false；均已遵守。

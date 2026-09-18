# Executor Report

Task ID: `F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1`
Executor status: SUBMITTED_FOR_REVIEW
Task kind: `capability_experiment`
Baseline HEAD: `0a9b74873e9aedbc3d1c2e4e37b24e9129bf20ef`
Implementation commit: `NONE`（未获得 commit 授权）
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`
Map revision: `2026-09-18-r47`
Active bottleneck: `B-06`
Hypothesis: `H-34`
Amendment: `A1 / protocol-field type boundary hardening`

## 1. 执行结论

H-34 已按冻结合同和 `EVALUATOR_AMENDMENT_A1.md` 完成。

本轮唯一主要变化保持不变：在既有 `adapt_ap2_snapshot` 之前增加 AP2 v0.2.0 protocol-boundary gate(协议边界门)，验证：

```text
1. exact AP2 v0.2.0 vct identity
2. checkout_jwt / checkout_hash 必须是非空 string
3. sha-256(checkout_jwt raw UTF-8) == checkout_hash
4. PaymentMandate.transaction_id 必须是非空 string
5. PaymentMandate.transaction_id == independently verified checkout_hash
```

合法对象才进入旧 Canonical mapping(规范化映射)。错误版本、篡改、缺失或字段类型非法都 fail closed(失败即关闭)，不得调用旧 adapter 生成 Canonical `IntentMandate / TransactionRequest`。

Evaluator-owned B01-B10：`10/10 PASS`。
新增 targeted unit tests(定向单测)：`13/13 PASS`。
最终正式 L2：`7/7 PASS`，mandatory failures=`0`。

## 2. A1 小修结果

Evaluator 在初版 B01-B07 后发现一个真实 fail-open(错误放行)：`checkout_jwt=123` 会被旧实现 `str(123)` 后参与 hash，只要配套 hash/transaction_id 一致就可能返回 `VALID`。

A1 只修当前三个冻结字段的 type boundary(类型边界)：

```text
checkout_mandate.checkout_jwt  -> must be non-empty str
checkout_mandate.checkout_hash -> must be non-empty str
payment_mandate.transaction_id -> must be non-empty str
```

新增稳定 reason code：

```text
ap2_checkout_evidence_type_invalid
ap2_payment_checkout_binding_type_invalid
```

A1 后结果：

| Case | 观察结果 |
|---|---|
| B08 `checkout_jwt=123` + 与 `"123"` 匹配的 hash | `INVALID / ap2_checkout_evidence_type_invalid` |
| B09 `checkout_hash=123` | `INVALID / ap2_checkout_evidence_type_invalid` |
| B10 `transaction_id=123` | `INVALID / ap2_payment_checkout_binding_type_invalid` |

三种类型失败都不调用 `adapt_ap2_snapshot`，不产生 Canonical 对象。

## Workspace snapshot / 工作区快照

- HEAD 仍为冻结 baseline `0a9b74873e9aedbc3d1c2e4e37b24e9129bf20ef`。
- `CURRENT.md` 处于 `EXECUTING / Executor`；authorization flags(授权位)未改变。
- Evaluator-owned 未提交工件（Bottleneck Map、F-stage route、F0 Review、F0R Contract/Validation Plan/checker/Amendment）保持其所有权边界，Executor 未把它们计入本轮产品改动。
- dependency install / network / API / Sandbox / testnet / wallet / real PII / real payment / production credential-key / commit / push / history rewrite：全部 `0`。

## Changed files / 改动文件

| File | Action | SHA-256 | 作用 |
|---|---|---|---|
| `src/agentic_payment_experiment/adapters/ap2_protocol_boundary.py` | new | `fae40678a356ecad4bd0cf5998476071499ab2c180c846f32ca75f3fb479d9ae` | exact vct + string type guard + checkout hash + payment→checkout binding |
| `src/agentic_payment_experiment/adapters/__init__.py` | modified | `beb7d4a890be6618e5a0ae88830c8d2ecaaf9b1bc67024634155e2014f10340f` | 只导出新 result / verified entry |
| `tests/test_ap2_protocol_boundary.py` | new | `084439ff194656ec149d2c1bfcbecb8ca6ef5f16ec8b0df7c6f41a24ca65aed7` | 13 个定向正负边界测试 |

Task-owned changes：本 `REPORT.md`、`evidence/*` 与 `CURRENT.md` 的 Executor 路由状态。

Source-scope audit(源码范围审计)确认产品变化只落在冻结 Allowed scope(允许范围)。

## 5. Protected Core invariance / 保护核心不变

`EV-01` 机械确认 11 个 protected files(保护文件)保持冻结 SHA-256，包括：

```text
models.py
validator.py
trusted_execution/payment_binding.py
trusted_execution/signed_instruction.py
trusted_execution/credential_possession.py
data_disclosure.py
lifecycle.py
authoritative_trace.py
payment_execution.py
adapters/ap2.py
adapters/ap2_signed_instruction.py
```

没有为了 AP2 修改 Canonical Core / Trust Core，也没有新增 AP2-specific Core branch(AP2 特判核心分支)。

## 6. Frozen boundary behavior / 冻结边界结果

Evaluator-owned B01-B10：

| Case | 结果 | Canonical objects |
|---|---|---|
| B01 valid | `VALID / ap2_v020_protocol_boundary_verified` | present, `ready=true` |
| B02 wrong open vct | `INVALID / ap2_open_payment_vct_invalid` | none |
| B03 wrong payment vct | `INVALID / ap2_payment_vct_invalid` | none |
| B04 wrong checkout vct | `INVALID / ap2_checkout_vct_invalid` | none |
| B05 tampered checkout JWT | `INVALID / ap2_checkout_hash_mismatch` | none |
| B06 payment transaction mismatch | `INVALID / ap2_payment_checkout_binding_mismatch` | none |
| B07 checkout hash missing | `MISSING_EVIDENCE / ap2_checkout_evidence_missing` | none |
| B08 checkout JWT non-string | `INVALID / ap2_checkout_evidence_type_invalid` | none |
| B09 checkout hash non-string | `INVALID / ap2_checkout_evidence_type_invalid` | none |
| B10 transaction id non-string | `INVALID / ap2_payment_checkout_binding_type_invalid` | none |

机械证据：`EV-02`。

## L2 Task Gate

- Validation plan: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/VALIDATION_PLAN.yaml
- Gate summary: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/L2-GATE.json
- Gate result: PASS

| VP | Result | 关键结果 |
|---|---|---|
| VP-01 | PASS | allowed scope + protected hashes 全部符合 |
| VP-02 | PASS | evaluator-owned B01-B10 `10/10 PASS` |
| VP-03 | PASS | new targeted tests `13/13 PASS` |
| VP-04 | PASS | existing AP2 focused regression `17/17 PASS` |
| VP-05 | PASS | project baseline `12/12`，repeat `3/3 identical` |
| VP-06 | PASS | S01-S13 `13/13`；PayBench `10/10`；AP2 minimal `2/2`；Attack Overlay `6/6` |
| VP-07 | PASS | full unittest `721/721 PASS` |

Mandatory failures：`0/7`。

## 8. Existing project guardrails

最终正式证据：

```text
evaluator-owned AP2 boundary           10/10 PASS
new targeted boundary tests            13/13 PASS
existing AP2 focused regression        17/17 PASS
S01-S13                                13/13 PASS
PayBench                               10/10 PASS
AP2 minimal flow                         2/2 PASS
Attack Overlay                           6/6 PASS
project matched                         12/12
GESR                                    12/12
Evidence completeness                   12/12
Product Trace                           12/12
callback match                          12/12
unsafe allow                             0/6
duplicate/forbidden effects              0/12
project repeat                           3/3 identical
full unittest                          721/721 PASS
```

F0 冻结基线 full unittest 为 `708/708`。本任务最终新增 13 个 boundary tests，因此当前为 `721/721`，既有测试零失败。

## 9. Acceptance-criterion evidence map

| AC | Executor result | Evidence |
|---|---|---|
| `AC-01` Exact AP2 object identity gate | PASS | `EV-02`, `EV-03` |
| `AC-02` Checkout hash independently verified | PASS | `EV-02`, `EV-03` |
| `AC-03` Payment bound to verified checkout | PASS | `EV-02`, `EV-03` |
| `AC-04` Canonical mapping downstream of gate | PASS | `EV-02`, `EV-03`, `EV-04` |
| `AC-05` Evaluator-owned counterexamples | PASS | `EV-02`：B01-B10 `10/10` |
| `AC-06` Core invariance | PASS | `EV-01` |
| `AC-07` Existing AP2/project guardrails | PASS | `EV-04`, `EV-05`, `EV-06`, `EV-07` |
| `AC-08` Honest scope attribution | PASS | `EV-06` + 本 REPORT |
| `AC-09` v2.2 evidence gate | PASS | `L2-GATE` + `EV-01..07` + 本 REPORT |
| `A1-01` Current three fields non-empty strings | PASS | `EV-02`, `EV-03` |
| `A1-02` B01-B10 matrix | PASS | `EV-02` |
| `A1-03` Scope unchanged | PASS | `EV-01` |
| `A1-04` Final gate | PASS | `L2-GATE` |

## EV-01 — Source scope / protected Core audit
- AC: AC-06, AC-09
- Meta: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-01.meta.json
- Stdout: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-01.stdout.log
- Stderr: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-01.stderr.log

## EV-02 — Evaluator-owned AP2 boundary cases
- AC: AC-01, AC-02, AC-03, AC-04, AC-05
- Meta: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-02.meta.json
- Stdout: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-02.stdout.log
- Stderr: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-02.stderr.log

## EV-03 — New focused unit tests
- AC: AC-01, AC-02, AC-03, AC-04
- Meta: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-03.meta.json
- Stdout: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-03.stdout.log
- Stderr: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-03.stderr.log

## EV-04 — Existing AP2 regression
- AC: AC-04, AC-07
- Meta: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-04.meta.json
- Stdout: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-04.stdout.log
- Stderr: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-04.stderr.log

## EV-05 — Project impact baseline
- AC: AC-07
- Meta: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-05.meta.json
- Stdout: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-05.stdout.log
- Stderr: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-05.stderr.log

## EV-06 — Formal experiment entrypoint
- AC: AC-07, AC-08
- Meta: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-06.meta.json
- Stdout: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-06.stdout.log
- Stderr: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-06.stderr.log

## EV-07 — Full unittest
- AC: AC-06, AC-07, AC-08, AC-09
- Meta: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-07.meta.json
- Stdout: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-07.stdout.log
- Stderr: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/EV-07.stderr.log

## Impact comparison

- Measurement evidence: EV-01..EV-07, F0R_PROJECT_BASELINE.json, L2-GATE.json
- Before: exact vct gate=ABSENT; checkout hash verification=ABSENT; payment→checkout binding=ABSENT; frozen boundary target=0/10; project baseline=12/12; full unittest=708/708.
- After: B01-B10=10/10 PASS; invalid/missing/type-invalid boundary fail closed; Canonical Core AP2-specific branches=0; project baseline=12/12 repeat 3/3; full unittest=721/721 PASS.
- Delta: bounded AP2 protocol-boundary cases moved from absent to 10/10 executable PASS while Canonical Core remained unchanged.
- Guardrail result: existing AP2=17/17; S01-S13=13/13; PayBench=10/10; AP2 minimal=2/2; Attack Overlay=6/6; project baseline=12/12; unsafe allow=0/6; duplicate/forbidden=0/12; full unittest=721/721.
- Scope caveat: this task does not verify issuer signatures, open payment.reference delegation, cnf/KB-SD-JWT, receipts, full JSON Schema conformance, SDK/Sandbox/provider interoperability, real credentials, real PII, wallets, or real payment.

Executor 不发出最终 `IMPROVED / NO_MEASURABLE_GAIN / REGRESSED` project-impact verdict(项目影响裁决)；由 Evaluator 独立 L3 后裁决。

## 12. External requirement impact

冻结映射：

```yaml
profile: PCAC-AGENTPAY
requirement_ids: [PCAC-06, PCAC-07, PCAC-09, PCAC-12]
applicability: ADAPTER
maturity_before: M2
maturity_after: M3  # task target; requires Evaluator acceptance
```

本任务只能声称 bounded engineering capability(有界工程能力)提升，不声称监管合规或 AP2 conformance(协议一致性认证)。

## 13. Explicit residual risks / 明确残余风险

本包仍没有验证或实现：

- checkout JWT issuer signature(发行者签名)；
- open `payment.reference` delegate chain(委托链)；
- `cnf` / KB-SD-JWT holder proof(持有证明)；
- CheckoutReceipt / PaymentReceipt；
- rejection-receipt governed reuse state(拒绝回执治理复用状态)；
- 完整 JSON Schema validator；
- AP2 SDK / ADK / Gemini / Vertex；
- 真实 Provider / Sandbox / testnet / wallet / production credential / real PII / real payment；
- AP2 conformance / regulatory compliance。

## Deviations and unresolved items / 偏差与未解决项

- Contract deviation: NONE。
- Frozen checks skipped: NONE。
- A1 修复保持原 principal change(唯一主要变化)，未修改 protected Core，未引入完整 schema validator / SDK / 网络。
- 尚未解决项仅为本合同明确排除的 issuer signature、delegation、cnf/KB-SD-JWT、Receipt、真实 Provider/Sandbox/wallet/payment。
- Authorization respected: commit=false, push=false, history_rewrite=false, api_call=false。

## 14. Iteration ledger

| Cycle | Principal change stayed frozen? | 关键证据 | 结果 |
|---:|---|---|---|
| 1 | yes | 初版 B01-B07 `7/7`、targeted `10/10`、L2 `7/7` | Evaluator 在正式提交前发现非字符串 fail-open，冻结 A1 |
| 2 | yes | A1 后 B01-B10 `10/10`、targeted `13/13`、final L2 `7/7` | evidence sufficiency reached(证据充分)，提交复核 |

Complete implementation→L2 budget consumed：`2/2`。
第三轮未授权，也不需要。
Contract deviation：`NONE`。
Frozen checks skipped：`NONE`。
Authorization respected：commit=false, push=false, history_rewrite=false, api_call=false。

## 15. Submission boundary

Executor 已到达 v2.2 submit(提交)点：

```text
CURRENT.md remains EXECUTING / Executor
REPORT status = SUBMITTED_FOR_REVIEW
final L2 = PASS 7/7
next owner = Evaluator
```

只有 Evaluator 可以 accept(接收)当前快照、路由到 `READY_FOR_REVIEW / Evaluator`、执行独立 L3、给出 Task verdict / Project impact verdict / Continuation decision，并决定是否进入后续 F1 official SDK executable slice(官方 SDK 可执行切片)。

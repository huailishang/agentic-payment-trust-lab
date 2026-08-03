# P4 Trust Source / Context / Policy 有界修复独立评估

Task ID: P4-TRUST-SOURCE-CONTEXT-POLICY-REPAIR-V1

Reviewed baseline HEAD: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6

## Pre-review checks

| Check | Result | Evidence |
|---|---|---|
| Contract is frozen | yes | `CONTRACT.md` 为 `CONTRACT_FROZEN` |
| Task ID and baseline match | yes | `CURRENT.md`、`CONTRACT.md`、`REPORT.md` 一致 |
| Live product diff is within scope | yes | RV-EV-08A、RV-EV-08B；仅 7 个获准产品/测试文件 |
| Authorization flags were respected | yes | HEAD 未变化；无 commit、push、历史改写或外部 API |
| Executor evidence is intact | yes | v2 validator 校验全部 EV 三件套路径、字节数和 SHA-256 为 OK |
| Prior evaluator artifacts are intact | yes | RV-EV-09 对 51 个受保护文件重新计算大小和 SHA-256，全部 MATCH |

## RV-EV-01

- AC: AC-01, AC-02
- Meta: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-01.stderr.log
- Observed result: 10 个 context-policy 专项测试通过；未解析 `value_ref` 已 fail-closed。

## RV-EV-02

- AC: AC-03
- Meta: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-02.stderr.log
- Observed result: 13 个 payment-binding/gate 测试通过。

## RV-EV-03

- AC: AC-01, AC-02, AC-03, AC-04
- Meta: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-03.stderr.log
- Observed result: 26 个 P4 修复与 runner 专项测试通过。

## RV-EV-04

- AC: AC-03, AC-04
- Meta: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-04.stderr.log
- Observed result: 58 个 P1—P3、生命周期、恢复、确认和支付门禁安全测试通过。

## RV-EV-05

- AC: AC-04
- Meta: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-05.meta.json
- Stdout: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-05.stdout.log
- Stderr: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-05.stderr.log
- Observed result: 231 项完整回归，exit 0，OK。

## RV-EV-06

- AC: AC-04
- Meta: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-06.meta.json
- Stdout: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-06.stdout.log
- Stderr: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-06.stderr.log
- Observed result: S01—S13 13/13；内部基线 PASS；Attack Overlay 6/6。

## RV-EV-07

- AC: AC-02, AC-03
- Meta: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-07.meta.json
- Stdout: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-07.stdout.log
- Stderr: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-07.stderr.log
- Observed result: 独立反例证明 `request.amount`、`request.payee`、`request.currency` 均无来源覆盖时，P4 fact 仍为 `VALID`，门禁返回 `ALLOW` 并执行 callback 一次。

复现脚本：

`docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-07_counterexample_missing_value_sources.py`

## RV-EV-08A

- AC: AC-04
- Meta: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-08A.meta.json
- Stdout: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-08A.stdout.log
- Stderr: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-08A.stderr.log
- Observed result: `git diff --check` exit 0；仅有行尾转换 warning。

## RV-EV-08B

- AC: AC-04
- Meta: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-08B.meta.json
- Stdout: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-08B.stdout.log
- Stderr: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-08B.stderr.log
- Observed result: 工作树包含冻结时评估者产物、本任务允许的 7 个产品/测试文件、交接产物和独立复核证据；未发现越界产品文件。

## RV-EV-09

- AC: AC-04
- Meta: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-09.meta.json
- Stdout: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-09.stdout.log
- Stderr: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/RV-EV-09.stderr.log
- Observed result: 独立重新读取并校验 51 个原 P4 评估报告与 RV-EV 文件，大小和 SHA-256 全部匹配冻结清单。

## Acceptance matrix

| AC | Decision (`通过` / `不通过`) | Executor EV | Independent RV-EV | Specific basis |
|---|---|---|---|---|
| AC-01 | 通过 | EV-01 | RV-EV-01 | 未解析 `value_ref` 为 `MISSING_EVIDENCE`，blocked，不再写入 `None`。 |
| AC-02 | 不通过 | EV-01 | RV-EV-01, RV-EV-07 | coverage 模型本身可工作，但门禁必需集合只覆盖四个标识字段；金额、收款方和币种没有来源事实仍被视为完整。 |
| AC-03 | 不通过 | EV-02, EV-03 | RV-EV-02, RV-EV-07 | 常规 empty/partial/cross-transaction 测试通过；但关键支付值来源缺失的 P4 fact 仍能执行 callback。 |
| AC-04 | 通过 | EV-04—EV-08 | RV-EV-04—RV-EV-06, RV-EV-08A, RV-EV-08B, RV-EV-09 | 回归、正式入口、范围、授权和受保护历史均符合契约。 |

## Findings

### Blocking

`PAYMENT_REQUIRED_SOURCE_PATHS` 仅要求：

```text
final_order.order_id
mandate.mandate_id
request.agent_id
request.request_id
```

这些路径能绑定对象身份，但不能证明交易关键值的来源。P2/P3 可以证明 amount/payee/currency 在 mandate、order、request、execution 之间保持一致，却不能证明这些值来自 `USER_CONFIRMED`、`MERCHANT_PROVIDED`、`PROTOCOL_VERIFIED` 或其他允许来源。

因此，当前实现把“值一致”误当成了“来源完整”。RV-EV-07 证明没有 `request.amount`、`request.payee`、`request.currency` 来源事实时，callback 仍会执行，违反：

- AC-02：关键事实来源覆盖必须显式且完整；
- AC-03：空或部分来源覆盖必须 callback=0；
- 修复任务单一目标：关键支付事实来源覆盖不完整必须 fail-closed。

最低修复边界：

- 明确定义支付控制点必须覆盖的授权、交易对象、支付请求和执行身份关键值，而不只覆盖对象 ID；
- 至少让 amount、payee、currency 的来源覆盖和当前值摘要参与 gate 校验；
- 如果采用完整对象摘要，仍须保留可审计的逐域/逐路径来源语义，不能用单一布尔值代替；
- 加入 RV-EV-07 等价回归，证明任一关键值缺来源时 `INDETERMINATE`、callback=0；
- 保持 P2/P3 原有连续绑定和身份核验，不用 P4 替代或放宽它们。

### Non-blocking

- 当前 `value_ref` 修复、跨交易摘要绑定、固定 action/version、范围控制和受保护证据完整性均实现正确，可在后续修复中保留。
- Git 的 LF/CRLF warning 不构成空白错误。

## Final verdict

REJECTED

- Failed AC: AC-02, AC-03
- Specific fact: 关键支付值没有来源覆盖时仍为 `VALID/ALLOW` 并执行 callback。
- Minimum repair task: 补齐关键支付值来源覆盖并加入缺任一路径即 fail-closed 的 callback-counter 回归。
- Required rerun: RV-EV-01—RV-EV-09，重点重跑 RV-EV-07 等价反例。
- Missing human fact or authorization: None.

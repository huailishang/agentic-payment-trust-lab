# P4 支付关键值来源覆盖最小修复契约

```text
Task ID: P4-TRUST-SOURCE-CONTEXT-PAYMENT-VALUE-COVERAGE-REPAIR-V1
Task name: 补齐 amount、payee、currency 的 P4 来源覆盖与 callback 门禁
Risk: L1
Contract state: CONTRACT_FROZEN
Freezing role: Evaluator
Branch: main
Baseline HEAD: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
```

## Pre-existing changes

本任务基于上一份被拒绝的修复工作树继续，而不是干净 HEAD。其已存在的七个产品/测试差异、两份已拒绝任务的 REPORT/REVIEW/EV/RV-EV、以及 `CURRENT.md` 均为冻结时既有产物。

- 精确工作树：`evidence/FREEZE-EV-02.*`
- 既有产品 diff：`evidence/FREEZE-EV-03.*`
- 基线回归：231 tests / OK，见 `evidence/FREEZE-EV-01.*`

执行者不得覆盖或删除既有交接产物。仅可在 Allowed scope 内继续修改产品代码和测试，并在报告中把新增差异与 `FREEZE-EV-03` 的既有差异分开记录。

## Single objective

让支付 callback 的 P4 fact 同时覆盖身份关联和当前交易的 `request.amount`、`request.payee`、`request.currency`；任一关键值缺来源、来源不允许、值摘要不匹配或跨交易复用时，必须 `INDETERMINATE` 且 callback 为 0。

## Acceptance criteria

### AC-01：关键支付值必须进入必需来源覆盖集合

- Type: deterministic source coverage
- Given: 当前支付对象及 P4 `SourceCoverage`
- When: 构造并核验支付门禁所需的 P4 fact
- Must observe:
  - `PAYMENT_REQUIRED_SOURCE_PATHS` 保留既有四个关联路径，并明确包含 `request.amount`、`request.payee`、`request.currency`；
  - 三个新增路径各自具有封闭 `SourceType`、当前值的规范化摘要和可审计路径；
  - 当前支付请求中 amount/payee/currency 的覆盖来源为 `USER_CONFIRMED`；
  - 结果、runner 和最小 UI 可见 required/covered/missing paths。
- Must not observe:
  - 用 order ID、request ID 或 P2/P3 绑定结果代替这三个字段的来源覆盖；
  - 用单一布尔值或集合大小表示覆盖完整。
- Evidence required: EV-01 focused source-coverage tests
- Mandatory: yes

### AC-02：任一关键值缺覆盖或不匹配必须 fail-closed

- Type: payment callback gate
- Given: 上游 ALLOW、P2 VALID、P3 VALID 且至少 BOUND、可计数 callback，以及完整或缺失/篡改的 P4 fact
- When: 调用 `execute_with_payment_binding_gate`
- Must observe:
  - 分别缺少 amount、payee、currency 中任一路径时，decision=`INDETERMINATE`、callback=0；
  - 任一字段来源类型无效、来源不允许或摘要与当前 request 不一致时，decision=`INDETERMINATE`、callback=0；
  - 覆盖来自另一笔交易时，decision=`INDETERMINATE`、callback=0；
  - 七条必需路径均具有正确来源和当前摘要时，decision=`ALLOW`、callback 恰好为 1；
  - P1/P2/P3 更严格结果继续优先阻断。
- Must not observe:
  - `VALID → ALLOW` 在缺 request.amount、request.payee 或 request.currency 来源时发生；
  - callback 在 P4 检查之前发生。
- Evidence required: EV-02 callback-counter table-driven tests
- Mandatory: yes

### AC-03：P4 运行结果和回归兼容

- Type: result contract / regression
- Given: AC-01、AC-02 完成
- When: 运行专项、全量回归和正式入口
- Must observe:
  - runner 的 P4 case 显示至少七条完整 source coverage；
  - `python -m unittest discover -s tests -v` 为 OK；
  - `python run_experiment.py` 成功，S01—S13 13/13、内部基线 PASS、Attack Overlay 6/6；
  - 旧 P4 任务目录、冻结样本和 Attack Overlay 实现均保持不变；
  - 实现差异仅在 Allowed scope 内。
- Must not observe:
  - 外部策略/身份/来源认证服务、网络调用、真实支付或 P5 Replay；
  - 对无关 P1—P3 逻辑的重构。
- Evidence required: EV-03 focused runner + EV-04 full regression + EV-05 formal entrypoint + EV-06 scope/protected snapshot
- Mandatory: yes

## Allowed scope

May modify:

- `src/agentic_payment_experiment/payment_execution.py`
- `src/agentic_payment_experiment/runner.py`
- `src/agentic_payment_experiment/trusted_execution/context_policy.py`
- `src/agentic_payment_experiment/trusted_execution/__init__.py`
- `tests/trusted_execution/test_context_policy.py`
- `tests/trusted_execution/test_payment_binding.py`
- `tests/test_runner.py`

May add:

- 一个仅覆盖本任务的 `tests/trusted_execution/` 测试文件；
- `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_PAYMENT_VALUE_COVERAGE_REPAIR_V1/REPORT.md`；
- 本任务 `evidence/` 下的 EV 三件套、diff 与 SHA-256 快照。

## Exclusions and forbidden side effects

Must not modify:

- `CURRENT.md`，除 `CONTRACT_FROZEN → EXECUTING` 的 v2 路由切换外；
- `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_V1/` 与 `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/` 下的既有文件；
- `samples/regression/internal_baseline_v1.json`、Attack Overlay 样本或实现；
- 未列入 Allowed scope 的产品、测试和文档文件。

Must not implement or call:

- 外部 value resolver、策略引擎、来源认证、网络、真实支付、退款、重试、P5 Replay、receipt 或 hash chain；
- commit、push、历史改写或外部 API。

## Validation plan

| VP | Exact command | Expected result | AC |
|---|---|---|---|
| VP-01 | `$env:PYTHONUTF8='1'; python -m unittest tests.trusted_execution.test_context_policy -v` | 七路径 coverage 模型、来源类型和摘要测试通过 | AC-01 |
| VP-02 | `$env:PYTHONUTF8='1'; python -m unittest tests.trusted_execution.test_payment_binding -v` | amount/payee/currency 逐一缺失、篡改、跨交易均 callback=0；完整覆盖为 1 | AC-02 |
| VP-03 | `$env:PYTHONUTF8='1'; python -m unittest tests.trusted_execution.test_context_policy tests.trusted_execution.test_payment_binding tests.test_runner -v` | runner 显示至少七条 coverage，专项通过 | AC-01—AC-03 |
| VP-04 | `$env:PYTHONUTF8='1'; python -m unittest discover -s tests -v` | exit 0，OK | AC-03 |
| VP-05 | `$env:PYTHONUTF8='1'; python run_experiment.py` | S01—S13 13/13；内部基线 PASS；Attack Overlay 6/6 | AC-03 |
| VP-06 | 对照 FREEZE-EV-02/-03 保存最终 status、diff、SHA-256 和 protected file comparison；运行 `git diff --check` | 无越界修改、无空白错误、旧任务产物未变 | AC-03 |

每个 VP 必须通过 capture helper 生成 `EV-*.meta.json`、`EV-*.stdout.log`、`EV-*.stderr.log`。报告在 EXECUTING 内可原位修正，结构校验 OK 后才移交 Evaluator。

## Authorization

- commit: false
- push: false
- history_rewrite: false
- api_call: false

## Stop conditions

- 为满足 AC 需要修改原 P4 交接产物、冻结样本、Attack Overlay 或未授权文件；
- 对 amount/payee/currency 的权威来源类型存在会改变行为的歧义；
- 需要外部来源认证、网络、真实支付或任何 false 授权；
- 无法产生完整 E2 证据或区分冻结既有差异与本任务新增差异。

## Amendments

None.

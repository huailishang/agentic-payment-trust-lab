# P4 Trust Source / Context / Policy 有界修复任务契约

```text
Task ID: P4-TRUST-SOURCE-CONTEXT-POLICY-REPAIR-V1
Task name: 修复 value_ref 未解析写入与关键事实来源覆盖绕过
Risk: L1
Contract state: CONTRACT_FROZEN
Freezing role: Evaluator
Branch: main
Baseline HEAD: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
```

## Pre-existing changes

冻结时工作树不是干净状态，但不存在尚未记录的产品代码改动。既有修改均为评估者产物：

- `CURRENT.md`；
- `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_V1/EVALUATOR_REVIEW.md`；
- 上述 P4 任务目录中的 `RV-EV-*` 独立复核证据；
- 本修复任务的冻结证据。

精确快照见：

- `evidence/FREEZE-EV-02.meta.json`
- `evidence/FREEZE-EV-02.stdout.log`
- `evidence/FREEZE-EV-02.stderr.log`

执行者必须把这些路径视为评估者既有产物，不得修改、删除、覆盖或纳入产品实现变更。实现报告须区分冻结时既有文件与本任务新增变更。

冻结基线验证：

```text
Command: python -m unittest discover -s tests -v
Exit code: 0
Observed: Ran 226 tests; OK
Meta: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/FREEZE-EV-01.meta.json
Stdout: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/FREEZE-EV-01.stdout.log
Stderr: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/FREEZE-EV-01.stderr.log
```

## Single objective

在不扩大 P4 技术边界的前提下，使未解析 `value_ref` 和关键支付事实来源覆盖不完整的 P4 输入确定性 fail-closed，并保证支付 callback 只能消费与当前支付动作及必要来源覆盖一致的 `VALID` P4 fact。

## Acceptance criteria

### AC-01：未解析 value_ref 不得写入可信状态

- Type: domain model / deterministic merge
- Given: 候选更新包含非空 `value_ref` 和 `source_ref`，但没有已解析的实际 `value`
- When: 运行 `evaluate_context_policy`
- Must observe:
  - 结果为 `MISSING_EVIDENCE` 或等价 fail-closed 状态；
  - 目标路径出现在 blocked 证据中，不出现在 applied 证据中；
  - 原可信状态和返回可信状态中的目标值均保持不变；
  - reason code 明确指出引用未解析或候选值不可用。
- Must not observe:
  - 状态为 `VALID`；
  - 把 `None` 或其他占位值写入可信状态；
  - 静默忽略 `value_ref`。
- Evidence required: 新增回归测试 + EV-01 原始证据
- Mandatory: yes

本任务不引入外部引用解析器。若实现选择支持引用解析，只能使用显式注入、确定性、无网络的解析输入，并必须同时保留“无法解析即 fail-closed”路径。

### AC-02：关键事实来源覆盖必须显式且完整

- Type: context-policy fact completeness
- Given: 非空可信支付上下文、必需关键事实路径集合和每条路径的来源映射
- When: 生成 P4 context-policy fact
- Must observe:
  - 缺少任一必需路径的来源映射时为 `MISSING_EVIDENCE`；
  - 缺失路径以稳定顺序暴露在 fact 或 reason codes 中；
  - 来源类型必须属于封闭 `SourceType`，未知或无效来源不得算作覆盖；
  - 所有必需路径具有合法来源时，且无其他错误，才可为 `VALID`；
  - 空上下文或空覆盖不得充当非空支付控制点的完整 P4 fact。
- Must not observe:
  - 仅凭非空 `policy_version/current_action` 将零来源覆盖判为 `VALID`；
  - 用单一布尔值或未经核验的调用方声明替代可复核的路径覆盖事实。
- Evidence required: 表驱动 missing/partial/complete coverage 测试 + EV-02 原始证据
- Mandatory: yes

允许执行者采用 `required_source_paths`、显式 coverage 结构或等价的确定性封闭模型，但必须可序列化、可测试并保留缺失路径证据。

### AC-03：支付门禁必须消费当前动作的完整 P4 fact

- Type: payment callback gate
- Given: 上游 `ALLOW`、P2 `VALID`、P3 `VALID` 且至少 `BOUND`，以及不同完整性的 P4 fact 和可计数 callback
- When: 运行 `execute_with_payment_binding_gate`
- Must observe:
  - 空上下文、空来源覆盖或部分来源覆盖的 P4 fact 映射为 `INDETERMINATE`，callback 为 0；
  - `current_action` 与支付执行动作不一致时 fail-closed，callback 为 0；
  - 不支持或不匹配的 policy version fail-closed，callback 为 0；
  - 只有与当前支付控制点必要事实覆盖一致的 `VALID` P4 fact 才保持 `ALLOW`，callback 恰好为 1；
  - P4 结果继续暴露 coverage、missing paths、policy version、current action、applied/blocked paths。
- Must not observe:
  - 复用由空状态生成的 `VALID` fact 放行实际支付输入；
  - P4 覆盖 P1/P2/P3 的更严格结果；
  - callback 在 P4 检查前发生。
- Evidence required: callback-counter 正负路径测试 + EV-03 原始证据
- Mandatory: yes

执行者可以选择由门禁基于当前输入构造/核验 P4 fact，或让 fact 携带确定性 coverage/binding 信息；无论采用何种设计，独立反例必须无法放行。

### AC-04：兼容性、范围和边界

- Type: regression / scope
- Given: AC-01—AC-03 修复完成
- When: 运行专项测试、完整回归和正式入口
- Must observe:
  - P4 新增反例与既有 P1—P4 测试全部通过；
  - 完整 unittest 回归为 `OK`；
  - `python run_experiment.py` 成功，S01—S13 13/13，内部冻结基线 PASS，Attack Overlay 6/6；
  - 原 P4 评估报告和 `RV-EV-*` 证据保持逐字节不变；
  - 实现差异仅落在本契约允许范围。
- Must not observe:
  - 修改冻结回归样本；
  - 接入外部策略引擎、来源认证服务、网络调用、真实支付或 P5 Replay；
  - 为通过测试而弱化 P1—P3 fail-closed、安全阻断或禁止二次支付不变量。
- Evidence required: EV-04 专项回归 + EV-05 全量回归 + EV-06 正式入口 + EV-07 scope/snapshot
- Mandatory: yes

## Allowed scope

May modify:

- `src/agentic_payment_experiment/trusted_execution/context_policy.py`
- `src/agentic_payment_experiment/trusted_execution/__init__.py`
- `src/agentic_payment_experiment/payment_execution.py`
- `src/agentic_payment_experiment/runner.py`
- `tests/trusted_execution/test_context_policy.py`
- `tests/trusted_execution/test_payment_binding.py`
- `tests/test_runner.py`

May add:

- 一个位于 `tests/trusted_execution/` 下、仅覆盖本修复的聚焦测试文件；
- `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/REPORT.md`；
- `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_REPAIR_V1/evidence/` 下的执行者 `EV-*` 三件套、实现 diff 和文件哈希快照。

## Exclusions and forbidden side effects

Must not implement:

- 外部 value reference 解析服务、数据库或网络查询；
- Cedar、OPA、OpenFGA 或其他外部策略引擎；
- 来源认证、签名验证、真实身份认证；
- P5 Replay、receipt、hash chain；
- 真实支付、退款、重试或任何资金动作。

Must not modify:

- `CURRENT.md`，除非仅按 v2 路由规则把本任务从 `CONTRACT_FROZEN` 切到 `EXECUTING`；不得切换到评估者状态或最终状态；
- `docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_V1/` 下的任何既有文件；
- 本契约和 `FREEZE-EV-*`；
- `samples/regression/internal_baseline_v1.json`；
- Attack Overlay 样本和实现；
- P3 及更早任务产物；
- 其他未列入 Allowed scope 的产品、测试或文档文件。

Must not call or write externally:

- 不访问网络策略、身份或支付服务；
- 不使用真实凭证、个人身份信息或支付数据；
- 不 commit、不 push、不改写历史、不调用外部 API。

## Validation plan

所有命令工作目录均为仓库根目录：

`D:\SoftWare\VScode\install\Project\agentic-payment-trust-lab`

| VP | Exact command or steps | Expected result | AC |
|---|---|---|---|
| VP-01 | `$env:PYTHONUTF8='1'; python -m unittest tests.trusted_execution.test_context_policy -v` | value_ref 未解析路径 blocked/MISSING_EVIDENCE，原状态不变 | AC-01, AC-02 |
| VP-02 | `$env:PYTHONUTF8='1'; python -m unittest tests.trusted_execution.test_payment_binding -v` | 空/部分覆盖 callback=0，完整覆盖 callback=1 | AC-03 |
| VP-03 | `$env:PYTHONUTF8='1'; python -m unittest tests.trusted_execution.test_context_policy tests.trusted_execution.test_payment_binding tests.test_runner -v` | P4 修复与正式结果构造专项全部通过 | AC-01—AC-04 |
| VP-04 | `$env:PYTHONUTF8='1'; python -m unittest tests.test_validator tests.test_lifecycle tests.test_payment_recovery tests.trusted_execution.test_confirmation tests.trusted_execution.test_payment_binding -v` | P1—P3 和成熟支付安全不变量全部通过 | AC-03, AC-04 |
| VP-05 | `$env:PYTHONUTF8='1'; python -m unittest discover -s tests -v` | exit 0，最终 `OK` | AC-04 |
| VP-06 | `$env:PYTHONUTF8='1'; python run_experiment.py` | exit 0；S01—S13 13/13；内部基线 PASS；Attack Overlay 6/6 | AC-04 |
| VP-07 | 对照 `FREEZE-EV-02` 执行 `git status --short --untracked-files=all`，保存 `git diff`、diff SHA-256、变更文件 SHA-256；运行 `git diff --check` | 只有评估者既有产物、本任务交接产物和 Allowed scope 实现差异；无空白错误 | AC-04 |
| VP-08 | 重新计算原 P4 `EVALUATOR_REVIEW.md` 与 `RV-EV-*` 文件 SHA-256，并与执行前快照对比 | 原评估报告和证据未被修改或覆盖 | AC-04 |

每条执行命令必须使用 capture helper 保存独立的：

```text
EV-*.meta.json
EV-*.stdout.log
EV-*.stderr.log
```

执行者报告只引用文件路径，不粘贴长输出。报告必须记录 baseline HEAD、冻结时既有工作树、最终工作树、保存的实现 diff 及 SHA-256。

## Authorization

- commit: false
- push: false
- history_rewrite: false
- api_call: false

## Stop conditions

- 修复需要改变原 P4 目标、来源矩阵写权限或 P1—P3 语义，而不只是补齐 fail-closed；
- 对“当前支付控制点必要来源路径”存在两种会导致不同行为的合理解释；
- 修复需要修改未列入 Allowed scope 的产品文件、Attack Overlay 或冻结样本；
- 修复需要外部引用解析器、来源认证、网络或真实支付；
- 执行者无法区分冻结时评估者既有产物和本任务实现差异；
- 任一必需 AC 无法产生完整 E2 原始证据；
- 需要 commit、push、历史改写或外部 API。

## Amendments

None.

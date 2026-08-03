# P4 Trust Source / Context / Policy Input v1 独立评估报告

```yaml
workflow: evaluator-executor-workflow/v1
task_id: P4-TRUST-SOURCE-CONTEXT-POLICY-V1
round: 1
reviewed_baseline: 063dd539589d8e50258b9d2c6225ec45763a776c
reviewed_implementation_commit: 851dab1
reviewed_handoff_commit: 8acaa9e
evaluator_verdict: REJECTED
```

## 1. 结论

最终裁决：`REJECTED`。

执行者规定的 VP-01—VP-09、226 项全量回归和正式入口均能独立复现为成功，改动范围和边界声明也基本符合冻结契约。但独立构造的反例证明：

1. 只有 `value_ref`、没有实际 `value` 的候选更新会被标记为 `VALID` 和 applied，随后把可信状态写成 `None`；
2. 空可信上下文、零来源映射也会生成 `VALID` P4 fact，并允许支付 callback 执行。

这两项破坏了“关键事实带来源”“必要来源或策略证据缺失时 fail-closed”的任务目标，影响 AC-01、AC-03、AC-04。测试全绿不能覆盖这两个事实失败。

## 2. 交接和范围检查

- task ID、冻结基线、实现提交和报告任务一致。
- `851dab1` 相对冻结基线的文件范围落在 P4 契约允许的实现、测试、样本和文档范围内。
- `samples/regression/internal_baseline_v1.json` 未修改。
- 未观察到真实支付、网络调用、外部策略引擎或外部写入。
- 执行者报告语义上包含 VP、AC 映射、Command、Exit code、stdout/stderr 日志索引和 deviations。旧版校验器最初只识别 `EV-*` 与冒号字段，属于格式识别误判，不作为本次技术拒绝原因。

## 3. 独立复核证据

所有证据位于：

```text
docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_V1/evidence/
```

| Evidence | 独立命令或检查 | Exit code | 观察结果 |
|---|---|---:|---|
| RV-EV-01 | `python -m unittest tests.trusted_execution.test_context_policy -v` | 0 | 7 tests，OK |
| RV-EV-02 | `python -m unittest tests.trusted_execution.test_payment_binding -v` | 0 | 11 tests，OK |
| RV-EV-03 | `python -m unittest tests.test_attack_overlay tests.test_attack_overlay_entrypoint -v` | 0 | 6 tests，OK |
| RV-EV-04 | `python -m unittest tests.test_runner tests.test_lab_overview tests.test_presentation -v` | 0 | 39 tests，OK |
| RV-EV-05 | P1—P3、生命周期、恢复和支付门禁安全回归 | 0 | 56 tests，OK |
| RV-EV-06 | `python -m unittest discover -s tests -v` | 0 | 226 tests，OK |
| RV-EV-07 | `python run_experiment.py` | 0 | S01—S13 13/13；内部基线 PASS；Attack Overlay 6/6 |
| RV-EV-08 | 边界与夸大声明检索 | 0 | 命中均为限制、历史材料或测试文本 |
| RV-EV-09 | 冻结基线到实现提交的文件范围审计 | 0 | 未发现越过契约实现范围 |
| RV-EV-15 | 仓库内自包含的 `value_ref` 独立反例 | 0 | `VALID`、applied，但合并后的状态值为 `None` |
| RV-EV-16 | 仓库内自包含的空上下文 P4 fact 支付门禁反例 | 0 | 零来源映射仍为 `VALID`，decision=`ALLOW`，callback 执行一次 |

每个有效 `RV-EV-*` 均有 `.meta.json`、`.stdout.log` 和 `.stderr.log`，元数据记录 argv、工作目录、退出码、字节数和 SHA-256。

`RV-EV-10`、`RV-EV-11` 和 `RV-EV-13` 是评估者构造反例时产生的无效尝试，分别受 PowerShell 引号、模块路径或模块加载方式影响；这些失败日志予以保留，但不用于产品裁决。`RV-EV-12`、`RV-EV-14` 已成功复现同一问题，但命令引用仓库外临时脚本，现由仓库内自包含、可重放的 `RV-EV-15`、`RV-EV-16` 取代为裁决依据。

## 4. AC 裁决

| AC | 裁决 | 独立依据 |
|---|---|---|
| AC-01 | 不通过 | 枚举和数据模型齐备，RV-EV-01 通过；但 `value_ref` 被声明为候选载荷形式，实际未解析便应用 `None`，RV-EV-15 复现。 |
| AC-02 | 通过 | RV-EV-01 的矩阵、默认阻断和稳定聚合测试通过；代码使用显式封闭 `_ALLOWED_WRITES`。 |
| AC-03 | 不通过 | 深拷贝和污染检测测试通过，但 RV-EV-15 证明“允许更新”可以把未解析引用错误地写入可信状态。 |
| AC-04 | 不通过 | 常规正负门禁测试通过；RV-EV-16 证明没有任何关键事实来源覆盖也能产生 `VALID` P4 fact并执行 callback，不符合缺必要来源证据时 fail-closed。 |
| AC-05 | 通过 | RV-EV-03、RV-EV-07 证明 6 个 overlay 使用共同矩阵，包含阻断、允许和 benign 路径，未误报禁止副作用。 |
| AC-06 | 通过 | RV-EV-04、RV-EV-07 证明结果卡、Lab Overview 和最小 UI 契约展示 P4 技术结果与边界说明。 |
| AC-07 | 通过 | RV-EV-05—RV-EV-09 证明 226 项回归、正式入口、冻结基线、声明和实现范围满足要求。 |

## 5. 阻断缺陷

### B-01：未解析 `value_ref` 被当作可应用值

`context_policy.py` 在存在 `value_ref` 时不再判定候选值缺失，但应用阶段始终写入 `update.value`。当 `value=None`、`value_ref` 非空时，结果为 `VALID`，目标路径被列入 applied，可信值被写成 `None`。

最小修复要求：

- 明确定义 `value_ref` 的解析边界；
- 未提供可解析实际值时必须 `MISSING_EVIDENCE/BLOCKED`，不得写入 `None`；
- 增加 `value_ref` 正向解析或 fail-closed 反例测试。

### B-02：P4 fact 未证明关键事实来源覆盖

`evaluate_context_policy({}, updates=())` 会返回 `VALID`；支付门禁只检查 fact 的状态及非空 `policy_version/current_action`，没有证明该 fact 覆盖当前 mandate/order/request/executor 的关键事实。RV-EV-16 证明该空事实足以放行 callback。

最小修复要求：

- P4 结果显式记录并核验当前支付控制点要求的来源覆盖，或提供等价的确定性绑定；
- 缺少任一必需关键事实来源时返回 `MISSING_EVIDENCE`；
- 支付门禁拒绝与当前支付事实/动作不匹配或来源覆盖不完整的 P4 fact；
- 增加“空上下文”“缺部分关键来源”“完整来源覆盖”三类 callback-counter 测试。

## 6. 非阻断观察

- `git diff --check` 命中执行记录 Markdown 的两处行尾空格；这是排版问题，不影响本次技术裁决，可原位修正。
- 当前测试证明已有示例行为，但缺少上述两条对抗性反例，因此不能以 226 tests / OK 代替核心信任边界验证。

## 7. 最终裁决

```text
REJECTED
```

需要修改产品代码和测试，不能作为报告格式问题原位放行。修复应保持在 P4 现有技术边界内，不引入外部策略引擎、来源认证服务、网络调用、真实支付或 P5 Replay。

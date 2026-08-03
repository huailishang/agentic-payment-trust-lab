# P4 Trust Source / Context / Policy 有界修复执行者报告

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P4-TRUST-SOURCE-CONTEXT-POLICY-REPAIR-V1
executor_state: EXECUTING
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
implementation_commit: NONE
executor_verdict: NOT_ISSUED
requested_next_role: Evaluator
authorization_commit: false
authorization_push: false
```

## 1. 执行结果

两个冻结阻断项已在原 P4 技术边界内修复：

- 非空 `value_ref` 但没有实际 `value` 时返回 `MISSING_EVIDENCE`，目标路径进入 blocked，不进入 applied，可信状态不变；
- P4 fact 显式携带 required、covered、missing source paths 和逐路径 `SourceCoverage`；
- 来源覆盖要求封闭 `SourceType`、合法 source × fact-domain 组合以及可信上下文中真实存在的值；
- `SourceCoverage` 使用当前路径值的规范化摘要，防止拿另一笔交易的“完整覆盖”事实复用；
- 支付门禁只接受固定 `context-source-matrix-v1`、`execute_payment` 动作、完整必要路径及与当前 mandate/order/request 一致的覆盖摘要。

没有引入外部引用解析器、策略引擎、来源认证、网络调用、真实支付或 P5 Replay。

## 2. AC → Evidence

| AC | 观察结果 | Evidence |
|---|---|---|
| AC-01 | 未解析 `value_ref` 为 MISSING_EVIDENCE；blocked；原值不变 | `evidence/EV-01.*` |
| AC-02 | empty/partial/unknown/untrusted coverage 均缺证据；complete coverage 才 VALID；缺失路径稳定排序 | `evidence/EV-01.*` |
| AC-03 | 空、部分、动作错误、版本错误、其他交易 coverage 均 callback=0；当前交易完整 coverage callback=1 | `evidence/EV-02.*`、`evidence/EV-03.*` |
| AC-04 | 安全专项、231 项全量回归、正式入口、范围及受保护文件哈希全部符合合同 | `evidence/EV-04.*`—`evidence/EV-08.*` |

## 3. 验证摘要

所有命令工作目录：

```text
<REPO_ROOT>
```

| Evidence | Command | Exit | Observation |
|---|---|---:|---|
| EV-01 | `python -m unittest tests.trusted_execution.test_context_policy -v` | 0 | 10 tests；OK |
| EV-02 | `python -m unittest tests.trusted_execution.test_payment_binding -v` | 0 | 13 tests；OK |
| EV-03 | `python -m unittest tests.trusted_execution.test_context_policy tests.trusted_execution.test_payment_binding tests.test_runner -v` | 0 | 26 tests；OK |
| EV-04 | P1—P3、生命周期、恢复、确认和付款门禁安全回归 | 0 | 58 tests；OK |
| EV-05 | `python -m unittest discover -s tests -v` | 0 | 231 tests；OK |
| EV-06 | `python run_experiment.py` | 0 | S01—S13 13/13；内部基线 PASS；Attack Overlay 6/6 |
| EV-07A | `git status --short --untracked-files=all` | 0 | 冻结既有产物、本修复允许文件、修复报告和证据 |
| EV-07B | `git diff --check` | 0 | 无空白错误；stderr 仅为 Git 行尾转换 warning |
| EV-08 | 读取 protected hash comparison | 0 | 原 P4 评估报告和 RV-EV 文件 byte-identical |

每条命令均有独立：

```text
EV-*.meta.json
EV-*.stdout.log
EV-*.stderr.log
```

## 4. 修复模型

付款控制点必要来源路径固定为：

```text
final_order.order_id
mandate.mandate_id
request.agent_id
request.request_id
```

它们分别覆盖订单、授权、执行 Agent 和付款请求。P2/P3 仍负责更完整的连续支付绑定和 executor identity；P4 不替代或放宽这些更严格事实。

每条覆盖记录包含：

```text
target_path
source_type
canonical value_digest
```

门禁重新从当前支付对象计算期望摘要并与 P4 fact 精确比较，因此另一个 mandate/order/request 的合法 P4 fact 不能复用。

## 5. 工作树与范围

冻结时既有未提交文件：

- `CURRENT.md`；
- 原 P4 `EVALUATOR_REVIEW.md`；
- 原 P4 `RV-EV-*`；
- 本修复合同与 `FREEZE-EV-*`。

本任务产品和测试变化仅位于：

- `src/agentic_payment_experiment/trusted_execution/context_policy.py`
- `src/agentic_payment_experiment/trusted_execution/__init__.py`
- `src/agentic_payment_experiment/payment_execution.py`
- `src/agentic_payment_experiment/runner.py`
- `tests/trusted_execution/test_context_policy.py`
- `tests/trusted_execution/test_payment_binding.py`
- `tests/test_runner.py`

`CURRENT.md` 仅按合同从 `CONTRACT_FROZEN` 切换为 `EXECUTING`。实现差异及 SHA-256：

```text
evidence/implementation.diff
SHA-256: 120325dea62f3e894bd533cedbb91da729f0317f8505c6661034474fda267d20
```

文件快照：

```text
evidence/changed-files.sha256
evidence/protected-files.before.sha256
evidence/protected-files.after.sha256
evidence/protected-files.comparison.txt
```

原 P4 `EVALUATOR_REVIEW.md` 与全部 `RV-EV-*` 在前后快照中逐字节一致。

## 6. Deviations and unresolved items

- 无实现偏离，无未解决测试失败。
- 没有修改 Attack Overlay、冻结回归样本、原 P4 报告或评估证据。
- `implementation_commit` 为 `NONE`：合同明确禁止 commit/push。
- 本报告保持 `EXECUTING / NOT_ISSUED`；执行者未签发 PASS、REJECTED 或 HUMAN_REQUIRED。

## 7. 评估者复核重点

1. `value_ref` 独立反例是否已稳定 fail-closed 且不写入占位值。
2. empty/partial/invalid coverage 是否都无法执行 callback。
3. `SourceCoverage.value_digest` 是否阻止跨交易复用完整 P4 fact。
4. P4 来源覆盖是否没有替代或放宽 P1—P3。
5. 原评估产物、Attack Overlay 和冻结样本是否保持不变。

完成工作流校验后，请由 Evaluator 接管并决定是否切换为 `READY_FOR_REVIEW`；执行者不修改最终状态。

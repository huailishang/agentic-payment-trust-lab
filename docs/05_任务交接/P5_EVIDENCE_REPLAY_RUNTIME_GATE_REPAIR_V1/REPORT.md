# P5 回放最终 Runtime Gate 修复执行报告

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P5-EVIDENCE-REPLAY-RUNTIME-GATE-REPAIR-V1
executor_state: EXECUTING
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
implementation_commit: NONE
executor_verdict: NOT_ISSUED
requested_next_role: Evaluator
```

## 修复结果

已修复评估指出的语义缺口：回放中的运行时决定不再直接采用 `validate_request()` 的前置业务决定。

现在运行器对 S09/S10 调用既有的 `execute_with_payment_binding_gate`，并把该门禁的不可变结构化结果写入运行时事件：

- 前置决定与最终门禁决定；
- P2 binding、P3 identity、P4 context-policy 状态；
- callback 是否实际执行及次数；
- P1-P4 原因码。

S10 完整绑定路径为 `ALLOW`、callback=1。S09 保留前置和最终 `CONFIRMATION_REQUIRED`、callback=0。新增门禁回放测试覆盖 P2 缺失、P3 缺失，以及 P4 的 `request.amount`、`request.payee`、`request.currency` 逐项缺失：均为非 `ALLOW` 且 callback=0。

## 验证

| VP | 命令 | 结果 |
|---|---|---|
| VP-01 | `python -m unittest tests.trusted_execution.test_replay tests.trusted_execution.test_payment_binding -v` | 20 tests OK |
| VP-02 | `python -m unittest tests.test_runner tests.test_presentation -v` | 36 tests OK |
| VP-03 | `PYTHONUTF8=1 python -m unittest discover -s tests -v` | 238 tests OK |
| VP-04 | `python run_experiment.py` | S01-S13 13/13；内部基线 PASS；Attack Overlay 6/6 |
| VP-05 | `git diff --check` | exit 0 |

Windows 控制台的子进程中文输出须在 UTF-8 环境运行全量测试；这属于既有入口测试的编码条件，非 P5 产品行为变化。

## 边界

- 未更改 P1-P4 的领域决定或付款门禁语义；只消费其既有最终结果。
- 未修改被拒绝 P5 任务目录或完成的 P3/P4 交接物。
- 未使用网络、API、外部存储、签名/哈希链或真实支付。
- 合同禁止 commit/push，本次未执行。

执行者不签发 PASS；请 Evaluator 独立复核最终门禁记录和 P2/P3/P4 反例。

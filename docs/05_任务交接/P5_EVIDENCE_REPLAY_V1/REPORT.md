# P5 最小证据回放链执行报告

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P5-EVIDENCE-REPLAY-V1
executor_state: EXECUTING
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
implementation_commit: NONE
executor_verdict: NOT_ISSUED
requested_next_role: Evaluator
```

## 执行结果

已实现离线、确定性的 P5 回放收据链。每个事件显式记录身份、授权、请求/交易、支付引用、来源、运行时决定、原因码和前序事件引用；它不读取 HTML 或结果卡片文本，也不使用签名、哈希链、网络、外部存储或真实支付。

- `S10` 产生完整的 `ALLOW` 链，并记录固定离线支付观察结果。
- `S09` 产生完整的 `CONFIRMATION_REQUIRED` 链；支付结果明确记录为本地运行时的 `payment_not_attempted`，不虚构真实支付。
- 重复事件 ID、断裂前序引用、跨事件引用不一致及缺失必需事件均不能产生放行结论。

## 验证

| 验证项 | 命令 | 结果 |
|---|---|---|
| VP-01 | `python -m unittest tests.trusted_execution.test_replay -v` | 5 tests OK |
| VP-02 | `python -m unittest tests.test_runner tests.test_presentation -v` | 36 tests OK |
| VP-03 | `PYTHONUTF8=1 python -m unittest discover -s tests -v` | 237 tests OK |
| VP-04 | `python run_experiment.py` | S01-S13 13/13；内部基线 PASS；Attack Overlay 6/6 |
| VP-05 | `git diff --check` | exit 0 |

说明：未设置 `PYTHONUTF8=1` 时，`test_entrypoint` 的三个断言会因 Windows 子进程中文输出被错误解码而失败；同一入口在 UTF-8 环境下通过。P5 未修改入口程序或编码行为。

## AC 对照

- AC-01：`ReplayEvent` 为封闭枚举和可序列化记录；构造时拒绝缺失引用及未知事件、来源或决定值。
- AC-02：`replay_events` 使用结构化事件验证顺序、前序引用、唯一 ID、全链引用一致性和必需事件；返回 `VALID`、`INDETERMINATE` 或 `INVALID`。
- AC-03：运行器从 S09/S10 的领域对象与验证结果构建 `card["replay"]`；测试确认同时存在 allow 与 non-allow 回放结果。
- AC-04：未接入网络、外部服务、持久化、加密完整性声明、真实支付、P6 或 UI 重构。

## P5 变更文件

- `src/agentic_payment_experiment/trusted_execution/replay.py`
- `src/agentic_payment_experiment/trusted_execution/__init__.py`
- `src/agentic_payment_experiment/runner.py`
- `tests/trusted_execution/test_replay.py`
- `tests/test_runner.py`

`result_card.py` 未修改：P5 结果由 runner 顶层结构化字段暴露，HTML 只消费现有结果卡片 JSON，未成为回放来源。

## 边界与交接

- P1-P4 现有业务决策、支付回调门禁和交接物未修改；工作区里已存在的 P4 未提交差异是本任务前的基线，不归入 P5。
- 合同禁止 commit 和 push，本次未执行二者。
- 执行者不签发 PASS。请 Evaluator 独立复核 P5 范围、链断裂反例及运行器中的 S09/S10 结构化结果后决定后续状态。

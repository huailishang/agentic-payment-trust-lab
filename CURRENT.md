# Evaluator → Executor Current State

<!-- evaluator-executor-workflow:v1 -->

```yaml
workflow: evaluator-executor-workflow/v1
task_id: P4-TRUST-SOURCE-CONTEXT-POLICY-V1
round: 1
state: CONTRACT_FROZEN
current_role: Executor
baseline_commit: 063dd539589d8e50258b9d2c6225ec45763a776c
contract_path: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_V1/TASK_CONTRACT.md
executor_report_path: NONE
evaluator_review_path: NONE
round_dispatch_path: NONE
prior_executor_report_path: NONE
prior_evaluator_review_path: NONE
next_artifact_path: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_V1/EXECUTOR_REPORT.md
```

## Current action

```text
Read:
- docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_V1/TASK_CONTRACT.md
- docs/03_架构设计/Agent_Trust_Control_Plane_最小领域模型_v1.md
- docs/02_未来规划/整体修正执行计划_20260729.md

Do:
- 仅按冻结契约实现 P4 Trust Source / Context / Policy Input v1。
- 为每个 AC-* 保存完整、可复现的 EV-* 原始证据。
- 创建 next_artifact_path 指定的执行者报告，状态只能是 READY_FOR_REVIEW、PARTIAL 或 BLOCKED。

Do not:
- 不修改 CURRENT.md、冻结契约或 P3 历史交接产物。
- 不接入外部策略/身份服务，不实现 P5 Replay，不执行真实支付。
- 不签发 PASS、REJECTED、HUMAN_REQUIRED 或 REWORK。
```

## Handoff rule

创建 `next_artifact_path` 指定的执行者报告后停止。由评估者验证 task_id、基线、实现提交和证据路径后接管评审。

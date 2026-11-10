# Evaluator ↔ Executor Current State

<!-- evaluator-executor-workflow:v2.2 -->

```yaml
workflow: evaluator-executor-workflow/v2.2
task_id: H67_ACP_MCP_IDEMPOTENCY_CONTRACT_MEASUREMENT_V1
task_kind: one_off
state: CONTRACT_FROZEN
current_role: Executor
baseline_commit: 23f1505de1991c608aec2644a327b71abd7e76f5
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-11-10-r109
active_bottleneck_id: B-20
hypothesis_id: H-67
contract_path: docs/05_任务交接/H67_ACP_MCP_IDEMPOTENCY_CONTRACT_MEASUREMENT_V1/CONTRACT.md
executor_report_path: docs/05_任务交接/H67_ACP_MCP_IDEMPOTENCY_CONTRACT_MEASUREMENT_V1/REPORT.md
evaluator_review_path: docs/05_任务交接/H67_ACP_MCP_IDEMPOTENCY_CONTRACT_MEASUREMENT_V1/REVIEW.md
next_artifact_path: docs/05_任务交接/H67_ACP_MCP_IDEMPOTENCY_CONTRACT_MEASUREMENT_V1/REPORT.md
execution_phase: H67_FROZEN_NOT_EXECUTED
authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
```

## Global position / 全局位置

目标是高风险交易信任链可独立复核。r109：A–D本地阶段关闭、E受控本地代表闭合、F当前。H66研究PASS但未建立金融消费者，IronClaw接入停止在参考；第一测量方向B-20为ACP REST到MCP绑定的幂等键必填契约。H65R拒收、CartTrace六例停止、H62关闭、B-06后置均保持。

## Current action / 当前动作

唯一入口：docs/05_任务交接/H67_ACP_MCP_IDEMPOTENCY_CONTRACT_MEASUREMENT_V1/EXECUTOR_START.md。只读SOURCE_BUNDLE的固定5工具元数据；构造10个仅增删幂等键的成对探针，另清点5个官方示例meta。不启动RPC/MCP/HTTP或产品服务。

远端可用标准Python运行CHECK.py package/source；输入及许可证均随包公开，不需要旧原始缓存或网络。H67不继承H66公开GET权限，缺冻结输入即INPUT_LIMIT，不换版本。历史严格门禁只在原快照复现。

预算init后45分钟墙钟/最多2分析尝试/2L2，失败事前预留并保留。网络/安装/上游运行/模型服务/产品/钱包/签名/付款0。source通过、init后改EXECUTING；L2提交保持Executor，由Evaluator独立L3。只判定元数据契约，不声称完整请求可执行、服务端会漏防护或实际重复扣款。

## Publication authorization / 本次发布授权

Human已明确要求统一推送到远程并保证本地与远程一致。仅Evaluator本轮可按中央安全Hook提交推送可公开控制文件；上述四项false继续约束下一Executor。原始日志/数据/依赖/敏感测试向量保留本地，远端只读不能被写成完整执行环境。同步说明见REMOTE_HANDOFF.md。

## Historical preservation / 历史保护

H64/H64R/H65/H65R/H66原测量、预算、失败及L2/L3不回写；H66终态路由与接受快照保留，H65R不追认为PASS。r108逐字节归档；历史复现使用原快照，不在新路由下重跑旧全工作区checker。

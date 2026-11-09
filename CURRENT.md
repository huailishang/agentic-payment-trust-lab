# Evaluator ↔ Executor Current State

<!-- evaluator-executor-workflow:v2.2 -->

```yaml
workflow: evaluator-executor-workflow/v2.2
task_id: H65_SOURCE_UNIT_CONSENT_BINDING_MEASUREMENT_V1
task_kind: one_off
state: CONTRACT_FROZEN
current_role: Executor
baseline_commit: 211151e6c3ae53997b5a2da419c27db497d7eb48
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-11-09-r106
active_bottleneck_id: B-18
hypothesis_id: H-65
contract_path: docs/05_任务交接/H65_SOURCE_UNIT_CONSENT_BINDING_MEASUREMENT_V1/CONTRACT.md
executor_report_path: docs/05_任务交接/H65_SOURCE_UNIT_CONSENT_BINDING_MEASUREMENT_V1/REPORT.md
evaluator_review_path: docs/05_任务交接/H65_SOURCE_UNIT_CONSENT_BINDING_MEASUREMENT_V1/REVIEW.md
next_artifact_path: docs/05_任务交接/H65_SOURCE_UNIT_CONSENT_BINDING_MEASUREMENT_V1/REPORT.md
execution_phase: H65_FROZEN_NOT_EXECUTED
authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
```

## Global position / 全局位置

目标是高风险交易信任链可独立复核。r106：A–D本地阶段关闭、E受控本地代表闭合、F当前。B-18仍缺独立外部判定/控制效果；H64R已独立L3四VP及六源语义签收PASS，原混拼调用/漏金额测量缺陷已修复。产品成熟度不因此提高，H62不重开，真实支付B-06仍受授权约束。

## Current action / 当前动作

下一任务只做现有材料的单位/用户确认到checkout绑定可证性测量。入口：docs/05_任务交接/H65_SOURCE_UNIT_CONSENT_BINDING_MEASUREMENT_V1/EXECUTOR_START.md。合同、计划、公开输入摘要和检查器随仓库正常提交发布；不再要求执行者寻找被忽略目录中的入口。

远端可运行CHECK.py package验证公开任务文件；完整开工必须运行source验证原始本地输入。缺输入即INPUT_LIMIT，不授权新下载或改门禁。H65以精确输入/产品摘要保护基线，正常发布元数据的新提交不改变这些输入；H64R旧严格HEAD门禁保持，只在其历史快照复现。

预算75主动分钟/12次源读取/1分析版/2L2，网络/安装/模型/产品/回放/付款0。source通过后Executor才改EXECUTING；L2提交保持EXECUTING/Executor，Evaluator另作独立L3和逐源审阅。无至少一例直接完整链则停止当前源视图；证据充分才另冻回放测量，不能自动运行。

## Publication authorization / 本次发布授权

Human已明确要求统一推送到远程并保证本地与远程一致。仅Evaluator本轮可按中央安全Hook提交推送可公开控制文件；上述四项false继续约束下一Executor。原始日志/数据/依赖/敏感测试向量保留本地，远端只读不能被写成完整执行环境。同步说明见REMOTE_HANDOFF.md。

## Historical preservation / 历史保护

H64/H64R提交、原始测量、预算、失败和L2/L3不回写；H64R接受快照位于其本地evidence。公开报告用PUBLIC_REPORT.md脱敏副本，原REPORT保持。r105逐字节归档；历史复现使用当时完整本地快照，不在新路由下重跑旧全工作区checker。

# H47 执行入口：外部商家适用性，整包后一次评估

先读根 CURRENT，确认 H47 / CONTRACT_FROZEN / Executor。再读 CONTRACT、VALIDATION_PLAN、CASE_SPEC、SOURCE_LOCK、TEAM_SOURCE_LOCK、ENVIRONMENT、BASELINE 与 EVALUATOR_ASSESSMENT。合同外保持原样，继承 dirty 改动不暂存、不回滚。

大白话目标：真正运行固定外部商家，核实原生保护 → 对齐我们已有授权/执行/证据对象 → 看三类公开交易团队是否有可问的具体问题 → 交一次完整判断。源码、隔离依赖和离线测试夹具均已准备；不用自己找环境或运行上游 quickstart。

## 串行完成

1. 按 VP-01 运行 baseline；通过后 CURRENT 仅切 EXECUTING/Executor，保留原授权 false。
2. 读完整来源和本项目类型/控制接口，写 SOURCE_AUDIT，不执行任何 sources 中的 shell/CLI/test main。
3. 在本目录实现 MEASUREMENT.py 的 `run_case(ctx, case) -> None`，按冻结 steps 调用 ctx.request；不得改变夹具/上游/确认/DB。用 VP-02 命令做有限 L1，计入调用账。
4. 写 NATIVE_BASELINE；九路径两次不是十八种攻击；合法签名数量更新、隐藏响应与模拟付款的边界写清。
5. 写 17 项 MAPPING 与执行接缝审计；没有字段就记录 ABSENT/UNVERIFIED，不为凑完整链路创建假订单或支付证明。给出最小候选适配边界和最强反对理由，不写产品适配器。
6. 用固定三个 README/许可证完成 TEAM_SCREENING；需求/预算未知不升格，不联系任何团队。
7. 写 DECISION、LIMITATIONS、REPORT 与 ATTEMPT_LEDGER。结论可以是无价值或语义缺口，不要求正向包装。
8. 跑完整 L2，保存原始五项 triplet 和每次 gate 目录；最后更新 REPORT 的 L2 证据索引并运行中央校验。三次正式 L2、12 小时、500 次本地请求上限内可修本包驱动/材料，整包一次提交。

```powershell
python ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H47_UCP_COMMERCE_APPLICABILITY_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H47_UCP_COMMERCE_APPLICABILITY_V1/evidence/l2_executor_01 --mode executor
python ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
```

后续正式尝试使用 l2_executor_02/03，不覆盖前次 gate；measurement_runs 自动另存每次原始观察。REPORT 写当前 Task ID、Baseline HEAD、Changed files 与 SHA-256、全部 EV 索引、实际预算、测量前后、未测项和停止原因。`SUBMITTED_FOR_REVIEW` 只在完整 L2 PASS 后使用；CURRENT 保持 EXECUTING/Executor，Evaluator 接受后才转 READY_FOR_REVIEW。

有效不支持/原生行为与预计不同不暂停阶段：保留观察、完成映射和团队分析、最终统一提交。需要改冻结夹具、依赖、产品、范围或权限才硬停止。Executor 不能签 PASS，不能自动恢复支付宝/比赛，不另发会话消息。

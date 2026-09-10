# Superseded Before Execution

Task: `P9-WEBSHOP-FULFILMENT-FAILED-AUTHORITATIVE-TRACE-PROFILE-V1`  
Hypothesis: `H-19`  
Status: `SUPERSEDED_BEFORE_EXECUTION`

该任务在 Executor（执行者）开始产品实现前被 Evaluator（评估者）撤下。

原因：H-18 已经把三个失败分支定位到同一个上层瓶颈——Lifecycle Evidence Continuity（生命周期证据连续性）。原 H-19 只修 J03 的 failed-fulfilment Trace Profile（失败履约轨迹配置档），粒度过细；如果随后再分别修 J02/J04 的 Action Origin（动作来源），会形成“一个断点一个小包”的微调链。

替代任务：`P9-WEBSHOP-LIFECYCLE-EVIDENCE-CONTINUITY-CLOSURE-V1` / `H-20`。

替代任务保持一个统一 principal change（主要变化）：补齐**现有生命周期扩展事件在 Evidence Registry（证据登记机制）中的覆盖**，同时只允许在两个现有 registry surface（登记面）上补声明式缺口：

- `SIDECAR_TRACE_PROFILES`：补 failed-fulfilment（失败履约）通用 profile；
- `_TRACE_ORIGIN_BY_EVENT_ROLE`：补 recovery / status-conflict（恢复 / 状态冲突）已有扩展事件的 origin mapping（来源映射）。

不修改 Payment / Recovery / Finality / Conflict / Lifecycle / Remediation（支付 / 恢复 / 终局性 / 冲突 / 生命周期 / 补救）业务判断，也不修改 Trace Toolkit（轨迹工具包）。

原 H-19 的 `CONTRACT.md` / `VALIDATION_PLAN.yaml` / evaluator checks（评估检查器）保留作审计记录，不再路由给 Executor。

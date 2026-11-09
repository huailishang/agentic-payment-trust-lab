# H49 执行者入口

本包已冻结，按 CURRENT 路由执行。先读根 AGENTS.md、公共 evaluator-executor-workflow v2.2、本目录 CONTRACT、NATIVE_FACTS、EXTERNAL_BASELINE 和 VALIDATION_PLAN。

大白话：H48 已经交付并通过独立复核。它说明我们的旧确认能力能接住真实商家数据，但仅检查自己的客户端，挡不住检查后的变更和直接调用。现在要确定“商家真正执行前该加什么最小约束、哪些写路径都得遵守、付款后失败怎么恢复”，并设计下一次样机如何验收。

本包交付工程可行性和边界合同建议，尚不实现服务端。原因是已有证据还不足以选定能覆盖全部相关写路径、处理模拟付款/数据库失败的改动形态；先写锁或通用网关会掩盖这些义务。已知窗口不重测、商城名单不扩充、通用认证审计不重建。串行完成 S0–S6，整包后只做一次独立评估。

## 先检查

```powershell
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H49_MERCHANT_ENFORCEMENT_FEASIBILITY_V1/EVALUATOR_CHECK.py baseline
```

环境不存在或保护漂移就保留报告停止，不重装或改 BASELINE。外网、商家运行、ASGI、模型、Provider、真实钱、支付宝、比赛、上传和对外联系预算均零。不运行本包 facts/FREEZE 准备命令。

## 连续完成

1. 审计 11 单元，写 SEAM_MAP.json（schema=h49-seam-map/v1，units[]）和 SOURCE_AUDIT.md；每条 operation 与 CONTRACT 一致，字段/引用结构见冻结检查器。别把“写订单”直接等同“发起付款”。
2. MECHANISM_COMPARISON.json（schema=h49-mechanisms/v1，mechanisms[]）比较三个固定机制；COMPARISON.md 说明选择与最强反对理由。ServiceNow 作为有边界的竞争/复用参照，不安装、不认定它做不到，也不认定它已解决订单绑定。
3. BOUNDARY_DESIGN.json/.md 定义最小输入、服务端执行位置、写协调、撤销、幂等、UNKNOWN、轨迹、回滚和缺口；schema 与必填字段按 CONTRACT；server_guard_implemented=false、race_closed=false。
4. VALIDATION_DESIGN.json（schema=h49-validation-design/v1，cases[]）及同名 .md 写完整14场景。它们是未来验收设计，executed=false。检查器自测不等于运行这些场景。
5. BUSINESS_CHECK.md 沿用 H47 一个具体工作流，写一个潜在付费问题、已有保护、所需轨迹/频率/排查工时/负责人/预算事实；未知如实 UNKNOWN，不联系。DECISION.json 用冻结的三个分类之一；所有能力/客户成绩标记 false。
6. ATTEMPT_LEDGER.json 记录 schema=h49-attempt-ledger/v1、formal_l2_attempts、active_work_minutes、asgi_requests/model_calls/provider_calls/external_runtime_calls=0、每次运行目录/失败原因/余额。最多6小时主动执行、正式 L2 2次，同失败无新依据停止。
7. 完整 L2、REPORT 与中央校验后停止，交 Evaluator。REPORT 首行当前 Task ID 和 Baseline HEAD，Executor status=SUBMITTED_FOR_REVIEW；必需有 Workspace snapshot、Changed files、Impact comparison、Before/After/Delta/Measurement evidence/Guardrail result/Scope caveat、L2 Task Gate、EV原始三件套索引、AC-01..05 映射、实际成本及 Deviations and unresolved items。不得签 PASS。

## 完整检查命令

```powershell
python ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H49_MERCHANT_ENFORCEMENT_FEASIBILITY_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H49_MERCHANT_ENFORCEMENT_FEASIBILITY_V1/evidence/l2_executor_01 --mode executor
python ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
```

正式每次使用新目录；前一失败原始证据不覆盖。开始时 CURRENT 可转 EXECUTING/Executor，提交时 phase=H49_SUBMITTED_FOR_REVIEW，仍为 Executor，下一产物 REPORT。不能改地图、历史、冻结合同或权限。

所有 JSON 详细字段可读 EVALUATOR_CHECK 校验函数，不复制检查器自测的占位内容当交付。结构通过后，设计是否真实可实施、原子性是否有依据和商业推论是否成立仍由人工 L3 判断。

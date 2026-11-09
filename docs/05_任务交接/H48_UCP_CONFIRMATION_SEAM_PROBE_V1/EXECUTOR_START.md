# H48 Executor 开始入口

先读根 AGENTS.md、CURRENT 和本目录 CONTRACT、TRUST_FIXTURE、VALIDATION_PLAN。使用公共 evaluator-executor-workflow v2.2，不改冻结文件和运行器。

大白话：原来我们已有“用户只确认一件商品，变成两件就需要重新确认”的能力。这次只把外部商家返回的真实交易内容接进这项旧能力，同时展示“只在自己的客户端检查”为什么管不住别的入口或检查后的再次修改。不是再造支付网络，也不是宣布已接好一个安全生产商城。

按 S0→S6 连续完成，不逐阶段等评估者：输入来源表→纯投影→正常/变更/缺证据→穿插/旁路反例→可读演示和结论→完整 L2/报告。PROJECTOR.py 只实现 project_checkout，不复制 EVALUATOR_CHECK.oracle_result/expected_order 或导入 Evaluator 检查器来交付；源码与测试依据可读，但提交的实现必须独立使用项目模型/哈希辅助。不得通过替换原生函数、改运行时或在函数中运行商家动作产生结果。

S0 命令（仓库根）：

```powershell
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H48_UCP_CONFIRMATION_SEAM_PROBE_V1/EVALUATOR_CHECK.py baseline
```

完整 L2（每次使用新目录，最多三次）：

```powershell
python ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H48_UCP_CONFIRMATION_SEAM_PROBE_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H48_UCP_CONFIRMATION_SEAM_PROBE_V1/evidence/l2_executor_01 --mode executor
python ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
```

REPORT 应有 Task ID、Baseline HEAD、SUBMITTED_FOR_REVIEW、各 AC 的实现/证据映射、EV triplet 路径、L2 gate 与 plan 路径、实际成本、继承 dirty 工作区、限制。预填报告不等于完成。RESULT schema=h48-result/v1，classification=CLIENT_GUARD_ONLY，reason/strongest_alternative/next_question 给出有来源的解释；product_improved/production_adapter_ready/provider_proof_verified/customer_demand_validated/third_party_verified/atomic_snapshot_binding_proven/model_attack_measured 全 false，full_product_gate_comparison=NOT_MEASURED，customer_demand=UNKNOWN。

账本 ATTEMPT_LEDGER schema=h48-attempt-ledger/v1；formal_l2_attempts、asgi_requests、active_work_minutes、external_runtime_calls/model_calls/provider_calls=0。正式逐轮、L1 汇总计数，最多 3 次 L2 / 600 次包内请求 / 480 分钟主动执行；单轮正式上限 80。自报时间与客观 meta 分开，不伪造成本精度。L2 前先按本轮预计调用计入保守预留，完成后与 observations 和各阶段日志核对。

提交时不要自行转 Evaluator 或签 PASS；保留 EXECUTING/Executor，phase 可写 H48_SUBMITTED_FOR_REVIEW，next_artifact_path 指向 REPORT。评估者接受完整快照后再转 READY_FOR_REVIEW 独立 L3。

PREPARATION 仅为 Evaluator 检查夹具/判定依据，不是你的实现或正式 L2。禁止重跑 FREEZE、修改保护哈希、安装包/升级依赖或恢复支付宝/比赛/外部通信。

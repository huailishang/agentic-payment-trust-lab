# H62执行入口：批准只恢复订单，绝不再次付款

先读CURRENT、CONTRACT、INPUTS、H61 REVIEW/ANALYSIS。任务为SINGLE capability_experiment，四产品文件内实现。父库和父任务全部只读，使用新副本新合成批准；历史批准不授予执行权。

先实现共享的原生订单事务准备/保存逻辑，再实现交易库唯一消费收据和批准锁→原生交易锁的协议。ORDER_RECOVERY.run(config,request,hook=...)接口、show/revoke的CONSUMED结果、固定16场景及原生6旅程/批准24回归不可改。候选尚不存在，准备检查不是成绩。

360主动分钟/2L2/最多3完整套，所有L1/失败保留并计入预留预算。开始后设置同任务CURRENT为EXECUTING/Executor。维护真实ATTEMPT_LEDGER：task_id、active_work_minutes、闭合work_intervals_utc、formal_l2_attempts、reservations（四个journal相对键与行数）、network_calls/model_calls/provider_calls/real_payment_calls/packages_installed/git_write_operations全0。正式L2前按即将创建的目录计formal_l2_attempts，不能重置失败费用。

首次实现可按单case本地反馈：已有H47 Python执行RECOVERY_CASES.py --role executor --case R01_NORMAL；每次case/worker自动预留。开发反馈也计费，后续完整套不覆盖它。判别器/worker/计划/输入/合同冻结，不能为适配代码修改测试期望。

正式命令：

```powershell
python -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l2_executor_01 --mode executor
```

最多_02。VP07从真实journal行数机械同步reservations和已建立的L2目录数；冻结runner不替执行者填工时或结果，不重置失败费用。RESULT必须task_id、本地恢复classification、remaining_gaps非空、production_ready/real_identity_verified/provider_verified/customer_value_proven/standard_checkout_mandate_integrated均false；不能把本地订单恢复写成真实商户处置。

完整L2通过后REPORT写SUBMITTED_FOR_REVIEW、逐AC/EV、相同来源前后、事务/撤销全部入口、失败/工时/预算；CURRENT仍EXECUTING/Executor。中央结构OK后交Evaluator独立L3，不写REVIEW或自发最终PASS。不能改src/SDK、联网/安装/真实付款、提交或推送。

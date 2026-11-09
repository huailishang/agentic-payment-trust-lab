# H58 Executor 入口

先读CURRENT.md、CONTRACT.md、VALIDATION_PLAN.yaml和INPUTS.json；这是只读测量，不启动商城或付款。H57R已PASS/STOP，其剩余额度不沿用。

1. 先运行python -B 本包/CHECK.py inputs；有漂移立即停，不重建INPUTS。
2. 实现仅本包MEASURE.py。参数--role executor/evaluator --repeat 2；每次读取前追加唯一attempt_id/role/UTC到evidence/<role>/MEASUREMENT_ATTEMPTS.jsonl，Executor总<=8、Evaluator<=4。输出evidence/<role>/measurement_1.json及measurement_2.json，不覆盖失败证据；存在输出时先保留到唯一历史目录。本次成功Executor测量另写MEASUREMENT.json。不要导入CHECK.expected。
3. 按合同12主题/三机制/单一决策写ANALYSIS.json和中文ANALYSIS.md；可从CHECK.TOPICS/validate_analysis了解schema，禁止借检验器生成事实。读库仅SQLite mode=ro&immutable=1，所有未知保留。
4. 写RESULT、ATTEMPT_LEDGER和REPORT，记录工作区间start/end、读取次数、L2目录数；完整六VP后统一交评估者，不逐小步等待。
5. 公共门禁命令：python ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H58_MERCHANT_PAID_ORDER_GAP_MEASUREMENT_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H58_MERCHANT_PAID_ORDER_GAP_MEASUREMENT_V1/evidence/l2_executor_01 --mode executor
6. 公共结构检查：python ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
提交保持EXECUTING/Executor；Executor status: SUBMITTED_FOR_REVIEW仅L2 PASS后。不能改冻结Checker/计划/旧任务、不能Git或联网。通过只证明只读测量，不是安全补单/退款成绩。

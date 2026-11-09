<!-- Public display copy; original SHA-256: 8914ed156403f57b1004e43b58fc146d44d188dd69ebc9b933e7883e0fdc76fe; only trailing whitespace/line endings normalized. -->

# H60 Executor 入口：本地人工批准的对账处置登记

先读CURRENT、CONTRACT、CASE_SPEC、INPUTS和固定七VP。H59选择已解决，不再询问同一权限方向；本包只写新批准账本，不解锁旧claim、不补单/退款。真实人身份未验证，本地可信启动配置是显式假设。

唯一产品文件：APPROVAL_INBOX.py。实现冻结ApprovalInbox同步API、ApprovalDenied.code与本地CLI；来源事实须自己读SQLite，禁止导入HARNESS/CHECK或硬编码已知M06观察。approvals与approval_events须持久；候选连接源必须ro&immutable，只有独立ledger可写。完整接口/摘要/状态优先级见合同。

首次运行先建立ATTEMPT_LEDGER.json，含case_attempts=0、formal_l2_attempts=0、active_work_minutes=真实已用、闭合work_intervals_utc及合同所列八项0副作用。RESULT先完整如实写边界，再正式门禁；不要将尚未通过写成正式PASS。RUN_AND_ACCOUNT在成功/失败后同步实际case预留与门禁目录数。

准备只验证了来源/表结构/判别器，未运行候选，没有新批准。20例中的C11是冻结夹具副本的负向“已有订单”输入，不是候选创建业务订单；C09/10/11/12的overlay均明确保存，候选来源hash必须在overlay之外保持。所有原源/旧报告只读。

建议先编译、低成本定向诊断，再一次完整20例L1，完整七VP L2后一次统一交回。所有调用固定HARNESS的case预留都计费；若自己写独立诊断调用候选，也必须先记同一CASE_ATTEMPTS规范路径并占case预算，保留失败，不能另建不计费试验。固定案例runner按run建目录，不覆盖历史。

L2命令（公共runner使用已有H47 Python以提供yaml；冻结每项argv仍为python标准库）：
.task_envs/H47/.venv/Scripts/python.exe ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H60_LOCAL_OPERATOR_RECONCILIATION_APPROVAL_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H60_LOCAL_OPERATOR_RECONCILIATION_APPROVAL_V1/evidence/l2_executor_01 --mode executor

L2失败下一目录02，不覆盖；总<=2。提交前公共结构检查：
.task_envs/H47/.venv/Scripts/python.exe ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md

240主动分钟/160case，Evaluator另60；零HTTP/Provider/模型/安装/Git。CURRENT执行/提交仍EXECUTING/Executor，REPORT写SUBMITTED_FOR_REVIEW只在完整L2 PASS后；不签最终PASS。不改冻结Checker/计划/合同，不放宽不通过的反例；预算耗尽/需扩权限即停回Evaluator。

成功只证明“有证据绑定且可撤销、可持久读取的本地批准”，订单缺口仍存在。后续任何批准消费或自动业务执行必须另冻合同。

# H50 执行者入口

H49已最终PASS。现在做固定UCP商家本地副本样机，不重复来源研究、不接真实支付。先读CURRENT、AGENTS、公共evaluator-executor-workflow v2.2、CONTRACT、SOURCE_COPY、FROZEN_TESTS、EVALUATOR_CHECK及计划。

目标：保留原生商品/履约/库存/订单流程，把付款前持久化占用接到complete/update/cancel，让并发修改、重复请求和崩溃不能改变已确认快照或产生第二次模拟付款。

## 先检查

```powershell
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/EVALUATOR_CHECK.py baseline
```

漂移就停止，不重装、不改BASELINE、不运行PREPARE_FREEZE。原生35文件已复制，仅两处现有副本文件的明确方法可改，另加services/execution_control.py，原件和src/tests不动。

## 连续完成

1. CURRENT可转EXECUTING/Executor，其他关联/历史/false权限不变。
2. 按合同ExecutionControl、原生付款execution参数、同库合成授权、事务A/B和hooks实现；先正常完成，再拒绝/竞争，不全阻断。
3. L1可运行FROZEN_TESTS.py guarded --case G01_NORMAL等单项；不改冻结脚本迁就实现。全部case顺序在脚本，正式L2前可原范围修复。
4. 编写DESIGN.md、RESULT.json、ATTEMPT_LEDGER.json及REPORT.md。结果/开销按实际输出；原生金额绑定为NOT_OBSERVABLE，不写假before。
5. 完整L2及中央校验后一次交回，不自行签最终PASS；6小时/2次正式L2，同失败无新依据停止。

```powershell
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/evidence/l2_executor_01 --mode executor
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
```

正式每次新目录，不覆盖失败。REPORT写真实EV和Gate，使用普通Before/After/Delta/Measurement evidence/Guardrail result/Scope caveat标签；L2通过才SUBMITTED_FOR_REVIEW。提交时CURRENT仍EXECUTING/Executor，phase=H50_SUBMITTED_FOR_REVIEW、next_artifact仍REPORT，等Evaluator接受。

## 结论边界

15保护/2原生是本包固定验证，不等于H49未来14项全测；直接方法调用不等于HTTP/签名集成，同库合成授权不等于真实身份/跨系统撤销，模拟账本不等于Provider。网络/ASGI/模型/Provider/对外联系/安装/Git/真实资金全部零。

恢复只QUERY/WAIT保留待对账，不自动退款补单；库函数保留由AST/hash检查，语义仍待人工L3。代理并发0，内部会话及故障worker由冻结测试控制。不能手造成功观察。

# H50R 执行者入口

H50已REJECTED；冻结L3虽5/5，但补充独立反例发现B事务在途时同步锁等待阻塞事件循环/抛数据库锁错误，以及其他原生成功分支订单完成但未进入独立模拟付款。只修这两类合同违例，保留旧15场景，不扩网络或生产。

先读CURRENT、AGENTS、公共工作流、H50最终REVIEW、本包CONTRACT/INHERITED_COPY、FROZEN_TESTS及REPAIR_PROBES。36文件已从拒收快照复制，原件不动，只改本目录两个指定实现文件。

```powershell
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H50R_LOCAL_GUARD_CONTENTION_PAYMENT_ROUTING_REPAIR_V1/EVALUATOR_CHECK.py baseline
```

漂移停止，不改BASELINE/检查器。可转EXECUTING/Executor，串行修复锁/路由→廉价局部验证→全部旧回归及四条修复回归→材料→完整L2。REPAIR_PROBES的--diagnostic只为Evaluator准备展示继承失败，正式VP-06不带它，必须全部通过。

```powershell
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H50R_LOCAL_GUARD_CONTENTION_PAYMENT_ROUTING_REPAIR_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H50R_LOCAL_GUARD_CONTENTION_PAYMENT_ROUTING_REPAIR_V1/evidence/l2_executor_01 --mode executor
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
```

3小时/2次正式L2，不重置H50预算；每次新目录，重跑前归档上次*_l2.json，不覆盖失败。REPORT沿用原schema/模板但Task ID为本包；DESIGN解释改动，RESULT仍本地原型有限结论；账本分列继承和新开销。提交时CURRENT仍EXECUTING/Executor，phase=H50R_SUBMITTED_FOR_REVIEW、next_artifact仍REPORT，不自签PASS。

不接真实Google/Shop服务，四种分支只是合成工具数据。原生验证失败不charge，成功分支应统一经过同一模拟付款观察；不通过扩大HTTP/身份/自动退款来修本包。网络/ASGI/模型/Provider/对外联系/安装/Git全部零。

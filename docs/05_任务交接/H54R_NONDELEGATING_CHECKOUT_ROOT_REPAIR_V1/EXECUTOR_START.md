# H54R 执行入口

Task ID: H54R_NONDELEGATING_CHECKOUT_ROOT_REPAIR_V1
State: CONTRACT_FROZEN / Executor / repair / SINGLE
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Map revision: 2026-10-31-r90

项目目标为高风险支付可信执行/审计；A–D关闭、E仅本地、F当前。B-17标准消费第一缺陷是外层cnf被提取过程丢失，优先修它，再谈同事务接线/HTTP/Provider。父H54最终REJECTED/INCONCLUSIVE，固定L2/L3 8/8不抵消U02/U03；旧H53R仍PASS/STOP，支付宝/比赛延期。

先读CURRENT、地图r90、父H54/REVIEW及U02/U03原始材料、当前CONTRACT/SOURCE_COPY/ROOT_CASES/CHECK/REPAIR_CHECK/计划。只修本任务consumer.py，当前是逐字节父缺陷副本；不改父代码、SDK或冻结条件。必须同时保留官方完整根和有效载荷条件，明文/披露的外层cnf都拒绝，不能只在CheckoutMandate里搜字段。

120主动分钟/2正式L2/总312case；原36包装器最多288，根3最多24，合计39/完整轮。先预留后运行，所有失败保留。调试仅下列两个包装器，可对原36用--case单例；不要直接无账本调用候选。预记ATTEMPT_LEDGER正式次数及两类预留总和，再完整L2。

```text
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H54R_NONDELEGATING_CHECKOUT_ROOT_REPAIR_V1/CHECK.py baseline
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H54R_NONDELEGATING_CHECKOUT_ROOT_REPAIR_V1/FROZEN_TESTS.py --role executor
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H54R_NONDELEGATING_CHECKOUT_ROOT_REPAIR_V1/ROOT_CASES.py --role executor
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H54R_NONDELEGATING_CHECKOUT_ROOT_REPAIR_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H54R_NONDELEGATING_CHECKOUT_ROOT_REPAIR_V1/evidence/l2_executor_01 --mode executor
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
```

第二轮只用l2_executor_02，首轮不删除/覆盖。9/9通过后REPORT=SUBMITTED_FOR_REVIEW、CURRENT仍EXECUTING/Executor，整包后Evaluator一次统一独立L3，不自授PASS/自动下一任务。外层root类型/空结账/旧版本三个诊断不在本修复AC，不夹带全面协议重写。

零网络/安装/真实密钥/付款/下单/ASGI/模型/对外联系/Git。父H54两轮L2/144case、Evaluator46case及拒收原样保留。需要扩大实现/判据/依赖/预算/权限即停回Evaluator。

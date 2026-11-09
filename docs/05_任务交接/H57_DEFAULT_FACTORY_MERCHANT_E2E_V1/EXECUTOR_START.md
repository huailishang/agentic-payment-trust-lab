# H57 执行入口：回到商城整条交易链

Task ID: H57_DEFAULT_FACTORY_MERCHANT_E2E_V1
State: CONTRACT_FROZEN / Executor / capability_experiment / SINGLE
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Map revision: 2026-10-31-r93

这次做商城接线，不再扩授权字段：用官方商城样例的已接受本地分支，把现有控制接进正常服务工厂，跑创建→批准/授权→完成→重放→查询，以及异常后不重复付款。真实商城源码/HTTP/数据库都运行，付款仍是独立模拟账本，没有线上商户/真实资金。

先读CURRENT、地图r93、CONTRACT/CASE_SPEC、H51独立C07默认工厂基线、SOURCE_COPY和CHECK。37文件是H53R接受快照；除了dependencies.py中get_checkout_service函数体，其他36只读。新增merchant/guarded_app.py的create_app装配原server.app及原生命周期；禁止FastAPI dependency_overrides、新路由或patch签名/业务。HTTP_RUNTIME/RUN_JOURNEY为本轮测试实现，参考H51源码时不能沿用其替换工厂办法。

六条业务验收：正常+同键重放+订单查询；批准后改数量；缺确认；HTTP签名有效但授权被改；未配控制；模拟付款后订单失败/真正新进程查状态并拦重试。签发材料必须来自真实创建HTTP响应，不能用DB补字段。若这一步不兼容原合同，记录具体商家接缝后停止，不顺手修验证器。

240分钟/2L2/160实际HTTP请求，每完整六例<=28；每请求前预留HTTP_ATTEMPTS唯一ID、失败也计数，新目录保留所有原始数据。假付款/查询按实计，真实网络/支付/安装/模型/Git为0。M06不能用同进程重建对象冒充重启，恢复只是查询/不重扣，不自动补单。

```text
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H57_DEFAULT_FACTORY_MERCHANT_E2E_V1/CHECK.py baseline
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H57_DEFAULT_FACTORY_MERCHANT_E2E_V1/RUN_JOURNEY.py --role executor
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H57_DEFAULT_FACTORY_MERCHANT_E2E_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H57_DEFAULT_FACTORY_MERCHANT_E2E_V1/evidence/l2_executor_01 --mode executor
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
```

只新增规定装配/工厂/测试实现及报告。正式前预记ATTEMPT_LEDGER，7/7完整通过后REPORT=SUBMITTED_FOR_REVIEW，CURRENT仍EXECUTING/Executor；第二轮只用l2_executor_02，不覆盖失败，整包后Evaluator独立复核。H56仅保留支线，本轮不运行/不修改；标准CheckoutMandate/新profile不装进商城。

范围、协议、权限、预算要变即停回Evaluator。不自授PASS、不自动下一任务、不启动监听服务或接外部支付。

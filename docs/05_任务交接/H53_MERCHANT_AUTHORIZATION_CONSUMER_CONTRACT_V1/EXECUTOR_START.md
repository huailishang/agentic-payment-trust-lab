# H53 执行入口

Task ID: H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1
State: CONTRACT_FROZEN / Executor / one_off / SINGLE
Map revision: 2026-10-31-r86
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b

先读CURRENT、地图r86、CONTRACT、FROZEN_TESTS、FIXTURES、CHECK、INHERITED_COPY与VALIDATION_PLAN。旧草案已归档，不再按原来的“仅设计”执行。

本轮只做本地方法样机：把真实已验签原文/完整checkout与既有确认、数据库执行快照在同一claim事务强制一致。版本仍2026-04-08，完整普通JWS，不宣称完整JCS/UCP/AP2。当前没有候选实现或28例成绩，准备签验/3例旧API/76+8回归不算Executor结果。

使用现成环境，先运行CHECK.py baseline。只改任务内两份商家文件指定位置和新增ap2_authorization.py；精确参数/事务位置见合同。不能改冻结夹具、检查器或付款端口来通过。无可信配置/授权须拒绝，直接claim也受保护。

完整方法波次通过FROZEN_TESTS.py --out 本任务evidence内唯一文件运行；先预留28case、保存失败、覆盖前归档并记本角色账本。Executor<=280，Evaluator另<=112，廉价完整波次也计数。正式L2前先formal_l2_attempts加1并完成材料，然后执行：

```text
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/evidence/l2_executor_01 --mode executor
```

预算6主动小时、2正式L2；重试用新目录。28例/76回归/H37八例/范围材料等9项完整通过后REPORT=SUBMITTED_FOR_REVIEW；CURRENT仍EXECUTING/Executor、next_artifact=REPORT，中央validate_workflow通过后整包交Evaluator，不逐阶段等待，不自授PASS或自动下一包。

零网络/ASGI/模型/Provider/真实付款/安装/对外联系/Git，私钥只在内存；任务外成果只读。超范围/预算停止报精确缺项。H51/H52 STOP和支付宝/比赛后置不变。

# H53R 执行入口

Task ID: H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1
State: CONTRACT_FROZEN / Executor / repair / SINGLE
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Map revision: 2026-10-31-r87

先读CURRENT、地图r87、父H53最终REVIEW/独立S04–S06、当前CONTRACT、SOURCE_COPY、FROZEN_TESTS/TAIL_CASES/CHECK和计划。原H53 REJECTED及1/2 L2、56/280case保持，不能在父目录覆盖修复。

只可修改本任务merchant/services/ap2_authorization.py。当前仍是父提交的有缺陷副本，未有修复实现或L2。SDK可验证中间型链不代表可用于最终付款；显式收窄完整两跳、根/末角色和终结状态，确保错误aud/nonce的可继续委托末跳不能付款。不改SDK、另36商家文件、锁/确认/付款/恢复或冻结案例。

现成环境先CHECK.py baseline。28原回归通过FROZEN_TESTS.py --out evidence内独立文件运行，六例通过TAIL_CASES.py --out独立文件运行；合计34，每批先记账。Executor<=272，Evaluator另102；失败/旧观察必须保留。

预算2主动小时/2正式L2，正式前先formal_l2_attempts加1并写完整REPORT/RESULT，再运行：

```text
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01 --mode executor
```

9项完整通过后REPORT=SUBMITTED_FOR_REVIEW，CURRENT仍EXECUTING/Executor、next_artifact=REPORT；中央validate_workflow通过后一次交Evaluator。不得自授PASS、自动H53R2或逐阶段等Human。

零网络/ASGI/模型/Provider/真实付款/安装/对外联系/Git。私钥只在内存，已签材料均合成；不宣称完整协议/JCS/真实身份。越范围/预算停止回Evaluator，不改冻结保护消除失败。

# H80 执行入口

唯一权威为CURRENT.md与CONTRACT.md；本文件只说明已冻结入口。当前包准备完成不等于产品修复完成。

1. 读父H79 REVIEW及本包CONTRACT/PLAN/SOURCE/BASELINE/FREEZE，确认无源漂移。将CURRENT改为EXECUTING/Executor及实际执行阶段，权限全部保持。执行包无需逐步骤人工复核。
2. 使用已有Windows agent Python：`& 'D:/SoftWare/Anaconda/workspace/.conda/envs/agent/python.exe' -B 'docs/05_任务交接/H80_VERIFIED_FACT_CONTEXT_BINDING_REPAIR_V1/BOOTSTRAP.py' --mode implementation --attempt 1`。只登记，不实现代码；随后按合同完成两产品文件、三kwargs和新回归文件。可逆修复不新增安装/WSL/网络步骤。
3. 每cycle至多2次廉价目标L1，记录命令/结果；正式L2用同一BOOTSTRAP入口`--mode executor --attempt 1`。成功即停止重跑；失败只在原范围内尝试第二cycle和第二L2，各加`--attempt 2`。原失败与部分行为输出保留。行为观察直接在VP-02 stdout中，失败前已打印的原行也保留。
4. 一次提交完整REPORT：`Executor status: SUBMITTED_FOR_REVIEW`、Task/HEAD、Change summary、Validation、Acceptance criteria self-check、L2 Task Gate、EV-01至EV-04的AC/Meta/Stdout/Stderr、Impact comparison、实际费用/失败/边界。区分合成守护单测、历史公开证明与当前认证；不要将本地callback称为真实付款，不自行签发最终PASS。
5. 报告完成后执行现有agent Python加`-B 本包/SEAL.py`；它先结构校验、复核L2三件套，再封源码diff/摘要与SUBMISSION。报告格式问题先修报告，不重跑通过的L2。CURRENT保持EXECUTING/Executor，交Evaluator接受。

Evaluator先检查提交及全部摘要，加入SUBMISSION本身封ACCEPTED，路由READY_FOR_REVIEW/Evaluator，再执行BOOTSTRAP `--mode evaluator`唯一L3并逐AC验收。父H79/H78保护通过明确旧字节别名核验，禁止运行父真实发行或重写父原始证据。

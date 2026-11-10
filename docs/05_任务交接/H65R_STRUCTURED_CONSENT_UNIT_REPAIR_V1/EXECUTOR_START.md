# H65R执行入口

当前唯一任务以根CURRENT.md为准。本包修复H65漏读字段，不执行IronClaw、回放或产品改造。

1. 读CONTRACT.md、H65 REVIEW.md、EXPECTED.json和VALIDATION_PLAN.yaml。
2. 标准Python先运行本任务CHECK.py package。只有公开克隆也可核对合同与检查器。
3. 在具备既有原始输入及PyArrow的本地环境运行CHECK.py source；缺文件即INPUT_LIMIT（输入受限），不要改摘要或下载。
4. source通过才将CURRENT改EXECUTING/Executor；按合同创建一次分析结果和完整尝试账本。原H65提交、失败与L2/L3只读。
5. 正式L2使用公共runner与本任务冻结计划，最多2次，失败保留；成功提交REPORT时仍保持EXECUTING/Executor，由Evaluator接受复核。

源检查命令：`.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H65R_STRUCTURED_CONSENT_UNIT_REPAIR_V1/CHECK.py source`。

L2命令：`.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H65R_STRUCTURED_CONSENT_UNIT_REPAIR_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H65R_STRUCTURED_CONSENT_UNIT_REPAIR_V1/evidence/l2_executor_01 --mode executor`。

预算45主动分钟/8次完整episode读取/1版结果/2L2；网络、安装、模型、产品、回放、付款0。无需寻找未提交的隐蔽入口；原始输入不在公开仓库中，位置和摘要由INPUTS列出。包验证通过不是来源或L2通过。

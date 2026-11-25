# H90 执行入口

阅读冻结合同、计划及输入清单，在本机现有的 Windows Conda agent Python 3.12 下运行，确保随后启动的 `python` 仍解析到同一环境。切换到 EXECUTING / Executor 后，先执行 S0 的基线命令并保存原始结果，再按合同顺序完成 S1–S7。

```text
python -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-1 --mode executor
```

每轮使用不同证据目录，失败原件与预算如实保留。统一提交 REPORT、SUBMISSION 和运行证据。使用公共验证器确认结构后保留 EXECUTING / Executor，并在 CURRENT 标记提交。Evaluator 接受后另行执行独立 L3。

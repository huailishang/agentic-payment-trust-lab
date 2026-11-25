# H88 执行交接

按冻结合同 S0–S3 连续执行，唯一当前路由在仓库根目录 `CURRENT.md`。先检查现有 Windows Conda `agent` 的 Python 3.12 和 `CHECK.py preflight`，核对冻结摘要，然后进入实现。CHECK 以进程级导入隔离引用仓内 tests，子进程继承仓内 src 路径。保留基线文件，切勿在已改候选的工作区重建 `BASELINE.json` 或 `FREEZE.json`。

公共 L2 命令从仓库根目录运行。每次为 `--out` 选本任务下空目录，保留失败原件与账本。

```powershell
conda run --no-capture-output -n agent python -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H88_STORED_CONFIRMATION_WITHDRAWAL_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H88_STORED_CONFIRMATION_WITHDRAWAL_V1/evidence/l2-attempt-1 --mode executor
```

正式 L2 全通过后提交报告，附输入/提交摘要、两个入口增量、原图与事实回查、原回归和成本。Evaluator 确认接受后独立生成唯一 L3。全部额外权限保持 false。

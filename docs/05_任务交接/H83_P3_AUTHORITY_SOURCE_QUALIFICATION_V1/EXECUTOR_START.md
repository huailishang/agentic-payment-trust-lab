# H83 执行者入口

从仓库根目录使用现有 Windows Conda `agent`。完整范围、匹配规则、证据和预算见 [冻结合同](CONTRACT.md)。本任务只有一个合法产品改动文件。

## 初始基线

先把 `Get-FileHash -Algorithm SHA256` 对 `FREEZE.json` 的结果与 `CURRENT.md` 中的 `frozen_manifest_sha256` 比对，原样记录。然后执行以下两条，保存解释器身份和原始基线输出。第二条只适用于实现开始前。

```powershell
conda run --no-capture-output -n agent python -B -c 'import os, sys, yaml, cryptography; print(sys.executable, sys.version, os.name, yaml.__version__, cryptography.__version__)'
conda run --no-capture-output -n agent python -B docs/05_任务交接/H83_P3_AUTHORITY_SOURCE_QUALIFICATION_V1/CHECK.py before
```

原结果为 BOUND / ALLOW / 1 个模拟回调。基线失败时记录 BLOCKED。基线合格后在账本登记实现开始，再进入单文件改动。任一范围内实现可运行一次定向 `CHECK.py behavior --role executor`。原回归和正式三项 VP 在同一 L2 中统一运行。

## 正式 L2 与提交

如已存在输出目录，保留原件。首次执行用下列固定入口。合同允许且登记了再试原因时，第二次仅将 `--out` 更换为 `evidence/l2_retry_02`。

```powershell
$env:PYTHONUTF8 = '1'
conda run --no-capture-output -n agent python -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H83_P3_AUTHORITY_SOURCE_QUALIFICATION_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H83_P3_AUTHORITY_SOURCE_QUALIFICATION_V1/evidence/l2 --mode executor
```

正式命令 argv、退出码、已用实现/L2 次数、失败、墙钟与已知费用写入 `ATTEMPT_LEDGER.jsonl`。成功后写 `REPORT.md`、`SUBMISSION.json`、单文件 diff 与 SHA、冻结摘要、完整 VP 原始证据及 L2 门禁。报告落盘后执行结构校验。

```powershell
conda run --no-capture-output -n agent python -B ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
```

交接保持 EXECUTING / Executor，由 Evaluator 验收快照后改 READY_FOR_REVIEW 并独立执行 L3。

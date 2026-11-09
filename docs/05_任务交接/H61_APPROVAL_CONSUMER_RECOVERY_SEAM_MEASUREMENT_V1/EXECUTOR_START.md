# 执行 H61：只测批准到订单恢复的接缝，不执行补单

先读 CURRENT、本 CONTRACT/INPUTS/VALIDATION_PLAN、父 H60R REVIEW。H60R 已通过并停止扩展，父 H60 的拒收不回写。

只实现一个标准库只读 EXTRACT.py，按固定schema忠实提取十文件与三库，写至 --out 给定的本任务新证据路径。先读父批准记录和原商城 complete/claim/recover/订单事务代码，完成十主题、三方案比较、八项未来设计及一个结论。不能调用候选或商家函数，不能将保存的批准解释为当前业务执行授权。

新预算120主动分钟/两次正式L2/四次提取器调用；每次调用前由冻结 RUN_AND_ACCOUNT 预留，失败不覆盖。准备中不运行候选。建立真实ATTEMPT_LEDGER/RESULT/ASSESSMENT/ANALYSIS，先把CURRENT同任务设EXECUTING/Executor并更新phase，保留全局历史/权限。

```powershell
python -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H61_APPROVAL_CONSUMER_RECOVERY_SEAM_MEASUREMENT_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H61_APPROVAL_CONSUMER_RECOVERY_SEAM_MEASUREMENT_V1/evidence/l2_executor_01 --mode executor
```

最多_02，不改CHECK/INPUTS/合同/计划；只读材料缺真实接缝时形成有证据的STOP/合同变更结论，不伪造可实施性。完整L2成功后REPORT标SUBMITTED_FOR_REVIEW、引用六EV/Gate result/Gate summary/Validation plan及每AC/费用/失败，CURRENT仍EXECUTING/Executor，中央校验OK后交Evaluator。

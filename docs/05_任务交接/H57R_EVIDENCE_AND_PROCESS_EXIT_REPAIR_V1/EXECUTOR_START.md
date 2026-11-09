# 执行 H57R：修日志与真正的进程退出验证

你是Executor。先读CURRENT、本CONTRACT、VALIDATION_PLAN及父H57 REVIEW。父H57已拒收；不要回写其代码/日志/报告或把旧18请求当正式成绩。

本包商家接线候选完整复制，38商家文件全部冻结；只允许修本包HTTP_RUNTIME.py、RUN_JOURNEY.py中的证据记录/M06进程安排。两个脚本当前仍是父候选原样，修复没有实施，不是可直接通过的成品。重点：新规范JSONL预留；不承载M06商城的监督进程先等首worker退出，再开恢复worker。保持六条业务与验签/假PSP不变。

历史57请求已经花掉，本包最多新增103；正式L2最多2，Evaluator另80。历史保守计时120分钟，新主动工作最多90。先设CURRENT为EXECUTING/Executor并更新phase；先baseline/scope/selftest，再实现和必要L1。禁止不断重跑凑结果；预算守卫必须在每个HTTP前。

正式门禁命令：

```powershell
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/evidence/l2_executor_01 --mode executor
```

运行前按合同补齐真实ATTEMPT_LEDGER/RESULT/REPORT；run的请求计数产生后、VP-04前可由脚本更新预算计数，但不能伪造结果。L2创建目录会占1次尝试，失败必须保留，最多_02。不改CHECK/合同/计划。提交时REPORT列明全部七EV与L2摘要、失败、工时区间和PCAC；完整L2后一次交Evaluator，不自判PASS。

CodexPro先前误报和连接问题已修，不删模拟配置读取代码或绕过门禁；新准确错误才是新阻塞。没有网络/真实支付/安装/Git授权。若需动商家实现或额外权限，停止报告准确原因。

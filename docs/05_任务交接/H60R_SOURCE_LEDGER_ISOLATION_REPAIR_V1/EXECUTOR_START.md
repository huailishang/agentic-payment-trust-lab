# 执行 H60R：只修来源与账本的文件身份隔离

先读 CURRENT、父 H60 REVIEW、本 CONTRACT、VALIDATION_PLAN、INPUTS。父 H60 已拒收，不能把其 v3 成绩或自发 evaluator 模式当正式验收。新副本候选原样保留，修复未实施；Evaluator 未代改产品。

只改 APPROVAL_INBOX.py 的 ApprovalInbox.__init__ 函数体，在任何可写连接/建表前拒绝来源与账本的相同文件（尤其硬链接）。其他 AST 全冻结。HARNESS 已在本合同采纳独立审查过的连接关闭/相邻时钟修正，并加入四条别名例；不要改它或 CHECK/计划。

准备 baseline/scope/selftest 均不调用候选。先改实现，再必要 L1；不要先重跑已知失败原样候选。新 Executor 最多 72 案例、120 主动分钟、两次正式 L2；继承 79 案例/30分钟/两次已消费门禁，不能清零。不得使用 evaluator 模式，父子 Evaluator 只余 34 例。

建立真实 ATTEMPT_LEDGER/RESULT 并保存工作区间。先将 CURRENT 同任务设 EXECUTING/Executor、更新 phase；全局历史和四项授权不变。正式命令：

```powershell
python -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/evidence/l2_executor_01 --mode executor
```

最多再用 _02，失败不覆盖；每个 case 前持久预留由冻结运行器承担。完整 L2 成功后 REPORT 写 Executor status: SUBMITTED_FOR_REVIEW，引用七个 EV、真实 Gate result/Gate summary/Validation plan、每 AC/失败/费用/范围；CURRENT 仍 EXECUTING/Executor。中央校验 OK 后交 Evaluator，不能自判 PASS。零 HTTP/网络/Provider/安装/模型/Git/真实资金，不触发补单或退款。

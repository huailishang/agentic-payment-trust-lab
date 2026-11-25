# H87 执行交接

从CURRENT的CONTRACT_FROZEN/Executor开始。先核INPUTS.json与HEAD，本次基线是负责人已同步的df4073d，旧H85/H86冻结HEAD仍按原证据保留，不能机械重跑它们的严格旧HEAD检查。

按合同S0至S3连续完成，一次性交L2与报告。先将CURRENT切到EXECUTING/Executor，仅改状态和执行阶段，next_artifact_path指向REPORT.md。使用已存在原生Python3.12及项目tests包，所有命令工作目录为仓库根。无需安装或WSL。

正式L2命令为

```text
python -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/l2-attempt-1 --mode executor
```

每次正式尝试先在本任务evidence/ATTEMPT_LEDGER.jsonl追加角色、序号、开始时间和输出目录，结束追加返回码与成本。目录须新建且不存在旧Gate，第二次仅按合同可恢复分支使用l2-attempt-2，禁止覆盖。逐条引用四份EV、源接口定位、测量JSON及124项原回归。REPORT需含Task ID/Baseline HEAD/Executor status、Workspace snapshot、Changed files、L2 Task Gate、EV-01至EV-04、Impact comparison及Deviations。未测到合法撤回入口也属于测量结果，不能用模拟登记替代。

评估者先核提交、候选及输入摘要和原L2三件套，通过结构校验并接受快照后推进READY_FOR_REVIEW/Evaluator，再用相同计划--mode evaluator写全新evidence/l3。其命令只进入临时数据库，不发起外部动作。L3后逐AC与源码交叉裁决。当前制包仅预检语法、依赖和测试数量，正式行为测量及124项执行尚未发生。

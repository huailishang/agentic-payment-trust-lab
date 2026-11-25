# H89 Executor 入口

只沿 CURRENT.md 的 H89 合同执行。H88 已独立签收，禁止代改旧报告、旧门禁或恢复其预算。当前任务是八步骤统一离线测量，不是整份撤销实现。

1. 阅读 CONTRACT.md、VALIDATION_PLAN.yaml 和 INPUTS.json，确认原生 Windows Conda agent Python 3.12、无优化；为本次进程选择解释器和PATH，不安装或修改环境。按协议改 CURRENT 为 EXECUTING / Executor。
2. 顺序完成 S0–S7，前置满足自动继续。qualification可作便宜L1；接收面无整份入口也继续按冻结分支测量，不能伪造已受理事件。
3. 正式门禁使用公共 runner，下面 argv 在仓库根、同一原生环境执行：

```text
python -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1 --mode executor
```

4. 记录每步和每次正式尝试，失败不可覆盖；最多2次L2，第二次仅合同允许恢复，不自行修CHECK或产品。报告接收面签名、源码因果、三分支12行、机制约束、逐AC和费用，不把ALLOW写成已撤销后付款。
5. 统一 REPORT/SUBMISSION 交付，运行公共 validate_workflow.py；提交时 CURRENT 保持 EXECUTING / Executor，注明 SUBMITTED_FOR_REVIEW。Evaluator 接受同一快照后独立L3；不得替代验收。全部额外权限false，产品和历史只读。

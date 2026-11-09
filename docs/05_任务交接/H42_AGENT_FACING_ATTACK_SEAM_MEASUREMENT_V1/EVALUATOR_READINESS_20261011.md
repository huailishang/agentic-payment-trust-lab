# H42 执行前评估（2026-10-11）

> 历史执行前记录。后续已收到执行者提交并完成独立 L3；现行裁决为 REVIEW.md 的 PASS / NOT_APPLICABLE / STOP。以下“尚未提交/未测量”只描述本记录形成时，不能再用作当前状态。

Task ID: H42_AGENT_FACING_ATTACK_SEAM_MEASUREMENT_V1
Review type: PRE_EXECUTION_READINESS_ONLY
Assessment: READY_FOR_EXECUTOR / NOT_SUBMITTED_FOR_REVIEW
Task verdict: NOT_ISSUED
Project impact: NOT_MEASURED
Map basis: 2026-09-30-r70
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b

## 全局位置

项目要证明合法支付任务能完成，越权、错绑、漏确认和重复副作用可被阻断，并留下可独立复核的证据。A–D 阶段已关闭，E 在本地代表性边界闭环，F 仍缺外部实证。B-06 的支付宝凭证与绑定缺口保留；Human 在 2026-10-11 明确将支付宝后置，当前先评估 H42、外部对照与第三方复跑结果包。

本轮 Human 随后明确选择“先只完成评估和任务包”。因此不通知执行者、不派子智能体、不执行 H42 测量或外部模型实验，不修改 CURRENT、冻结合同、输入和检查器。本文不是正式 REVIEW，也不代替 L2/L3。

## 当前交付事实

现有 CONTRACT、VALIDATION_PLAN、BASELINE、FIXTURE、EVALUATOR_CHECK、GOVERNANCE_CHECK、EXECUTOR_START 均存在。

MEASUREMENT.py、SOURCE_AUDIT.md、REPORT.md 和 L2 证据尚不存在。CURRENT 仍为 CONTRACT_FROZEN / Executor。因此不是复核失败，也不能发 PASS 或 REJECTED；尚未形成可接受的执行快照。

## 本轮实际检查

| 检查 | 实际结果 | 能证明什么 |
|---|---|---|
| HEAD 与冻结保护哈希 | baseline 检查 exit 0；全部一致 | 当前受保护产品与检查器未漂移 |
| 策略相关回归 | 15/15 PASS | 现有策略测试可运行 |
| 闸门相关回归 | 42/42 PASS | 现有闸门测试可运行 |
| git diff --check | exit 0 | 当前已跟踪 diff 无空白错误；不等于审完所有未跟踪文件 |
| 中央 validate_workflow.py | OK，exit 0 | 现有路由与必需治理产物结构有效 |
| 运行时依赖 | Python 3.12.3、cryptography 46.0.7、PyYAML 6.0.3 已存在 | 无需新增安装即可进入原合同执行 |

首次直接调用 GOVERNANCE_CHECK 因 H42_TEST_PYTHON 未设置而停止；设置为现有 Python 可执行文件后 baseline 和 regressions 均通过。这是执行环境初始化要求，不是产品缺陷。

本轮没有运行 measurement，没有启动中央 L2/L3 runner，没有产生正式测量结果，也未消耗原合同“最多两次正式 L2 提交”的额度。以上结果来自评估者本轮命令输出；未生成正式 EV/RV-EV 三件套。

## 合同审查结论

原合同范围保持有效，不需要为本次准备工作改写：

1. 必须先真实调用策略，再把实际选择送入现有产品闸门，不能预填动作结果。
2. 用户授权、确认及已授权订单在 fixed 分支必须固定；不能跟随污染后的候选重建。
3. 良性正对照必须 ALLOW 且模拟 callback=1；正对照无效不能解释为攻击被拦截。
4. reconstructed_diagnostic 仅说明测试脚本重建确认的风险，其放行不等于固定授权下的漏洞。
5. 八次运行仅覆盖一个输入族及确定性重复；不能宣称真实 LLM、上游 WebShop 或支付宝验证。
6. 测出未授权模拟 callback 后停止并报告，不能在本包修改产品把结果改绿。

## 交给执行者时的唯一入口

仍使用本目录 EXECUTOR_START.md 和原 VALIDATION_PLAN.yaml。PowerShell 会话先执行：

```powershell
$env:H42_TEST_PYTHON = (Get-Command python).Source
```

然后按原合同实现 MEASUREMENT.py、SOURCE_AUDIT.md、REPORT.md，运行正式 L2，提交原始证据。不能复制本文准备检查冒充正式 L2。

本轮不派发该入口。后续收到符合合同的执行快照后，评估者再运行独立 L3，逐项判 AC。

## 结果后的决策

- 有效测量且固定授权拦截：关闭本输入族测量，比较外部对照的增量证据价值；不继续堆同类标题变体。
- 固定授权下出现未授权模拟 callback：先独立复现共同断点，再决定修复；不能直接跳到包装成功结果。
- 正对照失败或来源不清：修测量有效性；不发布安全结论。

后续设计入口见 ../../02_未来规划/外部对照与第三方复跑_评估任务计划_20261011.md。H44/H45 为有启动条件的草案，尚未替换 CURRENT。

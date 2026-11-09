# H42 Executor 入口

先读 CURRENT.md、CONTRACT.md、BASELINE.json、FIXTURE.json、VALIDATION_PLAN.yaml 与 EVALUATOR_CHECK.py。继承 H43 未提交的产品实现，不能回滚或重新实现它。

只实现本目录 MEASUREMENT.py 的 run_probe(cases=..., choose_action=..., gate_action=...)。cases 顺序已冻结；每项真实调用一次策略，再将实际选择映射为对应候选，最后通过注入 gate 调用现有产品闸门。用户确认与 authorized_adaptation 在 fixed 分支绑定商品 2且固定；reconstructed_diagnostic 只作测试脚本风险对照。

正对照须 ALLOW、模拟 callback=1。污染分支结果按实际记录：阻断和暴露失败均可完成测量，禁止调产品把测量改绿。真实回调由检查器替换成纯内存计数，不能接网络。整个目录均为合成离线测量，不冒充上游 WebShop 或真实用户确认。

使用现有含 cryptography 的 Python 指定 H42_TEST_PYTHON；用已有含 PyYAML 的 Python 执行中央 runner：

```text
python ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H42_AGENT_FACING_ATTACK_SEAM_MEASUREMENT_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H42_AGENT_FACING_ATTACK_SEAM_MEASUREMENT_V1/evidence/l2_executor --mode executor
```

提交 REPORT.md 与 SOURCE_AUDIT.md，逐项引用 L2 EV triplet；中央 validate_workflow.py --repo . --current CURRENT.md 必须 OK。正式 L2 最多两次。提交后由独立 Evaluator 接受快照、另跑 L3并裁决；执行者不能给 PASS或改 router。需要更改产品、攻击输入、预算或联网时 STOP并报告准确断点。

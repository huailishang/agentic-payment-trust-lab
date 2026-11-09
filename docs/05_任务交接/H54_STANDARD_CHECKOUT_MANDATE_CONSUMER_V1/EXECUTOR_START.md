# H54 执行入口

Task ID: H54_STANDARD_CHECKOUT_MANDATE_CONSUMER_V1
State: CONTRACT_FROZEN / Executor / capability_experiment / SINGLE
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Map revision: 2026-10-31-r89

项目要证明授权到执行/审计可靠；A–D已关闭，E仅本地，F当前。B-17本地消费/终结链已由H53R关闭，剩标准对象消费。H54只做平台单CheckoutMandate的商家验证方法，不付款、不迁移完整商家；后续执行接线由Evaluator另决策。H53仍拒收、H53R保持PASS/STOP，支付宝/比赛延期。

依次读CURRENT、最新地图r89、CONTRACT、PREPARATION_NOTES、SOURCE_MANIFEST、FIXTURES/FROZEN_TESTS、CHECK和VALIDATION_PLAN。完整JCS源码和独立向量已固定，无需安装或联网。准备证明材料/环境可跑，消费者consumer.py尚不存在，36例没有执行成绩。

1. 先运行下方baseline检查，通过后仅把CURRENT状态改EXECUTING/Executor。
2. 只实现consumer.py中的consume(request_json,session_json,trust,now)，遵循合同返回字段；不要写新的商家、付款口或另一个SDK。标准ap2.checkout_mandate、真实SDK验签、请求外根、完整JCS与原始vct缺一不可。
3. 调试只经FROZEN_TESTS.py --role executor，可加--case Cxx；自动预留case/新建材料目录、失败不覆盖。不得直接另写脚本无账本调用候选。360主动分钟/288case/2次完整L2，串行完成后一次交付。
4. 填写REPORT/RESULT/ATTEMPT_LEDGER，预记正式L2次数，运行完整8项。第二轮只许新目录l2_executor_02，旧失败保持。

```text
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H54_STANDARD_CHECKOUT_MANDATE_CONSUMER_V1/CHECK.py baseline
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H54_STANDARD_CHECKOUT_MANDATE_CONSUMER_V1/FROZEN_TESTS.py --role executor
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H54_STANDARD_CHECKOUT_MANDATE_CONSUMER_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H54_STANDARD_CHECKOUT_MANDATE_CONSUMER_V1/evidence/l2_executor_01 --mode executor
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
```

8/8通过才REPORT=SUBMITTED_FOR_REVIEW；CURRENT仍EXECUTING/Executor、next_artifact=REPORT，等Evaluator接受快照后独立L3。遇范围/权限/冻结判据/预算变化立即停止并说明，不能自授PASS或自动续下一任务。零网络、安装、真实密钥、付款、对外联系、提交/推送；本包公开合成签名材料不代表现实身份或生产支付。

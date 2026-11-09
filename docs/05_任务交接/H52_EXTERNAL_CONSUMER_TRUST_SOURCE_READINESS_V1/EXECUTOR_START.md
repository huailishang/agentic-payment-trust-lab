# H52 执行入口

Task ID: H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1
State: CONTRACT_FROZEN / Executor / one_off / SINGLE
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Map revision: 2026-10-30-r84

本包是长串行测量，不是“先看一页文档就回来”，也不是现在就接Stripe/Medusa。只写本目录测量驱动与材料，产品/商家实现全只读；整包L2后一次交Evaluator。

按顺序阅读CURRENT、地图r84、CONTRACT、CASE_SPEC、SOURCE_MANIFEST、REFERENCE/PACKET_CHECK、VALIDATION_PLAN；旧草案已归档，不再按其中2小时或“等客户”来执行。

串行完成来源/版本审计→可信角色与责任表→PROBES.py十二真实签名材料测量→12项接入义务和一个未来最小边界→材料/预算→完整8项L2→提交。普通不支持是合法测量结果，继续整包材料；只有保护/权限/范围或预算变化才停。禁止中途自动改产品、验签、schema或商家以让负例变绿。

使用现成H47 Windows环境，RUNTIME已解决旧H37纯Python依赖和模块路径，零安装；官方SDK只用固定v0.2.0，官方资料已离线保存。先运行PACKET_CHECK.py baseline，禁止改BASELINE来绕漂移。

廉价probe也须通过RUN_PROBES.py --out 本目录evidence内独立文件运行并记账。正式L2前先把formal_l2_attempts加1并完成REPORT/材料，然后运行：
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/evidence/l2_executor_01 --mode executor

后续L2使用新的证据目录，最多3次。源码/真实公开输入与API结果不能只交passed=true，禁止调用REFERENCE.recompute替代自己的驱动。输出结构可对照REFERENCE，Evaluator将从公开材料独立验算和审阅。

预算：6主动小时/3正式L2/144材料case；串行/代理0，所有网络/ASGI/Provider/模型/付款/Git写操作0。私钥仅内存，四角色全合成，不把验签通过冒充用户同意或端到端付款通过。

L2通过后REPORT=SUBMITTED_FOR_REVIEW，CURRENT仍EXECUTING/Executor、next_artifact=REPORT；执行中央validate_workflow后一次交回。只有Evaluator能接受快照、做L3并给最终PASS。

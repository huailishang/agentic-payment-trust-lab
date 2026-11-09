# H56 执行入口

Task ID: H56_TRUSTED_DISCLOSURE_PROFILE_V1
State: CONTRACT_FROZEN / Executor / capability_experiment / SINGLE
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Map revision: 2026-10-31-r92

这次开始补规则，不再重复调查：授权相关位置必须把摘要对应的内容提供齐，唯一明确可选资料区可以藏子内容。项目已有本地支付控制/恢复/审计，当前F/B-17卡的是授权事实完整性；未补好前不接付款。H55测量已PASS/STOP，H54R接受范围和父H54拒收保持。

先读CURRENT、地图r92、H55最终REVIEW、当前CONTRACT/SOURCE_COPY、PROFILE_CASES的P02/P04及冻结sources/BASELINE_OBSERVATIONS，再读全部检查器和计划。只改本任务consumer.py，当前仍是原样H54R，无完整性规则。不要动SDK/商家/旧代码；不要实现新签名声明或任意豁免配置。

固定配置在请求之外绑定平台kid/版本，不能信请求自声明。官方验签成功后，检查签名原文和披露摘要图，不能只看SDK抹掉未披露字段后的对象。所有授权位置默认查齐；仅根optional_data里可隐藏子资料，它不参与任何授权/业务事实。P06旧根可选字段隐藏与授权位置诱饵摘要拒绝是明确兼容代价，不能为了“兼容标准”放宽。

240主动分钟/2L2/424case（原36的288+根3的24+配置14的112）。每批包装器自动先记预留，新目录保存输入/输出/失败，不覆盖；正式前预记L2次数与三账本合计。

```text
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H56_TRUSTED_DISCLOSURE_PROFILE_V1/CHECK.py baseline
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H56_TRUSTED_DISCLOSURE_PROFILE_V1/FROZEN_TESTS.py --role executor
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H56_TRUSTED_DISCLOSURE_PROFILE_V1/ROOT_CASES.py --role executor
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H56_TRUSTED_DISCLOSURE_PROFILE_V1/PROFILE_CASES.py --role executor
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H56_TRUSTED_DISCLOSURE_PROFILE_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H56_TRUSTED_DISCLOSURE_PROFILE_V1/evidence/l2_executor_01 --mode executor
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
```

53场景/10项完整通过后REPORT=SUBMITTED_FOR_REVIEW，CURRENT仍EXECUTING/Executor，整包后Evaluator一次L3。第二轮只用l2_executor_02，不删首轮失败。新候选没有成绩，准备只确认旧对照14例和判别器；不自行PASS、不自动H57。

零网络/安装/真实密钥/付款/下单/HTTP/ASGI/模型/对外联系/Git。范围、AC、依赖、隐私例外、预算或权限要变就停止回Evaluator。

# H67执行入口：只测元数据中的防重复要求

先读CONTRACT、SOURCE_BUNDLE和PREPARATION；本包输入全部公开，使用标准Python，无需安装或原始数据缓存。

1. CHECK.py package/source通过后运行init，再将CURRENT改EXECUTING/Executor；墙钟45分钟从init计。
2. 分析前CHECK.py begin ANALYSIS，得到A编号；只读bundle，生成10探针/5示例观察及来源引用。版本结果写versions/A编号/RESULT.json；失败写同目录ERROR.json。运行finish A编号 该相对路径 SUCCEEDED或FAILED，成功后再将该版本复制为顶层RESULT.json，不覆盖旧版本。
3. 每探针对只增删meta.idempotency_key。分别记录容器必填与内部键必填；只解释meta子集，不运行示例或完整请求。服务端拒绝/补键/扣款均未测。
4. L2前begin L2得到L编号，使用公共runner，结束后finish L编号 evidence/l2_executor_01/L2-GATE.json SUCCEEDED或FAILED；失败换新目录保留。最多2分析尝试及2正式L2。
5. 运行final后编写REPORT，提供原始失败、矩阵、Gate result/summary与EV映射。提交保持EXECUTING/Executor，不签发PASS。报告完成后再运行final确认所有尝试封存。

CHECK前缀：`.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H67_ACP_MCP_IDEMPOTENCY_CONTRACT_MEASUREMENT_V1/CHECK.py`。

L2命令：`.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H67_ACP_MCP_IDEMPOTENCY_CONTRACT_MEASUREMENT_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H67_ACP_MCP_IDEMPOTENCY_CONTRACT_MEASUREMENT_V1/evidence/l2_executor_01 --mode executor`。

账本为追加JSONL，begin必须先于实质尝试，失败照计。不得运行旧checker、旧提取器、MCP/HTTP/支付服务、上游脚本或模型服务，不得新GET、安装、commit/push或修改产品。只交付这一份契约矩阵。

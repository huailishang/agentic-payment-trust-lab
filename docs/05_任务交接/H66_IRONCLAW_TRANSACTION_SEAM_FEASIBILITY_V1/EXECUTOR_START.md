# H66执行入口：先找具体消费者，不安装运行时

唯一问题、范围及停止条件以CONTRACT为准。先读锁定的IronClaw笔记、本仓已有覆盖与H65R REVIEW；不重读旧六例原始数据。

1. 标准Python运行本任务CHECK.py package；在仓库运行source核对公开历史/产品。无需CartTrace原始输入。
2. 运行CHECK.py init，再将CURRENT改EXECUTING/Executor。90分钟墙钟从init起计；只生成一版结论。
3. 每次公开源读取前运行CHECK.py reserve file 仓库相对路径，或reserve tree 固定提交、reserve issue 编号、reserve pr 编号。输出S编号；随后才调用GitHub连接器，必须取完整文件，不使用截断行片段。
4. 用文件工具保存sources/S编号.json，再运行CHECK.py finish S编号 sources/S编号.json SUCCEEDED。404等失败也保存错误对象并以FAILED结束；失败照计，最多同目标2次、总20次，顺序执行。
5. file来源JSON：kind、repository、ref、target、url、blob_sha、content、partial=false。url使用固定GitHub blob链接，content为完整原文；blob_sha须能由原文复算。issue/pr/tree来源JSON：kind、repository、target、url、observed_at、data；tree另含ref。失败对象保留kind/repository/target/error；不保存令牌、认证头或签名跳转地址。
6. 创建RESULT，引用source归档的原文行摘要，并写范围限制。继续必须是具体金融消费者和新增可独立判定边界，不能只填泛用工具模块。
7. 正式L2前reserve l2 VALIDATION_PLAN.yaml，运行公共runner；完成后finish L编号 evidence/l2_executor_01/L2-GATE.json SUCCEEDED或FAILED。失败换新目录保留，至多2次。随后运行final再写REPORT；报告中提供Gate result/summary、各EV映射、影响对比、所有失败和预算。

CHECK命令前缀：`.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/CHECK.py`。

L2：`.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l2_executor_01 --mode executor`。

提交保持EXECUTING/Executor；不自称PASS，不commit/push，不运行IronClaw、测试、钱包、签名、付款或本仓产品。来源足够即停，余额不是继续找更多模块的理由。连接器或固定源不可用就记录输入受限；不能换版本或扩大授权。
